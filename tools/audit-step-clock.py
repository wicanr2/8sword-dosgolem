#!/usr/bin/env python3
"""047：核對步數時鐘HD原語、實際CLI與即時時鐘回歸。"""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path

from PIL import Image


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def passed(path, names):
    text = path.read_text()
    assert '\nPASS\n' in text and '--- FAIL:' not in text and '--- SKIP:' not in text
    for name in names:
        assert re.search(r'^--- PASS: '+name+r' \(', text, re.M), name
    return text


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    root = a.project
    player = root/'workplace/player'
    batch = root/'workplace/probe-20261023/graphics-first/render-takeover-r1'
    prior = read(batch/'compat-render-audit-r1.json')
    promote = read(batch/'compat-render-promotion-r1.json')
    assert promote['audit_sha256'] == sha(batch/'compat-render-audit-r1.json')
    candidate, previous = player/'source-candidate-step-clock-r1', player/prior['candidate']
    inputs = {}
    for line in (candidate/'build-inputs.sha256').read_text().splitlines():
        digest, name = line.split(None, 1)
        assert name.startswith('/project/')
        name = name.removeprefix('/project/')
        assert sha(root/name) == sha(candidate/'src'/name) == digest
        inputs[name] = digest
    assert len(inputs) == 171
    programs = {name: sha(candidate/name) for name in prior['programs']}
    for name, digest in prior['programs'].items():
        assert sha(previous/name) == sha(player/name) == digest
    assert 'go1.24.13' in (candidate/'build-go-version.txt').read_text()
    core = player/'runtime-render-r1'
    runtime = read(candidate/'runtime.json')
    assert runtime == read(core/'render-core.json') and runtime['total_inputs'] == 923
    for name, digest in runtime['files'].items():
        assert sha(core/'src'/name) == digest
    for name, digest in prior['asset_hashes'].items():
        assert sha(player/'assets-painted-r62'/name) == digest
    original_manifest = read(root/'workplace/intake-20261023/source-manifest.json')
    originals = [f for f in original_manifest['files'] if f['path'].startswith('game/8sword/')]
    assert len(originals) == 158
    for f in originals:
        assert sha(root/'workplace/intake-20261023/sources'/f['path']) == f['sha256']
    tests = passed(batch/'step-clock-candidate-tests-r1.log', [
        'TestSourceStepClockReplay', 'TestSourceCompatNativeGlyphs', 'TestSourceCompatNativeMasked',
        'TestSourceCompatNativePlotAndRestore', 'TestResearchSourcePageOracle',
        'TestResearchSourceBitmapRowsOracle', 'TestResearchSourceRevealPointOracle'])
    for name, count in [('TestResearchSourcePageOracle', 64), ('TestResearchSourceBitmapRowsOracle', 20),
                        ('TestSourceCompatNativeGlyphs', 36), ('TestSourceCompatNativeMasked', 14),
                        ('TestSourceCompatNativePlotAndRestore', 28), ('TestResearchSourceRevealPointOracle', 3)]:
        assert len(re.findall(r'^ +--- PASS: '+name+r'/', tests, re.M)) == count, name
    passed(batch/'step-clock-candidate-live-r1.log', [
        'TestSourceRuntimeNormalAndControlledFault', 'TestOriginalModeDoesNotInstallRenderTakeover',
        'TestSourceCompatNativeGuard', 'TestSourceCompatNativeRejectsWithoutMutation',
        'TestResearchSourcePageOracle', 'TestResearchSourceBitmapRowsOracle', 'TestResearchSourceRevealPointOracle'])
    assert (batch/'step-clock-candidate-vet-r1.log').read_text() == ''
    paired = read(batch/'step-clock-candidate-replay-r1/replay.json')
    assert paired['status'] == 'passed-step-clock-original-control' and paired['production']
    assert paired['steps'] == 250000000 and paired['native_writes'] == [4194129, 0]
    assert len(paired['checkpoints']) == 25 and len(paired['mixed_pcm_sha256']) == 64
    hd_path, native_path = batch/'step-clock-cli-hd-r1', batch/'step-clock-cli-native-r1'
    hd, native = read(hd_path/'receipt.json'), read(native_path/'receipt.json')
    for key in ['steps', 'mode', 'pam_loaded', 'input_events', 'exec_log', 'file_ops', 'unimplemented']:
        assert hd[key] == native[key], key
    for status in [hd, native]:
        assert status['steps'] == 250000000 and status['sampled_frames'] == 249
        assert status['clock_mode'] == 'instruction' and status['normal_input_replay'] and not status['snapshot_loaded']
        assert status['owned_render_fault'] is None and not status['unimplemented']
    assert hd['hd'] and hd['source_renderer'] and hd['visible_scene'] == 'map'
    assert not native['hd'] and not native['source_renderer'] and native['go_compat_writes'] == 0
    assert hd['native_pixel_writes'] == 0 and native['native_pixel_writes'] == 4194129
    assert hd['go_compat_writes'] == 513065 and hd['go_reveal_pixels'] == 64000
    assert sha(hd_path/'final.state') == sha(native_path/'final.state')
    frames = {}
    for path in hd_path.glob('*.png'):
        with Image.open(path) as im:
            assert im.size == (1920, 1200)
            frames[path.name] = sha(path)
    assert len(frames) == 10
    cli_source = (root/'cmd/8sword-replay/main.go').read_text()
    assert 'EnableLiveClock' not in cli_source and 'AdvanceCycles' not in cli_source
    assert 'engine.Advance(target - now)' in cli_source
    receipts = [batch/'step-clock-primitives-r1.log', batch/'step-clock-replay-r1.log',
                batch/'step-clock-r1/executed-inputs.json', batch/'step-clock-candidate-tests-r1.log',
                batch/'step-clock-candidate-live-r1.log', batch/'step-clock-candidate-vet-r1.log',
                batch/'step-clock-candidate-replay-r1/replay.json', hd_path/'receipt.json', native_path/'receipt.json',
                batch/'compat-render-audit-r1.json', batch/'compat-render-promotion-r1.json']
    result = dict(schema=1, spec='047', status='PASS-scoped-047-step-clock', production=False,
                  candidate=candidate.name, previous=previous.name, programs=programs, previous_programs=prior['programs'],
                  source_inputs=inputs, source_input_count=171, build_inputs_sha256=sha(candidate/'build-inputs.sha256'),
                  runtime_sha256=sha(candidate/'runtime.json'), core_files=923, preserved_core_files=921,
                  assets='assets-painted-r62', asset_hashes=prior['asset_hashes'], original_files=158,
                  original_control_cases=165, steps=250000000, cli_sampled_frames=249, compared_source_frames=250,
                  native_pixel_writes=[4194129, 0], cli_state_sha256=sha(hd_path/'final.state'),
                  mixed_pcm_sha256=paired['mixed_pcm_sha256'], frames=frames,
                  receipts={str(p.relative_to(root)): sha(p) for p in receipts}, tool_sha256=sha(Path(__file__)),
                  limits=['Original step-clock non-pixel control remains; native Go handles the admitted pixel operations.',
                          'No new natural battle, ending, GUI save-cycle or overall FPS claim.',
                          'Only the two established clock/cost pairs are admitted.'])
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({key: result[key] for key in ['status', 'source_input_count', 'steps', 'cli_state_sha256', 'native_pixel_writes']}))


if __name__ == '__main__':
    main()
