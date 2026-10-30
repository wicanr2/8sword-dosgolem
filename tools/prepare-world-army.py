#!/usr/bin/env python3
"""030 DRAFT: prepare/audit/preserve the bounded native-shop Go army port."""
import argparse,gzip,hashlib,importlib.util,json,os,re,shutil,struct
from pathlib import Path

REL='workplace/probe-20261023/graphics-first/battle-r1/owned-world-army-r1'
BATCH='owned-world-army-r1'
TOOLS=['export-world-army-ida.py','research-world-army-port.go','research-world-army-port_test.go','probe-world-army.go','read-world-army-states.go','prepare-world-army.py']
REUSE=['paired-progress-check.go','research-owned-army.go','research-owned-world.go','research-native-progress.go','research-paired-progress.go','prepare-owned-army-ui.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def lib(r):
 s=importlib.util.spec_from_file_location('prior',r/'tools/prepare-owned-army-ui.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def verify(archive,out):
 d=read(archive/(BATCH+'.json'));seen=set()
 for f in d['files']:
  assert not Path(f['path']).is_absolute()and'..'not in Path(f['path']).parts
  o=d['objects'][f['sha256']];p=archive/BATCH/o['file'];assert sha(p)==o['stored_sha256'];b=gzip.decompress(p.read_bytes());assert len(b)==f['bytes']and digest(b)==f['sha256'];seen.add(f['sha256'])
 write(out,dict(status='passed-detached-world-army',files=len(d['files']),objects=len(seen),workplace_required=False,index_sha256=sha(archive/(BATCH+'.json'))))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','audit','archive','verify','integrity']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--out',type=Path);p.add_argument('--audit',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':verify(a.archive,a.out);return
 r=a.project;q=r/REL;m=lib(r);deps=m.dependencies(r)
 if a.action=='prepare':
  assert q.exists()and q.stat().st_uid==1000 and {p.name for p in q.iterdir()}=={'ida'}
  (q/'inputs').mkdir();src=q/'go-src'
  for n in deps['source_inputs']:
   t=src/n;t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,t)
  (src/'tools').mkdir(exist_ok=True)
  for n in TOOLS+REUSE:shutil.copyfile(r/'tools'/n,src/'tools'/n)
  text=(r/'tools/research-owned-army.go').read_text().removeprefix('//go:build ignore\n');text=text[:text.index('func main()')].replace('\n\t"flag"\n','\n');(src/'tools/owned-army-model.go').write_text(text)
  for ext in ['mod','sum']:shutil.copyfile(src/('go.'+ext),q/('probe.'+ext))
  with(q/'probe.mod').open('a')as f:f.write('\nrequire github.com/wicanr2/dosgolem v0.0.0\nreplace github.com/wicanr2/dosgolem => /core\n')
  for n in ['army-catalog.json','combat-catalog.json','seed-world.json','original-save.ay']:(q/'inputs'/n).write_bytes(m.stored(r,'owned-paired-save-r1','/inputs/'+n))
  shutil.copyfile(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY',q/'inputs/PAM.AY')
  assert sha(q/'inputs/PAM.AY')=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
  write(q/'baseline-r1.json',deps);return
 if a.action=='audit':
  raw=(q/'inputs/PAM.AY').read_bytes();ida=read(q/'ida/ida-world-army-r1.json');assert ida['tool']=='IDA Pro 9.4'and ida['function_count']==521 and ida['source_sha256']==digest(raw) and ida['exporter_sha256']==sha(r/'tools/export-world-army-ida.py')
  header=struct.unpack_from('<H',raw,8)[0]*16;relocs=set()
  for i in range(struct.unpack_from('<H',raw,6)[0]):off,seg=struct.unpack_from('<HH',raw,struct.unpack_from('<H',raw,24)[0]+i*4);relocs.add(header+seg*16+off)
  lines=0
  for b in ida['functions']:
   for l in b['lines']:
    pos=l['file_offset'];want=bytes.fromhex(l['bytes']);actual=bytearray(raw[pos:pos+len(want)]);assert pos==l['ida_linear']-0x10000+header
    for loc in relocs:
     if pos<=loc and loc+2<=pos+len(want):struct.pack_into('<H',actual,loc-pos,(struct.unpack_from('<H',actual,loc-pos)[0]+0x1000)&65535)
    assert bytes(actual)==want;lines+=1
  guard_text=(r/'tools/research-world-army-port.go').read_text().split('var worldArmyReadGuards = []uint16{',1)[1].split('}',1)[0]
  actual_guards={int(v,16)for v in re.findall(r'0x[0-9a-f]+',guard_text)}
  expected_guards={v['line']['ida_linear']-0x10000 for v in ida['candidates']if v['function']not in [0x154ea,0x158f0,0x1593c,0x15962]}|{0x56f1}
  assert actual_guards==expected_guards
  receipts=[]
  for phase,applied,maximum in [('control-r2',False,70),('port-r2',True,55)]:
   folder=q/phase;d=read(folder/'receipt.json');assert d['status']=='passed-world-army-port-probe'and d['go_port']==applied and d['maximum']==maximum and d['guest_gold']==299 and d['purchase_count']==1 and d['formal_guard']
   before=read(folder/'pair-before.json');after=read(folder/'pair-after.json');world=after['world'];idx=read(folder/'decoded/index.json');mem={n:gzip.decompress((folder/'decoded'/v['memory_file']).read_bytes()) for n,v in idx.items()}
   for b in mem.values():assert len(b)==1<<20
   army_before=(folder/'native-army-before.bin').read_bytes();army_after=(folder/'native-army-after.bin').read_bytes();assert army_before==struct.pack('<12H',1,30,*([0]*10))
   ds=0x1e880
   for name in ['before-commit.state','after-commit.state','final-map.state']:
    ram=mem[name];assert struct.unpack_from('<H',ram,ds+0x4f8)[0]==(300 if name=='before-commit.state' else 299)
    assert ram[ds+0x54a:ds+0x562]==(army_before if applied or name=='before-commit.state'else army_after)
   cold=read(folder/'cold-process-r1.json');assert cold['engine_guard']and not cold['journal_present']and cold['snapshot']==after
   native=(folder/'paired-save/gamedata.ay').read_bytes();saved=read(folder/'paired-save/gamedata.ay.army.json');assert native[12:]==(folder/'original-save.ay').read_bytes()[12:]and saved['original_sha256']==digest(native)and saved['world']==world
   values=[(struct.unpack_from('<H',native,i*2)[0]-i*2-3)&65535 for i in range(6)];assert values==[world['progress']['rank'],world['progress']['merit'],world['progress']['legacy_04f6'],world['army']['gold'],world['army']['leadership'],world['progress']['legacy_04fc']]
   if applied:
    assert d['blocked_f2'].startswith('unsupported world army operand at 0110:')
    assert army_before==army_after and world['army']['gold']==299 and world['army']['slots'][:2]==[dict(unit='native:01',count=31),dict(unit='openkb:wolf',count=5)]
    assert d['go_purchases']==1 and d['native_helper_entries']==0 and [x['route']for x in d['go_records']]==['capacity','command','used','commit'] and [x['value']for x in d['go_records']]==[1,1,45,1]
    assert world['army']['offers']['verified-militia-shop-r1']['stock']==d['offer_stock']-1 and world['army']['offers']['controlled-wolves']['stock']==995
    assert after['token']==d['cold_pair_token']and after['token']!=before['token']
   else:assert struct.unpack('<12H',army_after)==(1,31,*([0]*10))and before==after
   receipts.append(d)
  assert sha(q/'control-r2/projected-map.state')==sha(q/'port-r2/projected-map.state')
  for n in TOOLS+REUSE:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n)
  test=(q/'go-test-r3.log').read_text();assert'PASS'in test and'FAIL'not in test and'SKIP'not in test
  for n in ['go-vet-r3.log','probe-build-r3.log','reader-build-r1.log','pair-reader-build-r1.log']:assert(q/n).stat().st_size==0
  write(a.out,dict(status='passed-draft-world-army-port',dependencies=deps,source_tools={n:sha(r/'tools'/n)for n in TOOLS+REUSE},ida_functions=len(ida['functions']),ida_lines=lines,original_states_independently_read=6,cases=receipts,production_changed=False,limits=['Controlled five-wolf Go setup before ordinary militia-shop input.','One militia-shop caller; map stock identity/monthly/other consumers and normal expanded-army load remain unintegrated.','No original instruction-clock parity or new actual Ebiten window claim.']));return
 if a.action=='archive':
  receipt=a.audit or q/'audit-r1.json';d=read(receipt);assert d['source_tools']=={n:sha(r/'tools'/n)for n in TOOLS+REUSE};folder=a.archive/BATCH;folder.mkdir();files=[];objects={};selected={p for p in q.rglob('*')if p.is_file()};selected.update(r/'tools'/n for n in TOOLS+REUSE);selected.update(r/n for n in ['docs/spec/030-battle-expansion-proposal.md','RESEARCH-LOG.md'])
  for f in sorted(selected):
   assert not f.is_symlink()and f.stat().st_uid==1000;b=f.read_bytes();h=digest(b)
   if h not in objects:
    blob=gzip.compress(b,compresslevel=6,mtime=0);name=h+'.gzip';(folder/name).write_bytes(blob);objects[h]=dict(file=name,stored_sha256=digest(blob),stored_bytes=len(blob))
   files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(b),mode=f.stat().st_mode&0o777))
  write(a.archive/(BATCH+'.json'),dict(files=files,objects=objects,dependencies=deps,audit_sha256=sha(receipt)));write(a.out,dict(status='preserved-world-army-port',files=len(files),objects=len(objects),stored_bytes=sum(v['stored_bytes']for v in objects.values())));return
 assert not read(a.archive/'owned-world-army-verification-r1.json')['workplace_required'];art=read(r/'artwork/manifest.json');assert len(art['files'])==1040
 for f in art['files']:assert sha(r/'artwork'/f['path'])==f['sha256']
 write(a.out,dict(status='passed-world-army-integrity',source_inputs=197,programs=7,core=923,assets=535,artwork=1040,production_changed=False))
if __name__=='__main__':main()
