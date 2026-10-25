#!/usr/bin/env python3
"""核對047候選收據，保留上一組程式後提升本機播放器。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--player', required=True, type=Path)
    ap.add_argument('--candidate', required=True)
    ap.add_argument('--previous', required=True)
    ap.add_argument('--audit', required=True, type=Path)
    ap.add_argument('--receipt', required=True, type=Path)
    a = ap.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000
    assert a.player.stat().st_uid == 1000 and not a.receipt.exists()
    for name in [a.candidate, a.previous]:
        assert re.fullmatch(r'[a-zA-Z0-9_-]+', name)
    candidate, previous = a.player/a.candidate, a.player/a.previous
    assert candidate.is_dir() and previous.is_dir()
    audit = json.loads(a.audit.read_text())
    assert audit['status'] == 'PASS-scoped-047-production-source-renderer'
    assert sha(candidate/'build-inputs.sha256') == audit['build_inputs_sha256']
    programs = audit['binaries']
    assert set(programs) == {'8sword', '8sword-replay', 'gui-check', 'music-check', 'heroine-check', 'museum-check', 'story-prelude-check'}
    old = {}
    for name, digest in programs.items():
        src, target = candidate/name, a.player/name
        assert src.stat().st_uid == target.stat().st_uid == 1000
        assert sha(src) == digest and src.stat().st_mode & 0o111
        old[name] = sha(target)
        assert sha(previous/name) == old[name], '上一組程式必須先有完整保存'
    files = {name: (candidate/name).read_bytes() for name in programs}
    for name in ['build-inputs.sha256', 'build-source-checks.log', 'build-go-version.txt', 'runtime.json']:
        files[name] = (candidate/name).read_bytes()
    files['build-outputs.sha256'] = ''.join(f'{digest}  /out/{name}\n' for name, digest in programs.items()).encode()
    staged = {}
    try:
        for name, data in files.items():
            temp = a.player/('.source-promote-'+name+'.tmp')
            assert not temp.exists()
            if name in programs:
                os.link(candidate/name, temp)
            else:
                with temp.open('xb') as f:
                    f.write(data)
            staged[name] = temp
        for name, temp in staged.items():
            os.replace(temp, a.player/name)
    finally:
        for temp in staged.values():
            if temp.exists():
                temp.unlink()
    for name, digest in programs.items():
        assert sha(a.player/name) == digest and sha(previous/name) == old[name]
    receipt = dict(schema=1, status='promoted-scoped-047-source-renderer',
                   candidate=a.candidate, previous=a.previous, previous_programs=old,
                   programs=programs, audit_sha256=sha(a.audit), assets_changed=False,
                   preparer_sha256=sha(Path(__file__)))
    with a.receipt.open('x') as f:
        f.write(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(dict(status=receipt['status'], programs=len(programs), previous=a.previous)))


if __name__ == '__main__':
    main()
