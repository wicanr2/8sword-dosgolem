#!/usr/bin/env python3
"""053：獨立核對紅金光環、原版前綴及三字型完整畫面。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from PIL import Image, ImageChops, __version__


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def rgba(p): return Image.open(p).convert('RGBA')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for k in ['project','out']: p.add_argument('--'+k,type=Path,required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid()==1000 and __version__=='11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid==1000
    root=a.project; player=root/'workplace/player'; batch=root/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    assets=batch/'assets-ring-candidate-r1'; base=player/'assets-painted-r63'
    registration=read(batch/'ring-registration-r1.json')
    assert len(registration['base_files'])==460 and len(list(assets.iterdir()))==462
    assert all(f.is_file() and not f.is_symlink() and f.stat().st_uid==1000 for f in assets.iterdir())
    for name,digest in registration['base_files'].items(): assert sha(base/name)==sha(assets/name)==digest
    manifest=read(assets/'ending-ring.json')
    assert sha(assets/'ending-ring.json')==registration['manifest_sha256']=='40ade60742046cf04effb6153b7c6bc6c792386b5e2025a7e311965cbf6443db'
    art=batch/'end3-ring-art-r1'; generation=read(art/'generation-r1.json')
    assert sha(art/'generation-r1.json')==registration['generation_sha256']
    assert sha(art/generation['image'])==generation['image_sha256']=='a630bfb7dcbdccaa6cf4f5e7944f502c8632e12e31265fc534c472fe5cb93adc'
    assert sha(art/generation['prompt'])==generation['prompt_sha256']
    assert sha(art/generation['reference'])==generation['reference_sha256']
    raw=rgba(art/generation['image'])
    assert raw.size==(1318,1193) and raw.getchannel('A').getextrema()==(0,254)
    assert raw.getpixel((raw.width//2,raw.height//4))[3]==0
    texture=raw.resize((696,630),Image.Resampling.LANCZOS)
    assert texture.tobytes()==rgba(assets/manifest['image']).tobytes()
    assert sha(assets/manifest['image'])==manifest['image_sha256']
    sources={}; rows={}
    for row in read(batch/'source.json')['records']:
        if row['color_variant']:
            im=rgba(batch/row['image'])
            assert hashlib.sha256(im.tobytes()).hexdigest()==row['decoded_rgba_sha256']
            sources[row['record_sha256']]=im; rows[row['record_sha256']]=row
    source=rows[manifest['source_sha256']]
    assert source['source_file']=='END3.AY' and source['record']==1
    assert sha(batch/source['native'])==manifest['source_sha256']
    assert sha(root/'workplace/intake-20261023/sources/game/8sword/END3.AY')==manifest['original_sha256']
    assert not any(c[3] and c[:3]==(0,0,0) for c in sources[manifest['source_sha256']].getdata())
    log=(batch/'runtime-ring-r3.log').read_text()
    assert '\nPASS\n' in log and '--- FAIL:' not in log and '--- SKIP:' not in log
    for name in ['RingLoadAndFallback','RingTransparentReplay','SourceRuntime','SwordsTransparentReplay','EffectsLayering']:
        assert '--- PASS: TestEnding'+name in log,name
    assert (batch/'ring-vet-r3.log').read_text()==''
    run=batch/'runtime-ring-r3'; native=read(run/'native/runtime.json'); hd=read(run/'hd/runtime.json')
    for key in ['steps','state_sha256','native_pcm_sha256','inputs','file_ops','mutations','overlays','unimplemented']:
        assert native[key]==hd[key],key
    assert sha(run/'native/final.state')==sha(run/'hd/final.state')==hd['state_sha256']
    prior_prefix=read(batch/'runtime-effects-r1/native/runtime.json')
    for key in ['steps','state_sha256','native_pcm_sha256']:
        assert native[key]==prior_prefix[key],key
    assert native['hd'] is False and hd['hd'] is True
    assert hd['ending']['active'] and hd['ending']['stage']=='END4.AY'
    assert len(hd['mutations'])==1 and hd['mutations'][0]['old']==0 and hd['mutations'][0]['new']==1
    for key in ['masked-skipped-x86','direct-skipped-x86-instructions']: assert hd['ending']['direct'][key]>0
    assert len(hd['snapshots'])==1
    sample=hd['snapshots'][0]['prefix']; directory=run/'hd'; meta=read(directory/(sample+'.json'))
    assert (directory/(sample+'-before.state')).read_bytes()==(directory/(sample+'-after.state')).read_bytes()
    model_spec=importlib.util.spec_from_file_location('ending_model',root/'tools/audit-ending-gui.py')
    model=importlib.util.module_from_spec(model_spec); model_spec.loader.exec_module(model)
    rects=[(c['X']*3,c['Y']*6,(c['X']+c['W'])*3,(c['Y']+c['H'])*6) for c in meta['ops'] if c['SourceSHA']==manifest['source_sha256']]
    assert rects
    mask=Image.new('L',(1920,1200))
    for rect in rects: mask.paste(255,rect)
    frames=[]
    for font in ['noto','lishu','caoshu']:
        actual=directory/(sample+'-'+font+'.png'); chosen=dict(meta,font=font)
        expected=model.reconstruct(chosen,assets,sources)
        assert expected.tobytes()==rgba(actual).tobytes(),font
        previous=model.reconstruct(chosen,base,sources)
        diff=ImageChops.difference(previous.convert('RGB'),expected.convert('RGB'))
        assert diff.getbbox() is not None
        for c in diff.split(): assert not ImageChops.multiply(c,ImageChops.invert(mask)).getbbox()
        frames.append(dict(stage=meta['stage'],source='END3.AY#1',font=font,step=meta['step'],image=str(actual.relative_to(root)),image_sha256=sha(actual)))
    for name in ['01-main-menu.png','02-map.png','03-character.png','04-army.png']:
        assert rgba(run/'hd'/name).tobytes()==rgba(batch/'runtime-pair-r1/hd'/name).tobytes()
    candidate=player/'source-candidate-ring-r3'; previous=player/'source-candidate-pair-r1'; prior=read(batch/'pair-promotion-r1.json')
    inputs={}
    for line in (candidate/'build-inputs.sha256').read_text().splitlines():
        digest,name=line.split(None,1); assert name.startswith('/project/'); name=name.removeprefix('/project/')
        assert sha(root/name)==sha(candidate/'src'/name)==digest; inputs[name]=digest
    assert len(inputs)==175
    programs={}
    for line in (candidate/'build-outputs.sha256').read_text().splitlines():
        digest,name=line.split(None,1);name=Path(name).name
        assert sha(candidate/name)==digest
        assert sha(player/name)==sha(previous/name)==prior['programs'][name]
        programs[name]=digest
    assert len(programs)==7
    runtime=read(candidate/'runtime.json'); assert runtime['total_inputs']==923
    for name,digest in runtime['files'].items(): assert sha(player/'runtime-render-r1/src'/name)==digest
    originals=[v for v in read(root/'workplace/intake-20261023/source-manifest.json')['files'] if v['path'].startswith('game/8sword/')]
    assert len(originals)==158
    for v in originals: assert sha(root/'workplace/intake-20261023/sources'/v['path'])==v['sha256']
    result=dict(schema=1,spec='053',status='PASS-scoped-053-ending-ring',candidate=candidate.name,previous=previous.name,
        assets=assets.name,target_assets='assets-painted-r64',programs=programs,previous_programs=prior['programs'],
        asset_hashes={p.name:sha(p) for p in assets.iterdir()},source_inputs=inputs,source_input_count=175,
        build_inputs_sha256=sha(candidate/'build-inputs.sha256'),runtime_sha256=sha(candidate/'runtime.json'),core_files=923,
        frames=frames,ring_rectangles=rects,prefix_steps=hd['steps'],guest_state_sha256=hd['state_sha256'],native_pcm_sha256=hd['native_pcm_sha256'],prefix_direct=hd['ending']['direct'],
        generation_sha256=sha(art/'generation-r1.json'),receipts={str(p.relative_to(root)):sha(p) for p in [batch/'runtime-ring-r3.log',batch/'ring-vet-r3.log',batch/'ring-registration-r1.json']},
        tool_sha256=sha(Path(__file__)),model_sha256=sha(root/'tools/audit-ending-gui.py'),
        limits=['Ordinary player prefix with controlled original ending branch; no natural victory claim.','One real END3 ring source sampled in three fonts; no new full ending, Esc, GUI or save claim.'])
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],assets=462,inputs=175,frames=len(frames),steps=hd['steps'])))


if __name__=='__main__': main()
