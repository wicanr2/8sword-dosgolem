#!/usr/bin/env python3
"""047 DRAFT：核對正常繪圖攔截、CPU批次、實際Draw及真正存退讀。"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import runpy
import statistics


def read(path):
    return json.loads(path.read_text())


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for raw in iter(lambda: f.read(1024*1024), b''):
            h.update(raw)
    return h.hexdigest()


def frame_digest(path):
    h = hashlib.sha256()
    with gzip.open(path, 'rb') as f:
        for raw in iter(lambda: f.read(1024*1024), b''):
            h.update(raw)
    return h.hexdigest()


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def verify_manifest(path, root):
    lines = path.read_text().splitlines()
    for line in lines:
        sha, name = line.split('  ', 1)
        assert digest(root/name) == sha, name
    return len(lines)


def direct_calls(root):
    receipt = read(root/'direct-runtime-receipt.json')
    assert receipt['bound'] and not receipt['control'] and not receipt['production']
    assert receipt['pam_legacy_rgb_frames'] == 0 and receipt['pam_source_frames'] > 0
    commands = rows(root/'direct-runtime-commands.jsonl')
    source = rows(root/'owned-commands.jsonl')
    bitmaps = {(e['entry_step'], e['entry']): e for e in source if e['command'] == 'bitmap'}
    intervals = []
    pending = None
    for event in source:
        if event['command'] == 'panel-begin':
            assert pending is None
            pending = event
        elif event['command'] == 'panel-commit':
            assert pending and event['kind'] == pending['kind'] and event['start_step'] == pending['step']
            intervals.append((pending['step'], event['step'], event['kind']))
            pending = None
    assert pending is None
    accepted, by_panel, steps, cycles, compatibility = {}, {}, 0, 0, 0
    for event in commands:
        plan = event['plan']
        assert event['original_pixel_instructions_executed'] == 0
        entry, end = event['entry_step'], event['return_boundary_step']
        original = bitmaps[entry, plan['Entry']]
        assert original['step'] == end
        assert original['source_sha256'] == plan['SourceSHA256']
        assert (original['x_byte'], original['y'], original['width_bytes'], original['height'], original['dest']) == (
            plan['XByte'], plan['Y'], plan['WidthBytes'], plan['Height'], plan['Destination'])
        assert plan['Entry'] in (0x99c, 0x76f)
        assert plan['ReturnBoundary'] == {0x99c: 0xa6f, 0x76f: 0x854}[plan['Entry']]
        assert plan['Steps'] == end-entry == 32*plan['Height']+81
        assert plan['Cycles'] == plan['Steps']+4*plan['WidthBytes']*plan['Height']
        accepted[hex(plan['Entry'])] = accepted.get(hex(plan['Entry']), 0)+1
        panel = next((kind for begin, stop, kind in intervals if begin <= entry < stop), 'outside-panel')
        by_panel[panel] = by_panel.get(panel, 0)+1
        steps += plan['Steps']
        cycles += plan['Cycles']
        compatibility += 4*plan['WidthBytes']*plan['Height']
    assert accepted.get('0x99c', 0) > 0 and accepted.get('0x76f', 0) > 0
    counts = receipt['counts']
    assert len(commands) == counts['accepted']
    assert steps == counts['virtual-instructions'] and cycles == counts['virtual-cycles']
    assert compatibility == counts['compatibility-plane-bytes']
    return dict(accepted=len(commands), entries=accepted, panel_calls=by_panel,
                virtual_instructions=steps, virtual_cycles=cycles,
                compatibility_plane_bytes=compatibility,
                pam_source_frames=receipt['pam_source_frames'], pam_legacy_rgb_frames=0,
                fallbacks={k: v for k, v in counts.items() if k.startswith('fallback-')})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000
    assert not args.out.exists() and args.out.parent.stat().st_uid == 1000
    p = args.project
    battle = p/'workplace/probe-20261023/graphics-first/battle-r1'
    run, control = battle/'direct-hire-r3', battle/'owned-hire-vga-read-r2'
    paired = {}
    for name in ('final.state', 'audio.pcm', 'commands.jsonl', 'owned-commands.jsonl',
                 'owned-intro-commands.jsonl', 'vga-reads.json'):
        assert digest(run/name) == digest(control/name), name
        paired[name] = digest(run/name)
    a, b = frame_digest(run/'presentation.frames.gz'), frame_digest(control/'presentation.frames.gz')
    assert a == b
    paired['decompressed_frames'] = a
    files = lambda r: {str(f.relative_to(r)): digest(f) for f in r.rglob('*') if f.is_file()}
    assert files(run/'scratch') == files(control/'scratch')
    final = read(run/'final.json')
    assert final['recorded_frames'] == final['frame_pure_count'] == 542
    normal = direct_calls(run)
    assert normal['panel_calls'].get('character', 0) > 0
    assert normal['panel_calls'].get('army', 0) > 0
    assert {e['font_id'] for e in rows(run/'frames.jsonl')} == {'noto', 'lishu', 'caoshu'}
    build = battle/'owned-live-build-r28'
    inputs = verify_manifest(build/'build-inputs.sha256', build/'src')
    programs = verify_manifest(build/'build-outputs.sha256', build)
    # The runtime-call implementation and engine are unchanged from the tested r27.
    previous = battle/'owned-live-build-r27/src'
    for name in ('internal/eightsword/research_direct_runtime.go', 'internal/eightsword/research_direct_runtime_test.go',
                 'internal/eightsword/engine.go'):
        assert digest(build/'src'/name) == digest(previous/name)
    prefix = (battle/'direct-runtime-prefix-r2.log').read_text()
    assert prefix.count('    --- PASS: TestResearchDirectRuntimeNativePrefixAndPoisonedStack/') == 16
    assert '\nFAIL' not in prefix and '\nPASS\n' in prefix
    core = battle/'core-direct-r5'
    manifest = read(core/'runtime-manifest.json')
    assert digest(core/'runtime.patch') == manifest['patch_sha256']
    for name, sha in manifest['base_inputs'].items():
        assert digest(p/'workplace/dosgolem'/name) == sha
        if name not in manifest['changed']:
            assert digest(core/'src'/name) == sha
    for name, sha in manifest['changed'].items():
        assert digest(core/'src'/name) == sha
    tests = (core/'host-call-tests-r1.log').read_text()
    assert tests.count('--- PASS: TestResearchHostCall') == 3 and '\nPASS\n' in tests
    batch_tests = (battle/'render-batch-tests-r1.log').read_text()
    assert batch_tests.count('--- PASS: TestResearchOwnedBatch') == 2 and '\nPASS\n' in batch_tests
    performance = []
    for event in rows(run/'render-batch-audit.jsonl'):
        assert event['same_pixels'] and event['batch_rgba_sha256'] == event['reference_rgba_sha256']
        stats = event['batch']
        assert stats['NativeRGBPixels']+stats['TextureCopyPixels'] == 2304000
        old, modern = event['reference_ns'], event['batch_ns']
        assert len(old) == len(modern) == 3 and min(old+modern) > 0
        performance.append(dict(kind=event['kind'], font=event['font'],
                                reference_median_ms=statistics.median(old)/1e6,
                                batch_median_ms=statistics.median(modern)/1e6,
                                ratio=statistics.median(old)/statistics.median(modern),
                                batch=stats, rgba_sha256=event['batch_rgba_sha256']))
    assert len(performance) >= 10
    gui = p/'workplace/player/gui/direct-source-save-r3'
    decode = runpy.run_path(str(p/'tools/audit-owned-modal.py'))['frames']
    audit_gui = runpy.run_path(str(p/'tools/audit-owned-main-menu.py'))['audit_run']
    gui_results = {}
    for phase in ('save', 'reload'):
        root = gui/phase
        required = {'main-menu', 'first-map', 'character', 'army', 'return-map'}
        if phase == 'save':
            required |= {'new-game-confirm', 'music-menu', 'confirm', 'system'}
        result = audit_gui(root, required, decode, gui=True)
        status = read(root/'gui-final.json')
        assert status['closed'] and status['font_id'] == 'noto'
        assert not status['unimplemented'] and status['text']['MissingGlyphs'] == 0 and not status['text']['Errors']
        if phase == 'save':
            assert status['exited'] and status['exit_code'] == 0
        else:
            assert not status['exited'] and status['presented_scene'] == 'map'
        actual = read(root/'gui-input-receipt.json')
        assert actual['status'] == 'passed-input-path' and actual['flow'] == phase
        assert any(e.get('status', {}).get('presented_scene') == 'character' and
                   e.get('status', {}).get('presented_font_id') == 'noto' for e in actual['events'])
        result['direct'] = direct_calls(root)
        assert result['direct']['panel_calls'].get('character', 0) > 0
        gui_results[phase] = result
    saved = gui/'scratch/gamedata.ay'
    assert saved.stat().st_size == 2987 and digest(saved) == read(gui/'save/saved.json')['sha256']
    for phase in ('save', 'reload'):
        buffer = gui/phase/'snapshot-readonly/save-buffer-9e000.bin'
        assert saved.read_bytes() == buffer.read_bytes()
    result = dict(status='PASS-scoped-normal-direct-calls-and-batched-source-renderer', production=False,
                  paired_hashes=paired, normal=normal, normal_frames=542,
                  scratch_files=len(files(run/'scratch')), build_inputs=inputs, build_programs=programs,
                  native_prefix_cases=16, runtime_event_tests=3, batch_tests=2,
                  gui=gui_results, saved_sha256=digest(saved), saved_bytes=2987,
                  render_performance=performance,
                  limits=['Fixed-source admitted four/five-plane mode1 calls only; other primitives still execute native code.',
                          'CPU source-render timing includes packet and glyph work, not whole-game FPS; GPU and SIMD are not implemented.',
                          'Production r48 remains unchanged; whole-game rendering and asset/failure coverage remain incomplete.'])
    with args.out.open('x') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('gui', 'render_performance')}, ensure_ascii=False))
    print(json.dumps(dict(render_performance=performance), ensure_ascii=False))


if __name__ == '__main__':
    main()
