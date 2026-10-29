#!/usr/bin/env python3
"""Permanent B VFX sources, binaries, original controls and actual GUI evidence."""
import argparse
import gzip
import hashlib
import json
import os
import pathlib


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--project', type=pathlib.Path)
    p.add_argument('--archive', type=pathlib.Path, required=True)
    p.add_argument('--out', type=pathlib.Path, required=True)
    p.add_argument('--verify', action='store_true')
    p.add_argument('--restore', type=pathlib.Path)
    a = p.parse_args()
    assert os.getuid() == 1000 and not a.out.exists()
    index = a.archive / 'vfx-engine-r1.json'
    storage = a.archive / 'vfx-engine-r1'
    if a.verify or a.restore:
        d = json.loads(index.read_text())
        assert d['status'] == 'preserved'
        checked = set()
        if a.restore:
            assert a.restore.is_dir() and not any(a.restore.iterdir())
        for v in d['files']:
            n = pathlib.PurePosixPath(v['path'])
            assert not n.is_absolute() and '..' not in n.parts
            obj = d['objects'][v['sha256']]
            blob = (storage / obj['file']).read_bytes()
            assert sha(blob) == obj['stored_sha256']
            raw = gzip.decompress(blob)
            assert sha(raw) == v['sha256'] and len(raw) == v['bytes']
            checked.add(v['sha256'])
            if a.restore:
                f = a.restore / n
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_bytes(raw)
                f.chmod(v['mode'])
        result = dict(status='passed', files=len(d['files']), objects=len(checked),
                      workplace_required=False, restored=bool(a.restore),
                      index_sha256=sha(index.read_bytes()))
    else:
        assert a.project and not index.exists() and not storage.exists()
        r = a.project
        q = r / 'workplace/probe-20261023/graphics-first/battle-r1/battle-vfx-r1'
        audit = q / 'engine-audit-r1.json'
        assert json.loads(audit.read_text())['status'] == 'passed-scoped-vfx-engine'
        old = json.loads((a.archive / 'battle-vfx-r1.json').read_text())
        previous = {v['path']: v['sha256'] for v in old['files']}
        selected = []
        reused = []
        for f in q.rglob('*'):
            if not f.is_file():
                continue
            assert not f.is_symlink()
            n = str(f.relative_to(r))
            if previous.get(n) == sha(f.read_bytes()):
                reused.append(n)
            else:
                selected.append(f)
        for revision in ['r1', 'r2']:
            root = r / ('workplace/player/source-candidate-vfx-' + revision)
            selected.extend(f for f in root.rglob('*') if f.is_file())
        for name in ['archive-vfx-engine.py', 'audit-vfx-engine.py', 'prepare-vfx-engine.py',
                     'prepare-vfx-gui.py', 'vfx-gui-probe.go', 'check-vfx-gui.sh',
                     'check-vfx-cold.sh', 'probe-battle-vfx.go', 'archive-approved-art.py']:
            selected.append(r / 'tools' / name)
        selected.append(r / 'docs/spec/030-battle-expansion-proposal.md')
        storage.mkdir()
        files, objects = [], {}
        for f in sorted(set(selected)):
            assert f.stat().st_uid == 1000 and not f.is_symlink()
            raw = f.read_bytes()
            h = sha(raw)
            if h not in objects:
                blob = gzip.compress(raw, compresslevel=6, mtime=0)
                name = h + '.gzip'
                (storage / name).write_bytes(blob)
                objects[h] = dict(file=name, stored_sha256=sha(blob), stored_bytes=len(blob))
            files.append(dict(path=str(f.relative_to(r)), sha256=h, bytes=len(raw),
                              mode=f.stat().st_mode & 0o777))
        d = dict(schema=1, status='preserved', files=files, objects=objects,
                 audit_sha256=sha(audit.read_bytes()), reused_prototype_paths=reused,
                 dependencies={
                     'prototype': 'preserved/battle-vfx-r1.json',
                     'approved_art': 'artwork/manifest.json',
                     'original_core_modules': 'preserved/catalog.json.gz',
                     'r68_assets': 'preserved/tactics-r1.json plus existing r65 catalogs',
                     'note': 'Restore prototype then this archive into one root; approved B complete PNGs are in artwork. No original workplace is required to verify this archive.'})
        index.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
        result = dict(status='preserved', files=len(files), objects=len(objects),
                      reused_prototype_files=len(reused),
                      stored_bytes=sum(v['stored_bytes'] for v in objects.values()))
    a.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
