#!/usr/bin/env python3
"""053：依獨立核對提升七程式與素材，保留前版及既有來源核心。"""
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
    variants = {
        'PASS-scoped-053-ending-engine': ('r57',433,425,150,919),
        'PASS-scoped-053-ending-portrait': ('r58',439,433,152,921),
        'PASS-scoped-053-ending-swords': ('r60',441,439,154,921),
        'PASS-scoped-053-ending-duel': ('r61',443,441,156,921),
        'PASS-scoped-053-ending-effects': ('r62',455,443,158,921),
        'PASS-scoped-053-ending-pair': ('r63',460,455,173,923),
    }
    assert audit['status'] in variants
    version, count, preserved, inputs, previous_core = variants[audit['status']]
    core_count = 923 if audit['status'] == 'PASS-scoped-053-ending-pair' else 921
    candidate = a.player/audit['candidate']
    previous = a.player/audit['previous']
    assets = a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1'/audit['assets']
    target = a.player/audit['target_assets']
    assert target.name == 'assets-painted-'+version and not target.exists()
    assert sha(candidate/'build-inputs.sha256') == audit['build_inputs_sha256']
    for name,digest in audit['programs'].items():
        assert Path(name).name == name and sha(candidate/name) == digest
        assert sha(previous/name) == sha(a.player/name) == audit['previous_programs'][name]
        assert (a.player/name).stat().st_uid == (candidate/name).stat().st_uid == 1000
    for name,digest in audit['asset_hashes'].items():
        assert Path(name).name == name and not (assets/name).is_symlink() and sha(assets/name) == digest
    stage = a.player/('.ending-assets-'+version+'.tmp')
    assert not stage.exists()
    stage.mkdir()
    for name,digest in audit['asset_hashes'].items():
        shutil.copyfile(assets/name,stage/name)
        assert sha(stage/name) == digest
    assert len(list(stage.iterdir())) == count
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
        runtime.update(production=True,spec='docs/spec/053-ending-hd.md',core_files=core_count,source_preparation_sha256=audit['runtime_sha256'])
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
    report = dict(schema=1,status=audit['status'].replace('PASS-','promoted-',1),assets=target.name,files=count,preserved_files=preserved,
                  candidate=candidate.name,previous=previous.name,programs=audit['programs'],previous_programs=audit['previous_programs'],
                  audit_sha256=sha(a.audit),source_inputs=inputs,core_files=core_count,previous_core_files=previous_core,
                  prior_assets_unchanged=True,prior_core_unchanged=True,preparer_sha256=sha(Path(__file__)))
    with a.receipt.open('x') as f:
        f.write(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],assets=report['assets'],files=count)))


if __name__ == '__main__':
    main()
