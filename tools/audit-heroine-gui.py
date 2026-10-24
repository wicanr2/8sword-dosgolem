#!/usr/bin/env python3
"""033：按實際 Draw 記錄逐幀核對畫作與原版前景，不用即時狀態猜畫面。"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct
from PIL import Image

def audit(root,legacy,assets):
    final=json.loads((root/'gui-final.json').read_text());metadata=[json.loads(line) for line in (root/'intro-draw.jsonl').read_text().splitlines()];assert final['closed'] and final['heroine_error']==''
    stats=final['heroine']['stats'];assert stats['Retired'] and stats['Portraits']==1 and stats['UnknownWrites']==stats['Timeouts']==0 and not stats['Errors']
    raw=(legacy/'TIT4.AY.decoded').read_bytes();actor=raw[24876:24876+2764];assert hashlib.sha256(actor).hexdigest()=='222fb53822fa45e54ba2b22704dd79f3da698c8a09f5f1fdccfc9615cc1e25d5'
    idx=(legacy/'cold-trace/frame-020.idx').read_bytes();rgb=Image.open(legacy/'cold-trace/frame-020.png').convert('RGB').tobytes();palette={}
    for i,index in enumerate(idx):
        color=rgb[i*3:i*3+3];assert index not in palette or palette[index]==color;palette[index]=color
    art=Image.open(assets/'intro-heroine.png').convert('RGBA');assert hashlib.sha256((assets/'intro-heroine.png').read_bytes()).hexdigest()=='9a9775fcf7c58ac5c60e8b8e1774858c6527d580801d5d04920b4c419f0b09f8'
    expected=art.copy();preserved=0
    for y in range(20):
        for x in range(80):
            i=y*10+x//8;bit=7-x%8
            if actor[4+5*460+i]&(1<<bit):
                index=sum(((actor[4+plane*460+i]>>bit)&1)<<plane for plane in range(4));color=tuple(palette[index])+(255,)
                expected.paste(color,((112+x)*3,(80+y)*6,(113+x)*3,(81+y)*6));preserved+=1
    assert preserved==366;target=expected.tobytes();positive=[];held=[];frames=0
    with gzip.open(root/'presentation.frames.gz','rb') as f:
        def read(n):
            b=f.read(n);assert len(b)==n;return b
        assert read(8)==b'8SFRM001';width,height=struct.unpack('<II',read(8));assert (width,height)==(2944,1264);rgba=bytearray(width*height*4)
        while header:=f.read(24):
            ordinal,step,rows=struct.unpack('<QQQ',header);assert ordinal==frames+1 and rows<=height;seen=set()
            for _ in range(rows):
                y,=struct.unpack('<H',read(2));assert y<height and y not in seen;seen.add(y);rgba[y*width*4:(y+1)*width*4]=read(width*4)
            info=metadata[frames];assert info['draw']==ordinal and info['step']==step;frames+=1
            crop=b''.join(rgba[(y*width+848)*4:(y*width+2120)*4] for y in range(184,784));pixels=info.get('heroine_pixels',0)
            if pixels>0:
                assert pixels==42034 and crop==target,('actual Draw heroine/foreground pixels',ordinal)
                positive.append({'draw':ordinal,'step':step,'font_id':info['font_id'],'native_pixels':pixels})
                if len(positive)==1:Image.frombytes('RGBA',(width,height),bytes(rgba)).save(root/'heroine-first-actual-draw.png')
            elif pixels==0:
                assert crop!=target,('stale portrait after ownership ended',ordinal)
            else:held.append(ordinal)
    assert frames==len(metadata)==final['recorded_frames'] and positive and final['presented_heroine_pixels']==0
    result={'status':'passed-actual-draw-heroine-and-foreground','frames':frames,'portrait_draws':positive,'held_draws':held,'masked_native_pixels_per_portrait':366,'errors':stats['Errors'],'toolbar_cached_identical_pixels':final['toolbar_cached_pixels'],'toolbar_rendered_frames':final['toolbar_rendered_frames'],'recording_sha256':hashlib.sha256((root/'presentation.frames.gz').read_bytes()).hexdigest(),'scope':'Full portrait rect equals verified HD cache plus independently decoded original sixth-block foreground; no stale portrait in unowned Draws. Whole museum art remains separate.'}
    (root/'heroine-draw-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--legacy',type=Path,required=True);p.add_argument('--assets',type=Path,required=True);p.add_argument('receipts',type=Path,nargs='+');a=p.parse_args()
    for root in a.receipts:audit(root,a.legacy,a.assets)
