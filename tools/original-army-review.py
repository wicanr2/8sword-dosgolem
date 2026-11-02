#!/usr/bin/env python3
"""Prepare and preserve the original F2 / Go data bridge candidate."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/original-army-review-r1'
BATCH='original-army-review-r1'
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
  write(a.out,dict(status='passed-detached-original-army-review',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL;s=importlib.util.spec_from_file_location('h',r/'tools/prepare-owned-army-ui.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h);deps=h.dependencies(r)
 if a.action=='publish':
  import io
  from PIL import Image,ImageDraw,ImageFont,__version__
  assert __version__=='11.3.0'and read(r/'preserved/original-army-review-audit-r1.json')['status']=='passed-original-F2-Go-data-audit'
  assert a.out.is_dir()and a.out.stat().st_uid==1000
  idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));fontsha=h.FONT_SHA['noto'];raw=gzip.decompress((r/'preserved'/idx['objects'][fontsha]['path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==fontsha
  font=ImageFont.truetype(io.BytesIO(raw),36,index=3);small=ImageFont.truetype(io.BytesIO(raw),24,index=3);out=Image.new('RGB',(1920,720),'#11251f');draw=ImageDraw.Draw(out);sources=[]
  gui=read(q/'gui-r1/receipt.json');pic=q/'gui-r1'/gui['screenshots'][0]['canvas'];assert read(q/'gui-r1'/gui['screenshots'][0]['metadata'])['font_id']=='noto'
  for i,(label,path)in enumerate([('原版・Go資料',q/'runtime-hd-false/side-1.png'),('HD・Go資料',pic)]):
   im=Image.open(path).convert('RGB');assert im.size==(1920,1200);out.paste(im.resize((960,600),Image.Resampling.NEAREST),(i*960,64));draw.text((i*960+24,8),label,font=font,fill='#fff1b5');sources.append(dict(path=str(path.relative_to(r)),sha256=sha(path)))
  draw.text((24,675),'Go軍隊：31民兵＋1矮人；原影子軍隊仍是30民兵。明示測試配置。',font=small,fill='#fff1b5')
  path=a.out/'original-army-go-data-r1.png';assert not path.exists();out.save(path)
  write(a.out/'original-army-go-data-r1.json',dict(schema=1,output=path.name,output_sha256=sha(path),inputs=sources,audit_sha256=sha(r/'preserved/original-army-review-audit-r1.json'),controlled_army=True,clock_initial='12:00:00.00 via Oracle.SetClock',native_save_sha256=gui['save_pair_unchanged']['gamedata.ay'],comparison='Original/HD presentation of equivalent Go army data; each mode separately matched its original control frame',full_guest_state_parity_claimed=False,hd_actual_window_verified=True,extended_kind_presentation=False,original_clock_parity_claimed=False));return
 if a.action=='audit':
  from PIL import Image,__version__
  assert __version__=='11.3.0'and deps==read(q/'baseline.json')
  for n,hsh in read(q/'source-manifest.json').items():assert sha(r/n)==hsh and sha(q/'source'/n)==hsh,n
  results=[]
  for hd in ['false','true']:
   folder=q/('runtime-hd-'+hd);receipt=read(folder/'receipt.json');control=Image.open(folder/'side-0.png').convert('RGBA');owned=Image.open(folder/'side-1.png').convert('RGBA')
   assert control.size==owned.size==(1920,1200)and control.tobytes()==owned.tobytes();assert hashlib.sha256(owned.tobytes()).hexdigest()==receipt['frame_sha256'];assert receipt['save_pair_unchanged']and receipt['stale_and_source_rejected'];assert receipt['native_shadow_hex']=='01001e000000000000000000000000000000000000000000'and receipt['wait_boundary']=='0110:844C/return-3ED8'
   if hd=='true':assert 'Go data operation did not commit'in receipt['disabled_data_hook_refused']
   results.append(receipt)
  gui=read(q/'gui-r1/receipt.json');assert gui['status']=='passed-original-F2-Go-data-GUI'and gui['waits_for_original_panel_commit']and gui['program_sha256']==sha(q/'8sword-review-gui');shots=[]
  for row in gui['screenshots']:
   folder=q/'gui-r1';meta=read(folder/row['metadata']);png=Image.open(folder/row['canvas']).convert('RGBA');screen=Image.open(folder/row['screen']).convert('RGB');assert png.size==screen.size==(1920,1200)and png.convert('RGB').tobytes()==screen.tobytes();assert hashlib.sha256(png.tobytes()).hexdigest()==meta['canvas_sha256']==meta['presented_sha256']
   if meta['view']=='army':assert meta['original_review_ready']and meta['original_review_rows'][:2]==[dict(Kind=1,Count=31,Monthly=31),dict(Kind=21,Count=1,Monthly=1)]
   shots.append(dict(name=row['name'],rgba_sha256=meta['canvas_sha256']))
  assert(q/'tests-r3.log').read_text().rstrip().endswith('PASS');assert read(q/'gui-overlay-notice.json')['production_entry_remains_disabled']
  entry=read(q/'production-entry-receipt.json');assert entry['status']=='passed'and entry['program_sha256']==sha(q/'8sword-owned')
  write(a.out,dict(status='passed-original-F2-Go-data-audit',source_files=len(read(q/'source-manifest.json')),runtime=results,gui=shots,production_entry_remains_disabled=True,extended_kind_presentation=False,original_clock_parity_claimed=False));return
 if a.action=='gui':
  assert read(q/'runtime-hd-true/receipt.json')['full_frame_equal'];shutil.copytree(q/'runtime-hd-true/session',q/'gui-session');(q/'ui-assets').mkdir()
  for f in read(r/'preserved/owned-player-r1.json')['files']:
   marker='/owned-player-r1/ui-assets/'
   if marker in f['path']:(q/'ui-assets'/f['path'].split(marker,1)[1]).write_bytes(h.stored(r,'owned-player-r1',marker+f['path'].split(marker,1)[1]))
  for n in ['origin-terrain-packed.ay','map01.ay']:(q/'inputs'/n).write_bytes(h.stored(r,'owned-player-r1','/owned-player-r1/inputs/'+n))
  (q/'xcheck').write_bytes(h.stored(r,'owned-player-r1','/owned-player-r1/xcheck'));(q/'xcheck').chmod(493)
  src=q/'source/internal/ownedworld/world-army-review_main.go';raw=src.read_text();guard='\tif !*nativeImportOnly {\n\t\treturn ErrOriginalBattlefieldPending\n\t}\n';assert raw.count(guard)==1
  replacement=q/'research-main.go';replacement.write_text(raw.replace(guard,'',1));write(q/'gui-overlay.json',dict(Replace={'/out/source/internal/ownedworld/world-army-review_main.go':'/out/research-main.go'}));write(q/'gui-overlay-notice.json',dict(research_only=True,production_entry_remains_disabled=True,change='Remove only the startup guard for the bounded F2 GUI check. No army, input, IP or battle injection.'));return
 if a.action in ['prepare','freeze']:
  if a.action=='prepare':
   assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir();(q/'inputs').mkdir()
  else:assert q.is_dir()and read(q/'baseline.json')==deps
  names=set(read(r/'preserved/owned-player-source-manifest-r1.json'))|{str(p.relative_to(r))for p in(r/'internal/ownedworld').glob('*.go')}
  for n in sorted(names):
   dst=q/'source'/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,dst)
  if a.action=='prepare':
   for n in ['probe.mod','probe.sum']:(q/n).write_bytes(h.stored(r,'owned-player-r1','/owned-player-r1/'+n))
   for n in ['army-catalog.json','combat-catalog.json','PAM.AY']:(q/'inputs'/n).write_bytes(h.stored(r,'owned-player-r1','/owned-player-r1/inputs/'+n))
   write(q/'baseline.json',deps)
  shutil.copyfile(r/'tools/original-army-review.py',q/'original-army-review.py');(q/'source-manifest.json').write_text(json.dumps({n:sha(q/'source'/n)for n in sorted(names)},ensure_ascii=False,indent=2)+'\n');return
 assert read(r/'preserved/original-army-review-audit-r1.json')['status']=='passed-original-F2-Go-data-audit'
 assert read(q/'gui-r1/receipt.json')['waits_for_original_panel_commit']
 for hd in ['false','true']:assert read(q/('runtime-hd-'+hd)/'receipt.json')['full_frame_equal']
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for f in sorted(q.rglob('*')):
  if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
  assert f.stat().st_uid==1000 and not f.is_symlink();b=f.read_bytes();hsh=hashlib.sha256(b).hexdigest();obj=folder/(hsh+'.gz')
  if hsh not in objects:obj.write_bytes(gzip.compress(b,6,mtime=0));objects[hsh]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(f.relative_to(r)),bytes=len(b),sha256=hsh,mode=f.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Original data and complete binaries local only. Extended-kind presentation remains pending.'))
if __name__=='__main__':main()
