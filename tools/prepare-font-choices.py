#!/usr/bin/env python3
"""015：從固定字型與既有 Noto 字圖建立本機外掛。在 Docker 內執行。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from PIL import Image, ImageDraw, ImageFont, __version__

def sha(b): return hashlib.sha256(b).hexdigest()

def main():
    p=argparse.ArgumentParser()
    for n in ('base','sources','noto','cjk-fallback','out'):
        p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args()
    assert __version__=='11.3.0' and a.out.is_dir() and a.out.stat().st_uid==1000 and not any(a.out.iterdir())
    assert sha(a.noto.read_bytes())=='3cffb10242b4b7e6edd439ebf3bd7e392345525e093ea08149e0a0158a1b5151'
    serif_sha='93069d8e9e45d515cc421c971a79e6a5777704b348e36a9ef86578bf58adef77'
    assert sha(a.cjk_fallback.read_bytes())==serif_sha
    assert sha((a.sources/'README.md').read_bytes())=='6a1a07af68866daaac77489036fdd153a668c846083bc7b42f675de97772c930'
    serif=ImageFont.truetype(str(a.cjk_fallback),48,index=3)
    assert serif.getname()==('Noto Serif CJK TC','Regular')
    before={str(q.relative_to(a.base)):sha(q.read_bytes()) for q in a.base.rglob('*') if q.is_file()}
    assert 'story-background.json' in before and 'font-choices.json' not in before
    native={}
    for name in ('font','story'):
        m=json.loads((a.base/(name+'.json')).read_text())
        assert sha((a.base/m['atlas']).read_bytes())==m['atlas_sha256']
        atlas=Image.open(a.base/m['atlas']).convert('RGBA')
        for g in m['glyphs']:
            x,y,w,h=g['ink']
            native[g['character']]=atlas.crop((x,y,x+w,y+h))
    chars=sorted(native)
    assert len(chars)==853
    shutil.copytree(a.base,a.out,dirs_exist_ok=True)
    shutil.copyfile(a.sources/'README.md',a.out/'font-choice-lishu-NOTICE.txt')
    profiles=[]
    variants=[('lishu','隸書風 UnYetgul','UnYetgul.ttf','c9d42eaac473b8ab0461cc6c2d1a1bac79b0babdf73974c7269ae17b81fd5d51','COPYING','GPL-2.0'),('caoshu','劉建毛草','LiuJianMaoCao-Regular.ttf','cab396b91a5b7c0b4005a35891180d06e6751f5ac261fe680aec65c1ae209033','OFL.txt','OFL-1.1')]
    for ident,label,file,digest,notice,license in variants:
        assert sha((a.sources/file).read_bytes())==digest
        font=ImageFont.truetype(str(a.sources/file),48)
        missing=font.getmask('\U0010ffff')
        missing_key=missing.size,bytes(missing)
        def supports(c):
            mask=font.getmask(c)
            return (mask.size,bytes(mask))!=missing_key and bool(mask.getbbox())
        def primary(c): return 0x3400<=ord(c)<=0x9fff and supports(c)
        atlas=Image.new('RGBA',(1024,((len(chars)+15)//16)*64))
        glyphs=[]
        fallback=[]
        for i,c in enumerate(chars):
            use=primary(c)
            is_cjk=0x3400<=ord(c)<=0x9fff
            face=font if use else serif
            if use or is_cjk:
                box=face.getbbox(c)
                mask=Image.new('RGBA',(box[2]-box[0],box[3]-box[1]))
                ImageDraw.Draw(mask).text((-box[0],-box[1]),c,font=face,fill='white')
                if mask.width>48 or mask.height>56:
                    mask.thumbnail((48,56),Image.Resampling.LANCZOS)
            else:
                mask=native[c]
            if not use:
                fallback.append(c)
            x,y=i%16*64,i//16*64
            ox,oy=x+(64-mask.width)//2,y+(64-mask.height)//2
            atlas.paste(mask,(ox,oy))
            glyphs.append(dict(character=c,cell=[x,y,64,64],ink=[ox,oy,mask.width,mask.height],fallback=not use,fallback_face='noto-serif' if not use and is_cjk else 'noto-black' if not use else ''))
        name=f'font-choice-{ident}.png'
        atlas.save(a.out/name)
        title=Image.new('RGBA',(1776,570))
        big=ImageFont.truetype(str(a.sources/file),420)
        big_noto=ImageFont.truetype(str(a.cjk_fallback),420,index=3)
        for i,c in enumerate('神州八劍'):
            f=big if primary(c) else big_noto
            b=f.getbbox(c)
            ink=Image.new('RGBA',(b[2]-b[0],b[3]-b[1]))
            ImageDraw.Draw(ink).text((-b[0],-b[1]),c,font=f,fill=(245,207,113,255))
            ink.thumbnail((420,522),Image.Resampling.LANCZOS)
            title.paste(ink,(48+i*420+(420-ink.width)//2,(570-ink.height)//2))
        assert title.getbbox() and title.getbbox()[0]>=24 and title.getbbox()[2]<=1752 and title.getbbox()[1]>=24 and title.getbbox()[3]<=546
        title_name=f'font-title-{ident}.png'
        title.save(a.out/title_name)
        notice_name=f'font-choice-{ident}-LICENSE.txt'
        shutil.copyfile(a.sources/notice,a.out/notice_name)
        profiles.append(dict(id=ident,label=label,source_sha256=digest,cjk_fallback_sha256=serif_sha,atlas=name,atlas_sha256=sha((a.out/name).read_bytes()),width=atlas.width,height=atlas.height,glyphs=glyphs,title=title_name,title_sha256=sha((a.out/title_name).read_bytes()),notice=notice_name,notice_sha256=sha((a.out/notice_name).read_bytes()),license=license,fallback_count=len(fallback),fallback=''.join(fallback)))
    m=dict(schema=1,profiles=profiles,scope='local-only font plugins; UnYetgul GPL-2.0 font embedding has no exception; no public bundle produced')
    (a.out/'font-choices.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
    (a.out/'font-choices-import.json').write_text(json.dumps(dict(pillow=__version__,base_files=before,noto_sha256=sha(a.noto.read_bytes()),cjk_fallback_sha256=serif_sha,manifest_sha256=sha((a.out/'font-choices.json').read_bytes()),sources={n:sha((a.sources/n).read_bytes()) for n in ('UnYetgul.ttf','COPYING','LiuJianMaoCao-Regular.ttf','OFL.txt')}),ensure_ascii=False,indent=2)+'\n')
    assert all(sha((a.out/n).read_bytes())==h for n,h in before.items())
    print(json.dumps(dict(preserved=len(before),glyphs=len(chars),profiles=[dict(id=p['id'],fallback_count=p['fallback_count']) for p in profiles])))

if __name__=='__main__': main()
