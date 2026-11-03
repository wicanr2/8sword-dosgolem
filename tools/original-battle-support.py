#!/usr/bin/env python3
"""Spec030 original freeze/clone Go state, bounded samples and permanent evidence."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,sys
from pathlib import Path
sys.dont_write_bytecode=True
REL='workplace/probe-20261023/graphics-first/battle-r1/original-battle-support-r1'
BATCH='original-battle-support-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def clone_plan(kind,count):
 factor=20 if count<50 else 14 if count<100 else 13 if count<200 else 12 if count<300 else 11 if count<400 else 10
 scaled=count*factor//(20 if kind==12 else 10)
 return scaled,max(count,scaled),factor
def audit(r,q,out):
 import base64,struct
 from PIL import Image
 manifest=read(q/'source-manifest.json')
 for n,d in manifest.items():assert sha(r/n)==sha(q/'source'/n)==d,n
 for source in[q/'first-cohort-tests/source-manifest.json',q/'extra-turn-input-failed/source-manifest.json']:
  prior=read(source)
  for n,d in prior.items():
   if not n.endswith('_test.go'):assert manifest[n]==d,(source.name,n)
 pam=(q/'inputs/PAM.AY').read_bytes();image=bytearray(pam);word=lambda at:int.from_bytes(pam[at:at+2],'little');header=word(8)*16
 assert sha(q/'inputs/PAM.AY')=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
 for i in range(word(6)):
  at=word(24)+i*4;off=header+word(at+2)*16+word(at);image[off:off+2]=((word(off)+0x1000)&65535).to_bytes(2,'little')
 lines=functions=0
 for name,receipt in[('ida-spells-r4.json','provenance.json'),('ida-projection.json','projection-provenance.json')]:
  f=q/'evidence'/name;assert sha(f)==read(q/'evidence'/receipt)['sha256'];ida=read(f);assert ida['source_sha256']==sha(q/'inputs/PAM.AY')and ida['database_sha256']=='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac'
  functions+=len(ida['functions'])
  for fun in ida['functions']:
   for l in fun['lines']:
    raw=bytes.fromhex(l['bytes']);off=l.get('original_file_offset',l.get('file_offset'));assert bytes(image[off:off+len(raw)])==raw,(fun['name'],l['ida_linear']);lines+=1
 model=read(q/'support-models.json');assert len(model['counter_controls'])==46 and len(model['clone_models'])==24 and model['clone_refusals']==4 and model['counter_refusals']==8
 for item in model['counter_controls']:
  ip,a=item['ip'],item['before'];result=1 if ip==0x2134 else a+1 if ip==0x771 else a-1 if ip in[0x1a25,0x1c7f]else a
  flags=0xad7
  if ip!=0x2134:
   flags&=~0x8d5
   if result==0:flags|=0x40
   if result&32768:flags|=0x80
   if (result&255).bit_count()%2==0:flags|=4
   if ip==0x771:
    flags|=1
    if result&15==0:flags|=0x10
    if a==32767:flags|=0x800
   elif ip in[0x1a25,0x1c7f]:
    flags|=1
    if a&15==0:flags|=0x10
    if a==32768:flags|=0x800
  assert item['after']==(a if ip in[0x1a11,0x1c5e]else result)and item['flags']==flags,item
 for item in model['clone_models']:assert (item['scaled'],item['after'],item['factor'])==clone_plan(item['kind'],item['count'])
 assert read(q/'support-growth.json')==dict(valid=1,refusals=6,native_and_owned_returns=True)
 assert read(q/'support-clone-guards.json')==dict(refusals=8,state_unchanged=True)
 rows=[]
 for name in['freeze-hd','clone-hd','clone-no-growth-hd','clone-native','clone-space','clone-skip-hd']:
  folders=[q/'support-r1'/f'{name}-mode-{mode}'for mode in[0,1]];a,b=[read(p/'receipt.json')for p in folders]
  for key in['units_hex','hp_hex','counters_hex','charges_hex','seed','frame_sha256']:assert a[key]==b[key],(name,key)
  frames=[Image.open(p/'frame.png').convert('RGBA').tobytes()for p in folders];assert frames[0]==frames[1]and hashlib.sha256(frames[0]).hexdigest()==a['frame_sha256']
  charges=list(struct.unpack('<8H',bytes.fromhex(b['charges_hex'])));expected=[3]*8
  if name!='clone-space':expected[b['selector']]-=1
  assert charges==expected and b['counters']==list(struct.unpack('<6H',bytes.fromhex(b['counters_hex'])))and len(b['records'])==1
  record=b['records'][0];growth=[0]*6
  if name=='freeze-hd':assert record['FreezeWrites']==6 and sum(record['After'])-sum(record['Before'])==6 and record['Clone']is None
  else:
   assert record['After']==record['Before']and record['FreezeWrites']==0;c=record['Clone']
   if name=='clone-space':assert c is None
   else:
    scaled,after,factor=clone_plan(c['CasterKind'],c['Before']);assert(c['Scaled'],c['After'])==(scaled,after)and c['Updates']==1
    expected=list(range(c['Before'],scaled+1));assert(c['Planned']or[])==(c['Display']or[])==expected
    growth[c['Raw']]=after-c['Before'];assert b['rows'][0][c['Raw']]['count']==after
    if name=='clone-skip-hd':assert c['Before']==50 and c['Scaled']==35 and not expected
  assert b['growth']==growth and b['counter_reads']>0 and b['counter_consumes']>0
  words=struct.unpack('<24H',bytes.fromhex(b['units_hex']))
  for side in[0,1]:
   for raw,item in enumerate(b['rows'][side]):assert words[(side*6+raw)*2+1]==item['count']
  rows.append(dict(name=name,growth=growth,charges=charges,frame_sha256=b['frame_sha256']))
 worlds=[]
 assert '--- PASS: TestOriginalSupportWorld/clone'in(q/'extra-turn-input-failed/tests-world-r1.log').read_text()
 keys=['rank','merit','monthly_pay','gold','leadership','spell_power']
 for name,selector in[('clone-world-r1',6),('freeze-world-r1',4)]:
  folder=q/name;w=read(folder/'receipt.json');s=read(folder/'support.json');cold=read(folder/'process-cold/receipt.json')
  assert w['result']=='win'and w['ordinary_actions']>=2 and w['checkpoint_saves']==1 and s['records'][0]['Selector']==selector
  for key in['world_sha256','resources','location','charges_hex']:assert w[key]==cold[key],(name,key)
  assert cold['separate_process']and not cold['snapshot_loaded']and s['consumes']>0
  native=(folder/'scratch/gamedata.ay').read_bytes();saved=read(folder/'session/gamedata.ay.army.json');assert saved['original_sha256']==hashlib.sha256(native).hexdigest()and saved['world']['army']['slots']==w['remaining']
  assert len(native)==2987 and [(struct.unpack_from('<H',native,i*2)[0]-i*2-3)&65535 for i in range(6)]==[w['resources'][k]for k in keys]
  assert len(saved['native_files'])==9
  for file,encoded in saved['native_files'].items():assert base64.b64decode(encoded)==(folder/'scratch'/file).read_bytes()
  if selector==6:assert s['growth'][0]==40 and w['remaining'][0]['count']>w['initial'][0]['count']
  else:assert s['records'][0]['FreezeWrites']==6
  worlds.append(dict(name=name,remaining=w['remaining'],resources=w['resources'],ordinary_actions=w['ordinary_actions'],charges_hex=w['charges_hex']))
 for log in['tests-models-r2.log','tests-freeze-r1.log','tests-clones-r1.log','tests-skip-r1.log','tests-freeze-world-r2.log','tests-cold-r1.log','regression-r1.log','tests-fireball-regression-r1.log']:assert(q/log).read_text().rstrip().endswith('PASS'),log
 write(out,dict(status='passed-original-battle-support-audit',source_files=len(manifest),ida_functions=functions,ida_lines=lines,original_pairs=6,counter_instruction_controls=46,clone_models=24,counter_refusals=8,clone_write_refusals=8,growth_refusals=6,clone_bound_refusals=4,frames_counts_HP_counters_charges_seed_equal=True,held_retries=5,rows=rows,worlds=worlds,actual_F7_saves=2,separate_process_Continue=2,formal_runtime_unchanged=True,general_player_entry_disabled=True,limits=['Explicit caster, learned and charge fixtures; not natural acquisition.','Native clone targets only; original intermediate clone arithmetic retained as a compatibility check.','Post-clone over-leadership world path remains unsupported; Store bound unchanged.','Enemy specials, guard/boss bridges, rules/AI integration, dynamic poses, wide animation, mid-battle save and general startup remain open.','Engine frames; no new X11 acceptance.']))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['freeze','audit','publish','archive','verify'])
 for n in['project','archive','out']:p.add_argument('--'+n,type=Path)
 a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   o=d['objects'][f['sha256']];stored=(a.archive/BATCH/o['file']).read_bytes();assert hashlib.sha256(stored).hexdigest()==o['stored_sha256'];raw=gzip.decompress(stored);assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-original-battle-support',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL;s=importlib.util.spec_from_file_location('helper',r/'tools/prepare-owned-army-ui.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h);deps=h.dependencies(r);assert deps==read(q/'baseline.json')
 if a.action=='freeze':
  names=set(read(r/'preserved/owned-player-source-manifest-r1.json'))|{str(p.relative_to(r))for p in(r/'internal/ownedworld').glob('*.go')}
  for n in sorted(names):dst=q/'source'/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,dst)
  (q/'source-manifest.json').write_text(json.dumps({n:sha(q/'source'/n)for n in sorted(names)},indent=2)+'\n');shutil.copyfile(r/'tools/original-battle-support.py',q/'original-battle-support.py');return
 if a.action=='audit':audit(r,q,a.out);return
 if a.action=='publish':
  import io
  from PIL import Image,ImageDraw,ImageFont
  assert read(r/'preserved/original-battle-support-audit-r1.json')['status']=='passed-original-battle-support-audit'
  idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),28,index=3)
  canvas=Image.new('RGB',(1920,550),'#11251f');draw=ImageDraw.Draw(canvas);sources=[]
  for i,(path,label)in enumerate([('support-r1/clone-native-mode-1/frame.png','原版模式：複製30 → 60'),('support-r1/clone-hd-mode-1/frame.png','HD模式：相同Go兵力接管'),('clone-world-r1/map.png','複製後勝利：65民兵保存')]):
   file=q/path;canvas.paste(Image.open(file).resize((640,400),Image.Resampling.NEAREST),(i*640,60));draw.text((i*640+14,10),label,font=font,fill='#fff1b5');sources.append(dict(path=str(file.relative_to(r)),sha256=sha(file)))
  draw.text((18,480),'明示學習／次數配置；施法完成幀。原選單保留；F7與獨立程序Continue已驗。',font=font.font_variant(size=26),fill='#fff1b5')
  file=a.out/'original-battle-go-support-r1.png';assert not file.exists();canvas.save(file);write(a.out/'original-battle-go-support-r1.json',dict(schema=1,sha256=sha(file),inputs=sources,actual_window=False,spell_animation_midframe=False,general_player_entry=False,scope='Controlled clone fixtures; original/HD completion frames and postbattle map.'));return
 if a.action=='archive':
  assert read(r/'preserved/original-battle-support-audit-r1.json')['status']=='passed-original-battle-support-audit'
  folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
  for f in sorted(q.rglob('*')):
   if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
   assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();digest=hashlib.sha256(raw).hexdigest();obj=folder/(digest+'.gz')
   if digest not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[digest]=dict(file=obj.name,stored_sha256=sha(obj))
   files.append(dict(path=str(f.relative_to(r)),bytes=len(raw),sha256=digest,mode=f.stat().st_mode&0o777))
  write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Original files, complete frames/states and binaries local only; general startup disabled.'))
if __name__=='__main__':main()
