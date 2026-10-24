#!/usr/bin/env python3
"""014：依原始固定排列與批准 PNG 獨立核對故事前導。Docker only。"""
import argparse
import gzip
import hashlib
import json
import struct
from pathlib import Path
from PIL import Image

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def stream(path):
    with gzip.open(path,'rb') as f:
        def take(n):
            b=f.read(n);assert len(b)==n,('truncated',path);return b
        assert take(8)==b'8SFRM001'
        w,h=struct.unpack('<II',take(8));assert (w,h) in [(1920,1200),(2944,1264)]
        rgba=bytearray(w*h*4);number=0;previous=0
        while header:=f.read(24):
            assert len(header)==24
            n,step,rows=struct.unpack('<QQQ',header);number+=1
            assert n==number and step>=previous and rows<=h
            if n==1:assert rows==h
            previous=step;seen=set()
            for _ in range(rows):
                y,=struct.unpack('<H',take(2));assert y<h and y not in seen;seen.add(y)
                rgba[y*w*4:(y+1)*w*4]=take(w*4)
            yield n,step,bytes(rgba),(w,h)

def load(project,assets):
    runtime=project/'workplace/probe-20261023/music-first/intro-events-r1/unpacked-trace/runtime-0110.bin'
    source=project/'workplace/probe-20261023/graphics-first/intro-r1/TIT6V.AY.decoded'
    assert sha(runtime)=='a764a110b9f8b1d32a6ee9cc0dd650350f917959d647fe4b45cd7f1013eaae68'
    assert sha(source)=='9aadec77cf59adb1f444d47891526af7da888bebecc648a3fa16a6f0adcd6dfe'
    table=runtime.read_bytes()[0xa633-0x1100:0xa633-0x1100+3200]
    assert hashlib.sha256(table).hexdigest()=='607a192b8ed9cf7dcb8f5c83cb5b43b83e9f5dd473f68e91db5fda5a1c4055a6'
    order=[]
    for v in reversed(struct.unpack('<1600H',table)):
        for x in range(v%40,320,40):
            for y in range(v//40,200,40):order.append(y*320+x)
    assert len(order)==64000 and set(order)==set(range(64000))
    image=assets/'story-prelude.png'
    assert sha(image)=='93879b591e694968c7b777a0b89bdc60f2e3965718ddd520491ebdb2b198eb7c'
    art=Image.open(image).convert('RGBA');assert art.size==(1920,1200)
    return order,source.read_bytes()[768:],art

def expected(art,order,count):
    assert isinstance(count,int) and 0<=count<=64000
    if count==64000:return art
    mask=bytearray(64000)
    for at in order[:count]:mask[at]=255
    mask=Image.frombytes('L',(320,200),bytes(mask)).resize(art.size,Image.Resampling.NEAREST)
    return Image.composite(art,Image.new('RGBA',art.size,(0,0,0,255)),mask)

def isolation(hd,control):
    a,b=read(hd/'gui-final.json'),read(control/'gui-final.json')
    checks={}
    for name in ['final.state','audio.pcm']:
        assert sha(hd/name)==sha(control/name),name
        checks[name]=sha(hd/name)
    for key in ['input_events','exec_log','file_ops','bios_consumed','irq1_delivered','unimplemented']:
        assert a[key]==b[key],key
    def files(root):return {str(f.relative_to(root)):sha(f) for f in root.rglob('*') if f.is_file()}
    af,bf=files(hd/'scratch'),files(control/'scratch');assert af==bf
    assert a['frame_pure_count']==a['recorded_frames'] and b['frame_pure_count']==b['recorded_frames']
    assert a['recorded_frames']==b['recorded_frames']
    return {'checks':checks,'scratch_files':len(af),'Frame_purity':a['frame_pure_count']+b['frame_pure_count']}

def metadata(root):return [json.loads(s) for s in (root/'intro-draw.jsonl').read_text().splitlines()]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,required=True);ap.add_argument('--assets',type=Path,required=True)
    sub=ap.add_subparsers(dest='mode',required=True)
    normal=sub.add_parser('normal');normal.add_argument('hd',type=Path);normal.add_argument('control',type=Path);normal.add_argument('broken',type=Path)
    escape=sub.add_parser('escape');escape.add_argument('hd',type=Path);escape.add_argument('control',type=Path);escape.add_argument('--escape-ms',type=int,required=True)
    gui=sub.add_parser('gui');gui.add_argument('hd',type=Path)
    fallback=sub.add_parser('gui-fallback');fallback.add_argument('hd',type=Path)
    args=ap.parse_args();order,source,art=load(args.project,args.assets)
    root=args.hd;logs=metadata(root);counts={'reveal':0,'complete':0,'handoff':0};first={};previous=0
    controls=iter(stream(args.control/'presentation.frames.gz')) if args.mode in ['normal','escape'] else None
    for n,step,rgba,size in stream(root/'presentation.frames.gz'):
        info=logs[n-1];assert info['draw']==n and info['step']==step
        stage=info['stage'];central=Image.frombytes('RGBA',size,rgba)
        phase=info.get('prelude',{}).get('phase','')
        if phase in ['reveal','wait','handoff']:
            assert stage==('story-prelude-handoff' if phase=='handoff' else 'story-prelude'),('active prelude not presented',n,phase,stage)
        if size==(2944,1264):central=central.crop((512,64,2432,1264))
        control=None
        if controls is not None:
            cn,cs,control,shape=next(controls);assert (cn,cs,shape)==(n,step,size)
        if stage not in ['story-prelude','story-prelude-handoff']:
            if control is not None:assert rgba==control,('outside prelude changed',n,stage)
            continue
        p=info['prelude'];written=p['written'];assert written>=previous;previous=written
        want=expected(art,order,written)
        assert central.tobytes()==want.tobytes(),('prelude RGBA',root,n,step,stage,written)
        kind='handoff' if stage=='story-prelude-handoff' else 'complete' if written==64000 else 'reveal'
        counts[kind]+=1
        if controls is not None and kind!='handoff':
            idx=(root/f'native-{n:04d}.idx').read_bytes()
            assert idx==(args.control/f'native-{n:04d}.idx').read_bytes()
            mask=bytearray(64000)
            for at in order[:written]:mask[at]=1
            assert idx==bytes(source[i] if mask[i] else 0 for i in range(64000)),('original coverage',n)
        if kind not in first or (kind=='reveal' and written>=32000 and 'half' not in first):
            key='half' if kind=='reveal' and written>=32000 else kind
            if key not in first:
                name=f'prelude-{key}-actual-draw.png';central.save(root/name)
                if size==(2944,1264):Image.frombytes('RGBA',size,rgba).save(root/f'prelude-{key}-wide-draw.png')
                first[key]={'draw':n,'step':step,'written':written,'file':name}
    assert n==len(logs)
    final=read(root/'gui-final.json');p=final['intro_story']['prelude']
    if args.mode=='gui-fallback':
        assert sum(counts.values())==0
        s=final['intro_story']
        assert final['closed'] and p['loaded'] is False and 'SHA-256' in s['prelude_error']
        assert s['hd_background'] and not s['load_error'] and not s['background_error']
        assert read(root/'gui-input-receipt.json')['flow']=='prelude-fallback'
        for k in ['asset_error','graphics_error','font_error','museum_error','publisher_error']:
            if k in final:assert not final[k],k
        assert final['text']['MissingGlyphs']==0 and not final['text']['Errors']
        assert any(row.get('museum_stage')=='portrait' for row in logs)
        assert read(root/'captions-pixel-audit.json')['native_caption_exposure_frames']==[]
        assert set(read(root/'story-pixel-audit.json')['pages'])==set('12345')
        report={'status':'PASS-real-corrupt-prelude-GUI-isolation','frames':n,'prelude_HD_Draws':0,'other_HD_and_fonts_preserved':True,'caption_and_five_story_pages_independently_verified':True,'scope':'real corrupt file GUI plus status isolation; whole native prelude pixel fallback is verified separately by paired headless replay'}
        (root/'prelude-fallback-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(report,ensure_ascii=False));return
    assert sum(counts.values())>0
    assert p['loaded'] and p['retired'] and p['error']==''
    if args.mode!='gui':
        for row in logs:
            if p['start_step']<=row['step']<p['stop_step'] and (root/f'native-{row["draw"]:04d}.idx').exists():
                assert row['stage']=='story-prelude',('original mode 13h exposed',row['draw'])
    if args.mode in ['normal','gui']:
        assert p['written']==64000 and p['black_writes']==782 and p['stop_reason']=='story-background'
        assert counts['complete']>0
    report={'status':'PASS-scoped-story-prelude-'+args.mode,'counts':counts,'first_actual_draws':first,'scope':'known central prelude and handoff RGBA; independent original table and approved PNG; other GUI areas, device audio and gameplay not claimed'}
    if args.mode!='gui':
        report.update(isolation(root,args.control))
        report['frames_after_retirement']=sum(row['step']>=p['stop_step'] for row in logs)
    if args.mode=='escape':
        assert args.escape_ms in [15600,17550]
        assert p['stop_reason'] in ['escape','story-background']
        assert final['pam_loaded']
        report['ordinary_Esc_virtual_ms']=args.escape_ms
    if args.mode=='normal':
        report['broken_isolation']=isolation(args.broken,args.control)
        broken=read(args.broken/'gui-final.json')['intro_story']
        assert broken['prelude']['loaded'] is False and 'SHA-256' in broken['prelude_error']
        assert broken['hd_background'] and not broken['load_error'] and not broken['background_error']
        for a,b in zip(stream(args.broken/'presentation.frames.gz'),stream(args.control/'presentation.frames.gz'),strict=True):assert a==b
        report['broken_frames_same_control']=len(metadata(args.broken))
        report['Frame_purity']+=read(args.broken/'gui-final.json')['frame_pure_count']
        assert counts['handoff']>0 and final['intro_story']['stats']['Calls']==888 and final['intro_story']['stats']['Pages']==5 and final['pam_loaded']
    (root/'prelude-pixel-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
