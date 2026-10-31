#!/usr/bin/env python3
"""Isolated, read-only HD recruitment cards on the current Go candidate."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,struct,io
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/recruit-icons-r1'
BATCH='recruit-icons-r1'
NEW=['export-recruit-shop-ida.py','research-recruit-icons.go','recruit-icons-ui.go','prepare-recruit-icons.py','check-recruit-icons.py','check-recruit-icons-ui.py','recruit-icons.sh','research-recruit-icons_test.go','owned-army-ui-xcheck.go','recruit-native-main.go']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
    with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def helper(r):
    sp=importlib.util.spec_from_file_location('previous',r/'tools/prepare-owned-army-ui.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
def replace(p,a,b):
    s=p.read_text();assert s.count(a)==1,(p,a,s.count(a));p.write_text(s.replace(a,b))
def patch(src):
    p=src/'tools/world-army-review_main.go'
    replace(p,'g.Bound = true','if e:=installRecruitIcons(g.Engine);e!=nil{return e}\n g.Bound = true')
    replace(p,'g.Frame = g.Engine.Frame()','g.Frame = composeRecruitIcons(g.Engine,g.Engine.Frame())')
    replace(p,'return state','if recruitIconsCurrent!=nil {state["recruit_icons"]=recruitIconsCurrent.state()}\n return state')
    replace(p,'for i, n := range pairWorldResources(g.Snapshot.World).words() {','if g.Owned {for i, n := range pairWorldResources(g.Snapshot.World).words() {')
    replace(p,'if g.Owned {\n\t\tp, e := installWorldArmyPort', '}\n if g.Owned {\n\t\tp, e := installWorldArmyPort')
    replace(p,'if e := runArmyReview(); e != nil {','if e := runRecruitClient(); e != nil {')
def patch_probe(p):
    replace(p,'"encoding/json"','"encoding/json"\n "encoding/binary"')
    replace(p,'apply := flag.Bool(', 'icons := flag.Bool("icons", true, "read-only HD recruit icon")\n apply := flag.Bool(')
    replace(p,'png.Encode(f, e.Frame())','png.Encode(f, composeRecruitIcons(e,e.Frame()))')
    replace(p,'initialArmy := e.Oracle.Bytes','if *icons {waMust(installRecruitIcons(e))}\n initialArmy := e.Oracle.Bytes')
    replace(p,'waMust(os.Mkdir(*out, 0755))','waMust(os.Mkdir(*out, 0755))\n pcm,pcmErr:=os.OpenFile(filepath.Join(*out,"PCM.raw"),os.O_CREATE|os.O_EXCL|os.O_WRONLY,0600);waMust(pcmErr);defer pcm.Close()')
    replace(p,'e.RenderAudio()','samples:=e.RenderAudio();buf:=make([]byte,len(samples)*2);for i,s:=range samples{binary.LittleEndian.PutUint16(buf[i*2:],uint16(s))};_,pcmErr=pcm.Write(buf);waMust(pcmErr)')
    s=p.read_text();at=s.rfind('\n}');assert at>0;p.write_text(s[:at]+'\n if recruitIconsCurrent!=nil {waWrite(filepath.Join(*out,"icons.json"),recruitIconsCurrent.state())}\n'+s[at:])
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','archive','verify','publish']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--out',type=Path);p.add_argument('--images',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
    if a.action=='verify':
        d=read(a.archive/(BATCH+'.json'))
        for f in d['files']:
            v=d['objects'][f['sha256']];obj=a.archive/BATCH/v['file'];assert sha(obj)==v['stored_sha256'];b=gzip.decompress(obj.read_bytes());assert len(b)==f['bytes']and hashlib.sha256(b).hexdigest()==f['sha256']
        write(a.out,dict(status='passed-detached-recruit-icons',files=len(d['files']),objects=len(d['objects'])));return
    r=a.project;q=r/REL;m=helper(r);deps=m.dependencies(r)
    if a.action=='prepare':
        assert q.is_dir()and q.stat().st_uid==1000 and not(q/'go-src').exists();d=read(r/'preserved/battle-resume-r1.json')
        for f in d['files']:
            rel=f['path'].split('/battle-resume-r1/',1)[1]
            if not(rel.startswith(('go-src/','inputs/','ui-assets/'))or rel in ['probe.mod','probe.sum','xcheck','resume-execution-r1.json']):continue
            t=q/rel;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(m.stored(r,'battle-resume-r1','/battle-resume-r1/'+rel));t.chmod(f['mode'])
        (q/'pair-init').write_bytes(m.stored(r,'battle-resume-r1','/battle-resume-r1/resume-probe'));(q/'pair-init').chmod(0o700)
        shutil.copyfile(r/'tools/probe-world-army.go',q/'go-src/tools/probe-world-army.go')
        patch_probe(q/'go-src/tools/probe-world-army.go')
        patch(q/'go-src')
        old=read(q/'resume-execution-r1.json');ui=old['ui_build'].replace('/out/resume-ui','/out/recruit-ui')+' tools/recruit-icons-ui.go tools/recruit-native-main.go'
        probe=old['probe_build'].replace('/out/resume-probe','/out/recruit-probe').replace('tools/probe-battle-resume.go','tools/probe-world-army.go tools/recruit-icons-ui.go')
        write(q/'execution-r1.json',dict(ui_build=ui,probe_build=probe,source_base='preserved/battle-resume-r1.json',formal_changed=False,source_schema_promoted=False,go_image_sha256='8ed6bdee2bce1f32f804e888f942b25bbf62f2165a43344bb4587f3371de0581',uid=1000,network='none',memory='3g',cpus=2,pids=192));write(q/'baseline.json',deps)
    else:assert deps==read(q/'baseline.json')
    if a.action=='publish':
        from PIL import Image,ImageDraw,ImageFont
        audit=read(r/'preserved/recruit-icons-audit-r1.json');assert audit['status']=='passed-hd-recruit-icons-candidate'
        assert a.images.is_dir()and a.images.stat().st_uid==1000
        catalog=read(q/'inputs/army-catalog.json');names={v['native_kind']:v['name']for v in catalog['profiles']if v.get('native_kind',0)>0}
        index=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));fh=m.FONT_SHA['noto'];obj=index['objects'][fh];font_raw=gzip.decompress((r/'preserved'/obj['path']).read_bytes());assert hashlib.sha256(font_raw).hexdigest()==fh
        font=ImageFont.truetype(io.BytesIO(font_raw),24,index=3);sheet=Image.new('RGBA',(1100,1400),(7,36,26,255));draw=ImageDraw.Draw(sheet)
        for k in range(1,26):
            x,y=(k-1)%5*220,(k-1)//5*280;draw.rectangle((x+4,y+4,x+215,y+275),outline=(176,150,85,255),width=2)
            im=Image.open(q/f'asset-test-r2/kind{k:02d}.png').convert('RGBA');im=im.crop(im.getchannel('A').getbbox());im.thumbnail((184,218),Image.Resampling.LANCZOS);sheet.alpha_composite(im,(x+(220-im.width)//2,y+12+(218-im.height)//2))
            label=f'{k:02d} {names[k]}';assert draw.textlength(label,font=font)<=202;draw.text((x+110,y+250),label,font=font,anchor='mm',fill=(255,242,196,255))
        sheet.save(q/'overview-full-r1.png');small=sheet.resize((880,1120),Image.Resampling.LANCZOS);path=a.images/'recruit-unit-icons-r1.png';assert not path.exists();small.save(path)
        meta=audit['gui']['screens'][0];source=q/'gui-r4'/meta['phase']/meta['canvas'];im=Image.open(source).convert('RGB');im.thumbnail((960,600),Image.Resampling.LANCZOS);preview=a.images/'recruit-shop-hd-icons-r1.png';assert not preview.exists();im.save(preview)
        write(a.images/'recruit-unit-icons-r1.json',dict(audit_sha256=sha(r/'preserved/recruit-icons-audit-r1.json'),overview_sha256=sha(path),preview_sha256=sha(preview),font_sha256=fh,font='Noto Sans CJK TC Black',source_rows=audit['asset_test']['rows'],preview_source=str(source.relative_to(r)),preview_source_sha256=sha(source),rights='Derived from existing approved HD caches. Complete frames and source inputs remain in the local permanent batch.'))
        return
    if a.action in ['prepare','freeze']:
        if a.action=='freeze':
            p=q/'go-src/tools/world-army-review_main.go';p.write_bytes(m.stored(r,'battle-resume-r1','/battle-resume-r1/go-src/tools/world-army-review_main.go'));patch(q/'go-src')
            e=read(q/'execution-r1.json')
            if 'tools/recruit-native-main.go'not in e['ui_build']:e['ui_build']+=' tools/recruit-native-main.go';(q/'execution-r1.json').write_text(json.dumps(e,ensure_ascii=False,indent=2)+'\n')
        for n in NEW:
            if(r/'tools'/n).is_file():shutil.copyfile(r/'tools'/n,q/'go-src/tools'/n)
        text=(r/'tools/research-recruit-icons.go').read_text().removeprefix('//go:build ignore\n');(q/'go-src/internal/eightsword/recruit_icons_candidate.go').write_text(text)
        if(r/'tools/research-recruit-icons_test.go').is_file():
            text=(r/'tools/research-recruit-icons_test.go').read_text().removeprefix('//go:build ignore\n');(q/'go-src/internal/eightsword/recruit_icons_candidate_test.go').write_text(text)
        return
    folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
    for f in sorted(q.rglob('*')):
        if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
        assert f.stat().st_uid==1000 and not f.is_symlink();b=f.read_bytes();h=hashlib.sha256(b).hexdigest();obj=folder/(h+'.gz')
        if h not in objects:obj.write_bytes(gzip.compress(b,compresslevel=6,mtime=0));objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
        files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(b),mode=f.stat().st_mode&0o777))
    write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Full original inputs and complete objects remain local and excluded from Git.'))
if __name__=='__main__':main()
