#!/usr/bin/env python3
"""Rust敵術的來源恢復、向量與永久保存。只在Docker使用。"""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-enemy-spells-r1'
REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def module(r,name):
 s=importlib.util.spec_from_file_location(name,r/'tools'/name);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def vectors(r,q):
 lines=(q/'enemy-models.tsv').read_text().splitlines();nums=lambda v:','.join(map(str,v))or'-'
 rows=lambda a:','.join((s['unit']or'-')+'='+str(s['count'])for s in a)
 for source in read(q/'evidence/sources.json'):
  p=q/'evidence'/source['file'];assert sha(p)==source['sha256'];v=read(p);rec=v['record'];effects=rec['Effects']or[];clone=rec['Clone'];sel=rec['Selector']
  target=clone['Target']if clone else (effects[0]['Target']if effects and sel not in [1,7]else 1 if sel==3 else'-')
  fields=['CASE',v['name'],rec['Kind'],sel,v['gate_field'],target,rec['Gate']if rec['GateSeen']else'-',rows(v['rows'][0]),rows(v['rows'][1]),nums(rec['AfterCounters']),nums(struct.unpack('<12H',bytes.fromhex(v['hp_hex'])))]
  lines.append('\t'.join(map(str,fields)))
  for e in effects:lines.append('\t'.join(map(str,['EFFECT',0,e['Target'],e['Raw'],e['Before'],e['After'],e['Amount'],nums(e['Display']or[])])))
  if clone:lines.append('\t'.join(map(str,['EFFECT',1,clone['Target'],clone['Raw'],clone['Before'],clone['After'],0,nums(clone['Display']or[])])))
  lines.append('END')
 raw=('\n'.join(lines)+'\n').encode()
 for p in [q/'enemy-reference.tsv',r/'internal/remake-rust/enemy-reference.tsv']:
  if p.exists():assert p.read_bytes()==raw,p
  else:p.write_bytes(raw)
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['prepare','vectors','archive','verify','audit'])
 for n in ['project','work','archive','out']:ap.add_argument('--'+n,type=Path)
 a=ap.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  idx=read(a.archive/(BATCH+'.json'))
  for row in idx['files']:
   ob=idx['objects'][row['sha256']];p=a.archive/BATCH/ob['file'];assert sha(p)==ob['stored_sha256'];b=gzip.decompress(p.read_bytes());assert len(b)==row['bytes']and hashlib.sha256(b).hexdigest()==row['sha256']
  write(a.out,dict(status='passed-detached-rust-enemy',files=len(idx['files']),objects=len(idx['objects'])));return
 r=a.project;q=a.work or r/REL
 if a.action=='prepare':
  helper=module(r,'prepare-owned-army-ui.py');q.mkdir();(q/'native').mkdir();(q/'evidence').mkdir()
  for name in ['probe.mod','probe.sum']:(q/name).write_bytes(helper.stored(r,'rust-player-spells-r1',name))
  cases=[]
  for row in read(r/'preserved/original-battle-enemy-r1.json')['files']:
   parts=Path(row['path']).parts
   if 'enemy-r1'not in parts or not row['path'].endswith('-mode-1/receipt.json'):continue
   raw=helper.stored(r,'original-battle-enemy-r1',row['path']);name=parts[-2]+'.json';(q/'evidence'/name).write_bytes(raw);cases.append(dict(file=name,sha256=hashlib.sha256(raw).hexdigest()))
   control=helper.stored(r,'original-battle-enemy-r1',row['path'].replace('-mode-1/','-mode-0/'));v=json.loads(raw);c=json.loads(control)
   assert all(v[k]==c[k]for k in ['units_hex','hp_hex','counters_hex','selector','seed','frame_sha256'])
   (q/'evidence'/name.replace('-mode-1','-mode-0')).write_bytes(control)
  assert len(cases)==13;write(q/'evidence/sources.json',sorted(cases,key=lambda v:v['file']))
  for name in ['ida-spells-r4.json','ida-rounds.json','provenance.json']:(q/'evidence'/name).write_bytes(helper.stored(r,'original-battle-enemy-r1','evidence/'+name))
  previous='workplace/probe-20261023/graphics-first/battle-r1/rust-player-spells-r1/'
  for row in read(r/'preserved/rust-player-spells-r1.json')['files']:
   if row['path'].startswith(previous+'native/pack/'):
    dst=q/'native/pack'/Path(row['path']).name;dst.parent.mkdir(exist_ok=True);dst.write_bytes(helper.stored(r,'rust-player-spells-r1',row['path']))
  write(q/'media.json',{p.name:sha(p)for p in(q/'native/pack').iterdir()});return
 if a.action=='vectors':vectors(r,q);return
 if a.action=='audit':
  counts={k:len(v)for k,v in module(r,'prepare-owned-army-ui.py').dependencies(r).items()};assert list(counts.values())==[197,7,923,535]
  vectors(r,q)
  for n,h in read(q/'source-manifest.json').items():assert sha(q/'source'/n)==h
  crate={str(p.relative_to(r/'internal/remake-rust')):sha(p)for p in(r/'internal/remake-rust').rglob('*')if p.is_file()}
  assert all(sha(q/'rust-source'/n)==h for n,h in crate.items())
  assert 'PASS'in(q/'go-reference.log').read_text()and'FAIL'not in(q/'go-reference.log').read_text()
  test=(q/'native/tests.log').read_text();assert 'FAILED'not in test and'test result: ok. 29 passed'in test
  cli=(q/'native/cli.log').read_text();assert '384組模型、13份'in cli
  assert all(sha(q/'native/pack'/n)==h for n,h in read(q/'media.json').items())
  gui=read(q/'native/gui/receipt.json');assert gui['status']=='passed-rust-enemy-gui'and gui['binary_sha256']==sha(q/'native/8sword-remake')
  from PIL import Image
  for row in gui['captures']:
   n=row['number'];frame=q/'native/gui'/f'frame-{n:03}.ppm';assert frame.read_bytes()==frame.with_name(f'readback-{n:03}.ppm').read_bytes()
   assert row['captured']['frame_hash']==format(module(r,'rust-native-player.py').fnv(Image.open(frame).convert('RGBA').tobytes()),'016x')
  write(a.out,dict(status='passed-rust-enemy-audit',models=384,inherited_original_cases=13,crate=crate,binary_sha256=sha(q/'native/8sword-remake'),gui=gui,formal_baseline_counts=counts,execution=read(q/'execution.json'),limits=['Explicit battle roster, first side and seed. No world/save or full RNG stream parity.','Original pairs inherited; current Go helper models independently regenerated.','Selector7 only controlled entry; never added to autonomous distribution.','Shared approved impact effects, no original animation-phase parity.']));return
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for p in sorted(q.rglob('*')):
  if not p.is_file()or any(n in p.relative_to(q).parts for n in ['build-cache','rust-target']):continue
  assert p.stat().st_uid==1000 and not p.is_symlink();raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();obj=folder/(h+'.gz')
  if h not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(Path(REL)/p.relative_to(q)),bytes=len(raw),sha256=h,mode=p.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,rights='Original data, full captures and binaries local only; no release'))
if __name__=='__main__':main()
