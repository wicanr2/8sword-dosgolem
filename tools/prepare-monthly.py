#!/usr/bin/env python3
"""Frozen openKB-HD candidate plus narrow monthly source/control experiments."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/monthly-r1'
BATCH='monthly-r1'
NEW=['export-monthly-ida.py','research-monthly.go','probe-monthly-original.go','probe-monthly-candidate.go','monthly-native-save.go','monthly-store.go','monthly-port.go','monthly-ui.go','monthly-fixture.go','prepare-monthly.py','check-monthly.py','check-monthly-ui.py','monthly.sh']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
    with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def helper(r):
    sp=importlib.util.spec_from_file_location('h',r/'tools/prepare-owned-army-ui.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
def replace(p,a,b):
    s=p.read_text();assert s.count(a)==1,(p,a,s.count(a));p.write_text(s.replace(a,b))
def patch(src):
    p=src/'tools/research-paired-progress.go'
    replace(p,'After      progressPairBytes `json:"after"`','After      progressPairBytes `json:"after"`\n Monthly bool `json:"monthly,omitempty"`')
    replace(p,'i.Schema != campIntent)', 'i.Schema != campIntent && i.Schema != monthlyIntent)')
    replace(p,'if i.Schema==campIntent ||', 'if i.Schema==monthlyIntent {return checkMonthlyIntent(s,i)}\n if i.Monthly{return errors.New("monthly flag on legacy intent")}\n if i.Schema==campIntent ||')
    replace(p,'s.Combat.Digest(), b, after}', 's.Combat.Digest(), b, after, false}')
    p=src/'tools/world-army-review_main.go'
    replace(p,'return advanceEncounterUI(g)', 'return advanceMonthlyUI(g)')
    replace(p,'return state','state["monthly"]=monthlyStatus()\n return state')
    replace(p,'store, snap, e := openProgressPair(*session, c, cc)','if err:=setMonthlySavePAM(filepath.Join(*input,"PAM.AY"));err!=nil{return err}\n store, snap, e := openProgressPair(*session, c, cc)')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','publish','archive','verify']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--images',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
    if a.action=='verify':
        d=read(a.archive/(BATCH+'.json'))
        for f in d['files']:
            v=d['objects'][f['sha256']];obj=a.archive/BATCH/v['file'];assert sha(obj)==v['stored_sha256'];raw=gzip.decompress(obj.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
        write(a.out,dict(status='passed-detached-monthly',files=len(d['files']),objects=len(d['objects'])));return
    r=a.project;q=r/REL;m=helper(r);deps=m.dependencies(r)
    if a.action=='publish':
        from PIL import Image
        g=read(q/'gui-r1/receipt.json');assert g['status']=='passed-monthly-ui-cold';source=q/'gui-r1/warm'/g['screens'][0]['canvas'];dest=a.images/'monthly-go-report-r1.png';assert not dest.exists();im=Image.open(source);im.thumbnail((960,600),Image.Resampling.LANCZOS);im.save(dest)
        write(a.images/'monthly-go-report-r1.json',dict(source=str(source.relative_to(r)),source_sha256=sha(source),published_sha256=sha(dest),size=im.size,controlled_countdown=True,controlled_initial_army=True,monthly=g['report']['monthly'],original_shadow_unchanged=True,production_promoted=False));return
    if a.action=='prepare':
        assert q.is_dir()and q.stat().st_uid==1000 and not(q/'go-src').exists();d=read(r/'preserved/openkb-hd-r1.json')
        for f in d['files']:
            rel=f['path'].split('/openkb-hd-r1/',1)[1]
            if not(rel.startswith(('go-src/','inputs/','ui-assets/'))or rel in ['probe.mod','probe.sum','xcheck','openkb-execution-r1.json']):continue
            t=q/rel;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(m.stored(r,'openkb-hd-r1','/openkb-hd-r1/'+rel));t.chmod(f['mode'])
        e=read(q/'openkb-execution-r1.json');probe=e['probe_build'].replace('/out/openkb-probe','/out/monthly-original').replace('tools/openkb-hd-probe.go','tools/probe-monthly-original.go')+' tools/research-monthly.go tools/monthly-native-save.go';write(q/'monthly-execution-r1.json',dict(original_build=probe,previous_ui=e['ui_build']));write(q/'baseline.json',deps)
    else:assert deps==read(q/'baseline.json')
    if a.action in ['prepare','freeze']:
        if a.action=='freeze':
            for n in ['research-paired-progress.go','world-army-review_main.go']:(q/'go-src/tools'/n).write_bytes(m.stored(r,'openkb-hd-r1','/openkb-hd-r1/go-src/tools/'+n))
            patch(q/'go-src')
            e=read(q/'monthly-execution-r1.json');extra=' tools/research-monthly.go tools/monthly-native-save.go tools/monthly-store.go tools/monthly-port.go tools/monthly-ui.go';ui=e['previous_ui'].replace('/out/openkb-ui','/out/monthly-ui')+extra;e['ui_build']=ui;e['fixture_build']=ui.replace('/out/monthly-ui','/out/monthly-ui-fixture')+' tools/monthly-fixture.go'
            if 'tools/monthly-store.go'not in e['original_build']:e['original_build']+=' tools/monthly-store.go'
            e['candidate_build']=e['original_build'].replace('/out/monthly-original','/out/monthly-candidate').replace('tools/probe-monthly-original.go','tools/probe-monthly-candidate.go')+' tools/monthly-port.go'
            (q/'monthly-execution-r1.json').write_text(json.dumps(e,ensure_ascii=False,indent=2)+'\n')
        for n in NEW:
            if(r/'tools'/n).is_file():shutil.copyfile(r/'tools'/n,q/'go-src/tools'/n)
        return
    folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
    for f in sorted(q.rglob('*')):
        if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
        assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();h=hashlib.sha256(raw).hexdigest();obj=folder/(h+'.gz')
        if h not in objects:obj.write_bytes(gzip.compress(raw,compresslevel=6,mtime=0));objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
        files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(raw),mode=f.stat().st_mode&0o777))
    write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Complete original inputs, VM objects and full frames are local-only. Formal engine unchanged.'))
if __name__=='__main__':main()
