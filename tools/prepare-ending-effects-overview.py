#!/usr/bin/env python3
"""053：整理11筆效果原版／HD與正常爆光代表Frame。Docker only。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps, __version__


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ['project','audit','out']:
        p.add_argument('--'+key,type=Path,required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid()==1000 and __version__=='11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid==1000
    audit=json.loads(a.audit.read_text());assert audit['status']=='PASS-scoped-053-ending-effects'
    root=a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    assets=root/'assets-effects-candidate-r1'
    records=json.loads((assets/'ending-effects.json').read_text())['records']
    sources={v['record']:v for v in json.loads((root/'source.json').read_text())['records'] if v['source_file']=='END2.AY'}
    fontpath=a.project/'workplace/probe-20261023/graphics-first/font-settings-r1/NotoSansCJK-Black.ttc'
    assert sha(fontpath)=='3cffb10242b4b7e6edd439ebf3bd7e392345525e093ea08149e0a0158a1b5151'
    font=ImageFont.truetype(str(fontpath),22,index=3);small=ImageFont.truetype(str(fontpath),17,index=3)
    out=Image.new('RGB',(1280,1110),'#111722');draw=ImageDraw.Draw(out)
    draw.text((20,10),'END2法術效果／11筆原版與HD',font=font,fill='#ead4a0')
    entries=[]
    for row in records:
        i=row['record'];x,y=i%4*320,48+i//4*200
        label='腳下火焰' if i<3 else '曲線光流／僅素材' if i<6 else '爆光'
        draw.text((x+12,y+8),f'{i:02d}／'+label,font=small,fill='#ead4a0')
        for column,caption,path in [(0,'原版',root/sources[i]['image']),(1,'HD',assets/row['image'])]:
            draw.text((x+12+column*156,y+38),caption,font=small,fill='#d5dbea')
            im=Image.open(path).convert('RGBA')
            if column==0:im=im.resize((row['width'],row['height']),Image.Resampling.NEAREST)
            im=ImageOps.contain(im,(140,124),Image.Resampling.NEAREST if column==0 else Image.Resampling.LANCZOS)
            tile=Image.new('RGBA',(148,128),(0,0,0,255));tile.alpha_composite(im,((148-im.width)//2,(128-im.height)//2))
            out.paste(tile.convert('RGB'),(x+8+column*156,y+65))
            entries.append(dict(record=i,kind=caption,path=str(path.relative_to(a.project)),sha256=sha(path)))
    draw.text((972,478),'第3–5筆僅完成素材與載入',font=small,fill='#d5dbea')
    draw.text((972,510),'未聲明正常使用或自然通關',font=small,fill='#d5dbea')
    sample=next(v for v in audit['frames'] if v['stage']=='END2.AY' and v['font']=='noto')
    hd=a.project/sample['image'];native=hd.with_name(hd.name.replace('-noto.png','-native.png'))
    assert sha(hd)==sample['image_sha256']
    for x,label,path in [(20,'相同狀態／原版來源重建',native),(660,'Go實際畫布／依原版順序累積',hd)]:
        draw.text((x,668),label,font=font,fill='#ead4a0')
        out.paste(Image.open(path).convert('RGB').resize((600,375),Image.Resampling.LANCZOS),(x,714))
        entries.append(dict(kind=label,path=str(path.relative_to(a.project)),sha256=sha(path)))
    out.save(a.out)
    generations={}
    for name,version in [('ground','r1'),('flow','r1'),('burst','r1'),('burst','r2'),('burst','r3')]:
        gp=root/'effects-art-r1'/(name+'-generation-'+version+'.json');gen=json.loads(gp.read_text())
        generations[name+'-'+version]=dict(gen,prompt_text=(gp.parent/gen['prompt']).read_text())
    report=dict(schema=1,spec='053',image=a.out.name,image_sha256=sha(a.out),audit_sha256=sha(a.audit),
                entries=entries,generations=generations,tool_sha256=sha(Path(__file__)),
                scope='Eleven textures plus one verified source/HD Engine Frame. Records3-5 have no normal-use claim. Controlled original ending branch; no new GUI/save or natural-victory claim.')
    with a.out.with_suffix('.json').open('x') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(sha(a.out))


if __name__=='__main__':
    main()
