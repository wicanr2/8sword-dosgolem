#!/usr/bin/env python3
"""Prepare the bounded original recruitment quantity study (spec 030)."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/original-recruit-quantity-r1'
BATCH='original-recruit-quantity-r1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','gui','audit','publish','archive','verify']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   o=d['objects'][f['sha256']];z=(a.archive/BATCH/o['file']).read_bytes();assert hashlib.sha256(z).hexdigest()==o['stored_sha256'];raw=gzip.decompress(z);assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-original-recruit-quantity',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL;s=importlib.util.spec_from_file_location('h',r/'tools/prepare-owned-army-ui.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h);deps=h.dependencies(r)
 if a.action=='gui':
  assert read(q/'runtime-r1/receipt.json')['status']=='passed-original-recruit-quantity-runtime';shutil.copytree(q/'runtime-r1/initial-session',q/'gui-session')
  src=q/'source/internal/ownedworld/world-army-review_main.go';raw=src.read_text();guard='\tif !*nativeImportOnly {\n\t\treturn ErrOriginalBattlefieldPending\n\t}\n';assert raw.count(guard)==1;(q/'research-main.go').write_text(raw.replace(guard,'',1));write(q/'gui-overlay.json',dict(Replace={'/out/source/internal/ownedworld/world-army-review_main.go':'/out/research-main.go'}));write(q/'gui-overlay-notice.json',dict(research_only=True,change='Only remove the ordinary startup guard. Controlled army, original keyboard and numeric editor; no GUI RAM/IP injection.'));return
 if a.action=='audit':
  from PIL import Image,__version__
  assert __version__=='11.3.0'and deps==read(q/'baseline.json')
  for n,digest in read(q/'source-manifest.json').items():assert sha(r/n)==sha(q/'source'/n)==digest,n
  ida=read(q/'ida/ida-recruit-quantity-r1.json');assert ida['function_count']==521 and ida['exporter_sha256']==sha(r/'tools/export-original-recruit-quantity-ida.py')
  pam=(q/'inputs/PAM.AY').read_bytes();ida_image=bytearray(pam);u16=lambda off:int.from_bytes(pam[off:off+2],'little');header=u16(8)*16
  # IDA's MZ loader applies linear base 0x10000, adding segment 1000h at
  # relocation words. File offsets remain explicit and are checked separately.
  for i in range(u16(6)):
   entry=u16(24)+i*4;at=header+u16(entry+2)*16+u16(entry);value=(u16(at)+0x1000)&65535;ida_image[at:at+2]=value.to_bytes(2,'little')
  for f in ida['functions']:
   for line in f['lines']:
    raw=bytes.fromhex(line['bytes']);assert ida_image[line['file_offset']:line['file_offset']+len(raw)]==raw,line
  model=read(q/'models-r1/receipt.json');assert model['status']=='passed-original-recruit-models'and model['true_cost']==72000 and model['native_low_word']==6464 and model['boundary_gold_after']==0
  catalog={x['native_kind']:x for x in read(q/'inputs/army-catalog.json')['profiles']if x['origin']=='native'}
  for p in model['models']:assert p['price']==catalog[p['kind']]['gold']and p['command']==catalog[p['kind']]['command']and p['limit']==30000//p['command']
  run=read(q/'runtime-r1/receipt.json');assert run['status']=='passed-original-recruit-quantity-runtime'and run['frames_equal']==7 and run['cold_world_equal']
  stages=['prompt','editing-12','editing-1','editing-1234','ignored-fifth','reopened','confirm-1']
  for name in stages:
   x=Image.open(q/'runtime-r1'/f'side-0-{name}.png').convert('RGBA');y=Image.open(q/'runtime-r1'/f'side-1-{name}.png').convert('RGBA');assert x.size==y.size==(1920,1200)and x.tobytes()==y.tobytes(),name
  expected=json.loads(json.dumps(run['initial_world']));expected['revision']+=2;expected['army']['gold']-=1;expected['army']['slots'][0]['count']+=1;expected['army']['offers']['native-camp:00:01']=dict(unit='native:01',stock=2999);assert run['final_world']==expected
  before=(q/'runtime-r1/initial-session/gamedata.ay').read_bytes();after=(q/'runtime-r1/session/gamedata.ay').read_bytes();assert len(before)==len(after)==2987 and before[12:36]==after[12:36]
  assert {i for i,(x,y)in enumerate(zip(before,after))if x!=y}<={6,7,126,127}
  # Camp stock offset is interleaved across five tables: 76 + row*50 + group*2.
  assert int.from_bytes(after[126:128],'little')-129==2999
  gui=read(q/'gui-r1/receipt.json');assert gui['status']=='passed-original-recruit-quantity-GUI'and gui['cold_world_equal']and gui['program_sha256']==sha(q/'8sword-quantity-gui')
  for row in gui['screenshots']:
   folder=q/'gui-r1'/row['phase'];meta=read(folder/row['metadata']);im=Image.open(folder/row['canvas']).convert('RGBA');screen=Image.open(folder/row['screen']).convert('RGB');assert im.size==screen.size==(1920,1200)and im.convert('RGB').tobytes()==screen.tobytes();assert hashlib.sha256(im.tobytes()).hexdigest()==meta['canvas_sha256']==meta['presented_sha256']
  assert(q/'tests-final-r3.log').read_text().rstrip().endswith('PASS')
  entry=read(q/'production-entry-receipt.json');assert entry['status']=='passed'and entry['program_sha256']==sha(q/'8sword-owned')
  write(a.out,dict(status='passed-original-recruit-quantity-audit',source_files=len(read(q/'source-manifest.json')),ida_functions=4,source_instructions=sum(len(f['lines'])for f in ida['functions']),model_profiles=25,control_frames=14,gui_frames=len(gui['screenshots']),four_digit_editor_preserved=True,true_cost=72000,native_low_word=6464,controlled_army=True,full_guest_state_parity_claimed=False,production_entry_remains_disabled=True));return
 if a.action=='publish':
  import io
  from PIL import Image,ImageDraw,ImageFont
  assert read(r/'preserved/original-recruit-quantity-audit-r1.json')['status']=='passed-original-recruit-quantity-audit';idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));raw=gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes());font=ImageFont.truetype(io.BytesIO(raw),36,index=3);small=ImageFont.truetype(io.BytesIO(raw),24,index=3);out=Image.new('RGB',(1920,720),'#11251f');draw=ImageDraw.Draw(out);sources=[];gui=read(q/'gui-r1/receipt.json')
  for i,(name,title)in enumerate([('shop-input-lishu','原版數量輸入・Go計算'),('cold-f2-lishu','購兵冷讀・Go軍隊資料')]):
   row=next(x for x in gui['screenshots']if x['name']==name);folder=q/'gui-r1'/row['phase'];p=folder/row['canvas'];meta=folder/row['metadata'];im=Image.open(p);out.paste(im.resize((960,600),Image.Resampling.NEAREST),(i*960,64));draw.text((i*960+24,8),title,font=font,fill='#fff1b5');sources.append(dict(path=str(p.relative_to(r)),sha256=sha(p),metadata_path=str(meta.relative_to(r)),metadata_sha256=sha(meta)))
  draw.text((24,675),'原店購1民兵：30→31，另有2野狼；金500→499。明示軍隊測試配置。',font=small,fill='#fff1b5');p=a.out/'original-recruit-quantity-go-r1.png';assert not p.exists();out.save(p);write(a.out/'original-recruit-quantity-go-r1.json',dict(schema=1,output=p.name,output_sha256=sha(p),inputs=sources,audit_sha256=sha(r/'preserved/original-recruit-quantity-audit-r1.json'),clock_initial='12:00:00.00 via Oracle.SetClock; live 3000 cycles/ms',rng_comparison='No random outcome compared',controlled_army=True,actual_window_verified=True,full_guest_state_parity_claimed=False));return
 if a.action=='archive':
  assert read(r/'preserved/original-recruit-quantity-audit-r1.json')['status']=='passed-original-recruit-quantity-audit';folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
  for f in sorted(q.rglob('*')):
   if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
   assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();hsh=hashlib.sha256(raw).hexdigest();obj=folder/(hsh+'.gz')
   if hsh not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[hsh]=dict(file=obj.name,stored_sha256=sha(obj))
   files.append(dict(path=str(f.relative_to(r)),bytes=len(raw),sha256=hsh,mode=f.stat().st_mode&0o777))
  write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Original data, complete artwork and binaries local only. Ordinary player entry remains disabled.'));return
 if a.action=='prepare':
  assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir();(q/'inputs').mkdir();(q/'ui-assets').mkdir();(q/'ida').mkdir()
  for n in ['probe.mod','probe.sum']:(q/n).write_bytes(h.stored(r,'owned-player-r1','/owned-player-r1/'+n))
  for n in ['army-catalog.json','combat-catalog.json','PAM.AY','origin-terrain-packed.ay','map01.ay']:(q/'inputs'/n).write_bytes(h.stored(r,'owned-player-r1','/owned-player-r1/inputs/'+n))
  for row in read(r/'preserved/owned-player-r1.json')['files']:
   marker='/owned-player-r1/ui-assets/'
   if marker in row['path']:(q/'ui-assets'/row['path'].split(marker,1)[1]).write_bytes(h.stored(r,'owned-player-r1',marker+row['path'].split(marker,1)[1]))
  (q/'xcheck').write_bytes(h.stored(r,'owned-player-r1','/owned-player-r1/xcheck'));(q/'xcheck').chmod(493);write(q/'baseline.json',deps)
 else:assert q.is_dir()and read(q/'baseline.json')==deps
 names=set(read(r/'preserved/owned-player-source-manifest-r1.json'))|{str(p.relative_to(r))for p in(r/'internal/ownedworld').glob('*.go')}
 for n in sorted(names):
  dst=q/'source'/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,dst)
 (q/'source-manifest.json').write_text(json.dumps({n:sha(q/'source'/n)for n in sorted(names)},ensure_ascii=False,indent=2)+'\n')
 for n in ['original-recruit-quantity.py','export-original-recruit-quantity-ida.py']:shutil.copyfile(r/'tools'/n,q/n)
if __name__=='__main__':main()
