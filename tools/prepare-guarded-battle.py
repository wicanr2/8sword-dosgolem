#!/usr/bin/env python3
"""Prepare and preserve the ordinary fixed-guard Go battle candidate."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/guarded-battle-r1'
BATCH='guarded-battle-r1';PARENT='annihilation-origin-r1'
NEW=['prepare-guarded-battle.py','probe-guarded-save.go','guarded-layout.go','guarded-battle.go','guarded-store.go','guarded-battle_test.go','guarded-fixture.go','check-guarded-battle.py','check-guarded-battle-ui.py','guarded-battle.sh']
PATCHED=['research-battle-resume.go','research-controlled-battle.go','research-runtime-enemy.go','normal-encounter-ui.go']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
    with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def helper(r):
    sp=importlib.util.spec_from_file_location('h',r/'tools/prepare-owned-army-ui.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
def replace(p,a,b):
    s=p.read_text();assert s.count(a)==1,(p,a,s.count(a));p.write_text(s.replace(a,b))
def patch(src):
    p=src/'tools/research-controlled-battle.go'
    replace(p,'type controlledBattle struct {','type controlledBattle struct {\n Guard *guardedBinding')
    replace(p,'c := m.CPU\n\tds := uint32(0x1e880)','c := m.CPU\n if b.Guard!=nil&&guardedSignature(m.Mem)!=guardedCodeSHA{return errors.New("guard source signature")}\n\tds := uint32(0x1e880)')
    replace(p,'m.Read16(ds+uint32(sp)) != 0x171d || m.Read16(ds+uint32(sp)+2) != 0x110 || m.Read16(ds+uint32(bp)+2) != 0x0bd3 || m.Read16(ds+uint32(bp)+4) != 0x110','!guardEntryFrame(b,m)')
    replace(p,'c.IP = 0x171d','c.IP = guardReturnIP(b)')
    p=src/'tools/research-runtime-enemy.go'
    replace(p,'m.Read16(ds+uint32(bp)+2) != 0x171d || m.Read16(ds+uint32(bp)+4) != 0x110','!guardGeneratorFrame(x,m,bp)')
    replace(p,'m.Read16(ds+uint32(bp)-0xc) == 65 || m.Read16(ds+0x56d6) > 7','(x.Guard==nil && m.Read16(ds+uint32(bp)-0xc)==65)||(x.Guard!=nil&&m.Read16(ds+uint32(bp)-0xc)!=65) || m.Read16(ds+0x56d6) > 7')
    s=p.read_text();a=s.index('\tw := x.Current.World\n',s.index('func (x *runtimeEnemyBattle) importEnemy'));b=s.index('\tif e != nil {',s.index('w, e = w.begin',a));s=s[:a]+'\tw,e:=guardBeginWorld(x.Current.World,x.Store.Catalog,x.Store.Combat,x.Guard,rows)\n'+s[b:];p.write_text(s)
    p=src/'tools/research-battle-resume.go'
    replace(p,'if word(m.R[4]) != 0x171d || word(m.R[4]+2) != 0x110 || word(m.R[5]+2) != 0xbd3 || word(m.R[5]+4) != 0x110 || word(0x8d6a) > 1 || word(0x56d6) > 7 {','randomFrame:=word(m.R[4])==0x171d&&word(m.R[4]+2)==0x110&&word(m.R[5]+2)==0xbd3&&word(m.R[5]+4)==0x110\n if (!randomFrame&&!guardedFrame(s)) || word(0x8d6a)>1 ||word(0x56d6)>7 {')
    replace(p,'rows, e := decodeRuntimeEnemy(im.M.Mem[0x23f80:0x23f98], s.Catalog, s.Combat)','if guardedFrame(im){return guardValidateResume(s,p,im)}\n rows, e := decodeRuntimeEnemy(im.M.Mem[0x23f80:0x23f98], s.Catalog, s.Combat)')
    replace(p,'if native != nil {\n\t\tif prev.Resume == nil','if explicit!=nil&&explicit.Phase=="return"&&prev.World.Battle!=nil&&guardedKey(prev.World.Battle.Encounter)&&w.Battle==nil {if native!=nil{return progressPairBytes{},errors.New("guard return uses typed projection")};return buildGuardReturnPair(b,c,cc,w,files,r)}\n if native != nil {\n\t\tif prev.Resume == nil')
    replace(p,'ref,x:=savedResume(i.After.World);','if before.World.Battle!=nil&&guardedKey(before.World.Battle.Encounter)&&after.World.Battle==nil{return verifyGuardSettlement(s,i,before,after)}\n ref,x:=savedResume(i.After.World);')
    s=p.read_text();a=s.index('\t\tw := before.World\n',s.index('func checkResumeIntent'));b=s.index('\t\tif e != nil || worldDigest(w)',a);s=s[:a]+'''        _,im,x:=readResumeObject(s.Dir,after);if x!=nil{return x}
        w,e:=guardedBeginResume(s,before,after,im)
'''+s[b:];p.write_text(s)
    replace(p,'b.Current = p\n','b.Current = p\n var ge error;b.Guard,ge=guardSourceFromImage(im,s);if ge!=nil{return nil,ge}\n')
    p=src/'tools/normal-encounter-ui.go'
    replace(p,'e = x.Bridge.settle(DefeatInput{})','if x.Bridge.Guard!=nil{e=settleGuardRuntime(x.Bridge,x.Engine.Oracle,0)}else{e = x.Bridge.settle(DefeatInput{})}')
    replace(p,'var packed []byte;packed,e=originPackedInput();if e==nil{e=settleRuntimeOrigin(x.Bridge,x.Engine.Oracle,packed)}','if x.Bridge.Guard!=nil{e=settleGuardRuntime(x.Bridge,x.Engine.Oracle,3)}else{var packed []byte;packed,e=originPackedInput();if e==nil{e=settleRuntimeOrigin(x.Bridge,x.Engine.Oracle,packed)}}')
    replace(p,'e=settleRuntimeRoam(x.Bridge,x.Engine.Oracle)','if x.Bridge.Guard!=nil{e=settleGuardRuntime(x.Bridge,x.Engine.Oracle,2)}else{e=settleRuntimeRoam(x.Bridge,x.Engine.Oracle)}')
    replace(p,'e = settleRuntimeRetreat(x.Bridge, x.Engine.Oracle)','if x.Bridge.Guard!=nil{e=settleGuardRuntime(x.Bridge,x.Engine.Oracle,1)}else{e = settleRuntimeRetreat(x.Bridge, x.Engine.Oracle)}')
    replace(p,'v["battle_native_calls"], v["battle_events"] = x.Bridge.NativeCalls, x.Events','v["battle_native_calls"], v["battle_events"] = x.Bridge.NativeCalls, x.Events\n v["guarded_encounter"]=x.Bridge.Guard!=nil;if x.Bridge.Guard!=nil{v["guarded_binding"]=x.Bridge.Guard}')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','archive','verify','publish']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--images',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
    if a.action=='verify':
        d=read(a.archive/(BATCH+'.json'))
        for f in d['files']:
            o=d['objects'][f['sha256']];p=a.archive/BATCH/o['file'];assert sha(p)==o['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
        write(a.out,dict(status='passed-detached-guarded-battle',files=len(d['files']),objects=len(d['objects'])));return
    r=a.project;q=r/REL;m=helper(r);deps=m.dependencies(r)
    if a.action=='prepare':
        assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir();d=read(r/'preserved'/f'{PARENT}.json')
        for f in d['files']:
            rel=f['path'].split('/'+PARENT+'/',1)[1]
            if not(rel.startswith(('go-src/','inputs/','ui-assets/'))or rel in['probe.mod','probe.sum','xcheck','annihilation-origin-execution-r1.json']):continue
            t=q/rel;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(m.stored(r,PARENT,'/'+PARENT+'/'+rel));t.chmod(f['mode'])
        write(q/'baseline.json',deps)
        for suffix,name in[('/ida/ida-world-r3.json','ida-guard-world.json'),('/ida/ida-encounter-r1.json','ida-guard-rewards.json'),('/original-r2/receipt.json','original-guard-controls.json')]:
            (q/'inputs'/name).write_bytes(m.stored(r,'owned-encounter-r1',suffix))
        (q/'inputs/ida-save.json').write_bytes(m.stored(r,'native-checkpoint-r1','/ida/ida-checkpoint-r1.json'))
    else:assert deps==read(q/'baseline.json')
    if a.action in['prepare','freeze']:
        if a.action=='freeze':
            for n in PATCHED:(q/'go-src/tools'/n).write_bytes(m.stored(r,PARENT,'/'+PARENT+'/go-src/tools/'+n))
            patch(q/'go-src')
        for n in NEW:
            if(r/'tools'/n).is_file():shutil.copyfile(r/'tools'/n,q/'go-src/tools'/n)
        if a.action=='freeze':
            d=read(q/'annihilation-origin-execution-r1.json');ui=d['ui_build'].replace('/out/annihilation-origin-ui','/out/guarded-battle-ui')+' tools/guarded-layout.go tools/guarded-battle.go tools/guarded-store.go';test=ui.replace('go build','go test').replace('-o /out/guarded-battle-ui ','')+' tools/guarded-battle_test.go -run ^TestGuardedBattle$ -count=1';(q/'guarded-battle-execution-r1.json').write_text(json.dumps(dict(ui_build=ui,fixture_build=ui.replace('/out/guarded-battle-ui','/out/guarded-battle-fixture')+' tools/guarded-fixture.go',ui_test=test),indent=2)+'\n')
        return
    if a.action=='publish':
        from PIL import Image
        g=read(q/'gui-r2/receipt.json');assert g['status']=='passed-guarded-battle-ui';items=[]
        for row in g['screens']:
            if row['name']not in['guard-opened','guard-rematch','mixed-army']:continue
            source=q/'gui-r2'/row['phase']/row['canvas'];dest=a.images/('guarded-battle-'+row['name']+'-r1.png');assert not dest.exists();im=Image.open(source);im.thumbnail((960,600),Image.Resampling.LANCZOS);im.save(dest);items.append(dict(source=str(source.relative_to(r)),source_sha256=sha(source),published=dest.name,published_sha256=sha(dest)))
        write(a.images/'guarded-battle-runtime-r1.json',dict(images=items,controlled_initial_army_and_position=True,native_guard_unmodified=True,normal_ui_clicks=True,production_promoted=False));return
    folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
    for f in sorted(q.rglob('*')):
        if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
        assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();h=hashlib.sha256(raw).hexdigest();obj=folder/(h+'.gz')
        if h not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
        files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(raw),mode=f.stat().st_mode&0o777))
    write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Original inputs, VM objects and full frames local-only; no formal promotion.'))
if __name__=='__main__':main()
