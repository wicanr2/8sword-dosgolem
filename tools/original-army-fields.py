#!/usr/bin/env python3
"""Original-layout HD army fields: prepare, audit, publish and preserve."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/original-army-fields-r1'
BATCH='original-army-fields-r1'
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
  write(a.out,dict(status='passed-detached-original-army-fields',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL;s=importlib.util.spec_from_file_location('h',r/'tools/prepare-owned-army-ui.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h);deps=h.dependencies(r)
 if a.action in ['prepare','freeze']:
  if a.action=='prepare':
   assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir();(q/'inputs').mkdir();(q/'ui-assets').mkdir()
   for n in ['probe.mod','probe.sum']:(q/n).write_bytes(h.stored(r,'owned-player-r1','/owned-player-r1/'+n))
   for n in ['army-catalog.json','combat-catalog.json','PAM.AY','origin-terrain-packed.ay','map01.ay']:(q/'inputs'/n).write_bytes(h.stored(r,'owned-player-r1','/owned-player-r1/inputs/'+n))
   for f in read(r/'preserved/owned-player-r1.json')['files']:
    marker='/owned-player-r1/ui-assets/'
    if marker in f['path']:(q/'ui-assets'/f['path'].split(marker,1)[1]).write_bytes(h.stored(r,'owned-player-r1',marker+f['path'].split(marker,1)[1]))
   (q/'xcheck').write_bytes(h.stored(r,'owned-player-r1','/owned-player-r1/xcheck'));(q/'xcheck').chmod(493);write(q/'baseline.json',deps)
   # Preserve the exact original IDA evidence, without rerunning or renaming symbols.
   for batch in ['owned-world-army-view-r1','owned-world-army-dismiss-r1']:(q/(batch+'-ida.json')).write_bytes(h.stored(r,batch,'/ida/ida-army-view-r1.json'))
  else:assert q.is_dir()and read(q/'baseline.json')==deps
  names=set(read(r/'preserved/owned-player-source-manifest-r1.json'))|{str(p.relative_to(r))for p in(r/'internal/ownedworld').glob('*.go')}
  for n in sorted(names):
   dst=q/'source'/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,dst)
  (q/'source-manifest.json').write_text(json.dumps({n:sha(q/'source'/n)for n in sorted(names)},ensure_ascii=False,indent=2)+'\n');shutil.copyfile(r/'tools/original-army-fields.py',q/'original-army-fields.py');return
 if a.action=='gui':
  assert read(q/'runtime-r1/receipt.json')['status']=='passed-original-army-host-fields';shutil.copytree(q/'runtime-r1/initial-session',q/'gui-session')
  src=q/'source/internal/ownedworld/world-army-review_main.go';raw=src.read_text();guard='\tif !*nativeImportOnly {\n\t\treturn ErrOriginalBattlefieldPending\n\t}\n';assert raw.count(guard)==1;(q/'research-main.go').write_text(raw.replace(guard,'',1));write(q/'gui-overlay.json',dict(Replace={'/out/source/internal/ownedworld/world-army-review_main.go':'/out/research-main.go'}));write(q/'gui-overlay-notice.json',dict(research_only=True,change='Only remove the ordinary startup guard. Controlled saved army; no GUI RAM/IP injection.'));return
 if a.action=='audit':
  from PIL import Image,ImageChops,__version__
  assert __version__=='11.3.0'and deps==read(q/'baseline.json')
  for n,hashval in read(q/'source-manifest.json').items():assert sha(r/n)==sha(q/'source'/n)==hashval,n
  d=read(q/'runtime-r1/receipt.json');assert d['status']=='passed-original-army-host-fields'and d['transactions']==1 and d['cold_world_equal']and d['missing_art_rejected']and d['native_extended_rejected']
  before=d['initial_world'];expected=json.loads(json.dumps(before));expected['revision']+=1;expected['army']['slots']=before['army']['slots'][:1]+before['army']['slots'][2:]+[dict(unit='',count=0)];assert d['final_world']==expected
  assert(q/'runtime-r1/initial-session/gamedata.ay').read_bytes()==(q/'runtime-r1/session/gamedata.ay').read_bytes();assert d['native_shadow_hex']=='01001e000000000000000000000000000000000000000000'
  # Check original index-avoidance spans against the saved IDA call/cleanup sequence.
  ida=read(q/'owned-world-army-dismiss-r1-ida.json');f=next(x for x in ida['functions']if x['name']=='sub_1775A');spans={0x77cd:0x7801,0x7850:0x7884,0x78ad:0x78e1,0x7930:0x7964,0x798d:0x79c1,0x7a10:0x7a44,0x7a6d:0x7aa1,0x7af0:0x7b24,0x7baf:0x7be3}
  for start,end in spans.items():
   rows=[x for x in f['lines']if 0x10000+start<=x['ida_linear']<0x10000+end];assert rows[0]['bytes']=='8b874a05'and rows[-1]['bytes']=='83c406'and any('sub_24703'in x['instruction']for x in rows)
  catalog={x['id']:x for x in read(q/'inputs/army-catalog.json')['profiles']}
  for m in d['models']:assert m['name']==catalog[m['unit']]['name']and m['count']==4294967295 and m['monthly']==4294967295*catalog[m['unit']]['gold']
  pack=read(q/'ui-assets/unit-art.json');assert pack['catalog_raw_sha256']==sha(q/'inputs/army-catalog.json')and len(pack['rows'])==8
  for row in pack['rows']:
   p=q/'ui-assets'/row['file'];assert sha(p)==row['sha256']and Image.open(p).size==(512,512)
  control_frames=0
  for hd in ['false','true']:
   for stage in ['opened','selected-second','after-dismiss','f2-remaining','empty']:
    folder=q/('runtime-hd-'+hd);x=Image.open(folder/f'side-0-{stage}.png').convert('RGBA');y=Image.open(folder/f'side-1-{stage}.png').convert('RGBA');assert x.tobytes()==y.tobytes()and x.size==y.size==(1920,1200);control_frames+=2
   assert read(q/'f2-regression'/('runtime-hd-'+hd)/'receipt.json')['full_frame_equal']
  for route in ['read','commit']:
   fault=read(q/('fault-'+route)/'receipt.json');assert fault['pair_unchanged']and fault['native_shadow_unchanged']and fault['transactions']==0
  shots=[]
  for row in d['shots']:
   folder=q/'runtime-r1';base=Image.open(folder/(row['name']+'-base.png')).convert('RGBA');frame=Image.open(folder/(row['name']+'-frame.png')).convert('RGBA');assert hashlib.sha256(frame.tobytes()).hexdigest()==row['frame_sha256'];allowed=Image.new('L',frame.size);from PIL import ImageDraw;mask=ImageDraw.Draw(allowed)
   for i,unit in enumerate(row['rows']):
    if not unit['Host']:continue
    col,rank=divmod(i,3);left=(24+232*col)*3;top=(13+60*rank)*6;mask.rectangle((left,top,left+264-1,top+300-1),fill=255)
    for line in range(3):mask.rectangle(((112+232*col)*3,top+line*96,min((24+232*(col+1))*3-24,1368)-1,top+line*96+89),fill=255)
   diff=ImageChops.difference(base,frame).convert('RGB');diff.paste((0,0,0),mask=allowed);assert not diff.getbbox(),row['name']
   for field in read(folder/(row['name']+'-texts.json')):
    box,ink=field['Rect'],field['Ink'];assert not field['Ellipsized']and box[0]<=ink[0]<=ink[2]<=box[2]and box[1]<=ink[1]<=ink[3]<=box[3]
   shots.append(row['name'])
  gui=read(q/'gui-r1/receipt.json');assert gui['status']=='passed-original-army-fields-GUI'and gui['program_sha256']==sha(q/'8sword-fields-gui')and gui['cold_world_equal']
  for row in gui['screenshots']:
   folder=q/'gui-r1'/row['phase'];meta=read(folder/row['metadata']);im=Image.open(folder/row['canvas']).convert('RGBA');screen=Image.open(folder/row['screen']).convert('RGB');assert im.size==screen.size==(1920,1200)and im.convert('RGB').tobytes()==screen.tobytes();assert hashlib.sha256(im.tobytes()).hexdigest()==meta['canvas_sha256']==meta['presented_sha256']and meta['original_review_ready']
  assert(q/'tests-r1.log').read_text().rstrip().endswith('PASS')and(q/'tests-fields-r3.log').read_text().rstrip().endswith('PASS');entry=read(q/'production-entry-receipt.json');assert entry['status']=='passed'and entry['program_sha256']==sha(q/'8sword-owned')
  write(a.out,dict(status='passed-original-layout-HD-fields-audit',source_files=len(read(q/'source-manifest.json')),runtime_frames=shots,gui_frames=len(gui['screenshots']),models=d['models'],regression_control_frames=control_frames,unchanged_outside_fields=True,original_name_spans=9,original_art_parity_claimed=False,controlled_army=True,native_extended_rejected=True,production_entry_remains_disabled=True));return
 if a.action=='publish':
  import io
  from PIL import Image,ImageDraw,ImageFont
  assert read(r/'preserved/original-army-fields-audit-r1.json')['status']=='passed-original-layout-HD-fields-audit'
  idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));raw=gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes());font=ImageFont.truetype(io.BytesIO(raw),36,index=3);small=ImageFont.truetype(io.BytesIO(raw),24,index=3);out=Image.new('RGB',(1920,720),'#11251f');draw=ImageDraw.Draw(out);sources=[]
  gui=read(q/'gui-r1/receipt.json')
  for i,(name,title)in enumerate([('f2-noto','F2・原版版面＋Go新兵資料'),('f3-wolf-lishu','F3・方向鍵選隊＋隸書')]):
   row=next(x for x in gui['screenshots']if x['name']==name);p=q/'gui-r1'/row['phase']/row['canvas'];meta=q/'gui-r1'/row['phase']/row['metadata'];state=read(meta);im=Image.open(p);out.paste(im.resize((960,600),Image.Resampling.NEAREST),(i*960,64));draw.text((i*960+24,8),title,font=font,fill='#fff1b5');sources.append(dict(path=str(p.relative_to(r)),sha256=sha(p),font=state['font_id'],metadata_path=str(meta.relative_to(r)),metadata_sha256=sha(meta)))
  draw.text((24,675),'明示六隊測試配置；新增兵種未進原版索引。兩張皆為實際HD視窗。',font=small,fill='#fff1b5');p=a.out/'original-army-fields-go-r1.png';assert not p.exists();out.save(p);write(a.out/'original-army-fields-go-r1.json',dict(schema=1,output=p.name,output_sha256=sha(p),inputs=sources,audit_sha256=sha(r/'preserved/original-army-fields-audit-r1.json'),clock_initial='12:00:00.00 via Oracle.SetClock; live 3000 cycles/ms',rng_comparison='No random outcome compared',controlled_army=True,actual_window_verified=True,original_art_parity_claimed=False));return
 assert read(r/'preserved/original-army-fields-audit-r1.json')['status']=='passed-original-layout-HD-fields-audit'
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for f in sorted(q.rglob('*')):
  if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
  assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();hsh=hashlib.sha256(raw).hexdigest();obj=folder/(hsh+'.gz')
  if hsh not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[hsh]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(f.relative_to(r)),bytes=len(raw),sha256=hsh,mode=f.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Original data, complete artwork and binaries local only. Ordinary player entry remains disabled.'))
if __name__=='__main__':main()
