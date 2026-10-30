#!/usr/bin/env python3
"""Controlled confirmation/UI integration; production engine remains unchanged."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,struct,subprocess
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/owned-encounter-ui-r1'
BATCH='owned-encounter-ui-r1'
NEW=['prepare-encounter-ui.py','research-encounter-ui.go','check-encounter-ui.py','prepare-owned-battle-ui.py']
COMMON=['research-owned-army.go','research-owned-world.go','research-owned-defeat.go','research-owned-encounter.go','research-native-progress.go','research-paired-progress.go','research-world-army-port.go','research-world-army-review.go','world-army-review_draw.go','world-army-review_main.go','research-world-army-dismiss.go','world-army-dismiss_draw.go','research-army-presence.go','research-controlled-battle.go','owned-battle-ui.go','owned-battle-ui_draw.go','owned-army-ui.go','owned-army-ui_draw.go','owned-army-ui-xcheck.go','paired-progress-check.go']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def module(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def transform(src,q):
 changes=[]
 for n,replacements in {
  'world-army-review_main.go':[('return g.Engine.AdvanceCycles(100000)','return advanceEncounterUI(g)'),('g.Engine.Key(', 'encounterGuestKey(g, ')],
  'research-army-presence.go':[('[]uint16{0x1713, 0x177a, 0x1782}','[]uint16{0x177a, 0x1782}')],
 }.items():
  p=src/'tools'/n;old=p.read_text();new=old
  for a,b in replacements:assert a in new;new=new.replace(a,b)
  p.write_text(new);changes.append(dict(file=n,before=hashlib.sha256(old.encode()).hexdigest(),after=sha(p),replacements=replacements))
 write(q/'adapter-patches.json',changes)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','audit','archive','verify']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   o=d['objects'][f['sha256']];obj=a.archive/BATCH/o['file'];assert sha(obj)==o['stored_sha256'];b=gzip.decompress(obj.read_bytes());assert len(b)==f['bytes']and hashlib.sha256(b).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-encounter-ui',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL;m=module(r/'tools/prepare-owned-army-ui.py','prior');deps=m.dependencies(r)
 if a.action=='prepare':
  assert not q.exists();q.mkdir();(q/'inputs').mkdir();(q/'ui-assets').mkdir();src=q/'go-src'
  for n in deps['source_inputs']:
   t=src/n;t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,t)
  (src/'tools').mkdir(exist_ok=True)
  for n in COMMON:shutil.copyfile(r/'tools'/n,src/'tools'/n)
  text=(r/'tools/research-owned-army.go').read_text().removeprefix('//go:build ignore\n');text=text[:text.index('func main()')].replace('\n\t"flag"\n','\n');(src/'tools/owned-army-model.go').write_text(text)
  for ext in ['mod','sum']:shutil.copyfile(src/('go.'+ext),q/('probe.'+ext))
  with(q/'probe.mod').open('a')as f:f.write('\nrequire github.com/wicanr2/dosgolem v0.0.0\nreplace github.com/wicanr2/dosgolem => /core\n')
  for n in ['army-catalog.json','combat-catalog.json','seed-world.json','original-save.ay','battle-before.state','PAM.AY']:(q/'inputs'/n).write_bytes(m.stored(r,'controlled-owned-battle-r1','/inputs/'+n))
  (q/'inputs/map01.ay').write_bytes(m.stored(r,'owned-world-army-r1','/port-r2/scratch/map01.ay'))
  (q/'state-reader').write_bytes(m.stored(r,'controlled-owned-battle-r1','/state-reader'));(q/'state-reader').chmod(0o755)
  for case in ['win','retreat']:
   # Use the exact pre-battle Go fixture, with six resources projected into
   # the original save by the existing paired writer at runtime setup.
   receipt=json.loads(m.stored(r,'controlled-owned-battle-r1','/cases/'+case+'/receipt.json'))
   write(q/'inputs'/('world-'+case+'.json'),receipt['world_before'])
  fonts=module(r/'tools/prepare-owned-battle-ui.py','fontgen');fonts.TOOLS=['owned-battle-ui.go','owned-battle-ui_draw.go','research-encounter-ui.go'];fonts.fonts(r,q,m,extra_sources=['world-army-review_draw.go','world-army-dismiss_draw.go'])
  write(q/'baseline.json',deps);transform(src,q);return
 assert read(q/'baseline.json')==deps
 if a.action=='freeze':
  for n in NEW:shutil.copyfile(r/'tools'/n,q/'go-src/tools'/n)
  return
 if a.action=='audit':
  from PIL import Image
  gui=read(q/'gui-r1/receipt.json');assert gui['status']=='passed-controlled-confirmation-go-ui'
  glyphs={v['character']for v in read(q/'ui-assets/army-ui-fonts.json')['glyphs']}
  for n in ['world-army-review_draw.go','world-army-dismiss_draw.go','research-encounter-ui.go']:
   assert {v for v in(r/'tools'/n).read_text()if ord(v)>=128 and v.isprintable()}<=glyphs
  for n in NEW:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n)
  for n in COMMON:
   patches=read(q/'adapter-patches.json');patch=next((p for p in patches if p['file']==n),None)
   if patch:assert sha(r/'tools'/n)==patch['before']and sha(q/'go-src/tools'/n)==patch['after']
   else:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n)
  for n in ['build-r2.log','vet-r2.log','reader-build-r1.log','xcheck-build-r1.log']:assert(q/n).stat().st_size==0
  screens=[];cc=read(q/'inputs/combat-catalog.json')['profiles'];profiles={v['id']:v for v in read(q/'inputs/army-catalog.json')['profiles']}
  for case in gui['cases']:
   folder=q/'gui-r1'/case['case'];decoded=folder/'decoded'
   if not decoded.exists():subprocess.run([str(q/'state-reader'),'-calls',str(folder),'-out',str(decoded)],check=True)
   index=read(decoded/'index.json');ram={n:gzip.decompress((decoded/x['memory_file']).read_bytes())for n,x in index.items()};before,after,returned=[ram[n]for n in ['before-commit.state','after-commit.state','final-map.state']];ds=0x1e880
   allowed=set(range(ds+0x4f2,ds+0x4fe))|set(range(ds+0x54a,ds+0x562))|set(range(ds+0x56e8,ds+0x5718));assert all(a==b or i in allowed for i,(a,b)in enumerate(zip(before,after)))
   old=index['before-commit.state'];new=index['after-commit.state'];bp=old['registers'][5];u16=lambda b,p:struct.unpack_from('<H',b,p)[0];assert old['ip']==0x3733 and new['ip']==0x16e0 and new['registers'][4]==bp+6 and new['registers'][5]==u16(before,ds+bp)
   assert new['registers'][6]==u16(before,ds+bp-0x12)and new['registers'][7]==u16(before,ds+bp-0x10)and new['registers'][:4]==old['registers'][:4]
   assert after[ds+0x54a:ds+0x562]==returned[ds+0x54a:ds+0x562]==bytes([255])*24 and after[ds+0x56e8:ds+0x5718]==returned[ds+0x56e8:ds+0x5718]==bytes([255])*48 and index['final-map.state']['ip']==0xbd3
   final=case['final'];w=final['world'];initial=read(q/'inputs'/('world-'+case['case']+'.json'));rows=json.loads(json.dumps([initial['army']['slots'],initial['encounters']['random:controlled-r1']['enemy']]))
   previous=read(folder/'battle-start.json')['world']['battle']['state'];action_index=0;rounds=0
   for step in final['battle_events']:
    command=step['command']
    if command not in ['enemy','attack','round']:continue
    expected_state=json.loads(json.dumps(previous))
    if command=='round':expected_state['round']+=1;expected_state['acted']=[[False]*6 for _ in range(2)];rounds+=1
    else:
     event=final['combat_events'][action_index];action_index+=1;action=event['action'];side=action['side'];slot=action['source'];target=action['target'];assert side==int(command=='enemy')and not previous['acted'][side][slot]
     expected_state['acted'][side][slot]=True;expected_state['rows'][1-side][target]['count']-=event['loss'];alive=[any(x['count']for x in row)for row in expected_state['rows']];expected_state['result']='win'if not alive[1]else'loss'if not alive[0]else''
    assert step['world']['battle']['state']==expected_state;previous=expected_state
   assert action_index==len(final['combat_events'])and rounds==(13 if case['case']=='win'else 0)
   for e in final['combat_events'] or []:
    act=e['action'];s=rows[act['side']][act['source']];t=rows[1-act['side']][act['target']];damage=s['count']*cc[s['unit']]['attack']//5;n=damage//cc[t['unit']]['hp'];loss=0 if n==0 else t['count']if n>=t['count']-1 else n
    assert damage==e['damage']and loss==e['loss']and e['before']==t['count']and e['after']==t['count']-loss;t['count']-=loss
   expected=json.loads(json.dumps(initial));expected['revision']+=2;survivors=[v for v in rows[0]if v['count']];expected['army']['slots']=survivors+[dict(unit='',count=0)]*(6-len(survivors));expected['encounters']={}
   if case['case']=='win':
    enemy=initial['encounters']['random:controlled-r1']['enemy'];expected['army']['gold']+=sum(v['count']*profiles[v['unit']]['gold']for v in enemy if v['count']);expected['progress']['merit']+=sum(v['count']*profiles[v['unit']]['command']for v in enemy if v['count'])//2;expected['progress']['rank']+=1;expected['army']['recruit_rank']+=1;expected['army']['leadership']+=100;expected['progress']['legacy_04f6']+=100;expected['progress']['legacy_04fc']+=6;assert len(final['combat_events'])==28
   else:expected['army']['gold']-=initial['army']['gold']//4;assert len(final['combat_events'])==1
   assert w==expected==case['cold']['snapshot']['world']and final['battle_native_calls']==0 and final['battle_finished']and final['encounter_confirmed']
   native=(q/('session-'+case['case'])/'gamedata.ay').read_bytes();assert native[12:]==(q/'inputs/original-save.ay').read_bytes()[12:]
   words=[w['progress']['rank'],w['progress']['merit'],w['progress']['legacy_04f6'],w['army']['gold'],w['army']['leadership'],w['progress']['legacy_04fc']];assert [u16(returned,ds+0x4f2+i*2)for i in range(6)]==words==[(u16(native,i*2)-i*2-3)&65535 for i in range(6)]
   commands=final['battle_events'];assert next(x for x in commands if x['command']=='confirmation')['ax']==1 and commands[-1]['command']=='return'and commands[-1]['ip']==0xbd3
   assert case['paused']['steps_equal']and case['paused']['cycles_equal']and case['paused']['updates']>=3
   for s in case['screens']:
    folder=q/'gui-r1'/case['case'];png=Image.open(folder/s['canvas']);screen=Image.open(folder/s['screen']);assert png.size==screen.size==(1920,1200)and png.convert('RGB').tobytes()==screen.convert('RGB').tobytes();meta=read(folder/s['metadata']);assert hashlib.sha256(png.convert('RGBA').tobytes()).hexdigest()==meta['canvas_sha256']==meta['presented_sha256']
    for t in meta['text_fields']or []:
     box,ink=t['Rect'],t['Ink'];assert 0<=box[0]<box[2]<=1920 and 0<=box[1]<box[3]<=1200
     if ink[2]>ink[0]:assert box[0]<=ink[0]<ink[2]<=box[2]and box[1]<=ink[1]<ink[3]<=box[3]
    screens.append(dict(case=case['case'],sha256=sha(folder/s['canvas'])))
  write(a.out,dict(status='passed-controlled-confirmation-and-go-ui',dependencies=deps,source_tools={n:sha(r/'tools'/n)for n in NEW+COMMON},adapter_patches=read(q/'adapter-patches.json'),screens=screens,cases=gui['cases'],controlled_memory=True,normal_player_path=False,production_changed=False));return
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for f in sorted(q.rglob('*')):
  if not f.is_file()or 'build-cache'in f.relative_to(q).parts:continue
  assert f.stat().st_uid==1000 and not f.is_symlink();b=f.read_bytes();h=hashlib.sha256(b).hexdigest();obj=folder/(h+'.gz')
  if h not in objects:obj.write_bytes(gzip.compress(b,compresslevel=6,mtime=0));objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(b),mode=f.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Local original snapshots and full images excluded from Git.'))
if __name__=='__main__':main()
