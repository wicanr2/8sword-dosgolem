#!/usr/bin/env python3
"""Spec030 original world-result UI, Go resource writes and native F7 lifecycle."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,sys
from pathlib import Path
sys.dont_write_bytecode=True
REL='workplace/probe-20261023/graphics-first/battle-r1/original-battle-world-r1';BATCH='original-battle-world-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['freeze','cold','audit','publish','archive','verify']);
 for n in ['project','archive','out']:p.add_argument('--'+n,type=Path)
 a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   o=d['objects'][f['sha256']];z=(a.archive/BATCH/o['file']).read_bytes();assert hashlib.sha256(z).hexdigest()==o['stored_sha256'];raw=gzip.decompress(z);assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-original-battle-world',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL
 if a.action=='cold':
  import subprocess
  rows=[]
  for name in['native-retreat-go','hd-loss-go','expanded-win','expanded-loss-origin','expanded-win-promotion']:
   folder=q/'world-r1'/name;env=dict(os.environ,EIGHTSWORD_ORIGINAL_BATTLE_WORK=str(q),EIGHTSWORD_WORLD_COLD_SESSION=str(folder/'session'),EIGHTSWORD_WORLD_COLD_OUT=str(folder/'process-cold'),EIGHTSWORD_WORLD_COLD_HD='0'if name.startswith('native-')else'1')
   cmd=['xvfb-run','-a',str(q/'ownedworld.test'),'-test.run','^TestOriginalBattleWorldCold$','-test.v']
   with(folder/'process-cold.log').open('x')as log:subprocess.run(cmd,cwd=q/'source',env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60)
   receipt=read(folder/'process-cold/receipt.json');assert receipt['separate_process']and not receipt['snapshot_loaded'];rows.append(dict(name=name,receipt=receipt,command=cmd))
  write(a.out,dict(status='passed-original-battle-world-five-process-cold',rows=rows));return
 s=importlib.util.spec_from_file_location('helper',r/'tools/prepare-owned-army-ui.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h);deps=h.dependencies(r);assert deps==read(q/'baseline.json')
 if a.action=='freeze':
  names=set(read(r/'preserved/owned-player-source-manifest-r1.json'))|{str(p.relative_to(r))for p in(r/'internal/ownedworld').glob('*.go')}
  for n in sorted(names):dst=q/'source'/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,dst)
  (q/'source-manifest.json').write_text(json.dumps({n:sha(q/'source'/n)for n in sorted(names)},indent=2)+'\n');shutil.copyfile(r/'tools/original-battle-world.py',q/'original-battle-world.py');return
 if a.action=='audit':
  import base64,struct
  from PIL import Image
  manifest=read(q/'source-manifest.json')
  for n,d in manifest.items():assert sha(r/n)==sha(q/'source'/n)==d
  for old in['native-pairs-pass-expanded-input-failed','mixed-motion-diagnostic']:
   prior=read(q/old/'source-manifest.json')
   # Only the explicitly corrected motion planner and test code changed after
   # the original controls. The final Go cases were rerun with the correction.
   for n,d in prior.items():
    if n.endswith('_test.go')or n=='internal/ownedworld/original_battle_rounds.go':continue
    assert manifest[n]==d
  pam=(q/'inputs/PAM.AY').read_bytes();image=bytearray(pam);word=lambda at:int.from_bytes(pam[at:at+2],'little');header=word(8)*16
  for i in range(word(6)):
   at=word(24)+i*4;off=header+word(at+2)*16+word(at);image[off:off+2]=((word(off)+0x1000)&65535).to_bytes(2,'little')
  total=0
  for item in read(q/'evidence/provenance.json'):
   file=q/'evidence'/Path(item['original_path']).name;assert sha(file)==item['sha256'];v=read(file)
   assert v.get('function_count')in[None,521]and v.get('input_sha256',v.get('source_sha256'))==hashlib.sha256(pam).hexdigest()and v['database_sha256']=='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac'
   for f in v['functions']:
    for l in f['lines']:
     raw=bytes.fromhex(l['bytes']);assert bytes(image[l['file_offset']:l['file_offset']+len(raw)])==raw;total+=1
  data=header+(0x1e88-0x110)*16;thresholds=list(struct.unpack_from('<6H',pam,data+0x5b2));assert thresholds==[0,2000,5000,8000,12000,30000]
  units={v['id']:v for v in read(q/'inputs/army-catalog.json')['profiles']}
  names=['native-retreat-oracle','native-retreat-go','hd-loss-oracle','hd-loss-go','expanded-win','expanded-loss-origin','expanded-win-promotion']
  rows={n:read(q/'world-r1'/n/'receipt.json')for n in names}
  for a0,b0 in[('native-retreat-oracle','native-retreat-go'),('hd-loss-oracle','hd-loss-go')]:
   a1,b1=rows[a0],rows[b0]
   for key in['resources','location','seed_after','frame_sha256','saved_resources']:assert a1[key]==b1[key],(a0,key)
   pictures=[Image.open(q/'world-r1'/n/'map.png').convert('RGBA').tobytes()for n in[a0,b0]];assert pictures[0]==pictures[1]and hashlib.sha256(pictures[0]).hexdigest()==a1['frame_sha256']
  cold=read(q/'process-cold-receipt.json');assert cold['status']=='passed-original-battle-world-five-process-cold'and len(cold['rows'])==5
  keys=['rank','merit','monthly_pay','gold','leadership','spell_power']
  for name in names:
   row=rows[name];folder=q/'world-r1'/name
   if not row['go']:continue
   before=[row['before_resources'][k]for k in keys];expected=before[:]
   gold=sum(v['count']*units[v['unit']]['gold']for v in row['enemy_initial']if v['unit']);merit=sum(v['count']*units[v['unit']]['command']for v in row['enemy_initial']if v['unit'])//2
   assert(row['reward_gold'],row['reward_merit'])==(gold,merit)==(115,37)
   if row['result']=='win':expected[3]=min(30000,expected[3]+gold);expected[1]=min(30000,expected[1]+merit)
   elif row['result']=='retreat':
    plan=row['random'];n=(plan['Before']*214013+2531011)&0xffffffff;assert plan['After']==n and plan['Value']==(n>>16)&32767;expected[3]-=expected[3]//(plan['Value']//2730+3)
   else:assert row['result']=='loss'and row['choice']in[1,2]and not any(v['count']for v in row['remaining'])
   if row['result']!='loss'and expected[0]<5 and expected[1]>thresholds[expected[0]]:
    expected[0]+=1;expected[2]=min(30000,expected[2]+100);expected[4]=min(30000,expected[4]+100);expected[5]=min(30000,expected[5]+expected[0]*3)
   assert row['resources']==expected and [row['saved_resources'][k]for k in keys]==expected
   assert row['checkpoint_saves']==1 and row['cold_continue']and row['cold_location']==row['location']
   child=read(folder/'process-cold/receipt.json');assert child['world_sha256']==row['cold_store_world_sha256']and child['location']==row['location']and [child['resources'][k]for k in keys]==expected
   native=(folder/'scratch/gamedata.ay').read_bytes();saved=read(folder/'session/gamedata.ay.army.json');assert saved['original_sha256']==hashlib.sha256(native).hexdigest()and saved['world']['army']['slots']==row['remaining']
   assert len(native)==2987 and [(struct.unpack_from('<H',native,i*2)[0]-i*2-3)&65535 for i in range(6)]==expected
   assert len(saved['native_files'])==9
   for mapname,raw in saved['native_files'].items():assert len(base64.b64decode(raw))==5761 and base64.b64decode(raw)==(folder/'scratch'/mapname).read_bytes()
   pic=Image.open(folder/'map.png').convert('RGBA');assert hashlib.sha256(pic.tobytes()).hexdigest()==row['frame_sha256']
  assert [v['count']for v in rows['expanded-win']['remaining'][:2]]==[58,2]and rows['expanded-win']['actions']==17
  promotion=rows['expanded-win-promotion'];assert promotion['resources']==[2,2036,30000,30000,200,30000]
  for file in['tests-r2.log','tests-promotion-r1.log','regression-r1.log']:assert(q/file).read_text().rstrip().endswith('PASS')
  assert read(q/'world-controls.json')==dict(refusals=8,state_unchanged=True)and read(q/'motion-models.json')==dict(cases=6,dead_source_refused=True)
  write(a.out,dict(status='passed-original-battle-world-audit',source_files=len(manifest),ida_lines=total,original_pairs=2,frame_resource_location_seed_pairs_equal=True,go_world_results=5,actual_F7_saves=5,separate_process_cold=5,new_ids_in_native_tables=0,empty_destination_motion_corrected=True,motion_models=6,world_refusals=8,win_resources=rows['expanded-win']['resources'],win_survivors=rows['expanded-win']['remaining'],promotion_cap_resources=promotion['resources'],formal_runtime_unchanged=True,general_player_entry_disabled=True,not_verified=['guard/boss world results','special/caster actions and spells','formation/tactics and target AI integration','new unit hit/death poses','wide animation','battle in-progress save/resume in original battlefield','actual GUI window','general owned player startup']));return
 if a.action=='publish':
  import io
  from PIL import Image,ImageDraw,ImageFont
  assert read(r/'preserved/original-battle-world-audit-r1.json')['status']=='passed-original-battle-world-audit'
  idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),28,index=3)
  out=Image.new('RGB',(1920,535),'#11251f');draw=ImageDraw.Draw(out);sources=[]
  for i,(name,file,title)in enumerate([('expanded-win-promotion','map.png','晉級：2級，月薪與法力封頂'),('expanded-win','map.png','勝利：58民兵、2弓箭手；金615'),('expanded-loss-origin','map.png','全滅：原選單傳送回起點')]):
   source=q/'world-r1'/name/file;out.paste(Image.open(source).resize((640,400),Image.Resampling.NEAREST),(i*640,52));draw.text((i*640+10,8),title,font=font,fill='#fff1b5');sources.append(dict(path=str(source.relative_to(r)),sha256=sha(source),scenario=name))
  draw.text((18,474),'明示測試編成／晉級邊界；F7與獨立程序Continue已驗。Engine畫面，尚未開放一般Go入口。',font=font.font_variant(size=25),fill='#fff1b5');dest=a.out/'original-battle-world-f7-r1.png';assert not dest.exists();out.save(dest);write(a.out/'original-battle-world-f7-r1.json',dict(schema=1,sha256=sha(dest),inputs=sources,actual_window=False,general_player_entry=False,scope='Original random-encounter result UI; Go army/resources, source F7 and separate-process Continue.'));return
 if a.action=='archive':
  assert read(r/'preserved/original-battle-world-audit-r1.json')['status']=='passed-original-battle-world-audit'
  folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
  for f in sorted(q.rglob('*')):
   if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
   assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();digest=hashlib.sha256(raw).hexdigest();obj=folder/(digest+'.gz')
   if digest not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[digest]=dict(file=obj.name,stored_sha256=sha(obj))
   files.append(dict(path=str(f.relative_to(r)),bytes=len(raw),sha256=digest,mode=f.stat().st_mode&0o777))
  write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Full original data, frames, states and binaries local only. General owned player entry blocked.'))
if __name__=='__main__':main()
