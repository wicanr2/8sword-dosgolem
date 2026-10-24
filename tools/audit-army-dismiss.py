"""018 F3：獨立民兵取樣、真實字型墨點、客體隔離及 GUI Draw 核對。Docker only。"""
import argparse
import gzip
import hashlib
import json
import struct
from itertools import zip_longest
from pathlib import Path
from PIL import Image

RECT=(72,78,336,378)
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def files(p):return {str(f.relative_to(p)):sha(f) for f in p.rglob('*') if f.is_file()}
def stream(p):
    with gzip.open(p/'presentation.frames.gz','rb') as f:
        def take(n):
            b=f.read(n);assert len(b)==n;return b
        assert take(8)==b'8SFRM001'
        w,h=struct.unpack('<II',take(8));assert (w,h) in [(1920,1200),(2944,1264)]
        rgba=bytearray(w*h*4);ordinal=0
        while header:=f.read(24):
            assert len(header)==24
            n,step,rows=struct.unpack('<QQQ',header);ordinal+=1;assert n==ordinal and rows<=h
            if n==1:assert rows==h
            seen=set()
            for _ in range(rows):
                y,=struct.unpack('<H',take(2));assert y<h and y not in seen;seen.add(y)
                rgba[y*w*4:(y+1)*w*4]=take(w*4)
            im=Image.frombytes('RGBA',(w,h),bytes(rgba))
            yield n,step,im.crop((512,64,2432,1264)) if w==2944 else im

