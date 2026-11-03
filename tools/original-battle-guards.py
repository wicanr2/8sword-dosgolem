#!/usr/bin/env python3
"""Spec030 original guard/boss battlefield bridge and permanent evidence."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,sys
from pathlib import Path
sys.dont_write_bytecode=True
REL='workplace/probe-20261023/graphics-first/battle-r1/original-battle-guards-r1';BATCH='original-battle-guards-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def audit(r,q,out):
 import base64,struct
 from PIL import Image
 manifest=read(q/'source-manifest.json')
 for n,d in manifest.items():assert sha(r/n)==sha(q/'source'/n)==d,n
 for n,d in read(q/'first-passing-cohort/source-manifest.json').items():
  if not n.endswith('_test.go'):assert manifest[n]==d,n
 pam=(q/'inputs/PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
 image=bytearray(pam);word=lambda at:int.from_bytes(pam[at:at+2],'little');header=word(8)*16
 for i in range(word(6)):
  at=word(24)+i*4;off=header+word(at+2)*16+word(at);image[off:off+2]=((word(off)+0x1000)&65535).to_bytes(2,'little')
 for n,d in read(q/'evidence/provenance.json').items():assert sha(q/'evidence'/n)==d,n
 lines=functions=0
 for name in ['ida-guard-world.json','ida-guard-rewards.json','ida-save.json','ida-original-guards-r1.json','ida-original-guards-r2.json']:
  report=read(q/'evidence'/name);assert report.get('source_sha256',report.get('input_sha256'))==sha(q/'inputs/PAM.AY')and report['database_sha256']=='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac'
  functions+=len(report['functions'])
  for f in report['functions']:
   for line in f['lines']:
    raw=bytes.fromhex(line['bytes']);off=line.get('original_file_offset',line.get('file_offset'));assert bytes(image[off:off+len(raw)])==raw,(name,f['name'],line['ida_linear']);lines+=1
 ida=read(q/'evidence/ida-original-guards-r2.json');assert ida['uid']==1000 and ida['function_count']==521 and ida['exporter_sha256']==sha(r/'tools/export-original-battle-guards-ida.py')
 assert ida['index_sha256']==sha(q/'evidence/world-army-index-at-export.json')
 for f in ida['functions']:assert f['indexed_semantic']['level']and 'original_file_offset'in f['lines'][0]and 'indexed_operands'in f
 cleanup=next(f for f in ida['functions']if f['name']=='sub_132B4');assert cleanup['end']-cleanup['start']==43
 models=read(q/'guard-record-models.json');assert len(models['models'])==16 and models['record_refusals']==7 and models['interrupted_commit_recovered']and models['recovery_idempotent']and models['schema_unchanged']
 for v in models['models']:
  bases=[0x365e,0x3706,0x3766,0x37c6,0x3826,0x3886,0x38e6,0x3946];boss=[1,3,3,3,2,3,2,10];assert v['index']==(boss[v['region']]if v['boss']else 0)and v['npc_save_offset']==1508+bases[v['region']]-0x365e+v['index']*24 and v['cleared']and v['source_unchanged']
  if v['boss']:assert v['flags'][v['region']]
 assert read(q/'guard-reward-guards.json')==dict(refusals=12,state_unchanged=True)
 assert read(q/'guard-committed-retries.json')==dict(retries=5,RAM_cycles_registers_flags_resources_unchanged=True,no_second_store_required=True)
 pairs=[]
 for name in ['native-win','hd-retreat']:
  folders=[q/'guards-r1'/f'{name}-mode-{mode}'for mode in [0,1]];a,b=[read(p/'receipt.json')for p in folders]
  for key in ['resources','NPC_hex','swords_hex','seed','frame_sha256']:assert a[key]==b[key],(name,key)
  images=[Image.open(p/'map.png').convert('RGBA').tobytes()for p in folders];assert images[0]==images[1]and hashlib.sha256(images[0]).hexdigest()==b['frame_sha256']
  pairs.append(dict(name=name,frame_sha256=b['frame_sha256'],seed=b['seed'],resources=b['resources']))
 base=(q/'guards-r1/native-win-mode-0/session/gamedata.ay').read_bytes()
 decode=lambda raw,at:(struct.unpack_from('<H',raw,at)[0]-at-3)&65535
 world_names=['rank','merit','monthly_pay','gold','leadership','spell_power'];cases=[]
 for name in ['native-win','hd-retreat','hd-mixed-win','hd-boss-win']:
  folder=q/'guards-r1'/f'{name}-mode-1';v=read(folder/'receipt.json');cold=read(folder/'process-cold/receipt.json');saved=read(folder/'session/gamedata.ay.army.json');native=(folder/'scratch/gamedata.ay').read_bytes();ctx=v['context'];region,index=ctx['region'],ctx['index'];assert region==0 and index==(1 if name=='hd-boss-win'else 0)
  result='retreat'if name=='hd-retreat'else 'win';assert v['result']==result and v['native_guard_unmodified']and v['checkpoint_saves']==1 and v['pre_F7_cold_records_restored']
  bound=next(e for e in v['events']if e['event']=='bound');initial=[]
  for raw in range(6):
   at=1508+index*24+raw*4;kind,count=decode(base,at),decode(base,at+2);initial.append(dict(unit=f'native:{kind:02d}'if kind else '',count=count))
  assert bound['enemy']==initial,'guard fixture changed original roster'
  assert v['ordinary_actions']>=1 and v['resources'][0:2]==[1,10000]and v['resources'][4]==30000
  if result=='win':assert v['resources'][2:4]==[120,500]
  else:assert v['resources'][2]==100 and 0<=v['resources'][3]<500
  assert len([e for e in v['events']if e['event']=='committed'])==1
  assert len([e for e in v['events']if e['event']=='reward'and e['ip']==0x1b7b])==(result=='win')
  assert len([e for e in v['events']if e['event']=='reward'and e['ip']==0x1c7f])==(name=='hd-boss-win')
  assert saved['original_sha256']==hashlib.sha256(native).hexdigest()and len(native)==2987 and saved['world']['army']['slots']==v['remaining']
  assert hashlib.sha256(json.dumps(saved['world'],ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==v['world_sha256']
  prior_world=json.loads(json.dumps(saved['world']));prior_world['revision']-=1
  assert hashlib.sha256(json.dumps(prior_world,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==v['world_before_f7']
  assert v['resources']==[decode(native,i*2)for i in range(6)]and v['saved_resources']==dict(zip(world_names,v['resources']))
  assert native[12:36]==base[12:36],'native player shadow changed'
  npc=bytes.fromhex(v['NPC_hex']);flags=bytes.fromhex(v['swords_hex']);assert len(npc)==1008 and len(flags)==16
  native_npc=b''.join(decode(native,1508+i*2).to_bytes(2,'little')for i in range(504));native_flags=b''.join(decode(native,1318+i*4).to_bytes(2,'little')for i in range(8));assert native_npc==npc and native_flags==flags
  original_npc=b''.join(decode(base,1508+i*2).to_bytes(2,'little')for i in range(504));target=index*24;assert npc[:target]==original_npc[:target]and npc[target+24:]==original_npc[target+24:]
  if result=='win':assert npc[target:target+24]==bytes(24)
  else:
   rows=v['enemy_remaining'];encoded=bytearray(24)
   for raw,row in enumerate(rows):
    if row['count']:struct.pack_into('<HH',encoded,raw*4,int(row['unit'].split(':')[1]),row['count'])
   assert npc[target:target+24]==bytes(encoded)and npc[target:target+24]!=original_npc[target:target+24]
  record=saved['world']['encounters'][f'guarded:{region:02d}:{index:02d}'];assert record['cleared']==(result=='win')
  if result!='win':assert record['enemy']==v['enemy_remaining']
  assert v['world_sha256']==cold['world_sha256']and v['location']==cold['location']and v['NPC_hex']==cold['NPC_hex']and v['swords_hex']==cold['swords_hex']and v['saved_resources']==cold['resources']and cold['separate_process']and not cold['snapshot_loaded']
  assert len(saved['native_files'])==9
  for n,raw in saved['native_files'].items():assert len(base64.b64decode(raw))==5761 and base64.b64decode(raw)==(folder/'scratch'/n).read_bytes()
  before_native=(folder/'before-f7-cold/scratch/gamedata.ay').read_bytes();assert [decode(before_native,1508+i*2)for i in range(504)]==[decode(base,1508+i*2)for i in range(504)],'opaque NPC updated before F7'
  cases.append(dict(name=name,result=result,remaining=v['remaining'],resources=v['resources'],actions=v['ordinary_actions'],boss=ctx['boss'],record_key=f'guarded:{region:02d}:{index:02d}'))
 random=read(q/'world-r1/native-retreat-go/receipt.json');assert random['result']=='retreat'and random['checkpoint_saves']==1 and random['cold_continue']
 assert '--- PASS: TestOriginalGuardWorld/hd-retreat'in(q/'tests-hd-guards-r1.log').read_text()
 for name in ['tests-models-r2.log','tests-guards-r1.log','tests-native-win-r3.log','tests-mixed-boss-r1.log','tests-cold-r1.log','regression-r1.log','tests-random-regression-r1.log']:assert(q/name).read_text().rstrip().endswith('PASS'),name
 write(out,dict(status='passed-original-battle-guards-audit',source_files=len(manifest),ida_functions=functions,ida_lines=lines,cleanup_direct_body_bytes=43,original_pairs=pairs,Go_guard_worlds=cases,record_models=16,record_refusals=7,reward_refusals=12,committed_return_model_retries=5,interrupted_paired_commit_recovered=True,pre_F7_cold_engine_restorations=4,actual_F7_saves=4,separate_process_Continue=4,non_target_NPC_and_native_army_preserved=True,no_random_victory_reward_or_promotion=True,source_cohorts_production_equal=True,initial_seed=0x12345678,seed_method='setupCold sets DS:81BC/81BE before moving into the guard; no reroll.',formal_runtime_unchanged=True,general_entry_disabled=True,limits=['Large army, leadership30000, merit10000 and starting position are fixtures; native guard roster unchanged.','Original/Go comparisons cover native win and HD retreat only; mixed/boss cases have no equivalent native new-ID roster.','Record overlay restores Go NPC/sword authority before F7; full native opaque checkpoint updates at the original F7. No schema change.','Engine frames only; no new actual-window acceptance.','Final guard/ending bridge, in-process repeated battles, rules/AI integration, over-leadership persistence, dynamic poses, wide animation, mid-battle save and general startup remain open.']))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['freeze','audit','publish','archive','verify'])
 for n in ['project','archive','out']:p.add_argument('--'+n,type=Path)
 a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   obj=d['objects'][f['sha256']];stored=(a.archive/BATCH/obj['file']).read_bytes();assert hashlib.sha256(stored).hexdigest()==obj['stored_sha256'];raw=gzip.decompress(stored);assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-original-battle-guards',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL;s=importlib.util.spec_from_file_location('helper',r/'tools/prepare-owned-army-ui.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h);deps=h.dependencies(r);assert deps==read(q/'baseline.json')
 if a.action=='freeze':
  names=set(read(r/'preserved/owned-player-source-manifest-r1.json'))|{str(f.relative_to(r))for f in(r/'internal/ownedworld').glob('*.go')}
  for n in sorted(names):dst=q/'source'/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,dst)
  (q/'source-manifest.json').write_text(json.dumps({n:sha(q/'source'/n)for n in sorted(names)},indent=2)+'\n');shutil.copyfile(r/'tools/original-battle-guards.py',q/'original-battle-guards.py');return
 if a.action=='audit':audit(r,q,a.out);return
 if a.action=='publish':
  import io
  from PIL import Image,ImageDraw,ImageFont
  assert read(r/'preserved/original-battle-guards-audit-r1.json')['status']=='passed-original-battle-guards-audit'
  idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),28,index=3)
  canvas=Image.new('RGB',(1920,550),'#11251f');draw=ImageDraw.Draw(canvas);sources=[]
  for i,(name,label)in enumerate([('native-win','原版守軍勝利：月薪100 → 120'),('hd-retreat','HD撤退：守軍殘兵保留'),('hd-boss-win','HD頭目勝利：第一劍旗標保存')]):
   file=q/'guards-r1'/f'{name}-mode-1/map.png';canvas.paste(Image.open(file).resize((640,400),Image.Resampling.NEAREST),(i*640,60));draw.text((i*640+14,10),label,font=font,fill='#fff1b5');sources.append(dict(path=str(file.relative_to(r)),sha256=sha(file)))
  draw.text((18,480),'明示軍隊／起始位置；原守軍編成保持。圖為戰後地圖，F7及新程序讀檔已驗。',font=font.font_variant(size=26),fill='#fff1b5')
  file=a.out/'original-battle-guards-go-r1.png';assert not file.exists();canvas.save(file);write(a.out/'original-battle-guards-go-r1.json',dict(schema=1,sha256=sha(file),inputs=sources,actual_window=False,battle_animation_midframe=False,general_player_entry=False,scope='Controlled initial armies and positions; native guards unchanged; postbattle map frames.'));return
 assert read(r/'preserved/original-battle-guards-audit-r1.json')['status']=='passed-original-battle-guards-audit'
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for f in sorted(q.rglob('*')):
  if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
  assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();digest=hashlib.sha256(raw).hexdigest();obj=folder/(digest+'.gz')
  if digest not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[digest]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(f.relative_to(r)),bytes=len(raw),sha256=digest,mode=f.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Original assets/full frames/states and binaries local only; general startup disabled.'))
if __name__=='__main__':main()
