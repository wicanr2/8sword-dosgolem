"""006 PMAP45：獨立取樣、正常四組隔離與真正視窗圖塊核對。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
from itertools import zip_longest
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw

spec=importlib.util.spec_from_file_location('army_audit',Path(__file__).with_name('audit-army-dismiss.py'))
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def files(p):return {str(f.relative_to(p)):sha(f) for f in p.rglob('*') if f.is_file()}

def sources(a):
    raw=(a.original/'PMAP.AY').read_bytes();record=raw[45180:46184]
    assert hashlib.sha256(record).hexdigest()=='fb5ce418cd148e59050d07869bd932ef9ad8a1d26d1971182b00a4ddf55eb88b'
    colors=[(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),(170,85,0),(170,170,170),(85,85,85),(85,85,255),(85,255,85),(85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]
    native=Image.new('RGB',(64,25));native.putdata([colors[sum(((record[4+q*200+y*8+x//8]>>(7-x%8))&1)<<q for q in range(4))] for y in range(25) for x in range(64)])
    art=a.assets/'bamboo-painted-r1.png';assert sha(art)=='f778eee7b8d058cc7dd1ff8c989e78ffed1a33b3e2270ebfbb2076dd59f1f880'
    im=Image.open(art).convert('RGB');sw,sh=im.size;src=im.load();tile=Image.new('RGB',(192,150));pix=tile.load()
    for y in range(150):
        sy=max(0,(y+.5)*sh/150-.5);y0=int(sy);y1=min(y0+1,sh-1);fy=sy-y0
        for x in range(192):
            sx=max(0,(x+.5)*sw/192-.5);x0=int(sx);x1=min(x0+1,sw-1);fx=sx-x0;sums=[0.,0.,0.]
            for (xx,yy),weight in zip([(x0,y0),(x1,y0),(x0,y1),(x1,y1)],[(1-fx)*(1-fy),fx*(1-fy),(1-fx)*fy,fx*fy]):
                for c,v in enumerate(src[xx,yy]):sums[c]+=weight*v
            pix[x,y]=tuple(int(v+.5) for v in sums)
    return native,tile

def normal(a,native,tile):
    roots=[a.hd,a.old,a.broken,a.native];states=[read(p/'final.json') for p in roots]
    for name in ['final.state','audio.pcm']:assert len({sha(p/name) for p in roots})==1,name
    evidence=read(a.source_audit)
    assert sha(a.hd/'final.state')==evidence['state_sha256']
    assert sha(a.hd/'audio.pcm')==evidence['pcm_sha256']
    for key in ['steps','input_events','file_ops','exec_log','strings','unimplemented']:assert all(s[key]==states[0][key] for s in states),key
    assert all(files(p/'scratch')==files(roots[0]/'scratch') for p in roots)
    assert all(s['frame_pure_count']==s['recorded_frames']==380 for s in states)
    assert not states[0]['graphics_error'] and not states[1]['graphics_error'] and 'SHA-256' in states[2]['graphics_error'] and not states[3]['graphics_error']
    assert states[0]['graphics_materials']==states[1]['graphics_materials']+1
    assert not states[2].get('graphics_materials',0) and not states[3].get('graphics_materials',0)
    assert all(not s['text']['MissingGlyphs'] and not s['text']['Errors'] for s in states)
    mask=Image.new('L',(1920,1200));d=ImageDraw.Draw(mask)
    assert len(evidence['calls'])==42 and all(c['all_1600_pixels_exact'] for c in evidence['calls'])
    for c in evidence['calls']:
        x,y=c['x_byte']*24,c['y']*6;d.rectangle((x,y,x+191,y+149),fill=255)
    inverse=ImageChops.invert(mask);changed=[];checkpoints=[]
    for parts in zip_longest(*(helper.stream(p) for p in roots)):
        assert all(p is not None for p in parts)
        (n,step,im),(on,os,oi),(bn,bs,bi),(nn,ns,ni)=parts;assert (n,step)==(on,os)==(bn,bs)==(nn,ns)
        assert bi.tobytes()==ni.tobytes(),('fault fallback',n)
        diff=ImageChops.difference(im.convert('RGB'),oi.convert('RGB'))
        diff=ImageChops.lighter(ImageChops.lighter(diff.getchannel('R'),diff.getchannel('G')),diff.getchannel('B'))
        assert ImageChops.multiply(diff,inverse).getbbox() is None,('outside observed source rectangles',n)
        if diff.getbbox():changed.append(n)
    for p in a.hd.glob('*-hd.png'):
        old=Image.open(a.old/p.name).convert('RGB');got=Image.open(p).convert('RGB');nat=Image.open(a.hd/(p.name[:-7]+'-native.png')).convert('RGB').resize((640,200),Image.Resampling.NEAREST);want=old.copy();count=0
        for row in range(7):
            for col in range(7):
                x,y=8+col*64,12+row*25
                if nat.crop((x,y,x+64,y+25)).tobytes()==native.tobytes():want.paste(tile,(x*3,y*6));count+=1
        assert got.tobytes()==want.tobytes(),('full checkpoint reconstruction',p.name)
        checkpoints.append(dict(file=p.name,tiles=count,pixels=count*28800))
    assert changed and any(c['tiles']==6 for c in checkpoints)
    return dict(status='passed-normal-bamboo-isolation',frames_per_run=n,frame_pure_count=sum(s['frame_pure_count'] for s in states),state_sha256=sha(a.hd/'final.state'),pcm_sha256=sha(a.hd/'audio.pcm'),scratch_files=len(files(a.hd/'scratch')),changed_frames=changed,all_fault_frames_equal_no_terrain_control=True,checkpoints=checkpoints,limit='every-frame changes bounded by actual source-call rectangles; complete checkpoints reconstructed independently')

def gui(a,native,tile):
    root=a.receipt;targets={}
    for phase in ['save','reload']:
        p=root/phase;final=read(p/'gui-final.json');target=int(read(p/'saved.json')['status']['presented_frames']) if phase=='save' else int(final['recorded_frames']);found=False
        for n,step,im in helper.stream(p):
            if n!=target:continue
            for col in range(6):assert im.convert('RGB').crop((24+col*192,72,216+col*192,222)).tobytes()==tile.tobytes(),('actual bamboo tile',phase,n,col)
            im.save(p/'bamboo-actual-draw.png');targets[phase]=dict(draw=n,step=step,tiles=6,exact_pixels=172800);found=True
        assert found and final['closed'] and n==final['recorded_frames']
        assert not final['graphics_error'] and not final['font_error'] and not final['text']['MissingGlyphs']
    p=root/'reload/snapshot-readonly';report=read(p/'pages.json');assert report['crtc_display_start']==0 and report['mode']==14
    original=Image.open(p/'plane-offset-0000.png').convert('RGB')
    for col in range(6):assert original.crop((8+col*64,12,72+col*64,37)).tobytes()==native.tobytes(),('actual original source',col)
    return dict(status='passed-actual-bamboo-Draw',targets=targets,original_source_pixels=9600,limit='two complete actual Draws, save/read UI paths audited separately')

def main():
    p=argparse.ArgumentParser();p.add_argument('--assets',type=Path,required=True);p.add_argument('--original',type=Path,required=True);p.add_argument('--out',type=Path,required=True);sub=p.add_subparsers(dest='mode',required=True)
    n=sub.add_parser('normal')
    for key in ['hd','old','broken','native','source-audit']:n.add_argument('--'+key,type=Path,required=True)
    g=sub.add_parser('gui');g.add_argument('--receipt',type=Path,required=True)
    a=p.parse_args();assert not a.out.exists();native,tile=sources(a);result=normal(a,native,tile) if a.mode=='normal' else gui(a,native,tile)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
