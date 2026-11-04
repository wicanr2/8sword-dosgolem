#!/usr/bin/env python3
"""Spec030 新兵來源材質：固定候選、獨立核對、成果與永久保存。"""
import argparse, difflib, gzip, hashlib, importlib.util, json, os, re, shutil, sys
from pathlib import Path
sys.dont_write_bytecode = True
REL='workplace/probe-20261023/graphics-first/battle-r1/original-battle-art-r1'
BATCH='original-battle-art-r1'
STATUS='passed-original-battle-art-audit'
SCENE='internal/eightsword/source_scene.go'
EXTRA=['internal/eightsword/source_battle_art.go','internal/eightsword/source_battle_art_test.go']
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def write(p,v):
 with p.open('x') as f: json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def patched_scene(r):
 old=(r/SCENE).read_text().splitlines(keepends=True);patch=(r/'tools/source-battle-art.patch').read_text().splitlines(keepends=True)
 out=[];pos=0;i=2
 while i<len(patch):
  match=re.match(r'@@ -(\d+)(?:,\d+)? \+\d+(?:,\d+)? @@',patch[i]);assert match,patch[i]
  at=int(match[1])-1;assert at>=pos;out.extend(old[pos:at]);pos=at;i+=1
  while i<len(patch) and not patch[i].startswith('@@'):
   line=patch[i];kind=line[0];assert kind in ' +-'
   if kind in ' -':assert old[pos]==line[1:],(pos,line);pos+=1
   if kind in ' +':out.append(line[1:])
   i+=1
 out.extend(old[pos:]);return ''.join(out).encode()
