#!/usr/bin/env python3
"""014：核對海報姿態前導圖與正常開場，通過後可另版提升。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
from PIL import Image, __version__


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def repair_runtime_metadata(a):
    """舊提升器複製研究標記；只修正已提升程式的正式說明，核心與程式保持。"""
    promotion = read(a.audit)
    assert promotion['status'] == 'promoted-poster-pose-prelude-r4'
    player = a.player
    assert player.stat().st_uid == 1000
    build = player/promotion['build']
    for name, digest in promotion['programs'].items():
        assert sha(player/name) == sha(build/name) == digest
    runtime = player/'runtime.json'
    assert runtime.stat().st_uid == 1000 and not runtime.is_symlink()
    before = runtime.read_bytes()
    assert before == (build/'runtime.json').read_bytes()
    core = player/'runtime-input-r1/runtime-input.json'
    manifest = read(core)
    assert manifest['total_inputs'] == 921
    entries = manifest['base_inputs'] | manifest['added']
    assert len(entries) == 921
    for name, digest in entries.items():
        assert sha(player/'runtime-input-r1/src'/name) == digest
    data = read(runtime)
    data.update(production=True, spec='docs/spec/053-ending-hd.md', core_files=921,
                source_preparation_sha256=sha(core))
    temp = player/'.prelude-runtime-metadata.tmp'
    assert not temp.exists()
    temp.write_text(json.dumps(data, indent=2)+'\n')
    os.replace(temp, runtime)
    write = dict(schema=1, status='repaired-formal-r59-runtime-metadata',
                 previous_metadata=read(build/'runtime.json'),
                 previous_sha256=hashlib.sha256(before).hexdigest(),
                 runtime_sha256=sha(runtime), core_manifest_sha256=sha(core),
                 promotion_sha256=sha(a.audit), programs_unchanged=promotion['programs'],
                 tool_sha256=sha(Path(__file__)))
    with a.out.open('x') as f:
        f.write(json.dumps(write, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(status=write['status'], core_files=921)))


def promote(a):
    result=read(a.audit);player=a.player
    assert result['status']=='PASS-poster-pose-prelude-normal-source-render' and result['files']==439 and result['preserved_files']==436
    assert not a.out.exists() and player.stat().st_uid==a.out.parent.stat().st_uid==1000
    build,previous=player/'source-candidate-prelude-poster-r4',player/'source-candidate-end5-r1'
    assets,target=player/'assets-prelude-poster-r4',player/'assets-painted-r59'
    assert not target.exists() and sha(build/'build-inputs.sha256')==result['build_inputs_sha256']
    programs=result['programs']
    assert set(programs)=={'8sword','8sword-replay','gui-check','music-check','heroine-check','museum-check','story-prelude-check'}
    for name,expected in programs.items():
        assert sha(build/name)==expected and (build/name).stat().st_uid==1000
        assert sha(previous/name)==sha(player/name)==result['previous_programs'][name]
        assert (player/name).stat().st_uid==1000
    assert len(list(assets.iterdir()))==len(result['asset_hashes'])==439
    for name,expected in result['asset_hashes'].items():
        assert Path(name).name==name and sha(assets/name)==expected and not (assets/name).is_symlink() and (assets/name).stat().st_uid==1000
    target.mkdir()
    for name in result['asset_hashes']:os.link(assets/name,target/name)
    staged={}
    try:
        for name in programs:
            temp=player/('.prelude-poster-'+name+'.tmp');assert not temp.exists();os.link(build/name,temp);staged[name]=temp
        metadata={n:(build/n).read_bytes() for n in ['build-inputs.sha256','build-source-checks.log','build-go-version.txt']}
        runtime = read(build/'runtime.json')
        assert runtime['total_inputs'] == 921
        runtime.update(production=True, spec='docs/spec/053-ending-hd.md', core_files=921,
                       source_preparation_sha256=sha(player/'runtime-input-r1/runtime-input.json'))
        metadata['runtime.json']=(json.dumps(runtime,indent=2)+'\n').encode()
        metadata['build-outputs.sha256']=''.join(f'{value}  /out/{name}\n' for name,value in programs.items()).encode()
        for name,data in metadata.items():
            assert (player/name).stat().st_uid==1000
            temp=player/('.prelude-poster-'+name+'.tmp');assert not temp.exists()
            with temp.open('xb') as f:f.write(data)
            staged[name]=temp
        for name,temp in staged.items():os.replace(temp,player/name)
    finally:
        for temp in staged.values():
            if temp.exists():temp.unlink()
    for name,expected in programs.items():assert sha(player/name)==expected and sha(previous/name)==result['previous_programs'][name]
    report=dict(schema=1,status='promoted-poster-pose-prelude-r4',assets=target.name,files=439,preserved_files=436,
                build=build.name,previous=previous.name,programs=programs,previous_programs=result['previous_programs'],
                audit_sha256=sha(a.audit),tool_sha256=sha(Path(__file__)))
    with a.out.open('x') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],assets=target.name,files=439)))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('project','research','out'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--promote',action='store_true')
    p.add_argument('--repair-runtime-metadata',action='store_true')
    p.add_argument('--player',type=Path)
    p.add_argument('--audit',type=Path)
    a=p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid()==1000 and __version__=='11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid==1000
    if a.repair_runtime_metadata:
        assert not a.promote
        repair_runtime_metadata(a)
        return
    if a.promote:
        promote(a)
        return
    project,research=a.project,a.research;player=project/'workplace/player'
    assets,base,build,previous=player/'assets-prelude-poster-r4',player/'assets-painted-r58',player/'source-candidate-prelude-poster-r4',player/'source-candidate-end5-r1'
    reg=read(research/'registration-r4.json');m=reg['config']
    assert sha(research/'registration-r4.json')=='51804a43c8996b0cf706e65673fdcdb28954632cc074fe8aaf923d089035382b'
    assert len(list(assets.iterdir()))==len(reg['base_files_sha256'])==439
    replaced=set(reg['replaced']);assert replaced=={'story-prelude.png','story-prelude.json','story-prelude-import.json'}
    for name,expected in reg['base_files_sha256'].items():
        assert sha(base/name)==expected
        if name not in replaced:assert sha(assets/name)==expected
    assert read(assets/'story-prelude.json')==m and sha(assets/'story-prelude.png')==m['image_sha256']
    generation=read(research/'generation-r4.json')
    assert sha(research/'generation-r4.json')==reg['generation_sha256']
    assert generation['tool']=='built-in image_gen' and sha(research/generation['image'])==m['approved_sha256']
    assert sha(research/generation['prompt'])==generation['prompt_sha256']
    assert generation['actual_prompt']==(research/generation['prompt']).read_text()
    raw=Image.open(research/generation['image']).convert('RGBA')
    normalized=raw.resize((1920,1200),Image.Resampling.LANCZOS)
    assert normalized.tobytes()==Image.open(assets/m['image']).convert('RGBA').tobytes()
    assert hashlib.sha256(normalized.tobytes()).hexdigest()==reg['canvas_rgba_sha256']
    def inputs(root,current):
        result={}
        for line in (root/'build-inputs.sha256').read_text().splitlines():
            expected,name=line.split(None,1);name=name.removeprefix('/project/')
            assert sha(root/'src'/name)==expected
            if current:assert sha(project/name)==expected
            result[name]=expected
        return result
    new,old=inputs(build,True),inputs(previous,False)
    assert len(new)==152 and len(old)==152
    assert {n for n,expected in old.items() if new.get(n)!=expected}=={'internal/eightsword/story_prelude_assets.go','internal/eightsword/story_prelude_correction_test.go'}
    assert set(new)==set(old)
    loader=(build/'src/internal/eightsword/story_prelude_assets.go').read_text()
    assert m['approved_sha256'] in loader and m['image_sha256'] in loader
    log=(research/'tests-r4.log').read_text()
    for name in ['PosterPosePairs']:assert '--- PASS: TestStoryPrelude'+name in log
    assert '\nPASS\n' in log and '--- SKIP:' not in log and '\nFAIL' not in log
    programs={}
    for line in (build/'build-outputs.sha256').read_text().splitlines():
        expected,name=line.split(None,1);name=Path(name).name;assert sha(build/name)==expected;programs[name]=expected
    old_programs=read(project/'workplace/probe-20261023/graphics-first/ending-hd-r1/end5-promotion-r1.json')['programs']
    assert len(programs)==len(old_programs)==7
    for name,expected in old_programs.items():assert sha(previous/name)==sha(player/name)==expected
    spec=importlib.util.spec_from_file_location('prelude',project/'tools/audit-story-prelude.py')
    helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)
    runtime=project/'workplace/probe-20261023/music-first/intro-events-r1/unpacked-trace/runtime-0110.bin'
    source=project/'workplace/probe-20261023/graphics-first/intro-r1/TIT6V.AY.decoded'
    assert sha(runtime)=='a764a110b9f8b1d32a6ee9cc0dd650350f917959d647fe4b45cd7f1013eaae68'
    assert sha(source)==m['source_sha256']
    table=runtime.read_bytes()[0xa633-0x1100:0xa633-0x1100+3200]
    assert hashlib.sha256(table).hexdigest()=='607a192b8ed9cf7dcb8f5c83cb5b43b83e9f5dd473f68e91db5fda5a1c4055a6'
    order=[]
    for value in reversed(struct.unpack('<1600H',table)):
        for x in range(value%40,320,40):
            for y in range(value//40,200,40):order.append(y*320+x)
    assert len(order)==64000 and set(order)==set(range(64000))
    native=source.read_bytes()[768:];newroot,oldroot=research/'normal-poster-r4',project/'workplace/probe-20261023/graphics-first/story-art-r1/blue-person-correction-r4/normal-blue-r4'
    isolation=helpers.isolation(newroot,oldroot)
    newmeta,oldmeta=helpers.metadata(newroot),helpers.metadata(oldroot)
    oldart=Image.open(base/'story-prelude.png').convert('RGBA')
    counts={'reveal':0,'complete':0,'handoff':0};samples={};outside=0
    stream_old=iter(helpers.stream(oldroot/'presentation.frames.gz'))
    for number,step,rgba,size in helpers.stream(newroot/'presentation.frames.gz'):
        on,os_,orig,shape=next(stream_old);assert (number,step,size)==(on,os_,shape)
        info,control=newmeta[number-1],oldmeta[number-1]
        assert info['draw']==control['draw']==number and info['step']==control['step']==step and info['stage']==control['stage']
        assert info['prelude']==control['prelude'] and info['story_pages']==control['story_pages']
        stage=info['stage']
        if stage in ('story-prelude','story-prelude-handoff'):
            written=info['prelude']['written']
            assert rgba==helpers.expected(normalized,order,written).tobytes(),('new reveal mismatch',number,written)
            assert orig==helpers.expected(oldart,order,written).tobytes(),('old control mismatch',number,written)
            kind='handoff' if stage=='story-prelude-handoff' else 'complete' if written==64000 else 'reveal'
            counts[kind]+=1
            if kind!='handoff':
                idx=(newroot/f'native-{number:04d}.idx').read_bytes()
                assert idx==(oldroot/f'native-{number:04d}.idx').read_bytes()
                mask=bytearray(64000)
                for at in order[:written]:mask[at]=1
                assert idx==bytes(native[i] if mask[i] else 0 for i in range(64000))
            if kind not in samples:
                name=f'poster-prelude-{kind}-actual.png';target=research/name
                if target.exists():
                    assert Image.open(target).convert('RGBA').tobytes()==rgba
                else:
                    Image.frombytes('RGBA',size,rgba).save(target)
                samples[kind]=dict(draw=number,step=step,written=written,image=name,image_sha256=sha(target))
        else:
            assert rgba==orig,('outside prelude changed',number,stage);outside+=1
    assert number==len(newmeta)==len(oldmeta) and all(counts.values()) and outside>0
    final=read(newroot/'gui-final.json')
    assert final['source_renderer'] and final['source_frames']>0 and final['owned_render_fault'] is None
    assert final['graphics']['CompositedFrames']==0
    result=dict(schema=1,spec='014',status='PASS-poster-pose-prelude-normal-source-render',production=False,
                files=439,preserved_files=436,replaced=sorted(replaced),programs=programs,previous_programs=old_programs,
                build_inputs=152,build_inputs_sha256=sha(build/'build-inputs.sha256'),registration_sha256=sha(research/'registration-r4.json'),
                tests_sha256=sha(research/'tests-r4.log'),frames=number,counts=counts,outside_equal_frames=outside,isolation=isolation,samples=samples,
                clock='12:00:00.00 fixed before execution,3000 cycles/ms',guest_injection=False,
                asset_hashes={f.name:sha(f) for f in sorted(assets.iterdir())},tool_sha256=sha(Path(__file__)),pillow=__version__,
                limits=['Headless normal opening path; no new GUI/save claim.','Only prelude artwork and fixed loading pair changed; five story backgrounds retained.'])
    with a.out.open('x') as f:f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['status','frames','counts','outside_equal_frames']}))


if __name__=='__main__':
    main()
