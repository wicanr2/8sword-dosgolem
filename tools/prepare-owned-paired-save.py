#!/usr/bin/env python3
"""030 DRAFT: prepare, crash-test, audit and preserve paired progress storage."""
import argparse,base64,gzip,hashlib,importlib.util,json,os,shutil,struct,subprocess
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/owned-paired-save-r1'
TOOLS=['owned-paired-ui.sh','research-paired-progress.go','research-paired-progress_test.go','paired-progress-check.go','owned-paired-ui.go','prepare-owned-paired-save.py','check-owned-paired-ui.py']
REUSE=['research-native-progress.go','research-owned-army.go','research-owned-world.go','owned-army-ui.go','owned-army-ui_draw.go','owned-army-ui-xcheck.go','owned-battle-ui.go','owned-battle-ui_draw.go','owned-battle-ui_main.go','owned-battle-ui_test.go','prepare-owned-army-ui.py']
PHASES=['before-intent','intent-temp','intent-durable','native-temp','native-durable','world-temp','world-durable','cleared']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def lib(r):
 s=importlib.util.spec_from_file_location('prior',r/'tools/prepare-owned-army-ui.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def projection(w):return [w['progress']['rank'],w['progress']['merit'],w['progress']['legacy_04f6'],w['army']['gold'],w['army']['leadership'],w['progress']['legacy_04fc']]
def check_pair(folder,original):
 native=(folder/'gamedata.ay').read_bytes();world=read(folder/'gamedata.ay.army.json');assert len(native)==2987 and native[12:]==original[12:]
 assert world['original_sha256']==digest(native)
 values=[(struct.unpack_from('<H',native,i*2)[0]-i*2-3)&65535 for i in range(6)];assert values==projection(world['world'])
 return world['world']
def verify(a,out):
 d=read(a/'owned-paired-save-r1.json');objects=set()
 for f in d['files']:
  assert not Path(f['path']).is_absolute()and'..'not in Path(f['path']).parts
  obj=d['objects'][f['sha256']];p=a/'owned-paired-save-r1'/obj['file'];assert sha(p)==obj['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes']and digest(raw)==f['sha256'];objects.add(f['sha256'])
 write(out,dict(status='passed-detached-owned-paired-save',files=len(d['files']),objects=len(objects),workplace_required=False,index_sha256=sha(a/'owned-paired-save-r1.json')))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','exercise','audit','archive','verify','integrity']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--out',type=Path);p.add_argument('--audit',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':verify(a.archive,a.out);return
 r=a.project;q=r/REL;deps=None
 if a.action!='exercise':m=lib(r);deps=m.dependencies(r)
 if a.action=='prepare':
  assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir();(q/'inputs').mkdir();(q/'ui-assets').mkdir();src=q/'go-src'
  for n in deps['source_inputs']:
   target=src/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,target)
  (src/'tools').mkdir(exist_ok=True)
  for n in TOOLS+REUSE:shutil.copyfile(r/'tools'/n,src/'tools'/n)
  text=(r/'tools/research-owned-army.go').read_text().removeprefix('//go:build ignore\n');text=text[:text.index('func main()')].replace('\n\t"flag"\n','\n');(src/'tools/owned-army-model.go').write_text(text)
  for ext in ['mod','sum']:shutil.copyfile(src/('go.'+ext),q/('probe.'+ext))
  with(q/'probe.mod').open('a')as f:f.write('\nrequire github.com/wicanr2/dosgolem v0.0.0\nreplace github.com/wicanr2/dosgolem => /core\n')
  for n in ['army-catalog.json','combat-catalog.json','seed-world.json']:(q/'inputs'/n).write_bytes(m.stored(r,'owned-battle-ui-r1','/inputs/'+n))
  (q/'inputs/original-save.ay').write_bytes(m.stored(r,'owned-world-bridge-r1','/inputs/original-save.ay'))
  before=json.loads(m.stored(r,'owned-battle-ui-r1','/gui-r1/resumed/victory-lishu.json'))['world'];after=json.loads(m.stored(r,'owned-battle-ui-r1','/gui-r1/receipt.json'))['final_world'];write(q/'inputs/before-world.json',before);write(q/'inputs/after-world.json',after)
  old=read(r/'preserved/owned-battle-ui-r1.json')
  for f in old['files']:
   if '/ui-assets/'in f['path']:
    name=Path(f['path']).name;(q/'ui-assets'/name).write_bytes(m.stored(r,'owned-battle-ui-r1','/ui-assets/'+name))
  write(q/'baseline-r1.json',deps);return
 if a.action=='exercise':
  fault=q/'faults-r1';fault.mkdir();cases=[];base=(q/'inputs/original-save.ay').read_bytes();before=read(q/'inputs/before-world.json');after=read(q/'inputs/after-world.json')
  def call(mode,dir,world='before-world.json',stop=None,out=None,expected=0):
   cmd=[str(q/'paired-progress'),'-input',str(q/'inputs'),'-dir',str(dir),'-mode',mode,'-world',world]
   if stop:cmd+=['-stop',stop]
   if out:cmd+=['-out',str(out)]
   v=subprocess.run(cmd,capture_output=True,text=True,timeout=20);assert v.returncode==expected,(cmd,v.returncode,v.stdout,v.stderr);return v
  for phase in PHASES:
   d=fault/phase;call('init',d);old=[sha(d/n)for n in ['gamedata.ay','gamedata.ay.army.json']];v=call('commit',d,'after-world.json',phase,expected=91);(fault/(phase+'-stdout.log')).write_text(v.stdout+v.stderr)
   mixed=dict(native_sha256=sha(d/'gamedata.ay'),world_sha256=sha(d/'gamedata.ay.army.json'),intent=(d/'.owned-pair.intent.json').exists());write(fault/(phase+'-before-recovery.json'),mixed)
   call('read',d,out=fault/(phase+'-cold.json'));world=check_pair(d,base);expected=before if phase in PHASES[:2]else after;assert world==expected and not(d/'.owned-pair.intent.json').exists()
   cases.append(dict(phase=phase,exit_code=91,before_hashes=old,interrupted=mixed,recovered_native_sha256=sha(d/'gamedata.ay'),recovered_world_sha256=sha(d/'gamedata.ay.army.json'),recovered='old'if phase in PHASES[:2]else'new'))
  for name in ['session-r1','session-preview-r1']:call('init',q/name,'seed-world.json')
  write(q/'crash-receipt-r1.json',dict(status='passed-eight-real-process-crashes',cases=cases,real_exit_without_defer=True,normal_original_world=False));return
 if a.action=='audit':
  from PIL import Image
  base=(q/'inputs/original-save.ay').read_bytes();crash=read(q/'crash-receipt-r1.json');assert crash['status']=='passed-eight-real-process-crashes'and len(crash['cases'])==8
  before=read(q/'inputs/before-world.json');after=read(q/'inputs/after-world.json')
  for i,v in enumerate(crash['cases']):
   assert v['phase']==PHASES[i]and v['exit_code']==91;d=q/'faults-r1'/v['phase'];assert check_pair(d,base)==(before if i<2 else after)
   cold=read(q/'faults-r1'/(v['phase']+'-cold.json'));assert cold['engine_guard']and cold['snapshot']['world']==(before if i<2 else after)
   assert v['interrupted']['intent']==(2<=i<=6)
   if i in [4,5]:assert v['interrupted']['native_sha256']!=v['before_hashes'][0]and v['interrupted']['world_sha256']==v['before_hashes'][1]
  gui=read(q/'gui-r1/receipt.json');assert gui['status']=='passed-real-go-paired-ui'and gui['actions']==28 and gui['mid_cold_equal']and gui['final_cold_equal'];assert check_pair(q/'session-r1',base)==gui['final_world']
  commits=0
  for phase in ['fresh','resumed','final']:
   folder=q/'gui-r1'/phase
   for p in sorted(folder.glob('commit-*.json')):
    index=p.stem.split('-')[1];native=(folder/('native-'+index+'.ay')).read_bytes();saved=read(p);previous=json.loads(m.stored(r,'owned-battle-ui-r1','/gui-r1/'+phase+'/'+p.name));assert saved['world']==previous['world'];assert saved['original_sha256']==digest(native)and native[12:]==base[12:]
    assert [(struct.unpack_from('<H',native,i*2)[0]-i*2-3)&65535 for i in range(6)]==projection(saved['world']);commits+=1
  for item in gui['screens']:
   folder=q/'gui-r1'/item['phase'];im=Image.open(folder/item['canvas']);screen=Image.open(folder/item['screen']);assert im.size==screen.size==(1920,1200)and im.convert('RGB').tobytes()==screen.convert('RGB').tobytes();meta=read(folder/item['metadata']);assert digest(im.convert('RGBA').tobytes())==meta['canvas_sha256']==meta['presented_sha256']
  assert commits==sum(1 for f in read(r/'preserved/owned-battle-ui-r1.json')['files']if '/gui-r1/' in f['path']and Path(f['path']).name.startswith('commit-'))
  for n in TOOLS+REUSE:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n)
  for n in ['go-vet-r1.log','go-build-r1.log','checker-build-r1.log','xcheck-build-r1.log']:assert(q/n).stat().st_size==0
  test=(q/'go-test-r1.log').read_text();assert'PASS'in test and'FAIL'not in test and'SKIP'not in test
  write(a.out,dict(status='passed-draft-owned-paired-save',dependencies=deps,source_tools={n:sha(r/'tools'/n)for n in TOOLS+REUSE},process_crashes=crash,gui=gui,paired_ui_commits=commits,production_changed=False,limits=['Linux local filesystem, all participants use the paired store.','Process exits tested, not physical power loss, network filesystems or normal expanded-army world gameplay.']));return
 if a.action=='archive':
  receipt=a.audit or q/'audit-r1.json';d=read(receipt);assert d['source_tools']=={n:sha(r/'tools'/n)for n in TOOLS+REUSE};folder=a.archive/'owned-paired-save-r1';folder.mkdir();files=[];objects={};selected={p for p in q.rglob('*')if p.is_file()};selected.update(r/'tools'/n for n in TOOLS+REUSE);selected.add(r/'docs/spec/030-battle-expansion-proposal.md')
  for p in sorted(selected):
   assert not p.is_symlink()and p.stat().st_uid==1000;raw=p.read_bytes();h=digest(raw)
   if h not in objects:
    name=h+'.gzip';blob=gzip.compress(raw,compresslevel=6,mtime=0);(folder/name).write_bytes(blob);objects[h]=dict(file=name,stored_sha256=digest(blob),stored_bytes=len(blob))
   files.append(dict(path=str(p.relative_to(r)),sha256=h,bytes=len(raw),mode=p.stat().st_mode&0o777))
  write(a.archive/'owned-paired-save-r1.json',dict(files=files,objects=objects,dependencies=deps,audit_sha256=sha(receipt)));write(a.out,dict(status='preserved-owned-paired-save',files=len(files),objects=len(objects),stored_bytes=sum(v['stored_bytes']for v in objects.values())));return
 assert not read(a.archive/'owned-paired-save-verification-r1.json')['workplace_required'];art=read(r/'artwork/manifest.json');assert len(art['files'])==1040
 for f in art['files']:assert sha(r/'artwork'/f['path'])==f['sha256']
 write(a.out,dict(status='passed-owned-paired-save-integrity',source_inputs=197,programs=7,core=923,assets=535,artwork=1040,production_changed=False))
if __name__=='__main__':main()
