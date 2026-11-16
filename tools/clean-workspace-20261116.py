#!/usr/bin/env python3
"""2026-11-16 使用者授權的工作區清理：先保存未覆蓋檔，再刪除已逐 SHA 保存的研究副本與快取。

子命令：
  preserve --project P --scan SCAN.json.gz --out MANIFEST.json   # preserved 可寫
  plan     --project P --scan SCAN.json.gz --out PLAN.json.gz     # 全唯讀，逐物件解壓核對
  apply    --project P --plan PLAN.json.gz --out RESULT.json      # workplace 可寫
  dedup    --project P --out RESULT.json [--apply]                # preserved 內同 bytes 物件改硬連結
  restore  --project P --plan PLAN.json.gz --prefix 前綴 --out R.json # workplace 可寫，拒絕覆寫不同內容
SCAN 由逐檔 SHA 掃描產生（rows: path/sha256/bytes/ino/mtime_ns/covered 或 kind=symlink）。
"""
import argparse, collections, gzip, hashlib, json, os, pathlib, re, sys
from concurrent.futures import ProcessPoolExecutor

HEX = re.compile(r'^([0-9a-f]{64})\.(gz|gzip|raw)$')
SCOPE = ['workplace/probe-20261023/graphics-first/', 'workplace/gomodcache/']
PROTECTED = [
    'workplace/probe-20261023/graphics-first/battle-r1/rust-head-art-package-r1/',  # tools/rust-native-player.sh 現行預設批次
    'workplace/probe-20261023/graphics-first/ending-hd-r1/',  # 2026-10-28 清理工具既有保護
    'workplace/probe-20261023/graphics-first/all-graphics-integration-r1/',
]


def sha_file(p, codec='raw'):
    h = hashlib.sha256()
    op = gzip.open if codec != 'raw' else open
    with op(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def store_index(root):
    idx = collections.defaultdict(list)
    for folder, dirs, names in os.walk(root / 'preserved', followlinks=False):
        for n in names:
            m = HEX.match(n)
            if m:
                idx[m.group(1)].append(pathlib.Path(folder, n))
    return idx


def in_scope(path):
    return any(path.startswith(s) for s in SCOPE) and not any(path.startswith(p) for p in PROTECTED)


def load_scan(p):
    return json.loads(gzip.decompress(p.read_bytes()))['rows']


def check_obj(args):
    sha, path = args
    codec = 'raw' if path.endswith('.raw') else 'gzip'
    try:
        return sha, path, sha_file(path, codec) == sha
    except Exception:
        return sha, path, False


def cmd_preserve(a):
    r = a.project
    rows = [x for x in load_scan(a.scan) if x.get('covered') is False and x['path'].startswith(SCOPE[0])]
    out = []
    for x in rows:
        f = r / x['path']
        assert not f.is_symlink() and f.is_file()
        assert sha_file(f) == x['sha256'], x['path']
        dst = r / 'preserved' / 'objects' / x['sha256'][:2] / f"{x['sha256']}.gzip"
        if not dst.exists():
            dst.parent.mkdir(exist_ok=True)
            tmp = dst.with_name(dst.name + '.tmp')
            with open(f, 'rb') as src, gzip.open(tmp, 'wb', compresslevel=6) as g:
                for b in iter(lambda: src.read(1 << 20), b''):
                    g.write(b)
            assert sha_file(tmp, 'gzip') == x['sha256']
            os.replace(tmp, dst)
        out.append(dict(path=x['path'], sha256=x['sha256'], bytes=x['bytes'],
                        stored=str(dst.relative_to(r)), stored_sha256=sha_file(dst)))
    assert not a.out.exists()
    a.out.write_text(json.dumps(dict(schema=1, purpose='2026-11-16 清理前保存未覆蓋檔', files=out),
                                ensure_ascii=False, indent=1) + '\n')
    print(len(out), 'files preserved')


def cmd_plan(a):
    r = a.project
    idx = store_index(r)
    rows = load_scan(a.scan)
    cand = [x for x in rows if in_scope(x['path'])]
    need = {}
    for x in cand:
        if x.get('kind') == 'symlink':
            continue
        assert x['sha256'] in idx, ('not preserved', x['path'])
        need[x['sha256']] = str(idx[x['sha256']][0])
    with ProcessPoolExecutor(4) as ex:
        bad = [(s, p) for s, p, ok in ex.map(check_obj, need.items(), chunksize=64) if not ok]
    assert not bad, bad[:5]
    files = []
    for x in cand:
        f = r / x['path']
        s = f.lstat()
        if x.get('kind') == 'symlink':
            files.append(dict(path=x['path'], kind='symlink', target=x['target'], ino=s.st_ino))
        else:
            assert (s.st_size, s.st_mtime_ns, s.st_ino) == (x['bytes'], x['mtime_ns'], x['ino']), x['path']
            files.append(dict(path=x['path'], kind='file', sha256=x['sha256'], bytes=x['bytes'],
                              mtime_ns=x['mtime_ns'], ino=x['ino'],
                              stored=str(pathlib.Path(need[x['sha256']]).relative_to(r))))
    assert not a.out.exists()
    plan = dict(schema=1, scope=SCOPE, protected=PROTECTED, verified_objects=len(need), files=files)
    a.out.write_bytes(gzip.compress(json.dumps(plan, ensure_ascii=False).encode()))
    print(json.dumps(dict(files=len(files), verified_objects=len(need),
                          bytes=sum(v.get('bytes', 0) for v in files))))


def cmd_apply(a):
    r = a.project
    work = r / 'workplace'
    plan = json.loads(gzip.decompress(a.plan.read_bytes()))
    assert a.out and not a.out.exists()
    before = os.statvfs(work)
    removed = size = 0
    skipped = []
    parents = set()
    chmodded = set()
    for v in plan['files']:
        rel = pathlib.PurePosixPath(v['path'])
        assert not rel.is_absolute() and '..' not in rel.parts and in_scope(v['path'])
        f = r / rel
        assert all(not (r / pathlib.PurePosixPath(*rel.parts[:n])).is_symlink() for n in range(1, len(rel.parts)))
        try:
            s = f.lstat()
        except FileNotFoundError:
            continue
        assert s.st_uid == 1000
        if v['kind'] == 'symlink':
            if not f.is_symlink() or os.readlink(f) != v['target']:
                skipped.append(v['path']); continue
        elif f.is_symlink() or (s.st_size, s.st_mtime_ns, s.st_ino) != (v['bytes'], v['mtime_ns'], v['ino']):
            skipped.append(v['path']); continue
        try:
            f.unlink()
        except PermissionError:
            d = f.parent  # Go 模組快取等唯讀目錄：只放寬清理範圍內的目錄
            assert in_scope(str(d.relative_to(r)) + '/')
            os.chmod(d, d.stat().st_mode | 0o200); chmodded.add(str(d.relative_to(r)))
            f.unlink()
        removed += 1; size += v.get('bytes', 0); parents.add(f.parent)
    for parent in sorted(parents, key=lambda p: len(p.parts), reverse=True):
        while parent != work and str(parent.relative_to(r)) + '/' not in PROTECTED:
            try:
                parent.rmdir()
            except OSError:
                break
            parent = parent.parent
    after = os.statvfs(work)
    res = dict(schema=1, status='completed', removed_files=removed, removed_logical_bytes=size,
               free_bytes_before=before.f_bavail * before.f_frsize, free_bytes_after=after.f_bavail * after.f_frsize,
               changed_files_kept=skipped, chmodded_dirs=len(chmodded), plan_sha256=sha_file(a.plan), protected=PROTECTED)
    a.out.write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps(res, ensure_ascii=False))