def audit(r,q,out):
 from PIL import Image
 manifest=read(q/'source-manifest.json');candidate=patched_scene(r)
 for n,d in manifest.items():
  assert sha(q/'source'/n)==d,n
  assert (hashlib.sha256(candidate).hexdigest() if n==SCENE else sha(r/n))==d,n
 assert sha(r/SCENE)==read(r/'preserved/owned-player-source-manifest-r1.json')[SCENE]
 pam=(q/'inputs/PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
 image=bytearray(pam);word=lambda at:int.from_bytes(pam[at:at+2],'little');header=word(8)*16
 for i in range(word(6)):
  at=word(24)+i*4;off=header+word(at+2)*16+word(at);image[off:off+2]=((word(off)+0x1000)&65535).to_bytes(2,'little')
 lines=functions=0
 for name in ['evidence/ida-art-callers-r1.json','ida-art-wrappers-r1.json']:
  v=read(q/name);assert v['source_sha256']==sha(q/'inputs/PAM.AY')and v['database_sha256']=='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac';functions+=len(v['functions'])
  for f in v['functions']:
   for l in f['lines']:
    raw=bytes.fromhex(l['bytes']);off=l['original_file_offset'];assert bytes(image[off:off+len(raw)])==raw;lines+=1
 models=read(q/'art-tile-models.json');assert len(models['tiles'])==8 and models['refusals']==3
 # Independent PNG alpha conversion, bounding box, fit and nearest-neighbour reconstruction.
 pack=read(q/'ui-assets/unit-art.json');assert pack['catalog_raw_sha256']==sha(q/'inputs/army-catalog.json')
 tile_sources={v['id']:v for v in pack['rows']};assert len(tile_sources)==8
 for row in models['tiles']:
  raw=(q/'art-tiles'/row['file']).read_bytes();assert len(raw)==264*300*4 and hashlib.sha256(raw).hexdigest()==row['sha256']
  source=tile_sources[row['id']];file=q/'ui-assets'/source['file'];assert sha(file)==source['sha256']
  im=Image.open(file).convert('RGBA');assert im.size==(512,512);box=im.getchannel('A').getbbox();assert box
  bw,bh=box[2]-box[0],box[3]-box[1];w,h=252,288
  if w*bh>h*bw:w=h*bw//bh
  else:h=w*bh//bw
  left,top=(264-w)//2,300-h;expected=bytearray(264*300*4)
  for y in range(h):
   for x in range(w):
    red,green,blue,alpha=im.getpixel((box[0]+x*bw//w,box[1]+y*bh//h));at=((top+y)*264+left+x)*4
    expected[at:at+4]=bytes([((c*257*alpha//255)>>8)for c in [red,green,blue]]+[alpha])
  assert bytes(expected)==raw,(row['id'],'independent PNG reconstruction')
 bindings=read(q/'art-binding-models.json');assert bindings==dict(paired_commands=3,refusals=10,small_restore_and_death_clear=True,unbound_background_unchanged=True)
 results=[];compared_states=0;pixel_frames=0
 background_file=q/'inputs/battle-palace-background-r1.png';assert sha(background_file)=='521a7a99e37cd437b6cf54835002df42dde1ef29c9bc551af0a1bfaec10230f6'
 background=Image.open(background_file).convert('RGB');assert background.size==(1586,992)
 def background_pixel(x,y):
  sx=max(0,(x+.5)*1586/1920-.5);sy=max(0,(y+.5)*992/1200-.5);x0,y0=int(sx),int(sy);x1,y1=min(x0+1,1585),min(y0+1,991);fx,fy=sx-x0,sy-y0
  points=[(x0,y0),(x1,y0),(x0,y1),(x1,y1)];weights=[(1-fx)*(1-fy),fx*(1-fy),(1-fx)*fy,fx*fy]
  return tuple(int(sum(background.getpixel(p)[c]*w for p,w in zip(points,weights))+.5)for c in range(3))+(255,)
 dead_background_pixels=0
 for units in ['mixed','native','fragile']:
  dirs=[q/'art-world-r1'/units/m/'hd-mixed-go'for m in ['off','on']]
  receipts=[read(d/'receipt.json')for d in dirs];arts=[read(d/'art.json')for d in dirs]
  for phase in ['cancel','retreat','win']:
   assert (dirs[0]/(phase+'.state')).read_bytes()==(dirs[1]/(phase+'.state')).read_bytes(),(units,phase,'guest state');compared_states+=1
   assert (dirs[0]/(phase+'.png')).read_bytes()==(dirs[1]/(phase+'.png')).read_bytes(),(units,phase,'map frame')
  assert receipts[0]==receipts[1]and read(dirs[0]/'saved.json')==read(dirs[1]/'saved.json'),units
  status=arts[1]['status'];assert status['installed']and status['materials']==8
  assert status['commands']>0 if units!='native'else status['commands']==0
  assert len(arts[0]['captures'])==len(arts[1]['captures'])>0
  for a,b in zip(arts[0]['captures'],arts[1]['captures']):
   for key in ['file','rows','slots','coordinates_hex','step']:assert a[key]==b[key],(units,key)
   ims=[Image.open(d/a['file']).convert('RGBA')for d in dirs];assert ims[0].size==ims[1].size==(1920,1200)
   rects=[];coords=bytes.fromhex(a['coordinates_hex'])
   for slot,raw in enumerate(a['slots'][0]):
    row=a['rows'][0][raw]
    if row['unit'].startswith('openkb:'):
     rectangle=(coords[slot*2]*24,coords[slot*2+1]*6,264,300);rects.append(rectangle)
     if units=='fragile'and row['count']==0:
      rx,ry,w,h=rectangle
      for by in range(ry,ry+h):
       for bx in range(rx,rx+w):assert ims[1].getpixel((bx,by))==background_pixel(bx,by),(units,a['file'],'dead background',bx,by);dead_background_pixels+=1
   changed=0
   for y in range(1200):
    for x in range(1920):
     if ims[0].getpixel((x,y))!=ims[1].getpixel((x,y)):
      assert any(rx<=x<rx+w and ry<=y<ry+h for rx,ry,w,h in rects),(units,a['file'],x,y);changed+=1
   if units=='native':assert changed==0
   else:assert changed>0
   pixel_frames+=1
  saved=read(dirs[1]/'saved.json');cold=read(dirs[1]/'process-cold/receipt.json');assert saved['world_sha256']==cold['world_sha256']and saved['resources']==cold['resources']and saved['location']==cold['location']and cold['separate_process']and not cold['snapshot_loaded']
  if units=='fragile':
   assert any(any(row['unit']=='openkb:wolf'and row['count']==1 for row in c['rows'][0])for c in arts[1]['captures'])
   assert any(all(row['unit']!='openkb:wolf'or row['count']==0 for row in c['rows'][0])for c in arts[1]['captures'])
   assert all(row['unit']!='openkb:wolf'for row in saved['army'])
   assert any(e['source_width_bytes']==8 and e['source_height']==25 for e in arts[1]['events'])
   assert status['retired_units']>0 and status['retired_pixels']>0
  results.append(dict(units=units,commands=status['commands'],captures=len(arts[1]['captures']),army=saved['army'],F7=True,separate_process_Continue=True))
 for log in ['tests-api-r1.log','tests-art-final-r1.log','tests-matrix-r1.log','tests-cold-r1.log','regression-source-r1.log']:assert(q/log).read_text().rstrip().endswith('PASS'),log
 write(out,dict(status=STATUS,source_files=len(manifest),source_manifest_sha256=sha(q/'source-manifest.json'),source_scene_patch_sha256=sha(r/'tools/source-battle-art.patch'),ida_functions=functions,ida_lines=lines,full_guest_state_pairs=compared_states,battle_frame_pairs=pixel_frames,independent_dead_background_pixels=dead_background_pixels,worlds=results,tiles=8,binding_refusals=10,initial_small_restore_scaffold=True,formal_runtime_unchanged=True,general_entry_disabled=True,schema_unchanged=True,initial_seed=0x12345678,limits=['Standing/redraw/background-clear only; new hand-drawn action poses remain pending.','Frames are Engine output; no new X11 acceptance. Position and armies are explicit fixtures; not natural recruitment or clear.','No additional block-by-block PCM comparison; full guest snapshots match.','Differences are confined to live/dead new-unit footprints. Disabled control can retain obsolete native placeholders; dead regions use the independent HD background reference.','General startup, random/guard coordinator and rules/AI integration remain pending.']))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['freeze','audit','publish','archive','verify'])
 for n in ['project','archive','out']:p.add_argument('--'+n,type=Path)
 a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   ob=d['objects'][f['sha256']];obj=a.archive/BATCH/ob['file'];assert sha(obj)==ob['stored_sha256'];raw=gzip.decompress(obj.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-original-battle-art',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL;s=importlib.util.spec_from_file_location('helper',r/'tools/prepare-owned-army-ui.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h);deps=h.dependencies(r);assert deps==read(q/'baseline.json')
 if a.action=='freeze':
  names=set(read(r/'preserved/owned-player-source-manifest-r1.json'))|{str(f.relative_to(r))for f in(r/'internal/ownedworld').glob('*.go')}|set(EXTRA)
  assert not(q/'source').exists()
  for n in sorted(names):
   dst=q/'source'/n;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(patched_scene(r)if n==SCENE else(r/n).read_bytes())
  write(q/'source-manifest.json',{n:sha(q/'source'/n)for n in sorted(names)});shutil.copyfile(r/'tools/source-battle-art.patch',q/'source-battle-art.patch');return
 if a.action=='audit':audit(r,q,a.out);return
 assert read(r/'preserved/original-battle-art-audit-r1.json')['status']==STATUS
 if a.action=='publish':
  import io
  from PIL import Image,ImageDraw,ImageFont
  idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),27,index=3)
  canvas=Image.new('RGB',(1280,530),'#11251f');draw=ImageDraw.Draw(canvas);sources=[]
  for i,(rel,label)in enumerate([('mixed/on/hd-mixed-go/battle-000.png','原版HD戰場：野狼與女弓箭手'),('fragile/on/hd-mixed-go/battle-001.png','一隻野狼陣亡後：背景清除')]):
   f=q/'art-world-r1'/rel;canvas.paste(Image.open(f).resize((640,400),Image.Resampling.NEAREST),(i*640,58));draw.text((i*640+12,12),label,font=font,fill='#fff1b5');sources.append(dict(path=str(f.relative_to(r)),sha256=sha(f)))
  draw.text((12,473),'Go來源命令直接繪製；明示軍隊／位置。站姿與重繪已驗，手繪攻擊姿態待補。',font=font.font_variant(size=23),fill='#fff1b5')
  f=a.out/'original-battle-new-units-go-r1.png';assert not f.exists();canvas.save(f);write(a.out/'original-battle-new-units-go-r1.json',dict(sha256=sha(f),sources=sources,actual_window=False,general_entry=False));return
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for f in sorted(q.rglob('*')):
  if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
  assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();digest=hashlib.sha256(raw).hexdigest();obj=folder/(digest+'.gz')
  if digest not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[digest]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(f.relative_to(r)),bytes=len(raw),sha256=digest,mode=f.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Original data/full frames/states and binaries local only; general entry disabled.'))
if __name__=='__main__':main()
