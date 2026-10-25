#!/usr/bin/env python3
"""051：獨立核對三建築、提升本機r52或保存縮小六份來源總覽。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re

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
        f.write(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def audit(a):
    p, r = a.project, a.research
    player = p / 'workplace/player'
    assets, build, previous = player / 'assets-buildings-candidate-r1', player / 'source-candidate-buildings-r1', player / 'source-candidate-backgrounds-r1'
    regdir, controlled, batch = r / 'buildings-registration-r1', r / 'buildings-controlled-r1', r / 'buildings-hd-batch-r1'
    reg = read(regdir / 'registration.json')
    assert sha(regdir / 'registration.json') == '626a02c7ff83c2bf858d047306e27763ef95aa4202a3eed44fb70c6e0a6f97ce'
    assert len(reg['base_files']) == 377 and len(list(assets.iterdir())) == 387 and reg['deferred'] == [4, 6]
    for name, expected in reg['base_files'].items():
        assert sha(assets / name) == sha(player / 'assets-painted-r51' / name) == expected
    pins = re.findall(r'\{([135]), (847|848|850), "([a-f0-9]{64})", "([a-f0-9]{64})", "([a-f0-9]{64})"\}',
                      (build / 'src/internal/eightsword/buildings.go').read_text())
    assert len(pins) == len(reg['groups']) == 3
    sampler = module(p / 'tools/audit-encounter-gui.py', 'sampler')
    decoder = module(p / 'tools/prepare-hd-intro.py', 'decoder')
    caches = {}
    for group, pin in zip(reg['groups'], pins):
        i, m = group['number'], group['config']
        assert (str(i), str(group['material_id']), m['source_sha256'], m['native_sha256'], group['manifest_sha256']) == pin
        assert read(assets / group['manifest']) == m and sha(assets / group['manifest']) == pin[4]
        packed = (p / 'workplace/intake-20261023/sources/game/8sword' / m['source_file']).read_bytes()
        assert digest(packed) == pin[2]
        native = decoder.decode(packed)
        assert len(native) == 22404 and digest(native) == pin[3] and native == (regdir / f'live{i}-native.bin').read_bytes()
        image = m['image']
        assert image['source_index'] == group['material_id'] - 1
        assert sha(assets / image['file']) == sha(batch / image['file']) == image['sha256']
        assert sha(assets / m['prompt_file']) == sha(batch / m['prompt_file']) == m['prompt_sha256']
        receipt = batch / Path(image['file']).with_suffix('.json')
        assert sha(receipt) == group['generation_receipt_sha256']
        generation = read(receipt)
        assert generation['tool'] == 'built-in image_gen' and generation['image_sha256'] == image['sha256'] and generation['alpha_extrema'] == [255, 255]
        assert sha(batch / generation['reference']) == generation['reference_sha256']
        assert sha(p / generation['style_reference']) == generation['style_sha256']
        caches[m['source_file']] = sampler.sample(assets / image['file'], 1344, 600)
        assert digest(caches[m['source_file']]) == sha(regdir / f'live{i}-building.rgba') == m['cache_sha256']
    assert not (assets / 'building-live4.json').exists() and not (assets / 'building-live6.json').exists()
    log = (r / 'buildings-tests-r1.log').read_text()
    for name in ['RealSourcesAndCaches', 'FailureAtomic', 'ControlledSourceDraw']:
        assert '--- PASS: TestBuildings' + name in log
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
    source, old = inputs(build, True), inputs(previous, False)
    assert len(source) == 135 and len(old) == 133
    assert [n for n, expected in old.items() if source.get(n) != expected] == ['internal/eightsword/engine.go']
    assert set(source) - set(old) == {'internal/eightsword/buildings.go', 'internal/eightsword/buildings_test.go'}
    programs = {}
    for line in (build / 'build-outputs.sha256').read_text().splitlines():
        expected, name = line.split(None, 1)
        name = Path(name).name
        assert sha(build / name) == expected
        programs[name] = expected
    assert len(programs) == 7
    history = p / 'workplace/probe-20261023/graphics-first/battle-r1'
    old_programs = read(history / 'battle-backgrounds-promotion-r1.json')['programs']
    for name, expected in old_programs.items():
        assert sha(previous / name) == sha(player / name) == expected
    receipt = read(controlled / 'receipt.json')
    assert receipt['status'] == 'PASS-controlled-building-source-render-not-natural-recruitment'
    assert receipt['source_renderer'] and receipt['source_direct_calls'] > 0 and receipt['old_overlay_compositions'] == 0
    assert receipt['controlled_memory']['restored_and_verified'] and len(receipt['controlled_memory']['original_values']) == 2
    assert not receipt['gameplay_changed']
    bg = read(assets / 'battle-background.json')['image']
    assert sha(assets / bg['file']) == bg['sha256']
    background = sampler.sample(assets / bg['file'], 1920, 1200)
    rows = receipt['cases']
    assert len(rows) == 6 and {(row['source'], row['stage']) for row in rows} == {(f'LIVE{i}.AY', s) for i in (1, 3, 5) for s in ('building', 'restored')}
    for row in rows:
        assert row['pixels'] == 2304000 and row['frame_pure'] and row['paired_guest_equal'] and row['rect'] == [24, 72, 1344, 600]
        expected = bytearray(background)
        if row['stage'] == 'building':
            cache = caches[row['source']]
            for y in range(600):
                at = ((72 + y) * 1920 + 24) * 4
                expected[at:at + 1344 * 4] = cache[y * 1344 * 4:(y + 1) * 1344 * 4]
        im = Image.open(controlled / row['png']).convert('RGBA')
        assert im.size == (1920, 1200) and im.tobytes() == bytes(expected) and digest(expected) == row['frame_sha256']
    prior = history / 'source-player-audit-r3.json'
    assert sha(prior) == 'c7bab70fc8c6d2b58c5f8d13fab5fb2d96892a21ec9a05e5df8787cc72c7cd50'
    result = dict(schema=1, spec='051', status='PASS-scoped-051-building-batch', production=False,
                  new_buildings=3, registered_buildings=4, deferred=[4, 6], candidate_files=387, preserved_files=377,
                  build_inputs=135, programs=programs, previous_programs=old_programs,
                  build_inputs_sha256=sha(build / 'build-inputs.sha256'), registration_sha256=sha(regdir / 'registration.json'),
                  controlled_sha256=sha(controlled / 'receipt.json'), controlled_cases=6, controlled_pixels=13824000,
                  source_direct_calls=receipt['source_direct_calls'], old_overlay_compositions=0, memory_restored=True,
                  tests_sha256=sha(r / 'buildings-tests-r1.log'), prior_gui_save_sha256=sha(prior), prior_gui_reused=True,
                  asset_hashes={f.name: sha(f) for f in sorted(assets.iterdir())}, tool_sha256=sha(Path(__file__)), pillow=__version__,
                  limits=['Controlled presentation, not natural recruitment or rule/RNG parity.',
                          'LIVE4 inscription unknown and LIVE6 existing art decision pending; both stay native.',
                          'No new GUI/save or whole-game HD claim; full art and original data stay local.'])
    write(a.out, result)
    print(json.dumps({k: result[k] for k in ['status', 'new_buildings', 'candidate_files', 'controlled_cases', 'controlled_pixels']}))


def promote(a):
    player, result = a.player, read(a.audit)
    assert result['status'] == 'PASS-scoped-051-building-batch' and result['deferred'] == [4, 6]
    build, previous = player / 'source-candidate-buildings-r1', player / 'source-candidate-backgrounds-r1'
    assets, target = player / 'assets-buildings-candidate-r1', player / 'assets-painted-r52'
    assert player.stat().st_uid == 1000 and not target.exists() and not a.out.exists()
    assert sha(build / 'build-inputs.sha256') == result['build_inputs_sha256']
    programs = result['programs']
    assert set(programs) == {'8sword', '8sword-replay', 'gui-check', 'music-check', 'heroine-check', 'museum-check', 'story-prelude-check'}
    for name, expected in programs.items():
        assert sha(build / name) == expected and (build / name).stat().st_uid == 1000
        assert sha(previous / name) == sha(player / name) == result['previous_programs'][name]
        assert (player / name).stat().st_uid == 1000
    assert len(list(assets.iterdir())) == len(result['asset_hashes']) == 387
    for name, expected in result['asset_hashes'].items():
        assert Path(name).name == name and sha(assets / name) == expected
        assert (assets / name).stat().st_uid == 1000 and not (assets / name).is_symlink()
    staging = player / '.buildings-assets-r52.tmp'
    assert not staging.exists()
    staging.mkdir()
    for name in result['asset_hashes']:
        os.link(assets / name, staging / name)
    os.rename(staging, target)
    staged = {}
    try:
        for name in programs:
            temp = player / ('.buildings-promote-' + name + '.tmp')
            assert not temp.exists()
            os.link(build / name, temp)
            staged[name] = temp
        metadata = {n: (build / n).read_bytes() for n in ['build-inputs.sha256', 'build-source-checks.log', 'build-go-version.txt', 'runtime.json']}
        metadata['build-outputs.sha256'] = ''.join(f'{expected}  /out/{name}\n' for name, expected in programs.items()).encode()
        for name, data in metadata.items():
            assert (player / name).stat().st_uid == 1000
            temp = player / ('.buildings-promote-' + name + '.tmp')
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
    write(a.out, dict(schema=1, status='promoted-scoped-051-buildings', assets=target.name, files=387, preserved_files=377,
                      build=build.name, previous=previous.name, programs=programs, previous_programs=result['previous_programs'],
                      deferred=[4, 6], audit_sha256=sha(a.audit), tool_sha256=sha(Path(__file__))))
    print(json.dumps(dict(status='promoted-scoped-051-buildings', files=387, assets=target.name)))


def overview(a):
    result, promotion = read(a.audit), read(a.promotion)
    assert result['status'] == 'PASS-scoped-051-building-batch' and promotion['audit_sha256'] == sha(a.audit)
    assert promotion['status'] == 'promoted-scoped-051-buildings' and promotion['deferred'] == [4, 6]
    regdir = a.research / 'buildings-registration-r1'
    reg = read(regdir / 'registration.json')
    assert sha(regdir / 'registration.json') == result['registration_sha256']
    assert sha(regdir / 'comparison.png') == reg['comparison_sha256']
    target = a.out / 'buildings-original-hd-r1.png'
    assert not target.exists() and a.out.stat().st_uid == 1000
    with target.open('xb') as f:
        f.write((regdir / 'comparison.png').read_bytes())
    write(target.with_suffix('.json'), dict(schema=1, spec='051', status='registered-asset-overview-not-natural-recruitment-screenshots',
          image=target.name, image_sha256=sha(target), registered_buildings=4, deferred=[4, 6],
          groups=[dict(number=g['number'], material_id=g['material_id'], manifest_sha256=g['manifest_sha256'], config=g['config']) for g in reg['groups']],
          existing_buildings=['LIVE2.AY'], registration_sha256=sha(regdir / 'registration.json'),
          audit_sha256=sha(a.audit), promotion_sha256=sha(a.promotion), tool_sha256=sha(Path(__file__)),
          rights='user-requested compact comparison in existing private repository only; full assets stay local'))
    print(json.dumps(dict(image=target.name, registered_buildings=4, bytes=target.stat().st_size)))


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
