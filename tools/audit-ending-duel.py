#!/usr/bin/env python3
"""053：獨立核對END1人物、END3覆蓋及兩側原版收尾前綴。Docker only。"""
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
    assets = root/'assets-duel-candidate-r1'
    base = player/'assets-painted-r60'
    registration = read(root/'duel-registration-r1.json')
    assert len(registration['base_files']) == 441 and len(list(assets.iterdir())) == 443
    for name, digest in registration['base_files'].items():
        assert sha(base/name) == sha(assets/name) == digest
    assert all(f.is_file() and not f.is_symlink() and f.stat().st_uid == 1000 for f in assets.iterdir())
    manifest = read(assets/'ending-duel.json')
    assert sha(assets/'ending-duel.json') == registration['manifest_sha256'] == '53c709eb2d1f76d9b44aaf555e414c2e092e777fe629de9cdc9542b9af90b056'
    generation = read(root/'end1-art-r1/generation-r1.json')
    raw = root/'end1-art-r1'/generation['image']
    assert sha(raw) == generation['image_sha256'] == '40851c0c267d190ea25242a24aad7177ef15c668ecf448a3688a8210156e6210'
    assert sha(root/'end1-art-r1'/generation['prompt']) == generation['prompt_sha256']
    texture = Image.open(raw).convert('RGBA').crop((0,35,2169,680)).resize((1536,450),Image.Resampling.LANCZOS)
    assert texture.tobytes() == Image.open(assets/'ending-duel.png').convert('RGBA').tobytes()
    assert hashlib.sha256(texture.tobytes()).hexdigest() == registration['normalized_rgba_sha256']
    assert texture.getchannel('A').getextrema() == (255,255)
    log = (root/'runtime-duel-r1.log').read_text()
    for name in ['SourceRuntime','DuelLoadAndFallback','SwordsLoadAndFallback','SwordsTransparentReplay']:
        assert '--- PASS: TestEnding'+name in log
    assert '\nPASS\n' in log and '\nFAIL' not in log and '--- SKIP:' not in log
    assert (root/'runtime-duel-exit-r1.txt').read_text().strip() == 'passed'
    assert (root/'duel-vet-r1.log').read_text() == ''
    run = root/'runtime-duel-r1'
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
    assert [v['stage'] for v in hd['snapshots']] == ['END1.AY','END3.AY']
    previous_control = read(root/'runtime-swords-r1/native/runtime.json')
    for key in ['steps','state_sha256','native_pcm_sha256']:
        assert native[key] == previous_control[key], key
    for name in ['01-main-menu.png','02-map.png','03-character.png','04-army.png']:
        assert sha(run/'hd'/name) == sha(root/'runtime-swords-r1/hd'/name), name
    spec = importlib.util.spec_from_file_location('ending_model',project/'tools/audit-ending-gui.py')
    model = importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
    sources = {}
    for row in read(root/'source.json')['records']:
        if row['color_variant']:
            im = Image.open(root/row['image']).convert('RGBA')
            assert hashlib.sha256(im.tobytes()).hexdigest() == row['decoded_rgba_sha256']
            sources[row['record_sha256']] = im
    frames, all_rects = [], []
    for snapshot in hd['snapshots']:
        sample = snapshot['prefix']
        assert (run/'hd'/(sample+'-before.state')).read_bytes() == (run/'hd'/(sample+'-after.state')).read_bytes()
        meta = read(run/'hd'/(sample+'.json'))
        rects = [(c['X']*3,c['Y']*6,(c['X']+c['W'])*3,(c['Y']+c['H'])*6) for c in meta['ops'] if c['SourceSHA'] == manifest['source_sha256']]
        assert rects
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
            assert diff.getbbox() is not None
            for channel in diff.split():
                assert ImageChops.multiply(channel,ImageChops.invert(mask)).getbbox() is None
            frames.append(dict(stage=snapshot['stage'],font=font,step=meta['step'],image=str(actual.relative_to(project)),image_sha256=sha(actual)))
    previous = read(root/'swords-promotion-r1.json')
    build = player/'source-candidate-duel-r1'
    inputs = (build/'build-inputs.sha256').read_text().splitlines()
    assert len(inputs) == 156
    for line in inputs:
        digest, name = line.split(None,1);name = name.removeprefix('/project/')
        assert sha(project/name) == sha(build/'src'/name) == digest
    programs = {}
    for line in (build/'build-outputs.sha256').read_text().splitlines():
        digest,name = line.split(None,1);name = Path(name).name
        assert sha(build/name) == digest
        assert sha(player/name) == sha(player/'source-candidate-swords-r1'/name) == previous['programs'][name]
        programs[name] = digest
    assert len(programs) == 7
    core = read(player/'runtime-input-r1/runtime-input.json')
    entries = core['base_inputs'] | core['added']
    assert len(entries) == 921
    for name,digest in entries.items():
        assert sha(player/'runtime-input-r1/src'/name) == digest
    result = dict(schema=1,spec='053',status='PASS-scoped-053-ending-duel',production=False,
                  candidate=build.name,previous='source-candidate-swords-r1',assets=assets.name,
                  target_assets='assets-painted-r61',asset_hashes={f.name:sha(f) for f in sorted(assets.iterdir())},
                  preserved_assets=441,programs=programs,previous_programs=previous['programs'],
                  build_inputs_sha256=sha(build/'build-inputs.sha256'),source_inputs=156,
                  runtime_sha256=sha(player/'runtime-input-r1/runtime-input.json'),core_files=921,
                  prefix_steps=hd['steps'],guest_state_sha256=hd['state_sha256'],native_pcm_sha256=hd['native_pcm_sha256'],
                  prefix_direct=hd['ending']['direct'],
                  frames=frames,duel_rectangles=all_rects,tests_sha256=sha(root/'runtime-duel-r1.log'),
                  registration_sha256=sha(root/'duel-registration-r1.json'),model_tool_sha256=sha(project/'tools/audit-ending-gui.py'),
                  tool_sha256=sha(Path(__file__)),limits=['Controlled original ending branch, not natural victory.',
                  'Headless normal player prefix to END4; no new full ending, Esc, GUI or save claim.',
                  'Only END1 record0 added; END3 swords, effects, animation, rules and native PCM preserved.'])
    with a.out.open('x') as f:
        f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],steps=hd['steps'],frames=len(frames))))


if __name__ == '__main__':
    main()
