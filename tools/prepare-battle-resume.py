#!/usr/bin/env python3
"""Freeze a bounded battle-resume candidate from the preserved F7 candidate."""
import argparse, gzip, hashlib, importlib.util, json, os, shutil, struct
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/battle-resume-r1'
BATCH='battle-resume-r1'
NEW=['research-battle-resume.go','battle-resume-ui.go','probe-battle-resume.go','prepare-battle-resume.py','check-battle-resume.py','battle-resume-fixture.go','check-battle-resume-ui.py','battle-resume.sh','research-battle-resume_test.go','read-world-army-states.go']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
    with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def helper(r):
    spec=importlib.util.spec_from_file_location('previous',r/'tools/prepare-owned-army-ui.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def replace(p,a,b):
    s=p.read_text();assert s.count(a)==1,(p.name,a,s.count(a));p.write_text(s.replace(a,b))
def patch(src):
    p=src/'tools/research-native-checkpoint.go'
    replace(p,'WorldSave\n','WorldSave\n Resume *nativeResumeRef `json:"native_resume,omitempty"`\n')
    replace(p,'if s.Schema == "eightsword-owned-world-save/1" {','if s.Schema==resumeSchema{return validResumeEnvelope(s)}\n if s.Resume!=nil{return false}\n if s.Schema == "eightsword-owned-world-save/1" {')
    replace(p,'if s.Schema == checkpointSchema {','if s.Schema==resumeSchema{return resumeIntent}\n if s.Schema == checkpointSchema {')
    replace(p,'if bytes.Equal(native, before.Bytes.Native) && equalNativeMaps(maps, files) {','if r,_:=savedResume(before.Bytes.World);r==nil && bytes.Equal(native, before.Bytes.Native) && equalNativeMaps(maps, files) {')
    p=src/'tools/research-paired-progress.go'
    replace(p,'i.Schema != checkpointIntent)','i.Schema != checkpointIntent && i.Schema != resumeIntent)')
    replace(p,'if i.Schema == checkpointIntent { return checkCheckpointIntent(s,i) }','if i.Schema==resumeIntent || checkpointIntentSchema(i.Before)==resumeIntent || checkpointIntentSchema(i.After)==resumeIntent {return checkResumeIntent(s,i)}\n if i.Schema == checkpointIntent { return checkCheckpointIntent(s,i) }')
    replace(p,'func (s *progressPairStore) commitCheckpointBytes(expected string, w OwnedWorld, native []byte, files map[string][]byte)','func (s *progressPairStore) commitResumeBytes(expected string, w OwnedWorld, native []byte, files map[string][]byte, resume *nativeResumeRef)')
    replace(p,'buildCheckpointUpdate(b, s.Catalog, s.Combat, w, native, files)','buildResumeUpdate(b, s.Catalog, s.Combat, w, native, files, resume)')
    replace(p,'if e == nil {\n\t\ts.Pending = false\n\t}', 'if e==nil { e=validateResumeObject(s,snap) }\n if e == nil {\n\t\ts.Pending = false\n\t}')
    p=src/'tools/research-runtime-enemy.go'
    replace(p,'Stage                    string','Staged *OwnedWorld\n Stage                    string')
    replace(p,'return x.controlledBattle.enter(m)','if x.Staged!=nil{return false,errControlledBattleYield}\n return x.controlledBattle.enter(m)')
    replace(p,'if e = x.commit(w); e != nil {\n\t\treturn false, e\n\t}', 'x.Staged=&w // Durable activation occurs outside Machine.Step at the held gate.')
    p=src/'tools/normal-encounter-ui.go'
    replace(p,'Previous                             armyScreenExtra','ColdResume bool\n Previous                             armyScreenExtra')
    replace(p,'return x.Opened && !x.Finished ||','return x.UI!=nil && x.Opened && !x.Finished ||')
    replace(p,'return x.Opened && !x.Finished }','return x.UI!=nil && x.Opened && !x.Finished }')
    replace(p,'x.Opened = true\n\t\tx.Port.Current', 'if !x.ColdResume {if e:=captureBattleResume(x);e!=nil{return e}}\n x.Opened = true\n\t\tx.Port.Current')
    replace(p,'if e := pursuitOpening(x); e != nil {\n\t\t\treturn e\n\t\t}', '// Pursuit opening is activated atomically with the native anchor.')
    replace(p,'x.Confirmed = false\n','x.ColdResume=false\n x.Confirmed = false\n')
    p=src/'tools/world-army-review_main.go'
    replace(p,'materializeNativeCheckpoint(*root,*input,*scratch,snap)','materializeResumeCheckpoint(*root,*input,*scratch,store,snap)')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','archive','verify']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
    if a.action=='verify':
        d=read(a.archive/(BATCH+'.json'))
        for f in d['files']:
            o=d['objects'][f['sha256']];b=(a.archive/BATCH/o['file']).read_bytes();assert hashlib.sha256(b).hexdigest()==o['stored_sha256'];raw=gzip.decompress(b);assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
        write(a.out,dict(status='passed-detached-battle-resume',files=len(d['files']),objects=len(d['objects'])));return
    r=a.project;q=r/REL;m=helper(r);deps=m.dependencies(r)
    if a.action=='prepare':
        assert q.parent.is_dir()and q.parent.stat().st_uid==1000;q.mkdir();src=q/'go-src'
        d=read(r/'preserved/native-checkpoint-r1.json')
        for f in d['files']:
            rel=f['path'].split('/native-checkpoint-r1/',1)[1]
            if not(rel.startswith(('go-src/','inputs/','ui-assets/'))or rel in ['probe.mod','probe.sum','xcheck','execution-r1.json']):continue
            t=q/rel;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(m.stored(r,'native-checkpoint-r1','/native-checkpoint-r1/'+rel));t.chmod(f['mode'])
        (q/'inputs/battle-before.state').write_bytes(m.stored(r,'runtime-enemy-r1','/inputs/battle-before.state'))
        patch(src)
        # Pin the complete core index and relocated source bytes independently
        # of runtime frames. Do not treat VM codec v3 alone as ABI identity.
        core=hashlib.sha256(json.dumps(deps['core_files'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
        raw=(q/'inputs/PAM.AY').read_bytes();u16=lambda at:struct.unpack_from('<H',raw,at)[0];code=bytearray(raw[u16(8)*16:])
        for i in range(u16(6)):
            at=u16(24)+i*4;off=u16(at+2)*16+u16(at);struct.pack_into('<H',code,off,(struct.unpack_from('<H',code,off)[0]+0x110)&65535)
        sig=hashlib.sha256(code[0x151c:0x1796]+code[0x32e0:0x3774]+code[0x1953e:0x19566]).hexdigest()
        (src/'tools/battle-resume-pins.go').write_text('//go:build ignore\n\npackage main\nconst resumeCoreSHA="'+core+'"\nconst resumeCodeSHA="'+sig+'"\n')
        old=read(q/'execution-r1.json');ui=old['ui_build'].replace('/out/checkpoint-ui','/out/resume-ui')+' tools/research-battle-resume.go tools/battle-resume-pins.go tools/battle-resume-ui.go'
        common=['owned-army-model.go','research-owned-world.go','research-owned-defeat.go','research-owned-encounter.go','research-native-progress.go','research-paired-progress.go','research-world-army-port.go','research-controlled-battle.go','research-runtime-enemy.go','research-refusal-rng.go','research-native-checkpoint.go','research-battle-resume.go','battle-resume-pins.go']
        probe='go build -mod=readonly -modfile=/out/probe.mod -o /out/resume-probe '+' '.join('tools/'+n for n in common)+' tools/probe-battle-resume.go'
        write(q/'resume-execution-r1.json',dict(ui_build=ui,ui_fixture_build=ui.replace('/out/resume-ui','/out/resume-ui-fixture')+' tools/battle-resume-fixture.go',probe_build=probe,baseline=deps,core_sha256=core,code_sha256=sig,formal_changed=False))
        write(q/'baseline.json',deps)
    else:assert deps==read(q/'baseline.json')
    if a.action in ['prepare','freeze']:
        if a.action=='freeze':
            d=read(r/'preserved/native-checkpoint-r1.json')
            for f in d['files']:
                marker='/go-src/tools/'
                if marker in f['path']:
                    n=f['path'].split(marker,1)[1];(q/'go-src/tools'/n).write_bytes(m.stored(r,'native-checkpoint-r1',marker+n))
            patch(q/'go-src')
        for n in NEW:
            if (r/'tools'/n).is_file():shutil.copyfile(r/'tools'/n,q/'go-src/tools'/n)
        return
    folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
    for f in sorted(q.rglob('*')):
        if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
        assert f.stat().st_uid==1000 and not f.is_symlink();b=f.read_bytes();h=hashlib.sha256(b).hexdigest();obj=folder/(h+'.gz')
        if h not in objects:obj.write_bytes(gzip.compress(b,compresslevel=6,mtime=0));objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
        files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(b),mode=f.stat().st_mode&0o777))
    write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Local original inputs and complete objects excluded from Git.'))
if __name__=='__main__':main()
