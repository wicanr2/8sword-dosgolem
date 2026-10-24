#!/usr/bin/env python3
"""032：保留原始生成 PNG，加入固定工具列字集與兩側海報。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
from PIL import Image, ImageDraw, ImageFont, __version__

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--art',type=Path,required=True);p.add_argument('--font',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    assert a.out.is_dir() and a.out.stat().st_uid==os.getuid() and not list(a.out.iterdir())
    expected={'cover-poster-r1.png':'2d666efbb2b1fc714e92b82f078c3fd4139b7c690fce794b95c99c8b2725c55d','side-wings-r1.png':'f14552801e98d4171befeb1220a9626c9e2e7a25efdad011896d2d3abfcba341','toolbar-font-preview-r1.png':'34009f2ab958e1cf34436b8d10950cc173e834c8c18631e123b1b26601d32657'}
    assert __version__=='11.3.0' and sha(a.font)=='3cffb10242b4b7e6edd439ebf3bd7e392345525e093ea08149e0a0158a1b5151'
    font=ImageFont.truetype(str(a.font),48,index=3);assert font.getname()==('Noto Sans CJK TC','Black')
    chars=sorted(set(''.join(chr(i) for i in range(32,127))+'神州八劍字型海報經典封面龍虎延展關閉教育部隸書草書劉建毛草風'));assert len(chars)==123
    atlas=Image.new('RGBA',(1024,512));glyphs=[]
    for i,c in enumerate(chars):
        box=font.getbbox(c);x,y=i%16*64,i//16*64;w,h=box[2]-box[0],box[3]-box[1];ox,oy=x+(64-w)//2,y+(64-h)//2
        ImageDraw.Draw(atlas).text((ox-box[0],oy-box[1]),c,font=font,fill='white');glyphs.append({'character':c,'ink':[ox,oy,w,h]})
    for f in a.base.iterdir():
        assert f.is_file() and not f.is_symlink();shutil.copyfile(f,a.out/f.name)
    for n,alternate,target in [('cover-poster-r1.png','poster-cover-approved-r1.png','poster-cover.png'),('side-wings-r1.png','poster-wings-approved-r1.png','poster-wings.png')]:
        source=a.art/n if (a.art/n).exists() else a.art/alternate;assert sha(source)==expected[n];shutil.copyfile(source,a.out/target)
    atlas.save(a.out/'poster-toolbar-font.png');assert sha(a.out/'poster-toolbar-font.png')==expected['toolbar-font-preview-r1.png']
    m={'source_sha256':sha(a.font),'atlas_sha256':sha(a.out/'poster-toolbar-font.png'),'glyphs':glyphs}
    m={'schema':1,**m};(a.out/'poster-toolbar.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
    (a.out/'poster-toolbar-import.json').write_text(json.dumps({'spec':'032','base':a.base.name,'sources':expected,'generation_record':'poster-heroine-generated-r1.json','rights':'Local project artwork; no public distribution grant inferred.'},indent=2)+'\n')
    print('poster toolbar:',len(list(a.out.iterdir())),'files')
if __name__=='__main__':main()
