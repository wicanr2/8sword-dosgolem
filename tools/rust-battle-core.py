#!/usr/bin/env python3
"""固定Go兵種與原戰場收據的Rust移植工具。只在Docker內使用。"""
import argparse, gzip, hashlib, importlib.util, json, os, shutil
from pathlib import Path

BATCH='rust-battle-core-r1'
REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
PREV='workplace/probe-20261023/graphics-first/battle-r1/original-player-integration-r1'
OLD='workplace/probe-20261023/graphics-first/battle-r1/original-battle-rounds-r1'
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    with p.open('x') as f: json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def checked(r,batch,relative):
    index=read(r/'preserved'/(batch+'.json'))
    row=next(f for f in index['files'] if f['path']==relative)
    p=r/relative
    assert sha(p)==row['sha256'],relative
    return p
def rows_text(rows): return ','.join(f"{v['unit'] or '-'}={v['count']}" for v in rows)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['prepare','models','freeze','audit','archive','verify'])
    for n in ['project','work','crate','archive','out']:p.add_argument('--'+n,type=Path)
    a=p.parse_args();assert Path('/.dockerenv').exists() and os.getuid()==1000
    if a.action=='verify':
        idx=read(a.archive/(BATCH+'.json'))
        for row in idx['files']:
            ob=idx['objects'][row['sha256']];f=a.archive/BATCH/ob['file'];assert sha(f)==ob['stored_sha256']
            raw=gzip.decompress(f.read_bytes());assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
        write(a.out,dict(status='passed-detached-rust-battle-core',files=len(idx['files']),objects=len(idx['objects'])));return
    r=a.project;q=a.work or r/REL;crate=a.crate or r/'internal/remake-rust'
    if a.action=='prepare':
        assert q.is_dir() and not any(q.iterdir());(q/'inputs').mkdir();(q/'native').mkdir()
        sources={}
        for n in ['army-catalog.json','combat-catalog.json','PAM.AY']:
            source=checked(r,'original-player-integration-r1',PREV+'/inputs/'+n)
            shutil.copyfile(source,q/'inputs'/n);sources[n]=sha(source)
        assert sources['army-catalog.json']=='21902471f97d7c545db15a51905067bdbe3b8cfb2f9623a936eba862f273e2da'
        assert sources['combat-catalog.json']=='96a0b0e19f93e24ba942d10bc7bbb7e9a78a5a10cc9ce0fcf02fd3896940de13'
        army=read(q/'inputs/army-catalog.json');combat=read(q/'inputs/combat-catalog.json')['profiles']
        assert len(army['profiles'])==len(combat)==33
        lines=['# id name gold command rank attack hp ranged']
        for row in army['profiles']:
            c=combat[row['id']];assert c['id']==row['id'] and row.get('native_kind',0)==c.get('native_kind',0)
            fields=[row['id'],row['name'],row['gold'],row['command'],row['rank'],c['attack'],c['hp'],int(c['ranged'])]
            lines.append('\t'.join(map(str,fields)))
        dst=crate/'unit-catalog.tsv';assert not dst.exists();dst.write_text('\n'.join(lines)+'\n')
        source=checked(r,'original-battle-rounds-r1',OLD+'/expanded-receipt.json')
        shutil.copyfile(source,q/'inputs/expanded-receipt.json');sources['expanded-receipt.json']=sha(source)
        trace=read(source);assert trace['status']=='passed-original-rounds-expanded'
        replay=['# Captured Go original-interface commands; not a save or autonomous scheduler']
        for scenario in trace['rows']:
            history=scenario['history'] or [];initial=[scenario['initial'],[dict(v) for v in scenario['rows'][1]]]
            seen=set()
            for step in history:
                side=0 if step.get('player',False) else 1;t=step['target']
                for s,raw,key in [(side,t['SourceRaw'],'Source'),(1-side,t['TargetRaw'],'Target')]:
                    if (s,raw) not in seen:
                        assert s==1 or initial[s][raw]==t[key]
                        initial[s][raw]=dict(t[key]);seen.add((s,raw))
            replay.append('\t'.join(['BATTLE',str(scenario['case']),rows_text(initial[0]),rows_text(initial[1])]))
            for step in history:
                side=0 if step.get('player',False) else 1;t=step['target'];calls=step['calls']
                assert calls and all(c['damage']==calls[0]['damage'] and c['encoded']==calls[0]['encoded'] for c in calls)
                fields=['STEP',side,t['SourceRaw'],t['TargetRaw'],t['Source']['count'],step['Before'],step['After'],calls[0]['damage'],calls[0]['encoded'],','.join(str(c['BeforeHP']) for c in calls),','.join(str(c['AfterHP']) for c in calls),','.join(map(str,step['Display'] or [])) or '-']
                replay.append('\t'.join(map(str,fields)))
            replay.append('\t'.join(['END',scenario['result'],rows_text(scenario['rows'][0]),rows_text(scenario['rows'][1])]))
        dst=crate/'battle-replay.tsv';assert not dst.exists();dst.write_text('\n'.join(replay)+'\n')
        for n in ['probe.mod','probe.sum']:shutil.copyfile(r/PREV/n,q/n)
        write(q/'inputs/source-receipt.json',dict(sources=sources,steps=sum(len(s['history']or[])for s in trace['rows']),scenarios=3,kind='Go migration reference; original evidence scope inherited; no new DOS run'))
        return
    if a.action=='models':
        assert not (crate/'battle-models.tsv').exists();shutil.copyfile(q/'battle-models.tsv',crate/'battle-models.tsv');return
    if a.action=='freeze':
        spec=importlib.util.spec_from_file_location('art',r/'tools/original-battle-art.py');art=importlib.util.module_from_spec(spec);spec.loader.exec_module(art)
        manifest=read(r/'preserved/owned-player-source-manifest-r1.json')
        names=set(manifest)|{str(p.relative_to(r))for p in(r/'internal/ownedworld').glob('*.go')}|set(art.EXTRA)
        assert not(q/'source').exists()
        for n in sorted(names):
            dst=q/'source'/n;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(art.patched_scene(r)if n==art.SCENE else(r/n).read_bytes())
        write(q/'source-manifest.json',{n:sha(q/'source'/n)for n in sorted(names)});return
    if a.action=='audit':
        spec=importlib.util.spec_from_file_location('baseline',r/'tools/prepare-owned-army-ui.py');baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline)
        deps=baseline.dependencies(r)
        assert deps==read(r/PREV/'baseline.json')
        for n,digest in read(q/'source-manifest.json').items():assert sha(q/'source'/n)==digest,n
        army=read(q/'inputs/army-catalog.json');combat=read(q/'inputs/combat-catalog.json')['profiles']
        actual={v[0]:v for line in (crate/'unit-catalog.tsv').read_text().splitlines()if not line.startswith('#')and(v:=line.split('\t'))}
        assert len(actual)==33
        for row in army['profiles']:
            c=combat[row['id']]
            assert actual[row['id']]==list(map(str,[row['id'],row['name'],row['gold'],row['command'],row['rank'],c['attack'],c['hp'],int(c['ranged'])]))
        models=(q/'battle-models.tsv').read_text().splitlines();counts={name:sum(line.startswith(name+'\t')for line in models)for name in ['SETUP','SORT','MOTION']}
        for n in ['unit-catalog.tsv','battle-models.tsv','battle-replay.tsv']:assert sha(crate/n)==sha(q/'rust-source'/n),n
        assert(q/'tests-model-export-r1.log').read_text().rstrip().endswith('PASS')
        log=(q/'native/tests-rust-r1.log').read_text();assert 'test result: ok. 12 passed' in log and 'FAILED' not in log
        cli=(q/'native/cli-r1.log').read_text();assert '40' in cli and '201' in cli and '33' in cli
        write(a.out,dict(status='passed-rust-battle-core-audit',models=counts,source=read(q/'inputs/source-receipt.json'),tests_passed=12,cli=cli,crate_files={str(p.relative_to(crate)):sha(p)for p in crate.rglob('*')if p.is_file()},native_binary_sha256=sha(q/'8sword-remake-kernel'),runtime_mounts=['crate:read-only','native output only:read-write'],original_executable_mounted=False,go_mounted=False,formal_baseline_counts={k:len(v)for k,v in deps.items()},limits=['Only native catalog/setup/sort/motion/ordinary state transitions.','Captured action order and selection; no autonomous scheduler, AI, original-style GUI or save integration.','Model vectors compare current Go helpers. Whole-action records inherit existing original-interface evidence; no fresh DOS oracle run.']))
        return
    folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
    for f in sorted(q.rglob('*')):
        if not f.is_file()or any(n in f.relative_to(q).parts for n in ['build-cache','rust-target']):continue
        assert not f.is_symlink()and f.stat().st_uid==1000
        raw=f.read_bytes();digest=hashlib.sha256(raw).hexdigest();obj=folder/(digest+'.gz')
        if digest not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[digest]=dict(file=obj.name,stored_sha256=sha(obj))
        files.append(dict(path=str(Path(REL)/f.relative_to(q)),bytes=len(raw),sha256=digest,mode=f.stat().st_mode&0o777))
    write(a.out,dict(files=files,objects=objects,rights='Full original inputs, receipts and binaries local only. No release.'))
if __name__=='__main__':main()
