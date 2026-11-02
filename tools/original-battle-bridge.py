#!/usr/bin/env python3
"""Spec030: original battle control evidence and bounded Go arithmetic bridge."""
import argparse,ast,gzip,hashlib,importlib.util,json,os,shutil
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/original-battle-bridge-r1'
BATCH='original-battle-bridge-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','audit','publish','archive','verify']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   o=d['objects'][f['sha256']];z=(a.archive/BATCH/o['file']).read_bytes();assert hashlib.sha256(z).hexdigest()==o['stored_sha256'];raw=gzip.decompress(z);assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-original-battle-bridge',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL;s=importlib.util.spec_from_file_location('h',r/'tools/prepare-owned-army-ui.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h);deps=h.dependencies(r)
 if a.action=='audit':
  from PIL import Image,__version__
  assert __version__=='11.3.0'and deps==read(q/'baseline.json')
  for n,digest in read(q/'source-manifest.json').items():assert sha(r/n)==sha(q/'source'/n)==digest,n
  ida=read(q/'ida/ida-battle-bridge-r1.json');assert ida['function_count']==521 and ida['exporter_sha256']==sha(r/'tools/export-original-battle-bridge-ida.py')
  pam=(q/'inputs/PAM.AY').read_bytes();image=bytearray(pam);u16=lambda at:int.from_bytes(pam[at:at+2],'little');header=u16(8)*16
  for i in range(u16(6)):
   entry=u16(24)+i*4;at=header+u16(entry+2)*16+u16(entry);image[at:at+2]=((u16(at)+0x1000)&65535).to_bytes(2,'little')
  for f in ida['functions']:
   for line in f['lines']:
    raw=bytes.fromhex(line['bytes']);assert image[line['file_offset']:line['file_offset']+len(raw)]==raw,line
  controls=read(q/'helper-controls-r1/receipt.json');assert controls['status']=='passed-original-battle-helper-controls'and len(controls['cases'])==8 and controls['seed']==0x12345678
  catalog=read(q/'inputs/combat-catalog.json')['profiles']
  for c in controls['cases']:
   v=c['go'];ap=catalog['native:%02d'%v['SourceKind']]['attack'];hp=catalog['native:%02d'%v['TargetKind']]['hp'];amount=ap*v['SourceCount']//v['Divisor']*v['Multiplier'];assert v['Damage']==amount and v['Encoded']==amount//hp+1==c['native_ax']and v['AfterHP']==(v['BeforeHP']-amount)%65536==c['native_hp']
  refusals=read(q/'refusals-r1.json');assert refusals['status']=='passed-original-battle-refusals'and len(refusals['cases'])==10 and refusals['no_state_change']and refusals['formation_rejected'];wide=refusals['wide_model'];assert wide['damage']==wide['attack']*wide['count']//wide['divisor']*wide['multiplier']==60000 and wide['encoded']==wide['damage']//wide['hp']+1==3001
  action=read(q/'action-r1/receipt.json');assert action['status']=='passed-original-battle-action'and len(action['rows'])==4 and all(x['normal_cold_start']and not x['controlled_snapshot']for x in action['rows'])
  for hd in [False,True]:
   rows=[x for x in action['rows']if x['hd']==hd];assert rows[0]['units']==rows[1]['units']and rows[0]['pending_hp']==rows[1]['pending_hp']and rows[0]['frame_sha256']==rows[1]['frame_sha256']and rows[0]['seed_after']==rows[1]['seed_after'];assert len(rows[1]['calls'])==len(rows[0]['native_calls'])>0
   for native,go in zip(rows[0]['native_calls'],rows[1]['calls']):assert native['source']==go['Source']and native['target']==go['Target']and native['before_hp']==go['BeforeHP']and native['after_hp']==go['AfterHP']and native['encoded']==go['Encoded']
   x=Image.open(q/'action-r1'/f'hd-{str(hd).lower()}-mode-0/frame.png').convert('RGBA');y=Image.open(q/'action-r1'/f'hd-{str(hd).lower()}-mode-1/frame.png').convert('RGBA');assert x.size==y.size and x.tobytes()==y.tobytes()
  assert(q/'tests-cold-r3.log').read_text().rstrip().endswith('PASS')and(q/'tests-refusals-final.log').read_text().rstrip().endswith('PASS')
  write(a.out,dict(status='passed-original-battle-bridge-audit',source_files=len(read(q/'source-manifest.json')),ida_functions=len(ida['functions']),helper_pairs=8,action_pairs=2,refusal_cases=10,formation_rejected=True,original_and_hd_frames_equal=True,fixed_original_seed=0x12345678,helper_controlled_snapshot=True,action_snapshot_loaded=False,action_normal_cold_start=True,ordinary_owned_player_entry_disabled=True,not_verified=['GUI','Go-world army entry and battle save lifecycle','extended IDs in original battlefield','formation/tactics bridge','natural player attack and all spells']));return
 if a.action=='publish':
  import io
  from PIL import Image,ImageDraw,ImageFont
  assert read(r/'preserved/original-battle-bridge-audit-r1.json')['status']=='passed-original-battle-bridge-audit';idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),36,index=3);out=Image.new('RGB',(1920,720),'#11251f');draw=ImageDraw.Draw(out);sources=[]
  for i,(hd,title)in enumerate([(False,'原版戰場・Go傷害計算'),(True,'HD原戰場・Go傷害計算')]):
   p=q/'action-r1'/f'hd-{str(hd).lower()}-mode-1/frame.png';im=Image.open(p);out.paste(im.resize((960,600),Image.Resampling.NEAREST),(i*960,64));draw.text((i*960+24,8),title,font=font,fill='#fff1b5');sources.append(dict(path=str(p.relative_to(r)),sha256=sha(p),dimensions=list(im.size)))
  draw.text((24,675),'冷啟動、正常走路遇敵，固定相同seed；至首個敵方普通行動返回。未驗GUI及Go戰果保存。',font=font.font_variant(size=24),fill='#fff1b5');p=a.out/'original-battle-go-arithmetic-r1.png';assert not p.exists();out.save(p);write(a.out/'original-battle-go-arithmetic-r1.json',dict(schema=1,output=p.name,output_sha256=sha(p),inputs=sources,audit_sha256=sha(r/'preserved/original-battle-bridge-audit-r1.json'),original_seed=0x12345678,controlled_snapshot=False,normal_cold_start=True,actual_window_verified=False,full_guest_state_parity_claimed=False));return
 if a.action=='archive':
  assert read(r/'preserved/original-battle-bridge-audit-r1.json')['status']=='passed-original-battle-bridge-audit';folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
  for f in sorted(q.rglob('*')):
   if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
   assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();hsh=hashlib.sha256(raw).hexdigest();obj=folder/(hsh+'.gz')
   if hsh not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[hsh]=dict(file=obj.name,stored_sha256=sha(obj))
   files.append(dict(path=str(f.relative_to(r)),bytes=len(raw),sha256=hsh,mode=f.stat().st_mode&0o777))
  write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Original data, full graphics and binaries local only; ordinary player entry remains disabled.'));return
 if a.action=='prepare':
  assert q.is_dir()and not(q/'inputs').exists();(q/'inputs').mkdir()
  for n in ['probe.mod','probe.sum']:(q/n).write_bytes(h.stored(r,'owned-player-r1','/owned-player-r1/'+n))
  for n in ['army-catalog.json','combat-catalog.json','PAM.AY']:(q/'inputs'/n).write_bytes(h.stored(r,'owned-player-r1','/owned-player-r1/inputs/'+n))
  d=read(r/'preserved/ai-observation-r1.json');row=next(x for x in d['files']if x['path']=='input-multi-r1/choi-hd-r1/multi-ready-before.state');z=(r/'preserved/ai-observation-r1'/row['stored']).read_bytes();assert hashlib.sha256(z).hexdigest()==row['stored_sha256'];raw=gzip.decompress(z);assert hashlib.sha256(raw).hexdigest()==row['sha256']and len(raw)==row['bytes'];(q/'inputs/start.state').write_bytes(raw);write(q/'snapshot-source.json',row);write(q/'baseline.json',deps)
 else:assert q.is_dir()and read(q/'baseline.json')==deps
 names=set(read(r/'preserved/owned-player-source-manifest-r1.json'))|{str(p.relative_to(r))for p in(r/'internal/ownedworld').glob('*.go')}
 for n in sorted(names):
  dst=q/'source'/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,dst)
 (q/'source-manifest.json').write_text(json.dumps({n:sha(q/'source'/n)for n in sorted(names)},ensure_ascii=False,indent=2)+'\n')
 for n in ['original-battle-bridge.py','export-original-battle-bridge-ida.py']:shutil.copyfile(r/'tools'/n,q/n)
if __name__=='__main__':main()
