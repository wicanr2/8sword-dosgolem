#!/usr/bin/env python3
"""Prepare/preserve the bounded Go encounter army-presence candidate."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,struct
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/owned-army-presence-r1'
BATCH='owned-army-presence-r1'
NEW=['probe-army-presence-oracle.go','research-army-presence.go','research-army-presence_test.go','prepare-army-presence.py','check-army-presence.py']
COMMON=['research-owned-army.go','research-owned-world.go','research-native-progress.go','research-paired-progress.go','research-world-army-port.go','research-world-army-port_test.go','research-world-army-review.go','world-army-review_draw.go','world-army-review_main.go','research-world-army-dismiss.go','world-army-dismiss_draw.go','owned-army-ui.go','owned-army-ui_draw.go','owned-army-ui-xcheck.go']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','evidence','freeze','audit','archive','verify']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   o=d['objects'][f['sha256']];obj=a.archive/BATCH/o['file'];assert sha(obj)==o['stored_sha256'];raw=gzip.decompress(obj.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-army-presence',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL
 s=importlib.util.spec_from_file_location('prior',r/'tools/prepare-owned-army-ui.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);deps=m.dependencies(r)
 if a.action=='prepare':
  assert not q.exists();q.mkdir();(q/'inputs').mkdir();(q/'ida').mkdir();src=q/'go-src'
  for n in deps['source_inputs']:
   t=src/n;t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,t)
  (src/'tools').mkdir(exist_ok=True)
  for n in COMMON+['probe-army-presence-oracle.go']:shutil.copyfile(r/'tools'/n,src/'tools'/n)
  text=(r/'tools/research-owned-army.go').read_text().removeprefix('//go:build ignore\n');text=text[:text.index('func main()')].replace('\n\t"flag"\n','\n');(src/'tools/owned-army-model.go').write_text(text)
  for ext in ['mod','sum']:shutil.copyfile(src/('go.'+ext),q/('probe.'+ext))
  with(q/'probe.mod').open('a')as f:f.write('\nrequire github.com/wicanr2/dosgolem v0.0.0\nreplace github.com/wicanr2/dosgolem => /core\n')
  for n in ['army-catalog.json','combat-catalog.json','seed-world.json','original-save.ay']:(q/'inputs'/n).write_bytes(m.stored(r,'owned-world-army-r1','/inputs/'+n))
  for n in ['army-catalog.json','combat-catalog.json','map01.ay']:
   if n=='map01.ay':(q/'inputs'/n).write_bytes(m.stored(r,'owned-world-army-r1','/port-r2/scratch/'+n))
  for label,batch,path in [('empty','owned-world-army-dismiss-r1','/session-r1/'),('present','owned-world-army-r1','/port-r2/paired-save/')]:
   d=q/('session-'+label);d.mkdir()
   for n in ['gamedata.ay','gamedata.ay.army.json']:(d/n).write_bytes(m.stored(r,batch,path+n))
  (q/'inputs/PAM.AY').write_bytes((r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes())
  (q/'ida/ida-world-army-r1.json').write_bytes(m.stored(r,'owned-world-army-r1','/ida/ida-world-army-r1.json'))
  # Reuse the exact already-tested three-font UI atlases, no new lettering.
  old=read(r/'preserved/owned-world-army-dismiss-r1.json')
  for f in old['files']:
   mark='/ui-assets/'
   if mark not in f['path']:continue
   t=q/'ui-assets'/f['path'].split(mark,1)[1];t.parent.mkdir(parents=True,exist_ok=True);o=old['objects'][f['sha256']];t.write_bytes(gzip.decompress((r/'preserved/owned-world-army-dismiss-r1'/o['file']).read_bytes()));assert sha(t)==f['sha256']
  write(q/'baseline.json',deps);return
 assert deps==read(q/'baseline.json')
 if a.action=='evidence':
  d=read(q/'oracle-r2.json');assert d['status']=='original-cpu-slices-complete';assert [v['empty_flag']for v in d['presence']]==[1,0,0]and len(d['losses'])==20
  for v in d['losses']:assert v['divisor']==v['controlled_rand']//2730+2 and v['loss']==v['gold_before']//v['divisor']and v['gold_after']==v['gold_before']-v['loss']
  ida=read(q/'ida/ida-world-army-r1.json');raw=(q/'inputs/PAM.AY').read_bytes();assert sha(q/'inputs/PAM.AY')==d['source_sha256']==ida['source_sha256'];header=struct.unpack_from('<H',raw,8)[0]*16;relocs=[]
  for i in range(struct.unpack_from('<H',raw,6)[0]):off,seg=struct.unpack_from('<HH',raw,struct.unpack_from('<H',raw,24)[0]+i*4);relocs.append(header+seg*16+off)
  f=next(v for v in ida['functions']if v['start']==0x1151c);assert [v['source']for v in f['xrefs']]==[0x10bd0]
  for line in f['lines']:
   pos=line['file_offset'];want=bytes.fromhex(line['bytes']);b=bytearray(raw[pos:pos+len(want)]);assert pos==line['ida_linear']-0x10000+header
   for loc in relocs:
    if pos<=loc and loc+2<=pos+len(want):struct.pack_into('<H',b,loc-pos,(struct.unpack_from('<H',b,loc-pos)[0]+0x1000)&65535)
   assert bytes(b)==want
  write(a.out,dict(status='passed-original-presence-evidence',source_sha256=d['source_sha256'],oracle_sha256=sha(q/'oracle-r2.json'),ida_export_sha256=sha(q/'ida/ida-world-army-r1.json'),ida_lines=len(f['lines']),presence_cases=3,loss_cases=20,address_spaces=ida['address_space'],formal_changed=False));return
 if a.action=='freeze':
  for n in NEW:shutil.copyfile(r/'tools'/n,q/'go-src/tools'/n)
  return
 if a.action=='audit':
  from PIL import Image
  assert read(q/'evidence-r2.json')['status']=='passed-original-presence-evidence'
  index=read(r/'docs/spec/world-army-consumers-r1.json');f=next(v for v in index['functions']if v['original_name']=='sub_1151C');resolution=f['resolution'];assert f['level']=='proven'and not f['production_integrated']and f['runtime']=='0110:151C'
  assert resolution['required_correction']in(r/resolution['older_spec']).read_text()and(r/resolution['unaffected_spec']).exists()and'0110:1650'in resolution['scope']
  log=(q/'go-test-r1.log').read_text();assert'PASS'in log and'FAIL'not in log and'SKIP'not in log
  for n in ['go-vet-r1.log','build-r1.log','xcheck-build-r1.log','oracle-r2.log']:assert(q/n).stat().st_size==0
  for n in NEW+COMMON:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n)
  gui=read(q/'gui-r1/receipt.json');assert gui['status']=='passed-actual-army-presence'and gui['cold_equal']and gui['present_pair_unchanged']
  events=gui['events'];assert len(events)==2 and events[0]['total']==0 and not events[0]['has_army'];loss=events[1];assert 2<=loss['divisor']<=14 and loss['loss']==loss['before']//loss['divisor']and loss['after']==loss['before']-loss['loss']
  expected=json.loads(json.dumps(gui['initial']));expected['revision']+=1;expected['army']['gold']-=loss['loss'];assert expected==gui['after']==read(q/'session-empty/gamedata.ay.army.json')['world']
  initial_native=m.stored(r,'owned-world-army-dismiss-r1','/session-r1/gamedata.ay');native=(q/'session-empty/gamedata.ay').read_bytes();side=read(q/'session-empty/gamedata.ay.army.json');assert len(native)==2987 and native[12:]==initial_native[12:]and side['original_sha256']==sha(q/'session-empty/gamedata.ay')
  vals=[(struct.unpack_from('<H',native,i*2)[0]-i*2-3)&65535 for i in range(6)];w=gui['after'];assert vals==[w['progress']['rank'],w['progress']['merit'],w['progress']['legacy_04f6'],w['army']['gold'],w['army']['leadership'],w['progress']['legacy_04fc']]
  checked=[]
  for s in gui['screens']:
   folder=q/'gui-r1'/s['phase'];im=Image.open(folder/s['canvas']);screen=Image.open(folder/s['screen']);assert im.size==screen.size==(1920,1200)and im.convert('RGB').tobytes()==screen.convert('RGB').tobytes()
   st=read(folder/s['metadata']);assert st['native_rows_hex']==gui['native_rows_hex']and st['presence_native_reads']==0 and hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()==st['canvas_sha256']==st['presented_sha256']
   if s['phase']=='present':assert st['presence_has_army']and st['presence_prompt']and st['presence_debits']==0
   else:assert not any(v['count']for v in st['world']['army']['slots'])and st['world']['army']['gold']==loss['after']
   checked.append(dict(phase=s['phase'],sha256=sha(folder/s['canvas'])))
  final=read(q/'gui-r1/empty/ui-final.json');assert final['presence_completed']==1 and final['presence_debits']==1 and final['presence_checks']==1
  write(a.out,dict(status='passed-isolated-army-presence-and-loss',dependencies=deps,source_tools={n:sha(r/'tools'/n)for n in NEW+COMMON},original_evidence=read(q/'evidence-r2.json'),original_presence_cases=3,original_loss_cases=20,go_parent_tests=6,rejection_cases=11,gui_screens=checked,native_rows_hex=gui['native_rows_hex'],loss=loss,native_save_sha256=sha(q/'session-empty/gamedata.ay'),cold_equal=True,original_other_2975_bytes_unchanged=True,formal_changed=False,full_expanded_battle=False,limits=gui['limits']));return
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for f in sorted(q.rglob('*')):
  if not f.is_file():continue
  assert not f.is_symlink()and f.stat().st_uid==1000;b=f.read_bytes();h=hashlib.sha256(b).hexdigest();obj=folder/(h+'.gz')
  if h not in objects:obj.write_bytes(gzip.compress(b,compresslevel=6,mtime=0));objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(b),mode=f.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Local original state and graphics; full objects excluded from Git.'))
if __name__=='__main__':main()
