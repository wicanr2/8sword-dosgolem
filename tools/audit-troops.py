#!/usr/bin/env python3
"""048：核對批次來源、正式載入快取、受控原版繪圖及正常存退讀。Docker only。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re

from PIL import Image


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def verify_manifest(path, root):
    rows = path.read_text().splitlines()
    for line in rows:
        digest, name = line.split(None, 1)
        assert sha(root / name) == digest, name
    return len(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('project', 'assets', 'registration', 'controlled', 'build', 'gui', 'out'):
        ap.add_argument('--' + name, type=Path, required=True)
    a = ap.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    original = a.project / 'workplace/intake-20261023/sources/game/8sword'
    base = a.project / 'workplace/player/assets-painted-r48'
    battle = a.project / 'workplace/probe-20261023/graphics-first/battle-r1'
    batch = battle / 'troops-hd-bulk-r1'
    assert sha(a.registration / 'registration.json') == '5a3476243b2e709a8915d262e95829e19a52f37599a027b0b32b8757e3bca18c'
    reg = read(a.registration / 'registration.json')
    assert len(reg['base_files']) == 223 and len(reg['groups']) == 20
    assert len(list(a.assets.iterdir())) == 344
    for name, digest in reg['base_files'].items():
        assert sha(base / name) == sha(a.assets / name) == digest
    table = re.findall(r'\{"(MAN\d\d\.EGG)", "([0-9a-f]{64})", "([0-9a-f]{64})"\}',
                       (a.build / 'src/internal/eightsword/troops.go').read_text())
    assert len(table) == 20
    seen_native, seen_record, count = set(), set(), 0
    for gi, group in enumerate(reg['groups']):
        assert tuple(table[gi]) == (group['resource'], group['source_sha256'], group['manifest_sha256'])
        assert sha(original / group['resource']) == group['source_sha256']
        assert sha(a.assets / group['manifest']) == group['manifest_sha256']
        m = read(a.assets / group['manifest'])
        assert m['frames'] == group['frames'] and len(m['frames']) == 4
        assert sha(batch / group['atlas']) == group['atlas_sha256']
        assert sha(a.assets / group['prompt_file']) == group['prompt_sha256']
        receipt_path = batch / (Path(group['atlas']).stem + '.json')
        assert sha(receipt_path) == group['receipt_sha256']
        receipt = read(receipt_path)
        atlas = Image.open(batch / group['atlas']).convert('RGBA')
        source = (original / group['resource']).read_bytes()
        for ri, frame in enumerate(group['frames']):
            entry = frame['image']
            assert entry['source_index'] == 159 + gi * 16 + ri * 4
            assert sha(a.assets / entry['file']) == entry['sha256']
            image = Image.open(a.assets / entry['file']).convert('RGBA')
            assert image.tobytes() == atlas.crop(receipt['poses'][ri]['quadrant']).tobytes()
            record = source[ri * 3304:(ri + 1) * 3304]
            assert hashlib.sha256(record).hexdigest() == frame['record_sha256'][0]
            for di in range(2):
                assert frame['native_sha256'][di] not in seen_native
                assert frame['record_sha256'][di] not in seen_record
                seen_native.add(frame['native_sha256'][di]); seen_record.add(frame['record_sha256'][di])
                expected = a.registration / f'troop-man{group["resource"][3:5]}-{ri}-{di}.rgba'
                assert sha(expected) == frame['cache_sha256'][di]
                assert expected.stat().st_size == 264 * 300 * 4
            count += 1
    assert count == 80 and len(seen_native) == len(seen_record) == 160
    inputs = verify_manifest(a.build / 'build-inputs.sha256', a.build / 'src')
    programs = verify_manifest(a.build / 'build-outputs.sha256', a.build)
    assert inputs == 113 and programs == 7
    for line in (a.build / 'build-inputs.sha256').read_text().splitlines():
        digest, name = line.split(None, 1)
        assert sha(a.project / name) == digest
    log = (battle / 'troops-tests-r1.log').read_text()
    for name in ('RealSourcesAndIndependentCaches', 'GroupFailureIsAtomic', 'ControlledOriginalDraw'):
        assert '--- PASS: TestTroops' + name in log
    assert '\nPASS\n' in log and '--- SKIP:' not in log and '\nFAIL' not in log
    control = read(a.controlled / 'receipt.json')
    assert control['status'] == 'PASS-controlled-original-draw-not-natural-encounter'
    cases = control['cases']
    assert len(cases) == 12
    observed = set()
    for row in cases:
        observed.add((row['resource'], row['mirrored'], row['battle']))
        assert row['record'] == 0 and row['frame_pure'] and row['pixels'] == 1920 * 1200
        im = Image.open(a.controlled / row['png']).convert('RGBA')
        assert im.size == (1920, 1200)
        assert hashlib.sha256(im.tobytes()).hexdigest() == row['frame_sha256']
    assert observed == {(source, mirror, battle) for source in ('MAN02.EGG', 'MAN08.EGG', 'MAN20.EGG')
                        for mirror in (False, True) for battle in (False, True)}
    assert control['controlled_memory']['source_buffer'] == '8000:0000' and not control['rules_changed']
    save = read(a.gui / 'save/gui-final.json')
    reload = read(a.gui / 'reload/gui-final.json')
    saved = a.gui / 'scratch/gamedata.ay'
    assert saved.stat().st_size == 2987 and sha(saved) == read(a.gui / 'save/saved.json')['sha256']
    gui = {}
    for phase, status in (('save', save), ('reload', reload)):
        root = a.gui / phase
        assert status['closed'] and status['hd'] and not status['unimplemented']
        assert status['text']['MissingGlyphs'] == 0 and not status['text']['Errors']
        for key in ('asset_error', 'graphics_error', 'battle_actor_error', 'battle_background_error',
                    'battle_effect_error', 'battle_marker_error', 'font_error', 'palette_error'):
            assert not status.get(key), (phase, key, status.get(key))
        receipt = read(root / 'gui-input-receipt.json')
        assert receipt['status'] == 'passed-input-path' and receipt['flow'] == phase
        assert any(e.get('status', {}).get('presented_scene') == 'character' for e in receipt['events'])
        assert saved.read_bytes() == (root / 'snapshot-readonly/save-buffer-9e000.bin').read_bytes()
        stream = read(root / 'continuous-audit.json')
        assert stream['frames'] == status['recorded_frames'] and stream['status'] == 'lossless-stream-valid'
        assert sha(root / 'presentation.frames.gz') == stream['recording_sha256']
        gui[phase] = dict(draws=stream['frames'], changed_frames=stream['changed_frames'],
                          font=status['font_id'], contact_sheets=stream['contact_sheets'])
    assert save['exited'] and save['exit_code'] == 0 and not reload['exited'] and reload['presented_scene'] == 'map'
    events = read(a.gui / 'save/gui-input-receipt.json')['events']
    fonts = {e.get('status', {}).get('presented_font_id') for e in events
             if e.get('status', {}).get('presented_scene') == 'main-menu'}
    assert {'noto', 'lishu', 'caoshu'} <= fonts
    for name in ('noto', 'lishu', 'caoshu'):
        assert (a.gui / 'save' / ('font-' + name + '.png')).is_file()
    assert read(a.gui / 'settings.json')['font'] == 'caoshu'
    result = dict(status='PASS-scoped-048-batch-import-and-sampled-presentation', production=False,
                  groups=20, poses=80, directions=160, battle_aliases=160,
                  preserved_assets=223, candidate_files=344, build_inputs=inputs, programs=programs,
                  registration_sha256=sha(a.registration / 'registration.json'),
                  registration_path=str(a.registration.relative_to(a.project)),
                  tests_sha256=sha(battle / 'troops-tests-r1.log'), controlled_cases=len(cases),
                  controlled_pixels=sum(c['pixels'] for c in cases), controlled_sha256=sha(a.controlled / 'receipt.json'),
                  saved_bytes=2987, saved_sha256=sha(saved), gui=gui,
                  asset_hashes={f.name: sha(f) for f in sorted(a.assets.iterdir())},
                  tool_sha256=sha(Path(__file__)),
                  limits=['Controlled draw calls are not natural encounters or gameplay parity.',
                          'Shared mechanism sampled; remaining creatures need no individual GUI gate.',
                          '047 direct renderer remains a separate research branch.'])
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'asset_hashes'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
