#!/usr/bin/env python3
"""053：獨立重建END6四材質、遮罩與完整結局代表。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, __version__


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def rgba(p): return Image.open(p).convert('RGBA')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid()==1000 and __version__=='11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid==1000
    root=a.project; player=root/'workplace/player'; batch=root/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    render=root/'workplace/probe-20261023/graphics-first/render-takeover-r1'
    assets=batch/'assets-pair-candidate-r1'; base=player/'assets-painted-r62'
    registration=read(batch/'pair-registration-r1.json')
    assert len(registration['base_files'])==455 and len(list(assets.iterdir()))==460
    for name,digest in registration['base_files'].items(): assert sha(base/name)==sha(assets/name)==digest
    manifest=read(assets/'ending-pair.json')
    assert sha(assets/'ending-pair.json')==registration['manifest_sha256']=='c230dfefb876877f2a5f8430296c4e4e2644497acfbe74562a48de95a245670b'
    art=batch/'end6-pair-art-r1'; generation=read(art/'generation-r2.json')
    assert sha(art/'generation-r2.json')==registration['generation_sha256']
    assert sha(art/generation['image'])==generation['image_sha256']=='510742d5838478747a8f3c0bb8c017fed6319071d7564c93718689b144e24a8b'
    for version in ['r1','r2']:
        g=read(art/('generation-'+version+'.json'))
        assert sha(art/g['image'])==g['image_sha256'] and sha(art/g['prompt'])==g['prompt_sha256']
    raw=rgba(art/generation['image'])
    sources={}; source_rows={}
    for row in read(batch/'source.json')['records']:
        if row['color_variant']:
            im=rgba(batch/row['image'])
            assert hashlib.sha256(im.tobytes()).hexdigest()==row['decoded_rgba_sha256']
            sources[row['record_sha256']]=im
            source_rows[row['record_sha256']]=row
    for row in manifest['records']:
        src=source_rows[row['source_sha256']]
        assert src['source_file']=='END6.AY' and src['record']==row['record']
        native=sources[row['source_sha256']]
        assert tuple(row['native_bbox'])==native.getchannel('A').getbbox()
        assert sum(c[3]!=0 and c[:3]==(0,0,0) for c in native.getdata())==row['black_writes']
        x,y,z,w=row['target_bbox']; expected=Image.new('RGBA',(408,300))
        expected.paste(raw.resize((z-x,w-y),Image.Resampling.LANCZOS),(x,y))
        assert expected.tobytes()==rgba(assets/row['image']).tobytes()
        assert sha(assets/row['image'])==row['image_sha256']
    logs=(batch/'runtime-pair-r1.log').read_text()
    assert '\nPASS\n' in logs and '--- FAIL:' not in logs and '--- SKIP:' not in logs
    for name in ['PairLoadAndFallback','PairSourceMasksAndReplay','SourceRuntime','EffectsLoadAndFallback','EffectsLayering','SwordsTransparentReplay']:
        assert '--- PASS: TestEnding'+name in logs,name
    assert (batch/'pair-vet-r1.log').read_text()==''
    spec=importlib.util.spec_from_file_location('ending_model',root/'tools/audit-ending-gui.py')
    model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
    controlled=[]
    sources['fixture-red']=Image.new('RGBA',(640,200),(255,85,85,255))
    for i in range(1,5):
        meta=read(batch/'pair-controlled-r1'/f'pair-{i:02d}.json')
        assert meta['controlled'] and meta['record']==i
        for suffix,group in [('hd',assets),('original',base)]:
            output=batch/'pair-controlled-r1'/f'pair-{i:02d}-{suffix}.png'
            assert model.reconstruct(meta,group,sources).tobytes()==rgba(output).tobytes()
            controlled.append(dict(record=i,kind=suffix,image=str(output.relative_to(root)),sha256=sha(output)))
    run=batch/'runtime-pair-r1'; pairs={}; frames=[]
    for suffix in ['', '-escape']:
        native,hd=read(run/('native'+suffix)/'runtime.json'),read(run/('hd'+suffix)/'runtime.json')
        for key in ['steps','state_sha256','native_pcm_sha256','inputs','file_ops','mutations','unimplemented']: assert native[key]==hd[key],key
        assert sha(run/('native'+suffix)/'final.state')==sha(run/('hd'+suffix)/'final.state')==native['state_sha256']
        prior=read(render/'compat-candidate-ending-r1'/('hd'+suffix)/'runtime.json')
        assert all(hd[k]==prior[k] for k in ['steps','state_sha256','native_pcm_sha256'])
        pairs['hd'+suffix]={k:hd[k] for k in ['steps','state_sha256','native_pcm_sha256']}
        old_by_stage={v['stage']:v['prefix'] for v in prior['snapshots']}
        for sample in hd['snapshots']:
            directory=run/('hd'+suffix); prefix=sample['prefix']; meta=read(directory/(prefix+'.json'))
            assert (directory/(prefix+'-before.state')).read_bytes()==(directory/(prefix+'-after.state')).read_bytes()
            rects=[(c['X']*3,c['Y']*6,(c['X']+c['W'])*3,(c['Y']+c['H'])*6) for c in meta['ops'] if c['SourceSHA'] in {v['source_sha256'] for v in manifest['records']}]
            for font in ['noto','lishu','caoshu']:
                actual=rgba(directory/(prefix+'-'+font+'.png')); chosen=dict(meta,font=font)
                assert model.reconstruct(chosen,assets,sources).tobytes()==actual.tobytes()
                if sample['stage']=='END6.AY':
                    assert rects
                    previous=model.reconstruct(chosen,base,sources)
                    mask=Image.new('L',(1920,1200)); draw=ImageDraw.Draw(mask)
                    for rect in rects: draw.rectangle((rect[0],rect[1],rect[2]-1,rect[3]-1),fill=255)
                    diff=ImageChops.difference(previous,actual).convert('RGB')
                    assert diff.getbbox() is not None
                    assert not ImageChops.multiply(diff,ImageChops.invert(mask).convert('RGB')).getbbox()
                else:
                    old=render/'compat-candidate-ending-r1'/('hd'+suffix)/(old_by_stage[sample['stage']]+'-'+font+'.png')
                    assert actual.tobytes()==rgba(old).tobytes()
                image=directory/(prefix+'-'+font+'.png')
                frames.append(dict(stage=sample['stage'],font=font,image=str(image.relative_to(root)),image_sha256=sha(image)))
    assert sum(v['stage']=='END6.AY' for v in frames)==3
    baseline=render/'compat-candidate-ending-r1/hd'
    for name in ['01-main-menu.png','02-map.png','03-character.png','04-army.png']:
        assert rgba(run/'hd'/name).tobytes()==rgba(baseline/name).tobytes()
    candidate=player/'source-candidate-pair-r1'; previous=player/'source-candidate-step-clock-r1'; old=read(render/'step-clock-audit-r1.json')
    inputs={}
    for line in (candidate/'build-inputs.sha256').read_text().splitlines():
        digest,name=line.split(None,1); assert name.startswith('/project/'); name=name.removeprefix('/project/')
        assert sha(root/name)==sha(candidate/'src'/name)==digest; inputs[name]=digest
    assert len(inputs)==173
    programs={name:sha(candidate/name) for name in old['programs']}
    assert {name:sha(player/name) for name in programs}==old['programs']
    for name,digest in old['programs'].items(): assert sha(previous/name)==digest
    runtime=read(candidate/'runtime.json'); assert runtime['total_inputs']==923
    for name,digest in runtime['files'].items(): assert sha(player/'runtime-render-r1/src'/name)==digest
    originals=[v for v in read(root/'workplace/intake-20261023/source-manifest.json')['files'] if v['path'].startswith('game/8sword/')]
    assert len(originals)==158
    for v in originals: assert sha(root/'workplace/intake-20261023/sources'/v['path'])==v['sha256']
    result=dict(schema=1,spec='053',status='PASS-scoped-053-ending-pair',candidate=candidate.name,previous=previous.name,
        assets=assets.name,target_assets='assets-painted-r63',programs=programs,previous_programs=old['programs'],
        asset_hashes={p.name:sha(p) for p in assets.iterdir()},source_inputs=inputs,source_input_count=173,
        build_inputs_sha256=sha(candidate/'build-inputs.sha256'),runtime_sha256=sha(candidate/'runtime.json'),core_files=923,
        frames=frames,controlled=controlled,ending=pairs,generation_sha256=sha(art/'generation-r2.json'),
        receipts={str(p.relative_to(root)):sha(p) for p in [batch/'runtime-pair-r1.log',batch/'pair-vet-r1.log',batch/'pair-registration-r1.json']},
        tool_sha256=sha(Path(__file__)),model_sha256=sha(root/'tools/audit-ending-gui.py'),
        limits=['Controlled original ending branch with ordinary player prefix; no natural-victory claim.','Four real-source controlled images and one normal END6 sample; no new GUI/save claim.'])
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],assets=460,inputs=173,frames=len(frames),controlled=len(controlled))))


if __name__=='__main__': main()
