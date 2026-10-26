#!/usr/bin/env python3
"""053 READY：將已檢視END5五筆材質加入新候選，保留r57全部433檔。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
from PIL import Image, __version__


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('project','registration','out'):
        p.add_argument('--'+key,type=Path,required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    root = a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    base = a.project/'workplace/player/assets-painted-r57'
    before = json.loads((root/'ending-promotion-audit-r1.json').read_text())['asset_hashes']
    assert len(before) == len(list(base.iterdir())) == 433
    for name,digest in before.items():
        assert (base/name).is_file() and not (base/name).is_symlink() and sha(base/name) == digest
    registration = json.loads((a.registration/'registration.json').read_text())
    assert sha(a.registration/'registration.json') == 'ea768491f23e6d431dba658eb3bb59c334c742356433710d23facc2d8a075d5e'
    assert len(registration['records']) == 5 and registration['production'] is False
    a.out.mkdir()
    for name in before:
        shutil.copyfile(base/name,a.out/name)
    for record in registration['records']:
        name = record['file']
        assert Path(name).name == name and sha(a.registration/name) == record['sha256']
        im = Image.open(a.registration/name).convert('RGBA')
        assert list(im.size) == record['size'] and im.getchannel('A').getextrema() == (255,255)
        shutil.copyfile(a.registration/name,a.out/name)
    manifest = dict(schema=1,source_file='END5.AY',original_sha256='30451ddf5c325e27b7905e89cd34dc563c89ad0f4cced3a04835e7563632e2c0',records=registration['records'])
    (a.out/'ending-portrait.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    assert len(list(a.out.iterdir())) == 439
    report = dict(schema=1,spec='053',production=False,entries=439,preserved_files=433,
                  base_assets=base.name,base_hashes=before,records=registration['records'],
                  registration_sha256=sha(a.registration/'registration.json'),manifest_sha256=sha(a.out/'ending-portrait.json'),
                  tool_sha256=sha(Path(__file__)),rights='Full generated images, fonts and original game remain local.')
    with (a.out.parent/(a.out.name+'-preparation.json')).open('x') as f:
        f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(entries=439,manifest_sha256=report['manifest_sha256'])))


if __name__ == '__main__':
    main()
