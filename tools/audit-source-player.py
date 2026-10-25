#!/usr/bin/env python3
"""047正式來源呈現：核對候選程式、實際Draw、三字型與真正存退讀。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

from PIL import Image, __version__ as PILLOW_VERSION


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def input_manifest(path, project):
    lines = path.read_text().splitlines()
    for line in lines:
        digest, name = line.split('  ', 1)
        assert name.startswith('/project/')
        assert sha(project / name.removeprefix('/project/')) == digest, name
    return len(lines)


def manifest_map(path):
    return {name: digest for digest, name in
            (line.split('  ', 1) for line in path.read_text().splitlines())}


def font_points(im, profiles, font):
    # Source 218 at (208,83): four ASCII spaces precede 開 at (240,83).
    # The toolbar cycles fonts on the main menu, before entering the map.
    # All opaque atlas points must match; a missing/covered field is not selected.
    glyphs, atlas = profiles[font]
    ix, iy, iw, ih = glyphs['開']['ink']
    dw, dh = min(iw, 48), min(ih, 90)
    left, top = 240*3+(48-dw)//2, 83*6+(90-dh)//2
    pixels, count = im.load(), 0
    for y in range(dh):
        for x in range(dw):
            if atlas.getpixel((ix+x*iw//dw, iy+y*ih//dh)) != 255:
                continue
            if pixels[left+x, top+y][:3] != (223, 195, 121):
                return 0
            count += 1
    return count


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for key in ('project', 'build', 'gui', 'toolbar', 'out'):
        ap.add_argument('--'+key, type=Path, required=True)
    args = ap.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000
    assert PILLOW_VERSION == '11.3.0' and not args.out.exists()
    p, build = args.project, args.build
    source_count = input_manifest(build/'build-inputs.sha256', p)
    binaries = {}
    for line in (build/'build-outputs.sha256').read_text().splitlines():
        digest, name = line.split('  ', 1)
        binary = build/Path(name).name
        assert sha(binary) == digest
        binaries[binary.name] = digest
    assert len(binaries) == 7
    assert read(build/'runtime.json')['production']
    # The diagnostic comparator is a frozen research result, never a renderer input.
    b = p/'workplace/probe-20261023/graphics-first/battle-r1'
    reference_receipt = b/'owned-guard-audit-r3.json'
    assert sha(reference_receipt) == 'd4a1958fd3a7a505032fa4feebe7e652015d72a5f8324cb5633110c8fbc83a1c'
    reference = p/'workplace/player/gui/owned-guard-save-r1/save'
    golden = {hashlib.sha256(Image.open(f).convert('RGBA').tobytes()).hexdigest(): f.name
              for f in reference.glob('panel-*-owned.png')}
    spec = importlib.util.spec_from_file_location('source_audit_stream', p/'tools/audit-army-dismiss.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    profiles = helper.fonts(p/'workplace/player/assets-painted-r49')
    phases, matched = {}, {}
    font_draws = {}
    for group, root, names in [('save', args.gui, ('save', 'reload')),
                              ('toolbar', args.toolbar, ('toolbar', 'toolbar-reload'))]:
        for name in names:
            q = root/name
            st, meta = read(q/'gui-final.json'), rows(q/'intro-draw.jsonl')
            stream = read(q/'continuous-audit.json')
            assert st['closed'] and st['hd'] and st['source_renderer'] and st['source_frames'] > 0
            assert st['direct_calls'] > 0 and st['owned_render_fault'] is None
            assert not any(st.get(k) for k in ['asset_error', 'graphics_error', 'font_error', 'unimplemented'])
            assert st['text']['ComposedFrames'] == st['text']['CachedFrames'] == 0
            assert st['text']['MissingGlyphs'] == 0 and not st['text']['Errors']
            assert len(meta) == st['recorded_frames'] == stream['frames']
            assert stream['status'] == 'lossless-stream-valid'
            assert sha(q/'presentation.frames.gz') == stream['recording_sha256']
            assert read(q/'gui-input-receipt.json')['status'] == 'passed-input-path'
            recorded, current = manifest_map(q/'build-inputs.sha256'), manifest_map(build/'build-inputs.sha256')
            test_changes = sorted(k for k in recorded.keys() | current.keys() if recorded.get(k) != current.get(k))
            assert all(name.endswith('_test.go') for name in test_changes), test_changes
            # Test fixture maintenance may follow a GUI run. Require all seven
            # actual binaries to remain byte-identical, including untouched tools.
            recorded_bins = {Path(k).name: v for k, v in manifest_map(q/'build-outputs.sha256').items()}
            assert recorded_bins == binaries
            assert sha(q/'build-go-version.txt') == sha(build/'build-go-version.txt')
            actual = {}
            for n, step, im in helper.stream(q):
                assert meta[n-1]['draw'] == n and meta[n-1]['step'] == step
                if group == 'save':
                    digest = hashlib.sha256(im.tobytes()).hexdigest()
                    if digest in golden:
                        actual.setdefault(golden[digest], []).append(n)
                        matched.setdefault(golden[digest], []).append([name, n])
                else:
                    font = meta[n-1]['font_id']
                    if font not in font_draws:
                        count = font_points(im, profiles, font)
                        if count:
                            font_draws[font] = dict(phase=name, draw=n, opaque_points=count)
            phases[group+'/'+name] = dict(draws=len(meta), changes=stream['changed_frames'],
                source_frames=st['source_frames'], direct_calls=st['direct_calls'],
                old_compositor_frames=0, font=st['font_id'], exact_completed_frames=actual,
                stream_sha256=stream['recording_sha256'], test_only_input_changes=test_changes)
    required = {'main-menu', 'new-game-confirm', 'first-map', 'army', 'character', 'return-map', 'system'}
    assert {f'panel-{name}-complete-owned.png' for name in required} <= set(matched)
    assert {'noto', 'lishu', 'caoshu'} == set(font_draws)
    assert read(args.toolbar/'settings.json')['font'] == 'lishu'
    assert read(args.toolbar/'toolbar-reload/gui-final.json')['font_id'] == 'lishu'
    natural = rows(args.gui/'save/intro-draw.jsonl')
    stages = {v['stage'] for v in natural}
    assert {'publisher-noto', 'title-noto', 'story-prelude', 'story-prelude-handoff', 'story-noto', 'captions-noto'} <= stages
    assert {'left', 'right', 'portrait', 'beam'} <= {v['museum_stage'] for v in natural}
    assert {1, 2, 3, 4, 5} <= {v['story_pages'] for v in natural}
    assert {0x42, 0x6a, 0x92, 0xba} <= {v['caption_source'] for v in natural}
    saved = args.gui/'scratch/gamedata.ay'
    assert saved.stat().st_size == 2987 and sha(saved) == read(args.gui/'save/saved.json')['sha256']
    for name in ('save', 'reload'):
        assert saved.read_bytes() == (args.gui/name/'snapshot-readonly/save-buffer-9e000.bin').read_bytes()
    first, cold = read(args.gui/'save/gui-final.json'), read(args.gui/'reload/gui-final.json')
    assert first['exited'] and first['exit_code'] == 0 and not cold['exited'] and cold['presented_scene'] == 'map'
    reads = [v for v in cold['file_ops'] if v['Op'] == 'read' and v['Name'] == 'gamedata.ay']
    assert len(reads) == 1 and reads[0]['Pos'] == 0 and reads[0]['Len'] == 2987 and not reads[0]['Failed']
    for f in (p/'internal/eightsword').glob('source*.go'):
        if f.name.endswith('_test.go'):
            continue
        text = f.read_text()
        assert not any(word in text for word in ['ScreenRGB(', '.Screen(', '.Compose(', 'EIGHTSWORD_RESEARCH_', 'png.Encode(']), f
    result = dict(schema=1, status='PASS-scoped-047-production-source-renderer',
        build_inputs=source_count, build_inputs_sha256=sha(build/'build-inputs.sha256'),
        binaries=binaries, phases=phases, font_draws=font_draws,
        natural_stages=sorted(stages), golden_reference_receipt_sha256=sha(reference_receipt),
        saved_bytes=2987, saved_sha256=sha(saved), read_step=reads[0]['Step'],
        unit_log_sha256=sha(b/'source-unit-r1.log'), core_log_sha256=sha(b/'source-core-unit-r1.log'),
        audit_sha256=sha(Path(__file__)), pillow=PILLOW_VERSION,
        limits=['Representative normal routes and controlled presentation fault; no per-troop encounter gate.',
                'No all-game, GPU, FPS, RNG-rule or hardware-cycle parity claim.'])
    with args.out.open('x') as f:
        f.write(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(status=result['status'], phases=len(phases), font_draws=font_draws,
                         saved_sha256=result['saved_sha256']), ensure_ascii=False))


if __name__ == '__main__':
    main()
