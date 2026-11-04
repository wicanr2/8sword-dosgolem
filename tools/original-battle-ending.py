#!/usr/bin/env python3
"""Spec030 final guard: freeze, audit, publish, preserve and detached verify."""
import argparse, gzip, hashlib, importlib.util, json, os, shutil, struct, sys
from pathlib import Path
sys.dont_write_bytecode = True
REL = 'workplace/probe-20261023/graphics-first/battle-r1/original-battle-ending-r1'
BATCH = 'original-battle-ending-r1'
STATUS = 'passed-original-battle-ending-audit'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def write(p,v):
 with p.open('x') as f: json.dump(v,f,ensure_ascii=False,indent=2); f.write('\n')
def audit(r,q,out):
 from PIL import Image
 manifest=read(q/'source-manifest.json')
 for n,d in manifest.items(): assert sha(r/n)==sha(q/'source'/n)==d,n
 for n,d in read(q/'runtime-cohort/source-manifest.json').items():
  if not n.endswith('_test.go'):assert d==manifest[n],n
 pam=(q/'inputs/PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
 image=bytearray(pam);word=lambda at:int.from_bytes(pam[at:at+2],'little');header=word(8)*16
 for i in range(word(6)):
  at=word(24)+i*4;off=header+word(at+2)*16+word(at);image[off:off+2]=((word(off)+0x1000)&65535).to_bytes(2,'little')
 lines=functions=0
 for name in ['ida-guard-world.json','ida-guard-rewards.json','ida-save.json','ida-original-guards-r1.json','ida-original-guards-r2.json']:
  v=read(q/'evidence'/name);assert v.get('source_sha256',v.get('input_sha256'))==sha(q/'inputs/PAM.AY') and v['database_sha256']=='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac'
  functions+=len(v['functions'])
  for f in v['functions']:
   for l in f['lines']:
    raw=bytes.fromhex(l['bytes']);off=l.get('original_file_offset',l.get('file_offset'));assert bytes(image[off:off+len(raw)])==raw;lines+=1
 guard=next(f for f in read(q/'evidence/ida-guard-world.json')['functions'] if f['name']=='sub_12DDE');by={l['ida_linear']:l for l in guard['lines']}
 assert by[0x13295]['bytes']=='c706e2560100' and by[0x1329b]['bytes']=='0e' and by[0x1329c]['bytes']=='e86fcf' and by[0x132a7]['bytes']=='e814e8'
 assert read(q/'ending-guards.json')==dict(refusals=16,state_unchanged=True)
 models=read(q/'ending-records.json');assert models['refusals']==15 and models['interrupted_commit_recovered'] and models['recovery_idempotent'] and models['opaque_checkpoint_preserved'] and models['boss_records_supply_swords']
 missing=read(q/'ending-missing-swords/receipt.json');assert missing['original_warning_branch']>0 and missing['battle_gate_entries']==0 and missing['progress_unchanged'] and not missing['ending_handoff']
 a=read(q/'ending-r1/hd-native-control/receipt.json');b=read(q/'ending-r1/hd-native-go/receipt.json')
 for key in ['resources','NPC_hex','swords_hex','seed','native_returned_hex']: assert a[key]==b[key],key
 # Frame is sampled at the first original target picker, before either result.
 assert Image.open(q/'ending-r1/hd-native-control/battle.png').convert('RGBA').tobytes()==Image.open(q/'ending-r1/hd-native-go/battle.png').convert('RGBA').tobytes()
 decode=lambda raw,at:(struct.unpack_from('<H',raw,at)[0]-at-3)&65535
 results=[]
 for name in ['hd-native-go','hd-mixed-go']:
  folder=q/'ending-r1'/name;v=read(folder/'receipt.json');cold=read(folder/'process-cold/receipt.json');play=read(folder/'process-cold/playback.json');save=read(folder/'session/gamedata.ay.army.json');native=(folder/'session/gamedata.ay').read_bytes();world=save['world']
  assert v['resources']==[1,10000,100,500,30000,0] and v['native_guard_unmodified'] and v['controlled_swords']==8 and v['prebattle_F7_saves']==1 and v['actions']>0
  assert [decode(native,i*2)for i in range(6)]==v['resources'] and world['army']['gold']==500 and world['army']['leadership']==30000 and world['progress']['rank']==1 and world['progress']['merit']==10000 and world['progress']['legacy_04f6']==100 and world['progress']['legacy_04fc']==0
  assert v['enemy_initial']==models['enemy']==[dict(unit=u,count=n)for u,n in [('native:19',500),('native:24',500),('native:10',400),('native:25',400),('native:15',400),('native:20',400)]]
  assert v['remaining']==world['army']['slots'] and world['encounters']['guarded:00:04']==dict(enemy=v['enemy_initial'],cleared=True)
  digest=hashlib.sha256(json.dumps(world,ensure_ascii=False,separators=(',',':')).encode()).hexdigest();assert digest==v['world_sha256']==cold['world_sha256'] and cold['token']==v['token']
  assert cold['separate_process'] and not cold['snapshot_loaded'] and cold['battle_actions']==0 and cold['exit_code']==play['exit_code']==0 and play['gameplay_hooks_disabled'] and play['stages']['END7.AY']
  assert play['ending']['error']=='' and play['ending']['bound']
  for counter in ['glyph-go-rows','masked-skipped-x86','direct-skipped-x86-instructions']:assert play['ending']['direct'][counter]>0,counter
  assert len([e for e in v['events']if e['event']=='committed'])==1 and not [e for e in v['events']if e['event']=='reward']
  assert [e['event']for e in cold['events']]==['bound','ending-replay','ending-handoff']
  assert save['original_sha256']==sha(folder/'session/gamedata.ay') and len(save['native_files'])==9
  npc=bytes.fromhex(v['NPC_hex']);flags=bytes.fromhex(v['swords_hex']);assert flags==b'\x01\x00'*8 and npc[96:120]==bytes(24)
  oldnpc=b''.join(decode(native,1508+i*2).to_bytes(2,'little')for i in range(504));assert oldnpc[:96]==npc[:96] and oldnpc[120:]==npc[120:] and oldnpc[96:120]!=bytes(24)
  for i,row in enumerate(v['enemy_initial']):assert (decode(native,1604+i*4),decode(native,1606+i*4))==(int(row['unit'].split(':')[1]),row['count'])
  assert native[12:36]==(folder/'process-cold/scratch/gamedata.ay').read_bytes()[12:36]
  prior=json.loads(json.dumps(world));prior['revision']-=1;prior['army']['slots']=v['player'];del prior['encounters']['guarded:00:04'];assert hashlib.sha256(json.dumps(prior,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==v['world_before']
  results.append(dict(name=name,actions=v['actions'],remaining=v['remaining'],resources=v['resources'],world_sha256=digest,ending_exit_code=0,separate_process_replay_without_battle=True))
 for name in ['tests-models-final-r1.log','tests-go-final-r1.log','tests-native-final-r1.log','tests-mixed-final-r1.log','tests-cold-hd-native-go-r1.log','tests-cold-hd-mixed-go-r1.log','regression-final-r1.log']:
  assert(q/name).read_text().rstrip().endswith('PASS'),name
 write(out,dict(status=STATUS,source_files=len(manifest),ida_functions=functions,ida_lines=lines,source_manifest_sha256=sha(q/'source-manifest.json'),original_final_guard_roster_unchanged=True,original_Go_comparison=['resources','NPC','eight_swords','seed','returned_army','first_target_picker_frame'],worlds=results,hook_refusals=16,record_refusals=15,actual_missing_swords_refused=True,interrupted_commit_recovered=True,no_victory_salary_before_ending=True,prebattle_F7_saves=3,separate_process_replays=2,schema_unchanged=True,formal_runtime_unchanged=True,general_entry_disabled=True,limits=['Armies, leadership30000, merit10000, eight swords and adjacent position are explicit fixtures; not a natural clear.','HD original/Go final battle sampled; native mode final battle not newly sampled.','Cold Continue returns to prebattle F7 checkpoint; move/confirm at final guard replays ending, without another battle or transaction. Not automatic return-phase resume.','Engine Frames only; no new actual-window acceptance.','New-unit standing/action art is not integrated into Engine.Frame; mixed first-picker frames still use the original temporary pose. Data results do not prove appearance.','In-process repeated battles/cancel re-entry, rules/AI integration, battle resume and general startup remain open.']))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['freeze','audit','publish','archive','verify'])
 for n in ['project','archive','out']:p.add_argument('--'+n,type=Path)
 a=p.parse_args();assert Path('/.dockerenv').exists() and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   ob=d['objects'][f['sha256']];p=a.archive/BATCH/ob['file'];assert sha(p)==ob['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes'] and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-original-battle-ending',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL;s=importlib.util.spec_from_file_location('helper',r/'tools/prepare-owned-army-ui.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h);deps=h.dependencies(r);assert deps==read(q/'baseline.json')
 if a.action=='freeze':
  names=set(read(r/'preserved/owned-player-source-manifest-r1.json'))|{str(f.relative_to(r))for f in(r/'internal/ownedworld').glob('*.go')}
  for n in sorted(names):dst=q/'source'/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,dst)
  (q/'source-manifest.json').write_text(json.dumps({n:sha(q/'source'/n)for n in sorted(names)},indent=2)+'\n');shutil.copyfile(r/'tools/original-battle-ending.py',q/'original-battle-ending.py');return
 if a.action=='audit':audit(r,q,a.out);return
 assert read(r/'preserved/original-battle-ending-audit-r1.json')['status']==STATUS
 if a.action=='publish':
  import io
  from PIL import Image,ImageDraw,ImageFont
  idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),28,index=3)
  canvas=Image.new('RGB',(1280,540),'#11251f');draw=ImageDraw.Draw(canvas);sources=[]
  for i,(rel,label)in enumerate([('hd-native-go/battle.png','原版HD戰場：原六隊最終守軍'),('hd-mixed-go/process-cold/END7.AY.png','獨立程序讀檔：HD結局完整播放')]):
   f=q/'ending-r1'/rel;canvas.paste(Image.open(f).resize((640,400),Image.Resampling.NEAREST),(i*640,60));draw.text((i*640+12,12),label,font=font,fill='#fff1b5');sources.append(dict(path=str(f.relative_to(r)),sha256=sha(f)))
  draw.text((14,475),'明示軍隊／八劍／位置；原守軍不改。新增兵種戰果已驗，站姿與動態圖像待接線。',font=font.font_variant(size=24),fill='#fff1b5')
  f=a.out/'original-battle-ending-go-r1.png';assert not f.exists();canvas.save(f);write(a.out/'original-battle-ending-go-r1.json',dict(sha256=sha(f),sources=sources,actual_window=False,general_entry=False));return
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for f in sorted(q.rglob('*')):
  if not f.is_file() or 'build-cache'in f.relative_to(q).parts:continue
  assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();digest=hashlib.sha256(raw).hexdigest();obj=folder/(digest+'.gz')
  if digest not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[digest]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(f.relative_to(r)),bytes=len(raw),sha256=digest,mode=f.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Original data/full frames/states and binaries local only; general entry disabled.'))
if __name__=='__main__':main()
