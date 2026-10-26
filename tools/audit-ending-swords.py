#!/usr/bin/env python3
"""053：獨立核對八劍素材、原版收尾前綴及三字型完整Frame。Docker only。"""
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
    assets = root/'assets-swords-candidate-r3'
    base = player/'assets-painted-r59'
    registration = read(root/'swords-registration-r2.json')
    assert len(registration['base_files']) == 439 and len(list(assets.iterdir())) == 441
    for name, digest in registration['base_files'].items():
        assert sha(base/name) == sha(assets/name) == digest
    assert all(f.is_file() and not f.is_symlink() and f.stat().st_uid == 1000 for f in assets.iterdir())
    manifest = read(assets/'ending-swords.json')
    assert sha(assets/'ending-swords.json') == registration['manifest_sha256'] == '3799c2ca8cc2ea6a5e6a6942d571263bc7a6323f0e9c92b6b7020e8d8b0d3ae8'
    generation = read(root/'swords-art-r1/generation-r2.json')
    raw = root/'swords-art-r1'/generation['image']
    assert sha(raw) == generation['image_sha256'] == 'd3d83dc3d23207934976a47145e06ea321321f62658a19071920a363311bc91f'
    assert sha(root/'swords-art-r1'/generation['prompt']) == generation['prompt_sha256']
    texture = Image.open(raw).convert('RGBA').resize((528,420),Image.Resampling.LANCZOS)
    assert texture.tobytes() == Image.open(assets/'ending-swords.png').convert('RGBA').tobytes()
    assert hashlib.sha256(texture.tobytes()).hexdigest() == registration['normalized_rgba_sha256']
    assert texture.getpixel((264,210))[3] == 0
    log = (root/'runtime-swords-r1.log').read_text()
    for name in ['SourceRuntime','SwordsLoadAndFallback','SwordsTransparentReplay']:
        assert '--- PASS: TestEnding'+name in log
    assert '\nPASS\n' in log and '\nFAIL' not in log and '--- SKIP:' not in log
    assert (root/'runtime-swords-exit-r1.txt').read_text().strip() == 'passed'
    assert (root/'swords-vet-r1.log').read_text() == ''
    run = root/'runtime-swords-r1'
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
    assert len(hd['snapshots']) == 1 and hd['snapshots'][0]['stage'] == 'END3.AY'
    sample = hd['snapshots'][0]['prefix']
    assert (run/'hd'/(sample+'-before.state')).read_bytes() == (run/'hd'/(sample+'-after.state')).read_bytes()
    spec = importlib.util.spec_from_file_location('ending_model',project/'tools/audit-ending-gui.py')
    model = importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
    sources = {}
    for row in read(root/'source.json')['records']:
        if row['color_variant']:
            im = Image.open(root/row['image']).convert('RGBA')
            assert hashlib.sha256(im.tobytes()).hexdigest() == row['decoded_rgba_sha256']
            sources[row['record_sha256']] = im
    meta = read(run/'hd'/(sample+'.json'))
    rects = [(c['X']*3,c['Y']*6,(c['X']+c['W'])*3,(c['Y']+c['H'])*6) for c in meta['ops'] if c['SourceSHA'] == manifest['source_sha256']]
    assert rects
    mask = Image.new('L',(1920,1200),0)
    for rect in rects:
        mask.paste(255,rect)
    frames = []
    for font in ['noto','lishu','caoshu']:
        m = dict(meta,font=font)
        expected = model.reconstruct(m,assets,sources)
        actual = run/'hd'/(sample+'-'+font+'.png')
        assert expected.tobytes() == Image.open(actual).convert('RGBA').tobytes(),font
        previous = model.reconstruct(m,base,sources)
        diff = ImageChops.difference(expected.convert('RGB'),previous.convert('RGB'))
        assert diff.getbbox() is not None
        for channel in diff.split():
            assert ImageChops.multiply(channel,ImageChops.invert(mask)).getbbox() is None
        frames.append(dict(font=font,step=meta['step'],image_sha256=sha(actual)))
    previous = read(project/'workplace/probe-20261023/graphics-first/story-art-r1/hero-poster-pose-r4/promotion-r4.json')
    build = player/'source-candidate-swords-r1'
    inputs = (build/'build-inputs.sha256').read_text().splitlines()
    assert len(inputs) == 154
    for line in inputs:
        digest, name = line.split(None,1);name = name.removeprefix('/project/')
        assert sha(project/name) == sha(build/'src'/name) == digest
    programs = {}
    for line in (build/'build-outputs.sha256').read_text().splitlines():
        digest,name = line.split(None,1);name = Path(name).name
        assert sha(build/name) == digest
        assert sha(player/name) == sha(player/'source-candidate-prelude-poster-r4'/name) == previous['programs'][name]
        programs[name] = digest
    assert len(programs) == 7
    core = read(player/'runtime-input-r1/runtime-input.json')
    entries = core['base_inputs'] | core['added']
    assert len(entries) == 921
    for name,digest in entries.items():
        assert sha(player/'runtime-input-r1/src'/name) == digest
    result = dict(schema=1,spec='053',status='PASS-scoped-053-ending-swords',production=False,
                  candidate=build.name,previous='source-candidate-prelude-poster-r4',assets=assets.name,
                  target_assets='assets-painted-r60',asset_hashes={f.name:sha(f) for f in sorted(assets.iterdir())},
                  preserved_assets=439,programs=programs,previous_programs=previous['programs'],
                  build_inputs_sha256=sha(build/'build-inputs.sha256'),source_inputs=154,
                  runtime_sha256=sha(player/'runtime-input-r1/runtime-input.json'),core_files=921,
                  prefix_steps=hd['steps'],guest_state_sha256=hd['state_sha256'],native_pcm_sha256=hd['native_pcm_sha256'],
                  prefix_direct=hd['ending']['direct'],
                  frames=frames,sword_rectangles=rects,tests_sha256=sha(root/'runtime-swords-r1.log'),
                  registration_sha256=sha(root/'swords-registration-r2.json'),model_tool_sha256=sha(project/'tools/audit-ending-gui.py'),
                  tool_sha256=sha(Path(__file__)),limits=['Controlled original ending branch, not natural victory.',
                  'Headless normal player prefix to END4; no new full ending, Esc, GUI or save claim.',
                  'Only END3 record0 added; source masks, animation, rules and native PCM preserved.'])
    with a.out.open('x') as f:
        f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],steps=hd['steps'],frames=len(frames))))


if __name__ == '__main__':
    main()
