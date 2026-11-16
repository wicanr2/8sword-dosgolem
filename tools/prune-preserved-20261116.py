#!/usr/bin/env python3
"""2026-11-16 使用者授權：刪除 preserved 中只屬 Go／HD 階段研究的物件。

保留條件（任一成立即保留）：
- 被名稱以 rust-、hd-music、v1.0 開頭，或含 20261116 的保存清單引用
- 任一來源路徑在 music-first、dist-all，或不在 workplace 之下
- 不被 catalog.json.gz 或較早的 workspace-cleanup 清單引用（屬其他類別，不在本次範圍）
第二輪 plan-r2（Go 版退役）改用明確保留清單，清單外一律刪除：
- rust-head-art-package-r1、v1.0-filenames-r1、hd-music* 清單引用的物件
- artwork/manifest.json 原圖的備份
- 任一來源路徑屬 KEEP_R2_PATHS
子命令：
  plan  --project P --out PLAN.json.gz        # preserved 唯讀
  plan-r2 --project P --out PLAN.json.gz      # preserved 唯讀
  apply --project P --plan PLAN --out R.json  # preserved 可寫
"""
import argparse, collections, glob, gzip, hashlib, json, os, pathlib, re

HEX = re.compile(r'^([0-9a-f]{64})\.(gz|gzip|raw)$')
KEEP_MANIFEST = re.compile(r'^(rust-|hd-music|v1\.0)|20261116')
KEEP_R2_MANIFEST = re.compile(r'^(rust-head-art-package-r1\.json|v1\.0-filenames-r1\.json|hd-music)')
KEEP_R2_PATHS = ('workplace/player/assets-painted-r69/', '/music-first/', 'dist-all/v1.0/', 'dist-all/v.0.1.1-20261112/',
                 'workplace/intake-20261023/', 'workplace/dosgolem/', 'workplace/probe-20261023/text-first/',
                 'workplace/probe-20261023/graphics-first/battle-r1/rust-head-art-package-r1/',
                 '珍092-神州八劍.rar', '8sword.zip')


def manifests(pres):
    for p in sorted(glob.glob(str(pres / '*.json'))) + sorted(glob.glob(str(pres / '*.json.gz'))):
        try:
            raw = open(p, 'rb').read()
            d = json.loads(gzip.decompress(raw) if p.endswith('.gz') else raw)
        except Exception:
            continue
        if isinstance(d, dict) and isinstance(d.get('files'), list):
            yield pathlib.Path(p).name, d['files']


def plan(a):
    r = a.project; pres = r / 'preserved'
    refs = collections.defaultdict(set); paths = collections.defaultdict(set)
    for name, files in manifests(pres):
        for f in files:
            if isinstance(f, dict) and isinstance(f.get('sha256'), str):
                refs[f['sha256']].add(name)
                for k in ('path', 'source_path'):
                    if isinstance(f.get(k), str):
                        paths[f['sha256']].add(f[k])
    rows = []; keep = collections.Counter()
    for folder, dirs, names in os.walk(pres, followlinks=False):
        for n in names:
            m = HEX.match(n)
            if not m:
                continue
            sha = m.group(1); p = pathlib.Path(folder, n); s = p.lstat()
            rs = refs.get(sha, set()); ps = paths.get(sha, set())
            if not any(x == 'catalog.json.gz' or x.startswith('workspace-cleanup') for x in rs):
                keep['other-class'] += 1; continue
            if any(KEEP_MANIFEST.search(x) for x in rs):
                keep['kept-manifest'] += 1; continue
            if not ps or any('/music-first/' in x or x.startswith('dist-all/') or not x.startswith('workplace/') for x in ps):
                keep['kept-path'] += 1; continue
            rows.append(dict(path=str(p.relative_to(r)), sha256=sha, bytes=s.st_size, ino=s.st_ino,
                             mtime_ns=s.st_mtime_ns, refs=sorted(rs)[:5], example=sorted(ps)[0]))
    uniq = {}
    for x in rows:
        uniq.setdefault(x['ino'], x['bytes'])
    out = dict(schema=1, keep_counts=keep, files=rows, unique_bytes=sum(uniq.values()))
    assert not a.out.exists()
    a.out.write_bytes(gzip.compress(json.dumps(out, ensure_ascii=False).encode()))
    print(json.dumps(dict(files=len(rows), shas=len({x['sha256'] for x in rows}),
                          unique_bytes=out['unique_bytes'], keep=keep)))


