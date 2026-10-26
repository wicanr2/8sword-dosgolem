#!/usr/bin/env python3
"""053：整理紅金光環原版／HD與同狀態實際Go畫布。Docker only。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ['project','audit','out']: p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid()==1000
    assert not a.out.exists() and a.out.parent.stat().st_uid==1000
    audit=json.loads(a.audit.read_text()); assert audit['status']=='PASS-scoped-053-ending-ring'
    root=a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1'; assets=root/audit['assets']
    manifest=json.loads((assets/'ending-ring.json').read_text())
    fontpath=a.project/'workplace/probe-20261023/graphics-first/font-settings-r1/NotoSansCJK-Black.ttc'
    assert sha(fontpath)=='3cffb10242b4b7e6edd439ebf3bd7e392345525e093ea08149e0a0158a1b5151'
    title=ImageFont.truetype(str(fontpath),25,index=3); small=ImageFont.truetype(str(fontpath),18,index=3)
    out=Image.new('RGB',(1280,870),'#111722'); d=ImageDraw.Draw(out)
    d.text((20,12),'END3紅金光環／原版與HD',font=title,fill='#ead4a0')
    entries=[]
    for x,label,path,original in [(20,'原版來源',root/'end3-ay-01-native.png',True),(660,'HD透明手繪',assets/manifest['image'],False)]:
        d.text((x,56),label,font=title,fill='#ead4a0')
        im=Image.open(path).convert('RGBA')
        if original: im=im.resize((696,630),Image.Resampling.NEAREST)
        im=ImageOps.contain(im,(340,308),Image.Resampling.NEAREST if original else Image.Resampling.LANCZOS)
        tile=Image.new('RGBA',(600,308),(0,0,0,255)); tile.alpha_composite(im,((600-im.width)//2,(308-im.height)//2))
        out.paste(tile.convert('RGB'),(x,98))
        entries.append(dict(kind=label,image=str(path.relative_to(a.project)),sha256=sha(path)))
    d.text((20,420),'保留外紅內粉、透明環隙與中央金光；沿原版命令直接由Go混合',font=small,fill='#d5dbea')
    frame=next(v for v in audit['frames'] if v['font']=='noto'); hd=a.project/frame['image']
    assert sha(hd)==frame['image_sha256']
    native=hd.with_name(hd.name.replace('-noto.png','-native.png'))
    for x,label,path in [(20,'相同狀態／原版來源重建',native),(660,'相同狀態／實際Go HD畫布',hd)]:
        d.text((x,450),label,font=title,fill='#ead4a0')
        out.paste(Image.open(path).convert('RGB').resize((600,375),Image.Resampling.LANCZOS),(x,495))
        entries.append(dict(kind=label,image=str(path.relative_to(a.project)),sha256=sha(path)))
    out.save(a.out)
    gp=root/'end3-ring-art-r1/generation-r1.json'; generation=json.loads(gp.read_text())
    report=dict(schema=1,spec='053',image=a.out.name,image_sha256=sha(a.out),audit_sha256=sha(a.audit),entries=entries,generation=dict(generation,prompt_text=(gp.parent/generation['prompt']).read_text()),tool_sha256=sha(Path(__file__)),scope='One registered ring texture and one verified END3 Engine frame. Controlled ending branch, no new GUI/save or natural victory claim. Full PNG remains local.')
    a.out.with_suffix('.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(sha(a.out))


if __name__=='__main__': main()
