#!/usr/bin/env python3
"""016：從固定 TIT1 與字型建立發行商字圖。在 Docker 執行。"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import struct
from PIL import Image,ImageDraw,ImageFont,ImageChops,__version__

SOURCE='8e971808ea94931ceb3ba78f3d1918984290584bd592d13ce7d081dfb08a34ac'
DECODED='d0bcfa366f8d8c13745c253fbeef1a04691aad24d4a5718cebd9645c17fc1308'
MASK='7c6f7c1719915f4ddee9ac2d03938e42654c45777a3236c58b1ee3ea89a90985'
FIELDS=[('軟體',(273,642,729,840),170),('世界',(1212,648,1626,840),170),('C&P',(195,942,450,1044),86),('智冠股份有限公司',(471,840,1425,1068),110),('1991',(1425,942,1665,1044),86)]
FONTS={'noto':('NotoSansCJK-Black.ttc','3cffb10242b4b7e6edd439ebf3bd7e392345525e093ea08149e0a0158a1b5151'),'lishu':('UnYetgul.ttf','c9d42eaac473b8ab0461cc6c2d1a1bac79b0babdf73974c7269ae17b81fd5d51'),'caoshu':('LiuJianMaoCao-Regular.ttf','cab396b91a5b7c0b4005a35891180d06e6751f5ac261fe680aec65c1ae209033'),'serif':('NotoSerifCJK-Regular.ttc','93069d8e9e45d515cc421c971a79e6a5777704b348e36a9ef86578bf58adef77')}
def sha(b):return hashlib.sha256(b).hexdigest()

def build(a):
    assert __version__=='11.3.0' and a.out.is_dir() and a.out.stat().st_uid==1000 and not any(a.out.iterdir())
    assert sha(a.source.read_bytes())==SOURCE
    spec=importlib.util.spec_from_file_location('intro',Path(__file__).with_name('prepare-hd-intro.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    data=module.decode(a.source.read_bytes());assert sha(data)==DECODED and struct.unpack_from('<HH',data)==(63,160)
    idx=bytearray(640*200)
    for y in range(160):
        for x in range(504):idx[(y+20)*640+x+64]=sum(((data[4+plane*63*160+y*63+x//8]>>(7-x%8))&1)<<plane for plane in range(4))
    assert sha(idx)=='dfebfbd028187e9022d45743d40ab1d38f209ebd3ffd589149585a1a54459d9e'
    alive={i for i,v in enumerate(idx) if v};mask=Image.new('L',(640,200));icon=Image.new('L',(640,200));icon_count=0
    while alive:
        first=alive.pop();stack=[first];points=[]
        while stack:
            i=stack.pop();points.append(i);x,y=i%640,i//640
            for yy in range(max(0,y-1),min(200,y+2)):
                for xx in range(max(0,x-1),min(640,x+2)):
                    at=yy*640+xx
                    if at in alive:alive.remove(at);stack.append(at)
        bbox=(min(i%640 for i in points),min(i//640 for i in points),max(i%640 for i in points)+1,max(i//640 for i in points)+1)
        is_icon=bbox in ((295,20,347,36),(219,37,425,138));icon_count+=int(is_icon)
        for i in points:(icon if is_icon else mask).putpixel((i%640,i//640),255)
    assert icon_count==2 and sha(mask.tobytes())==MASK
    for name,h in FONTS.values():assert sha((a.fonts/name).read_bytes())==h
    before={str(p.relative_to(a.base)):sha(p.read_bytes()) for p in a.base.rglob('*') if p.is_file()}
    assert 'font-choices.json' in before and 'publisher.json' not in before
    shutil.copytree(a.base,a.out,dirs_exist_ok=True);mask.save(a.out/'publisher-erase.png')
    icon=icon.resize((1920,1200),Image.Resampling.NEAREST);words=[]
    for ident in ('noto','lishu','caoshu'):
        overlay=Image.new('RGBA',(1920,1200));fallback=[]
        for text,(x0,y0,x1,y1),px in FIELDS:
            w,h=x1-x0,y1-y0;cell=w//len(text);group=Image.new('L',(w,h))
            for i,c in enumerate(text):
                font=ImageFont.truetype(str(a.fonts/FONTS[ident][0]),px,index=3 if ident=='noto' else 0)
                missing=font.getmask('\U0010ffff');m=font.getmask(c)
                if ident!='noto' and (not 0x3400<=ord(c)<=0x9fff or (m.size,bytes(m))==(missing.size,bytes(missing)) or not m.getbbox()):
                    font=ImageFont.truetype(str(a.fonts/FONTS['serif' if 0x3400<=ord(c)<=0x9fff else 'noto'][0]),px,index=3);fallback.append(c)
                b=font.getbbox(c);glyph=Image.new('L',(b[2]-b[0],b[3]-b[1]));ImageDraw.Draw(glyph).text((-b[0],-b[1]),c,font=font,fill=255);assert glyph.getbbox()
                glyph.thumbnail((cell-14,h-14),Image.Resampling.LANCZOS);group.paste(glyph,(i*cell+(cell-glyph.width)//2,(h-glyph.height)//2))
            shape=group.getbbox();assert shape
            color=Image.new('RGBA',(w,h));draw=ImageDraw.Draw(color)
            for y in range(h):
                t=(y-shape[1])/max(1,shape[3]-shape[1]-1);green=85+round(170*max(0,1-abs(t-.5)*3));draw.line((0,y,w-1,y),fill=(255,green,85,255))
            color.putalpha(group);shadow=Image.new('RGBA',(w,h),(0,0,170,255));shadow.putalpha(group);overlay.alpha_composite(shadow,(x0+4,y0+5));overlay.alpha_composite(color,(x0,y0))
        assert ImageChops.multiply(overlay.getchannel('A'),icon).getbbox() is None
        file=f'publisher-{ident}.png';overlay.save(a.out/file);words.append(dict(id=ident,file=file,sha=sha((a.out/file).read_bytes()),width=1920,height=1200,fallback=''.join(fallback)))
    m=dict(schema=1,source_sha256=SOURCE,decoded_sha256=DECODED,mask='publisher-erase.png',mask_sha256=sha((a.out/'publisher-erase.png').read_bytes()),words=words,fields=[dict(text=t,rect=list(r),font_px=px) for t,r,px in FIELDS],rights='local-only original-derived wordmarks; font licenses and notices retained in base')
    (a.out/'publisher.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');(a.out/'publisher-import.json').write_text(json.dumps(dict(base_files=before,fonts={name:h for name,h in FONTS.values()},source_sha256=SOURCE,mask_raw_sha256=MASK,pillow=__version__),ensure_ascii=False,indent=2)+'\n')
    assert all(sha((a.out/n).read_bytes())==h for n,h in before.items());assert all(p.stat().st_uid==1000 for p in a.out.rglob('*'))
    print(json.dumps(dict(preserved=len(before),added=6,mask_sha256=m['mask_sha256'],words=words)))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('base','source','fonts','out'):p.add_argument('--'+n,type=Path,required=True)
    build(p.parse_args())
