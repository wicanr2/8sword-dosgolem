#!/usr/bin/env python3
"""033：獨立串流、來源遮罩與客體隔離核對。在固定 Pillow Docker 執行。"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct
from PIL import Image

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frames(root):
    with gzip.open(root/'presentation.frames.gz','rb') as f:
        assert f.read(8)==b'8SFRM001';w,h=struct.unpack('<II',f.read(8));assert (w,h)==(1920,1200);rgba=bytearray(w*h*4);n=0;step0=0
        while header:=f.read(24):
            ordinal,step,rows=struct.unpack('<QQQ',header);assert ordinal==n+1 and step>=step0 and rows<=h;n=ordinal;step0=step
            seen=set()
            for _ in range(rows):
                y,=struct.unpack('<H',f.read(2));assert y<h and y not in seen;seen.add(y);data=f.read(w*4);assert len(data)==w*4;rgba[y*w*4:(y+1)*w*4]=data
            assert ordinal!=1 or rows==h
            yield ordinal,step,bytes(rgba)

def main():
    p=argparse.ArgumentParser()
    for n in ['control','hd','broken','legacy','assets','out']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();roots=[a.control,a.hd,a.broken];statuses=[json.loads((r/'gui-final.json').read_text()) for r in roots]
    for key in ['final.state','audio.pcm']:
        assert len({sha(r/key) for r in roots})==1,key
    scratch=[{f.relative_to(r/'scratch').as_posix():sha(f) for f in (r/'scratch').rglob('*') if f.is_file()} for r in roots];assert scratch[0]==scratch[1]==scratch[2]
    for s in statuses:
        assert s['frame_pure_count']==s['recorded_frames']==428 and s['closed'];assert s['input_events']==statuses[0]['input_events'] and s['file_ops']==statuses[0]['file_ops'] and s['exec_log']==statuses[0]['exec_log']
    stats=statuses[1]['heroine']['stats'];assert stats['Portraits']==1 and stats['Composed']>0 and stats['Retired'] and not stats['Errors'] and stats['Timeouts']==stats['UnknownWrites']==0
    assert statuses[0]['heroine'] is None and statuses[0]['heroine_error']=='' and statuses[2]['heroine'] is None and 'SHA-256' in statuses[2]['heroine_error']
    records={}
    for name,blocks in [('TIT3.AY',4),('TIT4.AY',6),('TIT5.AY',4)]:
        raw=(a.legacy/(name+'.decoded')).read_bytes();off=0
        while off<len(raw):
            w,h=struct.unpack_from('<HH',raw,off);size=4+w*h*blocks;b=raw[off:off+size];records[hashlib.sha256(b).hexdigest()]=(off,w,h,blocks,b);off+=size
        assert off==len(raw)
    events=statuses[1]['heroine']['events'];assert len(events)==218;owners={};event_index=0
    # Verify the actual visible source independently of presenter page metadata.
    original_idx=(a.legacy/'cold-trace/frame-020.idx').read_bytes();original_rgb=Image.open(a.legacy/'cold-trace/frame-020.png').convert('RGB').tobytes();palette={}
    for i,index in enumerate(original_idx):
        color=original_rgb[i*3:i*3+3];assert index not in palette or palette[index]==color;palette[index]=color
    portrait=records['1ad430667a6d06969e1e71e1fa0b1f57453e65865488bbaa3416f86027e8924b'][-1];actor=records['222fb53822fa45e54ba2b22704dd79f3da698c8a09f5f1fdccfc9615cc1e25d5'][-1];native=bytearray()
    for y in range(100):
        for x in range(424):
            index=sum(((portrait[4+pl*5300+y*53+x//8]>>(7-x%8))&1)<<pl for pl in range(4));ax,ay=x-112,y-80
            if 0<=ax<80 and 0<=ay<46 and actor[4+5*460+ay*10+ax//8]&(128>>(ax%8)):
                index=sum(((actor[4+pl*460+ay*10+ax//8]>>(7-ax%8))&1)<<pl for pl in range(4))
            native.extend(palette[index]+b'\xff')
    expected_native=Image.frombytes('RGBA',(424,100),bytes(native)).resize((1272,600),Image.Resampling.NEAREST).tobytes()
    def apply(e):
        assert not e['Invalid'];at=e['At'];page=e['Page']
        if at==0x5b0c:owners.pop(page,None);return
        if at in (0x5d76,0x5d9c):
            owners[page]=bytearray(owners[e['SourcePage']]) if e['SourcePage'] in owners else bytearray(42400);return
        off,w,h,blocks,b=records[e['SourceSHA']];assert (off,w,h,blocks)==(e['RecordOffset'],e['Width'],e['Height'],e['Blocks'])
        if e['SourceSHA']=='1ad430667a6d06969e1e71e1fa0b1f57453e65865488bbaa3416f86027e8924b':
            assert e['Rows']==[page+(y+20)*80+14 for y in range(100)];owners[page]=bytearray([255])*42400;return
        if page not in owners:return
        for yy,row in enumerate(e['Rows']):
            for xx in range(w):
                mask=b[4+5*w*h+yy*w+xx] if blocks==6 else 255;local=row-page+xx
                for bit in range(8):
                    x,y=(local%80)*8+bit-112,local//80-20
                    if mask&(128>>bit) and 0<=x<424 and 0<=y<100:owners[page][y*424+x]=0
    rows=[json.loads(line) for line in (a.hd/'intro-draw.jsonl').read_text().splitlines()];art=Image.open(a.assets/'intro-heroine.png').convert('RGBA');changed=0;foreground=0
    streams=[frames(r) for r in roots]
    for ordinal,group in enumerate(zip(*streams,strict=True),1):
        original,hd,broken=group;assert original[:2]==hd[:2]==broken[:2];assert original[2]==broken[2],('fault fallback',ordinal);row=rows[ordinal-1];assert row['draw']==ordinal and row['step']==hd[1]
        while event_index<len(events) and events[event_index]['Serial']<=row['serial']:apply(events[event_index]);event_index+=1
        pixels=row['heroine_pixels'];expected=Image.frombytes('RGBA',(1920,1200),original[2])
        if pixels>0:
            visible=[mask for mask in owners.values() if sum(v!=0 for v in mask)==pixels];assert len(visible)==1;assert pixels==42034
            assert expected.crop((336,120,1608,720)).tobytes()==expected_native,('visible original source',ordinal)
            mask=Image.frombytes('L',(424,100),bytes(visible[0])).resize((1272,600),Image.Resampling.NEAREST);rect=expected.crop((336,120,1608,720));expected.paste(Image.composite(art,rect,mask),(336,120));changed+=1;foreground+=366
        elif pixels<0:
            raise AssertionError('held frame requires pre-transaction native receipt; do not weaken comparison')
        assert expected.tobytes()==hd[2],('complete RGBA',ordinal)
    assert changed>=3 and ordinal==428
    result={'status':'passed-scoped-heroine-normal-source-and-isolation','frames_per_group':ordinal,'pure_frames':sum(s['frame_pure_count'] for s in statuses),'heroine_frames':changed,'preserved_foreground_native_pixels':foreground,'source_transactions':len(events),'state_sha256':sha(a.hd/'final.state'),'pcm_sha256':sha(a.hd/'audio.pcm'),'scratch_files':len(scratch[0]),'inputs':len(statuses[1]['input_events']),'errors':stats['Errors'],'scope':'Normal cold boot through museum and first story, exact complete presentation difference against original execution control; no all-game or RNG parity claim.'}
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
