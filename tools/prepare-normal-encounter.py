#!/usr/bin/env python3
"""Isolated normal-map entry, reusing the preserved and sampled Go adapters."""
import argparse, gzip, hashlib, importlib.util, json, os, shutil
from pathlib import Path

REL = 'workplace/probe-20261023/graphics-first/battle-r1/normal-encounter-r1'
BATCH = 'normal-encounter-r1'
NEW = ['normal-encounter-ui.go', 'prepare-normal-encounter.py', 'check-normal-encounter.py', 'normal-encounter.sh']

def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p, v):
    with p.open('x') as f:
        json.dump(v, f, ensure_ascii=False, indent=2); f.write('\n')
def helper(r):
    s = importlib.util.spec_from_file_location('old', r/'tools/prepare-owned-army-ui.py')
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['prepare','freeze','audit','archive','verify'])
    p.add_argument('--project', type=Path); p.add_argument('--archive', type=Path); p.add_argument('--out', type=Path)
    a=p.parse_args(); assert Path('/.dockerenv').exists() and os.getuid()==1000
    if a.action=='verify':
        d=read(a.archive/(BATCH+'.json'))
        for f in d['files']:
            o=d['objects'][f['sha256']]; obj=a.archive/BATCH/o['file']; assert sha(obj)==o['stored_sha256']
            b=gzip.decompress(obj.read_bytes()); assert len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256']
        write(a.out,dict(status='passed-detached-normal-encounter',files=len(d['files']),objects=len(d['objects']))); return
    r=a.project; q=r/REL; m=helper(r); deps=m.dependencies(r)
    if a.action=='prepare':
        assert not q.exists(); q.mkdir(); src=q/'go-src'; (src/'tools').mkdir(parents=True)
        for n in deps['source_inputs']:
            t=src/n; t.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(r/n,t)
        # Restore the exact admitted adapter versions. No old research workspace
        # or controlled snapshot is required to prepare this candidate.
        d=read(r/'preserved/refusal-rng-r1.json')
        for f in d['files']:
            path=f['path']; marker='/go-src/tools/'
            if marker in path:
                name=path.split(marker,1)[1]
                if name=='research-encounter-ui.go': continue
                (src/'tools'/name).write_bytes(m.stored(r,'refusal-rng-r1',marker+name))
        for n in ['probe.mod','probe.sum','paired-reader','xcheck']:
            (q/n).write_bytes(m.stored(r,'refusal-rng-r1','/'+n))
        for n in ['paired-reader','xcheck']: (q/n).chmod(0o700)
        (q/'inputs').mkdir(); (q/'ui-assets').mkdir()
        for n in ['army-catalog.json','combat-catalog.json','original-save.ay','map01.ay']:
            (q/'inputs'/n).write_bytes(m.stored(r,'refusal-rng-r1','/inputs/'+n))
        w=json.loads(m.stored(r,'refusal-rng-r1','/inputs/world-runtime.json'))
        write(q/'inputs/world-normal.json',w)
        for f in d['files']:
            if '/ui-assets/' not in f['path']: continue
            name=f['path'].split('/ui-assets/',1)[1]; t=q/'ui-assets'/name
            t.parent.mkdir(parents=True,exist_ok=True); t.write_bytes(m.stored(r,'refusal-rng-r1','/ui-assets/'+name))
        t=src/'tools/refusal-rng-ui.go'; s=t.read_text().replace('\n\t"path/filepath"','')
        for n in ['before-seed.state','after-seed.state','decision.state']:
            old='o.SaveStateFile(filepath.Join(*encounterEvidence, "'+n+'"))'
            assert old in s; s=s.replace(old,'saveEncounterState(o, "'+n+'")')
        t.write_text(s)
        t=src/'tools/world-army-review_main.go'; s=t.read_text()
        old='if g.Extra != nil && g.Extra.IsActive() {\n\t\treturn "dismiss"'
        assert old in s; s=s.replace(old,'if encounterCurrent != nil && encounterCurrent.active() { return "battle" }\n\t'+old)
        t.write_text(s)
        for n in NEW: shutil.copyfile(r/'tools'/n,src/'tools'/n)
        old=json.loads(m.stored(r,'refusal-rng-r1','/execution-r1.json'))
        command=old['ui_build'].replace('/out/encounter-ui','/out/normal-ui').replace('tools/research-encounter-ui.go','tools/normal-encounter-ui.go')
        write(q/'execution-r1.json',dict(build=command,vet=command.replace('go build','go vet').replace('-o /out/normal-ui ',''),go_image=old['go_image'],go_image_sha256=old['go_image_sha256'],uid=1000,network='none',memory='3g',cpus=2,pids=192,timeout_seconds=900,normal_entry=True,snapshot_load=False,test_seed=False,fixture='Pre-existing Go army: 2500 wolves, leadership30000, gold5000; ordinary Continue and movement.'))
        write(q/'baseline.json',deps); return
    assert deps==read(q/'baseline.json')
    if a.action=='freeze':
        for n in NEW: shutil.copyfile(r/'tools'/n,q/'go-src/tools'/n)
        return
    if a.action=='audit':
        assert all(sha(q/'go-src'/n)==h for n,h in deps['source_inputs'].items())
        inherited=read(r/'preserved/refusal-rng-r1.json')
        for f in inherited['files']:
            if '/go-src/tools/' not in f['path']: continue
            n=f['path'].split('/go-src/tools/',1)[1]
            if n=='research-encounter-ui.go': continue
            expected=m.stored(r,'refusal-rng-r1','/go-src/tools/'+n)
            if n=='refusal-rng-ui.go':
                s=expected.decode().replace('\n\t"path/filepath"','')
                for name in ['before-seed.state','after-seed.state','decision.state']:
                    s=s.replace('o.SaveStateFile(filepath.Join(*encounterEvidence, "'+name+'"))','saveEncounterState(o, "'+name+'")')
                expected=s.encode()
            if n=='world-army-review_main.go':
                s=expected.decode(); old='if g.Extra != nil && g.Extra.IsActive() {\n\t\treturn "dismiss"'
                expected=s.replace(old,'if encounterCurrent != nil && encounterCurrent.active() { return "battle" }\n\t'+old).encode()
            assert (q/'go-src/tools'/n).read_bytes()==expected,n
        d=read(q/'gui-r1/receipt.json'); assert d['status']=='passed-normal-map-entry'
        count=d['encounters']; assert count in [1,2] and len(d['battles'])==len(d['returns'])==count
        first=d['initial']; final=d['final']; assert d['cold']['snapshot']['world']==final['world']
        assert final['encounter_sequence']==count and final['presence_completed']==count and final['battle_native_calls']==0 and final['presence_native_reads']==0
        assert final['native_rows_hex']==first['native_rows_hex'] and not final['controlled_memory'] and not final['encounter_injected']
        assert final['world']['battle'] is None and not final['presence_active'] and final['battle_finished']
        assert len([e for e in final['battle_events'] if e['command']=='natural-encounter'])==count
        for b in d['battles']:
            assert b['normal_player_path'] and not b['controlled_memory'] and not b['encounter_injected'] and b['encounter_confirmed'] and b['world']['battle'] is not None
        expected=json.loads(json.dumps(first['world']))
        for back in d['returns']:
            p=back['retreat_rng']; assert p['After']==(p['Before']*214013+2531011)&0xffffffff
            assert p['Value']==(p['After']>>16)&32767
            expected['army']['gold']-=expected['army']['gold']//(p['Value']//2730+3); expected['revision']+=2
            assert back['world']==expected
        from PIL import Image
        for s in d['screens']:
            canvas=Image.open(q/'gui-r1'/s['canvas']).convert('RGBA'); screen=Image.open(q/'gui-r1'/s['screen']).convert('RGB'); meta=read(q/'gui-r1'/s['metadata'])
            assert canvas.convert('RGB').tobytes()==screen.tobytes() and hashlib.sha256(canvas.tobytes()).hexdigest()==meta['canvas_sha256']==meta['presented_sha256']
        assert (q/'session/gamedata.ay').read_bytes()[12:]==(q/'inputs/original-save.ay').read_bytes()[12:]
        assert all(sha(r/'tools'/n)==sha(q/'go-src/tools'/n) for n in NEW)
        write(a.out,dict(status='passed-normal-map-entry',rearm_naturally_sampled=count==2,source_tools={n:sha(r/'tools'/n) for n in NEW},dependencies=deps,gui=d,production_changed=False,normal_movement=True,controlled_starting_army=True,full_save_lifecycle=False)); return
    folder=a.archive/BATCH; folder.mkdir(); files=[]; objects={}
    for f in sorted(q.rglob('*')):
        if not f.is_file() or 'build-cache' in f.relative_to(q).parts: continue
        assert f.stat().st_uid==1000 and not f.is_symlink(); b=f.read_bytes(); h=hashlib.sha256(b).hexdigest(); obj=folder/(h+'.gz')
        if h not in objects: obj.write_bytes(gzip.compress(b,compresslevel=6,mtime=0)); objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
        files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(b),mode=f.stat().st_mode&0o777))
    write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Local original evidence and full objects excluded from Git.'))
if __name__=='__main__': main()
