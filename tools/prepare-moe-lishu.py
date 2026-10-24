#!/usr/bin/env python3
"""015 追加：教育部隸書，保留原 TTF，以完整字型排版生成呈現快取。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import sys
from types import SimpleNamespace
from PIL import Image,ImageDraw,ImageFont,__version__
sys.dont_write_bytecode = True

MOE='f0ba5eda31727ad89cc0b1f6b9a7dfda02f061fa101c18548b6f8ea0145c108b'
SERIF='93069d8e9e45d515cc421c971a79e6a5777704b348e36a9ef86578bf58adef77'
SOURCE='https://language.moe.gov.tw/material/info?m=9fe3fb11-c3d5-41f2-b029-6d18a2c2fd0d'
LICENSE='https://creativecommons.org/licenses/by-nd/3.0/tw/legalcode'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

def main():
    p=argparse.ArgumentParser()
    for n in ['base','publisher-base','source','fonts','out']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();assert __version__=='11.3.0';assert a.out.is_dir() and a.out.stat().st_uid==os.getuid() and not list(a.out.iterdir())
    fontpath=a.fonts/'TW-MOE-Li-3.00.ttf';assert sha(fontpath)==MOE;assert sha(a.fonts/'NotoSerifCJK-Regular.ttc')==SERIF
    font=ImageFont.truetype(str(fontpath),48);assert font.getname()==('TW-MOE-Li','Regular');serif=ImageFont.truetype(str(a.fonts/'NotoSerifCJK-Regular.ttc'),48,index=3)
    missing=font.getmask('\U0010ffff');key=(missing.size,bytes(missing))
    def primary(c):
        m=font.getmask(c);return 0x3400<=ord(c)<=0x9fff and (m.size,bytes(m))!=key and bool(m.getbbox())
    before={f.name:sha(f) for f in a.base.iterdir() if f.is_file()};assert len(before)==len(list(a.base.iterdir()))
    for f in a.base.iterdir():assert not f.is_symlink();shutil.copyfile(f,a.out/f.name)
    native={}
    for name in ['font','story']:
        m=json.loads((a.base/(name+'.json')).read_text());assert sha(a.base/m['atlas'])==m['atlas_sha256'];im=Image.open(a.base/m['atlas']).convert('RGBA')
        for g in m['glyphs']:
            x,y,w,h=g['ink'];native[g['character']]=im.crop((x,y,x+w,y+h))
    chars=sorted(native);assert len(chars)==853;atlas=Image.new('RGBA',(1024,3456));glyphs=[];fallback=[]
    for i,c in enumerate(chars):
        use=primary(c);cjk=0x3400<=ord(c)<=0x9fff
        if use or cjk:
            face=font if use else serif;b=face.getbbox(c);ink=Image.new('RGBA',(b[2]-b[0],b[3]-b[1]));ImageDraw.Draw(ink).text((-b[0],-b[1]),c,font=face,fill='white');ink.thumbnail((48,56),Image.Resampling.LANCZOS)
        else:ink=native[c]
        if not use:fallback.append(c)
        x,y=i%16*64,i//16*64;ox,oy=x+(64-ink.width)//2,y+(64-ink.height)//2;atlas.paste(ink,(ox,oy));glyphs.append(dict(character=c,cell=[x,y,64,64],ink=[ox,oy,ink.width,ink.height],fallback=not use,fallback_face='noto-serif' if not use and cjk else 'noto-black' if not use else ''))
    assert len(fallback)==135 and ''.join(c for c in fallback if 0x3400<=ord(c)<=0x9fff)=='佈崗歎秘'
    atlas.save(a.out/'font-choice-lishu.png');title=Image.new('RGBA',(1776,570));big=ImageFont.truetype(str(fontpath),420)
    for i,c in enumerate('神州八劍'):
        assert primary(c);b=big.getbbox(c);ink=Image.new('RGBA',(b[2]-b[0],b[3]-b[1]));ImageDraw.Draw(ink).text((-b[0],-b[1]),c,font=big,fill=(245,207,113,255));ink.thumbnail((420,522),Image.Resampling.LANCZOS);title.paste(ink,(48+i*420+(420-ink.width)//2,(570-ink.height)//2))
    title.save(a.out/'font-title-lishu.png');box=title.getbbox();assert box and box[0]>=24 and box[1]>=24 and box[2]<=1752 and box[3]<=546
    notice=f'教育部隸書 3.00\n著作人：中華民國教育部\n來源：{SOURCE}\n授權：創用 CC 姓名標示－禁止改作 3.0 台灣\n{LICENSE}\n原始完整 TTF SHA-256：{MOE}\n原 TTF 保持不變；本目錄保存一般文字排版的圖片快取。\n缺字以 Noto Serif CJK TC 回退；數字與標點採 Noto Black 900。\n'
    (a.out/'font-choice-lishu-NOTICE.txt').write_text(notice);(a.out/'font-choice-lishu-LICENSE.txt').write_text('CC BY-ND 3.0 Taiwan\n'+LICENSE+'\nAttribution: 中華民國教育部\n')
    m=json.loads((a.base/'font-choices.json').read_text());profile=next(x for x in m['profiles'] if x['id']=='lishu');profile.update(label='教育部隸書',source_sha256=MOE,cjk_fallback_sha256=SERIF,glyphs=glyphs,atlas_sha256=sha(a.out/'font-choice-lishu.png'),title_sha256=sha(a.out/'font-title-lishu.png'),notice_sha256=sha(a.out/'font-choice-lishu-LICENSE.txt'),license='CC-BY-ND-3.0-TW',fallback_count=len(fallback),fallback=''.join(fallback));m['scope']='Local font rendering caches; original MOE TTF unmodified; attribution and license URI retained.';write(a.out/'font-choices.json',m)
    spec=importlib.util.spec_from_file_location('publisher',Path(__file__).with_name('prepare-hd-publisher.py'));mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.FONTS['lishu']=('TW-MOE-Li-3.00.ttf',MOE)
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);mod.build(SimpleNamespace(base=a.publisher_base,source=a.source,fonts=a.fonts,out=tmp))
        for n in ['publisher-noto.png','publisher-caoshu.png','publisher-erase.png']:assert sha(tmp/n)==before[n]
        shutil.copyfile(tmp/'publisher-lishu.png',a.out/'publisher-lishu.png');pub=json.loads((tmp/'publisher.json').read_text())
        for row in pub['words']:row['font_source_sha256']=mod.FONTS[row['id']][1]
        write(a.out/'publisher.json',pub)
    write(a.out/'font-choices-import.json',dict(base_files=before,pillow=__version__,source_sha256=MOE,source_url=SOURCE,license_uri=LICENSE,attribution='中華民國教育部',manifest_sha256=sha(a.out/'font-choices.json'),cjk_count=722,primary_cjk=718,missing_cjk='佈崗歎秘',noto_black_fallback=131))
    write(a.out/'publisher-import.json',dict(base_files=before,fonts={n:h for n,h in mod.FONTS.values()},source_sha256=mod.SOURCE,mask_raw_sha256=mod.MASK,pillow=__version__))
    changed=sorted(n for n,h in before.items() if sha(a.out/n)!=h);assert set(changed)<=set(['font-choice-lishu.png','font-title-lishu.png','font-choice-lishu-NOTICE.txt','font-choice-lishu-LICENSE.txt','font-choices.json','font-choices-import.json','publisher-lishu.png','publisher.json','publisher-import.json']);assert all(f.stat().st_uid==os.getuid() for f in a.out.iterdir());print('MOE lishu:',len(before),'files; changed:',changed)
if __name__=='__main__':main()
