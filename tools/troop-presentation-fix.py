#!/usr/bin/env python3
"""Spec030: transparent recruitment silhouettes and corrected openKB identities."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,tempfile
from pathlib import Path
from PIL import Image,__version__
REL='workplace/probe-20261023/graphics-first/battle-r1/troop-presentation-fix-r1'
BATCH='troop-presentation-fix-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def module(p,name):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['capture','prepare','freeze','gui','audit','publish','archive','verify']);
 for n in ['project','generated','archive','out']:p.add_argument('--'+n,type=Path)
 a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000 and __version__=='11.3.0'
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   v=d['objects'][f['sha256']];z=(a.archive/BATCH/v['file']).read_bytes();assert hashlib.sha256(z).hexdigest()==v['stored_sha256'];raw=gzip.decompress(z);assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-troop-presentation-fix',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL;h=module(r/'tools/prepare-owned-army-ui.py','helper')
 if a.action=='capture':
  art=r/'artwork';plan=read(art/'openkb-hd-corrections-r2.json');manifest=read(art/'manifest.json');before=sha(art/'manifest.json');prior=len(manifest['files']);added=[]
  assert prior==1066 and art.stat().st_uid==1000
  def save(raw,path,source,role):
   dest=art/path;dest.parent.mkdir(parents=True,exist_ok=True);assert dest.parent.stat().st_uid==1000 and not dest.exists();dest.write_bytes(raw);item=dict(source=source,path=path,sha256=sha(dest),bytes=len(raw),role=role,basis='User corrected archer to Chinese female and pike to peasant with sharpened wooden pole.');
   if path.endswith('.png'):
    im=Image.open(dest);assert im.mode=='RGBA'and im.getchannel('A').getextrema()==(0,255);item['image']=dict(size=list(im.size),mode=im.mode)
   added.append(item);return item
  for row in plan['rows']:
   src=a.generated/Path(row['generated_path']).relative_to('/home/anr2/.codex/generated_images');assert src.is_file()and src.stat().st_uid==1000
   item=save(src.read_bytes(),row['master'],row['generated_path'],'master');row['master_sha256']=item['sha256'];row['reference_sha256']=sha(art/row['reference']);save((json.dumps(row,ensure_ascii=False,indent=2)+'\n').encode(),row['provenance'],'artwork/openkb-hd-corrections-r2.json#'+row['id'],'provenance')
  save((json.dumps(plan,ensure_ascii=False,indent=2)+'\n').encode(),'approved/provenance/openkb-hd-r2/generation.json','artwork/openkb-hd-corrections-r2.json','provenance');assert sha(art/'manifest.json')==before
  manifest['files']+=added;manifest.setdefault('additions',[]).append(dict(index='openkb-hd-corrections-preservation-r2.json',previous_manifest_sha256=before,files=len(added)))
  fd,name=tempfile.mkstemp(prefix='.troop-correction-',dir=art);os.close(fd);temp=Path(name);temp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');os.replace(temp,art/'manifest.json');write(art/'openkb-hd-corrections-preservation-r2.json',dict(status='preserved-corrected-openkb-masters',prior_files=prior,added_files=len(added),manifest_files=len(manifest['files']),prior_manifest_sha256=before,manifest_sha256=sha(art/'manifest.json'),rows=plan['rows']));return
 deps=h.dependencies(r)
 if a.action=='prepare':
  assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir()
  for n in ['inputs','ui-assets','initial-session']:(q/n).mkdir()
  batch='original-reinforcement-quantity-r1';d=read(r/'preserved'/f'{batch}.json');marker='/'+batch+'/'
  for row in d['files']:
   name=row['path'].split(marker,1)[1]
   if name in ['probe.mod','probe.sum','xcheck']or name.startswith(('inputs/','ui-assets/','initial-session/')):
    dst=q/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(h.stored(r,batch,marker+name));dst.chmod(row['mode'])
  previous=read(q/'ui-assets/unit-art.json');pack=json.loads(json.dumps(previous));corrections=read(r/'artwork/openkb-hd-corrections-preservation-r2.json')
  for row in corrections['rows']:
   master=r/'artwork'/row['master'];assert sha(master)==row['master_sha256'];im=Image.open(master);im=im.crop(im.getchannel('A').getbbox());im.thumbnail((472,472),Image.Resampling.LANCZOS);canvas=Image.new('RGBA',(512,512));canvas.alpha_composite(im,((512-im.width)//2,(512-im.height)//2));dest=q/'ui-assets'/('unit-'+row['file']+'.png');canvas.save(dest);next(v for v in pack['rows']if v['id']==row['id'])['sha256']=sha(dest)
  (q/'ui-assets/unit-art.json').write_text(json.dumps(pack,ensure_ascii=False,indent=2)+'\n');write(q/'prior-art-pack.json',previous);write(q/'baseline.json',deps)
 if a.action in ['prepare','freeze']:
  assert read(q/'baseline.json')==deps
  names=set(read(r/'preserved/owned-player-source-manifest-r1.json'))|{str(p.relative_to(r))for p in(r/'internal/ownedworld').glob('*.go')}
  for name in sorted(names):
   dst=q/'source'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/name,dst)
  (q/'source-manifest.json').write_text(json.dumps({n:sha(q/'source'/n)for n in sorted(names)},ensure_ascii=False,indent=2)+'\n');shutil.copyfile(Path(__file__),q/Path(__file__).name);shutil.copyfile(r/'tools/check-troop-presentation-gui.py',q/'check-troop-presentation-gui.py');return
 if a.action=='gui':
  shutil.copytree(q/'initial-session',q/'gui-session');src=q/'source/internal/ownedworld/world-army-review_main.go';raw=src.read_text();guard='\tif !*nativeImportOnly {\n\t\treturn ErrOriginalBattlefieldPending\n\t}\n';assert raw.count(guard)==1;(q/'research-main.go').write_text(raw.replace(guard,'',1));write(q/'gui-overlay.json',dict(Replace={'/out/source/internal/ownedworld/world-army-review_main.go':'/out/research-main.go'}));return
 if a.action=='audit':
  assert deps==read(q/'baseline.json')
  for n,digest in read(q/'source-manifest.json').items():assert sha(r/n)==sha(q/'source'/n)==digest,n
  corrections=read(r/'artwork/openkb-hd-corrections-preservation-r2.json');assert corrections['manifest_files']==1071
  for row in corrections['rows']:
   im=Image.open(r/'artwork'/row['master']);assert sha(r/'artwork'/row['master'])==row['master_sha256']and im.mode=='RGBA'and im.size==(1254,1254)and im.getchannel('A').getextrema()==(0,255)
  prior=read(q/'prior-art-pack.json');pack=read(q/'ui-assets/unit-art.json');assert pack['schema']==prior['schema']and pack['catalog_raw_sha256']==prior['catalog_raw_sha256']and len(pack['rows'])==8
  unchanged=[]
  for old,new in zip(prior['rows'],pack['rows']):
   assert old['id']==new['id']and old['file']==new['file']and sha(q/'ui-assets'/new['file'])==new['sha256']
   if new['id']not in ['openkb:arcr','openkb:pike']:assert old==new;unchanged.append(new['id'])
  model=read(q/'presentation-model-r1.json');assert model['status']=='passed-transparent-recruit-presentation'and model['outside_silhouette_unchanged']and model['source_frame_unchanged']and model['both_original_quantity_paths']
  alpha=verify_alpha(q)
  gui=read(q/'gui-r1/receipt.json');assert gui['status']=='passed-troop-presentation-GUI'and gui['memory_injected']==False and gui['program_sha256']==sha(q/'8sword-presentation-gui')
  for row in gui['screenshots']:
   folder=q/'gui-r1'/row['phase'];meta=read(folder/row['metadata']);im=Image.open(folder/row['canvas']).convert('RGBA');screen=Image.open(folder/row['screen']).convert('RGB');assert im.size==screen.size==(1920,1200)and im.convert('RGB').tobytes()==screen.tobytes();assert hashlib.sha256(im.tobytes()).hexdigest()==meta['canvas_sha256']==meta['presented_sha256']
  assert(q/'tests-r1.log').read_text().rstrip().endswith('PASS')
  write(a.out,dict(status='passed-troop-presentation-fix-audit',source_files=len(read(q/'source-manifest.json')),corrected_units=['openkb:arcr','openkb:pike'],unchanged_unit_images=unchanged,transparent_native_and_new_recruitment=True,alpha_reconstruction=alpha,gui_frames=len(gui['screenshots']),ordinary_player_entry_disabled=True,rules_save_and_transactions_unchanged=True));return
 if a.action=='publish':
  assert read(r/'preserved/troop-presentation-fix-audit-r1.json')['status']=='passed-troop-presentation-fix-audit'
  publish(r,q,a.out,h);return
 if a.action=='archive':
  assert read(r/'preserved/troop-presentation-fix-audit-r1.json')['status']=='passed-troop-presentation-fix-audit';folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
  for f in sorted(q.rglob('*')):
   if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
   assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();digest=hashlib.sha256(raw).hexdigest();obj=folder/(digest+'.gz')
   if digest not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[digest]=dict(file=obj.name,stored_sha256=sha(obj))
   files.append(dict(path=str(f.relative_to(r)),bytes=len(raw),sha256=digest,mode=f.stat().st_mode&0o777))
  write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Complete original inputs, PNGs and binaries local only; artwork masters independently preserved.'))
def verify_alpha(q):
 from PIL import ImageChops,ImageOps
 base=Image.open(q/'alpha-base.png').convert('RGB');reports=[]
 for name,src in [('native','icon'),('new','new-icon')]:
  image=Image.open(q/f'alpha-{name}.png').convert('RGB');icon=Image.open(q/f'alpha-{src}.png').convert('RGBA');bbox=icon.getchannel('A').getbbox();x0,y0,x1,y1=bbox;sw,sh=x1-x0,y1-y0;w,h=222,480
  if w*sh>h*sw:w=h*sw//sh
  else:h=w*sh//sw
  left,top=1081+(222-w)//2,117+(480-h)//2;allowed=Image.new('L',base.size);mask=allowed.load();pixels=icon.load();output=image.load();original=base.load();transparent=opaque=0
  for y in range(h):
   for x in range(w):
    c=pixels[x0+x*sw//w,y0+y*sh//h];at=(left+x,top+y)
    if c[3]==0:assert output[at]==original[at];transparent+=1
    else:
     mask[at]=255
     if c[3]==255:assert output[at]==c[:3];opaque+=1
  # Cached native tiles may contain almost entirely partial-alpha samples.
  # Require positive coverage; do not invent an opaque-area quota.
  diff=ImageChops.difference(image,base);outside=ImageChops.multiply(diff,ImageOps.invert(allowed).convert('RGB'));assert outside.getbbox()is None and transparent>0 and opaque>0
  reports.append(dict(path=name,source_sha256=sha(q/f'alpha-{src}.png'),transparent_samples_unchanged=transparent,opaque_samples_equal=opaque,outside_silhouette_differences=0,partial_alpha='Existing Go premultiplied blending retained; not used for exact RGB oracle.'))
 return reports
def publish(r,q,out,h):
 import io
 from PIL import ImageDraw,ImageFont
 idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));raw=gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes());font=ImageFont.truetype(io.BytesIO(raw),36,index=3);gui=read(q/'gui-r1/receipt.json');sources=[]
 sheet=Image.new('RGB',(1920,1410),'#11251f');draw=ImageDraw.Draw(sheet)
 for i,(name,title)in enumerate([('native-transparent','原版募兵・透明部隊'),('new-wolf-input','新增野狼・透明數量輸入'),('new-eight','新增兵種・女弓箭手與農民'),('army-reviewed','原版軍隊頁・既有Go進度')]):
  row=next(x for x in gui['screenshots']if x['name']==name);folder=q/'gui-r1'/row['phase'];p=folder/row['canvas'];x,y=i%2*960,i//2*670;sheet.paste(Image.open(p).resize((960,600),Image.Resampling.NEAREST),(x,y+60));draw.text((x+20,y+8),title,font=font,fill='#fff1b5');sources.append(dict(path=str(p.relative_to(r)),sha256=sha(p),metadata_sha256=sha(folder/row['metadata'])))
 draw.text((24,1355),'實際X11與Go提交逐RGB相同；只改圖像與alpha合成，原版數量輸入、規則與存檔保持。',font=font.font_variant(size=26),fill='#fff1b5');sheet.save(out/'troop-presentation-corrected-r1.png');write(out/'troop-presentation-corrected-r1.json',dict(schema=1,output_sha256=sha(out/'troop-presentation-corrected-r1.png'),inputs=sources,actual_window_verified=True,controlled_initial_army=True,scope='Presentation only; no battle integration acceptance.'))
 # Reuse the established gallery geometry and source-license metadata, with
 # the two corrected masters substituted explicitly and all six others kept.
 gallery=module(r/'tools/prepare-openkb-hd.py','gallery');original_read=gallery.read;art=read(r/'artwork/openkb-hd-preservation-r1.json');corr={x['id']:x for x in read(r/'artwork/openkb-hd-corrections-preservation-r2.json')['rows']}
 for row in art['rows']:
  if row['id']in corr:row['master']=corr[row['id']]['master'];row['master_sha256']=corr[row['id']]['master_sha256']
 gallery.read=lambda p:art if Path(p)==r/'artwork/openkb-hd-preservation-r1.json'else original_read(p)
 temp=q/'gallery-r2';temp.mkdir();gallery.publish(r,q,temp,h,True)
 for old,new in [('openkb-eight-original-hd-r1.png','openkb-eight-original-hd-r2.png'),('troops-all-original-hd-with-openkb-r4.png','troops-all-original-hd-with-openkb-r5.png'),('openkb-eight-original-hd-r1.json','openkb-eight-original-hd-r2.json')]:shutil.copyfile(temp/old,out/new)
if __name__=='__main__':main()
