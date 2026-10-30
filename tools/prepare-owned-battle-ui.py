#!/usr/bin/env python3
"""030 DRAFT: Go battle UI inputs, independent pixel/state audit and preservation."""
import argparse,gzip,hashlib,importlib.util,io,json,os,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,__version__

REL='workplace/probe-20261023/graphics-first/battle-r1/owned-battle-ui-r1'
TOOLS=['owned-battle-ui.go','owned-battle-ui_draw.go','owned-battle-ui_main.go','owned-battle-ui_test.go','prepare-owned-battle-ui.py','check-owned-battle-ui.py','owned-battle-ui.sh']
REUSE=['owned-army-ui.go','owned-army-ui_draw.go','owned-army-ui-xcheck.go','research-owned-army.go','research-owned-world.go','prepare-owned-army-ui.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def lib(r):
 s=importlib.util.spec_from_file_location('old_ui',r/'tools/prepare-owned-army-ui.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def fonts(r,q,m):
 assert __version__=='11.3.0';catalog=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));faces={}
 for id,h in m.FONT_SHA.items():
  raw=gzip.decompress((r/'preserved'/catalog['objects'][h]['path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==h
  faces[id]=ImageFont.truetype(io.BytesIO(raw),48,index=3 if id in ('noto','serif') else 0)
 chars={chr(i) for i in range(32,127)}|{'…','　'}
 for name in TOOLS[:3]+['owned-army-ui.go','owned-army-ui_draw.go','research-owned-army.go','research-owned-world.go']:
  chars.update(c for c in (r/'tools'/name).read_text() if ord(c)>=128 and c.isprintable())
 chars.update(c for c in (r/'internal/eightsword/owned_combat.go').read_text() if ord(c)>=128 and c.isprintable())
 for p in read(q/'inputs/army-catalog.json')['profiles']:chars.update(p['name'])
 chars=sorted(chars);height=(len(chars)+15)//16*64;profiles=[]
 for id in ['noto','lishu','caoshu']:
  face=faces[id];missing=face.getmask('\U0010ffff');missing=(missing.size,bytes(missing));atlas=Image.new('RGBA',(1024,height));fallback=[]
  for i,c in enumerate(chars):
   if c in (' ','　'):continue
   mask=face.getmask(c);cjk=0x3400<=ord(c)<=0x9fff;primary=id=='noto' or cjk and (mask.size,bytes(mask))!=missing and bool(mask.getbbox())
   selected=face if primary else faces['serif'] if id=='lishu' and cjk else faces['noto']
   if not primary:fallback.append(c)
   box=selected.getbbox(c);assert box[2]>box[0] and box[3]>box[1]
   ink=Image.new('RGBA',(box[2]-box[0],box[3]-box[1]));ImageDraw.Draw(ink).text((-box[0],-box[1]),c,font=selected,fill='white');ink.thumbnail((48,52),Image.Resampling.LANCZOS)
   atlas.paste(ink,(i%16*64+(64-ink.width)//2,i//16*64+(64-ink.height)//2))
  name='army-ui-'+id+'.png';atlas.save(q/'ui-assets'/name);profiles.append(dict(id=id,file=name,sha=sha(q/'ui-assets'/name),source_sha256=m.FONT_SHA[id],width=1024,height=height,fallbacks=len(fallback),fallback_characters=''.join(fallback)))
 write(q/'ui-assets/army-ui-fonts.json',dict(schema=1,army_catalog_sha256=sha(q/'inputs/army-catalog.json'),glyphs=[dict(character=c,cell=[i%16*64,i//16*64,64,64]) for i,c in enumerate(chars)],profiles=profiles,font_sources=m.FONT_SHA,pillow=__version__))
 old=r/'workplace/player/assets-painted-r69'
 for name in ['font-choice-lishu-NOTICE.txt','font-choice-lishu-LICENSE.txt','font-choice-caoshu-LICENSE.txt']:shutil.copyfile(old/name,q/'ui-assets'/name)
 (q/'ui-assets/font-NOTICE.txt').write_text('字型沿正式原檔：Noto Sans CJK TC Black、教育部隸書3.00、劉建毛草。原字型未修改。\n隸書缺中文採Noto Serif CJK TC，英數與標點採Noto Black。字圖含控制器與戰鬥核心的提示字元。\n')
def verify(a,out):
 d=read(a/'owned-battle-ui-r1.json');checked=set()
 for f in d['files']:
  assert not Path(f['path']).is_absolute() and '..' not in Path(f['path']).parts
  obj=d['objects'][f['sha256']];p=a/'owned-battle-ui-r1'/obj['file'];assert sha(p)==obj['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes'] and hashlib.sha256(raw).hexdigest()==f['sha256'];checked.add(f['sha256'])
 write(out,dict(status='passed-detached-owned-battle-ui',files=len(d['files']),objects=len(checked),workplace_required=False,index_sha256=sha(a/'owned-battle-ui-r1.json')))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','audit','archive','verify','integrity']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--out',type=Path);p.add_argument('--audit',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists() and os.getuid()==1000
 if a.action=='verify':verify(a.archive,a.out);return
 r=a.project;q=r/REL;m=lib(r);deps=m.dependencies(r)
 if a.action=='prepare':
  assert not q.exists() and q.parent.stat().st_uid==1000;q.mkdir()
  for n in ['inputs','ui-assets','session-r1','session-preview-r1']:(q/n).mkdir()
  for n in ['army-catalog.json','combat-catalog.json','original-save.ay']:(q/'inputs'/n).write_bytes(m.stored(r,'owned-world-r1','/inputs/'+n))
  flow=json.loads(m.stored(r,'owned-world-r1','/flow-r2/receipt.json'));w=flow['initial'];w['army']['gold']=5000;w['army']['slots']=[dict(unit='',count=0) for _ in range(6)];w['army']['offers']['wolf-camp']['stock']=1000
  write(q/'inputs/seed-world.json',w)
  for n in ['session-r1','session-preview-r1']:shutil.copyfile(q/'inputs/original-save.ay',q/n/'gamedata.ay')
  src=q/'go-src'
  for n in deps['source_inputs']:
   target=src/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,target)
  (src/'tools').mkdir(exist_ok=True)
  for n in TOOLS+REUSE:shutil.copyfile(r/'tools'/n,src/'tools'/n)
  text=(r/'tools/research-owned-army.go').read_text().removeprefix('//go:build ignore\n');text=text[:text.index('func main()')].replace('\n\t"flag"\n','\n');(src/'tools/owned-army-model.go').write_text(text)
  for suffix in ['mod','sum']:shutil.copyfile(src/('go.'+suffix),q/('probe.'+suffix))
  with (q/'probe.mod').open('a') as f:f.write('\nrequire github.com/wicanr2/dosgolem v0.0.0\nreplace github.com/wicanr2/dosgolem => /core\n')
  fonts(r,q,m);write(q/'baseline-r1.json',deps);return
 if a.action=='audit':
  gui=read(q/'gui-r1/receipt.json');assert gui['status']=='passed-real-go-battle-ui' and gui['actions']==28 and gui['mid_cold_equal'] and gui['final_cold_equal'] and gui['duplicate_enemy_rejected'] and gui['duplicate_reward_rejected']
  for item in gui['screens']:
   folder=q/'gui-r1'/item['phase'];png=Image.open(folder/item['canvas']);ppm=Image.open(folder/item['screen']);assert png.size==ppm.size==(1920,1200);assert png.convert('RGB').tobytes()==ppm.convert('RGB').tobytes()
   meta=read(folder/item['metadata']);assert hashlib.sha256(png.convert('RGBA').tobytes()).hexdigest()==meta['canvas_sha256']==meta['presented_sha256']
   for f in meta['text_fields']:
    box,ink=f['Rect'],f['Ink'];assert 0<=box[0]<box[2]<=1920 and 0<=box[1]<box[3]<=1200
    if ink[2]>ink[0]:assert box[0]<=ink[0]<ink[2]<=box[2] and box[1]<=ink[1]<ink[3]<=box[3]
  assert {item['font'] for item in gui['screens']}=={'noto','lishu','caoshu'}
  # Independently replay each adjacent saved state using catalog scalars. This
  # fixture has one front-row non-native melee stack per side, no special effects.
  cc=read(q/'inputs/combat-catalog.json')['profiles'];actions=0;previous=None;rounds=0
  commits=[]
  for phase in ['fresh','resumed','final']:
   commits.extend(sorted((q/'gui-r1'/phase).glob('commit-*.json')))
  for p in commits:
   cur=read(p)['world'];b=cur['battle']
   if previous is not None and b and previous['battle']:
    old=previous['battle']['state'];new=b['state']
    if old!=new and old['round']==new['round']:
     changed=[(side,i) for side in range(2) for i in range(6) if old['acted'][side][i]!=new['acted'][side][i]];assert len(changed)==1;side,i=changed[0];assert i==0 and new['acted'][side][i]
     source=old['rows'][side][i];target=old['rows'][1-side][0];amount=source['count']*cc[source['unit']]['attack']//old['config']['divisors'][side]*old['config']['multipliers'][side];n=amount//cc[target['unit']]['hp'];loss=0 if n==0 else target['count'] if n>=target['count']-1 else n
     expected=json.loads(json.dumps(old));expected['acted'][side][i]=True;expected['rows'][1-side][0]['count']-=loss
     alive=[any(v['count'] for v in row) for row in expected['rows']];expected['result']='win' if not alive[1] else 'loss' if not alive[0] else '';assert new==expected;actions+=1
    elif old['round']!=new['round']:
     expected=json.loads(json.dumps(old));expected['round']+=1;expected['acted']=[[False]*6 for _ in range(2)];assert new==expected;rounds+=1
   previous=cur
  assert actions==28 and rounds==13
  final=gui['final_world'];assert final['army']['gold']==4400 and final['army']['slots'][0]['count']==29 and final['army']['leadership']==1100 and final['progress']['merit']==2012 and final['progress']['rank']==2 and final['army']['offers']['wolf-camp']['stock']==970
  pack=read(q/'ui-assets/army-ui-fonts.json')
  for p in pack['profiles']:assert sha(q/'ui-assets'/p['file'])==p['sha'] and p['source_sha256']==m.FONT_SHA[p['id']]
  test=(q/'go-test-r4.log').read_text();assert 'PASS' in test and 'FAIL' not in test and 'SKIP' not in test
  write(a.out,dict(status='passed-draft-owned-battle-ui',dependencies=deps,source_tools={n:sha(r/'tools'/n) for n in TOOLS+REUSE},gui=gui,independently_replayed_actions=actions,round_transitions=rounds,production_changed=False,guest_instructions=0,limits=['Explicit UI fixtures and operator-selected action order; no normal original-world path.','Special actions, retreat and defeat world handoff remain outside this UI.']))
  return
 if a.action=='archive':
  receipt=a.audit or q/'audit-r1.json';d=read(receipt);assert d['source_tools']=={n:sha(r/'tools'/n) for n in TOOLS+REUSE};folder=a.archive/'owned-battle-ui-r1';folder.mkdir();files=[];objects={};selected={p for p in q.rglob('*') if p.is_file()};selected.update(r/'tools'/n for n in TOOLS+REUSE);selected.add(r/'docs/spec/030-battle-expansion-proposal.md')
  for p in sorted(selected):
   assert not p.is_symlink() and p.stat().st_uid==1000;raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest()
   if h not in objects:
    name=h+'.gzip';blob=gzip.compress(raw,compresslevel=6,mtime=0);(folder/name).write_bytes(blob);objects[h]=dict(file=name,stored_sha256=hashlib.sha256(blob).hexdigest(),stored_bytes=len(blob))
   files.append(dict(path=str(p.relative_to(r)),sha256=h,bytes=len(raw),mode=p.stat().st_mode&0o777))
  write(a.archive/'owned-battle-ui-r1.json',dict(files=files,objects=objects,dependencies=deps,audit_sha256=sha(receipt)));write(a.out,dict(status='preserved-owned-battle-ui',files=len(files),objects=len(objects),stored_bytes=sum(v['stored_bytes'] for v in objects.values())));return
 assert read(a.archive/'owned-battle-ui-verification-r1.json')['workplace_required'] is False
 art=read(r/'artwork/manifest.json');assert len(art['files'])==1040
 for f in art['files']:assert sha(r/'artwork'/f['path'])==f['sha256']
 for d in [q,a.archive/'owned-battle-ui-r1']:assert all(p.stat().st_uid==1000 for p in d.rglob('*'))
 write(a.out,dict(status='passed-owned-battle-ui-integrity',source_inputs=197,programs=7,core=923,assets=535,artwork=1040,production_changed=False))
if __name__=='__main__':main()
