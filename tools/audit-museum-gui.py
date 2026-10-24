#!/usr/bin/env python3
"""017：獨立重建實際寬版 Draw 的博物館美術帶；不冒稱 GUI 客體對拍。"""
import argparse,gzip,hashlib,json,runpy,struct
from pathlib import Path
from PIL import Image,ImageChops

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('gui',type=Path)
parser.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[1])
parser.add_argument('--assets',type=Path,required=True)
parser.add_argument('--research',type=Path,required=True)
args=parser.parse_args()
model=runpy.run_path(str(Path(__file__).with_name('audit-museum.py')))
model['load_model'](args.project,args.assets,args.research)
context=model['render'].__globals__
first={};metadata=[];root=args.gui
title_checks=[];title_sources={};last_title={}
listing=json.loads((args.assets/"intro.json").read_text())
title_sources["noto"]=(listing["file"],listing["sha256"])
for profile in json.loads((args.assets/"font-choices.json").read_text())["profiles"]:title_sources[profile["id"]]=(profile["title"],profile["title_sha256"])
title_cache={}

def stream(path):
 global first
 with gzip.open(path,'rb') as source:
  assert source.read(8)==b'8SFRM001'
  width,height=struct.unpack('<II',source.read(8));assert (width,height)==(2944,1264)
  pixels=bytearray(width*height*4);number=0;previous=0
  while header:=source.read(24):
   assert len(header)==24
   ordinal,step,rows=struct.unpack('<QQQ',header)
   number+=1;assert ordinal==number and step>=previous and rows<=height
   previous=step;seen=set()
   for _ in range(rows):
    y,=struct.unpack('<H',source.read(2));assert y<height and y not in seen;seen.add(y)
    data=source.read(width*4);assert len(data)==width*4;pixels[y*width*4:(y+1)*width*4]=data
   central=b''.join(pixels[((y+64)*width+512)*4:((y+64)*width+2432)*4] for y in range(1200))
   entry=metadata[number-1];assert entry['draw']==number and entry['step']==step
   stage=entry.get('museum_stage','')
   if entry['stage'] in ['title-noto','title-transition']:
    font=entry['font_id']
    if font not in title_cache:
     name,want=title_sources[font];png=args.assets/name;assert hashlib.sha256(png.read_bytes()).hexdigest()==want
     ink=Image.open(png).convert('RGBA');assert ink.size==(1776,570)
     alpha=ink.getchannel('A');opaque=alpha.point(lambda a:255 if a==255 else 0);clear=alpha.point(lambda a:255 if a==0 else 0)
     title_cache[font]=(ink.convert('RGB'),opaque,clear)
    ink,opaque,clear=title_cache[font]
    actual=Image.frombytes('RGBA',(1920,1200),central).crop((48,300,1824,870)).convert('RGB')
    assert ImageChops.multiply(ImageChops.difference(actual,ink),opaque.convert('RGB')).getbbox() is None,('title opaque glyph differs',number,font)
    assert ImageChops.multiply(actual,clear.convert('RGB')).getbbox() is None,('title transparent background differs',number,font)
    if entry['stage']=='title-transition' and font in last_title:assert central==last_title[font],('title hold changed',number)
    if entry['stage']=='title-noto':last_title[font]=central
    title_checks.append({'draw':number,'stage':entry['stage'],'font':font})

   if stage and stage not in first:
    Image.frombytes('RGBA',(1920,1200),central).save(root/('museum-'+stage+'-first-actual-draw.png'))
    Image.frombytes('RGBA',(width,height),bytes(pixels)).save(root/('museum-'+stage+'-first-wide-draw.png'))
    first[stage]={'actual_Draw':number,'step':step,'central_rgba_sha256':hashlib.sha256(central).hexdigest()}
   yield number,step,central

context['stream']=stream
final=json.loads((root/'gui-final.json').read_text())
assert final['closed'] and not final['museum_error'] and final['heroine'] is None
assert final['presentation_size']==[2944,1264]
events=final['museum_transactions'];assert len(events)<=512 and events
(root/'museum-transactions.json').write_text(json.dumps(events,indent=2)+'\n')
metadata=[json.loads(line) for line in (root/'intro-draw.jsonl').read_text().splitlines()]
result=model['audit'](root)
assert all(result['independent_draws'].get(stage,0)>0 for stage in ['left','right','portrait','beam','drain'])
assert result['painted_actor_sources']>0 and len(result['beam_tints'])==2
assert title_checks and final['museum'].get('title_handoff_frames',0)>0
result.update(status='PASS-formal-museum-actual-GUI-art-region',first_actual_Draws=first,title_glyph_Draws=len(title_checks),title_handoff_updates=final['museum'].get('title_handoff_frames',0),actual_title_handoff_Draws=sum(x['stage']=='title-transition' for x in title_checks),
              scope='source-defined museum art band on every sampled actual Draw; outside art band uses actual GUI pixels, not paired original GUI oracle',
              limit='headless state/PCM isolation and normal GUI save/exit/reload are separate receipts')
(root/'museum-draw-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
