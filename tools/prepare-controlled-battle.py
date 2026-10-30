#!/usr/bin/env python3
"""Explicit controlled VM-state experiments; no production path promotion."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,struct,subprocess
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/controlled-owned-battle-r1'
BATCH='controlled-owned-battle-r1'
NEW=['prepare-controlled-battle.py','research-controlled-battle.go','probe-controlled-battle.go']
COMMON=['research-owned-army.go','research-owned-world.go','research-owned-defeat.go','research-owned-encounter.go','research-native-progress.go','research-paired-progress.go','research-world-army-port.go','paired-progress-check.go','read-world-army-states.go']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','decode','audit','archive','verify']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--out',type=Path);p.add_argument('--work',type=Path,help='explicit writable alias for decode');a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   o=d['objects'][f['sha256']];obj=a.archive/BATCH/o['file'];assert sha(obj)==o['stored_sha256'];b=gzip.decompress(obj.read_bytes());assert len(b)==f['bytes']and hashlib.sha256(b).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-controlled-battle',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL
 if a.action=='decode':
  work=a.work or q
  for d in sorted((work/'cases').iterdir()):subprocess.run([str(q/'state-reader'),'-calls',str(d),'-out',str(d/'decoded')],check=True)
  return
 s=importlib.util.spec_from_file_location('prior',r/'tools/prepare-owned-army-ui.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);deps=m.dependencies(r)
 if a.action=='prepare':
  assert not q.exists();q.mkdir();(q/'inputs').mkdir();src=q/'go-src'
  for n in deps['source_inputs']:
   t=src/n;t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,t)
  (src/'tools').mkdir(exist_ok=True)
  for n in COMMON:shutil.copyfile(r/'tools'/n,src/'tools'/n)
  text=(r/'tools/research-owned-army.go').read_text().removeprefix('//go:build ignore\n');text=text[:text.index('func main()')].replace('\n\t"flag"\n','\n');(src/'tools/owned-army-model.go').write_text(text)
  for ext in ['mod','sum']:shutil.copyfile(src/('go.'+ext),q/('probe.'+ext))
  with(q/'probe.mod').open('a')as f:f.write('\nrequire github.com/wicanr2/dosgolem v0.0.0\nreplace github.com/wicanr2/dosgolem => /core\n')
  for n in ['army-catalog.json','combat-catalog.json','seed-world.json','original-save.ay']:(q/'inputs'/n).write_bytes(m.stored(r,'owned-battle-ui-r1','/inputs/'+n))
  (q/'inputs/battle-before.state').write_bytes(m.stored(r,'owned-world-r1','/normal-r4/04-battle-call-before.state'))
  (q/'inputs/ida-world-army-r1.json').write_bytes(m.stored(r,'owned-world-army-r1','/ida/ida-world-army-r1.json'))
  (q/'inputs/PAM.AY').write_bytes((r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes())
  write(q/'baseline.json',deps);return
 assert deps==read(q/'baseline.json')
 if a.action=='freeze':
  for n in NEW:shutil.copyfile(r/'tools'/n,q/'go-src/tools'/n)
  return
 if a.action=='audit':
  for n in NEW+COMMON:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n)
  raw=(q/'inputs/PAM.AY').read_bytes();ida=read(q/'inputs/ida-world-army-r1.json');assert sha(q/'inputs/PAM.AY')==ida['source_sha256']=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0';header=struct.unpack_from('<H',raw,8)[0]*16;relocs=[];lines=0
  for i in range(struct.unpack_from('<H',raw,6)[0]):off,seg=struct.unpack_from('<HH',raw,struct.unpack_from('<H',raw,24)[0]+i*4);relocs.append(header+seg*16+off)
  for f in ida['functions']:
   if f['start']not in [0x1151c,0x132e0]:continue
   for line in f['lines']:
    pos=line['file_offset'];want=bytes.fromhex(line['bytes']);b=bytearray(raw[pos:pos+len(want)]);assert pos==line['ida_linear']-0x10000+header
    for loc in relocs:
     if pos<=loc and loc+2<=pos+len(want):struct.pack_into('<H',b,loc-pos,(struct.unpack_from('<H',b,loc-pos)[0]+0x1000)&65535)
    assert bytes(b)==want;lines+=1
  profiles=read(q/'inputs/combat-catalog.json')['profiles'];army={v['id']:v for v in read(q/'inputs/army-catalog.json')['profiles']}
  results=[]
  for d in sorted((q/'cases').iterdir()):
   v=read(d/'receipt.json');idx=read(d/'decoded/index.json');ram={n:gzip.decompress((d/'decoded'/x['memory_file']).read_bytes())for n,x in idx.items()};before,after,final=[ram[n]for n in ['before-commit.state','after-commit.state','final-map.state']]
   allowed=set()
   for p in v['injected_ranges']:allowed.update(range(p['linear'],p['linear']+p['bytes']))
   changed=[i for i,(x,y)in enumerate(zip(before,after))if x!=y];assert set(changed)<=allowed and len(changed)==v['injected_changed_bytes']
   old=idx['before-commit.state'];new=idx['after-commit.state'];bp=old['registers'][5];ds=0x1e880;u16=lambda b,p:struct.unpack_from('<H',b,p)[0]
   assert old['ip']==0x3733 and old['registers'][4]==bp-0x14
   assert new['ip']==0x32e0 and new['registers'][4]==bp+2 and new['registers'][5]==u16(before,ds+bp)
   assert new['registers'][:4]==old['registers'][:4]and new['registers'][6]==u16(before,ds+bp-0x12)and new['registers'][7]==u16(before,ds+bp-0x10)
   if v['expected_rejection']:
    assert v['rejected']and after==final and v['disk_unchanged']
    for k in ['registers','segments','ip','flags']:assert idx['after-commit.state'][k]==idx['final-map.state'][k]
    results.append(v);continue
   assert not v['rejected']and v['native_calls']==0 and v['return_gate']==0x0bd3
   assert after[ds+0x54a:ds+0x562]==final[ds+0x54a:ds+0x562]==bytes([255])*24
   assert after[ds+0x56e8:ds+0x5718]==final[ds+0x56e8:ds+0x5718]==bytes([255])*48
   w=v['world_after'];assert v['cold_final']['world']==w and w['battle']is None and not w['encounters']
   initial=v['world_before'];rows=json.loads(json.dumps([initial['army']['slots'],initial['encounters']['random:controlled-r1']['enemy']]))
   for event in v['actions']:
    action=event['action'];side=action['side'];source=rows[side][action['source']];target=rows[1-side][action['target']];damage=source['count']*profiles[source['unit']]['attack']//5;quotient=damage//profiles[target['unit']]['hp'];loss=0 if quotient==0 else target['count']if quotient>=target['count']-1 else quotient
    assert event['damage']==damage and event['loss']==loss and event['before']==target['count']and event['after']==target['count']-loss;target['count']-=loss
   expected_world=json.loads(json.dumps(initial));expected_world['revision']+=2;survivors=[x for x in rows[0]if x['count']];expected_world['army']['slots']=survivors+[dict(unit='',count=0)]*(6-len(survivors));expected_world['encounters']={}
   if v['result']==0:
    enemy=initial['encounters']['random:controlled-r1']['enemy'];expected_world['army']['gold']=min(30000,initial['army']['gold']+sum(x['count']*army[x['unit']]['gold']for x in enemy if x['count']));expected_world['progress']['merit']=min(30000,initial['progress']['merit']+sum(x['count']*army[x['unit']]['command']for x in enemy if x['count'])//2)
    rank=initial['progress']['rank']
    if rank<5 and expected_world['progress']['merit']>initial['progress']['thresholds'][rank]:
     expected_world['progress']['rank']+=1;expected_world['army']['recruit_rank']+=1;expected_world['army']['leadership']=min(30000,initial['army']['leadership']+100);expected_world['progress']['legacy_04f6']=min(30000,initial['progress']['legacy_04f6']+100);expected_world['progress']['legacy_04fc']=min(30000,initial['progress']['legacy_04fc']+(rank+1)*3)
   elif v['result']==1:expected_world['army']['gold']-=initial['army']['gold']//(v['random_input']//2730+3)
   assert expected_world==w
   native=(d/'paired-save/gamedata.ay').read_bytes();side=read(d/'paired-save/gamedata.ay.army.json');assert side['world']==w and side['original_sha256']==sha(d/'paired-save/gamedata.ay')and native[12:]==(q/'inputs/original-save.ay').read_bytes()[12:]
   expected=[w['progress']['rank'],w['progress']['merit'],w['progress']['legacy_04f6'],w['army']['gold'],w['army']['leadership'],w['progress']['legacy_04fc']];assert [u16(final,ds+0x4f2+i*2)for i in range(6)]==expected==[(u16(native,i*2)-i*2-3)&65535 for i in range(6)]
   assert idx['final-map.state']['ip']==0x0bd3;results.append(v)
  assert len(results)==9 and sum(x['rejected']for x in results)==5
  write(a.out,dict(status='passed-controlled-go-battle-memory',cases=results,dependencies=deps,source_tools={n:sha(r/'tools'/n)for n in NEW+COMMON},ida_lines=lines,input_state_sha256=sha(q/'inputs/battle-before.state'),controlled_memory=True,normal_player_path=False,production_changed=False,limits=['Fixed pre-battle snapshot and explicit RAM/register injection.','Go fixtures supply encounter and combat configuration; no natural enemy import claim.','Raw dosgolem return-ABI experiment, not a new HD GUI or full world-save acceptance.']));return
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for f in sorted(q.rglob('*')):
  if not f.is_file():continue
  assert f.stat().st_uid==1000 and not f.is_symlink();b=f.read_bytes();h=hashlib.sha256(b).hexdigest();obj=folder/(h+'.gz')
  if h not in objects:obj.write_bytes(gzip.compress(b,compresslevel=6,mtime=0));objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(b),mode=f.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Local original snapshots; full objects excluded from Git.'))
if __name__=='__main__':main()
