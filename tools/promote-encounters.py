#!/usr/bin/env python3
"""049：核對獨立收據後提升本機七程式與r50，保留全部舊版。Docker only。"""
import argparse
import hashlib
import json
import os
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('player', 'audit', 'receipt'):
        p.add_argument('--' + key, type=Path, required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000
    assert a.player.stat().st_uid == 1000 and not a.receipt.exists()
    audit = json.loads(a.audit.read_text())
    assert audit['status'] == 'PASS-scoped-049-map-encounter-batch'
    candidate = a.player / 'source-candidate-encounters-r1'
    assets = a.player / 'assets-encounters-candidate-r2'
    previous = a.player / 'source-candidate-r4'
    target = a.player / 'assets-painted-r50'
    assert not target.exists()
    assert sha(candidate / 'build-inputs.sha256') == audit['build_inputs_sha256']
    programs = audit['programs']
    assert set(programs) == {'8sword', '8sword-replay', 'gui-check', 'music-check', 'heroine-check', 'museum-check', 'story-prelude-check'}
    for name, digest in programs.items():
        assert sha(candidate / name) == digest
        assert sha(previous / name) == sha(a.player / name) == audit['previous_programs'][name]
        assert (candidate / name).stat().st_uid == (a.player / name).stat().st_uid == 1000
    assert len(list(assets.iterdir())) == len(audit['asset_hashes']) == 367
    for name, digest in audit['asset_hashes'].items():
        assert Path(name).name == name and sha(assets / name) == digest
        assert (assets / name).stat().st_uid == 1000 and not (assets / name).is_symlink()
    stage = a.player / '.encounters-assets-r50.tmp'
    assert not stage.exists()
    stage.mkdir()
    for name in audit['asset_hashes']:
        os.link(assets / name, stage / name)
    for name, digest in audit['asset_hashes'].items():
        assert sha(stage / name) == digest
    os.rename(stage, target)
    staged = {}
    try:
        for name in programs:
            temp = a.player / ('.encounters-promote-' + name + '.tmp')
            assert not temp.exists()
            os.link(candidate / name, temp)
            staged[name] = temp
        metadata = {name: (candidate / name).read_bytes() for name in ['build-inputs.sha256', 'build-source-checks.log', 'build-go-version.txt', 'runtime.json']}
        metadata['build-outputs.sha256'] = ''.join(f'{digest}  /out/{name}\n' for name, digest in programs.items()).encode()
        for name, data in metadata.items():
            temp = a.player / ('.encounters-promote-' + name + '.tmp')
            assert not temp.exists()
            with temp.open('xb') as f:
                f.write(data)
            staged[name] = temp
        for name, temp in staged.items():
            os.replace(temp, a.player / name)
    finally:
        for temp in staged.values():
            if temp.exists():
                temp.unlink()
    for name, digest in programs.items():
        assert sha(a.player / name) == digest
        assert sha(previous / name) == audit['previous_programs'][name]
    report = dict(schema=1, status='promoted-scoped-049-map-encounters', assets=target.name,
                  files=367, preserved_files=344, candidate=candidate.name, previous=previous.name,
                  programs=programs, previous_programs=audit['previous_programs'], audit_sha256=sha(a.audit),
                  prior_assets_unchanged=True, prior_core_unchanged=True, preparer_sha256=sha(Path(__file__)))
    with a.receipt.open('x') as f:
        f.write(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ['status', 'assets', 'files', 'preserved_files']}))


if __name__ == '__main__':
    main()
