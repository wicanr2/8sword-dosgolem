#!/usr/bin/env python3
"""Prepare/preserve isolated original evidence and Go origin-return candidate."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/annihilation-origin-r1'
BATCH='annihilation-origin-r1';PARENT='annihilation-roam-r1'
NEW=['prepare-annihilation-origin.py','export-annihilation-origin-ida.py','probe-annihilation-origin.go','origin-map.go','annihilation-origin.go','annihilation-origin_test.go','check-annihilation-origin-ui.py','check-annihilation-origin.py','annihilation-origin.sh']
PATCHED=['research-battle-resume.go','research-controlled-battle.go','normal-encounter-ui.go']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
    with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def helper(r):
    sp=importlib.util.spec_from_file_location('h',r/'tools/prepare-owned-army-ui.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
def replace(p,a,b):
    s=p.read_text();assert s.count(a)==1,(p,a,s.count(a));p.write_text(s.replace(a,b))
def patch(src):
    p=src/'tools/research-battle-resume.go';replace(p,'r.Result <= 2','r.Result <= 3')
    replace(p,'// First accept an ordinary Go action or settlement retaining the anchor.','ref,x:=savedResume(i.After.World);if x!=nil{return x};if ref!=nil&&ref.Phase=="return"&&ref.Result==3{return verifyOriginIntent(s,i,before,after)}\n // First accept an ordinary Go action or settlement retaining the anchor.')
    replace(src/'tools/research-controlled-battle.go','// Go has already applied the world result.','if b.Result==3 {if e:=applyOriginReturn(m,b);e!=nil{return false,e}}\n // Go has already applied the world result.')
    p=src/'tools/normal-encounter-ui.go'
    replace(p,'if roamAvailable(x) {s="roam"}','if roamAvailable(x) {s="roam";if a<360{s="origin"}}')
    replace(p,'case "roam":','case "origin":\n        var packed []byte;packed,e=originPackedInput();if e==nil{e=settleRuntimeOrigin(x.Bridge,x.Engine.Oracle,packed)}\n    case "roam":')
    replace(p,'p.button("roam", "冒險浪跡江湖", image.Rect(60,190,650,260),false,true)','p.button("origin", "傳送回起點",image.Rect(60,190,350,260),false,true)\n        p.button("roam", "冒險浪跡江湖",image.Rect(370,190,650,260),false,true)')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','archive','verify','publish']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--images',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
    if a.action=='verify':
        d=read(a.archive/(BATCH+'.json'))
        for f in d['files']:
            o=d['objects'][f['sha256']];p=a.archive/BATCH/o['file'];assert sha(p)==o['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
        write(a.out,dict(status='passed-detached-annihilation-origin',files=len(d['files']),objects=len(d['objects'])));return
    r=a.project;q=r/REL;m=helper(r);deps=m.dependencies(r)
    if a.action=='prepare':
        assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir();d=read(r/'preserved'/f'{PARENT}.json')
        for f in d['files']:
            rel=f['path'].split('/'+PARENT+'/',1)[1]
            if not(rel.startswith(('go-src/','inputs/','ui-assets/'))or rel in['probe.mod','probe.sum','xcheck','annihilation-roam-execution-r1.json']):continue
            t=q/rel;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(m.stored(r,PARENT,'/'+PARENT+'/'+rel));t.chmod(f['mode'])
        write(q/'baseline.json',deps);(q/'ida').mkdir()
        (q/'inputs/origin-source.state').write_bytes(m.stored(r,'owned-defeat-r1','/inputs/oracle-state.state'))
        packed=(r/'workplace/intake-20261023/sources/game/8sword/MAP1.AY').read_bytes();assert hashlib.sha256(packed).hexdigest()=='7835299e69ca627034132cb6dffa6f40df640f46dfce430642ad9780093a346a';(q/'inputs/origin-terrain-packed.ay').write_bytes(packed)
        shutil.copyfile(r/'docs/spec/world-army-consumers-r1.json',q/'inputs/world-army-consumers-at-origin-export.json')
    else:assert deps==read(q/'baseline.json')
    if a.action in['prepare','freeze']:
        if a.action=='freeze':
            for n in PATCHED:(q/'go-src/tools'/n).write_bytes(m.stored(r,PARENT,'/'+PARENT+'/go-src/tools/'+n))
            patch(q/'go-src')
        for n in NEW:
            if(r/'tools'/n).is_file():shutil.copyfile(r/'tools'/n,q/'go-src/tools'/n)
        if a.action=='freeze':
            d=read(q/'annihilation-roam-execution-r1.json');ui=d['ui_build'].replace('/out/annihilation-roam-ui','/out/annihilation-origin-ui')+' tools/origin-map.go tools/annihilation-origin.go';test=ui.replace('go build','go test').replace('-o /out/annihilation-origin-ui ','')+' tools/annihilation-origin_test.go -run ^TestAnnihilationOrigin$ -count=1';write_path=q/'annihilation-origin-execution-r1.json';write_path.write_text(json.dumps(dict(original_build='go build -mod=readonly -modfile=/out/probe.mod -o /out/origin-probe tools/probe-annihilation-origin.go tools/origin-map.go',original_run='/out/origin-probe -root /game -input /out/inputs -out /out/original-r3',ui_build=ui,fixture_build=ui.replace('/out/annihilation-origin-ui','/out/annihilation-origin-fixture')+' tools/battle-resume-fixture.go tools/rear-actions-fixture.go',ui_test=test),indent=2)+'\n')
        return
    if a.action=='publish':
        from PIL import Image
        g=read(q/'gui-r1/receipt.json');assert g['status']=='passed-annihilation-origin-ui';items=[]
        for row in g['screens']:
            if row['name']not in['loss','returned']:continue
            source=q/'gui-r1'/row['phase']/row['canvas'];dest=a.images/('annihilation-origin-'+row['name']+'-r1.png');assert not dest.exists();im=Image.open(source);im.thumbnail((960,600),Image.Resampling.LANCZOS);im.save(dest);items.append(dict(source=str(source.relative_to(r)),source_sha256=sha(source),published=dest.name,published_sha256=sha(dest)))
        write(a.images/'annihilation-origin-runtime-r1.json',dict(images=items,controlled_initial_army_and_native_entry_and_enemy=True,normal_ui_clicks=True,production_promoted=False));return
    folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
    for f in sorted(q.rglob('*')):
        if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
        assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();h=hashlib.sha256(raw).hexdigest();obj=folder/(h+'.gz')
        if h not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
        files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(raw),mode=f.stat().st_mode&0o777))
    write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Original inputs, VM objects and full frames local-only; no formal promotion.'))
if __name__=='__main__':main()
