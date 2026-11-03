#!/usr/bin/env python3
"""Spec030 player attack-spell Go data: source freeze, audit and permanent evidence."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,sys
from pathlib import Path
sys.dont_write_bytecode=True
REL='workplace/probe-20261023/graphics-first/battle-r1/original-battle-spells-r1';BATCH='original-battle-spells-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def audit(r,q,deps,out):
 import base64,struct
 from PIL import Image
 manifest=read(q/'source-manifest.json')
 for n,d in manifest.items():assert sha(r/n)==sha(q/'source'/n)==d,n
 pam=(q/'inputs/PAM.AY').read_bytes();image=bytearray(pam);word=lambda at:int.from_bytes(pam[at:at+2],'little');header=word(8)*16
 for i in range(word(6)):
  at=word(24)+i*4;off=header+word(at+2)*16+word(at);image[off:off+2]=((word(off)+0x1000)&65535).to_bytes(2,'little')
 origin=read(q/'evidence/provenance.json');evidence=q/'evidence/ida-spells-r4.json';assert sha(evidence)==origin['sha256']
 ida=read(evidence);assert ida['tool']=='IDA 9.4'and ida['source_sha256']==sha(q/'inputs/PAM.AY')and ida['database_sha256']=='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac'
 lines=0
 for f in ida['functions']:
  for l in f['lines']:
   raw=bytes.fromhex(l['bytes']);off=l['original_file_offset'];assert bytes(image[off:off+len(raw)])==raw,(f['name'],hex(l['ida_linear']));lines+=1
 profiles=read(q/'inputs/combat-catalog.json')['profiles'];rows=[]
 names=['fireball-hd','thunder-hd','exorcism-hd','assassination-hd','assassination-fail-hd','halve-hd','quake-hd','fireball-native','cancel-menu','cancel-target','cancel-target-space']
 for name in names:
  paths=[q/'casts-r1'/f'{name}-mode-{mode}'for mode in[0,1]];a,b=[read(p/'receipt.json')for p in paths]
  for k in['units_hex','hp_hex','charges_hex','seed','frame_sha256']:assert a[k]==b[k],(name,k)
  pictures=[Image.open(p/'frame.png').convert('RGBA').tobytes()for p in paths];assert pictures[0]==pictures[1]and hashlib.sha256(pictures[0]).hexdigest()==a['frame_sha256']
  record=b['record'];sel=record['Selector'];effects=record['Effects']or[];charges=list(struct.unpack('<8H',bytes.fromhex(b['charges_hex'])))
  assert record['BeforeCharges']==[3]*8 and record['AfterCharges']==charges
  expected=[3]*8
  if name.startswith('cancel-'):assert not effects and not record['Random']
  else:expected[b['selector']]-=1
  if name=='cancel-target':expected[0]-=1 # Original Esc retreats after charge consumption; Space refunds.
  assert expected==charges
  if name=='assassination-fail-hd':assert not effects and record['Random']['Value']%50>=10
  elif not name.startswith('cancel-'):assert effects
  for e in effects:
   assert e['Updates']==1 and e['selector']==sel and e['Source']==record['Caster']
   target=profiles[b['rows'][1][e['Raw']]['unit']];before=e['Before'];factor=6
   if sel in[0,1]:amount=(2//3+1)*factor//(target['hp']//10)+2
   elif sel==2:amount=14 if not 6<=target['native_kind']<=15 else (2+1)*14//(target['hp']//10)+2
   elif sel==3:amount=before
   elif sel==5:amount=before//2+1
   else:assert sel==7;amount=before if before<50 else before*6//20+21
   after=max(0,before-amount);assert(e['Amount'],e['After'])==(amount,after)
   assert b['rows'][1][e['Raw']]['count']==after
   planned=[]
   if sel!=7:
    start=min(before,5)if after==0 else after+5 if amount>=5 else before
    planned=list(range(start,after-1,-1))
   assert(e['Display']or[])==(e['Planned']or[])==planned
  if record['Random']:
   z=record['Random'];n=(z['Before']*214013+2531011)&0xffffffff;assert z['After']==n and z['Value']==(n>>16)&32767
  words=struct.unpack('<24H',bytes.fromhex(b['units_hex']))
  for side in[0,1]:
   for raw,s in enumerate(b['rows'][side]):assert words[(side*6+raw)*2+1]==s['count']
  rows.append(dict(name=name,selector=b['selector'],effects=len(effects),charges=charges,seed=b['seed'],frame_sha256=b['frame_sha256']))
 assert read(q/'spell-models.json')==dict(cases=13,refusals=9)
 assert read(q/'spell-guards.json')==dict(refusals=8,state_unchanged=True)
 assert read(q/'spell-entry-guards.json')==dict(refusals=5,valid_entry=1,guest_unchanged=True)
 world=read(q/'spell-world-r1/receipt.json');cold=read(q/'spell-world-r1/process-cold/receipt.json')
 assert world['result']=='win'and world['ordinary_actions']>=2 and world['checkpoint_saves']==1 and world['records'][0]['Effects']
 assert world['stored_rules']=='formation'and world['battle_rules_applied']=='native'
 for key in['world_sha256','resources','location','charges_hex']:assert cold[key]==world[key],('cold',key)
 assert cold['separate_process']and not cold['snapshot_loaded']
 folder=q/'spell-world-r1';native=(folder/'scratch/gamedata.ay').read_bytes();saved=read(folder/'session/gamedata.ay.army.json')
 assert saved['original_sha256']==hashlib.sha256(native).hexdigest()and saved['world']['army']['slots']==world['remaining']
 assert len(saved['native_files'])==9
 for n,raw in saved['native_files'].items():assert base64.b64decode(raw)==(folder/'scratch'/n).read_bytes()
 for log in['tests-fireball-r4.log','tests-remaining-r1.log','tests-assassination-fail-r1.log','tests-target-space-r1.log','tests-entry-guards-r1.log','tests-spell-world-r1.log','tests-spell-cold-r1.log','regression-r1.log']:assert(q/log).read_text().rstrip().endswith('PASS'),log
 write(out,dict(status='passed-original-battle-spells-audit',source_files=len(manifest),ida_functions=len(ida['functions']),ida_lines=lines,original_pairs=len(names),frames_counts_HP_charges_seed_equal=True,spells=[0,1,2,3,5,7],rows=rows,models=13,model_refusals=9,hook_refusals=13,held_retries_per_pair=5,world=world,separate_process_Continue=True,formal_runtime_unchanged=True,general_player_entry_disabled=True,limits=['Controlled caster/learned/stat/charge fixtures; not natural spell acquisition.','Original intermediate arithmetic remains as a checked compatibility calculation.','Native caster kinds 10/12 and native enemy profiles only.','Freeze/clone and enemy specials, guard/boss adapters, rules/AI integration, wide animation and battle mid-save remain open.','Engine frames; no new actual window acceptance.']))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['freeze','audit','publish','archive','verify']);
 for n in ['project','archive','out']:p.add_argument('--'+n,type=Path)
 a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   o=d['objects'][f['sha256']];z=(a.archive/BATCH/o['file']).read_bytes();assert hashlib.sha256(z).hexdigest()==o['stored_sha256'];raw=gzip.decompress(z);assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-original-battle-spells',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL;s=importlib.util.spec_from_file_location('helper',r/'tools/prepare-owned-army-ui.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h);deps=h.dependencies(r);assert deps==read(q/'baseline.json')
 if a.action=='freeze':
  names=set(read(r/'preserved/owned-player-source-manifest-r1.json'))|{str(p.relative_to(r))for p in(r/'internal/ownedworld').glob('*.go')}
  for n in sorted(names):dst=q/'source'/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,dst)
  (q/'source-manifest.json').write_text(json.dumps({n:sha(q/'source'/n)for n in sorted(names)},indent=2)+'\n');shutil.copyfile(r/'tools/original-battle-spells.py',q/'original-battle-spells.py');return
 if a.action=='audit':audit(r,q,deps,a.out);return
 if a.action=='publish':
  import io
  from PIL import Image,ImageDraw,ImageFont
  assert read(r/'preserved/original-battle-spells-audit-r1.json')['status']=='passed-original-battle-spells-audit'
  idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),28,index=3)
  canvas=Image.new('RGB',(1920,550),'#11251f');draw=ImageDraw.Draw(canvas);sources=[]
  items=[('casts-r1/fireball-native-mode-1/frame.png','原版模式：火球完成，目標35 → 30'),('casts-r1/fireball-hd-mode-1/frame.png','HD模式：同局Go兵力與原演出'),('spell-world-r1/map.png','施法後勝利、F7與重新載入')]
  for i,(path,label)in enumerate(items):
   file=q/path;canvas.paste(Image.open(file).resize((640,400),Image.Resampling.NEAREST),(i*640,60));draw.text((i*640+14,10),label,font=font,fill='#fff1b5');sources.append(dict(path=str(file.relative_to(r)),sha256=sha(file)))
  draw.text((18,480),'明示施法者／次數配置；原戰場完成幀。Go持有正式兵數，原選單與HD演出保留。',font=font.font_variant(size=26),fill='#fff1b5')
  dest=a.out/'original-battle-go-spells-r1.png';assert not dest.exists();canvas.save(dest);write(a.out/'original-battle-go-spells-r1.json',dict(schema=1,sha256=sha(dest),inputs=sources,actual_window=False,spell_animation_midframe=False,general_player_entry=False,scope='Controlled spell fixtures; original battlefield completion frames and postbattle map.'));return
 if a.action=='archive':
  assert read(r/'preserved/original-battle-spells-audit-r1.json')['status']=='passed-original-battle-spells-audit'
  folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
  for f in sorted(q.rglob('*')):
   if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
   assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();digest=hashlib.sha256(raw).hexdigest();obj=folder/(digest+'.gz')
   if digest not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[digest]=dict(file=obj.name,stored_sha256=sha(obj))
   files.append(dict(path=str(f.relative_to(r)),bytes=len(raw),sha256=digest,mode=f.stat().st_mode&0o777))
  write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Full original files, frames, states and binaries local only; player startup disabled.'))
if __name__=='__main__':main()
