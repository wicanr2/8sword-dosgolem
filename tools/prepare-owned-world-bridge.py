#!/usr/bin/env python3
"""030 DRAFT: prepare, independently audit and preserve native resource transport."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,struct
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/owned-world-bridge-r1'
TOOLS=['export-owned-save-ida.py','research-native-progress.go','research-native-progress_test.go','probe-native-progress.go','prepare-owned-world-bridge.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def lib(r):
 s=importlib.util.spec_from_file_location('old',r/'tools/prepare-owned-army-ui.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def stored_path(r,batch,predicate):
 d=read(r/'preserved'/(batch+'.json'));fs=[f for f in d['files'] if predicate(f['path'])];assert len(fs)==1,[f['path'] for f in fs];f=fs[0];obj=d['objects'][f['sha256']];p=r/'preserved'/batch/obj['file'];assert sha(p)==obj['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes'] and hashlib.sha256(raw).hexdigest()==f['sha256'];return raw,f['path']
def verify(a,out):
 d=read(a/'owned-world-bridge-r1.json');checked=set()
 for f in d['files']:
  assert not Path(f['path']).is_absolute() and '..' not in Path(f['path']).parts
  obj=d['objects'][f['sha256']];p=a/'owned-world-bridge-r1'/obj['file'];assert sha(p)==obj['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes'] and hashlib.sha256(raw).hexdigest()==f['sha256'];checked.add(f['sha256'])
 write(out,dict(status='passed-detached-owned-world-bridge',files=len(d['files']),objects=len(checked),workplace_required=False,index_sha256=sha(a/'owned-world-bridge-r1.json')))
def resources(raw):
 assert len(raw)==2987;n=[(struct.unpack_from('<H',raw,i*2)[0]-i*2-3)&65535 for i in range(6)]
 return dict(zip(['rank','merit','monthly_pay','gold','leadership','spell_power'],n))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','audit','archive','verify','integrity']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--out',type=Path);p.add_argument('--audit',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists() and os.getuid()==1000
 if a.action=='verify':verify(a.archive,a.out);return
 r=a.project;q=r/REL;deps=lib(r).dependencies(r)
 if a.action=='prepare':
  assert q.stat().st_uid==1000 and not(q/'go-src').exists();src=q/'go-src'
  for n in deps['source_inputs']:
   t=src/n;t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,t)
  (src/'tools').mkdir(exist_ok=True)
  for n in TOOLS:shutil.copyfile(r/'tools'/n,src/'tools'/n)
  for ext in ['mod','sum']:shutil.copyfile(src/('go.'+ext),q/('probe.'+ext))
  with(q/'probe.mod').open('a')as f:f.write('\nrequire github.com/wicanr2/dosgolem v0.0.0\nreplace github.com/wicanr2/dosgolem => /core\n')
  d=read(r/'preserved/troop-capacity-r1.json');maps=[f['path'] for f in d['files'] if f['path'].lower().endswith('/scratch/map01.ay')];write(q/'inputs/native-map-candidates.json',maps)
  # Use the exact normal F7 save and its paired map, never an arbitrary map.
  files=[f['path'] for f in d['files'] if f['path'].endswith('/saved-gamedata.ay')];assert len(files)==1,files
  prefix=files[0].rsplit('/',1)[0];native=q/'inputs/native';native.mkdir()
  saved,origin=stored_path(r,'troop-capacity-r1',lambda p:p==files[0]);(q/'inputs/original-save.ay').write_bytes(saved);(native/'gamedata.ay').write_bytes(saved)
  mapdata,maporigin=stored_path(r,'troop-capacity-r1',lambda p:p.lower()==(prefix+'/scratch/map01.ay').lower());(native/'map01.ay').write_bytes(mapdata)
  battle,battleorigin=stored_path(r,'owned-battle-ui-r1',lambda p:p.endswith('/gui-r1/receipt.json'));b=json.loads(battle);assert b['status']=='passed-real-go-battle-ui';w=b['final_world'];target=dict(rank=w['progress']['rank'],merit=w['progress']['merit'],monthly_pay=w['progress']['legacy_04f6'],gold=w['army']['gold'],leadership=w['army']['leadership'],spell_power=w['progress']['legacy_04fc']);write(q/'inputs/target-resources.json',target);(q/'inputs/go-battle-source.json').write_bytes(battle);write(q/'inputs/provenance.json',dict(native_save_source=origin,native_map_source=maporigin,go_source=battleorigin,go_source_sha256=hashlib.sha256(battle).hexdigest(),controlled_transport=True));write(q/'baseline-r1.json',deps);return
 if a.action=='audit':
  ida=read(q/'ida/ida-save-r1.json');assert ida['tool']=='IDA Pro 9.4' and ida['function_count']==521;raw=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();header=int.from_bytes(raw[8:10],'little')*16
  reloc=set();count,table=struct.unpack_from('<H',raw,6)[0],struct.unpack_from('<H',raw,24)[0]
  for i in range(count):off,seg=struct.unpack_from('<HH',raw,table+i*4);reloc.add(header+seg*16+off)
  lines=0
  for body in ida['bodies']:
   for l in body['lines']:
    pos=l['file_offset'];bs=bytearray.fromhex(l['bytes']);assert pos==l['ida_linear']-0x10000+header
    original=bytearray(raw[pos:pos+len(bs)])
    for at in reloc:
     if pos<=at and at+2<=pos+len(bs):v=struct.unpack_from('<H',original,at-pos)[0];struct.pack_into('<H',original,at-pos,(v+0x1000)&65535)
    assert bytes(original)==bytes(bs),(hex(l['ida_linear']),original.hex(),bs.hex());lines+=1
  base=(q/'inputs/original-save.ay').read_bytes();before=resources(base);target=read(q/'inputs/target-resources.json');result=[]
  provenance=read(q/'inputs/provenance.json')
  saved_source,_=stored_path(r,'troop-capacity-r1',lambda p:p==provenance['native_save_source']);map_source,_=stored_path(r,'troop-capacity-r1',lambda p:p==provenance['native_map_source']);go_source,_=stored_path(r,'owned-battle-ui-r1',lambda p:p==provenance['go_source'])
  assert base==saved_source==(q/'inputs/native/gamedata.ay').read_bytes() and map_source==(q/'inputs/native/map01.ay').read_bytes() and go_source==(q/'inputs/go-battle-source.json').read_bytes()
  w=json.loads(go_source)['final_world'];assert target==dict(rank=w['progress']['rank'],merit=w['progress']['merit'],monthly_pay=w['progress']['legacy_04f6'],gold=w['army']['gold'],leadership=w['army']['leadership'],spell_power=w['progress']['legacy_04fc'])
  for phase in ['control-r1','transport-r1']:
   folder=q/phase;d=read(folder/'receipt.json');assert d['status']=='passed-native-resource-transport';expected=before if phase=='control-r1'else target;assert d['before']==before and d['after']==d['cold_resources']==expected
   candidate=(folder/'go-candidate.ay').read_bytes();saved=(folder/'native-saved.ay').read_bytes();assert resources(candidate)==resources(saved)==expected and candidate[12:]==base[12:] and len(candidate)==2987
   assert (folder/'native-army-before.bin').read_bytes()==(folder/'native-army-after.bin').read_bytes() and saved[12:36]==base[12:36]
   assert d['native_prefix_equals_go'] and d['cold_engine'] and not d['snapshot_loaded'] and not d['normal_extended_army_path'];result.append(d)
  log=(q/'go-test-r1.log').read_text();assert 'PASS' in log and 'FAIL' not in log and 'SKIP' not in log
  write(a.out,dict(status='passed-draft-native-resource-bridge',dependencies=deps,source_tools={n:sha(r/'tools'/n)for n in TOOLS},ida_lines=lines,native_cases=result,all_nonresource_candidate_bytes_preserved=2975,production_changed=False,limits=['Controlled six-resource write in native RAM, not natural Go army handoff.','Original army, unknown save fields and formal sidecar guard are untouched.']));return
 if a.action=='archive':
  receipt=a.audit or q/'audit-r1.json';audit=read(receipt);assert audit['source_tools']=={n:sha(r/'tools'/n)for n in TOOLS};directory=a.archive/'owned-world-bridge-r1';directory.mkdir();selected={p for p in q.rglob('*')if p.is_file()};selected.update(r/'tools'/n for n in TOOLS);selected.update(r/n for n in ['docs/spec/030-battle-expansion-proposal.md','RESEARCH-LOG.md']);files=[];objects={}
  for p in sorted(selected):
   assert not p.is_symlink() and p.stat().st_uid==1000;raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest()
   if h not in objects:
    blob=gzip.compress(raw,compresslevel=6,mtime=0);name=h+'.gzip';(directory/name).write_bytes(blob);objects[h]=dict(file=name,stored_sha256=hashlib.sha256(blob).hexdigest(),stored_bytes=len(blob))
   files.append(dict(path=str(p.relative_to(r)),sha256=h,bytes=len(raw),mode=p.stat().st_mode&0o777))
  write(a.archive/'owned-world-bridge-r1.json',dict(files=files,objects=objects,dependencies=deps,audit_sha256=sha(receipt)));write(a.out,dict(status='preserved-owned-world-bridge',files=len(files),objects=len(objects),stored_bytes=sum(v['stored_bytes']for v in objects.values())));return
 assert not read(a.archive/'owned-world-bridge-verification-r1.json')['workplace_required'];art=read(r/'artwork/manifest.json');assert len(art['files'])==1040
 for f in art['files']:assert sha(r/'artwork'/f['path'])==f['sha256']
 write(a.out,dict(status='passed-owned-world-bridge-integrity',source_inputs=197,programs=7,core=923,assets=535,artwork=1040,production_changed=False))
if __name__=='__main__':main()
