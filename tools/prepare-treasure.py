#!/usr/bin/env python3
"""Restore the last candidate and freeze the narrow chest-resource experiment."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/story-resources-r1'
BATCH='treasure-r1'
NEW=['prepare-treasure.py','export-story-resources-ida.py','treasure-data.go','treasure-native-save.go','probe-treasure.go','probe-treasure-faults.go','treasure-port.go','treasure-store.go','treasure-ui.go','treasure-fixture.go','check-treasure.py','check-treasure-ui.py','treasure.sh']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
    with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def helper(r):
    sp=importlib.util.spec_from_file_location('h',r/'tools/prepare-owned-army-ui.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
def patch(src):
    p=src/'tools/research-paired-progress.go';s=p.read_text()
    def repl(a,b):
        nonlocal s
        assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
    repl('Monthly bool `json:"monthly,omitempty"`','Monthly bool `json:"monthly,omitempty"`\n Treasure *treasureAward `json:"treasure,omitempty"`');repl('i.Schema != monthlyIntent)','i.Schema != monthlyIntent && i.Schema != treasureIntent)');repl('if i.Schema==monthlyIntent','if i.Schema==treasureIntent{return checkTreasureIntent(s,i)}\n if i.Treasure!=nil{return errors.New("treasure on legacy intent")}\n if i.Schema==monthlyIntent');repl('s.Combat.Digest(), b, after, false}','s.Combat.Digest(), b, after, false, nil}');p.write_text(s)
    p=src/'tools/world-army-review_main.go';s=p.read_text();assert s.count('return advanceMonthlyUI(g)')==1;s=s.replace('return advanceMonthlyUI(g)','return advanceTreasureUI(g)');s=s.replace('if wideMonthlyVisible()','if treasureCurrent!=nil && treasureCurrent.Active{return "treasure"}; if wideMonthlyVisible()');assert s.count('return state')==1;s=s.replace('return state','state["treasure"]=treasureStatus()\n return state');p.write_text(s)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','archive','verify','publish']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--images',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
    if a.action=='verify':
        d=read(a.archive/(BATCH+'.json'))
        for f in d['files']:
            obj=d['objects'][f['sha256']];p=a.archive/BATCH/obj['file'];assert sha(p)==obj['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
        write(a.out,dict(status='passed-detached-treasure',files=len(d['files']),objects=len(d['objects'])));return
    r=a.project;q=r/REL;m=helper(r);deps=m.dependencies(r)
    if a.action=='prepare':
        assert q.is_dir()and q.stat().st_uid==1000 and not(q/'go-src').exists();d=read(r/'preserved/monthly-wide-r1.json')
        for f in d['files']:
            rel=f['path'].split('/monthly-wide-r1/',1)[1]
            if not(rel.startswith(('go-src/','inputs/','ui-assets/'))or rel in['probe.mod','probe.sum','xcheck','monthly-wide-execution-r1.json']):continue
            t=q/rel;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(m.stored(r,'monthly-wide-r1','/monthly-wide-r1/'+rel));t.chmod(f['mode'])
        write(q/'baseline.json',deps)
    else:assert deps==read(q/'baseline.json')
    if a.action in['prepare','freeze']:
        if a.action=='freeze':
            for n in['research-paired-progress.go','world-army-review_main.go']:(q/'go-src/tools'/n).write_bytes(m.stored(r,'monthly-wide-r1','/monthly-wide-r1/go-src/tools/'+n))
            patch(q/'go-src')
        for n in NEW:
            if(r/'tools'/n).is_file():shutil.copyfile(r/'tools'/n,q/'go-src/tools'/n)
        d=read(q/'monthly-wide-execution-r1.json');extra=' tools/treasure-data.go tools/treasure-native-save.go';e=dict(original_build=d['candidate_build'].replace('/out/monthly-wide-candidate','/out/treasure-original').replace('tools/probe-monthly-candidate.go','tools/probe-treasure.go')+extra)
        if a.action=='freeze':
            extra+=' tools/treasure-store.go tools/treasure-port.go';e['candidate_build']=e['original_build'].replace('/out/treasure-original','/out/treasure-candidate')+' tools/treasure-store.go tools/treasure-port.go';e['original_build']=e['candidate_build'].replace('/out/treasure-candidate','/out/treasure-original');e['ui_build']=d['ui_build'].replace('/out/monthly-wide-ui','/out/treasure-ui')+extra+' tools/treasure-ui.go';e['fixture_build']=e['ui_build'].replace('/out/treasure-ui','/out/treasure-ui-fixture')+' tools/treasure-fixture.go'
        if 'candidate_build'in e:e['fault_build']=e['candidate_build'].replace('/out/treasure-candidate','/out/treasure-faults').replace('tools/probe-treasure.go','tools/probe-treasure-faults.go')
        (q/'treasure-execution-r1.json').write_text(json.dumps(e,indent=2)+'\n');return
    if a.action=='publish':
        from PIL import Image
        gui=read(q/'gui-r1/receipt.json');assert gui['status']=='passed-treasure-ui-cold';rows=[]
        for frame in gui['screens'][:2]:
            source=q/'gui-r1'/frame['phase']/frame['canvas'];name='treasure-'+frame['name']+'-r1.png';t=a.images/name;assert not t.exists();im=Image.open(source);im.thumbnail((960,600),Image.Resampling.LANCZOS);im.save(t);rows.append(dict(source=str(source.relative_to(r)),source_sha256=sha(source),file=name,sha256=sha(t)))
        write(a.images/'treasure-runtime-r1.json',dict(rows=rows,controlled_initial_position=True,controlled_initial_army=True,ordinary_movement_and_choice=True,production_promoted=False));return
    folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
    for f in sorted(q.rglob('*')):
        if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
        assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();h=hashlib.sha256(raw).hexdigest();obj=folder/(h+'.gz')
        if h not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
        files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(raw),mode=f.stat().st_mode&0o777))
    write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Original inputs, VM objects and full frames local-only; no production promotion.'))
if __name__=='__main__':main()
