#!/usr/bin/env python3
"""Preserve eight image_gen masters, bind them to the isolated Go UI, publish galleries."""
import argparse,gzip,hashlib,importlib.util,io,json,os,shutil,struct,tempfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,__version__
REL='workplace/probe-20261023/graphics-first/battle-r1/openkb-hd-r1'
BATCH='openkb-hd-r1'
NEW=['openkb-hd-art.go','openkb-hd-probe.go','prepare-openkb-hd.py','check-openkb-hd.py','check-openkb-hd-ui.py','openkb-hd.sh']
PATCHED=['world-army-review_main.go','world-army-review_draw.go','world-army-dismiss_draw.go','owned-battle-ui_draw.go']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
    if p.exists():assert read(p)==v,(p,'different existing output');return
    with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def helper(r):
    sp=importlib.util.spec_from_file_location('old',r/'tools/prepare-owned-army-ui.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
def replace(p,a,b):
    s=p.read_text();assert s.count(a)==1,(p,a,s.count(a));p.write_text(s.replace(a,b))
def patch(src):
    p=src/'tools/world-army-review_main.go'
    replace(p,'g.Bound = true','hdUnitArt=loadHDUnitArtwork(g.Engine,flag.Lookup("ui-assets").Value.String(),g.Fonts.CatalogRawSHA)\n g.Bound = true')
    replace(p,'return state','state["unit_art"]=hdUnitArtworkStatus()\n return state')
    p=src/'tools/world-army-review_draw.go'
    replace(p,'if fonts.Atlases[font] == nil {','resetHDUnitArtwork("review")\n if fonts.Atlases[font] == nil {')
    replace(p,'p.text(fmt.Sprintf("review-%d-name", i)', 'drawHDUnitArtwork(out,r.ID,image.Rect(x+18,y+75,x+220,y+320),false)\n p.text(fmt.Sprintf("review-%d-name", i)')
    for y in ['78','158','225','285']:replace(p,'image.Rect(x+24, y+'+y+',','image.Rect(x+240, y+'+y+',')
    p=src/'tools/world-army-dismiss_draw.go'
    replace(p,'out := image.NewRGBA','resetHDUnitArtwork("dismiss")\n out := image.NewRGBA')
    replace(p,'p.text(fmt.Sprintf("dismiss-%d-name", i)','drawHDUnitArtwork(out,r.ID,image.Rect(x+16,y+66,x+200,y+210),false)\n p.text(fmt.Sprintf("dismiss-%d-name", i)')
    replace(p,'image.Rect(x+25, y+85','image.Rect(x+220, y+85');replace(p,'image.Rect(x+25, y+155','image.Rect(x+220, y+155')
    p=src/'tools/owned-battle-ui_draw.go'
    replace(p,'out := image.NewRGBA','resetHDUnitArtwork("battle")\n out := image.NewRGBA')
    replace(p,'p.text("unit", name, image.Rect(rect.Min.X+16, rect.Min.Y+58, rect.Max.X-16, rect.Min.Y+112), 38, uiGold, true)','p.text("unit", name, image.Rect(rect.Min.X+12, rect.Min.Y+54, rect.Max.X-12, rect.Min.Y+98), 30, uiGold, true)\n drawHDUnitArtwork(out,stack.Unit,image.Rect(rect.Min.X+12,rect.Min.Y+105,rect.Min.X+130,rect.Min.Y+220),side==1)')
    replace(p,'image.Rect(rect.Min.X+16, rect.Min.Y+120, rect.Max.X-16, rect.Min.Y+166), 34, 18','image.Rect(rect.Min.X+138, rect.Min.Y+108, rect.Max.X-10, rect.Min.Y+164), 28, 10')
    replace(p,'image.Rect(rect.Min.X+16, rect.Min.Y+178, rect.Max.X-16, rect.Min.Y+220), 28','image.Rect(rect.Min.X+138, rect.Min.Y+178, rect.Max.X-10, rect.Min.Y+220), 24')
def capture(a):
    r,art=a.project,a.artwork;assert art.stat().st_uid==1000;plan=read(r/'artwork/openkb-hd-generation-r1.json');old=read(art/'manifest.json');prior=sha(art/'manifest.json');assert len(old['files'])==1040;rows=[];m=helper(r)
    def save(raw,path,source,role):
        target=art/path;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert target.read_bytes()==raw
        else:target.write_bytes(raw)
        row=dict(source=source,path=path,sha256=sha(target),bytes=len(raw),role=role,basis='User authorized same-style HD additions and requested these eight units in README/game screenshots.')
        if target.suffix=='.png':
            with Image.open(target)as im:row['image']=dict(size=list(im.size),mode=im.mode)
        rows.append(row);return row
    style=m.stored(r,'recruit-icons-r1','/recruit-icons-r1/asset-test-r2/kind01.png');save(style,'approved/references/openkb-hd-r1/native01-style.png','preserved/recruit-icons-r1.json#asset-test-r2/kind01.png','reference')
    adopted=[]
    for entry in plan['rows']:
        generated=a.generated/Path(entry['generated_path']).relative_to('/home/anr2/.codex/generated_images');assert generated.is_file()and generated.stat().st_uid==1000
        master=save(generated.read_bytes(),entry['master'],entry['generated_path'],'master');im=Image.open(art/entry['master']);assert im.mode=='RGBA'and 512<=min(im.size)<=max(im.size)<=4096;alpha=im.getchannel('A');assert alpha.getextrema()==(0,255)and alpha.getbbox()
        source=a.openkb/'data/free'/(entry['file']+'.png');assert source.is_file();ref=save(source.read_bytes(),'approved/references/openkb-hd-r1/'+entry['file']+'.png','openkb-code/data/free/'+source.name,'reference')
        record=dict(entry,master_sha256=master['sha256'],reference_sha256=ref['sha256'],reference=ref['path'],master_bytes=master['bytes'],role='Single static presentation sprite; no rule/animation parity claim.')
        save((json.dumps(record,ensure_ascii=False,indent=2)+'\n').encode(),entry['provenance'],'artwork/openkb-hd-generation-r1.json#'+entry['id'],'provenance');adopted.append(record)
    plan.update(status='adopted-isolated-presentation',rows=adopted);save((json.dumps(plan,ensure_ascii=False,indent=2)+'\n').encode(),'approved/provenance/openkb-hd-r1/generation.json','artwork/openkb-hd-generation-r1.json','provenance')
    assert sha(art/'manifest.json')==prior;old['files'].extend(rows);old.setdefault('additions',[]).append(dict(index='openkb-hd-preservation-r1.json',previous_manifest_sha256=prior,files=len(rows)));fd,name=tempfile.mkstemp(prefix='.openkb-art-',dir=art);os.close(fd);tmp=Path(name);tmp.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,art/'manifest.json')
    write(a.out,dict(status='preserved-eight-openkb-hd-masters',prior_files=1040,added_files=len(rows),manifest_files=len(old['files']),prior_manifest_sha256=prior,manifest_sha256=sha(art/'manifest.json'),rows=adopted));return
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['capture','prepare','freeze','gallery','publish','archive','verify']);
    for n in ['project','artwork','generated','openkb','out','archive','images']:p.add_argument('--'+n,type=Path)
    a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000 and __version__=='11.3.0'
    if a.action=='capture':capture(a);return
    if a.action=='verify':
        d=read(a.archive/(BATCH+'.json'))
        for f in d['files']:
            v=d['objects'][f['sha256']];obj=a.archive/BATCH/v['file'];assert sha(obj)==v['stored_sha256'];raw=gzip.decompress(obj.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
        write(a.out,dict(status='passed-detached-openkb-hd',files=len(d['files']),objects=len(d['objects'])));return
    r=a.project;q=r/REL;m=helper(r);deps=m.dependencies(r)
    if a.action=='prepare':
        assert q.is_dir()and q.stat().st_uid==1000;d=read(r/'preserved/camp-stock-r1.json')
        for f in d['files']:
            rel=f['path'].split('/camp-stock-r1/',1)[1]
            if not(rel.startswith(('go-src/','inputs/','ui-assets/'))or rel in ['probe.mod','probe.sum','xcheck','camp-probe','camp-execution-r1.json']):continue
            t=q/rel;t.parent.mkdir(parents=True,exist_ok=True);raw=m.stored(r,'camp-stock-r1','/camp-stock-r1/'+rel)
            if t.exists():assert t.read_bytes()==raw,(t,'existing candidate differs')
            else:t.write_bytes(raw)
            t.chmod(f['mode'])
        e=read(q/'camp-execution-r1.json');ui=e['ui_build'].replace('/out/camp-ui','/out/openkb-ui')+' tools/openkb-hd-art.go';probe=e['probe_build'].replace('/out/camp-probe','/out/openkb-probe').replace('tools/probe-camp-stock.go','tools/openkb-hd-probe.go')+' tools/openkb-hd-art.go';write(q/'openkb-execution-r1.json',dict(ui_build=ui,fixture_build=ui.replace('/out/openkb-ui','/out/openkb-ui-fixture')+' tools/battle-resume-fixture.go',probe_build=probe,source_base='preserved/camp-stock-r1.json'));write(q/'baseline.json',deps)
        art=read(r/'artwork/openkb-hd-preservation-r1.json');pack=dict(schema=1,catalog_raw_sha256=sha(q/'inputs/army-catalog.json'),rows=[])
        for row in art['rows']:
            im=Image.open(r/'artwork'/row['master']).convert('RGBA');im=im.crop(im.getchannel('A').getbbox());im.thumbnail((472,472),Image.Resampling.LANCZOS);canvas=Image.new('RGBA',(512,512));canvas.alpha_composite(im,((512-im.width)//2,(512-im.height)//2));name='unit-'+row['file']+'.png';canvas.save(q/'ui-assets'/name);pack['rows'].append(dict(id=row['id'],file=name,sha256=sha(q/'ui-assets'/name)))
        write(q/'ui-assets/unit-art.json',pack)
        # Explicit, separate showcase progress. Native army stays unchanged.
        w=read(q/'inputs/world-normal.json');w['army']['recruit_rank']=5;w['progress']['rank']=5;w['army']['slots']=[dict(unit='openkb:'+id,count=count)for id,count in [('arcr',20),('pike',10),('wolf',50),('skel',40),('troll',2),('drui',4)]];write(q/'inputs/showcase-a.json',w)
        w['army']['slots']=[dict(unit=id,count=count)for id,count in [('openkb:vamp',3),('openkb:drag',1),('native:01',30),('',0),('',0),('',0)]];write(q/'inputs/showcase-b.json',w)
    else:assert deps==read(q/'baseline.json')
    if a.action in ['prepare','freeze']:
        if a.action=='freeze':
            for n in PATCHED:(q/'go-src/tools'/n).write_bytes(m.stored(r,'camp-stock-r1','/camp-stock-r1/go-src/tools/'+n))
        for n in NEW+['battle-resume-fixture.go']:
            if(r/'tools'/n).is_file():shutil.copyfile(r/'tools'/n,q/'go-src/tools'/n)
        patch(q/'go-src');return
    if a.action in ['gallery','publish']:publish(r,q,a.images,m,a.action=='gallery');return
    folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
    for f in sorted(q.rglob('*')):
        if not f.is_file()or 'build-cache'in f.relative_to(q).parts:continue
        assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();h=hashlib.sha256(raw).hexdigest();obj=folder/(h+'.gz')
        if h not in objects:obj.write_bytes(gzip.compress(raw,compresslevel=6,mtime=0));objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
        files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(raw),mode=f.stat().st_mode&0o777))
    write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Complete local frames, original inputs and objects excluded from Git. Published README images are separately indexed.'))
def publish(r,q,images,m,gallery_only=False):
    assert images.is_dir()and images.stat().st_uid==1000
    index=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));h=m.FONT_SHA['noto'];raw=gzip.decompress((r/'preserved'/index['objects'][h]['path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==h
    fonts={n:ImageFont.truetype(io.BytesIO(raw),n,index=3)for n in [22,26,30,36,42]}
    art=read(r/'artwork/openkb-hd-preservation-r1.json');pack=read(q/'ui-assets/unit-art.json');mapping={v['id']:v for v in pack['rows']};sheet=Image.new('RGBA',(1600,1020),(7,36,26,255));draw=ImageDraw.Draw(sheet)
    draw.text((800,34),'openKB 八種新增單位・中國古風 HD',font=fonts[42],anchor='mm',fill=(232,205,132,255));draw.text((800,82),'左：openKB 來源　右：神州八劍 HD 靜態圖像',font=fonts[26],anchor='mm',fill=(245,234,197,255));records=[]
    def fit(im,area,resample):
        im=im.crop(im.getchannel('A').getbbox());im.thumbnail((area[2]-area[0],area[3]-area[1]),resample);x=area[0]+(area[2]-area[0]-im.width)//2;y=area[1]+(area[3]-area[1]-im.height)//2;sheet.alpha_composite(im,(x,y))
    for i,row in enumerate(art['rows']):
        x,y=i%4*400,i//4*430+130;draw.rectangle((x+5,y+5,x+394,y+423),outline=(150,135,83,255),width=2);assert draw.textlength(row['name'],font=fonts[30])<=368;draw.text((x+200,y+30),row['name'],font=fonts[30],anchor='mm',fill=(232,205,132,255))
        ref=r/'artwork'/row['reference'];source=Image.open(ref).convert('RGBA').crop((0,0,48,34));key=source.getpixel((0,0))[:3]
        for yy in range(source.height):
            for xx in range(source.width):
                p=source.getpixel((xx,yy))
                if p[:3]==key:source.putpixel((xx,yy),(0,0,0,0))
        # Enlarge retro pixels without inventing source detail.
        source=source.resize((192,136),Image.Resampling.NEAREST);fit(source,(x+20,y+88,x+155,y+342),Image.Resampling.NEAREST)
        asset=q/'ui-assets'/mapping[row['id']]['file'];fit(Image.open(asset).convert('RGBA'),(x+165,y+62,x+380,y+366),Image.Resampling.LANCZOS)
        draw.text((x+85,y+388),'來源',font=fonts[22],anchor='mm',fill=(181,193,155,255));draw.text((x+270,y+388),'HD',font=fonts[22],anchor='mm',fill=(245,234,197,255))
        info=Image.open(ref).info;records.append(dict(id=row['id'],name=row['name'],master=row['master'],master_sha256=row['master_sha256'],source=row['reference'],source_sha256=sha(ref),runtime_asset_sha256=sha(asset),source_first_frame=[0,0,48,34],display_color_key=list(key),source_metadata={k:str(v)for k,v in info.items()if k in ['Author','License','LicenseURL','Copyright']}))
    draw.text((800,1002),'新增圖示已接隔離 Go 候選；完整世界與自然取得仍待接入',font=fonts[22],anchor='mm',fill=(181,193,155,255))
    new=images/'openkb-eight-original-hd-r1.png'
    if not new.exists():sheet.convert('RGB').save(new)
    old=Image.open(r/'docs/images/troops-all-original-hd-r3.png').convert('RGBA');combined=Image.new('RGBA',(2000,100+old.height+1275),(7,36,26,255));d=ImageDraw.Draw(combined);d.text((1000,48),'神州八劍 25 種原版 ＋ openKB 8 種新增・共 33 種',font=fonts[42],anchor='mm',fill=(232,205,132,255));combined.alpha_composite(old,(0,100));combined.alpha_composite(sheet.resize((2000,1275),Image.Resampling.LANCZOS),(0,100+old.height));allpath=images/'troops-all-original-hd-with-openkb-r4.png'
    if not allpath.exists():combined.convert('RGB').save(allpath)
    record=dict(schema=1,units=records,count=8,total_native_plus_added=33,source_font_sha256=h,original_25_sheet_sha256=sha(r/'docs/images/troops-all-original-hd-r3.png'),overview_sha256=sha(new),combined_overview_sha256=sha(allpath),method='Eight source first poses and generated static HD sprites; source color key for display, nearest-neighbor retro enlargement. Existing 25-unit sheet embedded unchanged.',rights='Source previews: openKB free sprites, driedfruit and other upstream contributors; per-file author/license metadata above. Complete inputs remain local.')
    write(images/'openkb-eight-original-hd-r1.json',record)
    if gallery_only:return
    audit=read(r/'preserved/openkb-hd-audit-r1.json');assert audit['status']=='passed-openkb-hd-presentation';gui=read(q/'gui-r1/receipt.json');screens=[]
    for phase,name,public in [('army-a','army-hd','openkb-army-a-hd-r1.png'),('army-b','army-hd','openkb-army-b-hd-r1.png'),('battle-warm','battle-hd','openkb-battle-hd-r1.png')]:
        folder=q/'gui-r1'/phase;meta=read(folder/(name+'.json'));source=folder/meta['last_capture'];im=Image.open(source).convert('RGB');im.thumbnail((1280,800),Image.Resampling.LANCZOS);target=images/public;assert not target.exists();im.save(target);screens.append(dict(image=public,sha256=sha(target),source=str(source.relative_to(r)),source_sha256=sha(source),controlled_initial_army=True,controlled_battle_entry=phase.startswith('battle')))
    write(images/'openkb-game-screenshots-r1.json',dict(screens=screens,audit_sha256=sha(r/'preserved/openkb-hd-audit-r1.json'),natural_acquisition=False,source='Actual Ebiten/Go window; full submitted frame and X11 SHA checked independently.'))
if __name__=='__main__':main()
