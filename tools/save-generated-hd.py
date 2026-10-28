#!/usr/bin/env python3
"""054：保存內建image_gen完整PNG、實際提示與參考，不覆寫既有定稿。Docker only。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
from PIL import Image, __version__


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['project','archive','request','image']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();assert Path('/.dockerenv').is_file() and os.getuid()==1000 and __version__=='11.3.0'
    request=json.loads(a.request.read_text());name=request['name'];assert re.fullmatch(r'[a-z0-9-]+',name)
    assert a.image.is_file() and a.archive.stat().st_uid==1000
    target=a.archive/'approved/masters/all-graphics-hd-r1'/(name+'.png')
    meta=a.archive/'approved/provenance/all-graphics-hd-r1';meta.mkdir(parents=True,exist_ok=True)
    assert not target.exists() and not (meta/(name+'.json')).exists()
    shutil.copyfile(a.image,target)
    assert sha(target)==sha(a.image)
    prompt=meta/(name+'.prompt.txt');assert not prompt.exists();prompt.write_text(request['prompt'])
    refs=[]
    for i,path in enumerate(request['references']):
        src=a.project/path;assert src.is_file()
        if path.startswith('artwork/approved/'):
            permanent=path.removeprefix('artwork/')
        else:
            dst=a.archive/'approved/references/all-graphics-hd-r1/generated'/(name+f'-ref-{i+1}.png')
            dst.parent.mkdir(parents=True,exist_ok=True);assert not dst.exists();shutil.copyfile(src,dst)
            permanent=str(dst.relative_to(a.archive))
        refs.append(dict(source=path,path=permanent,sha256=sha(src)))
    with Image.open(target) as raw:
        im=raw.convert('RGBA');size=list(im.size);alpha=list(im.getchannel('A').getextrema())
    report=dict(schema=1,spec='054',name=name,tool='built-in image_gen',scope=request['scope'],status='art-prepared-not-production',image=str(target.relative_to(a.archive)),image_sha256=sha(target),size=size,alpha_extrema=alpha,prompt=str(prompt.relative_to(a.archive)),prompt_sha256=sha(prompt),references=refs,default_generated_image=request['default_generated_image'],tool_sha256=sha(Path(__file__)))
    receipt=meta/(name+'.json');receipt.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    index=a.archive/'hd-additions-r1.json'
    data=json.loads(index.read_text()) if index.exists() else dict(schema=1,spec='054',images=[])
    assert not any(r['name']==name for r in data['images'])
    data['images'].append(dict(name=name,receipt=str(receipt.relative_to(a.archive)),receipt_sha256=sha(receipt),**{k:report[k] for k in ['image','image_sha256','prompt','prompt_sha256','size','alpha_extrema','scope','status']}))
    index.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(name=name,image=report['image'],sha256=sha(target),size=size,alpha=alpha)))


if __name__=='__main__':main()
