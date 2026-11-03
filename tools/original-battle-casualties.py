#!/usr/bin/env python3
"""Spec030 first original enemy melee, Go authoritative casualties and preservation."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,sys
from pathlib import Path
sys.dont_write_bytecode=True
REL='workplace/probe-20261023/graphics-first/battle-r1/original-battle-casualties-r1';BATCH='original-battle-casualties-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','audit','publish','archive','verify'])
 for n in ['project','archive','out']:p.add_argument('--'+n,type=Path)
 a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   o=d['objects'][f['sha256']];z=(a.archive/BATCH/o['file']).read_bytes();assert hashlib.sha256(z).hexdigest()==o['stored_sha256'];raw=gzip.decompress(z);assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-original-battle-casualties',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL;s=importlib.util.spec_from_file_location('helper',r/'tools/prepare-owned-army-ui.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h);deps=h.dependencies(r)
 if a.action=='prepare':
  parent=q.parent/'original-battle-actions-r1';assert q.is_dir()and not(q/'inputs').exists();shutil.copytree(parent/'inputs',q/'inputs');shutil.copytree(parent/'ui-assets',q/'ui-assets')
  for n in ['probe.mod','probe.sum']:shutil.copyfile(parent/n,q/n)
  write(q/'baseline.json',deps)
 if a.action in ['prepare','freeze']:
  assert deps==read(q/'baseline.json');names=set(read(r/'preserved/owned-player-source-manifest-r1.json'))|{str(p.relative_to(r))for p in(r/'internal/ownedworld').glob('*.go')}
  for n in sorted(names):dst=q/'source'/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,dst)
  (q/'source-manifest.json').write_text(json.dumps({n:sha(q/'source'/n)for n in sorted(names)},ensure_ascii=False,indent=2)+'\n')
  for n in ['original-battle-casualties.py','export-original-battle-casualties-ida.py']:shutil.copyfile(r/'tools'/n,q/n)
  return
 if a.action=='audit':
  from PIL import Image
  assert deps==read(q/'baseline.json')
  for n,d in read(q/'source-manifest.json').items():assert sha(r/n)==sha(q/'source'/n)==d
  ida=read(q/'ida/ida-casualties.json');assert ida['function_count']==521 and len(ida['functions'])==9 and ida['exporter_sha256']==sha(r/'tools/export-original-battle-casualties-ida.py')
  pam=(q/'inputs/PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()==ida['source_sha256'];im=bytearray(pam);word=lambda at:int.from_bytes(pam[at:at+2],'little');header=word(8)*16
  for i in range(word(6)):
   at=word(24)+i*4;off=header+word(at+2)*16+word(at);im[off:off+2]=((word(off)+0x1000)&65535).to_bytes(2,'little')
  for f in ida['functions']:
   for l in f['lines']:
    raw=bytes.fromhex(l['bytes']);assert im[l['file_offset']:l['file_offset']+len(raw)]==raw
  models=read(q/'casualty-models.json');assert models['status']=='passed-original-battle-casualty-models'and len(models['rows'])==18 and len(models['refusals'])==8
  catalog=read(q/'inputs/combat-catalog.json')['profiles']
  def record(v):
   hp=catalog[v['target']['Target']['unit']]['hp'];attack=catalog[v['target']['Source']['unit']]['attack'];n=v['target']['Source']['count'];encoded=attack*n//5//hp+1
   assert 1<=len(v['calls'])<=2 and all(c['damage']==attack*n//5 and c['encoded']==encoded for c in v['calls'])and v['updates']==1
   before=v['Before'];after=before if encoded==1 else (0 if encoded>=before else before-encoded+1);assert v['After']==after and v['Loss']==before-after
   display=[]
   if encoded>1:
    display=list(range(min(before,5),-1,-1))if after==0 else list(range(before if encoded<5 else before-encoded+5,after-1,-1))
   assert v['Display']==v['PlannedDisplay']and(v['Display']or[])==display
   return after
  for row in models['rows']:
   record(row['record']);assert row['held_retries']==5
   if row['id'].startswith('openkb:'):assert bytes.fromhex(row['native_hex'])==bytes(4)
  cold=read(q/'cold-receipt.json');assert cold['normal_cold_start']and not cold['snapshot_loaded']and cold['seed']==0x12345678
  for hd in [False,True]:
   rows=[v for v in cold['rows']if v['hd']==hd];assert len(rows)==2
   for key in ['units_hex','pending_hp_hex','frame_rgba_sha256','seed_after']:assert rows[0][key]==rows[1][key]
   assert len(rows[1]['record']['calls'])==2;record(rows[1]['record'])
   x=Image.open(q/'cold-r1'/f'hd-{str(hd).lower()}-mode-0/frame.png').convert('RGBA');y=Image.open(q/'cold-r1'/f'hd-{str(hd).lower()}-mode-1/frame.png').convert('RGBA');assert x.tobytes()==y.tobytes()and hashlib.sha256(x.tobytes()).hexdigest()==rows[0]['frame_rgba_sha256']
  expanded=read(q/'expanded-receipt.json');assert not expanded['playable']and not expanded['actual_window_verified']and len(expanded['rows'])==2
  for row in expanded['rows']:
   after=record(row['record']);assert row['rows'][0][0]['count']==after and len(row['record']['calls'])==2 and bytes.fromhex(row['native_rows_hex'])[:4]==bytes(4)and row['held_retries']==5 and row['controlled_enemy_first_argument']
   initial=row['record']['Before']*catalog['openkb:wolf']['hp'];assert row['pending_HP'][0][0]==max(0,initial-sum(v['damage']for v in row['record']['calls']))
   frame=Image.open(q/'expanded-r1'/str(row['case'])/'frame.png').convert('RGBA');assert hashlib.sha256(frame.tobytes()).hexdigest()==row['frame_rgba_sha256']
  assert expanded['rows'][0]['record']['After']==0 and expanded['rows'][1]['record']['After']>0
  assert(q/'tests-r1.log').read_text().rstrip().endswith('PASS')
  assert(q/'regression-r1.log').read_text().rstrip().endswith('PASS')and len(read(q/'models-r1.json')['refusals'])==19
  write(a.out,dict(status='passed-original-battle-casualties-audit',source_files=len(read(q/'source-manifest.json')),ida_functions=9,models=18,refusals=8,cold_native_HD_pairs=2,expanded_full_melee_cases=2,authoritative_updates_each=1,held_retries_each=5,native_projection_refusals=19,presence_regression=True,controlled_enemy_first_argument=True,new_ids_in_original_tables=0,ordinary_player_entry_disabled=True,not_verified=['expanded player turn/ranged/spells','next attack/complete battle','new unit hit/death poses','GUI','world save lifecycle']));return
 if a.action=='publish':
  import io
  from PIL import Image,ImageDraw,ImageFont
  assert read(r/'preserved/original-battle-casualties-audit-r1.json')['status']=='passed-original-battle-casualties-audit';idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),32,index=3)
  out=Image.new('RGB',(1920,750),'#11251f');draw=ImageDraw.Draw(out);receipt=read(q/'expanded-receipt.json');sources=[]
  for i,row in enumerate(receipt['rows']):
   v=row['record'];title=f"野狼 {v['Before']} → {v['After']}：Go結算一次";source=q/'expanded-r1'/str(i)/'frame.png';out.paste(Image.open(source).resize((960,600),Image.Resampling.NEAREST),(i*960,64));draw.text((i*960+20,10),title,font=font,fill='#fff1b5');sources.append(dict(path=str(source.relative_to(r)),sha256=sha(source),record=v))
  draw.text((24,679),'原版HD敵軍近戰；受控編成與敵先手。下一次行動前暫停，尚未開放完整戰鬥。',font=font.font_variant(size=26),fill='#fff1b5');dest=a.out/'original-battle-go-casualties-r1.png';assert not dest.exists();out.save(dest);write(a.out/'original-battle-go-casualties-r1.json',dict(schema=1,output_sha256=sha(dest),inputs=sources,actual_window_verified=False,playable=False,controlled_typed_override=True,controlled_enemy_first_argument=True,scope='First enemy melee complete; Go authoritative count only. New unit hit/death poses unimplemented.'));return
 if a.action=='archive':
  assert read(r/'preserved/original-battle-casualties-audit-r1.json')['status']=='passed-original-battle-casualties-audit';folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
  for f in sorted(q.rglob('*')):
   if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
   assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();digest=hashlib.sha256(raw).hexdigest();obj=folder/(digest+'.gz')
   if digest not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[digest]=dict(file=obj.name,stored_sha256=sha(obj))
   files.append(dict(path=str(f.relative_to(r)),bytes=len(raw),sha256=digest,mode=f.stat().st_mode&0o777))
  write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Full original data, frames, states and binaries local only. Expanded battle held after first enemy melee.'))
if __name__=='__main__':main()
