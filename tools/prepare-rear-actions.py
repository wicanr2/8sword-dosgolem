#!/usr/bin/env python3
"""Wire the already verified rear actions into the isolated battle UI."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/rear-actions-r1'
BATCH='rear-actions-r1'
NEW=['prepare-rear-actions.py','rear-actions.go','rear-actions_test.go','rear-actions-fixture.go','check-rear-actions.py','check-rear-actions-ui.py','rear-actions.sh']
PATCHED=['owned-battle-ui.go','owned-battle-ui_draw.go','normal-encounter-ui.go']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
    with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def helper(r):
    sp=importlib.util.spec_from_file_location('h',r/'tools/prepare-owned-army-ui.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
def replace(p,a,b):
    s=p.read_text();assert s.count(a)==1,(p,a,s.count(a));p.write_text(s.replace(a,b))
def patch(src):
    p=src/'tools/owned-battle-ui.go';s=p.read_text();a=s.index('func (u *battleUI) enemyPlan()');b=s.index('func (u *battleUI) apply(',a);s=s[:a]+'''func (u *battleUI) enemyPlan() (game.OwnedCombatOutcome,error) {return rearEnemyPlan(u)}
'''+s[b:];s=s.replace('case "enemy":\n\t\tp, e := u.enemyPlan()\n\t\tif e != nil {\n\t\t\treturn e\n\t\t}\n\t\treturn u.apply(p)','case "enemy":\n return rearEnemyAction(u)');assert 'return rearEnemyAction(u)'in s;s=s.replace('case "attack":\n','case "rear:0", "rear:2", "rear:5":\n return rearPlayerAction(u,name)\n case "attack":\n',1);p.write_text(s)
    p=src/'tools/owned-battle-ui_draw.go';replace(p,'for _, b := range battleButtons {\n\t\tif pt.In(b.Rect)', 'for _,b:=range rearButtons {if pt.In(b.Rect){return b.ID}}\n for _, b := range battleButtons {\n\t\tif pt.In(b.Rect)');replace(p,'enabled = e == nil\n\t\tcase "settle":','enabled = e == nil || rearEnemyPassAvailable(u)\n\t\tcase "settle":');replace(p,'// Filesystem errors can contain','paintRearButtons(u,&p)\n // Filesystem errors can contain')
    replace(src/'tools/normal-encounter-ui.go','case "attack", "enemy", "round", "pass":','case "attack", "enemy", "round", "pass", "rear:0", "rear:2", "rear:5":')
def fonts(r,q):
    # Reuse the fixed renderer, retaining every old atlas cell and all notices.
    path=r/'tools/prepare-monthly-wide.py';source=path.read_text();a=source.index('def fonts(r,q):');b=source.index('def main():',a);fn=source[a:b];start=fn.index("text='");end=fn.index("';extra=",start);fn=fn[:start]+"text='定額打擊剋制比例敵方後排略過。已儲存。'"+fn[end+1:]
    ns=dict(globals());exec('import gzip,hashlib,io,json\nfrom PIL import Image,ImageDraw,ImageFont,__version__\n'+fn,ns);ns['fonts'](r,q)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','archive','verify','publish']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--images',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
    if a.action=='verify':
        d=read(a.archive/(BATCH+'.json'))
        for f in d['files']:
            o=d['objects'][f['sha256']];p=a.archive/BATCH/o['file'];assert sha(p)==o['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
        write(a.out,dict(status='passed-detached-rear-actions',files=len(d['files']),objects=len(d['objects'])));return
    r=a.project;q=r/REL;m=helper(r);deps=m.dependencies(r)
    if a.action=='prepare':
        assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir();d=read(r/'preserved/summon-r1.json')
        for f in d['files']:
            rel=f['path'].split('/summon-r1/',1)[1]
            if not(rel.startswith(('go-src/','inputs/','ui-assets/'))or rel in['probe.mod','probe.sum','xcheck','summon-execution-r1.json']):continue
            t=q/rel;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(m.stored(r,'summon-r1','/summon-r1/'+rel));t.chmod(f['mode'])
        shutil.copyfile(r/'preserved/owned-combat-audit-r1.json',q/'inputs/owned-combat-audit.json');write(q/'baseline.json',deps);fonts(r,q)
    else:assert deps==read(q/'baseline.json')
    if a.action in['prepare','freeze']:
        if a.action=='freeze':
            for n in PATCHED:(q/'go-src/tools'/n).write_bytes(m.stored(r,'summon-r1','/summon-r1/go-src/tools/'+n))
        patch(q/'go-src')
        for n in NEW:
            if(r/'tools'/n).is_file():shutil.copyfile(r/'tools'/n,q/'go-src/tools'/n)
        d=read(q/'summon-execution-r1.json');ui=d['ui_build'].replace('/out/summon-ui','/out/rear-actions-ui')+' tools/rear-actions.go';test=ui.replace('go build','go test').replace('-o /out/rear-actions-ui ','')+' tools/rear-actions_test.go -run ^TestRearActions$ -count=1';e=dict(ui_build=ui,fixture_build=ui.replace('/out/rear-actions-ui','/out/rear-actions-fixture')+' tools/battle-resume-fixture.go tools/rear-actions-fixture.go',ui_test=test);(q/'rear-actions-execution-r1.json').write_text(json.dumps(e,indent=2)+'\n');return
    if a.action=='publish':
        from PIL import Image
        g=read(q/'gui-r1/receipt.json');assert g['status']=='passed-rear-actions-ui-cold';items=[]
        for i,label in [(0,'player'),(2,'enemy')]:
            row=g['screens'][i];source=q/'gui-r1'/row['phase']/row['canvas'];dest=a.images/('rear-actions-'+label+'-r1.png');assert not dest.exists();im=Image.open(source);im.thumbnail((960,600),Image.Resampling.LANCZOS);im.save(dest);items.append(dict(source=str(source.relative_to(r)),source_sha256=sha(source),published=dest.name,published_sha256=sha(dest)))
        write(a.images/'rear-actions-runtime-r1.json',dict(images=items,controlled_native_entry_and_enemy=True,normal_ui_clicks=True,production_promoted=False));return
    folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
    for f in sorted(q.rglob('*')):
        if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
        assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();h=hashlib.sha256(raw).hexdigest();obj=folder/(h+'.gz')
        if h not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
        files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(raw),mode=f.stat().st_mode&0o777))
    write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Original inputs, VM objects and full frames local-only; no formal promotion.'))
if __name__=='__main__':main()
