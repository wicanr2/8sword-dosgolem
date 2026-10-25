#!/usr/bin/env python3
"""049：獨立核對十四筆來源、快取、完整受控Frame與固定建置；Docker only。"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re

from PIL import Image, __version__


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(path):
    return sha(path.read_bytes())


def read(path):
    return json.loads(path.read_text())


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('project', 'assets', 'registration', 'controlled', 'build', 'out'):
        p.add_argument('--' + key, type=Path, required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    battle = a.project / 'workplace/probe-20261023/graphics-first/battle-r1'
    native = module(a.project / 'tools/catalog-encounter.py', 'native')
    sampler = module(a.project / 'tools/audit-encounter-gui.py', 'sampler')
    source = (a.project / 'workplace/intake-20261023/sources/game/8sword/ENEMY.AY').read_bytes()
    assert sha(source) == '0d18b068e177b54f7b8a2b30072e9ae3ebc984fbed9fd6a8706f71d3140a5ffd'
    assert digest(a.registration / 'registration.json') == '77dfef9139811bb22de5ed9e1790da3d8789d5b8913e9392fae61bc6f51c34d3'
    reg = read(a.registration / 'registration.json')
    assert len(reg['groups']) == 14 and len(reg['base_files']) == 344
    assert len(list(a.assets.iterdir())) == 367
    for name, expected in reg['base_files'].items():
        assert digest(a.assets / name) == digest(a.project / 'workplace/player/assets-painted-r49' / name) == expected
    text = (a.build / 'src/internal/eightsword/map_encounter_batch.go').read_text()
    pins = re.findall(r'"([a-f0-9]{64})"', text.split('type encounterBatchAlias')[0])
    assert len(pins) == 14
    frequency = Counter()
    for i in range(14):
        raw = source[i * 1204:(i + 1) * 1204]
        for record in [raw, native.mirror(raw)]:
            for h in range(1, 26, 2):
                prefix = native.prefix(record, h)
                frequency[sha(prefix[:4 + 32 * h])] += 1
    cache, seen = {}, set()
    for i, group in enumerate(reg['groups']):
        assert group['record'] == i and digest(a.assets / group['manifest']) == pins[i] == group['manifest_sha256']
        m = read(a.assets / group['manifest'])
        assert m == group['config']
        entry = m['image']
        assert digest(a.assets / entry['file']) == entry['sha256']
        assert digest(a.assets / m['prompt_file']) == m['prompt_sha256']
        target = m['target_rect']
        sampled = sampler.sample(a.assets / entry['file'], target[2], target[3], actor=True, rect=entry['source_rect'])
        full = bytearray(192 * 150 * 4)
        for y in range(target[3]):
            at = ((target[1] + y) * 192 + target[0]) * 4
            full[at:at + target[2] * 4] = sampled[y * target[2] * 4:(y + 1) * target[2] * 4]
        def flip(data):
            return b''.join(data[(y * 192 + x) * 4:(y * 192 + x + 1) * 4] for y in range(150) for x in range(191, -1, -1))
        normal = flip(full) if m['sampled_mirrored'] else bytes(full)
        for direction, data in enumerate([normal, flip(normal)]):
            assert sha(data) == m['cache_sha256'][direction]
            assert data == (a.registration / f'encounter-{i:02d}-{direction}.rgba').read_bytes()
            cache[i, direction] = data
        raw = source[i * 1204:(i + 1) * 1204]
        for alias in m['aliases']:
            direction, height = alias['direction'], alias['height']
            prefix = native.prefix(native.mirror(raw) if direction else raw, height)
            key = sha(prefix[:4 + 32 * height])
            assert frequency[key] == 1 and key not in seen and alias['native_sha256'] == key
            assert sha(prefix) == alias['record_sha256']
            assert sha(cache[i, direction][:height * 6 * 192 * 4]) == alias['cache_sha256']
            seen.add(key)
    assert len(seen) == 321
    log = (battle / 'encounters-tests-r2.log').read_text()
    for name in ['RealSourcesAndCaches', 'FailureAtomic', 'ControlledSourceDraw']:
        assert '--- PASS: TestEncounterBatch' + name in log
    assert '\nPASS\n' in log and '--- SKIP:' not in log and '\nFAIL' not in log
    inputs = {}
    for line in (a.build / 'build-inputs.sha256').read_text().splitlines():
        expected, name = line.split(None, 1)
        name = name.removeprefix('/project/')
        assert digest(a.build / 'src' / name) == digest(a.project / name) == expected
        inputs[name] = expected
    assert len(inputs) == 131
    previous = a.project / 'workplace/player/source-candidate-r4'
    old_inputs = {}
    for line in (previous / 'build-inputs.sha256').read_text().splitlines():
        expected, name = line.split(None, 1)
        name = name.removeprefix('/project/')
        assert digest(previous / 'src' / name) == expected
        old_inputs[name] = expected
    changed = sorted(n for n, expected in old_inputs.items() if inputs.get(n) != expected)
    assert changed == ['internal/eightsword/engine.go']
    assert set(inputs) - set(old_inputs) == {'internal/eightsword/map_encounter_batch.go', 'internal/eightsword/map_encounter_batch_test.go'}
    programs = {}
    for line in (a.build / 'build-outputs.sha256').read_text().splitlines():
        expected, name = line.split(None, 1)
        name = Path(name).name
        assert digest(a.build / name) == expected
        programs[name] = expected
    assert len(programs) == 7
    old_programs = read(battle / 'source-promotion-r1.json')['programs']
    for name, expected in old_programs.items():
        assert digest(previous / name) == digest(a.project / 'workplace/player' / name) == expected
    controlled = read(a.controlled / 'receipt.json')
    assert controlled['status'] == 'PASS-controlled-source-render-not-natural-encounter'
    assert controlled['source_renderer'] and controlled['source_direct_calls'] > 0
    assert controlled['old_overlay_compositions'] == 0 and not controlled['gameplay_changed']
    assert controlled['controlled_memory']['restored_and_verified']
    assert len(controlled['controlled_memory']['original_values']) == 2
    bg = read(a.assets / 'battle-background.json')['image']
    assert digest(a.assets / bg['file']) == bg['sha256']
    background = sampler.sample(a.assets / bg['file'], 1920, 1200)
    cases = controlled['cases']
    assert {(r['record'], r['direction'], r['height']) for r in cases} == {(i, d, h) for i in (5, 8, 9) for d in (0, 1) for h in (13, 25)}
    assert len(cases) == 12
    for row in cases:
        assert row['frame_pure'] and row['paired_guest_equal'] and row['pixels'] == 2304000
        expected = bytearray(background)
        tile, height = cache[row['record'], row['direction']], row['height']
        for y in range(height * 6):
            for x in range(192):
                src = (y * 192 + x) * 4
                at = (((112 - height) * 6 + y) * 1920 + 480 + x) * 4
                alpha = tile[src + 3]
                for c in range(3):
                    expected[at + c] = min(255, tile[src + c] + (expected[at + c] * (255 - alpha) + 127) // 255)
        im = Image.open(a.controlled / row['png']).convert('RGBA')
        assert im.size == (1920, 1200) and im.tobytes() == bytes(expected)
        assert sha(expected) == row['frame_sha256']
    # This prior GUI/save evidence stays explicitly separate from this RAM fixture.
    prior = battle / 'source-player-audit-r3.json'
    assert digest(prior) == 'c7bab70fc8c6d2b58c5f8d13fab5fb2d96892a21ec9a05e5df8787cc72c7cd50'
    assert read(prior)['status'] == 'PASS-scoped-047-production-source-renderer'
    report = dict(schema=1, spec='049', status='PASS-scoped-049-map-encounter-batch', production=False,
                  records=14, directions=28, new_aliases=321, preserved_legacy_aliases=21, ambiguous_prefixes=22,
                  candidate_files=367, preserved_files=344, build_inputs=131, programs=programs, previous_programs=old_programs,
                  source_changed=changed, source_added=sorted(set(inputs) - set(old_inputs)),
                  build_inputs_sha256=digest(a.build / 'build-inputs.sha256'), registration_sha256=digest(a.registration / 'registration.json'),
                  controlled_sha256=digest(a.controlled / 'receipt.json'), controlled_cases=12, controlled_pixels=27648000,
                  old_overlay_compositions=0, memory_restored=True, tests_sha256=digest(battle / 'encounters-tests-r2.log'),
                  prior_gui_save_evidence_sha256=digest(prior), prior_gui_reused=True, no_new_per_creature_gui_gate=True,
                  asset_hashes={f.name: digest(f) for f in sorted(a.assets.iterdir())},
                  tool_sha256=digest(Path(__file__)), pillow=__version__,
                  limits=['Controlled RAM draw, not a natural encounter or rule/RNG parity claim.',
                          'Prior normal GUI and save evidence remains scoped to 047/048; no new GUI/save claim.',
                          'MAN visual correspondences are strong inference; official unit names unknown.',
                          'No full-game HD completion claim; original-derived assets stay local.'])
    with a.out.open('x') as f:
        f.write(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ['status', 'records', 'new_aliases', 'candidate_files', 'controlled_cases', 'controlled_pixels']}))


if __name__ == '__main__':
    main()
