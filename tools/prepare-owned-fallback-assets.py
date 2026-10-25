#!/usr/bin/env python3
"""047 DRAFT：建立兩份固定r49故障副本，原組與原版保持唯讀。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid()==1000
    assert not a.out.exists() and a.out.parent.stat().st_uid==1000
    source=a.project/'workplace/player/assets-painted-r49'
    expected=json.loads((a.project/'workplace/probe-20261023/graphics-first/battle-r1/troops-runtime-audit-r1.json').read_text())['asset_hashes']
    assert len(expected)==344 and {f.name for f in source.iterdir()}==set(expected)
    for name,sha in expected.items():assert digest(source/name)==sha,name
    a.out.mkdir()
    cases={}
    for name in ('missing','corrupt'):
        target=a.out/name
        target.mkdir()
        for file in source.iterdir():shutil.copy2(file,target/file.name)
        if name=='missing':
            changed='terrain.json'
            (target/changed).unlink()
        else:
            changed='grass-painted-r1.png'
            with (target/changed).open('ab') as f:f.write(b'\x00')
        actual={f.name:digest(f) for f in target.iterdir()}
        for file,sha in expected.items():
            if file!=changed:assert actual[file]==sha,(name,file)
        assert all(f.stat().st_uid==1000 for f in target.iterdir())
        cases[name]=dict(files=actual,changed=changed)
    result=dict(schema=1,production=False,base='assets-painted-r49',base_hashes=expected,cases=cases,
                tool_sha256=digest(Path(__file__)),scope='graphics group failure only; fonts/music unchanged')
    (a.out/'fixtures.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(out=str(a.out),cases={k:dict(files=len(v['files']),changed=v['changed']) for k,v in cases.items()})))


if __name__=='__main__':main()
