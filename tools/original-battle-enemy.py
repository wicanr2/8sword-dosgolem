#!/usr/bin/env python3
"""Spec030 original enemy-special Go data and permanent evidence."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,sys
from pathlib import Path
sys.dont_write_bytecode=True
REL='workplace/probe-20261023/graphics-first/battle-r1/original-battle-enemy-r1';BATCH='original-battle-enemy-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def amount(selector,kind,before):
 if selector in [0,1]:return 2 if kind==12 else 5
 if selector==2:return 6 if kind==12 else 15
 if selector==3:return before
 if selector==5:return before//(3 if kind==12 else 2)+1
 if selector==7:return before if before<50 else before*6//(20 if kind==12 else 10)+1
 raise AssertionError(selector)
def clone(kind,before):
 factor=20 if before<50 else 14 if before<100 else 13 if before<200 else 12 if before<300 else 11 if before<400 else 10
 scaled=before*factor//(20 if kind==12 else 10)
 return scaled,max(before,scaled)
def audit(r,q,out):
 import base64,struct
 from PIL import Image
 manifest=read(q/'source-manifest.json')
 for n,d in manifest.items():assert sha(r/n)==sha(q/'source'/n)==d,n
 # Prior special-return samples precede the separately verified rear-target
 # motion correction. Accept only that exact edit; all other production
 # sources, including the enemy controller, must have identical hashes.
 motion_path='internal/ownedworld/original_battle_rounds.go';current=(r/motion_path).read_text()
 start=current.index('// Original rear-target cases in sub_21EA0/sub_22DBC');end=current.index('// Original 22F55/23607',start);prior_motion=current[:start]+current[end:]
 new='if !direct {\n\t\tvar err error\n\t\tr.MotionAfter[side], err = roundMotionPlanForTarget(r.Rows[side], r.Slots[side], int(ss), int(ts))'
 old='if !direct {\n\t\tfrom, to := int(ss), int(ts%3)\n\t\tvar err error\n\t\tr.MotionAfter[side], err = roundMotionPlan(r.Rows[side], r.Slots[side], from, to)'
 assert prior_motion.count(new)==1;prior_motion=prior_motion.replace(new,old);prior_motion_sha=hashlib.sha256(prior_motion.encode()).hexdigest()
 for folder in ['initial-input-failed','fixture-boundary-failed','first-passing-cohort','motion-world-failed']:
  prior=read(q/folder/'source-manifest.json')
  for n,d in prior.items():
   if not n.endswith('_test.go'):assert (prior_motion_sha if n==motion_path else manifest[n])==d,(folder,n)
 pam=(q/'inputs/PAM.AY').read_bytes();assert sha(q/'inputs/PAM.AY')=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
 image=bytearray(pam);word=lambda at:int.from_bytes(pam[at:at+2],'little');header=word(8)*16
 for i in range(word(6)):
  at=word(24)+i*4;off=header+word(at+2)*16+word(at);image[off:off+2]=((word(off)+0x1000)&65535).to_bytes(2,'little')
 lines=functions=0
 for name,receipt in [('ida-spells-r4.json','provenance.json'),('ida-projection.json','projection-provenance.json'),('ida-rounds.json','rounds-provenance.json')]:
  f=q/'evidence'/name;assert sha(f)==read(q/'evidence'/receipt)['sha256'];ida=read(f);assert ida['source_sha256']==sha(q/'inputs/PAM.AY')and ida['database_sha256']=='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac'
  functions+=len(ida['functions'])
  for fun in ida['functions']:
   for line in fun['lines']:
    raw=bytes.fromhex(line['bytes']);off=line.get('original_file_offset',line.get('file_offset'));assert bytes(image[off:off+len(raw)])==raw,(name,fun['name'],line['ida_linear']);lines+=1
 model=read(q/'enemy-models.json');assert len(model['counter_controls'])==46 and len(model['amount_models'])==60 and model['empty_shifted_target_amount']==1 and model['amount_refusals']==6 and model['counter_refusals']==8
 for item in model['counter_controls']:
  ip,a=item['ip'],item['before'];result=1 if ip==0x2184 else a+1 if ip==0xfa9 else a-1 if ip in [0x1699,0x189d]else a;flags=0xad7
  if ip!=0x2184:
   flags&=~0x8d5
   if result==0:flags|=0x40
   if result&32768:flags|=0x80
   if (result&255).bit_count()%2==0:flags|=4
   if ip==0xfa9:
    flags|=1
    if result&15==0:flags|=0x10
    if a==32767:flags|=0x800
   elif ip in [0x1699,0x189d]:
    flags|=1
    if a&15==0:flags|=0x10
    if a==32768:flags|=0x800
  assert item['after']==(a if ip in [0x165b,0x187c]else result)and item['flags']==flags,item
 for item in model['amount_models']:
  loss=amount(item['selector'],item['kind'],item['before']);assert item['amount']==loss and item['after']==max(0,item['before']-loss)
 guards=read(q/'enemy-guards.json');assert guards['impact_refusals']==8 and guards['entry_refusals']==11 and guards['shifted_alias_refusals']==1 and guards['state_unchanged'] and [x['alias']for x in guards['shifted_alias_controls']]==list(range(12))
 motion=read(q/'enemy-motion-research.json');assert len(motion['rows'])==72 and not motion['complete_battle']
 for v in motion['rows']:
  source,target=v['from'],v['target'];dest=target if target<3 else [[0,1,0],[1,1,1],[1,2,2]][source][target-3];expected=list(range(6));empty=v['empty_destination']and target%3!=source and dest==target%3
  if empty:expected[source],expected[dest]=expected[dest],expected[source]
  elif source<dest:expected[source:dest+1]=expected[source+1:dest+1]+[source]
  elif source>dest:expected[dest:source+1]=[source]+expected[dest:source]
  assert v['after']==v['go_after']==expected,(v,expected)
 def record(rec,rows=None):
  selector=rec['Selector'];assert selector in range(8)and rec['Kind']in [10,12]
  if selector==3:assert rec['GateSeen']and rec['Gate']<50
  if selector==4:assert rec['FreezeWrites']==6 and sum(rec['AfterCounters'])-sum(rec['BeforeCounters'])==6
  else:assert rec['BeforeCounters']==rec['AfterCounters']and rec['FreezeWrites']==0
  if selector==6:
   c=rec['Clone'];scaled,after=clone(c['CasterKind'],c['Before']);assert(c['Scaled'],c['After'])==(scaled,after)and c['Updates']==1 and (c['Planned']or[])==(c['Display']or[])==list(range(c['Before'],scaled+1))
   if rows is not None:assert rows[1][c['Raw']]['count']==after
  else:assert rec['Clone']is None
  for e in rec['Effects']or[]:
   loss=amount(selector,rec['Kind'],e['Before']);after=max(0,e['Before']-loss);assert e['selector']==selector and e['Amount']==loss and e['After']==after and e['Updates']==1
   if selector==7:assert not e['Display']and not e['Planned']
   else:
    first=min(e['Before'],5)if after==0 else after+5 if loss>=5 else e['Before'];assert(e['Planned']or[])==(e['Display']or[])==list(range(first,after-1,-1))
   if rows is not None:assert rows[0][e['Raw']]['count']==after
 rows=[]
 for name in [f'selector-{i}-hd'for i in range(8)]+['native-mode','kind12','gate0','natural-dispatch','clone12']:
  folders=[q/'enemy-r1'/f'{name}-mode-{mode}'for mode in [0,1]];a,b=[read(p/'receipt.json')for p in folders]
  for key in ['selector','units_hex','hp_hex','counters_hex','seed','frame_sha256']:assert a[key]==b[key],(name,key)
  assert b['requested_selector']==-1 or b['selector']==b['requested_selector']
  frames=[Image.open(p/'frame.png').convert('RGBA').tobytes()for p in folders];assert frames[0]==frames[1]and hashlib.sha256(frames[0]).hexdigest()==b['frame_sha256']
  assert b['counters']==list(struct.unpack('<6H',bytes.fromhex(b['counters_hex'])));rec=b['record'];assert rec['Selector']==b['selector']and rec['SeedAfter']==b['seed'];record(rec,b['rows'])
  words=struct.unpack('<24H',bytes.fromhex(b['units_hex']))
  for side in [0,1]:
   for raw,item in enumerate(b['rows'][side]):assert words[(side*6+raw)*2+1]==item['count']
  rows.append(dict(name=name,selector=b['selector'],effects=len(rec['Effects']or[]),frame_sha256=b['frame_sha256'],seed=b['seed']))
 folder=q/'enemy-world-r1';w=read(folder/'receipt.json');enemy=read(folder/'enemy.json');cold=read(folder/'process-cold/receipt.json');assert w['result']=='win'and w['ordinary_actions']>=2 and w['checkpoint_saves']==1 and enemy['controlled_enemy_first']and enemy['forced_first_selector']==1
 assert enemy['reads']>0 and enemy['consumes']>0 and enemy['player_counter_consumes']>0
 for rec in enemy['records']:record(rec)
 effects=enemy['records'][0]['Effects'];assert len(effects)==3
 for raw in [1,2]:
  e=next(e for e in effects if e['Raw']==raw);assert e['Before']==2 and e['After']==0 and e['Updates']==1
 for key in ['world_sha256','resources','location','charges_hex']:assert w[key]==cold[key],key
 assert cold['separate_process']and not cold['snapshot_loaded'];native=(folder/'scratch/gamedata.ay').read_bytes();saved=read(folder/'session/gamedata.ay.army.json');assert saved['original_sha256']==hashlib.sha256(native).hexdigest()and saved['world']['army']['slots']==w['remaining']
 keys=['rank','merit','monthly_pay','gold','leadership','spell_power'];assert len(native)==2987 and [(struct.unpack_from('<H',native,i*2)[0]-i*2-3)&65535 for i in range(6)]==[w['resources'][k]for k in keys]
 assert len(saved['native_files'])==9
 for file,encoded in saved['native_files'].items():assert base64.b64decode(encoded)==(folder/'scratch'/file).read_bytes()
 for log in ['tests-selector0-r3.log','tests-batch1-r1.log','tests-selectors1-4-r1.log','tests-selectors5-7-r1.log','tests-extras-r1.log','tests-world-r1.log','tests-cold-r1.log','regression-r2.log','tests-motion-research-r4.log']:assert(q/log).read_text().rstrip().endswith('PASS'),log
 expanded=read(q/'enemy-expanded-r1/receipt.json');record(expanded['record'],expanded['rows']);assert expanded['native_player_hex']=='00'*24 and expanded['original_shadow_unchanged']and expanded['record']['Selector']==1 and len(expanded['record']['Effects'])==2
 write(out,dict(status='passed-original-battle-enemy-audit',source_files=len(manifest),ida_functions=functions,ida_lines=lines,original_pairs=len(rows),counter_instruction_controls=46,shifted_alias_instruction_controls=12,isolated_motion_branch_controls=72,prior_cohort_motion_source_sha256=prior_motion_sha,amount_models=60,refusals=34,frames_counts_HP_counters_seed_equal=True,held_retries=5,rows=rows,all_expanded_army_native_projection_zero=True,world=dict(remaining=w['remaining'],resources=w['resources'],ordinary_actions=w['ordinary_actions'],enemy_actions=len(enemy['records']),new_ID_targets_reduced=2),actual_F7_saves=1,separate_process_Continue=1,initial_seed=0x12345678,seed_method='setupCold fixes DS:81BC/81BE before encounter; selector fixtures replace BP-4 after original RNG, without reseeding or rerolling.',formal_runtime_unchanged=True,general_player_entry_disabled=True,limits=['Explicit enemy roster, first-side and selector fixtures; not natural enemy acquisition.','Selector7 is not selected by observed original remainder340 mapping; controlled dispatch only.','Original intermediate arithmetic and animation retained; Go owns final counts/counters.','Special-return pairs precede the exact rear-target helper edit; 72 isolated original branches and a final-source world chain verify that edit.','Engine frames; no new X11 acceptance.','Guard/boss bridges, rules/AI integration, dynamic poses, wide animation, mid-battle save and general startup remain open.']))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['freeze','audit','publish','archive','verify'])
 for n in['project','archive','out']:p.add_argument('--'+n,type=Path)
 a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   o=d['objects'][f['sha256']];stored=(a.archive/BATCH/o['file']).read_bytes();assert hashlib.sha256(stored).hexdigest()==o['stored_sha256'];raw=gzip.decompress(stored);assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-original-battle-enemy',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL;s=importlib.util.spec_from_file_location('helper',r/'tools/prepare-owned-army-ui.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h);deps=h.dependencies(r);assert deps==read(q/'baseline.json')
 if a.action=='freeze':
  names=set(read(r/'preserved/owned-player-source-manifest-r1.json'))|{str(p.relative_to(r))for p in(r/'internal/ownedworld').glob('*.go')}
  for n in sorted(names):dst=q/'source'/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,dst)
  (q/'source-manifest.json').write_text(json.dumps({n:sha(q/'source'/n)for n in sorted(names)},indent=2)+'\n');shutil.copyfile(r/'tools/original-battle-enemy.py',q/'original-battle-enemy.py');return
 if a.action=='audit':audit(r,q,a.out);return
 if a.action=='publish':
  import io
  from PIL import Image,ImageDraw,ImageFont
  assert read(r/'preserved/original-battle-enemy-audit-r1.json')['status']=='passed-original-battle-enemy-audit'
  idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),28,index=3)
  canvas=Image.new('RGB',(1920,550),'#11251f');draw=ImageDraw.Draw(canvas);sources=[]
  for i,(path,label)in enumerate([('enemy-r1/native-mode-mode-1/frame.png','原版模式：敵方火焰結算'),('enemy-r1/selector-1-hd-mode-1/frame.png','HD模式：敵方多目標特殊'),('enemy-world-r1/map.png','新增兵受術後取勝、F7保存')]):
   file=q/path;canvas.paste(Image.open(file).resize((640,400),Image.Resampling.NEAREST),(i*640,60));draw.text((i*640+14,10),label,font=font,fill='#fff1b5');sources.append(dict(path=str(file.relative_to(r)),sha256=sha(file)))
  draw.text((18,480),'明示敵軍／分派配置；特殊完成幀。原版戰場保留，Go處理兵力與行動計數。',font=font.font_variant(size=26),fill='#fff1b5')
  file=a.out/'original-battle-go-enemy-r1.png';assert not file.exists();canvas.save(file);write(a.out/'original-battle-go-enemy-r1.json',dict(schema=1,sha256=sha(file),inputs=sources,actual_window=False,animation_midframe=False,general_player_entry=False,scope='Controlled enemy fixtures; original/HD completion frames and postbattle map.'));return
 if a.action=='archive':
  assert read(r/'preserved/original-battle-enemy-audit-r1.json')['status']=='passed-original-battle-enemy-audit'
  folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
  for f in sorted(q.rglob('*')):
   if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
   assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();digest=hashlib.sha256(raw).hexdigest();obj=folder/(digest+'.gz')
   if digest not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[digest]=dict(file=obj.name,stored_sha256=sha(obj))
   files.append(dict(path=str(f.relative_to(r)),bytes=len(raw),sha256=digest,mode=f.stat().st_mode&0o777))
  write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Original files, full frames/states and binaries local only; general startup disabled.'))
if __name__=='__main__':main()
