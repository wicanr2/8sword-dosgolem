#!/usr/bin/env python3
"""Rust普通遭遇的資料準備、核對及本機保存。Docker限定。"""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-journey-r1';REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def module(r,n):
 s=importlib.util.spec_from_file_location(n,r/'tools'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['prepare','media','vectors','freeze','audit','archive','verify']);
 for n in['project','work','archive','out','assets']:ap.add_argument('--'+n,type=Path)
 a=ap.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   o=d['objects'][f['sha256']];p=a.archive/BATCH/o['file'];assert sha(p)==o['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-rust-journey',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=a.work or r/REL;h=module(r,'prepare-owned-army-ui.py')
 if a.action=='vectors':
  lines=['# Existing Go world settlement receipts; only resources and settlement RNG are compared'];names=['expanded-win','native-retreat-go','expanded-win-promotion']
  for name in names:
   raw=h.stored(r,'original-battle-world-r1',f'world-r1/{name}/receipt.json');d=json.loads(raw);(q/f'evidence/inherited-{name}.json').write_bytes(raw);v=d['before_resources'];before=[v[k]for k in['rank','merit','monthly_pay','gold','leadership','spell_power']];rng=d['random'];enemy=','.join(f"{s['unit']}={s['count']}"for s in d['enemy_initial']);lines.append('\t'.join([d['result'],','.join(map(str,before)),enemy,str(rng['Before']if rng else 0),','.join(map(str,d['resources'])),str(rng['After']if rng else 0)]))
  raw=h.stored(r,'original-battle-world-r1','world-r1/native-retreat-oracle/receipt.json');(q/'evidence/inherited-native-retreat-oracle.json').write_bytes(raw);assert json.loads(raw)['resources']==json.loads((q/'evidence/inherited-native-retreat-go.json').read_bytes())['resources'];(q/'settlement.tsv').write_text('\n'.join(lines)+'\n');return
 if a.action=='media':
  from PIL import Image
  h.dependencies(r);sources={}
  for kind in range(1,26):
   p=q/f'native/pack/unit_native_{kind:02}.rgba'
   if p.exists():continue
   manifest=a.assets/f'troop-man{kind:02}.json'
   if not manifest.exists():manifest=a.assets/f'battle-man{kind:02}.json'
   m=read(manifest)['frames'][0];v=m['image'];source=a.assets/v['file'];assert sha(source)==v['sha256'];im=Image.open(source).convert('RGBA');assert im.size==(v['width'],v['height']);x,y,w,hh=v['source_rect'];tx,ty,tw,th=m['target_rect'];tile=Image.new('RGBA',(264,300));tile.paste(im.crop((x,y,x+w,y+hh)).resize((tw,th),Image.Resampling.BILINEAR),(tx,ty));b=b'8SRGBA01'+struct.pack('<II',264,300)+tile.tobytes();p.write_bytes(b+struct.pack('<Q',module(r,'rust-native-player.py').fnv(b)));sources[str(kind)]=dict(manifest=manifest.name,sha256=sha(manifest),image=v,target=m['target_rect'])
  assert all((q/f'native/pack/unit_native_{i:02}.rgba').is_file()for i in range(1,26));write(a.out,sources);return
 if a.action=='prepare':
  q.mkdir();(q/'native/pack').mkdir(parents=True);(q/'evidence').mkdir()
  for f in read(r/'preserved/rust-world-r1.json')['files']:
   if '/native/pack/'in f['path']:(q/'native/pack'/Path(f['path']).name).write_bytes(h.stored(r,'rust-world-r1',f['path']))
  for name in['probe.mod','probe.sum']:(q/name).write_bytes(h.stored(r,'rust-world-r1','/'+name))
  (q/'evidence/ida-world-r3.json').write_bytes(h.stored(r,'owned-world-r1','ida/ida-world-r3.json'))
  (q/'evidence/ida-defeat-r2.json').write_bytes(h.stored(r,'original-battle-world-r1','evidence/ida-defeat-r2.json'))
  pam=r/'workplace/intake-20261023/sources/game/8sword/PAM.AY';raw=pam.read_bytes();assert sha(pam)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0';ds=struct.unpack_from('<H',raw,8)[0]*16+0x1d780
  words=lambda off,n:list(struct.unpack_from('<'+'H'*n,raw,ds+off))
  write(q/'evidence/pam-initial.json',dict(resources=words(0x4f2,6),army=words(0x54a,12),thresholds=words(0x5b2,6),enemy=words(0x26ae,1),modifiers=[words(0x26b2,1),words(0x26b8,1)]));return
 if a.action=='freeze':
  shutil.copytree(r/'internal/remake-rust',q/'rust-source');(q/'tools').mkdir()
  for n in['rust-journey.py','rust-journey-gui.py','rust-native-player.sh']:shutil.copy2(r/'tools'/n,q/'tools'/n)
  shutil.copy2(r/'internal/ownedworld/rust_journey_reference_test.go',q/'evidence/rust_journey_reference_test.go');write(q/'media.json',{p.name:sha(p)for p in(q/'native/pack').iterdir()if p.is_file()});return
 if a.action=='audit':
  counts={k:len(v)for k,v in h.dependencies(r).items()};assert list(counts.values())==[197,7,923,535]
  crate={str(p.relative_to(r/'internal/remake-rust')):sha(p)for p in(r/'internal/remake-rust').rglob('*')if p.is_file()};assert all(sha(q/'rust-source'/n)==v for n,v in crate.items());assert all(sha(q/'native/pack'/n)==v for n,v in read(q/'media.json').items())
  assert(q/'generator.tsv').read_bytes()==(r/'internal/remake-rust/generator-reference.tsv').read_bytes();log=(q/'native/tests.log').read_text();assert 'FAILED'not in log and 'test result: ok.'in log
  assert '46 passed'in log and len((q/'generator.tsv').read_text().splitlines())==321
  assert(q/'settlement.tsv').read_bytes()==(r/'internal/remake-rust/settlement-reference.tsv').read_bytes()
  initial=read(q/'evidence/pam-initial.json');assert initial['resources']==[1,0,100,500,100,0]and initial['army']==[1,30]+[0]*10 and initial['thresholds']==[0,2000,5000,8000,12000,30000]and initial['enemy']==[0]and initial['modifiers']==[[0],[0]]
  assert all((q/f'native/pack/unit_native_{i:02}.rgba').is_file()for i in range(1,26))
  gui=read(q/'native/gui/receipt.json');assert gui['status']=='passed-rust-journey-gui'and gui['binary_sha256']==sha(q/'native/8sword-remake')
  from PIL import Image
  for row in gui['runs']:
   assert row['exit']==0
   for cap in row['captures']:
    p=q/'native/gui'/row['name']/f"frame-{cap['number']:03}.ppm";assert p.read_bytes()==p.with_name(f"readback-{cap['number']:03}.ppm").read_bytes();assert cap['captured']['frame_hash']==format(module(r,'rust-native-player.py').fnv(Image.open(p).convert('RGBA').tobytes()),'016x')
  write(a.out,dict(status='passed-rust-journey-audit',crate=crate,binary_sha256=sha(q/'native/8sword-remake'),baseline=counts,gui=gui,initial=read(q/'evidence/pam-initial.json'),execution=read(q/'execution.json'),limits=['Bounded native random encounters; guarded sites/recruit/monthly/complete world remain pending.','Controlled generator oracle; rule RNG excludes ambient original drawing calls.','Journey development checkpoint is not complete game schema or Go save importer.','Approved art; native prompt and result text simplified, no full animation timing claim.']));return
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for p in sorted(q.rglob('*')):
  if not p.is_file()or any(n in p.relative_to(q).parts for n in['go-cache','rust-target']):continue
  assert not p.is_symlink()and p.stat().st_uid==1000;raw=p.read_bytes();v=hashlib.sha256(raw).hexdigest();o=folder/(v+'.gz')
  if v not in objects:o.write_bytes(gzip.compress(raw,6,mtime=0));objects[v]=dict(file=o.name,stored_sha256=sha(o))
  files.append(dict(path=str(Path(REL)/p.relative_to(q)),sha256=v,bytes=len(raw),mode=p.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,rights='Full original-derived maps/media/binary and RE exports local only; no Release'))
if __name__=='__main__':main()
