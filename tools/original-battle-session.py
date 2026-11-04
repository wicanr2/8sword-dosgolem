#!/usr/bin/env python3
"""Spec030 guard lifecycle: freeze, audit, publish, preserve and detached verify."""
import argparse, gzip, hashlib, importlib.util, json, os, shutil, struct, sys
from pathlib import Path
sys.dont_write_bytecode = True
REL = 'workplace/probe-20261023/graphics-first/battle-r1/original-battle-session-r1'
BATCH = 'original-battle-session-r1'
STATUS = 'passed-original-battle-session-audit'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def write(p,v):
 with p.open('x') as f: json.dump(v,f,ensure_ascii=False,indent=2); f.write('\n')
def audit(r,q,out):
 from PIL import Image
 manifest=read(q/'source-manifest.json')
 for n,d in manifest.items():assert sha(r/n)==sha(q/'source'/n)==d,n
 pam=(q/'inputs/PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
 image=bytearray(pam);word=lambda at:int.from_bytes(pam[at:at+2],'little');header=word(8)*16
 for i in range(word(6)):
  at=word(24)+i*4;off=header+word(at+2)*16+word(at);image[off:off+2]=((word(off)+0x1000)&65535).to_bytes(2,'little')
 lines=functions=0
 for name in ['ida-guard-world.json','ida-guard-rewards.json','ida-save.json','ida-original-guards-r1.json','ida-original-guards-r2.json']:
  v=read(q/'evidence'/name);assert v.get('source_sha256',v.get('input_sha256'))==sha(q/'inputs/PAM.AY')and v['database_sha256']=='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac';functions+=len(v['functions'])
  for f in v['functions']:
   for l in f['lines']:
    raw=bytes.fromhex(l['bytes']);off=l.get('original_file_offset',l.get('file_offset'));assert bytes(image[off:off+len(raw)])==raw;lines+=1
 models=read(q/'session-ending-models.json');assert len(models['models'])==6 and models['refusals']==7 and models['no_F7_depleted_victory_retains_checkpoint']and models['schema_unchanged']
 rearm=read(q/'session-rearm-models.json');assert rearm==dict(refusals=13,refusals_preserve_controllers_and_guest=True,valid_rearm_preserves_guest_and_hook_pointers=True,latest_army_loaded=31,old_spell_growth_enemy_state_cleared=True)
 a,b=[read(q/'sessions-r1'/n/'receipt.json')for n in ['hd-native-control','hd-native-go']]
 for i,phase in enumerate(['cancel','retreat','win']):
  x,y=a['phases'][i],b['phases'][i];assert x['phase']==y['phase']==phase
  for key in ['resources','NPC_hex','swords_hex','seed','frame_rgba_sha256']:assert x[key]==y[key],(phase,key)
  if i:
   raw=struct.unpack('<12H',bytes.fromhex(x['native_army_hex']));assert y['outcome']['army']==[dict(unit=f'native:{k:02d}'if k else '',count=n)for k,n in zip(raw[::2],raw[1::2])]
  pictures=[Image.open(q/'sessions-r1'/n/(phase+'.png')).convert('RGBA').tobytes()for n in ['hd-native-control','hd-native-go']];assert pictures[0]==pictures[1]and hashlib.sha256(pictures[0]).hexdigest()==y['frame_rgba_sha256']
 decode=lambda raw,at:(struct.unpack_from('<H',raw,at)[0]-at-3)&65535
 results=[]
 for name in ['hd-native-go','hd-mixed-go']:
  folder=q/'sessions-r1'/name;v=read(folder/'receipt.json');saved=read(folder/'saved.json');cold=read(folder/'process-cold/receipt.json');side=read(folder/'session/gamedata.ay.army.json');world=side['world'];native=(folder/'session/gamedata.ay').read_bytes();assert v['same_engine']and v['native_guard_unmodified']
  phases=v['phases'];assert [p['phase']for p in phases]==['cancel','retreat','win']
  for i,p in enumerate(phases):
   expected=['','retreat','win'][i];o=p['outcome'];assert o['sequence']==i+1 and o['cancelled']==(i==0)and o['result']==expected and o['key']=='guarded:00:00'
   assert len([e for e in p['events']if e['event']=='committed'])==(i!=0)
   assert len([e for e in p['events']if e['event']=='reward'and e['ip']==0x1b7b])==(i==2)
   assert p['resources'][0:2]==[1,10000]and p['resources'][4:]==[30000,0]
   assert p['resources'][2:4]==[[100,500],[100,450],[120,450]][i]
  assert phases[0]['outcome']['army']==v['player']==phases[1]['outcome']['army']
  assert phases[1]['outcome']['enemy'][0]==dict(unit='native:11',count=40)and phases[1]['outcome']['enemy'][4:]==[dict(unit='',count=0)]*2
  assert saved['cleared_revisit_no_battle']and saved['saves']==1 and saved['army']==world['army']['slots']==phases[2]['outcome']['army']
  digest=hashlib.sha256(json.dumps(world,ensure_ascii=False,separators=(',',':')).encode()).hexdigest();assert digest==saved['world_sha256']==cold['world_sha256']and saved['resources']==cold['resources']and saved['location']==cold['location']
  prior=json.loads(json.dumps(world));prior['revision']-=1;assert hashlib.sha256(json.dumps(prior,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==phases[2]['world_sha256']
  assert cold['separate_process']and not cold['snapshot_loaded']and side['original_sha256']==sha(folder/'session/gamedata.ay')and len(side['native_files'])==9
  assert [decode(native,i*2)for i in range(6)]==phases[2]['resources']
  assert bytes.fromhex(phases[2]['NPC_hex'])[:24]==bytes(24)and all(decode(native,1508+i*2)==0 for i in range(12))
  results.append(dict(name=name,returns=4,cancels=1,cleared_visits=1,battles=2,resources=phases[2]['resources'],army=saved['army'],world_sha256=digest,F7_saves=1,separate_process_Continue=True))
 p=q/'ending-r1/hd-partial-go';v=read(p/'receipt.json');cold=read(p/'process-cold/receipt.json');play=read(p/'process-cold/playback.json');world=read(p/'session/gamedata.ay.army.json')['world'];native=(p/'session/gamedata.ay').read_bytes()
 partial=[dict(unit=u,count=400)for u in ['native:10','native:25','native:15','native:20']]+[dict(unit='',count=0)]*2
 assert v['controlled_partial_checkpoint']and not v['native_guard_unmodified']and v['enemy_initial']==partial and world['encounters']['guarded:00:04']==dict(enemy=partial,cleared=True)
 assert v['world_sha256']==cold['world_sha256']and v['token']==cold['token']and cold['battle_actions']==0 and cold['exit_code']==play['exit_code']==0 and play['stages']['END7.AY']and play['gameplay_hooks_disabled']
 assert v['resources']==[decode(native,i*2)for i in range(6)]==[1,10000,100,500,30000,0]
 for c in ['glyph-go-rows','masked-skipped-x86','direct-skipped-x86-instructions']:assert play['ending']['direct'][c]>0
 for n in ['tests-session-final-r1.log','tests-native-final-r1.log','tests-mixed-final-r1.log','tests-session-native-cold-r1.log','tests-session-mixed-cold-r1.log','tests-partial-final-r1.log','tests-partial-cold-r1.log','regression-final-r1.log']:assert(q/n).read_text().rstrip().endswith('PASS'),n
 write(out,dict(status=STATUS,source_files=len(manifest),source_manifest_sha256=sha(q/'source-manifest.json'),ida_functions=functions,ida_lines=lines,original_Go_phase_comparisons=3,session_worlds=results,rearm_refusals=13,partial_checkpoint_models=6,partial_checkpoint_refusals=7,no_F7_depleted_victory_retains_checkpoint=True,partial_checkpoint_actual_battle_and_process_cold_ending=True,partial_enemy_initial=partial,formal_runtime_unchanged=True,general_entry_disabled=True,schema_unchanged=True,initial_seed=0x12345678,limits=['Guard-only session; random/guard interchange and general startup not integrated.','Position, armies, leadership30000 and merit10000 are explicit fixtures. Ordinary native guard roster unchanged.','Cancel comparison concerns the noncombat path only: native shadow still has 30 militia; the custom native army is injected at the first battle entry. Not full-guest-state parity.','Partial final guard is a controlled four-row checkpoint derived from the original last four rows; not a natural prior retreat.','No-F7 final history retention is a Store model; not an additional full final battle.','New-unit standing/action art remains pending; data results do not prove appearance.','Engine Frames only; no new X11 or natural-clear acceptance.']))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['freeze','audit','publish','archive','verify'])
 for n in ['project','archive','out']:p.add_argument('--'+n,type=Path)
 a=p.parse_args();assert Path('/.dockerenv').exists() and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   ob=d['objects'][f['sha256']];p=a.archive/BATCH/ob['file'];assert sha(p)==ob['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes'] and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-original-battle-session',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL;s=importlib.util.spec_from_file_location('helper',r/'tools/prepare-owned-army-ui.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h);deps=h.dependencies(r);assert deps==read(q/'baseline.json')
 if a.action=='freeze':
  names=set(read(r/'preserved/owned-player-source-manifest-r1.json'))|{str(f.relative_to(r))for f in(r/'internal/ownedworld').glob('*.go')}
  for n in sorted(names):dst=q/'source'/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,dst)
  (q/'source-manifest.json').write_text(json.dumps({n:sha(q/'source'/n)for n in sorted(names)},indent=2)+'\n');shutil.copyfile(r/'tools/original-battle-session.py',q/'original-battle-session.py');return
 if a.action=='audit':audit(r,q,a.out);return
 assert read(r/'preserved/original-battle-session-audit-r1.json')['status']==STATUS
 if a.action=='publish':
  import io
  from PIL import Image,ImageDraw,ImageFont
  idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),28,index=3)
  canvas=Image.new('RGB',(1280,540),'#11251f');draw=ImageDraw.Draw(canvas);sources=[]
  for i,(rel,label)in enumerate([('sessions-r1/hd-native-go/win.png','同一程序取消、撤退後再戰勝利'),('ending-r1/hd-partial-go/process-cold/END7.AY.png','殘兵存檔讀取：完整HD結局')]):
   f=q/rel;canvas.paste(Image.open(f).resize((640,400),Image.Resampling.NEAREST),(i*640,60));draw.text((i*640+12,12),label,font=font,fill='#fff1b5');sources.append(dict(path=str(f.relative_to(r)),sha256=sha(f)))
  draw.text((14,475),'明示軍隊／位置；一般守軍編成不改。最終四隊為受控存檔配置，非自然通關。',font=font.font_variant(size=24),fill='#fff1b5')
  f=a.out/'original-battle-session-go-r1.png';assert not f.exists();canvas.save(f);write(a.out/'original-battle-session-go-r1.json',dict(sha256=sha(f),sources=sources,actual_window=False,general_entry=False));return
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for f in sorted(q.rglob('*')):
  if not f.is_file() or 'build-cache'in f.relative_to(q).parts:continue
  assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();digest=hashlib.sha256(raw).hexdigest();obj=folder/(digest+'.gz')
  if digest not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[digest]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(f.relative_to(r)),bytes=len(raw),sha256=digest,mode=f.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Original data/full frames/states and binaries local only; general entry disabled.'))
if __name__=='__main__':main()
