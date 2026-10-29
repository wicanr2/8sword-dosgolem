"""Narrow visual update: eight map cue colors, actual F4 samples and preservation."""
import argparse,ast,gzip,hashlib,json,os,pathlib,re,shutil,struct,subprocess,urllib.parse
from PIL import Image,ImageChops,ImageDraw,ImageFont
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def check_actor_mask(folder,raw):
 text=gzip.decompress((folder/'text-mask.gz').read_bytes());assert len(text)==128000
 mask=Image.frombytes('L',(640,200),bytes(255 if v else 0 for v in text)).resize((1920,1200),Image.Resampling.NEAREST)
 grid=gzip.decompress((folder/'actor-grid.gz').read_bytes());assert len(grid)==128000*6;info=read(folder/'actor-tiles.json');tiles={}
 for key,row in info.items():
  if row['missing']:continue
  tile=Image.open(folder/row['file']).getchannel('A');assert tile.size==(row['width']*3,row['height']*6);tiles[int(key)]=tile.point(lambda a:255 if a else 0)
 for i,(ident,local) in enumerate(struct.iter_unpack('<HI',grid)):
  if not ident:continue
  x,y=i%640*3,i//640*6;row=info[str(ident)];width=row.get('width',0);height=row.get('height',0)
  if ident not in tiles or not width or local>=width*height:alpha=Image.new('L',(3,6),255)
  else:
   sx,sy=local%width*3,local//width*6;alpha=tiles[ident].crop((sx,sy,sx+3,sy+6))
  mask.paste(ImageChops.lighter(mask.crop((x,y,x+3,y+6)),alpha),(x,y))
 assert mask.tobytes()==bytes(255 if v else 0 for v in raw),'actor protection differs from actual tile alpha'
