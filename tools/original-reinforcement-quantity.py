#!/usr/bin/env python3
"""Spec 030: extended-unit offers through the original four-digit editor."""
import argparse,ast,gzip,hashlib,importlib.util,json,os,shutil
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/original-reinforcement-quantity-r1'
BATCH='original-reinforcement-quantity-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','gui','audit','publish','archive','verify']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   o=d['objects'][f['sha256']];z=(a.archive/BATCH/o['file']).read_bytes();assert hashlib.sha256(z).hexdigest()==o['stored_sha256'];raw=gzip.decompress(z);assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-original-reinforcement-quantity',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL;s=importlib.util.spec_from_file_location('h',r/'tools/prepare-owned-army-ui.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h);deps=h.dependencies(r)
 if a.action=='gui':
  shutil.copytree(q/'initial-session',q/'gui-session');src=q/'source/internal/ownedworld/world-army-review_main.go';raw=src.read_text();guard='\tif !*nativeImportOnly {\n\t\treturn ErrOriginalBattlefieldPending\n\t}\n';assert raw.count(guard)==1;(q/'research-main.go').write_text(raw.replace(guard,'',1));write(q/'gui-overlay.json',dict(Replace={'/out/source/internal/ownedworld/world-army-review_main.go':'/out/research-main.go'}));return
 if a.action=='audit':
  from PIL import Image,__version__
  assert __version__=='11.3.0'and deps==read(q/'baseline.json')
  for n,digest in read(q/'source-manifest.json').items():assert sha(r/n)==sha(q/'source'/n)==digest,n
  run=read(q/'reinforcement-runtime-r1/receipt.json');assert run['status']=='passed-original-reinforcement-quantity-runtime'and run['native_purchases']==0 and run['native_stock']==3000 and run['cancel_unchanged']and run['invalid_unchanged']and run['cold_world_equal']
  catalog={u['id']:u for u in read(q/'inputs/army-catalog.json')['profiles']}
  assert len(run['models'])==8
  for m in run['models']:assert m['price']==catalog[m['unit']]['gold']and m['command']==catalog[m['unit']]['command']and m['limit']==(30000-m['used'])//m['command']
  w=run['final_world'];assert w['army']['slots'][:2]==[dict(unit='native:01',count=30),dict(unit='openkb:wolf',count=4)]and w['army']['gold']==420 and w['army']['offers']['reinforce:00:01:01:wolf']['stock']==73
  expected=json.loads(json.dumps(run['before_purchase_world']));expected['revision']+=1;expected['army']['gold']-=80;expected['army']['slots'][1]['count']+=2;expected['army']['offers']['reinforce:00:01:01:wolf']['stock']-=2;assert w==expected
  before=(q/'initial-session/gamedata.ay').read_bytes();after=(q/'reinforcement-runtime-r1/session/gamedata.ay').read_bytes();assert len(before)==len(after)==2987 and{i for i,(x,y)in enumerate(zip(before,after))if x!=y}<={6,7}
  for name in run['images']:assert Image.open(q/'reinforcement-runtime-r1'/(name+'.png')).size==(1920,1200)
  regression=read(q/'runtime-r1/receipt.json');assert regression['frames_equal']==7 and regression['cold_world_equal'];assert(q/'tests-final.log').read_text().rstrip().endswith('PASS')
  for name in ['prompt','editing-12','editing-1','editing-1234','ignored-fifth','reopened','confirm-1']:
   x=Image.open(q/'runtime-r1'/f'side-0-{name}.png').convert('RGBA');y=Image.open(q/'runtime-r1'/f'side-1-{name}.png').convert('RGBA');assert x.size==y.size==(1920,1200)and x.tobytes()==y.tobytes(),name
  gui=read(q/'gui-r1/receipt.json');assert gui['status']=='passed-original-reinforcement-quantity-GUI'and gui['program_sha256']==sha(q/'8sword-reinforcement-gui')and gui['cold_world_equal']
  assert read(q/'gui-r1/warm-receipt.json')['world']==w
  for row in gui['screenshots']:
   folder=q/'gui-r1'/row['phase'];meta=read(folder/row['metadata']);im=Image.open(folder/row['canvas']).convert('RGBA');screen=Image.open(folder/row['screen']).convert('RGB');assert im.size==screen.size==(1920,1200)and im.convert('RGB').tobytes()==screen.tobytes();assert hashlib.sha256(im.tobytes()).hexdigest()==meta['canvas_sha256']==meta['presented_sha256']
  entry=read(q/'production-entry-receipt.json');assert entry['status']=='passed'and entry['program_sha256']==sha(q/'8sword-owned')
  write(a.out,dict(status='passed-original-reinforcement-quantity-audit',source_files=len(read(q/'source-manifest.json')),models=8,runtime_frames=len(run['images']),gui_frames=len(gui['screenshots']),native_regression_frames=14,cold_world_equal=True,native_stock=3000,independent_wolf_stock=73,controlled_army=True,full_guest_state_parity_claimed=False,ordinary_entry_disabled=True));return
 if a.action=='publish':
  import io
  from PIL import Image,ImageDraw,ImageFont
  assert read(r/'preserved/original-reinforcement-quantity-audit-r1.json')['status']=='passed-original-reinforcement-quantity-audit';idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),36,index=3);out=Image.new('RGB',(1920,720),'#11251f');draw=ImageDraw.Draw(out);sources=[];gui=read(q/'gui-r1/receipt.json')
  for i,(name,title)in enumerate([('wolf-confirm-2','新增野狼・原版數量輸入'),('cold-f2-lishu','購兵冷讀・原版軍隊頁')]):
   row=next(x for x in gui['screenshots']if x['name']==name);folder=q/'gui-r1'/row['phase'];p=folder/row['canvas'];meta=folder/row['metadata'];out.paste(Image.open(p).resize((960,600),Image.Resampling.NEAREST),(i*960,64));draw.text((i*960+24,8),title,font=font,fill='#fff1b5');sources.append(dict(path=str(p.relative_to(r)),sha256=sha(p),metadata_sha256=sha(meta)))
  draw.text((24,673),'招募2野狼：2→4，金500→420；原店民兵庫存3000保持。明示測試軍隊。',font=font.font_variant(size=24),fill='#fff1b5');p=a.out/'original-reinforcement-quantity-go-r1.png';assert not p.exists();out.save(p);write(a.out/'original-reinforcement-quantity-go-r1.json',dict(schema=1,output=p.name,output_sha256=sha(p),inputs=sources,audit_sha256=sha(r/'preserved/original-reinforcement-quantity-audit-r1.json'),controlled_army=True,actual_window_verified=True,clock_initial='12:00 via Oracle.SetClock; live3000 cycles/ms',rng_comparison='No random outcome compared',full_guest_state_parity_claimed=False));return
 if a.action=='archive':
  assert read(r/'preserved/original-reinforcement-quantity-audit-r1.json')['status']=='passed-original-reinforcement-quantity-audit';folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
  for f in sorted(q.rglob('*')):
   if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
   assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();hsh=hashlib.sha256(raw).hexdigest();obj=folder/(hsh+'.gz')
   if hsh not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[hsh]=dict(file=obj.name,stored_sha256=sha(obj))
   files.append(dict(path=str(f.relative_to(r)),bytes=len(raw),sha256=hsh,mode=f.stat().st_mode&0o777))
  write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Original data, complete artwork and binaries local only; ordinary entry remains disabled.'));return
 if a.action=='prepare':
  assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir()
  for n in ['inputs','ui-assets','initial-session']:(q/n).mkdir()
  parent=read(r/'preserved/original-recruit-quantity-r1.json')
  for row in parent['files']:
   path=row['path'];mark='/original-recruit-quantity-r1/';name=path.split(mark,1)[1]
   if name in ['probe.mod','probe.sum','xcheck']or name.startswith(('inputs/','ui-assets/','runtime-r1/initial-session/')):
    dst=q/name.replace('runtime-r1/initial-session/','initial-session/');dst.write_bytes(h.stored(r,'original-recruit-quantity-r1',mark+name));dst.chmod(row['mode'])
  write(q/'baseline.json',deps)
 else:assert q.is_dir()and read(q/'baseline.json')==deps
 names=set(read(r/'preserved/owned-player-source-manifest-r1.json'))|{str(p.relative_to(r))for p in(r/'internal/ownedworld').glob('*.go')}
 for n in sorted(names):
  dst=q/'source'/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,dst)
 (q/'source-manifest.json').write_text(json.dumps({n:sha(q/'source'/n)for n in sorted(names)},ensure_ascii=False,indent=2)+'\n')
 shutil.copyfile(Path(__file__),q/Path(__file__).name)
if __name__=='__main__':main()
