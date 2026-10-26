#!/usr/bin/env python3
"""052：獨立核對透明圖示、提升本機r54或保存README縮小總覽。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

from PIL import Image, __version__


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, obj):
    assert not path.exists() and path.parent.stat().st_uid == 1000
    with path.open('x') as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=2)+'\n')


def module(path, name):
    spec = importlib.util.spec_from_file_location(name,path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def audit(a):
    p,r=a.project,a.research
    player=p/'workplace/player'
    assets,build,previous=player/'assets-man-icons-candidate-r2',player/'source-candidate-items-r2',player/'source-candidate-map51-r1'
    regdir,controlled,batch=r/'man-icons-registration-r2',r/'items-controlled-r2',r/'man-icons-r1'
    reg=read(regdir/'registration.json')
    assert sha(regdir/'registration.json')=='c003ef2ce4a3d5670272929018a535f9d458674cfd788355c9709ec4b96d40ea'
    assert len(reg['base_files'])==391 and len(list(assets.iterdir()))==425
    for name,expected in reg['base_files'].items():
        assert sha(assets/name)==sha(player/'assets-painted-r53'/name)==expected
    manifest=reg['config']
    assert read(assets/'man-items.json')==manifest
    assert sha(assets/'man-items.json')==reg['manifest_sha256']=='b2404cd42918fd36987554205eece12d55ff04d5365c5a1378c56645dc8d30b2'
    packed=(p/'workplace/intake-20261023/sources/game/8sword/MAN.AY').read_bytes()
    assert digest(packed)==manifest['source_sha256']=='9849714498718f6616644ad717906cc426c3f3f5f335cdb99dbcc8173c8dbe12'
    assert sha(batch/'request.json')==reg['request_sha256']
    sampler=module(p/'tools/audit-encounter-gui.py','sampler')
    caches={}
    assert len(manifest['entries'])==len(reg['generation_receipts'])==16
    for entry,receipt_row in zip(manifest['entries'],reg['generation_receipts']):
        i=entry['source_index'];offset=entry['offset'];raw=packed[offset:offset+388]
        assert raw[:4]==bytes((4,0,16,0)) and digest(raw)==entry['record_sha256'] and digest(raw[:260])==entry['native_sha256']
        assert raw==(regdir/f'man-{i:02d}-native.bin').read_bytes()
        im=entry['image']
        assert sha(assets/im['file'])==sha(batch/im['file'])==im['sha256']
        assert sha(assets/entry['prompt_file'])==sha(batch/entry['prompt_file'])==entry['prompt_sha256']
        assert sha(batch/receipt_row['receipt'])==receipt_row['receipt_sha256']
        generation=read(batch/receipt_row['receipt'])
        assert generation['index']==i and generation['tool']=='built-in image_gen' and generation['alpha_extrema']==[0,255]
        assert sha(batch/generation['reference'])==generation['reference_sha256']
        assert generation['actual_prompt']==(batch/entry['prompt_file']).read_text()
        assert Image.open(assets/im['file']).convert('RGBA').getchannel('A').getextrema()==(0,255)
        caches[i]=sampler.sample(assets/im['file'],96,96,actor=True)
        assert digest(caches[i])==sha(regdir/f'man-{i:02d}.rgba')==entry['cache_sha256']
    log=(r/'items-tests-r2.log').read_text()
    for name in ['RealSourcesAndCaches','FailureAtomic','ControlledSourceDraw']:
        assert '--- PASS: TestItems'+name in log
    for name in ['MatchesFrozenLayers','RejectsBeforePainting']:
        assert '--- PASS: TestSourceOwnedBatch'+name in log
    assert '\nPASS\n' in log and '--- SKIP:' not in log and '\nFAIL' not in log
    def inputs(root,current):
        result={}
        for line in (root/'build-inputs.sha256').read_text().splitlines():
            expected,name=line.split(None,1);name=name.removeprefix('/project/')
            assert sha(root/'src'/name)==expected
            if current:assert sha(p/name)==expected
            result[name]=expected
        return result
    new,old=inputs(build,True),inputs(previous,False)
    assert len(new)==139 and len(old)==137
    assert {n for n,expected in old.items() if new.get(n)!=expected}=={'internal/eightsword/engine.go','internal/eightsword/graphics_actor.go','internal/eightsword/source_scene.go','internal/eightsword/source_render.go'}
    assert set(new)-set(old)=={'internal/eightsword/item_icons.go','internal/eightsword/item_icons_test.go'}
    assert reg['manifest_sha256'] in (build/'src/internal/eightsword/item_icons.go').read_text()
    programs={}
    for line in (build/'build-outputs.sha256').read_text().splitlines():
        expected,name=line.split(None,1);name=Path(name).name
        assert sha(build/name)==expected;programs[name]=expected
    old_programs=read(r/'map-interaction-r1/map51-promotion-r1.json')['programs']
    assert len(programs)==len(old_programs)==7
    for name,expected in old_programs.items():assert sha(previous/name)==sha(player/name)==expected
    receipt=read(controlled/'receipt.json')
    assert receipt['status']=='PASS-controlled-item-source-render-not-natural-acquisition'
    assert receipt['source_renderer'] and receipt['source_direct_calls']>0 and receipt['old_overlay_compositions']==0
    assert receipt['controlled_memory']['restored_and_verified'] and len(receipt['controlled_memory']['original_values'])==2
    assert not receipt['gameplay_changed']
    bg=read(assets/'battle-background.json')['image'];assert sha(assets/bg['file'])==bg['sha256']
    background=sampler.sample(assets/bg['file'],1920,1200)
    rows=receipt['cases']
    assert len(rows)==8 and {(row['index'],row['stage']) for row in rows}=={(i,s) for i in (15,27) for s in ('material-draw','restored','color-draw','color-restored')}
    for row in rows:
        assert row['pixels']==2304000 and row['frame_pure'] and row['paired_guest_equal'] and row['rect']==[288,360,96,96]
        expected=bytearray(background)
        if row['stage'] in ('material-draw','color-draw'):
            cache=caches[row['index']]
            for y in range(96):
                for x in range(96):
                    src=(y*96+x)*4;dst=((360+y)*1920+288+x)*4;alpha=cache[src+3]
                    for c in range(3):
                        base=0 if row['stage']=='color-draw' else expected[dst+c]
                        expected[dst+c]=min(255,cache[src+c]+(base*(255-alpha)+127)//255)
        image=Image.open(controlled/row['png']).convert('RGBA')
        assert image.size==(1920,1200) and image.tobytes()==bytes(expected) and digest(expected)==row['frame_sha256']
    prior=p/'workplace/probe-20261023/graphics-first/battle-r1/source-player-audit-r3.json'
    assert sha(prior)=='c7bab70fc8c6d2b58c5f8d13fab5fb2d96892a21ec9a05e5df8787cc72c7cd50'
    result=dict(schema=1,spec='052',status='PASS-scoped-052-item-icons',production=False,icons=16,candidate_files=425,preserved_files=391,
                build_inputs=139,programs=programs,previous_programs=old_programs,build_inputs_sha256=sha(build/'build-inputs.sha256'),
                registration_sha256=sha(regdir/'registration.json'),controlled_sha256=sha(controlled/'receipt.json'),
                controlled_cases=8,controlled_pixels=18432000,source_direct_calls=receipt['source_direct_calls'],old_overlay_compositions=0,
                memory_restored=True,tests_sha256=sha(r/'items-tests-r2.log'),prior_gui_save_sha256=sha(prior),prior_gui_reused=True,
                asset_hashes={f.name:sha(f) for f in sorted(assets.iterdir())},tool_sha256=sha(Path(__file__)),pillow=__version__,
                limits=['Controlled source rendering, not natural acquisition or item-rule/RNG parity.',
                        'Only fixed32x16 item icons may use owned source colors; other actor eligibility is unchanged.',
                        'No new GUI/save or whole-game HD claim; full art and prompts stay local.'])
    write(a.out,result)
    print(json.dumps({k:result[k] for k in ['status','icons','candidate_files','controlled_cases','controlled_pixels']}))


def promote(a):
    player,result=a.player,read(a.audit)
    assert result['status']=='PASS-scoped-052-item-icons' and result['icons']==16
    build,previous=player/'source-candidate-items-r2',player/'source-candidate-map51-r1'
    assets,target=player/'assets-man-icons-candidate-r2',player/'assets-painted-r54'
    assert player.stat().st_uid==1000 and not target.exists() and not a.out.exists()
    assert sha(build/'build-inputs.sha256')==result['build_inputs_sha256']
    programs=result['programs']
    assert set(programs)=={'8sword','8sword-replay','gui-check','music-check','heroine-check','museum-check','story-prelude-check'}
    for name,expected in programs.items():
        assert sha(build/name)==expected and (build/name).stat().st_uid==1000
        assert sha(previous/name)==sha(player/name)==result['previous_programs'][name]
        assert (player/name).stat().st_uid==1000
    assert len(list(assets.iterdir()))==len(result['asset_hashes'])==425
    for name,expected in result['asset_hashes'].items():
        assert Path(name).name==name and sha(assets/name)==expected and (assets/name).stat().st_uid==1000 and not (assets/name).is_symlink()
    target.mkdir()
    for name in result['asset_hashes']:os.link(assets/name,target/name)
    staged={}
    try:
        for name in programs:
            temp=player/('.items-promote-'+name+'.tmp');assert not temp.exists();os.link(build/name,temp);staged[name]=temp
        metadata={n:(build/n).read_bytes() for n in ['build-inputs.sha256','build-source-checks.log','build-go-version.txt','runtime.json']}
        metadata['build-outputs.sha256']=''.join(f'{expected}  /out/{name}\n' for name,expected in programs.items()).encode()
        for name,data in metadata.items():
            assert (player/name).stat().st_uid==1000
            temp=player/('.items-promote-'+name+'.tmp');assert not temp.exists()
            with temp.open('xb') as f:f.write(data)
            staged[name]=temp
        for name,temp in staged.items():os.replace(temp,player/name)
    finally:
        for temp in staged.values():
            if temp.exists():temp.unlink()
    for name,expected in programs.items():assert sha(player/name)==expected and sha(previous/name)==result['previous_programs'][name]
    write(a.out,dict(schema=1,status='promoted-scoped-052-item-icons',assets=target.name,files=425,preserved_files=391,
                     build=build.name,previous=previous.name,programs=programs,previous_programs=result['previous_programs'],
                     audit_sha256=sha(a.audit),tool_sha256=sha(Path(__file__))))
    print(json.dumps(dict(status='promoted-scoped-052-item-icons',files=425,assets=target.name)))


def overview(a):
    result,promotion=read(a.audit),read(a.promotion)
    assert result['status']=='PASS-scoped-052-item-icons' and promotion['audit_sha256']==sha(a.audit)
    assert promotion['status']=='promoted-scoped-052-item-icons'
    regdir=a.research/'man-icons-registration-r2';reg=read(regdir/'registration.json')
    assert sha(regdir/'registration.json')==result['registration_sha256'] and sha(regdir/'comparison.png')==reg['comparison_sha256']
    target=a.out/'item-icons-original-hd-r1.png';assert not target.exists() and a.out.stat().st_uid==1000
    with target.open('xb') as f:f.write((regdir/'comparison.png').read_bytes())
    write(target.with_suffix('.json'),dict(schema=1,spec='052',status='registered-item-assets-not-natural-acquisition-screenshots',
          image=target.name,image_sha256=sha(target),icons=16,entries=reg['config']['entries'],
          registration_sha256=sha(regdir/'registration.json'),audit_sha256=sha(a.audit),promotion_sha256=sha(a.promotion),
          tool_sha256=sha(Path(__file__)),rights='user-requested compact comparison in existing private repository only; full assets stay local'))
    print(json.dumps(dict(image=target.name,icons=16,bytes=target.stat().st_size)))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('audit','promote','overview'))
    for key in ('project','research','player','audit','promotion'):p.add_argument('--'+key,type=Path)
    p.add_argument('--out',required=True,type=Path)
    a=p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid()==1000 and __version__=='11.3.0'
    {'audit':audit,'promote':promote,'overview':overview}[a.action](a)


if __name__=='__main__':
    main()
