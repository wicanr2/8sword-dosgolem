#!/usr/bin/env python3
"""053：依獨立核對提升七程式與r57，保留r56及既有來源核心。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('project','player','audit','receipt'):
        p.add_argument('--'+key,type=Path,required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000
    assert a.player.stat().st_uid == 1000 and not a.receipt.exists()
    audit = json.loads(a.audit.read_text())
    assert audit['status'] == 'PASS-scoped-053-ending-engine'
    candidate = a.player/audit['candidate']
    previous = a.player/audit['previous']
    assets = a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1'/audit['assets']
    target = a.player/audit['target_assets']
    assert target.name == 'assets-painted-r57' and not target.exists()
    assert sha(candidate/'build-inputs.sha256') == audit['build_inputs_sha256']
    for name,digest in audit['programs'].items():
        assert Path(name).name == name and sha(candidate/name) == digest
        assert sha(previous/name) == sha(a.player/name) == audit['previous_programs'][name]
        assert (a.player/name).stat().st_uid == (candidate/name).stat().st_uid == 1000
    for name,digest in audit['asset_hashes'].items():
        assert Path(name).name == name and not (assets/name).is_symlink() and sha(assets/name) == digest
    stage = a.player/'.ending-assets-r57.tmp'
    assert not stage.exists()
    stage.mkdir()
    for name,digest in audit['asset_hashes'].items():
        shutil.copyfile(assets/name,stage/name)
        assert sha(stage/name) == digest
    assert len(list(stage.iterdir())) == 433
    os.rename(stage,target)
    staged = {}
    try:
        for name in audit['programs']:
            temp = a.player/('.ending-promote-'+name+'.tmp')
            assert not temp.exists()
            os.link(candidate/name,temp)
            staged[name] = temp
        metadata = {name:(candidate/name).read_bytes() for name in ['build-inputs.sha256','build-source-checks.log','build-go-version.txt']}
        runtime = json.loads((candidate/'runtime.json').read_text())
        runtime.update(production=True,spec='docs/spec/053-ending-hd.md',core_files=921,source_preparation_sha256=audit['runtime_sha256'])
        metadata['runtime.json'] = (json.dumps(runtime,indent=2)+'\n').encode()
        metadata['build-outputs.sha256'] = ''.join(f'{digest}  /out/{name}\n' for name,digest in audit['programs'].items()).encode()
        for name,data in metadata.items():
            temp = a.player/('.ending-promote-'+name+'.tmp')
            assert not temp.exists()
            temp.write_bytes(data)
            staged[name] = temp
        for name,temp in staged.items():
            os.replace(temp,a.player/name)
    finally:
        for temp in staged.values():
            if temp.exists(): temp.unlink()
    for name,digest in audit['programs'].items():
        assert sha(a.player/name) == digest and sha(previous/name) == audit['previous_programs'][name]
    report = dict(schema=1,status='promoted-scoped-053-ending-engine',assets=target.name,files=433,preserved_files=425,
                  candidate=candidate.name,previous=previous.name,programs=audit['programs'],previous_programs=audit['previous_programs'],
                  audit_sha256=sha(a.audit),source_inputs=150,core_files=921,previous_core_files=919,
                  prior_assets_unchanged=True,prior_core_unchanged=True,preparer_sha256=sha(Path(__file__)))
    with a.receipt.open('x') as f:
        f.write(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],assets=report['assets'],files=433)))


if __name__ == '__main__':
    main()
