#!/usr/bin/env python3
"""053：整理END6四張原版／HD及同狀態結局代表，完整原圖留本機。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['project','audit','out']: p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid()==1000
    assert not a.out.exists() and a.out.parent.stat().st_uid==1000
    audit=json.loads(a.audit.read_text()); assert audit['status']=='PASS-scoped-053-ending-pair'
    root=a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    assets=root/audit['assets']; manifest=json.loads((assets/'ending-pair.json').read_text())
    sources={r['record']:r for r in json.loads((root/'source.json').read_text())['records'] if r['source_file']=='END6.AY'}
    fontpath=a.project/'workplace/probe-20261023/graphics-first/font-settings-r1/NotoSansCJK-Black.ttc'
    assert sha(fontpath)=='3cffb10242b4b7e6edd439ebf3bd7e392345525e093ea08149e0a0158a1b5151'
    title=ImageFont.truetype(str(fontpath),24,index=3); small=ImageFont.truetype(str(fontpath),17,index=3)
    out=Image.new('RGB',(1280,730),'#111722'); d=ImageDraw.Draw(out)
    d.text((20,12),'END6雙人縮小動畫／原版與HD',font=title,fill='#ead4a0')
    entries=[]
    for i,row in enumerate(manifest['records']):
        x=i*320; d.text((x+12,58),f'第{row["record"]}筆／原位置與縮小比例',font=small,fill='#ead4a0')
        for column,label,path in [(0,'原版',root/sources[row['record']]['image']),(1,'HD',assets/row['image'])]:
            d.text((x+12+column*156,88),label,font=small,fill='#d5dbea')
            im=Image.open(path).convert('RGBA')
            if column==0: im=im.resize((408,300),Image.Resampling.NEAREST)
            im=ImageOps.contain(im,(148,128),Image.Resampling.NEAREST if column==0 else Image.Resampling.LANCZOS)
            tile=Image.new('RGBA',(148,132),(0,0,0,255));tile.alpha_composite(im,((148-im.width)//2,(132-im.height)//2))
            out.paste(tile.convert('RGB'),(x+8+column*156,116))
            entries.append(dict(record=row['record'],kind=label,image=str(path.relative_to(a.project)),sha256=sha(path)))
    d.text((20,270),'同一張手繪定稿，按四筆原始bbox縮放；黑色遮罩與透明背景保持',font=small,fill='#d5dbea')
    sample=next(v for v in audit['frames'] if v['stage']=='END6.AY' and v['font']=='noto')
    hd=a.project/sample['image']; native=hd.with_name(hd.name.replace('-noto.png','-native.png'))
    assert sha(hd)==sample['image_sha256']
    for x,label,path in [(20,'相同狀態／原版來源重建',native),(660,'Go實際畫布／雙人HD',hd)]:
        d.text((x,310),label,font=title,fill='#ead4a0')
        out.paste(Image.open(path).convert('RGB').resize((600,375),Image.Resampling.LANCZOS),(x,355))
        entries.append(dict(kind=label,image=str(path.relative_to(a.project)),sha256=sha(path)))
    out.save(a.out)
    generations={}
    for version in ['r1','r2']:
        gp=root/'end6-pair-art-r1'/('generation-'+version+'.json'); record=json.loads(gp.read_text())
        generations[version]=dict(record,prompt_text=(gp.parent/record['prompt']).read_text())
    report=dict(schema=1,spec='053',image=a.out.name,image_sha256=sha(a.out),audit_sha256=sha(a.audit),entries=entries,
                generations=generations,selected='r2',tool_sha256=sha(Path(__file__)),
                scope='Four registered textures plus one verified END6 Engine frame. Controlled original ending branch; no new GUI/save or natural victory claim. Full generated PNGs remain local.')
    a.out.with_suffix('.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(sha(a.out))


if __name__=='__main__': main()
