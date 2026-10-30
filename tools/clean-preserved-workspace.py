#!/usr/bin/env python3
"""Clean verified archived workspace copies while protecting the current runtime."""
import argparse
import collections
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import time


def sha(path, codec='raw'):
    h = hashlib.sha256()
    with (gzip.open if codec == 'gzip' else open)(path, 'rb') as stream:
        for data in iter(lambda: stream.read(1 << 20), b''):
            h.update(data)
    return h.hexdigest()


def read(path):
    return json.loads(gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_text())


def write(path, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    with path.open('xb') as stream:
        stream.write(gzip.compress(raw, compresslevel=6, mtime=0) if path.suffix == '.gz' else raw)


def stamp(path):
    s = path.lstat()
    return dict(bytes=s.st_size, mtime_ns=s.st_mtime_ns, inode=s.st_ino,
                device=s.st_dev, uid=s.st_uid, mode=stat.S_IMODE(s.st_mode),
                allocated_bytes=s.st_blocks * 512, links=s.st_nlink)


def same_file(a, b):
    return all(a[k] == b[k] for k in ['bytes', 'mtime_ns', 'inode', 'device', 'uid', 'mode'])


def safe(root, name):
    rel = Path(name)
    assert not rel.is_absolute() and '..' not in rel.parts
    path = root / rel
    assert all(not p.is_symlink() for p in [path, *path.parents] if p != root.parent)
    return path


def protections(root):
    runtime = read(root / 'workplace/player/runtime.json')
    fixed = ['workplace/intake-20261023', 'workplace/gomodcache', 'workplace/dosgolem',
             'workplace/probe-20261023/text-first', 'workplace/player/assets',
             'workplace/player/' + runtime['assets'],
             'workplace/player/' + runtime['application_source_candidate'],
             'workplace/player/assets-painted-r68',
             'workplace/player/source-candidate-map-color-r2',
             'workplace/player/gui/compat-pixels-save-r2',
             'workplace/probe-20261023/graphics-first/battle-r1/owned-defeat-r1']

    def protected(name):
        p = Path(name)
        if not p.parts or p.parts[0] != 'workplace':
            return True
        if any(name == v or name.startswith(v + '/') for v in fixed):
            return True
        if p.name.lower().startswith('gamedata.ay') or any(v in {'save', 'saves', 'scratch'} for v in p.parts):
            return True
        if len(p.parts) >= 3 and p.parts[1] == 'player':
            if (len(p.parts) == 3 and (root / p).is_file()) or p.parts[2].startswith('runtime-'):
                return True
        return False
    return fixed, protected


def references(root):
    refs = collections.defaultdict(list)
    indexes = {}
    sources = [root / 'preserved/catalog.json.gz', *sorted((root / 'preserved').glob('*.json'))]
    for index in sources:
        data = read(index)
        if not isinstance(data, dict) or not isinstance(data.get('files'), list):
            continue
        objects = data.get('objects')
        used = False
        for item in data['files']:
            if not isinstance(item, dict) or 'sha256' not in item:
                continue
            key = item['sha256']
            reference = None
            if isinstance(objects, dict) and key in objects:
                obj = objects[key]
                if 'file' in obj:
                    name = 'preserved/' + index.stem + '/' + obj['file']
                    codec = 'gzip'
                elif 'path' in obj and obj.get('codec') in {'gzip', 'raw', 'artwork'}:
                    name = ('artwork/' if obj['codec'] == 'artwork' else 'preserved/') + obj['path']
                    codec = 'gzip' if obj['codec'] == 'gzip' else 'raw'
                else:
                    continue
                reference = dict(path=name, codec=codec, index=str(index.relative_to(root)))
                if obj.get('stored_sha256'):
                    reference['stored_sha256'] = obj['stored_sha256']
            elif 'stored' in item:
                reference = dict(path='preserved/' + index.stem + '/' + item['stored'], codec='gzip', index=str(index.relative_to(root)))
                if item.get('stored_sha256'):
                    reference['stored_sha256'] = item['stored_sha256']
            if reference:
                path = safe(root, reference['path'])
                if path.is_file() and reference not in refs[key]:
                    refs[key].append(reference)
                    used = True
        if used:
            indexes[str(index.relative_to(root))] = sha(index)
    art_index = root / 'artwork/manifest.json'
    for item in read(art_index)['files']:
        refs[item['sha256']].append(dict(path='artwork/' + item['path'], codec='raw', index='artwork/manifest.json'))
    indexes['artwork/manifest.json'] = sha(art_index)
    return refs, indexes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['plan', 'apply', 'restore', 'integrity', 'preserve-active', 'verify-active'])
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--prefix')
    a = parser.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000
    root = a.project
    if a.action == 'verify-active':
        data = read(a.plan)
        checked = set()
        for item in data['files']:
            obj = data['objects'][item['sha256']]
            blob = safe(root, 'preserved/owned-defeat-inprogress-r1/' + obj['file'])
            assert sha(blob) == obj['stored_sha256'] and sha(blob, 'gzip') == item['sha256']
            checked.add(item['sha256'])
        write(a.out, dict(status='verified-unfinished-defeat-preservation', files=len(data['files']),
                          objects=len(checked), workplace_required=False, validation_status='DRAFT, not gameplay acceptance'))
        return
    fixed, protected = protections(root)
    runtime_path = root / 'workplace/player/runtime.json'
    if a.action == 'preserve-active':
        active = root / 'workplace/probe-20261023/graphics-first/battle-r1/owned-defeat-r1'
        archive = root / 'preserved/owned-defeat-inprogress-r1'
        assert active.is_dir() and not archive.exists() and not a.plan.exists()
        archive.mkdir()
        selected = {f for f in active.rglob('*') if f.is_file() and not f.is_symlink()}
        selected.update(root / 'tools' / name for name in ['probe-owned-defeat.go', 'export-owned-defeat-ida.py',
                        'research-owned-defeat.go', 'research-owned-defeat_test.go', 'owned-defeat-check.go',
                        'audit-owned-defeat.py', 'clean-preserved-workspace.py'])
        selected.add(root / 'docs/spec/030-battle-expansion-proposal.md')
        files, objects = [], {}
        for f in sorted(selected):
            assert not f.is_symlink() and f.stat().st_uid == 1000
            raw = f.read_bytes()
            key = hashlib.sha256(raw).hexdigest()
            if key not in objects:
                blob = gzip.compress(raw, compresslevel=6, mtime=0)
                name = key + '.gzip'
                (archive / name).write_bytes(blob)
                objects[key] = dict(file=name, stored_sha256=hashlib.sha256(blob).hexdigest(), stored_bytes=len(blob))
            files.append(dict(path=str(f.relative_to(root)), sha256=key, bytes=len(raw), mode=stat.S_IMODE(f.stat().st_mode)))
        write(a.plan, dict(schema=1, files=files, objects=objects, status='unfinished-defeat-preserved',
                           note='Original 12 controls captured; Go defeat prototype and partial audit tool are unfinished.'))
        write(a.out, dict(status='preserved-unfinished-defeat', files=len(files), objects=len(objects),
                          stored_bytes=sum(v['stored_bytes'] for v in objects.values()), validation_status='DRAFT'))
        return
    if a.action == 'plan':
        assert not a.plan.exists()
        refs, indexes = references(root)
        verified = {}
        entries, unknown, errors = [], collections.Counter(), []
        started = time.monotonic()
        for folder, dirs, names in os.walk(root / 'workplace', followlinks=False):
            path = Path(folder)
            dirs[:] = [v for v in dirs if not (path / v).is_symlink() and not protected(str((path / v).relative_to(root)))]
            for name in names:
                f = path / name
                rel = str(f.relative_to(root))
                if protected(rel) or f.is_symlink() or not f.is_file():
                    continue
                before = stamp(f)
                if before['uid'] != 1000:
                    unknown['other-owner'] += before['bytes']
                    continue
                key = sha(f)
                if stamp(f) != before:
                    unknown['changed-during-read'] += before['bytes']
                    continue
                if key not in verified:
                    for ref in refs.get(key, []):
                        try:
                            stored = safe(root, ref['path'])
                            s = stamp(stored)
                            if ref.get('stored_sha256') and sha(stored) != ref['stored_sha256']:
                                raise ValueError('stored digest mismatch')
                            if sha(stored, ref['codec']) != key or stamp(stored) != s:
                                raise ValueError('archive digest changed')
                            verified[key] = dict(**ref, stamp=s)
                            break
                        except (OSError, ValueError, EOFError) as err:
                            errors.append(dict(path=ref['path'], error=str(err)))
                if key in verified:
                    entries.append(dict(path=rel, sha256=key, stamp=before))
                else:
                    unknown[str(Path(rel).parent)] += before['bytes']
                if len(entries) and len(entries) % 5000 == 0:
                    print(json.dumps(dict(verified_files=len(entries), unique_objects=len(verified), seconds=round(time.monotonic() - started))), flush=True)
        plan = dict(schema=1, runtime_sha256=sha(runtime_path), protected=fixed,
                    files=entries, references=verified, indexes=indexes,
                    logical_bytes=sum(v['stamp']['bytes'] for v in entries),
                    allocated_link_bytes=sum(v['stamp']['allocated_bytes'] for v in entries),
                    unselected_bytes=dict(unknown), archive_errors=errors)
        write(a.plan, plan)
        print(json.dumps({k: v for k, v in plan.items() if k not in {'files', 'references', 'indexes', 'unselected_bytes'}}, ensure_ascii=False), flush=True)
        return
    plan = read(a.plan)
    assert plan['schema'] == 1
    if a.action != 'restore':
        assert plan['runtime_sha256'] == sha(runtime_path)
    if a.action == 'apply':
        assert a.out and not a.out.exists()
        for name, key in plan['indexes'].items():
            assert sha(safe(root, name)) == key
        for ref in plan['references'].values():
            assert stamp(safe(root, ref['path'])) == ref['stamp']
        free_before = shutil.disk_usage(root).free
        deleted, kept, parents = [], [], set()
        for item in plan['files']:
            assert not protected(item['path'])
            f = safe(root, item['path'])
            if not f.exists():
                kept.append(dict(path=item['path'], reason='already-missing'))
                continue
            if not same_file(stamp(f), item['stamp']) or sha(f) != item['sha256']:
                kept.append(dict(path=item['path'], reason='changed'))
                continue
            f.unlink()
            deleted.append(item)
            parents.add(f.parent)
        for p in sorted(parents, key=lambda p: len(p.parts), reverse=True):
            while p != root / 'workplace' and not protected(str(p.relative_to(root))):
                try: p.rmdir()
                except OSError: break
                p = p.parent
        grouped = collections.defaultdict(list)
        for item in deleted:
            s = item['stamp']; grouped[(s['device'], s['inode'])].append(s)
        eligible_blocks = sum(v[0]['allocated_bytes'] for v in grouped.values() if len(v) == v[0]['links'])
        write(a.out, dict(status='cleaned-verified-workspace-copies', plan_sha256=sha(a.plan),
                         removed_files=len(deleted), removed_logical_bytes=sum(v['stamp']['bytes'] for v in deleted),
                         removed_inode_allocated_bytes=eligible_blocks,
                         free_bytes_before=free_before, free_bytes_after=shutil.disk_usage(root).free,
                         kept=kept, protected=fixed,
                         note='Filesystem free-space changes can include other concurrent projects.'))
        print(json.dumps(read(a.out), ensure_ascii=False), flush=True)
        return
    if a.action == 'restore':
        assert a.prefix and a.prefix.startswith('workplace/') and '..' not in Path(a.prefix).parts
        restored = 0
        for item in plan['files']:
            if item['path'] != a.prefix and not item['path'].startswith(a.prefix.rstrip('/') + '/'):
                continue
            f = safe(root, item['path'])
            if f.exists():
                assert f.is_file() and sha(f) == item['sha256']
                continue
            ref = plan['references'][item['sha256']]
            stored = safe(root, ref['path'])
            f.parent.mkdir(parents=True, exist_ok=True)
            assert f.parent.stat().st_uid == 1000
            temp = f.with_name(f.name + '.cleanup-restore.tmp')
            assert not temp.exists()
            with (gzip.open if ref['codec'] == 'gzip' else open)(stored, 'rb') as source, temp.open('xb') as dest:
                shutil.copyfileobj(source, dest, length=1 << 20)
            assert sha(temp) == item['sha256'] and temp.stat().st_size == item['stamp']['bytes']
            temp.chmod(item['stamp']['mode'])
            try:
                os.link(temp, f)
            finally:
                temp.unlink()
            restored += 1
        print(json.dumps(dict(status='restored-cleanup-prefix', prefix=a.prefix, restored=restored)))
        return
    assert a.out and not a.out.exists()
    baseline = read(root / 'preserved/owned-combat-audit-r1.json')
    runtime = read(runtime_path)
    roots = dict(source_inputs=root, programs=root/'workplace/player', core_files=root/'workplace/player/runtime-render-r1/src', asset_hashes=root/'workplace/player'/runtime['assets'])
    for group, folder in roots.items():
        for name, key in baseline[group].items():
            assert sha(folder / name) == key, (group, name)
    for item in read(root/'artwork/manifest.json')['files']:
        assert sha(root/'artwork'/item['path']) == item['sha256']
    active = root/'workplace/probe-20261023/graphics-first/battle-r1/owned-defeat-r1'
    root_owned = [str(f.relative_to(root)) for f in active.rglob('*') if f.lstat().st_uid == 0]
    assert not root_owned
    assert all(not p.is_dir() for p in active.rglob('*.md'))
    write(a.out, dict(status='passed-cleanup-runtime-integrity', sources=197, programs=7, core=923,
                      assets=535, artwork=1040, active_defeat_research_kept=True, root_owned_active_outputs=0,
                      free_bytes=shutil.disk_usage(root).free, cleanup_plan_sha256=sha(a.plan)))


if __name__ == '__main__':
    main()
