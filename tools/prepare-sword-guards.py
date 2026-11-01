#!/usr/bin/env python3
"""Isolated sword and final-guard continuation of guarded-battle-r1."""
import argparse,gzip,hashlib,importlib.util,json,os,re,shutil
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/sword-guards-r1';BATCH='sword-guards-r1';PARENT='guarded-battle-r1'
NEW=['prepare-sword-guards.py','probe-sword-guards.go','sword-guards.go','sword-lifecycle.go','sword-guards_test.go','sword-guards-fixture.go','check-sword-guards-ui.py','check-sword-guards.py','sword-guards.sh']
HOOKS=['research-world-army-port.go','research-controlled-battle.go','research-runtime-enemy.go','research-world-army-review.go','world-army-review_main.go','research-world-army-dismiss.go','research-army-presence.go','normal-encounter-ui.go','refusal-rng-ui.go','native-checkpoint-port.go','recruit-icons-ui.go','recruit-native-main.go','monthly-native-save.go','monthly-port.go','treasure-native-save.go','treasure-port.go','alchemy-native-save.go','alchemy-port.go','summon-native-save.go','summon-port.go','guarded-battle.go']
PATCHED=list(dict.fromkeys(['guarded-battle.go','guarded-store.go','research-owned-encounter.go','normal-encounter-ui.go']+HOOKS))
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def helper(r):
    sp=importlib.util.spec_from_file_location('h',r/'tools/prepare-owned-army-ui.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
def replace(p,a,b):
    s=p.read_text();assert s.count(a)==1,(p,a,s.count(a));p.write_text(s.replace(a,b))
def patch(src):
    p=src/'tools/guarded-battle.go'
    replace(p,'if ctx.Boss || region == 0 && index == 4 || !ctx.EndingGuardAlive {','if e:=swordSource(mem,ctx);e!=nil{return nil,e}\n if !ctx.EndingGuardAlive {')
    replace(p,'start := guardNPCAt(int(g.Context.Region), int(g.Context.Index))','if e:=swordNativeBinding(mem,native,g,skipTarget);e!=nil{return e}\n start := guardNPCAt(int(g.Context.Region), int(g.Context.Index))')
    replace(p,'m.CPU.IP = 0x32ad','if e:=swordApply(m,b);e!=nil{return false,e}\n m.CPU.IP=0x32ad;if swordEnding(b){m.CPU.IP=0x329b}')
    p=src/'tools/guarded-store.go'
    replace(p,'base.Native = native','native,e=projectSwords(native,region,index,r.Result);if e!=nil{return base,e}\n base.Native = native')
    p=src/'tools/research-owned-encounter.go'
    replace(p,' || (ctx.Region == 0 && ctx.Index == 4)','')
    p=src/'tools/normal-encounter-ui.go'
    replace(p,'v["controlled_memory"], v["normal_player_path"] = false, true','swordState(v,x)\n v["controlled_memory"], v["normal_player_path"] = false, true')
    p=src/'tools/world-army-review_main.go'
    replace(p,'if g.Frame == nil || g.Frame.Bounds()', 'g.Frame,g.Texts=swordDecorate(g,g.Frame,g.Texts)\n if g.Frame == nil || g.Frame.Bounds()')
    for n in HOOKS:
        p=src/'tools'/n;s=p.read_text()
        for method,new in [('OnCall','swordOnCall'),('OnHostInstruction','swordOnHostInstruction')]:s=re.sub(r'(\b[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\.'+method+r'\(',lambda m:new+'('+m[1]+', ',s)
        p.write_text(s)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','archive','verify','publish']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--out',type=Path);p.add_argument('--images',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
    if a.action=='verify':
        d=read(a.archive/(BATCH+'.json'))
        for f in d['files']:
            o=d['objects'][f['sha256']];p=a.archive/BATCH/o['file'];assert sha(p)==o['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
        write(a.out,dict(status='passed-detached-sword-guards',files=len(d['files']),objects=len(d['objects'])));return
    r=a.project;q=r/REL;m=helper(r);deps=m.dependencies(r)
    if a.action=='prepare':
        assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir();d=read(r/'preserved'/f'{PARENT}.json')
        for f in d['files']:
            rel=f['path'].split('/'+PARENT+'/',1)[1]
            if not(rel.startswith(('go-src/','inputs/','ui-assets/'))or rel in['probe.mod','probe.sum','xcheck','guarded-battle-execution-r1.json']):continue
            t=q/rel;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(m.stored(r,PARENT,'/'+PARENT+'/'+rel));t.chmod(f['mode'])
        write(q/'baseline.json',deps)
        cat=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()))
        for f in cat['files']:
            if not f['path'].endswith('/ida-handoff-r1.json'):continue
            obj=cat['objects'][f['sha256']];raw=gzip.decompress((r/'preserved'/obj['path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==f['sha256'];(q/'inputs/ida-ending-handoff.json').write_bytes(raw);break
        else:raise RuntimeError('missing preserved ending evidence')
    else:assert deps==read(q/'baseline.json')
    if a.action in['prepare','freeze']:
        if a.action=='freeze':
            for n in PATCHED:(q/'go-src/tools'/n).write_bytes(m.stored(r,PARENT,'/'+PARENT+'/go-src/tools/'+n))
            patch(q/'go-src')
        for n in NEW:
            if(r/'tools'/n).is_file():shutil.copyfile(r/'tools'/n,q/'go-src/tools'/n)
        if a.action=='freeze':
            old=read(q/'guarded-battle-execution-r1.json');ui=old['ui_build'].replace('/out/guarded-battle-ui','/out/sword-guards-ui')+' tools/sword-guards.go tools/sword-lifecycle.go';test=ui.replace('go build','go test').replace('-o /out/sword-guards-ui ','')+' tools/sword-guards_test.go -run ^TestSwordGuards$ -count=1';(q/'sword-guards-execution-r1.json').write_text(json.dumps(dict(ui_build=ui,fixture_build=ui.replace('/out/sword-guards-ui','/out/sword-guards-fixture')+' tools/sword-guards-fixture.go',ui_test=test),indent=2)+'\n')
        return
    if a.action=='publish':
        from PIL import Image
        g=read(q/'gui-r3/receipt.json');assert g['status']=='passed-sword-guards-ui';items=[]
        for row in g['screens']:
            if row['name']not in['boss-sword-hud','final-opened','hd-ending']:continue
            source=q/row.get('batch','gui-r3')/row['phase']/row['canvas'];dest=a.images/('sword-guards-'+row['name']+'-r1.png');assert not dest.exists();im=Image.open(source);im.thumbnail((960,600),Image.Resampling.LANCZOS);im.save(dest);items.append(dict(source=str(source.relative_to(r)),source_sha256=sha(source),published=dest.name,published_sha256=sha(dest)))
        write(a.images/'sword-guards-runtime-r1.json',dict(images=items,controlled_initial_army_and_position=True,controlled_final_eight_swords=True,native_enemies_unmodified=True,production_promoted=False));return
    folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
    for f in sorted(q.rglob('*')):
        if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
        assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();h=hashlib.sha256(raw).hexdigest();obj=folder/(h+'.gz')
        if h not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
        files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(raw),mode=f.stat().st_mode&0o777))
    write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Original data, VM and complete frames local-only; no formal promotion.'))
if __name__=='__main__':main()
