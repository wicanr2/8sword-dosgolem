#!/usr/bin/env python3
"""030 DRAFT: fixed F2 review input/fonts, independent audit and preservation."""
import argparse,gzip,hashlib,importlib.util,io,json,os,shutil,struct
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,__version__
REL='workplace/probe-20261023/graphics-first/battle-r1/owned-world-army-view-r1'
BATCH='owned-world-army-view-r1'
TOOLS=['export-world-army-view-ida.py','research-world-army-review.go','world-army-review_draw.go','world-army-review_main.go','research-world-army-review_test.go','prepare-world-army-review.py','check-world-army-review.py','world-army-review.sh']
REUSE=['research-owned-army.go','research-owned-world.go','research-native-progress.go','research-paired-progress.go','research-world-army-port.go','owned-army-ui.go','owned-army-ui_draw.go','owned-army-ui-xcheck.go','prepare-owned-army-ui.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def lib(r):
 s=importlib.util.spec_from_file_location('prior',r/'tools/prepare-owned-army-ui.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def fonts(r,q,m,extra=()):
 assert __version__=='11.3.0';index=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));faces={}
 for id,h in m.FONT_SHA.items():
  raw=gzip.decompress((r/'preserved'/index['objects'][h]['path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==h;faces[id]=ImageFont.truetype(io.BytesIO(raw),48,index=3 if id in ['noto','serif']else 0)
 chars={chr(n)for n in range(32,127)}|{'…','　'}
 for n in ['world-army-review_draw.go','world-army-review_main.go',*extra]:chars.update(c for c in(r/'tools'/n).read_text()if ord(c)>=128 and c.isprintable())
 for p in read(q/'inputs/army-catalog.json')['profiles']:chars.update(p['name'])
 chars=sorted(chars);glyphs=[dict(character=c,cell=[i%16*64,i//16*64,64,64])for i,c in enumerate(chars)];height=((len(chars)+15)//16)*64;profiles=[]
 for id in ['noto','lishu','caoshu']:
  face=faces[id];missing=face.getmask('\U0010ffff');missing=(missing.size,bytes(missing));atlas=Image.new('RGBA',(1024,height));fallbacks=[]
  for i,c in enumerate(chars):
   if c in [' ','　']:continue
   mask=face.getmask(c);cjk=0x3400<=ord(c)<=0x9fff;primary=id=='noto'or(cjk and(mask.size,bytes(mask))!=missing and bool(mask.getbbox()));selected=face if primary else faces['serif']if id=='lishu'and cjk else faces['noto']
   if not primary:fallbacks.append(c)
   box=selected.getbbox(c);assert box[2]>box[0]and box[3]>box[1];ink=Image.new('RGBA',(box[2]-box[0],box[3]-box[1]));ImageDraw.Draw(ink).text((-box[0],-box[1]),c,font=selected,fill='white');ink.thumbnail((48,52),Image.Resampling.LANCZOS);atlas.paste(ink,(i%16*64+(64-ink.width)//2,i//16*64+(64-ink.height)//2))
  name='army-ui-'+id+'.png';atlas.save(q/'ui-assets'/name);profiles.append(dict(id=id,file=name,sha=sha(q/'ui-assets'/name),source_sha256=m.FONT_SHA[id],width=1024,height=height,fallbacks=len(fallbacks)))
 write(q/'ui-assets/army-ui-fonts.json',dict(schema=1,army_catalog_sha256=sha(q/'inputs/army-catalog.json'),glyphs=glyphs,profiles=profiles,font_sources=m.FONT_SHA))
 for name in ['font-choice-lishu-NOTICE.txt','font-choice-lishu-LICENSE.txt','font-choice-caoshu-LICENSE.txt']:shutil.copyfile(r/'workplace/player/assets-painted-r69'/name,q/'ui-assets'/name)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','audit','archive','verify','integrity']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--out',type=Path);p.add_argument('--audit',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'));seen=set()
  for f in d['files']:
   assert not Path(f['path']).is_absolute()and'..'not in Path(f['path']).parts;o=d['objects'][f['sha256']];p=a.archive/BATCH/o['file'];assert sha(p)==o['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256'];seen.add(f['sha256'])
  write(a.out,dict(status='passed-detached-army-review',files=len(d['files']),objects=len(seen),workplace_required=False));return
 r=a.project;q=r/REL;m=lib(r);deps=m.dependencies(r)
 if a.action=='prepare':
  assert{p.name for p in q.iterdir()}=={'ida'}and q.stat().st_uid==1000;(q/'inputs').mkdir();(q/'ui-assets').mkdir();src=q/'go-src'
  for n in deps['source_inputs']:
   t=src/n;t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,t)
  (src/'tools').mkdir(exist_ok=True)
  for n in TOOLS+REUSE:shutil.copyfile(r/'tools'/n,src/'tools'/n)
  t=(r/'tools/research-owned-army.go').read_text().removeprefix('//go:build ignore\n');t=t[:t.index('func main()')].replace('\n\t"flag"\n','\n');(src/'tools/owned-army-model.go').write_text(t)
  for ext in ['mod','sum']:shutil.copyfile(src/('go.'+ext),q/('probe.'+ext))
  with(q/'probe.mod').open('a')as f:f.write('\nrequire github.com/wicanr2/dosgolem v0.0.0\nreplace github.com/wicanr2/dosgolem => /core\n')
  for n in ['army-catalog.json','combat-catalog.json']:(q/'inputs'/n).write_bytes(m.stored(r,'owned-world-army-r1','/inputs/'+n))
  native=m.stored(r,'owned-world-army-r1','/port-r2/paired-save/gamedata.ay');world=m.stored(r,'owned-world-army-r1','/port-r2/paired-save/gamedata.ay.army.json');(q/'inputs/review-save.json').write_bytes(world)
  (q/'inputs/map01.ay').write_bytes(m.stored(r,'owned-world-army-r1','/port-r2/scratch/map01.ay'))
  for name in ['session-r1','session-preview-r1']:
   folder=q/name;folder.mkdir();(folder/'gamedata.ay').write_bytes(native);(folder/'gamedata.ay.army.json').write_bytes(world)
  fonts(r,q,m);write(q/'baseline-r1.json',deps);return
 if a.action=='audit':
  gui=read(q/'gui-r1/receipt.json');assert gui['status']=='passed-actual-f2-review'and gui['cold_equal']and gui['font_hold_once']and gui['go_native_draw_calls']==0
  ida=read(q/'ida/ida-army-view-r1.json');raw=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();assert ida['source_sha256']==hashlib.sha256(raw).hexdigest()and ida['exporter_sha256']==sha(r/'tools/export-world-army-view-ida.py');header=struct.unpack_from('<H',raw,8)[0]*16;reloc=[]
  for i in range(struct.unpack_from('<H',raw,6)[0]):off,seg=struct.unpack_from('<HH',raw,struct.unpack_from('<H',raw,24)[0]+i*4);reloc.append(header+seg*16+off)
  lines=0
  for b in ida['functions']:
   for l in b['lines']:
    pos=l['file_offset'];want=bytes.fromhex(l['bytes']);actual=bytearray(raw[pos:pos+len(want)]);assert pos==l['ida_linear']-0x10000+header
    for loc in reloc:
     if pos<=loc and loc+2<=pos+len(want):struct.pack_into('<H',actual,loc-pos,(struct.unpack_from('<H',actual,loc-pos)[0]+0x1000)&65535)
    assert bytes(actual)==want;lines+=1
  for s in gui['screens']:
   folder=q/'gui-r1'/s['phase'];im=Image.open(folder/s['canvas']);screen=Image.open(folder/s['screen']);assert im.size==screen.size==(1920,1200)and im.convert('RGB').tobytes()==screen.convert('RGB').tobytes();state=read(folder/s['metadata']);assert hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()==state['canvas_sha256']==state['presented_sha256']
   for f in state['text_fields']or[]:
    rect,ink=f['Rect'],f['Ink'];assert ink==[0,0,0,0]or(rect[0]<=ink[0]<=ink[2]<=rect[2]and rect[1]<=ink[1]<=ink[3]<=rect[3])
  for n in ['gamedata.ay','gamedata.ay.army.json']:assert sha(q/'session-r1'/n)==gui['pair_before'][n]==gui['pair_after'][n]
  for n in TOOLS+REUSE:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n)
  text=(q/'go-test-r1.log').read_text();assert'PASS'in text and'FAIL'not in text and'SKIP'not in text
  for n in ['go-vet-r2.log','go-build-r2.log','xcheck-build-r1.log']:assert(q/n).stat().st_size==0
  write(a.out,dict(status='passed-draft-f2-review',dependencies=deps,source_tools={n:sha(r/'tools'/n)for n in TOOLS+REUSE},ida_functions=3,ida_lines=lines,gui=gui,production_changed=False,limits=['Read-only F2 on the controlled existing Go save; dismissal and full world handoff remain blocked.','Actual GUI tested with software rendering and muted device output; PCM still generated.','Native-dispatch control capture retains the map in the HD presenter; it is a control-flow receipt, not an original F2 visual oracle.','Only the observed display mode is dynamically verified; alternate-mode coverage remains limited.']));return
 if a.action=='archive':
  receipt=a.audit or q/'audit-r1.json';d=read(receipt);assert d['source_tools']=={n:sha(r/'tools'/n)for n in TOOLS+REUSE};folder=a.archive/BATCH;folder.mkdir();objects={};files=[];selected={p for p in q.rglob('*')if p.is_file()};selected.update(r/'tools'/n for n in TOOLS+REUSE);selected.add(r/'docs/spec/030-battle-expansion-proposal.md')
  for f in sorted(selected):
   assert not f.is_symlink()and f.stat().st_uid==1000;raw=f.read_bytes();h=hashlib.sha256(raw).hexdigest()
   if h not in objects:
    name=h+'.gzip';blob=gzip.compress(raw,compresslevel=6,mtime=0);(folder/name).write_bytes(blob);objects[h]=dict(file=name,stored_sha256=hashlib.sha256(blob).hexdigest(),stored_bytes=len(blob))
   files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(raw),mode=f.stat().st_mode&0o777))
  write(a.archive/(BATCH+'.json'),dict(files=files,objects=objects,dependencies=deps,audit_sha256=sha(receipt)));write(a.out,dict(status='preserved-f2-review',files=len(files),objects=len(objects),stored_bytes=sum(v['stored_bytes']for v in objects.values())));return
 assert not read(a.archive/'owned-world-army-view-verification-r1.json')['workplace_required'];art=read(r/'artwork/manifest.json');assert len(art['files'])==1040
 for f in art['files']:assert sha(r/'artwork'/f['path'])==f['sha256']
 write(a.out,dict(status='passed-f2-review-integrity',source_inputs=197,programs=7,core=923,assets=535,artwork=1040,production_changed=False))
if __name__=='__main__':main()