def sprite(assets):
    m=read(assets/'terrain.json');entry=next(v for v in m['actors'] if v['source_index']==84)
    path=assets/entry['file'];assert sha(path)==entry['sha256']
    im=Image.open(path).convert('RGBA');sw,sh=im.size;pix=im.load();out=bytearray(264*300*4)
    for y in range(300):
        sy=max(0,(y+.5)*sh/300-.5);y0=int(sy);y1=min(y0+1,sh-1);fy=sy-y0
        for x in range(264):
            sx=max(0,(x+.5)*sw/264-.5);x0=int(sx);x1=min(x0+1,sw-1);fx=sx-x0;sums=[0.,0.,0.,0.]
            for (xx,yy),weight in zip([(x0,y0),(x1,y0),(x0,y1),(x1,y1)],[(1-fx)*(1-fy),fx*(1-fy),(1-fx)*fy,fx*fy]):
                r,g,b,a=pix[xx,yy]
                if a<=3:continue
                for c,v in enumerate([v*257*a//255 for v in (r,g,b)]+[a*257]):sums[c]+=weight*v
            at=(y*264+x)*4
            for c in range(3):out[at+c]=min(255,int(sums[c]/257+.5))
            out[at+3]=255
    return bytes(out)

def native_sprite(original):
    raw=(original/'MAN01.EGG').read_bytes();assert hashlib.sha256(raw).hexdigest()=='a7e02cf495800fac19c293688043f3af6eb6deaec1a61a581ed3f9d5b8b3e5f1'
    palette=[(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),(170,85,0),(170,170,170),(85,85,85),(85,85,255),(85,255,85),(85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]
    im=Image.new('RGB',(88,50));pixels=[]
    for y in range(50):
        for x in range(88):
            original_x=87-x;at=y*11+original_x//8;bit=7-original_x%8
            color=sum(((raw[4+plane*550+at]>>bit)&1)<<plane for plane in range(4)) if (raw[4+5*550+at]>>bit)&1 else 0
            pixels.append(palette[color])
    im.putdata(pixels);return im.resize((264,300),Image.Resampling.NEAREST).convert('RGBA').tobytes()

def fonts(assets):
    m=read(assets/'font.json');result={'noto':(m,Image.open(assets/m['atlas']).getchannel('A'))}
    assert sha(assets/m['atlas'])==m['atlas_sha256']
    for p in read(assets/'font-choices.json')['profiles']:
        assert sha(assets/p['atlas'])==p['atlas_sha256'];result[p['id']]=(p,Image.open(assets/p['atlas']).getchannel('A'))
    return {k:({g['character']:g for g in m['glyphs']},im) for k,(m,im) in result.items()}

def empty_paper(assets):
    entry=next(e for e in read(assets/'terrain.json')['materials'] if e['source_index']==46)
    path=assets/entry['file'];assert sha(path)==entry['sha256']
    im=Image.open(path).convert('RGBA')
    if entry.get('source_rect'):
        x,y,w,h=entry['source_rect'];im=im.crop((x,y,x+w,y+h))
    sw,sh=im.size;pix=im.load();out=bytearray(192*150*4)
    for y in range(150):
        sy=max(0,(y+.5)*sh/150-.5);y0=int(sy);y1=min(y0+1,sh-1);fy=sy-y0
        for x in range(192):
            sx=max(0,(x+.5)*sw/192-.5);x0=int(sx);x1=min(x0+1,sw-1);fx=sx-x0;sums=[0.,0.,0.]
            for (xx,yy),weight in zip([(x0,y0),(x1,y0),(x0,y1),(x1,y1)],[(1-fx)*(1-fy),fx*(1-fy),(1-fx)*fy,fx*fy]):
                r,g,b,a=pix[xx,yy];assert a==255
                for c,v in enumerate((r,g,b)):sums[c]+=weight*v
            at=(y*192+x)*4
            for c in range(3):out[at+c]=int(sums[c]+.5)
            out[at+3]=255
    if entry.get('sampling','periodic')=='periodic':
        previous=bytes(out)
        for y in range(150):
            for x in range(192):
                ax=.5*max(0,1-min(x,191-x)/16);ay=.5*max(0,1-min(y,149-y)/16)
                for c in range(3):out[(y*192+x)*4+c]=int(sum(previous[(yy*192+xx)*4+c]*w for (xx,yy),w in zip([(x,y),(191-x,y),(x,149-y),(191-x,149-y)],[(1-ax)*(1-ay),ax*(1-ay),(1-ax)*ay,ax*ay]))+.5)
    # F2 paper starts at original (8,12); actor area starts at (24,13).
    return b''.join(bytes(out[(((6+y)%150)*192+(48+x)%192)*4:(((6+y)%150)*192+(48+x)%192)*4+4]) for y in range(300) for x in range(264))

def text_points(im,font,profiles,fallback=False):
    glyphs,atlas=profiles[font];points=0
    fields=[('種類:',112,13,10),('數量:',112,29,10),('月薪:',112,45,10),('民兵',152,13,14),('30',152,29,14),('30',152,45,14)]
    pix=im.load()
    for text,x,y,fg in fields:
        color=(85,255,85) if fg==10 and fallback else (223,195,121) if fg==10 else (255,241,181)
        for ch in text:
            width=16 if ord(ch)>=0x3400 else 8;g=glyphs[ch];ix,iy,iw,ih=g['ink'];dw,dh=min(iw,width*3),min(ih,90)
            left,top=x*3+(width*3-dw)//2,y*6+(90-dh)//2;count=0
            for yy in range(dh):
                for xx in range(dw):
                    if atlas.getpixel((ix+xx*iw//dw,iy+yy*ih//dh))!=255:continue
                    assert pix[left+xx,top+yy][:3]==color,('font pixel',font,ch,left+xx,top+yy,pix[left+xx,top+yy],color)
                    count+=1
            assert count>0,(font,ch);points+=count;x+=width
    return points

def normal(a,hd_sprite,profiles):
    roots=[a.hd,a.control,a.broken,a.native];states=[read(p/'gui-final.json') for p in roots]
    for name in ('final.state','audio.pcm'):assert len({sha(p/name) for p in roots})==1,name
    for k in ['steps','input_events','exec_log','file_ops','bios_consumed','irq1_delivered','unimplemented','strings']:
        assert all(s[k]==states[0][k] for s in states),k
    assert files(roots[0]/'scratch')==files(roots[1]/'scratch')==files(roots[2]/'scratch')==files(roots[3]/'scratch')
    assert all(s['recorded_frames']==s['frame_pure_count']==418 for s in states)
    assert states[0]['graphics']['ActorFallbackCalls']==0 and states[1]['graphics']['ActorFallbackCalls']==2
    assert not states[0]['graphics_error'] and states[2]['graphics_error'] and 'SHA-256' in states[2]['graphics_error']
    assert not states[2].get('graphics_materials',0) and not states[2].get('graphics_actor_materials',0)
    checks=[]
    for name in ['04-f3','08-before-enter']:
        image=Image.open(a.hd/(name+'-hd.png')).convert('RGBA');assert image.crop(RECT).tobytes()==hd_sprite
        checks.append(dict(checkpoint=name,opaque_font_points=text_points(image,'noto',profiles),sprite_pixels=264*300))
    for name in ['03-army-before','06-army-after','11-empty-f2','12-empty-f3']:
        assert (a.hd/(name+'-hd.png')).read_bytes()==(a.control/(name+'-hd.png')).read_bytes(),name
    changed=[];unchanged=0
    for parts in zip_longest(*(stream(p) for p in roots)):
        assert all(x is not None for x in parts)
        (n,step,im),(cn,cs,ci),(bn,bs,bi),(nn,ns,ni)=parts
        assert (n,step)==(cn,cs)==(bn,bs)==(nn,ns)
        assert bi.tobytes()==ni.tobytes(),('broken fallback',n)
        if im.tobytes()!=ci.tobytes():
            from PIL import ImageChops
            box=ImageChops.difference(im.convert('RGB'),ci.convert('RGB')).getbbox()
            assert box[0]>=24 and box[1]>=72 and box[2]<=1368 and box[3]<=1122,('difference outside original content',n,box)
            changed.append(n)
        else:unchanged+=1
    return dict(status='passed-normal-F3-isolation-and-pixels',frames_per_run=n,frame_pure_count=sum(s['frame_pure_count'] for s in states),state_sha256=sha(a.hd/'final.state'),pcm_sha256=sha(a.hd/'audio.pcm'),scratch_files=len(files(a.hd/'scratch')),changed_frames=changed,unchanged_frames=unchanged,all_broken_frames_equal_native_art_control=True,checkpoints=checks)

def gui(a,hd_sprite,old_sprite,profiles):
    root=a.receipt;meta=[json.loads(x) for x in (root/'intro-draw.jsonl').read_text().splitlines()];matched={};examples={}
    expected=old_sprite if a.fallback else hd_sprite
    empty={};verified=[];paper=empty_paper(a.assets)
    for path in list(root.glob('*empty-f[23].json'))+list(root.glob('*-after-enter.json')):
        s=read(path);assert not any(v in s['visible_sources'] for v in [1330,1338,1346,10380]),path
        empty.setdefault(s['presented_frames'],[]).append((path.name,paper if path.name.endswith('f2.json') else bytes((0,0,0,255))*(264*300)))
    for n,step,im in stream(root):
        info=meta[n-1];assert info['draw']==n and info['step']==step
        for name,want in empty.get(n,[]):
            assert im.crop(RECT).tobytes()==want,('empty-list ghost',name,n)
            verified.append(dict(checkpoint=name,draw=n,pixels=264*300))
        # Identify F3 by its original selected-name background and black pane,
        # independently of whether its actor happens to match the HD image.
        # F2 jade-paper pages and empty lists cannot satisfy this predicate.
        if im.getpixel((457,79))!=(255,85,85,255):continue
        if im.getpixel((900,800))!=(0,0,0,255):continue
        if im.crop(RECT).tobytes()!=expected:
            im.save(root/('dismiss-failed-draw-'+str(n)+'.png'))
            raise AssertionError(('F3 sprite RGBA',n,step))
        font=info['font_id'];points=text_points(im,font,profiles,a.fallback)
        matched[font]=matched.get(font,0)+1
        if font not in examples:
            name='dismiss-'+font+'-actual-draw.png';im.save(root/name);examples[font]=dict(draw=n,step=step,file=name,opaque_font_points=points)
    final=read(root/'gui-final.json');assert final['closed'] and n==final['recorded_frames']==len(meta)
    assert (verified if a.empty_only else matched) and not final['text']['MissingGlyphs'] and not final['text']['Errors']
    assert len(verified)==sum(len(v) for v in empty.values())
    if a.fallback:
        assert final['graphics_error'] and 'SHA-256' in final['graphics_error'];assert not final.get('graphics_materials',0)
    else:assert final['graphics']['ActorFallbackCalls']==0 and not final['graphics_error']
    return dict(status='passed-actual-F3-Draw-and-fonts',frames=n,matched_fonts=matched,examples=examples,empty_checkpoints=verified,fallback=a.fallback,limit='F3 selected-name background and black pane identify candidate Draws; all candidates checked; empty-list rectangles reconstructed independently; save/read checked separately')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--assets',type=Path,required=True);ap.add_argument('--original',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    sub=ap.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('normal')
    for name in ('hd','control','broken','native'):p.add_argument('--'+name,type=Path,required=True)
    p=sub.add_parser('gui');p.add_argument('--receipt',type=Path,required=True);p.add_argument('--fallback',action='store_true');p.add_argument('--empty-only',action='store_true')
    a=ap.parse_args();art,profiles=sprite(a.assets),fonts(a.assets)
    result=normal(a,art,profiles) if a.mode=='normal' else gui(a,art,native_sprite(a.original),profiles)
    assert not a.out.exists();a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
