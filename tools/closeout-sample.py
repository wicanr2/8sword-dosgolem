#!/usr/bin/env python3
"""核對既有HD階段的固定抽樣；不提升尚未接入的新兵種。"""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,subprocess
from pathlib import Path
REL='workplace/player/phase-closeout-r1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def dependency(r):
 s=importlib.util.spec_from_file_location('army',r/'tools/prepare-owned-army-ui.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m.dependencies(r)
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()
def status_errors(s):
 assert not s['owned_render_fault']and not s['unimplemented']
 for k,v in s.items():
  if k.endswith('_error'):assert not v,(k,v)
 if s.get('music'):assert not s['music'].get('load_error')
def verify_batch(r,name):
 d=read(r/'preserved'/(name+'.json'))
 for h,o in d['objects'].items():
  p=r/'preserved'/name/o['file'];assert sha(p)==o['stored_sha256'];assert hashlib.sha256(gzip.decompress(p.read_bytes())).hexdigest()==h
 return dict(files=len(d['files']),objects=len(d['objects']))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','stage-gui','guard','audit','archive','verify']);p.add_argument('--project',type=Path);p.add_argument('--out',type=Path);p.add_argument('--archive',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/'phase-closeout-r1.json')
  for f in d['files']:
   obj=a.archive/'phase-closeout-r1'/d['objects'][f['sha256']]['file'];raw=gzip.decompress(obj.read_bytes());assert sha(obj)==d['objects'][f['sha256']]['stored_sha256']and len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-closeout',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL
 if a.action=='guard':
  folder=q/'guard';folder.mkdir();scratch=folder/'scratch';scratch.mkdir()
  for n in ['gamedata.ay','gamedata.ay.army.json']:shutil.copyfile(r/'workplace/probe-20261023/graphics-first/battle-r1/owned-world-army-dismiss-r1/session-preview-r1'/n,scratch/n)
  before={f.name:sha(f)for f in scratch.iterdir()}
  args=[str(r/'workplace/player/8sword-replay'),'-root',str(r/'workplace/intake-20261023/sources/game/8sword'),'-assets',str(r/'workplace/player/assets-painted-r69'),'-out',str(folder),'-until','1']
  proc=subprocess.run(args,capture_output=True,text=True,timeout=30);(q/'guard.log').write_text(proc.stdout+proc.stderr)
  assert proc.returncode!=0 and'自有軍隊存檔的玩家交接尚未完成'in proc.stderr and'啟動原版程式前停止'in proc.stderr
  assert before=={f.name:sha(f)for f in scratch.iterdir()}and not(folder/'final.state').exists()
  write(q/'guard.json',dict(status='passed-early-guard',exit_code=proc.returncode,save_hashes=before,new_troop_player_handoff_complete=False));return
 deps=dependency(r);identity=digest(deps)
 if a.action=='stage-gui':
  folder=r/'workplace/player/phase-closeout-gui-bin-r1';folder.mkdir();old=r/'workplace/player/source-candidate-owned-combat-r1'
  for n,h in deps['programs'].items():assert sha(old/n)==h;shutil.copy2(old/n,folder/n)
  shutil.copy2(old/'build-go-version.txt',folder/'build-go-version.txt')
  for name,values in [('build-inputs.sha256',deps['source_inputs']),('build-outputs.sha256',deps['programs'])]:
   (folder/name).write_text(''.join(h+'  '+n+'\n'for n,h in sorted(values.items())))
  failed=r/'workplace/player/gui/phase-closeout-r1'
  if failed.exists():failed.rename(q/'gui-bootstrap-failed-r1')
  write(q/'gui-bootstrap.json',dict(note='Original candidate lacks legacy GUI harness metadata filenames. Staged identical SHA-verified seven binaries with reconstructed metadata; no build or product change.',programs=deps['programs']));return
 if a.action=='prepare':
  assert not q.exists();q.mkdir();assert q.stat().st_uid==1000
  art=read(r/'artwork/manifest.json');assert len(art['files'])==1040
  for f in art['files']:assert sha(r/'artwork'/f['path'])==f['sha256']
  plan=dict(schema=1,baseline='503ed45',identity_sha256=identity,counts={k:len(v)for k,v in deps.items()},artwork_files=1040,original_manifest_sha256=sha(r/'preserved/catalog.json.gz'),samples=[
   dict(id='identity',method='All current source/binary/core/asset and permanent artwork hashes'),
   dict(id='replay-native',method='Existing CLI fixed input, 250M instructions, native mode'),
   dict(id='replay-hd',method='Same CLI fixed input, 250M instructions, HD Go source renderer, zero native pixel writes'),
   dict(id='normal-gui',method='Current formal build, actual XTEST new game/recruitment/natural battle retreat/F7/exit/cold reload; no recording'),
   dict(id='reused-mechanisms',method='Read accepted AI/tactics/VFX/music receipts and verify permanent F3 objects; no per-unit rerun'),
   dict(id='guard',method='Actual formal executable refuses expanded paired save before DOS; input files unchanged')],
   limits=['Purposive mechanism samples, no statistical full-game coverage claim.','Existing HD/features stage only. Expanded army world/month/event/battle handoff is not implemented in the formal player path.','No Rust migration, public release, hardware timing or new listening claim.'],paths=dict(native='workplace/player/replays/phase-closeout-native-r1',hd='workplace/player/replays/phase-closeout-hd-r1',gui='workplace/player/gui/phase-closeout-r1'))
  write(a.out,plan);return
 plan=read(r/'preserved/phase-closeout-plan-r1.json');assert identity==plan['identity_sha256']
 if a.action=='audit':
  from PIL import Image
  replays={}
  for mode in ['native','hd']:
   folder=r/plan['paths'][mode];v=read(folder/'receipt.json');assert v['steps']==250000000 and v['hd']==(mode=='hd')and v['normal_input_replay']and not v['snapshot_loaded']
   assert (folder/'final.state').stat().st_size>0;assert Image.open(folder/'final.png').size==(1920,1200)
   if mode=='hd':assert v['native_pixel_writes']==0 and v['source_renderer']and not v['owned_render_fault']
   if mode=='hd':status_errors(v)
   replays[mode]=dict(receipt_sha256=sha(folder/'receipt.json'),state_sha256=sha(folder/'final.state'),native_pixel_writes=v['native_pixel_writes'])
  replay_same_state=replays['native']['state_sha256']==replays['hd']['state_sha256']
  failed_gui=r/plan['paths']['gui'];failure_log=(failed_gui/'save/gui-check.log').read_text();assert 'panic:'in failure_log
  failed_status=read(failed_gui/'save/gui-state.json');status_errors(failed_status)
  # This additional basic path does not replace the failed predeclared gate.
  gui=r/'workplace/player/gui/phase-closeout-core-r1';summaries={}
  for phase in ['save','reload']:
   v=read(gui/phase/'gui-input-receipt.json');s=v['final_status'];assert v['status']=='passed-input-path'and v['flow']==phase and s['hd']and s['source_renderer']and not s['owned_render_fault']
   status_errors(s)
   for key in ['asset_error','graphics_error','music_error','completion_error']:assert not s.get(key),(phase,key,s.get(key))
   summaries[phase]=dict(receipt_sha256=sha(gui/phase/'gui-input-receipt.json'),steps=s['steps'])
  saved=read(gui/'save/saved.json');assert saved['bytes']==2987 and saved['sha256']==sha(gui/'scratch/gamedata.ay')
  assert read(gui/'reload/gui-input-receipt.json')['final_status']['font_id']=='caoshu'
  reuse={}
  for n in ['ai-engine-audit-r1.json','tactics-audit-r1.json','vfx-engine-audit-r1.json','hd-music-audit-r1.json','owned-world-army-dismiss-audit-r1.json']:
   v=read(r/'preserved'/n);assert v['status'].lower().startswith('pass');reuse[n]=dict(status=v['status'],sha256=sha(r/'preserved'/n))
  assert read(q/'guard.json')['status']=='passed-early-guard'
  preserved=verify_batch(r,'owned-world-army-dismiss-r1')
  gap=failure_log[failure_log.index('panic:'):].split('：',1)[0]
  write(a.out,dict(schema=1,status='qualified-hd-closeout-with-gui-gap',all_planned_gates_passed=False,project_complete=False,plan_sha256=sha(r/'preserved/phase-closeout-plan-r1.json'),identity_sha256=identity,replays=replays,replay_complete_state_equal=replay_same_state,additional_basic_gui=summaries,planned_gui_gate=dict(status='not-passed',reason=gap,log_sha256=sha(failed_gui/'save/gui-check.log'),render_fault=None,classification='Unresolved normal-input path; no claim that this proves a product defect or a successful encounter.'),save_sha256=saved['sha256'],reused=reuse,f3_preserved=preserved,new_troop_player_handoff_complete=False,limits=plan['limits']));return
 assert a.action=='archive';assert read(r/'preserved/phase-closeout-audit-r1.json')['status']=='qualified-hd-closeout-with-gui-gap';dest=a.archive/'phase-closeout-r1';dest.mkdir(exist_ok=True);files=[];objects={}
 source=q/'sources';source.mkdir()
 for n in ['closeout-sample.py','gui-check.sh','player.sh']:shutil.copyfile(r/'tools'/n,source/n)
 sources=[q,r/plan['paths']['native'],r/plan['paths']['hd'],r/plan['paths']['gui'],r/'workplace/player/gui/phase-closeout-core-r1']
 for root in sources:
  for f in sorted(root.rglob('*')):
   if not f.is_file():continue
   assert f.stat().st_uid==1000;raw=f.read_bytes();h=hashlib.sha256(raw).hexdigest();obj=dest/(h+'.gz')
   if not obj.exists():obj.write_bytes(gzip.compress(raw,compresslevel=6,mtime=0))
   else:assert gzip.decompress(obj.read_bytes())==raw
   objects[h]=dict(file=obj.name,stored_sha256=sha(obj));files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(raw),mode=f.stat().st_mode&0o777))
 write(a.out,dict(schema=1,files=files,objects=objects,rights='Local only; original save/state/graphics are not distributed.'))
if __name__=='__main__':main()
