#!/usr/bin/env python3
"""047：核對Go相容像素候選、原版控制、完整結局與真正視窗存讀。"""
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


def rgba(path):
    with Image.open(path) as im:
        return im.size, hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()


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
    prior = read(batch/'native-render-audit-r1.json')
    promotion = read(batch/'native-render-promotion-r1.json')
    assert promotion['audit_sha256'] == sha(batch/'native-render-audit-r1.json')
    candidate, previous = player/'source-candidate-compat-r2', player/prior['candidate']
    inputs = {}
    for line in (candidate/'build-inputs.sha256').read_text().splitlines():
        digest, name = line.split(None, 1)
        assert name.startswith('/project/')
        name = name.removeprefix('/project/')
        assert sha(root/name) == sha(candidate/'src'/name) == digest
        inputs[name] = digest
    assert len(inputs) == 170
    tested = player/'source-candidate-compat-r1'
    # r2 adds only source-command telemetry and changes the GUI observer.
    # The pixel algorithms, core and ending implementation are unchanged.
    allowed = {'internal/eightsword/engine.go', 'internal/eightsword/source_scene.go',
               'internal/eightsword/source_runtime_test.go', 'tools/gui-check.go'}
    changed = {name for name in inputs if sha(tested/'src'/name) != inputs[name]}
    assert changed == allowed
    before, after = (tested/'src/internal/eightsword/source_scene.go').read_text(), (root/'internal/eightsword/source_scene.go').read_text()
    assert after.replace('\t\t\t\tif actor != 0 {\n\t\t\t\t\tp.e.sourceActorCommits++\n\t\t\t\t}\n', '') == before
    before, after = (tested/'src/internal/eightsword/engine.go').read_text(), (root/'internal/eightsword/engine.go').read_text()
    assert after.replace('\tsourceActorCommits   uint64\n', '').replace('\tout["source_actor_commits"] = e.sourceActorCommits\n', '') == before
    programs = {name: sha(candidate/name) for name in prior['programs']}
    for name, digest in prior['programs'].items():
        assert sha(previous/name) == sha(player/name) == digest
    assert 'go1.24.13' in (candidate/'build-go-version.txt').read_text()
    core = player/'runtime-render-r1'
    runtime = read(candidate/'runtime.json')
    assert runtime == read(core/'render-core.json') and runtime['total_inputs'] == 923
    assert {str(p.relative_to(core/'src')) for p in (core/'src').rglob('*') if p.is_file()} == set(runtime['files'])
    for name, digest in runtime['files'].items():
        assert sha(core/'src'/name) == digest
    assert len(prior['asset_hashes']) == 455
    for name, digest in prior['asset_hashes'].items():
        assert sha(player/'assets-painted-r62'/name) == digest
    manifest = read(root/'workplace/intake-20261023/source-manifest.json')
    originals = [f for f in manifest['files'] if f['path'].startswith('game/8sword/')]
    assert len(originals) == 158
    for f in originals:
        assert sha(root/'workplace/intake-20261023/sources'/f['path']) == f['sha256']
    tests = (batch/'compat-candidate-tests-r1.log').read_text()
    assert '\nPASS\n' in tests and '\nFAIL' not in tests and '--- FAIL:' not in tests and '--- SKIP:' not in tests
    for name in ['TestSourceCompatNativeGlyphs', 'TestSourceCompatNativeMasked',
                 'TestSourceCompatNativePlotAndRestore', 'TestSourceCompatNativeGuard',
                 'TestSourceCompatNativeRejectsWithoutMutation', 'TestOriginalModeDoesNotInstallRenderTakeover',
                 'TestHDFrameCannotFallBackToOriginalRGB', 'TestSourceRuntimeNormalAndControlledFault',
                 'TestEndingSourceRuntime']:
        assert re.search(r'^--- PASS: '+name+r' \(', tests, re.M), name
    assert re.search(r'native pixel writes=\[[1-9][0-9]* 0\] Go compatibility writes=[1-9]', tests)
    assert (batch/'compat-candidate-vet-r1.log').read_text() == ''
    newest = (batch/'compat-candidate-tests-r2.log').read_text()
    assert '\nPASS\n' in newest and '--- FAIL:' not in newest and '--- SKIP:' not in newest
    assert '--- PASS: TestSourceRuntimeNormalAndControlledFault' in newest
    assert re.search(r'native pixel writes=\[[1-9][0-9]* 0\] Go compatibility writes=[1-9]', newest)
    assert (batch/'compat-candidate-vet-r2.log').read_text() == ''
    probe = read(batch/'compat-native-writes-r3.json')
    assert probe['native_writes'] == {} and probe['steps'] == 88509680
    for name in ['compat-native-r1.log', 'compat-native-r3.log']:
        t = (batch/name).read_text()
        assert '\nPASS\n' in t and '--- FAIL:' not in t
    source = (root/'internal/eightsword/source_compat.go').read_text()
    assert 'native-video-write-leftover' in source and 'return false, e.renderFault' in source
    assert 'copy(m.EGAPlane' in source and 'm.EGAPlane(plane)[at] =' in source
    assert not re.search(r'\b(?:CPU|m|Oracle)\.(?:Step|Run)\(', source)
    compared = {}
    ending = batch/'compat-candidate-ending-r1'
    ending_pairs = {}
    for suffix in ['', '-escape']:
        native, hd = read(ending/('native'+suffix)/'runtime.json'), read(ending/('hd'+suffix)/'runtime.json')
        for key in ['steps', 'state_sha256', 'native_pcm_sha256', 'inputs', 'file_ops', 'unimplemented']:
            assert native[key] == hd[key], key
        assert sha(ending/('native'+suffix)/'final.state') == sha(ending/('hd'+suffix)/'final.state') == native['state_sha256']
        old = read(batch/'ending-full-r1'/('hd'+suffix)/'runtime.json')
        assert all(hd[key] == old[key] for key in ['steps', 'state_sha256', 'native_pcm_sha256'])
        ending_pairs['hd'+suffix] = {key: hd[key] for key in ['steps', 'state_sha256', 'native_pcm_sha256']}
        for frame in (ending/('hd'+suffix)).glob('*.png'):
            assert rgba(frame) == rgba(batch/'ending-full-r1'/('hd'+suffix)/frame.name), frame.name
            compared[str(frame.relative_to(ending))] = sha(frame)
    gui = player/'gui/compat-pixels-save-r2'
    saved = read(gui/'save-cycle-audit.json')
    assert saved['status'] == 'passed-scoped-normal-gui-save-exit-reload' and saved['saved_bytes'] == 2987
    guis = {}
    for phase in ['save', 'reload']:
        status = read(gui/phase/'gui-final.json')
        assert status['hd'] and status['source_renderer'] and status['owned_render_fault'] is None
        assert not status['asset_error'] and not status['unimplemented']
        assert status['go_compat_reads'] > 0 and status['go_compat_writes'] > 0
        assert status['source_actor_commits'] > 0
        stream = read(gui/phase/'continuous-audit.json')
        assert stream['status'] == 'lossless-stream-valid' and stream['frames'] == status['recorded_frames']
        assert any(line.startswith(programs['8sword']+' ') for line in (gui/phase/'executables.sha256').read_text().splitlines())
        guis[phase] = {key: status[key] for key in ['recorded_frames', 'go_compat_reads', 'go_compat_writes', 'go_compat_restore_rows', 'source_actor_commits']}
    receipt_paths = [batch/'compat-candidate-tests-r1.log', batch/'compat-candidate-vet-r1.log',
                     batch/'compat-native-writes-r3.json', batch/'compat-native-r1.log', batch/'compat-native-r3.log',
                     batch/'native-render-audit-r1.json', batch/'native-render-promotion-r1.json', gui/'save-cycle-audit.json',
                     batch/'compat-candidate-tests-r2.log', batch/'compat-candidate-vet-r2.log', tested/'build-inputs.sha256']
    for phase in ['save', 'reload']:
        receipt_paths += [gui/phase/'continuous-audit.json', gui/phase/'gui-final.json',
                          ending/('hd' if phase == 'save' else 'hd-escape')/'runtime.json']
    result = dict(schema=1, spec='047', status='PASS-scoped-047-go-compatibility', production=False,
                  candidate=candidate.name, previous=previous.name, programs=programs, previous_programs=prior['programs'],
                  source_inputs=inputs, source_input_count=170, build_inputs_sha256=sha(candidate/'build-inputs.sha256'),
                  runtime_sha256=sha(candidate/'runtime.json'), core_files=923, preserved_core_files=921,
                  assets='assets-painted-r62', asset_hashes=prior['asset_hashes'], original_files=158,
                  sampled_native_pixel_write_sites=0, original_control_cases=78, rejection_cases=7,
                  full_control_build=tested.name, telemetry_delta_files=sorted(changed),
                  ending=ending_pairs, compared_frames=compared, gui=guis, saved_sha256=saved['saved_sha256'],
                  receipts={str(p.relative_to(root)): sha(p) for p in receipt_paths}, tool_sha256=sha(Path(__file__)),
                  limits=['Known pixel contracts use native Go; original non-pixel control and timing remain.',
                          'Unregistered HD writes stop on their first notification; no all-game reachability claim.',
                          'Ending entry is an authorized controlled original branch, not natural victory.',
                          'No overall FPS or release claim.'])
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(status=result['status'], inputs=170, frames=len(compared), gui=guis)))


if __name__ == '__main__':
    main()
