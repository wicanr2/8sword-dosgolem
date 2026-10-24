#!/usr/bin/env python3
"""017：從原始平面、來源交易及 PNG 獨立重建正式博物館逐幀。Docker only。"""
from pathlib import Path
import argparse,copy,gzip,hashlib,json,runpy,struct
from PIL import Image
read=lambda p:json.loads(p.read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
def stream(path):
    with gzip.open(path,'rb') as f:
        assert f.read(8)==b'8SFRM001'
        assert struct.unpack('<II',f.read(8))==(1920,1200)
        rgba=bytearray(1920*1200*4);number=0;previous=0
        while header:=f.read(24):
            n,step,rows=struct.unpack('<QQQ',header)
            number+=1
            assert n==number and step>=previous and rows<=1200
            previous=step;seen=set()
            for _ in range(rows):
                y,=struct.unpack('<H',f.read(2))
                assert y<1200 and y not in seen
                seen.add(y);row=f.read(1920*4);assert len(row)==1920*4
                rgba[y*1920*4:(y+1)*1920*4]=row
            yield number,step,bytes(rgba)


def empty():
    return dict(role=None,native=Image.new('RGBA',(640,200),(0,0,0,255)),
                ink=Image.new('RGBA',(640,200)),known=False)


def native_apply(pages,event):
    page=event['page'];operation=event['operation']
    if operation=='clear':
        p=empty();p['known']=True;pages[page]=p
        assert event['at']==0x5b0c
        return
    if operation=='copy':
        source,destination={0x5d76:(0,16384),0x5d9c:(16384,0)}[event['at']]
        assert event['source_page']==source and page==destination
        pages[destination]=copy.deepcopy(pages.get(source,empty()))
        return
    assert operation=='draw'
    w,h,raw=records[event['source_sha256']]
    p=pages.setdefault(page,empty())
    if event['blocks']==4:
        p['role']='right' if event['role']=='portrait' else event['role']
        p['ink']=Image.new('RGBA',(640,200))
        if w==80 and h==100 and event['rows']==list(range(page+4000,page+12000,80)):
            p['known']=True
    for y,address in enumerate(event['rows']):
        for x in range(w):
            i=y*w+x;local=address-page+x
            for bit in range(8):
                if event['blocks']==6 and not raw[4+5*w*h+i]&(128>>bit):
                    continue
                index=sum(((raw[4+plane*w*h+i]>>(7-bit))&1)<<plane for plane in range(4))
                pixel=((local%80)*8+bit,local//80)
                assert 0<=pixel[0]<640 and 0<=pixel[1]<200
                color=(*palette[index],255)
                p['native'].putpixel(pixel,color)
                if event['blocks']==6 and p['role']=='left':
                    p['ink'].putpixel(pixel,color)


def apply(pages,event):
    native_apply(pages,event)
    p=pages.get(event['page'])
    if event['operation'] in ['clear','copy']:return
    source=event['source_sha256']
    if event['blocks']==4:
        if event['role'] in ['left','right']:
            p.update(actor=None,actor_count=0,portrait=None,beam=None)
        else:
            p['portrait']=copy.deepcopy(event)
    elif source in actors:
        p['actor_count']=p.get('actor_count',0)+1
        p['actor']=copy.deepcopy(event) if p['actor_count']==1 else None
    elif source in beam_sources:
        p['beam']=copy.deepcopy(event)
    else:
        raise AssertionError(('unknown source',source))


def draw_actor(band,event,sprite,tint=None):
    pixels=band.load();src=sprite.load()
    for y in range(sprite.height):
        row=event['rows'][y//6]-event['page']
        for x in range(sprite.width):
            r,g,b,a=src[x,y]
            if not a:continue
            address=row+x//24
            dx,dy=address%80*24+x%24,(address//80-20)*6+y%6
            assert 0<=dx<1920 and 0<=dy<780
            if tint is not None:
                intensity=max(r,g,b)
                r,g,b=[(intensity*c+127)//255 for c in tint]
            dest=pixels[dx,dy]
            assert dest[3]==255
            pixels[dx,dy]=tuple((s*a+d*(255-a)+127)//255 for s,d in zip((r,g,b),dest[:3]))+(255,)


def beam_tint(source):
    w,h,raw=records[source];n=w*h
    colors=set()
    for i in range(n):
        for bit in range(8):
            if raw[4+5*n+i]&(128>>bit):
                index=sum(((raw[4+plane*n+i]>>(7-bit))&1)<<plane for plane in range(4))
                colors.add(tuple(palette[index]))
    return max(colors,key=sum)


def render(page,variant,scenes_enabled,actors_enabled):
    result=Image.new('RGBA',(1920,780))
    native=variant=='native'
    if native:
        # Independently decoded source bitmap calls already include every masked write.
        return page['native'].crop((0,20,640,150)).resize((1920,780),Image.Resampling.NEAREST)
    result.paste(left[variant] if page['role']=='left' else arts['right:'+variant],(0,180))
    if page.get('portrait'):result.paste(arts['portrait:all'],(336,0))
    actor=page.get('actor')
    if actor and actors_enabled:
        draw_actor(result,actor,actors[actor['source_sha256']])
        if page.get('beam'):
            assert scenes_enabled
            draw_actor(result,page['beam'],arts['beam:all'],beam_tint(page['beam']['source_sha256']))
    else:
        ink=page['ink'].crop((0,50,640,150)).resize((1920,600),Image.Resampling.NEAREST)
        result.alpha_composite(ink,(0,180))
    return result


def audit(path,control=None):
    final=read(path/'gui-final.json');status=final['museum'];variant=status['variant']
    scene_enabled=status['scene_loaded']==3;actor_enabled=status['actor_loaded']==10 and variant!='native'
    meta=[json.loads(l) for l in (path/'intro-draw.jsonl').read_text().splitlines()]
    events=read(path/'museum-transactions.json')
    wanted={m['museum']['hold_version'] for m in meta if m.get('museum') and m['museum']['stage']=='hold'}
    pages={};history={0:{}};serial=0;counts={};painted_sources=set();beam_colors=set()
    baseline=iter(stream(control/'presentation.frames.gz')) if control else None
    for number,step,rgba in stream(path/'presentation.frames.gz'):
        m=meta[number-1];info=m['museum']
        if info is None:
            assert serial==0 and not m.get('museum_stage')
            info=dict(serial=0,errors=[],stage='',page=0,hold_version=0)
        assert (m['draw'],m['step'])==(number,step) and not info['errors']
        while serial<info['serial']:
            event=events[serial];assert event['serial']==serial+1 and event['step']<=step
            apply(pages,event);serial+=1
            if serial in wanted:history[serial]=copy.deepcopy(pages)
        if baseline:
            n,s,base=next(baseline);assert (n,s)==(number,step)
        else:base=rgba
        p=pages.get(info['page'])
        held=info['stage']=='hold'
        if held:p=history[info['hold_version']].get(info['page'])
        if held:assert p and p['role'] in ['left','right'],(path.name,number,'unowned museum hold overwrites upstream frame')
        supported=p and p['role'] in ['left','right'] and (p['role']=='left' or scene_enabled or variant=='native')
        expected=bytearray(base)
        if supported and (held or info['stage'] in ['left','right','portrait','beam','drain']):
            key='held' if held else info['stage'];counts[key]=counts.get(key,0)+1
            image=render(p,variant,scene_enabled,actor_enabled)
            target=Image.frombytes('RGBA',(1920,1200),bytes(expected))
            # Native oracle compares exactly the known source-covered regions; other pixels use baseline.
            if variant=='native':
                target.paste(image.crop((0,180,1920,780)),(0,300))
                if p.get('portrait'):target.paste(image.crop((336,0,1608,600)),(336,120))
            else:target.alpha_composite(image,(0,120))
            expected=target.tobytes()
            if actor_enabled and p.get('actor'):painted_sources.add(p['actor']['source_sha256'])
            if actor_enabled and p.get('beam'):beam_colors.add(beam_tint(p['beam']['source_sha256']))
        assert rgba==bytes(expected),(path.name,number,info['stage'],'full RGBA differs')
    assert number==len(meta)==final['recorded_frames'] and final['closed']
    assert serial==len(events) and status['retired'] and status['observer_after_retire']==status['unknown_writes']==0
    return dict(frames=number,independent_draws=counts,painted_actor_sources=len(painted_sources),
                beam_tints=sorted(beam_colors),all_frames_exact=True,transactions=serial,
                scene_loaded=status['scene_loaded'],scene_validated=status['scene_validated'],scene_error=status['scene_error'])


def load_model(project,assets,research):
 global records,palette,left,arts,actors,beam_sources
 records={}
 decoded=project/'workplace/probe-20261023/graphics-first/intro-r1'
 for name,blocks,expected in [('TIT3.AY',4,'c91efb90db3c5fa8ef9a109c0bf362fee14f9b486693e92088a5c504d3b0f590'),('TIT4.AY',6,'59ce4bbb648666351545e0e9c0d6da7015689075b2f29375cf11e15839551d92'),('TIT5.AY',4,'1ad430667a6d06969e1e71e1fa0b1f57453e65865488bbaa3416f86027e8924b')]:
  raw=(decoded/(name+'.decoded')).read_bytes();assert sha(raw)==expected
  at=0
  while at<len(raw):
   w,h=struct.unpack_from('<HH',raw,at);length=4+w*h*blocks
   assert 0<w<=80 and 0<h<=200 and at+length<=len(raw)
   record=raw[at:at+length];records[sha(record)]=(w,h,record);at+=length
  assert at==len(raw)
 trace=research/'trace-r1/calls.jsonl'
 palette=json.loads(trace.read_text().splitlines()[0])['display']['Palette']
 manifest=read(assets/'museum.json');assert manifest['palette']=='a-purple'
 clean=runpy.run_path(str(Path(__file__).with_name('prepare-hd-museum.py')))['clean_cache']
 images={}
 for item in manifest['assets']:
  file=assets/item['file'];assert sha(file.read_bytes())==item['png_sha256']
  cache=clean(file,item);assert sha(cache)==item['cache_sha256']
  images[item['id']]=Image.frombytes('RGBA',(item['width'],item['height']),cache)
 left={'a-purple':images['left']};arts={'right:a-purple':images['right'],'portrait:all':images['portrait'],'beam:all':images['beam']}
 actors={item['source_records'][0]:images[item['id']] for item in manifest['assets'] if item['id'].startswith('actor-')}
 beam_sources=set(next(item['source_records'] for item in manifest['assets'] if item['id']=='beam'))

def main():
 global records,palette,left,arts,actors,beam_sources
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('hd',type=Path);parser.add_argument('control',type=Path);parser.add_argument('broken',type=Path)
 parser.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[1])
 parser.add_argument('--assets',type=Path,required=True)
 parser.add_argument('--research',type=Path,required=True)
 args=parser.parse_args()
 load_model(args.project,args.assets,args.research)
 paths=[args.hd,args.control,args.broken]
 checks={}
 for name in ['final.state','audio.pcm']:
  checks[name]=[sha((p/name).read_bytes()) for p in paths];assert len(set(checks[name]))==1,name
 files=lambda p:{str(f.relative_to(p)):sha(f.read_bytes()) for f in p.rglob('*') if f.is_file()}
 assert files(args.hd/'scratch')==files(args.control/'scratch')==files(args.broken/'scratch')
 final=[read(p/'gui-final.json') for p in paths]
 for key in ['file_ops','input_events','exec_log','music','text']:
  assert final[0][key]==final[1][key]==final[2][key],key
 for p,st in zip(paths,final):
  assert st['frame_pure_count']==st['recorded_frames']==428 and st['closed']
  assert (p/'frame-before.state').read_bytes()==(p/'frame-after.state').read_bytes()
 assert final[0]['heroine'] is None and final[1]['heroine'] is not None
 assert final[2]['museum_error'] and not final[2]['heroine_error'] and not final[2]['graphics_error'] and not final[2]['font_error']
 for a,b in zip(stream(args.control/'presentation.frames.gz'),stream(args.broken/'presentation.frames.gz')):assert a==b
 result=audit(args.hd,args.control)
 assert result['painted_actor_sources']==10 and len(result['beam_tints'])==2
 assert all(result['independent_draws'].get(k,0)>0 for k in ['left','right','portrait','beam','held','drain'])
 result.update(status='PASS-formal-museum-normal-replay',checks=checks,frame_purity_total=1284,same_scratch_files=len(files(args.hd/'scratch')),broken_frames_same_control=428,source_palette_trace_sha256=sha((args.research/'trace-r1/calls.jsonl').read_bytes()),scope='normal opening presentation; no RNG, gameplay, GUI or audio device claim')
 (args.hd/'museum-pixel-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
