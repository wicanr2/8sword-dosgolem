#!/usr/bin/env python3
"""Resume a verified total loss through the original roam outcome, in isolation."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/annihilation-roam-r1'
BATCH='annihilation-roam-r1'
PARENT='rear-actions-r1'
NEW=['prepare-annihilation-roam.py','annihilation-roam.go','annihilation-roam_test.go','check-annihilation-roam-ui.py','check-annihilation-roam.py','annihilation-roam.sh']
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
    replace(src/'tools/research-controlled-battle.go','func (b *controlledBattle) settle(input DefeatInput) error {','func (b *controlledBattle) settle(input DefeatInput) error {\n    if input.Reason=="annihilation" && (input.Choice!="roam" || input.Origin!=nil) {return errors.New("only roam is admitted for total loss")}')
    p=src/'tools/research-battle-resume.go'
    replace(p,'r.Result <= 1','r.Result <= 2')
    replace(p,'\t} else {\n\t\treturn nil, errors.New("resume unsupported battle result")','\t} else if before.Battle.State.Result == "loss" {\n        input = DefeatInput{Reason:"annihilation", Choice:"roam"}\n        next.Result = 2\n    } else {\n\t\treturn nil, errors.New("resume unsupported battle result")')
    p=src/'tools/normal-encounter-ui.go'
    replace(p,'s = "retreat"','s = "retreat"\n        if roamAvailable(x) {s="roam"}')
    replace(p,'case "retreat":\n','case "roam":\n        e=settleRuntimeRoam(x.Bridge,x.Engine.Oracle)\n    case "retreat":\n')
    replace(p,'p.button("retreat", "撤退返回地圖", image.Rect(60, 190, 650, 260), false, x.UI.World.Battle != nil && x.UI.World.Battle.State.Result == "")','if roamAvailable(x) {\n        p.button("roam", "冒險浪跡江湖", image.Rect(60,190,650,260),false,true)\n    } else {\n        p.button("retreat", "撤退返回地圖", image.Rect(60,190,650,260),false,x.UI.World.Battle != nil && x.UI.World.Battle.State.Result == "")\n    }')
    replace(p,'out, texts := paintBattleUI(x.UI, f)','out, texts := paintBattleUI(x.UI, f)\n    if roamAvailable(x) {\n        uiFill(out,image.Rect(1240,115,1870,180),out.RGBAAt(5,5))\n        p:=armyUIPaint{Fonts:f,Canvas:out,Font:id}\n        p.text("phase", "全軍覆沒，請選擇去向", image.Rect(1250,120,1860,178),34,uiGold,true)\n        kept:=texts[:0];for _,t:=range texts{if t.Role!="phase"{kept=append(kept,t)}};texts=append(kept,p.Texts...)\n    }')
def fonts(r,q):
    source=(r/'tools/prepare-monthly-wide.py').read_text();a=source.index('def fonts(r,q):');b=source.index('def main():',a);fn=source[a:b];start=fn.index("text='");end=fn.index("';extra=",start);fn=fn[:start]+"text='冒險浪跡江湖全軍覆沒，請選擇去向。傳送回起點待接入。'"+fn[end+1:]
    ns=dict(globals());exec('import gzip,hashlib,io,json\nfrom PIL import Image,ImageDraw,ImageFont,__version__\n'+fn,ns);ns['fonts'](r,q)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','archive','verify','publish']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--images',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
    if a.action=='verify':
        d=read(a.archive/(BATCH+'.json'))
        for f in d['files']:
            o=d['objects'][f['sha256']];p=a.archive/BATCH/o['file'];assert sha(p)==o['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
        write(a.out,dict(status='passed-detached-annihilation-roam',files=len(d['files']),objects=len(d['objects'])));return
    r=a.project;q=r/REL;m=helper(r);deps=m.dependencies(r)
    if a.action=='prepare':
        assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir();d=read(r/'preserved'/f'{PARENT}.json')
        for f in d['files']:
            rel=f['path'].split('/'+PARENT+'/',1)[1]
            if not(rel.startswith(('go-src/','inputs/','ui-assets/'))or rel in['probe.mod','probe.sum','xcheck','rear-actions-execution-r1.json']):continue
            t=q/rel;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(m.stored(r,PARENT,'/'+PARENT+'/'+rel));t.chmod(f['mode'])
        write(q/'baseline.json',deps);fonts(r,q)
        for suffix,name in [('/original-r2/receipt.json','original-defeat.json'),('/ida/ida-defeat-r2.json','ida-defeat.json')]:
            (q/'inputs'/name).write_bytes(m.stored(r,'owned-defeat-r1',suffix))
    else:assert deps==read(q/'baseline.json')
    if a.action in['prepare','freeze']:
        if a.action=='freeze':
            for n in PATCHED:(q/'go-src/tools'/n).write_bytes(m.stored(r,PARENT,'/'+PARENT+'/go-src/tools/'+n))
        patch(q/'go-src')
        for n in NEW:
            if(r/'tools'/n).is_file():shutil.copyfile(r/'tools'/n,q/'go-src/tools'/n)
        d=read(q/'rear-actions-execution-r1.json');ui=d['ui_build'].replace('/out/rear-actions-ui','/out/annihilation-roam-ui')+' tools/annihilation-roam.go';test=ui.replace('go build','go test').replace('-o /out/annihilation-roam-ui ','')+' tools/annihilation-roam_test.go -run ^TestAnnihilationRoam$ -count=1';e=dict(ui_build=ui,fixture_build=ui.replace('/out/annihilation-roam-ui','/out/annihilation-roam-fixture')+' tools/battle-resume-fixture.go tools/rear-actions-fixture.go',ui_test=test);(q/'annihilation-roam-execution-r1.json').write_text(json.dumps(e,indent=2)+'\n');return
    if a.action=='publish':
        from PIL import Image
        g=read(q/'gui-r1/receipt.json');assert g['status']=='passed-annihilation-roam-ui';items=[]
        for row in g['screens']:
            if row['name']not in['loss','returned']:continue
            source=q/'gui-r1'/row['phase']/row['canvas'];dest=a.images/('annihilation-roam-'+row['name']+'-r1.png');assert not dest.exists();im=Image.open(source);im.thumbnail((960,600),Image.Resampling.LANCZOS);im.save(dest);items.append(dict(source=str(source.relative_to(r)),source_sha256=sha(source),published=dest.name,published_sha256=sha(dest)))
        write(a.images/'annihilation-roam-runtime-r1.json',dict(images=items,controlled_initial_army_and_native_entry_and_enemy=True,normal_ui_clicks=True,production_promoted=False));return
    folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
    for f in sorted(q.rglob('*')):
        if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
        assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();h=hashlib.sha256(raw).hexdigest();obj=folder/(h+'.gz')
        if h not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
        files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(raw),mode=f.stat().st_mode&0o777))
    write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Original inputs, VM objects and full frames local-only; no formal promotion.'))
if __name__=='__main__':main()
