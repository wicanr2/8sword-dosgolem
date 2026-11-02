#!/usr/bin/env python3
"""Spec030 original battlefield six-stack projection: prepare, audit and preserve."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/original-army-projection-r1'
BATCH='original-army-projection-r1'
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
  write(a.out,dict(status='passed-detached-original-army-projection',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL;s=importlib.util.spec_from_file_location('h',r/'tools/prepare-owned-army-ui.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h);deps=h.dependencies(r)
 if a.action=='prepare':
  assert q.is_dir()and not(q/'inputs').exists();(q/'inputs').mkdir();parent=q.parent/'original-battle-bridge-r1'
  for n in ['probe.mod','probe.sum']:shutil.copyfile(parent/n,q/n)
  for n in ['army-catalog.json','combat-catalog.json','PAM.AY']:shutil.copyfile(parent/'inputs'/n,q/'inputs'/n)
  write(q/'baseline.json',deps)
 if a.action in ['prepare','freeze']:
  assert read(q/'baseline.json')==deps
  names=set(read(r/'preserved/owned-player-source-manifest-r1.json'))|{str(p.relative_to(r))for p in(r/'internal/ownedworld').glob('*.go')}
  for n in sorted(names):
   dst=q/'source'/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,dst)
  (q/'source-manifest.json').write_text(json.dumps({n:sha(q/'source'/n)for n in sorted(names)},ensure_ascii=False,indent=2)+'\n')
  for n in ['original-army-projection.py','export-original-army-projection-ida.py']:shutil.copyfile(r/'tools'/n,q/n)
  return
 if a.action=='publish':
  import io
  from PIL import Image,ImageDraw,ImageFont
  assert read(r/'preserved/original-army-projection-audit-r1.json')['status']=='passed-original-army-projection-audit';idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),36,index=3);out=Image.new('RGB',(1920,760),'#11251f');draw=ImageDraw.Draw(out);sources=[]
  for i,(hd,title)in enumerate([(False,'原版戰場・Go六隊資料'),(True,'HD原戰場・Go六隊資料')]):
   f=q/'projection-action-r1'/f'hd-{str(hd).lower()}-mode-1/frame.png';im=Image.open(f);out.paste(im.resize((960,600),Image.Resampling.NEAREST),(i*960,64));draw.text((i*960+24,8),title,font=font,fill='#fff1b5');sources.append(dict(path=str(f.relative_to(r)),sha256=sha(f),dimensions=list(im.size)))
  draw.text((24,675),'首個敵方行動畫面。正常Esc返回：30民兵剩16，Go進度保存／冷讀一致；原軍隊影子保持。',font=font.font_variant(size=25),fill='#fff1b5')
  draw.text((24,715),'固定seed 0x12345678；Engine畫面。僅原25種資料橋接，新增兵種與完整世界戰果尚未接入。',font=font.font_variant(size=24),fill='#fff1b5');f=a.out/'original-army-projection-r1.png';assert not f.exists();out.save(f);write(a.out/'original-army-projection-r1.json',dict(schema=1,output=f.name,output_sha256=sha(f),inputs=sources,audit_sha256=sha(r/'preserved/original-army-projection-audit-r1.json'),seed=0x12345678,normal_cold_start=True,actual_window_verified=False,scope='Original25 projection, ordinary action and Escape return; partial typed remainder store, not complete world settlement.'));return
 if a.action=='archive':
  assert read(r/'preserved/original-army-projection-audit-r1.json')['status']=='passed-original-army-projection-audit';folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
  for f in sorted(q.rglob('*')):
   if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
   assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();hsh=hashlib.sha256(raw).hexdigest();obj=folder/(hsh+'.gz')
   if hsh not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[hsh]=dict(file=obj.name,stored_sha256=sha(obj))
   files.append(dict(path=str(f.relative_to(r)),bytes=len(raw),sha256=hsh,mode=f.stat().st_mode&0o777))
  write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Original data, full frames and binaries local only; ordinary player entry disabled.'));return
 if a.action=='audit':
  from PIL import Image,__version__
  assert __version__=='11.3.0'and deps==read(q/'baseline.json')
  for n,digest in read(q/'source-manifest.json').items():assert sha(r/n)==sha(q/'source'/n)==digest,n
  ida=read(q/'ida/ida-projection.json');assert ida['function_count']==521 and ida['exporter_sha256']==sha(r/'tools/export-original-army-projection-ida.py')
  pam=(q/'inputs/PAM.AY').read_bytes();image=bytearray(pam);u16=lambda at:int.from_bytes(pam[at:at+2],'little');header=u16(8)*16
  for i in range(u16(6)):
   entry=u16(24)+i*4;at=header+u16(entry+2)*16+u16(entry);image[at:at+2]=((u16(at)+0x1000)&65535).to_bytes(2,'little')
  for f in ida['functions']:
   for line in f['lines']:
    raw=bytes.fromhex(line['bytes']);assert image[line['file_offset']:line['file_offset']+len(raw)]==raw,line
  m=read(q/'models-r1.json');assert m['status']=='passed-original-army-projection-models'and m['six_slots']and m['shadow_unchanged']and len(m['refusals'])>=10
  d=read(q/'projection-action-r1/receipt.json');assert d['status']=='passed-original-army-projection-action'and len(d['rows'])==4
  for hd in [False,True]:
   rows=[x for x in d['rows']if x['hd']==hd];a0,a1=rows;assert a0['mode']==0 and a1['mode']==1
   for k in ['units','pending_hp','frame_sha256','seed_after','return_seed','remaining','battle_result']:assert a0[k]==a1[k],k
   assert a1['shadow_before']==a1['shadow_after']and a1['copies']==a1['captures']==1 and a1['store_cold_read']and a1['native_file_unchanged']
   raw=bytes.fromhex(a0['shadow_after']);decoded=[]
   for i in range(6):
    k=int.from_bytes(raw[i*4:i*4+2],'little');n=int.from_bytes(raw[i*4+2:i*4+4],'little');decoded.append(dict(unit='native:%02d'%k if k else '',count=n))
   assert decoded==a1['remaining']and decoded[0]==dict(unit='native:01',count=16)
   prefix=q/'projection-action-r1';s0=read(prefix/f'hd-{str(hd).lower()}-mode-0/session/gamedata.ay.army.json');s1=read(prefix/f'hd-{str(hd).lower()}-mode-1/session/gamedata.ay.army.json')
   for mode,saved in [(0,s0),(1,s1)]:
    native=prefix/f'hd-{str(hd).lower()}-mode-{mode}/session/gamedata.ay';assert saved['schema']=='eightsword-owned-world-save/5'and saved['original_sha256']==sha(native)=='84fb0c8f5e4645954160eea8de45d030d7efd632cdb3dafa896f7c4e9c626eef'
   s0['world']['revision']+=1;s0['world']['army']['slots']=decoded;assert s0==s1
   x=Image.open(q/'projection-action-r1'/f'hd-{str(hd).lower()}-mode-0/frame.png').convert('RGBA');y=Image.open(q/'projection-action-r1'/f'hd-{str(hd).lower()}-mode-1/frame.png').convert('RGBA');assert x.size==y.size==(1920,1200)and x.tobytes()==y.tobytes()
  assert(q/'tests-r1.log').read_text().rstrip().endswith('PASS')
  write(a.out,dict(status='passed-original-army-projection-audit',source_files=len(read(q/'source-manifest.json')),ida_functions=len(ida['functions']),six_slot_model=True,refusals=m['refusals'],cold_start_pairs=2,full_frames_equal=True,normal_escape_return=True,typed_remainder_saved_and_cold_read=True,native_shadow_and_file_unchanged=True,seed=0x12345678,ordinary_player_entry_disabled=True,not_verified=['expanded IDs in original battlefield','all actions/formation/tactics','complete world result settlement','GUI','normal F7 integration']))
if __name__=='__main__':main()
