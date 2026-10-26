#!/usr/bin/env python3
"""045：核對第51筆受控呈現、提升本機素材或建立65筆README圖集。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, __version__


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, obj):
    assert not path.exists() and path.parent.stat().st_uid == 1000
    with path.open('x') as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def audit(a):
    p, r = a.project, a.research
    player = p / 'workplace/player'
    assets, build, previous = player / 'assets-map51-candidate-r1', player / 'source-candidate-map51-r1', player / 'source-candidate-buildings-r1'
    regdir, controlled, batch = r / 'map51-registration-r1', r / 'map51-controlled-r2', r / 'map51-hd-r1'
    reg = read(regdir / 'registration.json')
    assert sha(regdir / 'registration.json') == '770e822929f0131cd2e94956da9dbbf469c9cc871fcb8083da6a6205ce0c52e8'
    assert len(reg['base_files']) == 387 and len(list(assets.iterdir())) == 391
    for name, expected in reg['base_files'].items():
        assert sha(assets / name) == sha(player / 'assets-painted-r52' / name) == expected
    m = reg['config']
    assert sha(assets / 'map-landmark-51.json') == reg['manifest_sha256'] == '336bcb02dc4dc859b00abe9655457d95e6bc45bbd6eabba02d1a0900408bbc72'
    assert read(assets / 'map-landmark-51.json') == m
    source = (p / 'workplace/intake-20261023/sources/game/8sword/PMAP.AY').read_bytes()
    assert digest(source) == m['source_sha256'] == '9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02'
    raw = source[51*1004:52*1004]
    assert digest(raw) == m['record_sha256'] and digest(raw[:804]) == m['native_sha256'] and raw == (regdir / 'pmap51-native.bin').read_bytes()
    im = m['image']
    assert sha(assets / im['file']) == sha(batch / im['file']) == im['sha256']
    assert sha(assets / m['prompt_file']) == sha(batch / m['prompt_file']) == m['prompt_sha256']
    assert sha(batch / 'generation.json') == reg['generation_sha256']
    generation = read(batch / 'generation.json')
    assert generation['tool'] == 'built-in image_gen' and generation['alpha_extrema'] == [255, 255]
    assert sha(batch / generation['reference']) == generation['reference_sha256']
    assert Image.open(assets / im['file']).convert('RGBA').getchannel('A').getextrema() == (255, 255)
    sampler = module(p / 'tools/audit-encounter-gui.py', 'sampler')
    cache = sampler.sample(assets / im['file'], 192, 150)
    assert digest(cache) == sha(regdir / 'map51.rgba') == m['cache_sha256']
    log = (r / 'map51-tests-r2.log').read_text()
    for name in ['RealSourcesAndCaches', 'FailureAtomic', 'ControlledSourceDraw']:
        assert '--- PASS: TestMap51' + name in log
    assert '\nPASS\n' in log and '--- SKIP:' not in log and '\nFAIL' not in log
    def inputs(root, current):
        result = {}
        for line in (root / 'build-inputs.sha256').read_text().splitlines():
            expected, name = line.split(None, 1)
            name = name.removeprefix('/project/')
            assert sha(root / 'src' / name) == expected
            if current:
                assert sha(p / name) == expected
            result[name] = expected
        return result
    inputs_new, inputs_old = inputs(build, True), inputs(previous, False)
    assert len(inputs_new) == 137 and len(inputs_old) == 135
    assert [n for n, expected in inputs_old.items() if inputs_new.get(n) != expected] == ['internal/eightsword/engine.go']
    assert set(inputs_new) - set(inputs_old) == {'internal/eightsword/map_landmark51.go', 'internal/eightsword/map_landmark51_test.go'}
    loader = (build / 'src/internal/eightsword/map_landmark51.go').read_text()
    for expected in [reg['manifest_sha256'], im['sha256'], m['prompt_sha256'], m['record_sha256'], m['native_sha256'], m['cache_sha256']]:
        assert expected in loader
    programs = {}
    for line in (build / 'build-outputs.sha256').read_text().splitlines():
        expected, name = line.split(None, 1)
        name = Path(name).name
        assert sha(build / name) == expected
        programs[name] = expected
    old_programs = read(r / 'buildings-promotion-r1.json')['programs']
    assert len(programs) == len(old_programs) == 7
    for name, expected in old_programs.items():
        assert sha(previous / name) == sha(player / name) == expected
    receipt = read(controlled / 'receipt.json')
    assert receipt['status'] == 'PASS-controlled-map51-source-render-not-natural-reachability'
    assert receipt['source_renderer'] and receipt['source_direct_calls'] > 0 and receipt['old_overlay_compositions'] == 0
    assert receipt['controlled_memory']['restored_and_verified'] and len(receipt['controlled_memory']['original_values']) == 2
    assert not receipt['gameplay_changed']
    bg = read(assets / 'battle-background.json')['image']
    assert sha(assets / bg['file']) == bg['sha256']
    background = sampler.sample(assets / bg['file'], 1920, 1200)
    rows = receipt['cases']
    assert len(rows) == 4 and {row['stage'] for row in rows} == {'back-hidden', 'back-copied', 'front-drawn', 'restored'}
    for row in rows:
        assert row['pixels'] == 2304000 and row['frame_pure'] and row['paired_guest_equal'] and row['rect'] == [288, 360, 192, 150]
        expected = bytearray(background)
        if row['stage'] in ('back-copied', 'front-drawn'):
            for y in range(150):
                at = ((360 + y) * 1920 + 288) * 4
                expected[at:at + 192*4] = cache[y*192*4:(y+1)*192*4]
        image = Image.open(controlled / row['png']).convert('RGBA')
        assert image.size == (1920, 1200) and image.tobytes() == bytes(expected) and digest(expected) == row['frame_sha256']
    caches = read(r / 'map51-caches-r2/caches.json')
    assert len(caches) == 65 and [c['index'] for c in caches] == list(range(65))
    for row in caches:
        i = row['index']
        assert row['native_sha256'] == digest(source[i*1004:i*1004+804])
        path = r / 'map51-caches-r2' / row['file']
        assert path.stat().st_size == 192*150*4 and sha(path) == row['cache_sha256']
    assert caches[51]['cache_sha256'] == m['cache_sha256']
    prior = p / 'workplace/probe-20261023/graphics-first/battle-r1/source-player-audit-r3.json'
    assert sha(prior) == 'c7bab70fc8c6d2b58c5f8d13fab5fb2d96892a21ec9a05e5df8787cc72c7cd50'
    result = dict(schema=1, spec='045', status='PASS-scoped-045-map51', production=False,
                  main_map_materials=65, candidate_files=391, preserved_files=387, build_inputs=137,
                  programs=programs, previous_programs=old_programs, build_inputs_sha256=sha(build / 'build-inputs.sha256'),
                  registration_sha256=sha(regdir / 'registration.json'), controlled_sha256=sha(controlled / 'receipt.json'),
                  controlled_cases=4, controlled_pixels=9216000, old_overlay_compositions=0, memory_restored=True,
                  source_direct_calls=receipt['source_direct_calls'], caches_sha256=sha(r / 'map51-caches-r2/caches.json'),
                  tests_sha256=sha(r / 'map51-tests-r2.log'), prior_gui_save_sha256=sha(prior), prior_gui_reused=True,
                  asset_hashes={f.name: sha(f) for f in sorted(assets.iterdir())}, tool_sha256=sha(Path(__file__)), pillow=__version__,
                  limits=['Controlled presentation, not natural map reachability or rule/RNG parity.',
                          '65 means PMAP0-64 runtime material caches, not whole-game HD coverage.',
                          'No new GUI/save claim; other64 caches reuse their previous validation. Full art stays local.'])
    write(a.out, result)
    print(json.dumps({k: result[k] for k in ['status', 'main_map_materials', 'candidate_files', 'controlled_cases', 'controlled_pixels']}))


def promote(a):
    player, result = a.player, read(a.audit)
    assert result['status'] == 'PASS-scoped-045-map51' and result['main_map_materials'] == 65
    build, previous = player / 'source-candidate-map51-r1', player / 'source-candidate-buildings-r1'
    assets, target = player / 'assets-map51-candidate-r1', player / 'assets-painted-r53'
    assert player.stat().st_uid == 1000 and not target.exists() and not a.out.exists()
    assert sha(build / 'build-inputs.sha256') == result['build_inputs_sha256']
    programs = result['programs']
    assert set(programs) == {'8sword', '8sword-replay', 'gui-check', 'music-check', 'heroine-check', 'museum-check', 'story-prelude-check'}
    for name, expected in programs.items():
        assert sha(build / name) == expected and (build / name).stat().st_uid == 1000
        assert sha(previous / name) == sha(player / name) == result['previous_programs'][name]
        assert (player / name).stat().st_uid == 1000
    assert len(list(assets.iterdir())) == len(result['asset_hashes']) == 391
    for name, expected in result['asset_hashes'].items():
        assert Path(name).name == name and sha(assets / name) == expected
        assert (assets / name).stat().st_uid == 1000 and not (assets / name).is_symlink()
    target.mkdir()
    for name in result['asset_hashes']:
        os.link(assets / name, target / name)
    staged = {}
    try:
        for name in programs:
            temp = player / ('.map51-promote-' + name + '.tmp')
            assert not temp.exists()
            os.link(build / name, temp)
            staged[name] = temp
        metadata = {n: (build / n).read_bytes() for n in ['build-inputs.sha256', 'build-source-checks.log', 'build-go-version.txt', 'runtime.json']}
        metadata['build-outputs.sha256'] = ''.join(f'{expected}  /out/{name}\n' for name, expected in programs.items()).encode()
        for name, data in metadata.items():
            assert (player / name).stat().st_uid == 1000
            temp = player / ('.map51-promote-' + name + '.tmp')
            assert not temp.exists()
            with temp.open('xb') as f:
                f.write(data)
            staged[name] = temp
        for name, temp in staged.items():
            os.replace(temp, player / name)
    finally:
        for temp in staged.values():
            if temp.exists():
                temp.unlink()
    for name, expected in programs.items():
        assert sha(player / name) == expected and sha(previous / name) == result['previous_programs'][name]
    write(a.out, dict(schema=1, status='promoted-scoped-045-map51', assets=target.name, files=391, preserved_files=387,
                      build=build.name, previous=previous.name, programs=programs, previous_programs=result['previous_programs'],
                      audit_sha256=sha(a.audit), tool_sha256=sha(Path(__file__))))
    print(json.dumps(dict(status='promoted-scoped-045-map51', files=391, assets=target.name)))


def overview(a):
    result, promotion = read(a.audit), read(a.promotion)
    assert result['status'] == 'PASS-scoped-045-map51' and promotion['audit_sha256'] == sha(a.audit)
    assert promotion['status'] == 'promoted-scoped-045-map51'
    caches = read(a.research / 'map51-caches-r2/caches.json')
    assert sha(a.research / 'map51-caches-r2/caches.json') == result['caches_sha256']
    raw = (a.project / 'workplace/intake-20261023/sources/game/8sword/PMAP.AY').read_bytes()
    assert digest(raw) == '9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02'
    planar = module(a.project / 'tools/catalog-all-graphics.py', 'planar')
    font = ImageFont.truetype(str(a.project / 'workplace/probe-20261023/graphics-first/font-settings-r1/NotoSansCJK-Black.ttc'), 18, index=3)
    sheet = Image.new('RGB', (2040, 2450), '#172b2d')
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 8), '主地圖65筆：每格左原版／右HD；素材快取總覽，非自然實景對拍', font=font, fill='#f1d69b')
    for row in caches:
        i = row['index']
        x, y = (i % 5)*408+8, (i//5)*184+52
        original = planar.planar(raw[i*1004:(i+1)*1004], (0, 8, 25, 5)).convert('RGB').resize((192, 150), Image.Resampling.NEAREST)
        path = a.research / 'map51-caches-r2' / row['file']
        assert sha(path) == row['cache_sha256']
        hd = Image.frombytes('RGBA', (192, 150), path.read_bytes())
        sheet.paste(original, (x, y+24))
        sheet.paste(hd.convert('RGB'), (x+200, y+24))
        draw.text((x, y), f'PMAP {i:02d}   原版 / HD', font=font, fill='#f1d69b')
    target = a.out / 'world-map-original-hd-r1.png'
    assert not target.exists() and a.out.stat().st_uid == 1000
    sheet.save(target)
    write(target.with_suffix('.json'), dict(schema=1, spec='045', status='65-runtime-material-caches-not-natural-screenshots',
          image=target.name, image_sha256=sha(target), count=65, source='PMAP.AY', source_sha256=digest(raw),
          caches=caches, audit_sha256=sha(a.audit), promotion_sha256=sha(a.promotion), tool_sha256=sha(Path(__file__)),
          rights='user-requested compact comparison in existing private repository only; full assets stay local'))
    print(json.dumps(dict(image=target.name, count=65, bytes=target.stat().st_size)))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('audit', 'promote', 'overview'))
    for key in ('project', 'research', 'player', 'audit', 'promotion'):
        p.add_argument('--' + key, type=Path)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    {'audit': audit, 'promote': promote, 'overview': overview}[a.action](a)


if __name__ == '__main__':
    main()
