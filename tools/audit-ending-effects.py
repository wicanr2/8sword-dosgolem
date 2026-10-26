#!/usr/bin/env python3
"""053：獨立核對11筆END2效果、三階段完整Frame及原版收尾前綴。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from PIL import Image, ImageChops, __version__


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    return json.loads(p.read_text())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    project = a.project
    root = project/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    player = project/'workplace/player'
    assets = root/'assets-effects-candidate-r1'
    base = player/'assets-painted-r61'
    registration = read(root/'effects-registration-r1.json')
    assert len(registration['base_files']) == 443 and len(list(assets.iterdir())) == 455
    for name, digest in registration['base_files'].items():
        assert sha(base/name) == sha(assets/name) == digest
    assert all(f.is_file() and not f.is_symlink() and f.stat().st_uid == 1000 for f in assets.iterdir())
    manifest = read(assets/'ending-effects.json')
    assert sha(assets/'ending-effects.json') == registration['manifest_sha256'] == '720b89a14f76b3c47d82c85d21a054f985c7a4900986256e4b78cf5b6887957d'
    groups = [('ground',[0,1,2],1,3,480,198,'r1','8462f07af5e0dd65a85326d995d8ce38614a3d7259f4947473ab11f776fefb70'),
              ('flow',[3,4,5],3,1,216,336,'r1','fda542afe1d3388d27f8b626f3dd2832bb4675aac2246b452ae9c5bbf59fb38d'),
              ('burst',[6,7,8,9,10],3,2,288,240,'r3','7a85877e5007bcfdeb1b75ad084103319317e8c55fc9f6a2abf28c8945df3048')]
    for name,ids,cols,rows,w,h,version,digest in groups:
        batch = root/'effects-art-r1'
        gp = batch/(name+'-generation-'+version+'.json')
        generation = read(gp)
        assert sha(gp) == registration['generations'][name]
        raw = batch/generation['image']
        assert sha(raw) == generation['image_sha256'] == digest
        assert sha(batch/generation['prompt']) == generation['prompt_sha256']
        assert sha(batch/generation['reference']) == generation['reference_sha256']
        sheet = Image.open(raw).convert('RGBA').resize((cols*w,rows*h),Image.Resampling.LANCZOS)
        for cell,index in enumerate(ids):
            x,y = cell%cols*w,cell//cols*h
            expected = sheet.crop((x,y,x+w,y+h))
            row = manifest['records'][index]
            assert row['record'] == index and (row['width'],row['height']) == (w,h)
            assert sha(assets/row['image']) == row['image_sha256']
            assert expected.tobytes() == Image.open(assets/row['image']).convert('RGBA').tobytes()
    assert len(manifest['records']) == 11
    log = (root/'runtime-effects-r1.log').read_text()
    for name in ['SourceRuntime','DuelLoadAndFallback','EffectsLoadAndFallback','EffectsLayering','SwordsLoadAndFallback','SwordsTransparentReplay']:
        assert '--- PASS: TestEnding'+name in log
    assert '\nPASS\n' in log and '\nFAIL' not in log and '--- SKIP:' not in log
    assert (root/'runtime-effects-exit-r1.txt').read_text().strip() == 'passed'
    assert (root/'effects-vet-r1.log').read_text() == ''
    run = root/'runtime-effects-r1'
    native, hd = read(run/'native/runtime.json'), read(run/'hd/runtime.json')
    for key in ['steps','state_sha256','native_pcm_sha256','mutations','inputs','overlays','file_ops','unimplemented']:
        assert native[key] == hd[key], key
    assert (run/'native/final.state').read_bytes() == (run/'hd/final.state').read_bytes()
    assert len(hd['mutations']) == 1 and hd['mutations'][0]['old'] == 0 and hd['mutations'][0]['new'] == 1
    assert native['hd'] is False and hd['hd'] is True
    assert hd['ending']['active'] and hd['ending']['stage'] == 'END4.AY'
    # This prefix ends before END5 text. Only the observed image/mask work applies.
    for key in ['masked-skipped-x86','direct-skipped-x86-instructions']:
        assert hd['ending']['direct'][key] > 0
    assert len(hd['snapshots']) == 3 and {v['stage'] for v in hd['snapshots']} == {'END1.AY','END2.AY','END3.AY'}
    previous_control = read(root/'runtime-duel-r1/native/runtime.json')
    for key in ['steps','state_sha256','native_pcm_sha256']:
        assert native[key] == previous_control[key], key
    for name in ['01-main-menu.png','02-map.png','03-character.png','04-army.png']:
        assert sha(run/'hd'/name) == sha(root/'runtime-duel-r1/hd'/name), name
    spec = importlib.util.spec_from_file_location('ending_model',project/'tools/audit-ending-gui.py')
    model = importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
    sources = {}
    for row in read(root/'source.json')['records']:
        if row['color_variant']:
            im = Image.open(root/row['image']).convert('RGBA')
            assert hashlib.sha256(im.tobytes()).hexdigest() == row['decoded_rgba_sha256']
            sources[row['record_sha256']] = im
    frames, all_rects, sampled_effects = [], [], set()
    for snapshot in hd['snapshots']:
        sample = snapshot['prefix']
        assert (run/'hd'/(sample+'-before.state')).read_bytes() == (run/'hd'/(sample+'-after.state')).read_bytes()
        meta = read(run/'hd'/(sample+'.json'))
        effect_ids = {row['source_sha256']:row['record'] for row in manifest['records']}
        rects = [(c['X']*3,c['Y']*6,(c['X']+c['W'])*3,(c['Y']+c['H'])*6) for c in meta['ops'] if c['SourceSHA'] in effect_ids]
        sampled_effects.update(effect_ids[c['SourceSHA']] for c in meta['ops'] if c['SourceSHA'] in effect_ids)
        if snapshot['stage'] != 'END1.AY': assert rects
        if snapshot['stage'] == 'END2.AY': assert 7 in sampled_effects
        all_rects.extend(rects)
        mask = Image.new('L',(1920,1200),0)
        for rect in rects:
            mask.paste(255,rect)
        for font in ['noto','lishu','caoshu']:
            m = dict(meta,font=font)
            expected = model.reconstruct(m,assets,sources)
            actual = run/'hd'/(sample+'-'+font+'.png')
            assert expected.tobytes() == Image.open(actual).convert('RGBA').tobytes(),(snapshot['stage'],font)
            previous = model.reconstruct(m,base,sources)
            diff = ImageChops.difference(expected.convert('RGB'),previous.convert('RGB'))
            if snapshot['stage'] == 'END1.AY':
                assert diff.getbbox() is None
            else:
                assert diff.getbbox() is not None
            for channel in diff.split():
                assert ImageChops.multiply(channel,ImageChops.invert(mask)).getbbox() is None
            frames.append(dict(stage=snapshot['stage'],font=font,step=meta['step'],image=str(actual.relative_to(project)),image_sha256=sha(actual)))
    previous = read(root/'duel-promotion-r1.json')
    build = player/'source-candidate-effects-r1'
    inputs = (build/'build-inputs.sha256').read_text().splitlines()
    assert len(inputs) == 158
    for line in inputs:
        digest, name = line.split(None,1);name = name.removeprefix('/project/')
        assert sha(project/name) == sha(build/'src'/name) == digest
    programs = {}
    for line in (build/'build-outputs.sha256').read_text().splitlines():
        digest,name = line.split(None,1);name = Path(name).name
        assert sha(build/name) == digest
        assert sha(player/name) == sha(player/'source-candidate-duel-r1'/name) == previous['programs'][name]
        programs[name] = digest
    assert len(programs) == 7
    core = read(player/'runtime-input-r1/runtime-input.json')
    entries = core['base_inputs'] | core['added']
    assert len(entries) == 921
    for name,digest in entries.items():
        assert sha(player/'runtime-input-r1/src'/name) == digest
    result = dict(schema=1,spec='053',status='PASS-scoped-053-ending-effects',production=False,
                  candidate=build.name,previous='source-candidate-duel-r1',assets=assets.name,
                  target_assets='assets-painted-r62',asset_hashes={f.name:sha(f) for f in sorted(assets.iterdir())},
                  preserved_assets=443,programs=programs,previous_programs=previous['programs'],
                  build_inputs_sha256=sha(build/'build-inputs.sha256'),source_inputs=158,
                  runtime_sha256=sha(player/'runtime-input-r1/runtime-input.json'),core_files=921,
                  prefix_steps=hd['steps'],guest_state_sha256=hd['state_sha256'],native_pcm_sha256=hd['native_pcm_sha256'],
                  prefix_direct=hd['ending']['direct'],
                  frames=frames,effect_rectangles=all_rects,sampled_effect_records=sorted(sampled_effects),tests_sha256=sha(root/'runtime-effects-r1.log'),
                  registration_sha256=sha(root/'effects-registration-r1.json'),model_tool_sha256=sha(project/'tools/audit-ending-gui.py'),
                  tool_sha256=sha(Path(__file__)),limits=['Controlled original ending branch, not natural victory.',
                  'Headless normal player prefix to END4; no new full ending, Esc, GUI or save claim.',
                  'Only END2 effects added. Curved-flow records3-5 have images/load checks only, no natural-use claim. END1/END3/END5 art, rules and native PCM preserved.'])
    with a.out.open('x') as f:
        f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],steps=hd['steps'],frames=len(frames))))


if __name__ == '__main__':
    main()
