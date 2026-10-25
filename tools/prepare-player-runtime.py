#!/usr/bin/env python3
"""依047固定來源重建正式播放器核心，保留既有核心與研究副本。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify(root, out, pin):
    manifest = json.loads((out / 'runtime-manifest.json').read_text())
    base = manifest['base_inputs']
    assert len(base) == pin['base_files']
    assert digest(json.dumps(base, sort_keys=True, separators=(',', ':')).encode()) == pin['base_tree_sha256']
    assert manifest['changed'] == pin['changed']
    assert digest((out / 'runtime.patch').read_bytes()) == pin['reference_patch_sha256']
    expected = base | pin['changed']
    actual = {str(p.relative_to(out / 'src')): digest(p.read_bytes())
              for p in (out / 'src').rglob('*') if p.is_file()}
    assert actual == expected, '核心來源與固定清單不同'
    for name, sha in base.items():
        assert digest((root / 'workplace/dosgolem' / name).read_bytes()) == sha
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    root, out = args.project, args.out
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000
    assert out.parent.is_dir() and out.parent.stat().st_uid == os.getuid()
    pin = json.loads((root / 'tools/player-runtime-source.json').read_text())
    if not out.exists():
        subprocess.run(['python3', str(root / 'tools/prepare-direct-runtime.py'),
                        '--project', str(root), '--out', str(out), '--masked-planar'], check=True)
    manifest = verify(root, out, pin)
    receipt = out / 'player-runtime.json'
    data = {'schema': 1, 'production': True, 'spec': pin['spec'],
            'base_tree_sha256': pin['base_tree_sha256'],
            'core_files': len(manifest['base_inputs'] | manifest['changed']),
            'changed': pin['changed'], 'preparer_sha256': digest(Path(__file__).read_bytes())}
    if receipt.exists():
        assert json.loads(receipt.read_text()) == data
    else:
        with receipt.open('x') as f:
            f.write(json.dumps(data, indent=2) + '\n')
    print(json.dumps({'runtime': str(out), 'verified': True, 'core_files': data['core_files']}))


if __name__ == '__main__':
    main()
