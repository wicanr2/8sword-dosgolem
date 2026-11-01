#!/usr/bin/env python3
"""Narrow summon slice, reusing the preserved alchemy candidate."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/summon-r1'
BATCH='summon-r1'
NEW=['prepare-summon.py','summon-data.go','summon-native-save.go','probe-summon.go','summon-probe-bind.go','summon-port.go','summon-store.go','summon-ui.go','check-summon.py','check-summon-ui.py','summon.sh']
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
    repl('Alchemy *alchemyAward `json:"alchemy,omitempty"`','Alchemy *alchemyAward `json:"alchemy,omitempty"`\n Summon *summonAward `json:"summon,omitempty"`');repl('i.Schema != alchemyIntent)','i.Schema != alchemyIntent && i.Schema != summonIntent)');repl('if i.Schema==alchemyIntent','if i.Schema==summonIntent{return checkSummonIntent(s,i)}\n if i.Summon!=nil{return errors.New("summon on legacy intent")}\n if i.Schema==alchemyIntent');repl('s.Combat.Digest(), b, after, false, nil, nil}','s.Combat.Digest(), b, after, false, nil, nil, nil}');p.write_text(s)
    p=src/'tools/world-army-review_main.go';s=p.read_text();assert s.count('return advanceAlchemyUI(g)')==1;s=s.replace('return advanceAlchemyUI(g)','return advanceSummonUI(g)');s=s.replace('func (g *armyReviewApp) view() string {','func (g *armyReviewApp) view() string {\n if summonCurrent!=nil && summonCurrent.Active{return "summon"}');assert s.count('return state')==1;s=s.replace('return state','state["summon"]=summonStatus()\n return state');p.write_text(s)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','archive','verify','publish']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--images',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
    if a.action=='verify':
        d=read(a.archive/(BATCH+'.json'))
        for f in d['files']:
            obj=d['objects'][f['sha256']];p=a.archive/BATCH/obj['file'];assert sha(p)==obj['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
        write(a.out,dict(status='passed-detached-summon',files=len(d['files']),objects=len(d['objects'])));return
    r=a.project;q=r/REL;m=helper(r);deps=m.dependencies(r)
    if a.action=='prepare':
        assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir();d=read(r/'preserved/alchemy-r1.json')
        for f in d['files']:
            rel=f['path'].split('/alchemy-r1/',1)[1]
            if not(rel.startswith(('go-src/','inputs/','ui-assets/'))or rel in['probe.mod','probe.sum','xcheck','alchemy-execution-r1.json']):continue
            t=q/rel;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(m.stored(r,'alchemy-r1','/alchemy-r1/'+rel));t.chmod(f['mode'])
        (q/'inputs/summon-entry.state').write_bytes(m.stored(r,'remaining-spells-r1','/remaining-r1/original-map-r8/map-2/entry.state'))
        (q/'inputs/ida-monthly.json').write_bytes(m.stored(r,'monthly-r1','/monthly-r1/ida/ida-monthly-r1.json'))
        write(q/'baseline.json',deps)
    else:assert deps==read(q/'baseline.json')
    if a.action in['prepare','freeze']:
        if a.action=='freeze':
            for n in['research-paired-progress.go','world-army-review_main.go']:(q/'go-src/tools'/n).write_bytes(m.stored(r,'alchemy-r1','/alchemy-r1/go-src/tools/'+n))
            patch(q/'go-src')
        for n in NEW:
            if(r/'tools'/n).is_file():shutil.copyfile(r/'tools'/n,q/'go-src/tools'/n)
        d=read(q/'alchemy-execution-r1.json');e=dict(original_build=d['candidate_build'].replace('/out/alchemy-candidate','/out/summon-original').replace('tools/probe-alchemy.go','tools/probe-summon.go').replace(' tools/alchemy-probe-bind.go','')+' tools/summon-data.go tools/summon-native-save.go')
        if a.action=='freeze':
            e['candidate_build']=e['original_build'].replace('/out/summon-original','/out/summon-candidate')+' tools/summon-store.go tools/summon-port.go tools/summon-probe-bind.go';e['ui_build']=d['ui_build'].replace('/out/alchemy-ui','/out/summon-ui')+' tools/summon-data.go tools/summon-native-save.go tools/summon-store.go tools/summon-port.go tools/summon-ui.go';e.pop('original_build')
        (q/'summon-execution-r1.json').write_text(json.dumps(e,indent=2)+'\n');return
    if a.action=='publish':
        from PIL import Image
        g=read(q/'gui-r2/receipt.json');assert g['status']=='passed-summon-ui-cold';items=[]
        for i,label in [(0,'outcome'),(2,'army')]:
            row=g['screens'][i];source=q/'gui-r2'/row['phase']/row['canvas'];dest=a.images/('summon-go-'+label+'-r1.png');assert not dest.exists();im=Image.open(source);im.thumbnail((960,600),Image.Resampling.LANCZOS);im.save(dest);items.append(dict(source=str(source.relative_to(r)),source_sha256=sha(source),published=dest.name,published_sha256=sha(dest)))
        write(a.images/'summon-go-runtime-r1.json',dict(images=items,ordinary_f4_and_choice=True,initial_army_access_and_uses_fixture=True,award=g['outcome']['summon']['award'],production_promoted=False));return
    folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
    for f in sorted(q.rglob('*')):
        if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
        assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();h=hashlib.sha256(raw).hexdigest();obj=folder/(h+'.gz')
        if h not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
        files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(raw),mode=f.stat().st_mode&0o777))
    write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Original inputs, VM objects and full frames local-only; no production promotion.'))
if __name__=='__main__':main()
