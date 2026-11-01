#!/usr/bin/env python3
"""Sample purchased reinforcements across the existing v5 battle save path."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/reinforcement-battle-r1'
BATCH='reinforcement-battle-r1';PARENT='reinforcement-camps-r1'
NEW=['prepare-reinforcement-battle.py','check-reinforcement-battle.py','audit-reinforcement-battle.py']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def helper(r):
 s=importlib.util.spec_from_file_location('h',r/'tools/prepare-owned-army-ui.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','archive','verify']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   o=d['objects'][f['sha256']];p=a.archive/BATCH/o['file'];assert sha(p)==o['stored_sha256'];b=gzip.decompress(p.read_bytes());assert len(b)==f['bytes']and hashlib.sha256(b).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-reinforcement-battle',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL;m=helper(r);deps=m.dependencies(r)
 if a.action=='prepare':
  assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir();d=read(r/'preserved'/f'{PARENT}.json')
  for f in d['files']:
   rel=f['path'].split('/'+PARENT+'/',1)[1]
   if not(rel.startswith(('go-src/','inputs/','ui-assets/','session-gui-r2/'))or rel in ['probe.mod','probe.sum','execution-r1.json','reinforcement-ui','xcheck']):continue
   if rel.startswith('session-gui-r2/'):rel='session/'+rel.split('/',1)[1]
   t=q/rel;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(m.stored(r,PARENT,'/'+PARENT+'/'+f['path'].split('/'+PARENT+'/',1)[1]));t.chmod(f['mode'])
  shutil.copytree(q/'session',q/'initial-session')
  write(q/'baseline.json',deps);write(q/'parent.json',dict(batch=PARENT,archive_sha256=sha(r/'preserved'/f'{PARENT}.json'),binary_sha256=sha(q/'reinforcement-ui'),initial_world_sha256=sha(q/'session/gamedata.ay.army.json'),initial_native_sha256=sha(q/'session/gamedata.ay')))
 else:assert deps==read(q/'baseline.json')
 if a.action in ['prepare','freeze']:
  for n in NEW:
   if(r/'tools'/n).is_file():shutil.copyfile(r/'tools'/n,q/'go-src/tools'/n)
  return
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for f in sorted(q.rglob('*')):
  if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
  assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();h=hashlib.sha256(raw).hexdigest();obj=folder/(h+'.gz')
  if h not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(f.relative_to(r)),bytes=len(raw),sha256=h,mode=f.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Private original inputs, VM, full artwork and screenshots local-only; isolated candidate sample.'))
if __name__=='__main__':main()
