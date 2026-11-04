#!/usr/bin/env python3
"""原生戰中檢查點的準備、抽驗與永久保存；只在Docker執行。"""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-battle-checkpoint-r1'
REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def module(r,name):
 s=importlib.util.spec_from_file_location(name,r/'tools'/name);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['prepare','freeze','audit','archive','verify'])
 for n in ['project','work','archive','out']:ap.add_argument('--'+n,type=Path)
 a=ap.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  idx=read(a.archive/(BATCH+'.json'))
  for row in idx['files']:
   ob=idx['objects'][row['sha256']];p=a.archive/BATCH/ob['file'];assert sha(p)==ob['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==row['bytes']and hashlib.sha256(raw).hexdigest()==row['sha256']
  write(a.out,dict(status='passed-detached-rust-checkpoint',files=len(idx['files']),objects=len(idx['objects'])));return
 r=a.project;q=a.work or r/REL
 if a.action=='prepare':
  q.mkdir();(q/'native/pack').mkdir(parents=True);(q/'evidence').mkdir();helper=module(r,'prepare-owned-army-ui.py');prev='workplace/probe-20261023/graphics-first/battle-r1/rust-enemy-spells-r1/'
  for row in read(r/'preserved/rust-enemy-spells-r1.json')['files']:
   if row['path'].startswith(prev+'native/pack/'):(q/'native/pack'/Path(row['path']).name).write_bytes(helper.stored(r,'rust-enemy-spells-r1',row['path']))
  write(q/'media.json',{p.name:sha(p)for p in(q/'native/pack').iterdir()});shutil.copy2(r/'preserved/rust-enemy-spells-audit-r1.json',q/'evidence/inherited-audit.json');return
 if a.action=='freeze':
  shutil.copytree(r/'internal/remake-rust',q/'rust-source');(q/'tools').mkdir()
  for n in ['rust-battle-checkpoint.py','rust-checkpoint-gui.py','rust-native-player.sh']:shutil.copy2(r/'tools'/n,q/'tools'/n)
  return
 if a.action=='audit':
  counts={k:len(v)for k,v in module(r,'prepare-owned-army-ui.py').dependencies(r).items()};assert list(counts.values())==[197,7,923,535]
  crate={str(p.relative_to(r/'internal/remake-rust')):sha(p)for p in(r/'internal/remake-rust').rglob('*')if p.is_file()};assert all(sha(q/'rust-source'/n)==h for n,h in crate.items())
  log=(q/'native/tests.log').read_text();assert 'test result: ok. 35 passed'in log and'FAILED'not in log
  cli=(q/'native/cli.log').read_text();assert all(n in cli for n in ['2352','384','13份','201','309'])
  assert all(sha(q/'native/pack'/n)==h for n,h in read(q/'media.json').items())
  gui=read(q/'native/gui/receipt.json');assert gui['status']=='passed-rust-checkpoint-gui'and gui['binary_sha256']==sha(q/'native/8sword-remake')
  from PIL import Image
  for row in gui['runs']:
   assert row['exit']==0
   for cap in row['captures']:
    p=q/'native/gui'/row['name']/f"frame-{cap['number']:03}.ppm";assert p.read_bytes()==p.with_name(f"readback-{cap['number']:03}.ppm").read_bytes()
    assert cap['captured']['frame_hash']==format(module(r,'rust-native-player.py').fnv(Image.open(p).convert('RGBA').tobytes()),'016x')
  write(a.out,dict(status='passed-rust-checkpoint-audit',tests_passed=35,crate=crate,binary_sha256=sha(q/'native/8sword-remake'),formal_baseline_counts=counts,gui=gui,execution=read(q/'execution.json'),limits=['Native development battle checkpoint only; Go/world saves unchanged and not imported.','Inherited oracle vectors remain; no new original executable experiment.','Fixed rosters/seed; cold process uses saved controller without RAM/IP injection.','Media restarts on resume; no animation phase, playback cursor or original F7 parity claim.']));return
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for p in sorted(q.rglob('*')):
  if not p.is_file()or'rust-target'in p.relative_to(q).parts:continue
  assert p.stat().st_uid==1000 and not p.is_symlink();raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();obj=folder/(h+'.gz')
  if h not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(Path(REL)/p.relative_to(q)),bytes=len(raw),sha256=h,mode=p.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,rights='Full media, native checkpoints, captures and binary local only; no release'))
if __name__=='__main__':main()