def cmd_restore(a):
    r = a.project
    plan = json.loads(gzip.decompress(a.plan.read_bytes()))
    restored = 0
    for v in plan['files']:
        if not v['path'].startswith(a.prefix):
            continue
        rel = pathlib.PurePosixPath(v['path'])
        assert not rel.is_absolute() and '..' not in rel.parts and rel.parts[0] == 'workplace'
        f = r / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        if v['kind'] == 'symlink':
            if f.is_symlink():
                assert os.readlink(f) == v['target'], v['path']; continue
            assert not f.exists(); os.symlink(v['target'], f); restored += 1; continue
        if f.exists():
            assert sha_file(f) == v['sha256'], ('拒絕覆寫不同內容', v['path']); continue
        src = r / v['stored']
        tmp = f.with_name(f.name + '.restore.tmp')
        with (open(src, 'rb') if src.name.endswith('.raw') else gzip.open(src, 'rb')) as s, open(tmp, 'wb') as d:
            for b in iter(lambda: s.read(1 << 20), b''):
                d.write(b)
        assert sha_file(tmp) == v['sha256']
        os.replace(tmp, f); restored += 1
    res = dict(schema=1, prefix=a.prefix, restored=restored)
    if a.out.exists():
        print(json.dumps(res)); return
    a.out.write_text(json.dumps(res) + '\n'); print(json.dumps(res))


def cmd_dedup(a):
    r = a.project
    groups = collections.defaultdict(list)
    for folder, dirs, names in os.walk(r / 'preserved', followlinks=False):
        for n in names:
            if HEX.match(n):
                p = pathlib.Path(folder, n)
                s = p.lstat()
                assert not p.is_symlink() and s.st_uid == 1000
                groups[(n, s.st_size)].append(p)
    linked = saved = 0
    for (n, sz), ps in groups.items():
        byino = {}
        for p in ps:
            byino.setdefault(p.stat().st_ino, p)
        if len(byino) < 2:
            continue
        canon, *rest = sorted(byino.values(), key=lambda p: (not str(p).startswith(str(r / 'preserved/objects')), str(p)))
        ref = sha_file(canon)
        for p in rest:
            if sha_file(p) != ref:
                continue
            if a.apply:
                tmp = p.with_name(p.name + '.lnk.tmp')
                os.link(canon, tmp)
                os.replace(tmp, p)
            linked += 1; saved += sz
    assert not a.out.exists()
    res = dict(schema=1, applied=a.apply, relinked_files=linked, saved_bytes=saved)
    a.out.write_text(json.dumps(res, indent=1) + '\n')
    print(json.dumps(res))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('cmd', choices=['preserve', 'plan', 'apply', 'dedup', 'restore'])
    p.add_argument('--project', type=pathlib.Path, required=True)
    p.add_argument('--scan', type=pathlib.Path)
    p.add_argument('--plan', type=pathlib.Path)
    p.add_argument('--out', type=pathlib.Path, required=True)
    p.add_argument('--apply', action='store_true')
    p.add_argument('--prefix', default='workplace/')
    a = p.parse_args()
    assert os.getuid() == 1000
    dict(preserve=cmd_preserve, plan=cmd_plan, apply=cmd_apply, dedup=cmd_dedup, restore=cmd_restore)[a.cmd](a)


if __name__ == '__main__':
    main()
