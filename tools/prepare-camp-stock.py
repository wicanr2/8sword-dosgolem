#!/usr/bin/env python3
"""Restore the frozen recruit candidate and isolate the camp-stock revision."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/camp-stock-r1'
BATCH='camp-stock-r1'
NEW=['research-camp-stock.go','research-camp-stock-save.go','camp-stock-port.go','probe-camp-stock.go','prepare-camp-stock.py','check-camp-stock.py','check-camp-stock-ui.py','camp-stock.sh']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
    with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def helper(r):
    sp=importlib.util.spec_from_file_location('previous',r/'tools/prepare-owned-army-ui.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
def replace(p,a,b):
    s=p.read_text();assert s.count(a)==1,(p,a,s.count(a));p.write_text(s.replace(a,b))
def patch(src):
    p=src/'tools/research-native-checkpoint.go'
    replace(p,'if s.Schema==resumeSchema{return validResumeEnvelope(s)}','if s.Schema==campSchema {return validCampEnvelope(s)}\n if s.Schema==resumeSchema{return validResumeEnvelope(s)}')
    replace(p,'if s.Schema==resumeSchema{return resumeIntent}', 'if s.Schema==campSchema{return campIntent}\n if s.Schema==resumeSchema{return resumeIntent}')
    p=src/'tools/research-paired-progress.go'
    replace(p,'i.Schema != resumeIntent)', 'i.Schema != resumeIntent && i.Schema != campIntent)')
    replace(p,'if i.Schema==resumeIntent || checkpointIntentSchema(i.Before)==resumeIntent || checkpointIntentSchema(i.After)==resumeIntent {','if i.Schema==campIntent || checkpointIntentSchema(i.Before)==campIntent || checkpointIntentSchema(i.After)==campIntent {return checkCampIntent(s,i)}\n if i.Schema==resumeIntent || checkpointIntentSchema(i.Before)==resumeIntent || checkpointIntentSchema(i.After)==resumeIntent {')
    replace(p,'after, e := buildResumeUpdate(b, s.Catalog, s.Combat, w, native, files, resume)', 'after, e := buildCampUpdate(b, s.Catalog, s.Combat, w, native, files, resume)')
    replace(p,'if e==nil { e=validateResumeObject(s,snap) }','if e==nil {e=validateCampBindings(snap.Bytes.Native,snap.World.Army)}\n if e==nil {e=validateResumeObject(s,snap)}')
    p=src/'tools/research-battle-resume.go'
    replace(p,'b.Current = p','if e=overlayCampStocks(o,p);e!=nil{return nil,e}\n b.Current = p')
    patch_port(src/'tools/research-world-army-port.go')
def patch_port(p):
    replace(p,'ShopStock     uint16','ShopID, ShopUnit string\n ShopKind,ShopSP,ShopBP uint16\n ShopGroup,ShopRow int\n ShopCommitted bool\n ShopStock     uint16')
    replace(p,'{0x59c4, 0x5a54}', '{0x59c4, 0x5c94}')
    s=p.read_text();start=s.index('\te.Oracle.OnCall(oracle.Far(0x110, 0x54ea),');end=s.index('\n\t// These sentinels',start)
    s=s[:start]+'''\te.Oracle.OnCall(oracle.Far(0x110,0x54ea),func(o *oracle.Oracle){if err:=p.bindCamp(o);err!=nil{fail(err.Error())}})
 for group:=0;group<5;group++ {group:=group;e.Oracle.OnCall(oracle.Far(0x110,uint16(0x5a3b+group*0x90)),func(o *oracle.Oracle){if err:=p.finishCamp(o,group);err!=nil{fail(err.Error())}})}
'''+s[end:];p.write_text(s)
    replace(p,'m.Read16(ds+uint32(bp)+6) != 1','m.Read16(ds+uint32(bp)+6) != p.ShopKind')
    replace(p,'m.Read16(ds+uint32(sp)+2) != 1','m.Read16(ds+uint32(sp)+2) != p.ShopKind')
    replace(p,'if route == "commit" {','if route == "commit" {\n if p.ShopCommitted{return fault("purchase already committed")}')
    replace(p,'"verified-militia-shop-r1", uint32(count)', 'p.ShopID, uint32(count)')
    replace(p,'v.World.Army, "native:01"','v.World.Army, p.ShopUnit')
    replace(p,'idx["native:01"].Command','idx[p.ShopUnit].Command')
    replace(p,'p.Purchases++','p.Purchases++\n p.ShopCommitted=true')
    replace(p,'worldArmyPortRecord{ip, route, 1, value','worldArmyPortRecord{ip, route, p.ShopKind, value')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','archive','verify']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
    if a.action=='verify':
        d=read(a.archive/(BATCH+'.json'))
        for f in d['files']:
            o=d['objects'][f['sha256']];obj=a.archive/BATCH/o['file'];assert sha(obj)==o['stored_sha256'];b=gzip.decompress(obj.read_bytes());assert len(b)==f['bytes']and hashlib.sha256(b).hexdigest()==f['sha256']
        write(a.out,dict(status='passed-detached-camp-stock',files=len(d['files']),objects=len(d['objects'])));return
    r=a.project;q=r/REL;m=helper(r);deps=m.dependencies(r)
    if a.action=='prepare':
        assert q.is_dir()and q.stat().st_uid==1000 and not(q/'go-src').exists();d=read(r/'preserved/recruit-icons-r1.json')
        for f in d['files']:
            rel=f['path'].split('/recruit-icons-r1/',1)[1]
            if not(rel.startswith(('go-src/','inputs/','ui-assets/'))or rel in ['probe.mod','probe.sum','xcheck','pair-init','execution-r1.json']):continue
            t=q/rel;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(m.stored(r,'recruit-icons-r1','/recruit-icons-r1/'+rel));t.chmod(f['mode'])
        for n in ['before-commit.state','original-save.ay']:
            t=q/'inputs'/n;t.write_bytes(m.stored(r,'recruit-icons-r1','/recruit-icons-r1/control-r3/'+n))
        (q/'inputs/ida-checkpoint-r1.json').write_bytes(m.stored(r,'native-checkpoint-r1','/ida/ida-checkpoint-r1.json'))
        e=read(q/'execution-r1.json');extra=' tools/research-camp-stock.go tools/research-camp-stock-save.go tools/camp-stock-port.go';e['ui_build']=e['ui_build'].replace('/out/recruit-ui','/out/camp-ui')+extra
        # Use all established UI helpers but substitute a narrow probe main.
        e['probe_build']=e['probe_build'].replace('/out/recruit-probe','/out/camp-probe').replace('tools/probe-world-army.go','tools/probe-camp-stock.go')+extra
        write(q/'camp-execution-r1.json',e);write(q/'baseline.json',deps);patch(q/'go-src')
    else:assert deps==read(q/'baseline.json')
    if a.action in ['prepare','freeze']:
        for n,original in [('resume-native.ay','inputs/original-save.ay'),('held.state','probe-r3/held.state'),('old-resume-receipt.json','probe-r3/receipt.json')]:
            t=q/'inputs'/n
            if not t.exists():t.write_bytes(m.stored(r,'battle-resume-r1','/battle-resume-r1/'+original))
        if a.action=='freeze':
            # Reapply only this revision, from the immutable previous batch.
            for n in ['research-world-army-port.go']:
                (q/'go-src/tools'/n).write_bytes(m.stored(r,'recruit-icons-r1','/recruit-icons-r1/go-src/tools/'+n))
            patch_port(q/'go-src/tools/research-world-army-port.go')
            e=read(q/'camp-execution-r1.json')
            for k in ['ui_build','probe_build']:
                if 'tools/camp-stock-port.go'not in e[k]:e[k]+=' tools/camp-stock-port.go'
            (q/'camp-execution-r1.json').write_text(json.dumps(e,ensure_ascii=False,indent=2)+'\n')
        for n in NEW:
            if(r/'tools'/n).is_file():shutil.copyfile(r/'tools'/n,q/'go-src/tools'/n)
        return
    folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
    for f in sorted(q.rglob('*')):
        if not f.is_file()or 'build-cache'in f.relative_to(q).parts:continue
        assert f.stat().st_uid==1000 and not f.is_symlink();b=f.read_bytes();h=hashlib.sha256(b).hexdigest();obj=folder/(h+'.gz')
        if h not in objects:obj.write_bytes(gzip.compress(b,compresslevel=6,mtime=0));objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
        files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(b),mode=f.stat().st_mode&0o777))
    write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Original inputs and complete local objects excluded from Git. No formal save-format promotion.'))
if __name__=='__main__':main()
