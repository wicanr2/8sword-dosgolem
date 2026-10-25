#!/usr/bin/env python3
"""050：獨立核對、明示本機提升或保存縮小README總覽。Docker only。"""
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
    p, b = a.project, a.battle
    assets = p / 'workplace/player/assets-battle-backgrounds-candidate-r1'
    build = p / 'workplace/player/source-candidate-backgrounds-r1'
    previous = p / 'workplace/player/source-candidate-encounters-r1'
    regdir, controlled, batch = b / 'battle-backgrounds-registration-r1', b / 'battle-backgrounds-controlled-r1', b / 'battle-backgrounds-batch-r1'
    reg = read(regdir / 'registration.json')
    assert sha(regdir / 'registration.json') == '5d6e86061e30a01c32bfdda8538a1f4ee9ce38aa5e1e67ebba2fe5734c6a80c8'
    assert len(reg['base_files']) == 367 and len(list(assets.iterdir())) == 377
    for name, expected in reg['base_files'].items():
        assert sha(assets / name) == sha(p / 'workplace/player/assets-painted-r50' / name) == expected
    pins = re.findall(r'\{"(GRO0[345]\.EG)", "([a-f0-9]{64})", "([a-f0-9]{64})", "([a-f0-9]{64})"\}',
                      (build / 'src/internal/eightsword/battle_background_batch.go').read_text())
    assert len(pins) == len(reg['groups']) == 3
    sampler = module(p / 'tools/audit-encounter-gui.py', 'sampler')
    decoder = module(p / 'tools/prepare-hd-intro.py', 'decoder')
    caches = {}
    for group, pin in zip(reg['groups'], pins):
        i, m = group['number'], group['config']
        assert (m['source_file'], m['source_sha256'], m['native_sha256'], group['manifest_sha256']) == pin
        assert read(assets / group['manifest']) == m and sha(assets / group['manifest']) == pin[3]
        packed = (p / 'workplace/intake-20261023/sources/game/8sword' / m['source_file']).read_bytes()
        assert digest(packed) == pin[1]
        native = decoder.decode(packed)
        assert len(native) == 64004 and digest(native) == pin[2]
        assert native == (regdir / f'gro{i:02d}-native.bin').read_bytes()
        image = m['image']
        assert image['source_index'] == 840 + i
        assert sha(assets / image['file']) == sha(batch / image['file']) == image['sha256']
        assert sha(assets / m['prompt_file']) == sha(batch / m['prompt_file']) == m['prompt_sha256']
        receipt = batch / Path(image['file']).with_suffix('.json')
        assert sha(receipt) == group['generation_receipt_sha256']
        r = read(receipt)
        assert r['tool'] == 'built-in image_gen' and r['image_sha256'] == image['sha256'] and r['alpha_extrema'] == [255, 255]
        assert sha(batch / r['reference']) == r['reference_sha256']
        assert sha(p / r['style_reference']) == r['style_sha256']
        caches[m['source_file']] = sampler.sample(assets / image['file'], 1920, 1200)
        assert digest(caches[m['source_file']]) == sha(regdir / f'gro{i:02d}-background.rgba') == m['cache_sha256']
    log = (b / 'battle-backgrounds-tests-r1.log').read_text()
    for name in ['RealSourcesAndCaches', 'FailureAtomic', 'OwnershipQualification', 'ControlledSourceDraw']:
        assert '--- PASS: TestBackgroundBatch' + name in log
    assert '--- PASS: TestBattleBackgroundOwnershipRejectsMixedPages' in log
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
    assert len(source) == 133 and len(old) == 131
    changed = sorted(n for n, expected in old.items() if source.get(n) != expected)
    assert changed == ['internal/eightsword/battle_palace_background.go', 'internal/eightsword/battle_transactions.go', 'internal/eightsword/engine.go']
    assert set(source) - set(old) == {'internal/eightsword/battle_background_batch.go', 'internal/eightsword/battle_background_batch_test.go'}
    programs = {}
    for line in (build / 'build-outputs.sha256').read_text().splitlines():
        expected, name = line.split(None, 1)
        name = Path(name).name
        assert sha(build / name) == expected
        programs[name] = expected
    assert len(programs) == 7
    old_programs = read(b / 'encounters-promotion-r1.json')['programs']
    for name, expected in old_programs.items():
        assert sha(previous / name) == sha(p / 'workplace/player' / name) == expected
    receipt = read(controlled / 'receipt.json')
    assert receipt['status'] == 'PASS-controlled-background-source-render-not-natural-combat'
    assert receipt['source_renderer'] and receipt['source_direct_calls'] > 0 and receipt['old_overlay_compositions'] == 0
    assert receipt['controlled_memory']['restored_and_verified'] and len(receipt['controlled_memory']['original_values']) == 2
    assert not receipt['gameplay_changed']
    actor = (regdir / 'man02-0.rgba').read_bytes()
    m = read(assets / 'troop-man02.json')
    assert digest(actor) == m['frames'][0]['cache_sha256'][0]
    rows = receipt['cases']
    assert len(rows) == 9 and {(r['source'], r['stage']) for r in rows} == {(f'GRO{i:02d}.EG', s) for i in (3, 4, 5) for s in ('background', 'actor', 'restored')}
    for row in rows:
        assert row['pixels'] == 2304000 and row['frame_pure'] and row['paired_guest_equal']
        expected = bytearray(caches[row['source']])
        if row['stage'] == 'actor':
            for y in range(300):
                for x in range(264):
                    src = (y * 264 + x) * 4
                    at = ((360 + y) * 1920 + 480 + x) * 4
                    alpha = actor[src + 3]
                    for c in range(3):
                        expected[at + c] = min(255, actor[src + c] + (expected[at + c] * (255 - alpha) + 127) // 255)
        im = Image.open(controlled / row['png']).convert('RGBA')
        assert im.size == (1920, 1200) and im.tobytes() == bytes(expected) and digest(expected) == row['frame_sha256']
    prior = b / 'source-player-audit-r3.json'
    assert sha(prior) == 'c7bab70fc8c6d2b58c5f8d13fab5fb2d96892a21ec9a05e5df8787cc72c7cd50'
    result = dict(schema=1, spec='050', status='PASS-scoped-050-battle-background-batch', production=False,
                  new_backgrounds=3, registered_color_backgrounds=5, candidate_files=377, preserved_files=367,
                  build_inputs=133, programs=programs, previous_programs=old_programs, changed_inputs=changed,
                  build_inputs_sha256=sha(build / 'build-inputs.sha256'), registration_sha256=sha(regdir / 'registration.json'),
                  controlled_sha256=sha(controlled / 'receipt.json'), controlled_cases=9, controlled_pixels=20736000,
                  source_direct_calls=receipt['source_direct_calls'], old_overlay_compositions=0, memory_restored=True,
                  tests_sha256=sha(b / 'battle-backgrounds-tests-r1.log'), prior_gui_save_sha256=sha(prior), prior_gui_reused=True,
                  asset_hashes={f.name: sha(f) for f in sorted(assets.iterdir())}, tool_sha256=sha(Path(__file__)), pillow=__version__,
                  limits=['Controlled presentation, not natural combat, terrain selection, rule or RNG parity.',
                          'Original H monochrome variants stay separate; no new display-mode claim.',
                          'No new GUI/save or whole-game HD claim; full art and original data stay local.'])
    write(a.out, result)
    print(json.dumps({k: result[k] for k in ['status', 'new_backgrounds', 'candidate_files', 'controlled_cases', 'controlled_pixels']}))


def promote(a):
    player = a.player
    result = read(a.audit)
    assert result['status'] == 'PASS-scoped-050-battle-background-batch'
    build, previous = player / 'source-candidate-backgrounds-r1', player / 'source-candidate-encounters-r1'
    assets, target = player / 'assets-battle-backgrounds-candidate-r1', player / 'assets-painted-r51'
    assert player.stat().st_uid == 1000 and not target.exists() and not a.out.exists()
    assert sha(build / 'build-inputs.sha256') == result['build_inputs_sha256']
    programs = result['programs']
    assert set(programs) == {'8sword', '8sword-replay', 'gui-check', 'music-check', 'heroine-check', 'museum-check', 'story-prelude-check'}
    for name, expected in programs.items():
        assert sha(build / name) == expected and (build / name).stat().st_uid == 1000
        assert sha(previous / name) == sha(player / name) == result['previous_programs'][name]
    assert len(list(assets.iterdir())) == len(result['asset_hashes']) == 377
    for name, expected in result['asset_hashes'].items():
        assert Path(name).name == name and sha(assets / name) == expected
        assert (assets / name).stat().st_uid == 1000 and not (assets / name).is_symlink()
    staging = player / '.backgrounds-assets-r51.tmp'
    assert not staging.exists()
    staging.mkdir()
    for name in result['asset_hashes']:
        os.link(assets / name, staging / name)
    os.rename(staging, target)
    staged = {}
    try:
        for name in programs:
            temp = player / ('.backgrounds-promote-' + name + '.tmp')
            assert not temp.exists()
            os.link(build / name, temp)
            staged[name] = temp
        metadata = {n: (build / n).read_bytes() for n in ['build-inputs.sha256', 'build-source-checks.log', 'build-go-version.txt', 'runtime.json']}
        metadata['build-outputs.sha256'] = ''.join(f'{expected}  /out/{name}\n' for name, expected in programs.items()).encode()
        for name, data in metadata.items():
            temp = player / ('.backgrounds-promote-' + name + '.tmp')
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
    write(a.out, dict(schema=1, status='promoted-scoped-050-battle-backgrounds', assets=target.name,
                      files=377, preserved_files=367, build=build.name, previous=previous.name, programs=programs,
                      previous_programs=result['previous_programs'], audit_sha256=sha(a.audit), tool_sha256=sha(Path(__file__))))
    print(json.dumps(dict(status='promoted-scoped-050-battle-backgrounds', files=377, assets=target.name)))


def overview(a):
    result, promotion = read(a.audit), read(a.promotion)
    assert result['status'] == 'PASS-scoped-050-battle-background-batch' and promotion['audit_sha256'] == sha(a.audit)
    assert promotion['status'] == 'promoted-scoped-050-battle-backgrounds'
    regdir = a.battle / 'battle-backgrounds-registration-r1'
    reg = read(regdir / 'registration.json')
    assert sha(regdir / 'registration.json') == result['registration_sha256']
    assert sha(regdir / 'comparison.png') == reg['comparison_sha256']
    target = a.out / 'battle-backgrounds-original-hd-r1.png'
    assert not target.exists() and a.out.stat().st_uid == 1000
    with target.open('xb') as f:
        f.write((regdir / 'comparison.png').read_bytes())
    write(target.with_suffix('.json'), dict(schema=1, spec='050', status='registered-asset-overview-not-natural-combat-screenshots',
          image=target.name, image_sha256=sha(target), registered_color_backgrounds=5,
          groups=[dict(number=g['number'], manifest_sha256=g['manifest_sha256'], config=g['config']) for g in reg['groups']],
          existing_backgrounds=['GRO01.EG', 'GRO02.EG'], registration_sha256=sha(regdir / 'registration.json'),
          audit_sha256=sha(a.audit), promotion_sha256=sha(a.promotion), tool_sha256=sha(Path(__file__)),
          rights='user-requested compact comparison in existing private repository only; full assets stay local'))
    print(json.dumps(dict(image=target.name, backgrounds=5, bytes=target.stat().st_size)))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('audit', 'promote', 'overview'))
    for key in ('project', 'battle', 'player', 'audit', 'promotion'):
        p.add_argument('--' + key, type=Path)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    {'audit': audit, 'promote': promote, 'overview': overview}[a.action](a)


if __name__ == '__main__':
    main()
