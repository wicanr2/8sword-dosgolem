#!/usr/bin/env python3
"""Withdraw the card player entry without modifying native or owned saves."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,subprocess
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/original-battle-contract-r1'
BATCH='original-battle-contract-r1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','cli','archive','verify']);p.add_argument('--project',type=Path);p.add_argument('--work',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   o=d['objects'][f['sha256']];blob=(a.archive/BATCH/o['file']).read_bytes();assert hashlib.sha256(blob).hexdigest()==o['stored_sha256'];b=gzip.decompress(blob);assert len(b)==f['bytes']and hashlib.sha256(b).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-original-battle-contract',files=len(d['files']),objects=len(d['objects'])));return
 if a.action=='cli':
  q=a.work;before={n:sha(q/'existing-save'/n)for n in ['gamedata.ay','gamedata.ay.army.json']}
  args=['xvfb-run','-a',str(q/'8sword-owned'),'-root','/not-read','-input','/not-read','-session',str(q/'existing-save'),'-scratch',str(q/'must-not-exist')]
  run=subprocess.run(args,capture_output=True,text=True,timeout=30);(q/'rejected-player.log').write_text(run.stdout+run.stderr);assert run.returncode==1 and '卡片戰鬥入口已停用'in run.stderr and not(q/'must-not-exist').exists(),run.stderr
  assert before=={n:sha(q/'existing-save'/n)for n in before}
  args=['xvfb-run','-a',str(q/'8sword-owned'),'-root','/game','-input',str(q/'inputs'),'-session',str(q/'imported'),'-import-native','/game','-import-only']
  run=subprocess.run(args,capture_output=True,text=True,timeout=30);(q/'import-only.log').write_text(run.stdout+run.stderr);assert run.returncode==0,run.stderr
  assert(q/'imported/gamedata.ay').read_bytes()==Path('/game/GAMEDATA.AY').read_bytes()
  assert read(q/'imported/gamedata.ay.army.json')['schema']=='eightsword-owned-world-save/5'
  write(q/'receipt.json',dict(status='passed-card-entry-withdrawal',card_player_refused_before_read=True,existing_pair_unchanged=before,import_only_passed=True,program_sha256=sha(q/'8sword-owned'),original_battle_bridge_complete=False));return
 r=a.project;q=r/REL;sp=importlib.util.spec_from_file_location('h',r/'tools/prepare-owned-army-ui.py');h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);deps=h.dependencies(r)
 if a.action=='prepare':
  assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir();(q/'inputs').mkdir();(q/'existing-save').mkdir()
  for n in read(r/'preserved/owned-player-source-manifest-r1.json'):
   dst=q/'source'/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,dst)
  for n in ['probe.mod','probe.sum']:
   (q/n).write_bytes(h.stored(r,'owned-player-r1','/owned-player-r1/'+n))
  for n in ['army-catalog.json','combat-catalog.json','PAM.AY']:
   (q/'inputs'/n).write_bytes(h.stored(r,'owned-player-r1','/owned-player-r1/inputs/'+n))
  for n in ['gamedata.ay','gamedata.ay.army.json']:
   (q/'existing-save'/n).write_bytes(h.stored(r,'owned-player-r1','/owned-player-r1/initial-import/'+n))
  shutil.copyfile(r/'tools/check-original-battle-contract.py',q/'check-original-battle-contract.py');write(q/'baseline.json',deps);write(q/'source-manifest.json',{str(p.relative_to(q/'source')):sha(p)for p in sorted((q/'source').rglob('*'))if p.is_file()});return
 assert read(q/'receipt.json')['status']=='passed-card-entry-withdrawal'
 assert read(q/'launcher-receipt.json')['status']=='passed'
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for f in sorted(q.rglob('*')):
  if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
  assert f.stat().st_uid==1000 and not f.is_symlink();b=f.read_bytes();hsh=hashlib.sha256(b).hexdigest();obj=folder/(hsh+'.gz')
  if hsh not in objects:obj.write_bytes(gzip.compress(b,6,mtime=0));objects[hsh]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(f.relative_to(r)),bytes=len(b),sha256=hsh,mode=f.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Native data and complete binary local-only. Original battlefield bridge not complete.'))
if __name__=='__main__':main()
