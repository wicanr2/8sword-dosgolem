#!/usr/bin/env python3
"""Reversible full-native checkpoint candidate; formal save formats stay intact."""
import argparse,ast,gzip,hashlib,importlib.util,json,os,shutil,struct,tempfile
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/native-checkpoint-r1'
BATCH='native-checkpoint-r1'
NEW=['research-native-checkpoint.go','native-checkpoint-port.go','native-checkpoint-ui.go','probe-native-checkpoint.go','research-native-checkpoint_test.go','prepare-native-checkpoint.py','check-native-checkpoint.py','native-checkpoint.sh','export-native-checkpoint-ida.py','owned-army-ui-xcheck.go']
COMMON=['owned-army-model.go','research-owned-world.go','research-owned-defeat.go','research-owned-encounter.go','research-native-progress.go','research-paired-progress.go','research-world-army-port.go','research-native-checkpoint.go','native-checkpoint-port.go']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
    with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def helper(r):
    s=importlib.util.spec_from_file_location('previous',r/'tools/prepare-owned-army-ui.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def patch(src):
    p=src/'tools/research-paired-progress.go';s=p.read_text()
    pairs=[('var saved WorldSave','var saved checkpointSave'),('saved.Schema != "eightsword-owned-world-save/1"','!validCheckpointEnvelope(saved, b.World)'),('i.Schema != "eightsword-pair-intent/1"','(i.Schema != "eightsword-pair-intent/1" && i.Schema != checkpointIntent)'),('expected, e := buildProgressPair(i.Before.Native, s.Catalog, s.Combat, after.World)','if i.Schema == checkpointIntent { return checkCheckpointIntent(s,i) }\n\tif checkpointIntentSchema(i.Before)==checkpointIntent {return errors.New("checkpoint envelope cannot be downgraded")}\n\texpected, e := buildProgressPair(i.Before.Native, s.Catalog, s.Combat, after.World)'),('func (s *progressPairStore) Commit(expected string, w OwnedWorld)','func (s *progressPairStore) commitCheckpointBytes(expected string, w OwnedWorld, native []byte, files map[string][]byte)'),('after, e := buildProgressPair(b.Native, s.Catalog, s.Combat, w)','after, e := buildCheckpointUpdate(b, s.Catalog, s.Combat, w, native, files)'),('progressPairIntent{"eightsword-pair-intent/1",','progressPairIntent{checkpointIntentSchema(after),')]
    for a,b in pairs:assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
    p.write_text(s)
    p=src/'tools/research-world-army-port.go';s=p.read_text();assert s.count('0x8524, ')==1;p.write_text(s.replace('0x8524, ',''))
    p=src/'tools/world-army-review_main.go';s=p.read_text();a=s.index('\tif e = os.Mkdir(*scratch, 0700)');b=s.index('\tengine, e := game.Open',a)
    s=s[:a]+'\tif e = materializeNativeCheckpoint(*root,*input,*scratch,snap);e!=nil{return e}\n'+s[b:];p.write_text(s)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','audit','archive','verify']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
    if a.action=='verify':
        d=read(a.archive/(BATCH+'.json'))
        for f in d['files']:
            o=d['objects'][f['sha256']];p=a.archive/BATCH/o['file'];assert sha(p)==o['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
        write(a.out,dict(status='passed-detached-native-checkpoint',files=len(d['files']),objects=len(d['objects'])));return
    r=a.project;q=r/REL;m=helper(r);deps=m.dependencies(r)
    if a.action=='prepare':
        assert(q/'ida/ida-checkpoint-r1.json').is_file()and not(q/'go-src').exists();src=q/'go-src';(src/'tools').mkdir(parents=True)
        for n in deps['source_inputs']:t=src/n;t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,t)
        d=read(r/'preserved/normal-encounter-r1.json')
        for f in d['files']:
            marker='/go-src/tools/'
            if marker in f['path']:
                n=f['path'].split(marker,1)[1];(src/'tools'/n).write_bytes(m.stored(r,'normal-encounter-r1',marker+n))
        for n in ['probe.mod','probe.sum','xcheck']:(q/n).write_bytes(m.stored(r,'normal-encounter-r1','/'+n))
        (q/'xcheck').chmod(0o700);(q/'inputs').mkdir();(q/'ui-assets').mkdir()
        for n in ['army-catalog.json','combat-catalog.json','original-save.ay','map01.ay','world-normal.json']:(q/'inputs'/n).write_bytes(m.stored(r,'normal-encounter-r1','/inputs/'+n))
        (q/'inputs/maps').mkdir()
        for i in range(9):
            n=f'map{i:02d}.ay';p=r/'workplace/intake-20261023/sources/game/8sword'/n.upper();b=(q/'inputs/map01.ay').read_bytes()if i==1 else p.read_bytes();assert len(b)==5761;(q/'inputs/maps'/n).write_bytes(b)
        (q/'inputs/PAM.AY').write_bytes((r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes())
        for f in d['files']:
            marker='/ui-assets/'
            if marker not in f['path']:continue
            n=f['path'].split(marker,1)[1];t=q/'ui-assets'/n;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(m.stored(r,'normal-encounter-r1',marker+n))
        patch(src)
        old=json.loads(m.stored(r,'normal-encounter-r1','/execution-r1.json'))
        command=old['build'].replace('/out/normal-ui','/out/checkpoint-ui')+' tools/research-native-checkpoint.go tools/native-checkpoint-port.go tools/native-checkpoint-ui.go'
        common=' '.join('tools/'+n for n in COMMON)
        write(q/'execution-r1.json',dict(ui_build=command,ui_vet=command.replace('go build','go vet').replace('-o /out/checkpoint-ui ',''),probe_build='go build -mod=readonly -modfile=/out/probe.mod -o /out/checkpoint-probe '+common+' tools/probe-native-checkpoint.go',test='go test -mod=readonly -modfile=/out/probe.mod '+common+' tools/probe-native-checkpoint.go tools/research-native-checkpoint_test.go',go_image=old['go_image'],go_image_sha256=old['go_image_sha256'],uid=1000,network='none',memory='3g',cpus=2,pids=192,normal_save_schema_promoted=False))
        write(q/'xcheck-execution-r1.json',dict(build='go build -mod=readonly -modfile=/out/probe.mod -o /out/xcheck tools/owned-army-ui-xcheck.go',reason='Existing XTEST helper extended with F7 keysym0xffc4; required before GUI sampling.'))
        write(q/'baseline.json',deps)
    else:assert deps==read(q/'baseline.json')
    if a.action in ['prepare','freeze']:
        for n in NEW:shutil.copyfile(r/'tools'/n,q/'go-src/tools'/n)
        return
    if a.action=='audit':
        assert all(sha(q/'go-src'/n)==h for n,h in deps['source_inputs'].items())
        for n in NEW:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n)
        with tempfile.TemporaryDirectory()as temp:
            expected=Path(temp);(expected/'tools').mkdir();inherited=read(r/'preserved/normal-encounter-r1.json');names=[]
            for f in inherited['files']:
                if '/go-src/tools/'not in f['path']:continue
                n=f['path'].split('/go-src/tools/',1)[1];names.append(n);(expected/'tools'/n).write_bytes(m.stored(r,'normal-encounter-r1','/go-src/tools/'+n))
            patch(expected)
            for n in names:
                if n in NEW:continue
                assert (expected/'tools'/n).read_bytes()==(q/'go-src/tools'/n).read_bytes(),n
        ida=read(q/'ida/ida-checkpoint-r1.json');raw=(q/'inputs/PAM.AY').read_bytes();assert sha(q/'inputs/PAM.AY')==ida['source_sha256'];header=struct.unpack_from('<H',raw,8)[0]*16;rel=[];lines=0
        for i in range(struct.unpack_from('<H',raw,6)[0]):off,seg=struct.unpack_from('<HH',raw,struct.unpack_from('<H',raw,24)[0]+i*4);rel.append(header+seg*16+off)
        for f in ida['functions']:
            for l in f['lines']:
                pos=l['file_offset'];want=bytes.fromhex(l['bytes']);b=bytearray(raw[pos:pos+len(want)]);assert pos==l['ida_linear']-0x10000+header
                for at in rel:
                    if pos<=at and at+2<=pos+len(want):struct.pack_into('<H',b,at-pos,(struct.unpack_from('<H',b,at-pos)[0]+0x1000)&65535)
                assert bytes(b)==want;lines+=1
        probe=read(q/'probe-r1/receipt.json');assert probe['status']=='passed-native-checkpoint-cold-engine'and probe['saved_location']==probe['cold_location']
        assert probe['saved_map_sha256']==probe['cold_map_sha256']and probe['native_army_unchanged']and probe['world_cold_equal']
        # Recompute the deliberately changed byte and original 100->50 map
        # normalization independently, using the saved raw evidence.
        folder=q/'probe-r1';before=(folder/'map-before-patch.bin').read_bytes();patched=bytearray(before);edit=probe['controlled_map_write'];assert before[edit['source']]==edit['after']and before[edit['target']]==edit['before'];patched[edit['target']]=edit['after'];assert bytes(patched)==(folder/'map-before-save.bin').read_bytes()
        normalized=bytes(patched).replace(bytes([100]),bytes([50]));assert normalized==(folder/'saved-map.bin').read_bytes()and hashlib.sha256(normalized).hexdigest()==probe['saved_map_sha256']
        side=read(folder/'session/gamedata.ay.army.json');assert side['schema']=='eightsword-owned-world-save/2'and side['world']==probe['world']and side['original_sha256']==sha(folder/'native-saved.ay')
        import base64
        assert set(side['native_files'])=={f'map{i:02d}.ay'for i in range(9)}
        for name,b64 in side['native_files'].items():
            b=base64.b64decode(b64,validate=True);assert len(b)==5761 and b==(folder/'scratch'/name).read_bytes()==(folder/'cold-scratch'/name).read_bytes()
        assert base64.b64decode(side['native_files'][probe['saved_location']['map_name']])==normalized
        for event in probe['file_events']:
            assert event['shadow_army_reads']==12 and sorted((v['Name'].lower(),v['N'])for v in event['write_requests'])==[('gamedata.ay',2987),('map01.ay',5761)]
        gui=read(q/'gui-r1/receipt.json');assert gui['status']=='passed-native-checkpoint-ui-cold'
        assert gui['saved']['world']==gui['cold']['world']and gui['saved']['native_location']==gui['cold']['native_location']
        from PIL import Image
        for s in gui['screens']:
            folder=q/'gui-r1'/s['phase'];im=Image.open(folder/s['canvas']).convert('RGBA');screen=Image.open(folder/s['screen']).convert('RGB');meta=read(folder/s['metadata']);assert im.convert('RGB').tobytes()==screen.tobytes()and hashlib.sha256(im.tobytes()).hexdigest()==meta['canvas_sha256']==meta['presented_sha256']
        write(a.out,dict(status='passed-native-checkpoint-candidate',ida_lines=lines,probe=probe,gui=gui,dependencies=deps,source_tools={n:sha(r/'tools'/n)for n in NEW},production_changed=False,format_promoted=False));return
    folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
    for f in sorted(q.rglob('*')):
        if not f.is_file()or 'build-cache'in f.relative_to(q).parts:continue
        assert f.stat().st_uid==1000 and not f.is_symlink();b=f.read_bytes();h=hashlib.sha256(b).hexdigest();obj=folder/(h+'.gz')
        if h not in objects:obj.write_bytes(gzip.compress(b,compresslevel=6,mtime=0));objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
        files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(b),mode=f.stat().st_mode&0o777))
    write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Local original game input and complete objects excluded from Git.'))
if __name__=='__main__':main()