def plan_r2(a):
    r = a.project; pres = r / 'preserved'
    keep = set(); why = collections.Counter()
    art = json.load(open(r / 'artwork' / 'manifest.json'))['files']
    keep |= {f['sha256'] for f in art}
    for name, files in manifests(pres):
        if name.startswith('preserved-prune'):
            continue
        for f in files:
            if not (isinstance(f, dict) and isinstance(f.get('sha256'), str)):
                continue
            ps = [f[k] for k in ('path', 'source_path') if isinstance(f.get(k), str)]
            if KEEP_R2_MANIFEST.search(name) or any(k in x for x in ps for k in KEEP_R2_PATHS):
                keep.add(f['sha256'])
    rows = []
    for folder, dirs, names in os.walk(pres, followlinks=False):
        for n in names:
            m = HEX.match(n)
            if not m:
                continue
            if m.group(1) in keep:
                why['kept'] += 1; continue
            p = pathlib.Path(folder, n); s = p.lstat()
            rows.append(dict(path=str(p.relative_to(r)), sha256=m.group(1), bytes=s.st_size, ino=s.st_ino, mtime_ns=s.st_mtime_ns))
    uniq = {}
    for x in rows:
        uniq.setdefault(x['ino'], x['bytes'])
    out = dict(schema=1, mode='go-retire', keep_shas=len(keep), files=rows, unique_bytes=sum(uniq.values()))
    assert not a.out.exists()
    a.out.write_bytes(gzip.compress(json.dumps(out, ensure_ascii=False).encode()))
    print(json.dumps(dict(files=len(rows), shas=len({x['sha256'] for x in rows}), unique_bytes=out['unique_bytes'], keep=why)))


def apply(a):
    r = a.project; pres = r / 'preserved'
    d = json.loads(gzip.decompress(a.plan.read_bytes()))
    assert a.out and not a.out.exists()
    before = os.statvfs(pres); removed = 0; skipped = []
    for v in d['files']:
        rel = pathlib.PurePosixPath(v['path'])
        assert rel.parts[0] == 'preserved' and '..' not in rel.parts and HEX.match(rel.name)
        f = r / rel
        try:
            s = f.lstat()
        except FileNotFoundError:
            continue
        if f.is_symlink() or (s.st_size, s.st_ino, s.st_mtime_ns) != (v['bytes'], v['ino'], v['mtime_ns']):
            skipped.append(v['path']); continue
        f.unlink(); removed += 1
    after = os.statvfs(pres)
    h = hashlib.sha256(a.plan.read_bytes()).hexdigest()
    res = dict(schema=1, removed_files=removed, skipped=skipped, plan_sha256=h,
               free_bytes_before=before.f_bavail * before.f_frsize, free_bytes_after=after.f_bavail * after.f_frsize)
    a.out.write_text(json.dumps(res, indent=1) + '\n'); print(json.dumps(res))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('cmd', choices=['plan', 'plan-r2', 'apply'])
    p.add_argument('--project', type=pathlib.Path, required=True)
    p.add_argument('--plan', type=pathlib.Path)
    p.add_argument('--out', type=pathlib.Path, required=True)
    a = p.parse_args(); assert os.getuid() == 1000
    dict(plan=plan, apply=apply)[a.cmd](a) if a.cmd != 'plan-r2' else plan_r2(a)
