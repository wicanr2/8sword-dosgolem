#!/usr/bin/env python3
"""Prepare a read-only diagnosis of the unresolved recruitment GUI path."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil
from pathlib import Path
REL='workplace/player/recruit-gui-diagnosis-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def chain_driver(source):
 # Sample one ordinary purchase; the full font/editing mechanism was already
 # checked separately. Return from the shop to the original encounter walk.
 a=source.index('\tfor i := 0; i < 3; i++ {',source.index('func (d *driver) recruitmentBuilding'))
 b=source.index('\tif hire {',a);source=source[:a]+source[b:]
 a=source.index('\t\t// Exercise ordinary numeric editing.');b=source.index('\t\td.press(10) // 1',a);source=source[:a]+source[b:]
 a=source.index('\t\td.press(19) // 0',a);b=source.index('\t\td.press(36)',a);source=source[:a]+source[b:]
 needle='\tif *battleCheck && *flow == "save" {\n\t\td.battle()';assert source.count(needle)==1
 return source.replace(needle,'\tif *battleCheck && *flow == "save" {\n\t\tif *hireCheck {\n\t\t\td.army("recruited")\n\t\t\tfor _, key := range []byte{116,116,114} {\n\t\t\t\td.press(key)\n\t\t\t\td.press(67)\n\t\t\t\td.scene("character")\n\t\t\t\td.press(9)\n\t\t\t\td.scene("map")\n\t\t\t}\n\t\t}\n\t\td.battle()')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','chain-driver','audit','archive','verify']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=json.loads((a.archive/'recruit-gui-diagnosis-r1.json').read_text())
  for f in d['files']:
   o=d['objects'][f['sha256']];obj=a.archive/'recruit-gui-diagnosis-r1'/o['file'];assert sha(obj)==o['stored_sha256'];raw=gzip.decompress(obj.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-recruit-diagnosis',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL
 if a.action=='chain-driver':
  with a.out.open('x')as f:f.write(chain_driver((r/'tools/gui-check.go').read_text()))
  return
 if a.action=='audit':
  from PIL import Image,ImageChops
  read=lambda p:json.loads(p.read_text())
  spec=importlib.util.spec_from_file_location('prior',r/'tools/prepare-owned-army-ui.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);deps=m.dependencies(r)
  baseline=read(q/'baseline.json');assert len(deps['source_inputs'])==197 and deps['programs']==baseline['programs']
  assert sha(q/'bin/8sword')==baseline['game_sha256']
  assert(q/'driver-chain.go').read_text()==chain_driver((r/'tools/gui-check.go').read_text())
  parent=read(r/'preserved/phase-closeout-audit-r1.json');assert parent['replay_complete_state_equal']and not parent['all_planned_gates_passed']
  before,after,f2=[read(q/n)for n in ['base-state.json','after-state.json','f2-state.json']]
  assert before['native_resources_04f2'][3]==500 and after['native_resources_04f2'][3]==499
  assert before['native_army_054a'][0]==dict(kind=1,count=30) and after['native_army_054a'][0]==dict(kind=1,count=31)
  assert f2['native_army_054a']==after['native_army_054a'] and f2['ds_56bc']==1
  assert after['state_sha256']==sha(q/'save/gui-final.state')and f2['state_sha256']==sha(q/'f2/save/gui-final.state')
  controls={}
  for name in ['short','five-frame']:
   d=read(q/'function-key-r2'/(name+'.json'));assert d['ds_56bc']==1
   assert {v['ip']for v in d['events']}=={0x3e92,0x75c6};controls[name]=dict(events=d['events'],hold_cycles=d['hold_cycles'])
  log=(q/'wait/save/player.log').read_text();commits=[v for v in log.splitlines()if'kind=panel-commit'in v and'kind:army'in v]
  assert len(commits)==1 and'primitive_pending:0'in commits[0]
  early=Image.open(q/'f2/save/diagnostic-f2.png').convert('RGB');late=Image.open(q/'wait/save/diagnostic-f2.png').convert('RGB')
  assert early.size==late.size and ImageChops.difference(early,late).getbbox()
  phases={}
  for phase in ['save','reload']:
   folder=q/'chain'/phase;receipt=read(folder/'gui-input-receipt.json');s=receipt['final_status']
   assert receipt['status']=='passed-input-path'and receipt['flow']==phase and s['hd']and s['source_renderer']
   assert not s['owned_render_fault']and not s['unimplemented']
   for k,v in s.items():
    if k.endswith('_error'):assert not v,(phase,k,v)
   phases[phase]=dict(receipt_sha256=sha(folder/'gui-input-receipt.json'),state_sha256=sha(folder/'gui-final.state'),steps=s['steps'])
  saved=read(q/'chain/save/saved.json');assert saved['bytes']==2987 and saved['sha256']==sha(q/'chain/scratch/gamedata.ay')
  for name in ['recruited-army-first','recruited-army-again','battle-01-first-encounter','battle-03-ready','battle-06-result','battle-07-result-closed','13-saved-map']:
   assert Image.open(q/'chain/save'/(name+'.png')).size==(1600,687)
  cold=read(q/'chain/reload/gui-input-receipt.json')['final_status'];reads=[v for v in cold['file_ops']if v['Op']=='read'and v['Name'].lower()=='gamedata.ay']
  assert len(reads)==1 and reads[0]['Len']==2987 and not reads[0]['Failed']
  save_ram,cold_ram=[read(q/n)for n in ['chain-save-state.json','chain-reload-state.json']]
  assert save_ram['native_resources_04f2']==cold_ram['native_resources_04f2']and save_ram['native_army_054a']==cold_ram['native_army_054a']
  assert save_ram['state_sha256']==phases['save']['state_sha256']and cold_ram['state_sha256']==phases['reload']['state_sha256']
  write(a.out,dict(schema=1,status='passed-recruitment-gui-diagnosis-and-normal-chain',all_planned_gates_passed=True,project_complete=False,production_code_changed=False,parent_audit_sha256=sha(r/'preserved/phase-closeout-audit-r1.json'),baseline=baseline,actual_recruitment=dict(before=before,after=after),actual_f2=f2,original_function_key_controls=controls,completed_panel=commits[0],early_capture_sha256=sha(q/'f2/save/diagnostic-f2.png'),completed_capture_sha256=sha(q/'wait/save/diagnostic-f2.png'),normal_gui=phases,save_sha256=saved['sha256'],cold_native_resources=cold_ram['native_resources_04f2'],cold_native_army=cold_ram['native_army_054a'],cold_read_step=reads[0]['Step'],driver_sha256=sha(q/'driver-chain.go'),resolved_gate='Normal original recruitment, F2, return walk, natural encounter, retreat, F7 save, DOS exit and fresh-process reload.',limits=['Purposeful representative sample, not whole-game parity.','Expanded troop world handoff remains DRAFT; formal sidecar guard unchanged.','The traced renderer is a disposable read-only diagnostic; the final chain uses the unchanged formal game binary.','No RAM/register/RNG edits or snapshot-entry replacement of the GUI path.']));return
 if a.action=='prepare':
  spec=importlib.util.spec_from_file_location('prior',r/'tools/prepare-owned-army-ui.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);deps=m.dependencies(r)
  assert not q.exists();q.mkdir();(q/'bin').mkdir()
  for n in ['8sword','gui-check']:shutil.copy2(r/'workplace/player'/n,q/'bin'/n)
  shutil.copyfile(r/'workplace/player/source-candidate-owned-combat-r1/build-go-version.txt',q/'bin/build-go-version.txt')
  for name,values in [('build-inputs.sha256',deps['source_inputs']),('build-outputs.sha256',deps['programs'])]:(q/'bin'/name).write_text(''.join(h+'  '+n+'\n'for n,h in sorted(values.items())))
  for ext in ['mod','sum']:shutil.copyfile(r/'workplace/player/source-candidate-owned-combat-r1'/('build.'+ext),q/('go.'+ext))
  src=(r/'tools/gui-check.go').read_text();needle='\t\td.recruitmentBuilding(*hireCheck)\n';assert src.count(needle)==1
  src=src.replace(needle,needle+'\t\td.shot("diagnostic-after-recruitment")\n\t\td.receipt("diagnostic-after-recruitment")\n\t\td.quit()\n\t\treturn\n')
  (q/'driver.go').write_text(src);shutil.copyfile(r/'tools/read-gui-army-state.go',q/'reader.go');write(q/'baseline.json',dict(programs=deps['programs'],source_count=len(deps['source_inputs']),driver_source_sha256=sha(q/'driver.go'),game_sha256=sha(q/'bin/8sword')));return
 assert a.action=='archive';dest=a.archive/'recruit-gui-diagnosis-r1';dest.mkdir(exist_ok=True);files=[];objects={}
 for f in sorted(q.rglob('*')):
  if not f.is_file():continue
  raw=f.read_bytes();h=hashlib.sha256(raw).hexdigest();obj=dest/(h+'.gz')
  if not obj.exists():obj.write_bytes(gzip.compress(raw,compresslevel=6,mtime=0))
  else:assert gzip.decompress(obj.read_bytes())==raw
  objects[h]=dict(file=obj.name,stored_sha256=sha(obj));files.append(dict(path=str(f.relative_to(r)),bytes=len(raw),sha256=h,mode=f.stat().st_mode&0o777))
 write(a.out,dict(schema=1,files=files,objects=objects,rights='Local original machine state, screenshots and diagnostic tools; objects excluded from Git.'))
if __name__=='__main__':main()
