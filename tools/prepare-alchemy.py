#!/usr/bin/env python3
"""Reuse preserved F4 evidence and the latest owned world; narrow alchemy slice."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/alchemy-r1'
BATCH='alchemy-r1'
NEW=['prepare-alchemy.py','alchemy-data.go','alchemy-native-save.go','probe-alchemy.go','alchemy-probe-bind.go','alchemy-port.go','alchemy-store.go','alchemy-ui.go','check-alchemy.py','check-alchemy-ui.py','alchemy.sh']
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
    repl('Treasure *treasureAward `json:"treasure,omitempty"`','Treasure *treasureAward `json:"treasure,omitempty"`\n Alchemy *alchemyAward `json:"alchemy,omitempty"`');repl('i.Schema != treasureIntent)','i.Schema != treasureIntent && i.Schema != alchemyIntent)');repl('if i.Schema==treasureIntent','if i.Schema==alchemyIntent{return checkAlchemyIntent(s,i)}\n if i.Alchemy!=nil{return errors.New("alchemy on legacy intent")}\n if i.Schema==treasureIntent');repl('s.Combat.Digest(), b, after, false, nil}','s.Combat.Digest(), b, after, false, nil, nil}');p.write_text(s)
    p=src/'tools/world-army-review_main.go';s=p.read_text();assert s.count('return advanceTreasureUI(g)')==1;s=s.replace('return advanceTreasureUI(g)','return advanceAlchemyUI(g)');s=s.replace('func (g *armyReviewApp) view() string {','func (g *armyReviewApp) view() string {\n if alchemyCurrent!=nil && alchemyCurrent.Active{return "alchemy"}');assert s.count('return state')==1;s=s.replace('return state','state["alchemy"]=alchemyStatus()\n return state');p.write_text(s)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','archive','verify','publish']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--images',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
    if a.action=='verify':
        d=read(a.archive/(BATCH+'.json'))
        for f in d['files']:
            obj=d['objects'][f['sha256']];p=a.archive/BATCH/obj['file'];assert sha(p)==obj['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
        write(a.out,dict(status='passed-detached-alchemy',files=len(d['files']),objects=len(d['objects'])));return
    r=a.project;q=r/REL;m=helper(r);deps=m.dependencies(r)
    if a.action=='prepare':
        assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir();d=read(r/'preserved/treasure-r1.json')
        for f in d['files']:
            rel=f['path'].split('/story-resources-r1/',1)[1]
            if not(rel.startswith(('go-src/','inputs/','ui-assets/'))or rel in['probe.mod','probe.sum','xcheck','treasure-execution-r1.json']):continue
            t=q/rel;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(m.stored(r,'treasure-r1','/story-resources-r1/'+rel));t.chmod(f['mode'])
        for name,suffix in [('alchemy-entry.state','/remaining-r1/original-map-r8/map-1/entry.state'),('ida-map-spells.json','/remaining-r1/ida-r3/ida-remaining.json')]:(q/'inputs'/name).write_bytes(m.stored(r,'remaining-spells-r1',suffix))
        write(q/'baseline.json',deps)
    else:assert deps==read(q/'baseline.json')
    if a.action in['prepare','freeze']:
        if a.action=='freeze':
            for n in['research-paired-progress.go','world-army-review_main.go']:(q/'go-src/tools'/n).write_bytes(m.stored(r,'treasure-r1','/story-resources-r1/go-src/tools/'+n))
            patch(q/'go-src')
        for n in NEW:
            if(r/'tools'/n).is_file():shutil.copyfile(r/'tools'/n,q/'go-src/tools'/n)
        xp=q/'go-src/tools/owned-army-ui-xcheck.go';xs=m.stored(r,'treasure-r1','/story-resources-r1/go-src/tools/owned-army-ui-xcheck.go').decode();assert xs.count('"F3": 0xffc0,')==1;xp.write_text(xs.replace('"F3": 0xffc0,','"F3": 0xffc0, "F4": 0xffc1,'))
        d=read(q/'treasure-execution-r1.json');e=dict(original_build=d['candidate_build'].replace('/out/treasure-candidate','/out/alchemy-original').replace('tools/probe-treasure.go','tools/probe-alchemy.go')+' tools/alchemy-data.go tools/alchemy-native-save.go')
        if a.action=='freeze':
            extra=' tools/alchemy-data.go tools/alchemy-native-save.go tools/alchemy-store.go tools/alchemy-port.go';e['candidate_build']=e['original_build'].replace('/out/alchemy-original','/out/alchemy-candidate')+' tools/alchemy-store.go tools/alchemy-port.go tools/alchemy-probe-bind.go';e['ui_build']=d['ui_build'].replace('/out/treasure-ui','/out/alchemy-ui')+extra+' tools/alchemy-ui.go';e.pop('original_build')
        e['xcheck_build']='go build -mod=readonly -modfile=/out/probe.mod -o /out/xcheck tools/owned-army-ui-xcheck.go'
        (q/'alchemy-execution-r1.json').write_text(json.dumps(e,indent=2)+'\n');return
    if a.action=='publish':
        from PIL import Image
        g=read(q/'gui-r1/receipt.json');row=g['screens'][0];source=q/'gui-r1'/row['phase']/row['canvas'];dest=a.images/'alchemy-go-runtime-r1.png';assert not dest.exists();im=Image.open(source);im.thumbnail((960,600),Image.Resampling.LANCZOS);im.save(dest);write(a.images/'alchemy-go-runtime-r1.json',dict(source=str(source.relative_to(r)),source_sha256=sha(source),published_sha256=sha(dest),initial_learned_and_uses_fixture=True,ordinary_f4_and_choice=True,amount=g['outcome']['alchemy']['amount'],production_promoted=False));return
    folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
    for f in sorted(q.rglob('*')):
        if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
        assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();h=hashlib.sha256(raw).hexdigest();obj=folder/(h+'.gz')
        if h not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
        files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(raw),mode=f.stat().st_mode&0o777))
    write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Original inputs, VM objects and full frames local-only; no production promotion.'))
if __name__=='__main__':main()
