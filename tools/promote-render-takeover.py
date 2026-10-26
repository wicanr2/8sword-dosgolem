#!/usr/bin/env python3
"""047：依獨立核對原子提升七程式，素材455檔與前版保持。"""
import argparse
import hashlib
import json
import os
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['project','player','audit','receipt']:
        p.add_argument('--'+name,required=True,type=Path)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == a.player.stat().st_uid == 1000
    assert not a.receipt.exists()
    audit = json.loads(a.audit.read_text())
    assert audit['status'] == 'PASS-scoped-047-native-render' and audit['source_input_count'] == 168 and audit['core_files'] == 923
    candidate,previous = a.player/audit['candidate'],a.player/audit['previous']
    assert sha(candidate/'build-inputs.sha256') == audit['build_inputs_sha256'] and sha(candidate/'runtime.json') == audit['runtime_sha256']
    for name,digest in audit['programs'].items():
        assert Path(name).name == name and sha(candidate/name) == digest
        assert sha(previous/name) == sha(a.player/name) == audit['previous_programs'][name]
        assert (candidate/name).stat().st_uid == (a.player/name).stat().st_uid == 1000
    for name,digest in audit['source_inputs'].items():
        assert sha(a.project/name) == sha(candidate/'src'/name) == digest
    for name,digest in audit['receipts'].items():
        assert sha(a.project/name) == digest
    for name,digest in audit['asset_hashes'].items():
        assert sha(a.player/audit['assets']/name) == digest
    staged = {}
    try:
        for name in audit['programs']:
            tmp = a.player/('.render-promote-'+name+'.tmp')
            assert not tmp.exists()
            os.link(candidate/name,tmp);staged[name] = tmp
        metadata = {name:(candidate/name).read_bytes() for name in ['build-inputs.sha256','build-source-checks.log','build-go-version.txt']}
        runtime = json.loads((candidate/'runtime.json').read_text())
        runtime.update(production=True,spec='docs/spec/047-hd-scene-renderer.md',core_files=923,
                       source_preparation_sha256=audit['runtime_sha256'])
        metadata['runtime.json'] = (json.dumps(runtime,indent=2)+'\n').encode()
        metadata['build-outputs.sha256'] = ''.join(f'{digest}  /out/{name}\n' for name,digest in audit['programs'].items()).encode()
        for name,data in metadata.items():
            tmp = a.player/('.render-promote-'+name+'.tmp')
            assert not tmp.exists();tmp.write_bytes(data);staged[name] = tmp
        for name,tmp in staged.items():
            os.replace(tmp,a.player/name)
    finally:
        for tmp in staged.values():
            if tmp.exists():tmp.unlink()
    for name,digest in audit['programs'].items():
        assert sha(a.player/name) == digest and sha(previous/name) == audit['previous_programs'][name]
    result = dict(schema=1,status='promoted-scoped-047-native-render',candidate=candidate.name,previous=previous.name,
        programs=audit['programs'],previous_programs=audit['previous_programs'],source_inputs=168,core_files=923,
        preserved_core_files=921,assets=audit['assets'],asset_files=455,audit_sha256=sha(a.audit),tool_sha256=sha(Path(__file__)))
    a.receipt.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],programs=7,core_files=923,assets=455)))


if __name__ == '__main__':
    main()
