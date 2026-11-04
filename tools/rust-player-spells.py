#!/usr/bin/env python3
"""Rust玩家法術：永久來源、向量、媒體與限定核對。只在Docker使用。"""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-player-spells-r1'
REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def module(r,name):
 spec=importlib.util.spec_from_file_location(name,r/'tools'/name);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def vectors(r,q):
 lines=(q/'spell-models.tsv').read_text().splitlines();nums=lambda v:','.join(map(str,v));rows=lambda v:','.join((s['unit']or'-')+'='+str(s['count'])for s in v)
 for item in read(q/'evidence/sources.json'):
  p=q/'evidence'/item['file'];assert sha(p)==item['sha256'];v=read(p);record=v.get('record');support=v.get('records');kind=v.get('kind',12);effects=[];militia=30
  if support:
   clone=support[0]['Clone']
   if clone:militia=clone['Before'];effects=[(0,clone['Target'],clone['Raw'],0,clone['Before'],clone['After'],clone['Display']or[])]
   charges=list(struct.unpack('<8H',bytes.fromhex(v['charges_hex'])));counters=v['counters'];seed=after=0
  else:
   effects=[(1,e['Target'],e['Raw'],e['Amount'],e['Before'],e['After'],e['Display']or[])for e in record['Effects']or[]]
   charges=record['AfterCharges'];counters=None;random=record['Random'];seed=random['Before']if random else 0;after=random['After']if random else 0
  ability=0 if 'assassination-fail'in v['name']else 4
  fields=['CASE',v['name'],kind,militia,v['selector'],v['cancel']or'-',ability,seed,after,rows(v['rows'][0]),rows(v['rows'][1]),nums(charges),nums(counters)if counters is not None else'-']
  lines.append('\t'.join(map(str,fields)))
  for side,slot,raw,n,before,last,display in effects:lines.append('\t'.join(map(str,['EFFECT',side,slot,raw,n,before,last,nums(display)if display else'-'])))
  lines.append('END')
 raw=('\n'.join(lines)+'\n').encode()
 for p in [q/'spell-reference.tsv',r/'internal/remake-rust/spell-reference.tsv']:
  if p.exists():assert p.read_bytes()==raw,p
  else:p.write_bytes(raw)
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['prepare','vectors','media','audit','archive','verify'])
 for n in ['project','work','assets','archive','out']:ap.add_argument('--'+n,type=Path)
 a=ap.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  index=read(a.archive/(BATCH+'.json'))
  for row in index['files']:
   ob=index['objects'][row['sha256']];p=a.archive/BATCH/ob['file'];assert sha(p)==ob['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==row['bytes']and hashlib.sha256(raw).hexdigest()==row['sha256']
  write(a.out,dict(status='passed-detached-rust-player-spells',files=len(index['files']),objects=len(index['objects'])));return
 r=a.project;q=a.work or r/REL
 if a.action=='prepare':
  helper=module(r,'prepare-owned-army-ui.py');q.mkdir();(q/'native').mkdir();(q/'evidence').mkdir();(q/'inputs').mkdir();prev='workplace/probe-20261023/graphics-first/battle-r1/rust-native-player-r1'
  for n in ['PAM.AY','army-catalog.json','combat-catalog.json']:(q/'inputs'/n).write_bytes(helper.stored(r,'rust-native-player-r1',prev+'/inputs/'+n))
  for n in ['probe.mod','probe.sum']:(q/n).write_bytes(helper.stored(r,'rust-native-player-r1',prev+'/'+n))
  cases=[]
  for batch,prefix in [('original-battle-spells-r1','casts-r1'),('original-battle-support-r1','support-r1')]:
   for row in read(r/'preserved'/(batch+'.json'))['files']:
    parts=Path(row['path']).parts
    if prefix not in parts or not row['path'].endswith('-mode-1/receipt.json')or'native-mode'in row['path']:continue
    raw=helper.stored(r,batch,row['path']);name=batch+'-'+parts[-2]+'.json';(q/'evidence'/name).write_bytes(raw);cases.append(dict(batch=batch,file=name,sha256=hashlib.sha256(raw).hexdigest()))
  write(q/'evidence/sources.json',sorted(cases,key=lambda v:v['file']))
  for n in ['ida-spells-r4.json','provenance.json']:(q/'evidence'/n).write_bytes(helper.stored(r,'original-battle-spells-r1','evidence/'+n))
  (q/'evidence/ida-rounds.json').write_bytes(helper.stored(r,'rust-native-player-r1','rust-native-player-r1/evidence/ida-rounds.json'))
  return
 if a.action=='vectors':vectors(r,q);return
 if a.action=='media':
  from PIL import Image
  base=module(r,'rust-native-player.py');pack=q/'native/pack'
  if not pack.exists():
   saved=sys.argv;sys.argv=[saved[0],'prepare','--project',str(r),'--work',str(q),'--assets',str(a.assets)];base.main();sys.argv=saved
  sources=[]
  entries=[(f'unit_native_{kind:02}.rgba',name,0)for kind,name in [(1,'battle-man01.json'),(10,'troop-man10.json'),(12,'troop-man12.json')]]+[(f'spell-impact-{i}.rgba','battle-pon.json',i)for i in range(4)]
  for dst,name,i in entries:
   meta=read(a.assets/name)['frames'][i];v=meta['image'];p=a.assets/v['file'];assert sha(p)==v['sha256'];im=Image.open(p).convert('RGBA');x,y,w,h=v['source_rect'];tx,ty,tw,th=meta['target_rect'];tile=Image.new('RGBA',(264,300));tile.paste(im.crop((x,y,x+w,y+h)).resize((tw,th),Image.Resampling.BILINEAR),(tx,ty));raw=b'8SRGBA01'+struct.pack('<II',264,300)+tile.tobytes();raw+=struct.pack('<Q',base.fnv(raw));p=pack/dst
   if p.exists():assert p.read_bytes()==raw
   else:p.write_bytes(raw)
   sources.append(dict(file=dst,manifest=name,frame=i,source=v))
  m=read(q/'media-source-r1.json')['music'];p=a.assets/m['file'];assert sha(p)==m['sha256']
  if not(pack/'music.ogg').exists():shutil.copy2(p,pack/'music.ogg')
  metadata=dict(sources=sources,pack_files={p.name:sha(p)for p in pack.iterdir()if p.is_file()},effects='approved PON four-frame impact; not full original animation parity')
  write(a.out or q/'spell-media-source-r2.json',metadata);return
 if a.action=='audit':
  from PIL import Image
  deps=module(r,'prepare-owned-army-ui.py').dependencies(r);counts={k:len(v)for k,v in deps.items()};assert list(counts.values())==[197,7,923,535]
  for n,h in read(q/'source-manifest.json').items():assert sha(q/'source'/n)==h,n
  vectors(r,q);log=(q/'tests-go-models-r2.log').read_text();assert'--- PASS: TestRustSpellReference'in log and'FAIL'not in log
  assert'test result: ok. 23 passed'in(q/'native/tests-rust-final.log').read_text()
  cli=(q/'native/cli-final.log').read_text();assert'2352'in cli and'15份'in cli
  crate=r/'internal/remake-rust';crate_files={str(p.relative_to(crate)):sha(p)for p in crate.rglob('*')if p.is_file()};assert all(sha(q/'rust-source'/n)==h for n,h in crate_files.items())
  media=read(q/'spell-media-source-r2.json');assert all(sha(q/'native/pack'/n)==h for n,h in media['pack_files'].items())
  gui=read(q/'native/gui-r3/receipt.json');assert gui['status']=='passed-rust-player-spells-gui'and gui['binary_sha256']==sha(q/'native/8sword-remake');pictures=[]
  for row in gui['rows']:
   assert row['exit']==0
   for capture in row['captures']:
    s=capture['status'];assert s['readback_equal']=='true';p=q/'native/gui-r3'/row['mode'];n=int(s['captures']);frame=p/f'frame-{n:03}.ppm';assert frame.read_bytes()==(p/f'readback-{n:03}.ppm').read_bytes();assert Image.open(frame).size==(1920,1320);captured=capture['captured'];assert format(module(r,'rust-native-player.py').fnv(Image.open(frame).convert('RGBA').tobytes()),'016x')==captured['frame_hash'];pictures.append(dict(case=row['mode'],label=capture['label'],sha256=sha(frame),captured=captured,status=s))
  win=gui['rows'][0]['final'];assert win['outcome']=='win'and win['sequence']=='17'and win['army']=='60,2,0,1,0,0'and win['charges']=='2,3,3,3,3,3,3,3'
  assert gui['rows'][1]['final']['outcome']=='retreat'and gui['rows'][1]['final']['charges']=='3,2,3,3,2,3,2,3'
  assert gui['rows'][2]['final']['outcome']=='retreat'and gui['rows'][2]['final']['charges']=='2,3,3,3,3,3,3,3'
  write(a.out,dict(status='passed-rust-player-spells-audit',tests_passed=23,models=2352,inherited_original_interface_cases=15,source_files=len(read(q/'source-manifest.json')),formal_baseline_counts=counts,crate_files=crate_files,binary_sha256=sha(q/'native/8sword-remake'),pictures=pictures,media=media,execution=read(q/'execution-r1.json'),limits=['Player spells only; enemy special dispatch and world/save pending.','15 spell receipts inherit existing original/Go pairs; models from current Go functions. No fresh original executable run.','Explicit rosters, enabled/stat/charge fixtures. Native RNG conditions controlled, no whole-call-stream parity.','Simplified menu backing and common PON impact; no complete original animation parity.','Linux X11 sampling; audio inherited, no new human-hearing or cross-platform acceptance.']))
  return
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for p in sorted(q.rglob('*')):
  if not p.is_file()or any(n in p.relative_to(q).parts for n in ['build-cache','rust-target']):continue
  assert p.stat().st_uid==1000 and not p.is_symlink();raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();obj=folder/(h+'.gz')
  if h not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(Path(REL)/p.relative_to(q)),bytes=len(raw),sha256=h,mode=p.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,rights='Original data, decoded media, captures and binaries local only; no release'))
if __name__=='__main__':main()
