#!/usr/bin/env python3
"""014 批准背景匯入。原圖與既有素材唯讀，僅寫新組；在 Docker 執行。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from PIL import Image, __version__

def sha(b):
    return hashlib.sha256(b).hexdigest()

def main():
    p=argparse.ArgumentParser()
    for n in ('base','approved','out'):
        p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args()
    assert a.out.is_dir() and a.out.stat().st_uid==1000 and not any(a.out.iterdir())
    assert __version__=='11.3.0'
    raw=a.approved.read_bytes()
    approved_sha='bd21a34613dabef939afc9b94c9f45473cef2cd5f0e42aeee660d3d02b6d5c04'
    assert sha(raw)==approved_sha
    before={str(q.relative_to(a.base)):sha(q.read_bytes()) for q in a.base.rglob('*') if q.is_file()}
    assert 'story.json' in before and 'story-background.json' not in before
    im=Image.open(a.approved).convert('RGBA')
    assert im.size==(1586,992) and im.getchannel('A').getextrema()==(255,255)
    shutil.copytree(a.base,a.out,dirs_exist_ok=True)
    im.resize((1920,1200),Image.Resampling.LANCZOS).save(a.out/'story-background.png')
    png_sha=sha((a.out/'story-background.png').read_bytes())
    assert png_sha=='734df8241381d2d016bb6c7421d8ce38b3dec2f7f91bdb0f7589b7d45b58ecbf'
    m=dict(schema=1,source_sha256='2df60e86386ebbea78d307fe620f426c6ff9cb8f34551c689a9343c5af13baa2',approved_sha256=approved_sha,image='story-background.png',image_sha256=png_sha,width=1920,height=1200,rights='local-only original-derived HD artwork; no public distribution permission')
    (a.out/'story-background.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
    (a.out/'story-background-import.json').write_text(json.dumps(dict(approved_file=a.approved.name,approved_sha256=approved_sha,pillow=__version__,resize='Lanczos full-frame, no crop',base_files=before,manifest_sha256=sha((a.out/'story-background.json').read_bytes()),rights=m['rights']),ensure_ascii=False,indent=2)+'\n')
    assert all(sha((a.out/n).read_bytes())==h for n,h in before.items())
    assert all(q.stat().st_uid==1000 for q in a.out.rglob('*'))
    print(json.dumps(dict(preserved=len(before),added=3,image_sha256=png_sha)))

if __name__=='__main__':
    main()
