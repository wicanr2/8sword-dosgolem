#!/usr/bin/env python3
"""047：獨立核對Go繪圖候選、原版模式、畫面回歸及真正視窗存讀。"""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path

from PIL import Image


PROGRAMS = ['8sword', '8sword-replay', 'gui-check', 'music-check',
            'heroine-check', 'museum-check', 'story-prelude-check']


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
    ending = root/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    candidate, previous = player/'source-candidate-render-r5', player/'source-candidate-effects-r1'
    inputs = {}
    for line in (candidate/'build-inputs.sha256').read_text().splitlines():
        digest, name = line.split(None, 1)
        assert name.startswith('/project/')
        name = name.removeprefix('/project/')
        assert sha(root/name) == sha(candidate/'src'/name) == digest
        inputs[name] = digest
    assert len(inputs) == 168
    programs = {name:sha(candidate/name) for name in PROGRAMS}
    prior_programs = {name:sha(previous/name) for name in PROGRAMS}
    assert {name:sha(player/name) for name in PROGRAMS} == prior_programs
    assert 'go1.24.13' in (candidate/'build-go-version.txt').read_text()
    runtime = read(candidate/'runtime.json')
    core = player/'runtime-render-r1'
    assert runtime == read(core/'render-core.json') and runtime['total_inputs'] == 923
    assert {str(p.relative_to(core/'src')) for p in (core/'src').rglob('*') if p.is_file()} == set(runtime['files'])
    for name, digest in runtime['files'].items():
        assert sha(core/'src'/name) == digest
    prior_core = read(player/'runtime-input-r1/runtime-input.json')
    original_core = {**prior_core['base_inputs'], **prior_core['added']}
    assert len(original_core) == 921 and runtime['base_inputs'] == original_core
    for name, digest in original_core.items():
        assert sha(player/'runtime-input-r1/src'/name) == digest
    original_manifest = read(root/'workplace/intake-20261023/source-manifest.json')
    original_files = [f for f in original_manifest['files'] if f['path'].startswith('game/8sword/')]
    assert len(original_files) == 158
    for f in original_files:
        assert sha(root/'workplace/intake-20261023/sources'/f['path']) == f['sha256']
    assets = read(ending/'effects-audit-r1.json')['asset_hashes']
    assert len(assets) == 455
    for name, digest in assets.items():
        assert sha(player/'assets-painted-r62'/name) == digest
    tests = (batch/'candidate-tests-r5.log').read_text()
    assert '\nPASS\n' in tests and '\nFAIL' not in tests and '--- FAIL:' not in tests and '--- SKIP:' not in tests
    for test in ['TestHDFrameCannotFallBackToOriginalRGB', 'TestOriginalModeDoesNotInstallRenderTakeover',
                 'TestResearchSourceGlyphOracle', 'TestResearchSourcePageOracle',
                 'TestResearchSourceBitmapRowsOracle', 'TestResearchIntroMaskedOracle',
                 'TestResearchIntroMaskedNormal', 'TestResearchSourceRevealTileOracle',
                 'TestResearchSourceRevealPointOracle', 'TestResearchSourceRevealNormal',
                 'TestSourceRuntimeNormalAndControlledFault', 'TestEndingSourceRuntime']:
        assert re.search(r'^--- PASS: '+test+r' \(',tests,re.M),test
    assert 'pixels=64000 native writes=[64000 0]' in tests
    assert (batch/'candidate-vet-r5.log').read_text() == ''
    frame_source = (root/'internal/eightsword/engine.go').read_text().split('func (e *Engine) Frame()')[1].split('func (e *Engine) presentIntro')[0]
    assert 'Tracker.Compose' not in frame_source and 'presentIntro' not in frame_source
    assert 'HD-source-renderer-unavailable' in frame_source and 'missing-source-renderer' in frame_source
    prefix = batch/'ending-prefix-r5'
    native, hd = read(prefix/'native/runtime.json'), read(prefix/'hd/runtime.json')
    for key in ['steps', 'state_sha256', 'native_pcm_sha256', 'inputs', 'file_ops', 'unimplemented']:
        assert native[key] == hd[key]
    assert native['steps'] == 89060489 and native['state_sha256'] == 'c863af8c6c7b33686fa01855946a31bbc0e32588f1c02b4890301f0e1e912564'
    assert sha(prefix/'native/final.state') == sha(prefix/'hd/final.state') == native['state_sha256']
    baseline = ending/'runtime-effects-r1/hd'
    compared = {}
    for name in ['01-main-menu.png', '02-map.png', '03-character.png', '04-army.png'] + [
            f'sample-{n:02}-{font}.png' for n in range(1,4) for font in ['noto','lishu','caoshu']]:
        assert rgba(prefix/'hd'/name) == rgba(baseline/name),name
        compared[name] = sha(prefix/'hd'/name)
    gui = player/'gui/render-takeover-r5-story-save-r1'
    saved = read(gui/'save-cycle-audit.json')
    assert saved['status'] == 'passed-scoped-normal-gui-save-exit-reload' and saved['saved_bytes'] == 2987
    gui_receipts = {}
    for phase in ['save','reload']:
        status = read(gui/phase/'gui-final.json')
        assert status['hd'] and status['source_renderer'] and status['owned_render_fault'] is None
        assert not status['asset_error'] and not status['unimplemented']
        assert status['go_reveal_pixels'] == 64000 and status['go_intro_mask_batches'] > 0
        assert status['go_page_clears'] > 0 and status['go_page_copies'] > 0 and status['go_bitmap_row_copies'] > 0
        stream = read(gui/phase/'continuous-audit.json')
        assert stream['frames'] == status['recorded_frames'] and stream['status'] == 'lossless-stream-valid'
        executable_lines = (gui/phase/'executables.sha256').read_text().splitlines()
        assert any(line.startswith(programs['8sword']+' ') for line in executable_lines)
        gui_receipts[phase] = dict(frames=stream['frames'],go_reveal_pixels=status['go_reveal_pixels'],
                                   go_page_clears=status['go_page_clears'],go_page_copies=status['go_page_copies'],
                                   go_bitmap_row_copies=status['go_bitmap_row_copies'])
    receipts = {str(p.relative_to(root)):sha(p) for p in [batch/'candidate-tests-r5.log',batch/'candidate-vet-r5.log',
        batch/'candidate-ending-full-r1.log',gui/'save-cycle-audit.json',gui/'save/continuous-audit.json',gui/'reload/continuous-audit.json']}
    result = dict(schema=1,spec='047',status='PASS-scoped-047-native-render',production=False,
        candidate=candidate.name,previous=previous.name,programs=programs,previous_programs=prior_programs,
        source_inputs=inputs,source_input_count=len(inputs),build_inputs_sha256=sha(candidate/'build-inputs.sha256'),
        runtime_sha256=sha(candidate/'runtime.json'),core_files=923,preserved_core_files=921,
        assets='assets-painted-r62',asset_hashes=assets,original_files=158,hd_rgb_overlay_removed=True,
        prefix_steps=native['steps'],prefix_state_sha256=native['state_sha256'],prefix_pcm_sha256=native['native_pcm_sha256'],
        compared_frames=compared,gui=gui_receipts,saved_sha256=saved['saved_sha256'],receipts=receipts,
        tool_sha256=sha(Path(__file__)),all_graphics_cpu_loops_skipped=False,
        limits=['Scoped Go primitives and sampled player paths only; remaining PAM plot/readback and event-adjacent masked/glyph compatibility need separate accounting.',
                'Full ending/BIOS-Esc evidence uses source-candidate-render-r1; final r5 ending coverage is the END4 prefix.',
                'No overall FPS, all-game completion, natural victory or new release claim.'])
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],source_inputs=len(inputs),core_files=923,assets=455,compared_frames=len(compared),gui=gui_receipts)))


if __name__ == '__main__':
    main()
