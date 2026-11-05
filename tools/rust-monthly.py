#!/usr/bin/env python3
"""Rust玩家月報：固定Go向量、媒體、核對與本機永久保存。"""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-monthly-r1';REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def module(r,n):
 s=importlib.util.spec_from_file_location(n,r/'tools'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','audit','archive','verify','images'])
 for n in ['project','work','out','archive']:p.add_argument('--'+n,type=Path)
 a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  j=read(a.archive/(BATCH+'.json'))
  for f in j['files']:
   o=j['objects'][f['sha256']];b=(a.archive/BATCH/o['file']).read_bytes();assert hashlib.sha256(b).hexdigest()==o['stored_sha256'];raw=gzip.decompress(b);assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  v=dict(status='passed-detached-rust-monthly',files=len(j['files']),objects=len(j['objects']));write(a.out,v);print(json.dumps(v));return
 r=a.project;q=a.work or r/REL;h=module(r,'prepare-owned-army-ui.py')
 if a.action=='prepare':
  q.mkdir();(q/'native/pack').mkdir(parents=True);(q/'evidence').mkdir()
  for f in read(r/'preserved/rust-controls-r1.json')['files']:
   if '/native/pack/'in f['path']:(q/'native/pack'/Path(f['path']).name).write_bytes(h.stored(r,'rust-controls-r1',f['path']))
  for name,key in [('legacy-v2.chk','native/gui/purchase-store/journey.chk'),('legacy-v1.chk','evidence/legacy-v1.chk')]:
   (q/'evidence'/name).write_bytes(h.stored(r,'rust-controls-r1',key))
  pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0';ds=struct.unpack_from('<H',pam,8)[0]*16+0x1d780;caps=[struct.unpack_from('<H',pam,ds+0x3a56+g*240+row*10)[0]for g in range(5)for row in range(24)];(q/'monthly-caps.tsv').write_text('\n'.join(map(str,caps))+'\n')
  proof=json.loads(h.stored(r,'monthly-wide-r1','candidate-r1/receipt.json'));(q/'evidence/go-monthly.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n');budget=['# name gold income six_unit=count due charged after disbanded'];stock=['# case index kind before cap after']
  for case in proof['cases']:
   before=case['before']['world'];b=case['budget'];army=','.join(s['unit']+'='+str(s['count'])for s in before['army']['slots']if s['count']);budget.append('\t'.join(map(str,[case['name'],b['Before'],b['Income'],army,b['Due'],b['Charged'],b['After'],int(b['Disbanded'])])))
   ix=json.loads(h.stored(r,'monthly-wide-r1','decoded-r1/'+case['name']+'/index.json'));v=ix['before.state'];ram=gzip.decompress(h.stored(r,'monthly-wide-r1','decoded-r1/'+case['name']+'/'+v['memory_file']));assert hashlib.sha256(ram).hexdigest()==v['memory_sha256'];after=h.stored(r,'monthly-wide-r1','candidate-r1/'+case['name']+'/after-native.ay');(q/'evidence'/('native-'+case['name']+'.ay')).write_bytes(after)
   for i in range(120):
    g,row=divmod(i,24);at=0x1e880+0x3efe+g*240+row*10;kind,n=struct.unpack_from('<HH',ram,at+6);off=36+row*50+4*10+g*2;end=(struct.unpack_from('<H',after,off)[0]-off-3)&65535;stock.append('\t'.join(map(str,[case['name'],i,kind,n,caps[i],end])))
  (q/'monthly-reference.tsv').write_text('\n'.join(budget)+'\n');(q/'monthly-stock.tsv').write_text('\n'.join(stock)+'\n');ida=h.stored(r,'monthly-r1','ida/ida-monthly-r1.json');(q/'evidence/ida-monthly.json').write_bytes(ida);write(q/'evidence/source.json',dict(status='passed-monthly-source',cases=len(proof['cases']),stock_vectors=len(stock)-1,pam_sha256=hashlib.sha256(pam).hexdigest(),ida_sha256=sha(q/'evidence/ida-monthly.json'),caps=caps,original_oracle='Inherited Go/IDA receipts; no new full original runtime comparison'));return
 if a.action=='freeze':
  shutil.copytree(r/'internal/remake-rust',q/'rust-source');(q/'tools').mkdir()
  for n in ['rust-monthly.py','rust-monthly-gui.py','rust-native-player.sh']:shutil.copy2(r/'tools'/n,q/'tools'/n)
  write(q/'media.json',{p.name:sha(p)for p in(q/'native/pack').iterdir()if p.is_file()});return
 if a.action=='audit':
  baseline={k:len(v)for k,v in h.dependencies(r).items()};assert list(baseline.values())==[197,7,923,535];crate={str(p.relative_to(r/'internal/remake-rust')):sha(p)for p in(r/'internal/remake-rust').rglob('*')if p.is_file()};assert all(sha(q/'rust-source'/p)==v for p,v in crate.items());assert all(sha(q/'native/pack'/p)==v for p,v in read(q/'media.json').items());assert all((q/n).read_bytes()==(r/'internal/remake-rust'/n).read_bytes()for n in ['monthly-caps.tsv','monthly-reference.tsv','monthly-stock.tsv']);log=(q/'native/tests.log').read_text();assert 'FAILED'not in log and '58 passed; 0 failed'in log;source=read(q/'evidence/source.json');assert source['cases']==6 and source['stock_vectors']==720;gui=read(q/'native/gui/receipt.json');assert gui['status']=='passed-rust-monthly-gui'and gui['binary_sha256']==sha(q/'native/8sword-remake')
  from PIL import Image
  for row in gui['runs']:
   assert row['exit']==0
   for cap in row['captures']:
    p=q/'native/gui'/row['name']/f"frame-{cap['number']:03}.ppm";assert p.read_bytes()==p.with_name(f"readback-{cap['number']:03}.ppm").read_bytes();assert cap['captured']['frame_hash']==format(module(r,'rust-native-player.py').fnv(Image.open(p).convert('RGBA').tobytes()),'016x')
  write(a.out,dict(status='passed-rust-monthly-audit',crate=crate,binary_sha256=sha(q/'native/8sword-remake'),baseline=baseline,gui=gui,source=read(q/'evidence/source.json'),execution=read(q/'execution.json'),limits=['Player finances and camp refill only; NPC growth and original calendar phases not ported.','Development v3 checkpoint; no Go save import or complete world schema.']));return
 if a.action=='images':
  from PIL import Image
  gui=read(q/'native/gui/receipt.json');picks=[('natural','monthly-lishu'),('cold','monthly-cold'),('natural','after-report-army'),('legacy','v2-camp-continued')];canvas=Image.new('RGB',(1920,1320));sources=[]
  for i,(name,label)in enumerate(picks):
   row=next(v for v in gui['runs']if v['name']==name);cap=next(v for v in row['captures']if v['label']==label);p=q/'native/gui'/name/f"frame-{cap['number']:03}.ppm";canvas.paste(Image.open(p).resize((960,660),Image.Resampling.LANCZOS),((i%2)*960,(i//2)*660));sources.append(dict(run=name,label=label,sha256=sha(p),captured=cap['captured']))
  assert not a.out.exists();canvas.save(a.out);write(a.out.with_suffix('.json'),dict(platform='Linux Rust SDL2',seed=1,binary_sha256=gui['binary_sha256'],image_sha256=sha(a.out),scope='Natural start to player monthly report; no RAM/IP injection. Original comparison is inherited Go rules only.',sources=sources));return
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for p in sorted(q.rglob('*')):
  if not p.is_file()or'rust-target'in p.relative_to(q).parts:continue
  assert not p.is_symlink()and p.stat().st_uid==1000;raw=p.read_bytes();v=hashlib.sha256(raw).hexdigest();obj=folder/(v+'.gz')
  if v not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[v]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(Path(REL)/p.relative_to(q)),sha256=v,bytes=len(raw),mode=p.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,rights='Full original-derived assets and binary local only; no Release'))
if __name__=='__main__':main()