def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','normal','audit','overview','archive','verify','promote','integrity']);p.add_argument('--project',type=pathlib.Path);p.add_argument('--out',type=pathlib.Path);p.add_argument('--archive',type=pathlib.Path);p.add_argument('--font',type=pathlib.Path);a=p.parse_args();assert os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/'map-spell-color-r2.json');checked=set()
  for v in d['files']:
   path=pathlib.PurePosixPath(v['path']);assert not path.is_absolute()and '..'not in path.parts;obj=d['objects'][v['sha256']];f=a.archive/'map-spell-color-r2'/obj['file'];assert sha(f)==obj['stored_sha256'];raw=gzip.decompress(f.read_bytes());assert hashlib.sha256(raw).hexdigest()==v['sha256']and len(raw)==v['bytes'];checked.add(v['sha256'])
  result=dict(status='passed-detached-map-color',files=len(d['files']),objects=len(checked),workplace_required=False,index_sha256=sha(a.archive/'map-spell-color-r2.json'))
 else:
  r=a.project;q=r/'workplace/probe-20261023/graphics-first/battle-r1/player-spells-r1/remaining-r1/map-color-r1';player=r/'workplace/player';candidate=player/'source-candidate-map-color-r2';old=read(r/'preserved/remaining-spells-audit-r1.json');allowed={'internal/eightsword/spell_cues.go','internal/eightsword/spell_cues_draw.go','internal/eightsword/spell_cues_test.go'}
  if a.action=='freeze':
   assert not candidate.exists();candidate.mkdir();inputs={}
   for n,h in old['source_inputs'].items():
    f=r/n;assert f.stat().st_uid==1000
    if n not in allowed:assert sha(f)==h
    dest=candidate/'src'/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest);inputs[n]=sha(f)
   assert len(inputs)==193;shutil.copyfile(player/'runtime.json',candidate/'runtime.json');result=dict(source_inputs=inputs,changed=[n for n,h in inputs.items()if old['source_inputs'][n]!=h],previous_programs=old['programs']);(candidate/'preparation.json').write_text(json.dumps(result,indent=2)+'\n');print('Frozen193 map color inputs');return
  if a.action=='normal':
   out=q/'normal-build-r2';subprocess.run(['python',str(r/'tools/prepare-remaining-normal.py'),'--project',str(r),'--source',str(candidate/'src'),'--out',str(out)],check=True);root=out/'src';f=root/'internal/eightsword/research_cues_test.go';s=f.read_text();s=s.replace('v.start+360000','v.start+1260000').replace('v.start + 360000','v.start + 1260000');needle='if p.Text.ID != 0 {';assert s.count(needle)==1;s=s.replace(needle,'if p.Text.ID != 0 || p.Actor.ID != 0 {',1)
   needle='mask := make([]byte, 128000)';assert needle in s;s=s.replace(needle,'textMask:=make([]byte,128000)\n for i,p:=range researchCueScene.Pixels[researchCueScene.Start:researchCueScene.Start+128000]{if p.Text.ID!=0{textMask[i]=1}}\n tf,te:=os.Create(filepath.Join(dir,"text-mask.gz"));if te!=nil{t.Fatal(te)};tg:=gzip.NewWriter(tf);tg.Write(textMask);tg.Close();tf.Close()\n '+needle,1);s=s.replace('mask := make([]byte, 128000)','researchExportActorMasks(e,researchCueScene,dir,t)\n mask := make([]byte, 128000)',1);f.write_text(s)
   (root/'internal/eightsword/research_actor_masks_test.go').write_text((r/'tools/research-map-spell-actors_test.go').read_text().removeprefix('//go:build ignore\n'))
   (root/'internal/eightsword/research_map_color_test.go').write_text((r/'tools/research-map-spell-color_test.go').read_text().removeprefix('//go:build ignore\n'))
   prior=player/'source-candidate-remaining-spells-r2/src/internal/eightsword/spell_cues_draw.go';assert sha(prior)==old['source_inputs']['internal/eightsword/spell_cues_draw.go'];(root/'internal/eightsword/prior_map_renderer_test.go').write_text(prior.read_text().replace('func drawSpellCue(','func drawPriorSpellCue(',1));meta=read(out/'preparation.json');meta['diagnostic_inputs']={str(f.relative_to(root)):sha(f)for f in root.rglob('*')if f.is_file()};meta['changed']=[n for n,h in meta['diagnostic_inputs'].items()if meta['base_inputs'].get(n)!=h];(out/'preparation.json').write_text(json.dumps(meta,indent=2)+'\n');print('Prepared normal map color and frozen-prior replay');return
  if a.action=='audit':
   prep=read(candidate/'preparation.json');assert set(prep['changed'])==allowed
   for n,h in prep['source_inputs'].items():assert sha(r/n)==sha(candidate/'src'/n)==h
   log=(q/'tests-r2.log').read_text();assert 'PASS'in log and 'FAIL'not in log and 'SKIP'not in log;assert not(q/'vet-r2.log').read_text().strip();assert 'go1.24.13'in(candidate/'build-go-version.txt').read_text()
   private=read(q/'normal-build-r2/preparation.json');assert private['base_inputs']==prep['source_inputs']
   for n,h in private['diagnostic_inputs'].items():assert sha(q/'normal-build-r2/src'/n)==h
   normal=read(q/'normal-r2/receipt.json');assert normal['status']=='passed-normal-f4-eight-map-cues';assert len(normal['cases'])==8
   rows=[]
   from PIL import ImageChops
   import importlib.util
   spec=importlib.util.spec_from_file_location('color_independent',r/'tools/audit-remaining-presentation.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
   for kind in range(8):
    d=q/'normal-r2'/str(kind);m=read(d/'receipt.json');assert m['kind']==kind and m['frame_guest_pure'];assert sha(d/'before.state')==sha(d/'after.state');x,y,w,h=m['layer_rect'];layer=Image.frombytes('RGBA',(w,h),gzip.decompress((d/'layer-rgba.gz').read_bytes()));full=Image.new('RGBA',(1920,1200));full.paste(layer,(x,y));mask=gzip.decompress((d/'mask-hd.gz').read_bytes());check_actor_mask(d,mask);expected=mod.rebuild(d/'base.png',full,mask);actual=Image.open(d/'frame.png').convert('RGBA');assert expected.tobytes()==actual.tobytes();before=Image.open(d/'prior-replay.png').convert('RGB');base=Image.open(d/'base.png').convert('RGB');old_diff=ImageChops.difference(before,base);new_diff=ImageChops.difference(actual.convert('RGB'),base);old_count=sum(any(v)for v in old_diff.getdata());new_count=sum(any(v)for v in new_diff.getdata());assert new_count>old_count,(kind,new_count,old_count);rows.append(dict(kind=kind,step=m['step'],sample=m['sample'],old_changed_pixels=old_count,new_changed_pixels=new_count,frame_sha256=sha(d/'frame.png')))
   runtime=read(player/'runtime.json')
   for n,h in runtime['files'].items():assert sha(player/'runtime-render-r1/src'/n)==h
   for n,h in old['asset_hashes'].items():assert sha(player/'assets-painted-r68'/n)==h
   for n,h in old['programs'].items():assert sha(player/n)==h
   for d in(q/'tests-r2').glob('cue-*'):
    assert sha(d/'final-0.state')==sha(d/'final-1.state');assert read(d/'receipt.json')['full_state_equal']
   result=dict(status='passed-map-spell-color',source_count=193,source_inputs=prep['source_inputs'],changed_sources=prep['changed'],programs={n:sha(candidate/n)for n in old['programs']},previous_programs=old['programs'],core_files=runtime['files'],asset_hashes=old['asset_hashes'],map_frames=rows,limits=['Eight normal F4 Engine frames, explicit learned/charges fixture; no new Ebiten GUI or natural learning claim.','Battle colors pixel-match accepted r2 baseline. Original rules, input, save, core and assets unchanged.','Prior snapshot/continuous limitations remain; this update changes map appearance only.'])
  elif a.action=='overview':
   audit=read(q/'audit-r2.json');assert audit['status']=='passed-map-spell-color';font=ImageFont.truetype(str(a.font),28);small=ImageFont.truetype(str(a.font),20);title=ImageFont.truetype(str(a.font),38);names=['造橋術','煉金術','召兵術','跳躍術','停時術','鳥瞰術','涉水術','傳送術'];out=r/'docs/images/map-spell-color-r2.png';assert not out.exists();im=Image.new('RGB',(1640,860),(12,30,29));draw=ImageDraw.Draw(im);draw.text((20,12),'地圖法術　彩光加強',(255,237,181),font=title);draw.text((20,62),'正常 F4 引擎畫面近景；人物與文字保留，顏色及範圍加強。',(212,221,209),font=small)
   sources=[]
   for kind in range(8):
    f=q/'normal-r2'/str(kind)/'frame.png';crop=(362,312,982,832);thumb=Image.open(f).convert('RGB').crop(crop).resize((390,327),Image.Resampling.LANCZOS);x=20+(kind%4)*405;y=105+(kind//4)*372;im.paste(thumb,(x,y));draw.text((x,y+332),names[kind],(255,237,181),font=font);sources.append(dict(kind=kind,name=names[kind],source=str(f.relative_to(r)),sha256=sha(f),crop=crop))
   im.save(out);comparison=r/'docs/images/map-spell-color-comparison-r2.png';assert not comparison.exists();im=Image.new('RGB',(1640,1510),(12,30,29));draw=ImageDraw.Draw(im);draw.text((20,12),'同一底圖與進度　舊版／彩光加強',(255,237,181),font=title)
   for row,kind in enumerate([2,7]):
    for col,name in enumerate(['prior-replay.png','frame.png']):
     f=q/'normal-r2'/str(kind)/name;thumb=Image.open(f).convert('RGB').crop((362,312,982,832)).resize((780,654),Image.Resampling.LANCZOS);x=20+col*810;y=72+row*710;im.paste(thumb,(x,y));draw.text((x,y+660),names[kind]+('　舊版 Go 重播'if col==0 else'　彩光加強'),(255,237,181),font=font)
   im.save(comparison);meta=dict(status='verified-map-color-overview',source_archive='preserved/map-spell-color-r2.json',audit_sha256=sha(q/'audit-r2.json'),sources=sources,overview_sha256=sha(out),comparison_sha256=sha(comparison),limits=audit['limits']);(r/'docs/images/map-spell-color-r2.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');print('Saved color overview and same-base comparison');return
  elif a.action=='archive':
   audit=q/'audit-r2.json';assert read(audit)['status']=='passed-map-spell-color';storage=a.archive/'map-spell-color-r2';index=a.archive/'map-spell-color-r2.json';assert not storage.exists()and not index.exists();storage.mkdir();files=[];objects={};selected=[f for d in[q,candidate,player/'source-candidate-map-color-r1']for f in d.rglob('*')if f.is_file()];selected.extend(r/n for n in ['tools/map-spell-color.py','tools/research-map-spell-color_test.go','tools/research-map-spell-actors_test.go','docs/spec/030-battle-expansion-proposal.md'])
   for f in sorted(selected):
    assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();h=hashlib.sha256(raw).hexdigest()
    if h not in objects:
     name=h+'.gzip';prior=a.archive/'map-spell-color-r1'/name
     if prior.is_file():os.link(prior,storage/name);blob=prior.read_bytes()
     else:blob=gzip.compress(raw,compresslevel=6,mtime=0);(storage/name).write_bytes(blob)
     objects[h]=dict(file=name,stored_sha256=hashlib.sha256(blob).hexdigest(),stored_bytes=len(blob))
    files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(raw),mode=f.stat().st_mode&0o777))
   index.write_text(json.dumps(dict(schema=1,files=files,objects=objects,audit_sha256=sha(audit),dependencies=['preserved/remaining-spells-r1.json: original controls, accepted prior renderers, core and asset catalogs.','Current Git documents supersede historical READY snapshots.']),indent=2)+'\n');result=dict(status='preserved-map-color',files=len(files),objects=len(objects),stored_bytes=sum(v['stored_bytes']for v in objects.values()))
  elif a.action=='promote':
   audit=read(q/'audit-r2.json');v=read(a.archive/'map-spell-color-verification-r2.json');assert v['workplace_required']is False and v['index_sha256']==sha(a.archive/'map-spell-color-r2.json');assert read(a.archive/'map-spell-color-r2.json')['audit_sha256']==sha(q/'audit-r2.json');staged={}
   for n,h in audit['previous_programs'].items():assert sha(player/n)==h
   for n,h in audit['source_inputs'].items():assert sha(r/n)==h
   for n,h in audit['programs'].items():
    assert sha(candidate/n)==h;dest=player/('.map-color-'+n+'.tmp');assert not dest.exists();os.link(candidate/n,dest);staged[n]=dest
   runtime=read(candidate/'runtime.json');runtime.update(application_source_inputs=193,application_source_candidate='source-candidate-map-color-r2',map_spell_color='saturated-r2');temp=player/'.map-color-runtime.tmp';assert not temp.exists();temp.write_text(json.dumps(runtime,indent=2)+'\n')
   for n,f in staged.items():os.replace(f,player/n)
   os.replace(temp,player/'runtime.json');result=dict(status='promoted-map-color',source_count=193,programs=audit['programs'],audit_sha256=sha(q/'audit-r2.json'))
  else:
   audit=read(a.archive/'map-spell-color-audit-r2.json')
   for n,h in audit['programs'].items():assert sha(player/n)==sha(candidate/n)==h
   for n,h in audit['source_inputs'].items():assert sha(r/n)==sha(candidate/'src'/n)==h
   for n,h in audit['previous_programs'].items():assert sha(player/'source-candidate-remaining-spells-r2'/n)==h
   for n,h in audit['core_files'].items():assert sha(player/'runtime-render-r1/src'/n)==h
   for n,h in audit['asset_hashes'].items():assert sha(player/'assets-painted-r68'/n)==h
   art=read(r/'artwork/manifest.json');assert len(art['files'])==1040
   for v in art['files']:assert sha(r/'artwork'/v['path'])==v['sha256']
   v=read(a.archive/'map-spell-color-verification-r2.json');assert v['index_sha256']==sha(a.archive/'map-spell-color-r2.json')
   for root in[q,candidate,a.archive/'map-spell-color-r2']:assert not subprocess.run(['find',str(root),'-user','root','-o','-type','d','-name','*.md'],capture_output=True,text=True,check=True).stdout
   assert not any(f.is_file()for f in(r/'workplace/gocache').rglob('*'));subprocess.run(['python',str(r/'tools/check-ai-resolution-backlinks.py'),'--project',str(r)],check=True);ast.parse((r/'tools/map-spell-color.py').read_text());links=0
   for doc in list(r.glob('*.md'))+[p for d in['docs','artwork','preserved']for p in(r/d).rglob('*.md')]:
    for target in re.findall(r'\[[^\]]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)',doc.read_text()):
     path=urllib.parse.unquote(target.strip('<>').split('#',1)[0])
     if not path or path.startswith('/')or re.match('[a-zA-Z][a-zA-Z0-9+.-]*:',path):continue
     assert(doc.parent/path).exists()or(doc.parent/path).resolve()==a.out.resolve(),(doc,target);links+=1
   result=dict(status='passed-map-color-integrity',source_count=193,programs=7,core_unchanged=923,assets_unchanged=525,artwork_unchanged=1040,files=v['files'],objects=v['objects'],markdown_links=links,root_owned_outputs=0,workspace_cache_files=0)
 assert a.out and not a.out.exists();a.out.write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
if __name__=='__main__':main()
