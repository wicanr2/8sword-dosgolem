"""034：獨立原圖取樣、正常重播隔離及 actual Draw 核對。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
from itertools import zip_longest
from pathlib import Path
from PIL import Image, ImageChops

RECT=(24,72,1368,672)
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def files(p): return {str(f.relative_to(p)):sha(f) for f in p.rglob('*') if f.is_file()}
spec=importlib.util.spec_from_file_location('army_audit',Path(__file__).with_name('audit-army-dismiss.py'))
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)

def sample(path):
    im=Image.open(path).convert('RGB');sw,sh=im.size;pix=im.load();out=bytearray(1344*600*4)
    for y in range(600):
        sy=max(0,(y+.5)*sh/600-.5);y0=int(sy);y1=min(y0+1,sh-1);fy=sy-y0
        for x in range(1344):
            sx=max(0,(x+.5)*sw/1344-.5);x0=int(sx);x1=min(x0+1,sw-1);fx=sx-x0;sums=[0.,0.,0.]
            for (xx,yy),weight in zip([(x0,y0),(x1,y0),(x0,y1),(x1,y1)],[(1-fx)*(1-fy),fx*(1-fy),(1-fx)*fy,fx*fy]):
                for c,v in enumerate(pix[xx,yy]): sums[c]+=weight*v
            at=(y*1344+x)*4
            for c in range(3): out[at+c]=int(sums[c]+.5)
            out[at+3]=255
    return bytes(out)

def font_points(im,font,profiles):
    glyphs,atlas=profiles[font];pixels=im.load();count=0
    for ch,x in zip('檢視主角',[488,520,552,584]):
        ix,iy,iw,ih=glyphs[ch]['ink'];dw,dh=min(iw,48),min(ih,90)
        left,top=x*3+(48-dw)//2,72+(90-dh)//2
        for y in range(dh):
            for xx in range(dw):
                if atlas.getpixel((ix+xx*iw//dw,iy+y*ih//dh))==255:
                    assert pixels[left+xx,top+y][:3]==(255,241,181),('font',font,ch,left+xx,top+y,pixels[left+xx,top+y])
                    count+=1
    assert count>0
    return count

def normal(a,art,profiles):
    roots=[a.hd,a.control,a.broken];states=[read(p/'final.json') for p in roots]
    for name in ['final.state','audio.pcm']: assert len({sha(p/name) for p in roots})==1,name
    for field in ['steps','input_events','exec_log','file_ops','strings','unimplemented']:
        assert all(s[field]==states[0][field] for s in states),field
    assert files(roots[0]/'scratch')==files(roots[1]/'scratch')==files(roots[2]/'scratch')
    for i,s in enumerate(states):
        assert s['recorded_frames']==s['frame_pure_count']
        for k in ['asset_error','graphics_error','font_error','battle_background_error','battle_actor_error','battle_effect_error','battle_marker_error']: assert not s[k],(i,k,s[k])
        assert not s['text']['MissingGlyphs'] and not s['text']['Errors']
    assert not states[0]['recruitment_building_error'] and not states[1]['recruitment_building_error']
    assert 'SHA-256' in states[2]['recruitment_building_error']
    metadata=[readline for readline in map(json.loads,(a.hd/'frames.jsonl').read_text().splitlines())]
    changed=[];verified=0
    for parts in zip_longest(*(helper.stream(p) for p in roots)):
        assert all(p is not None for p in parts)
        (n,step,im),(cn,cs,ci),(bn,bs,bi)=parts;assert (n,step)==(cn,cs)==(bn,bs)
        assert bi.tobytes()==ci.tobytes(),('broken fallback',n)
        box=ImageChops.difference(im.convert('RGB'),ci.convert('RGB')).getbbox()
        if box:
            assert box[0]>=RECT[0] and box[1]>=RECT[1] and box[2]<=RECT[2] and box[3]<=RECT[3],('outside',n,box)
            changed.append(n)
        m=metadata[n-1]
        if 11988 in m['visible_sources'] and 12238 in m['visible_sources']:
            assert im.crop(RECT).tobytes()==art,('building',n)
            font_points(im,m['font_id'],profiles);verified+=1
    assert changed and verified
    return dict(status='passed',frames_per_run=n,frame_pure_count=sum(s['frame_pure_count'] for s in states),changed_frames=changed,complete_building_frames=verified,state_sha256=sha(a.hd/'final.state'),pcm_sha256=sha(a.hd/'audio.pcm'),scratch_files=len(files(a.hd/'scratch')),all_broken_frames_equal_control=True)

def gui(a,art,profiles):
    root=a.receipt;meta=list(map(json.loads,(root/'intro-draw.jsonl').read_text().splitlines()))
    checkpoints={}
    for p in root.glob('recruitment-*.json'):
        s=read(p)
        if p.name not in ['recruitment-noto.json','recruitment-lishu.json','recruitment-caoshu.json']: continue
        checkpoints[int(s['presented_frames'])]=(p.name,s['font_id'])
    assert len(checkpoints)==3
    events=read(root/'gui-input-receipt.json')['events']
    start=min(checkpoints)
    after=max(read(root/name)['steps'] for name in ['recruitment-noto.json','recruitment-lishu.json','recruitment-caoshu.json'])
    end=next(int(e['status']['presented_frames']) for e in events if e['x11_keycode'] in [9,13] and e['down'] and e['status']['steps']>after)
    samples=[];continuous=0
    for n,step,im in helper.stream(root):
        assert meta[n-1]['draw']==n and meta[n-1]['step']==step
        if start<=n<=end:
            assert im.crop(RECT).tobytes()==art,('continuous building Draw',n)
            font_points(im,meta[n-1]['font_id'],profiles);continuous+=1
        if n not in checkpoints: continue
        name,font=checkpoints[n];assert meta[n-1]['font_id']==font
        assert im.crop(RECT).tobytes()==art,('actual building Draw',n,font)
        points=font_points(im,font,profiles)
        file='recruitment-'+font+'-actual-draw.png';im.save(root/file)
        samples.append(dict(checkpoint=name,draw=n,step=step,font=font,file=file,opaque_font_points=points,exact_building_pixels=806400))
    final=read(root/'gui-final.json')
    assert n==len(meta)==final['recorded_frames'] and final['closed']
    assert len(samples)==3 and {p['font'] for p in samples}=={'noto','lishu','caoshu'}
    for k in ['recruitment_building_error','graphics_error','font_error','battle_marker_error','battle_actor_error','battle_effect_error','battle_background_error']: assert not final[k],(k,final[k])
    assert not final['text']['MissingGlyphs'] and not final['text']['Errors']
    assert continuous==end-start+1
    return dict(status='passed-actual-Draw',frames=n,samples=samples,continuous_building_draws=continuous,continuous_draw_range=[start,end],limit='complete building from first selected checkpoint through Esc or first numeric-edit key-down, three normal-input fonts; save/reload audited separately')

def main():
    p=argparse.ArgumentParser();p.add_argument('--assets',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    sub=p.add_subparsers(dest='mode',required=True);n=sub.add_parser('normal')
    for key in ['hd','control','broken']: n.add_argument('--'+key,type=Path,required=True)
    g=sub.add_parser('gui');g.add_argument('--receipt',type=Path,required=True)
    a=p.parse_args();assert not a.out.exists()
    art_path=a.assets/'recruitment-building-r1.png';assert sha(art_path)=='7aa67f8975843e91e0a393863ba08bb77582fd4ab62ee10fad059bebcd5b61ab'
    art=sample(art_path);profiles=helper.fonts(a.assets)
    result=normal(a,art,profiles) if a.mode=='normal' else gui(a,art,profiles)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__': main()
