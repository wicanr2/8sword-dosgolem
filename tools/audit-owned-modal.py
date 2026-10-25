#!/usr/bin/env python3
"""047 DRAFT：核對F3至F7、確認框、原版標記動畫與自有場景提交。"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct

from PIL import Image, ImageChops


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frames(path):
    with gzip.open(path, 'rb') as stream:
        def take(n):
            data = stream.read(n)
            assert len(data) == n
            return data
        assert take(8) == b'8SFRM001'
        w, h = struct.unpack('<II', take(8))
        assert (w, h) in ((1920, 1200), (2944, 1264))
        rgba = bytearray(w * h * 4)
        previous_step = 0
        ordinal = 0
        while header := stream.read(24):
            assert len(header) == 24
            number, step, rows = struct.unpack('<QQQ', header)
            ordinal += 1
            assert number == ordinal and step >= previous_step and rows <= h
            assert ordinal > 1 or rows == h
            seen = set()
            for _ in range(rows):
                y, = struct.unpack('<H', take(2))
                assert y < h and y not in seen
                seen.add(y)
                rgba[y*w*4:(y+1)*w*4] = take(w*4)
            im = Image.frombytes('RGBA', (w, h), bytes(rgba))
            if w == 2944:
                im = im.crop((512, 64, 2432, 1264))
            yield number, step, hashlib.sha256(im.tobytes()).hexdigest()
            previous_step = step


def audit_run(root, required, gui=False):
    events = [json.loads(line) for line in (root/'owned-commands.jsonl').read_text().splitlines()]
    intervals, pending = [], None
    for event in events:
        if event['command'] == 'panel-begin':
            assert pending is None
            pending = event
        elif event['command'] == 'panel-commit':
            assert pending and event['kind'] == pending['kind'] and event['start_step'] == pending['step']
            assert event['primitive_pending'] == 0 and event['step'] > pending['step']
            intervals.append(dict(kind=event['kind'], begin=pending['step'], commit=event['step'], frames=0))
            pending = None
    receipt = read(root/'owned-receipt.json')
    assert pending is None and receipt['panel_at_end'] is None and receipt['active_at_end'] == 0
    assert receipt['commands'].get('writes-outside-command', 0) == 0
    assert not any('reject' in key for key in receipt['commands'])
    assert required <= {x['kind'] for x in intervals}
    rendered = list(frames(root/'presentation.frames.gz'))
    prior = None
    for number, step, digest in rendered:
        for interval in intervals:
            if interval['begin'] <= step < interval['commit']:
                assert prior == digest, (root, number, interval)
                interval['frames'] += 1
        prior = digest
    staged = sum(x['frames'] for x in intervals)
    calls = receipt['commands'].get('panel-staged-frames', 0)
    assert 0 <= staged <= calls
    if not gui:
        assert staged > 0
    completed = []
    for event in events:
        if event['command'] != 'completed-capture' or not event['kind'].startswith('panel-'):
            continue
        name = event['kind']
        own = Image.open(root/(name+'-owned.png')).convert('RGBA')
        legacy = Image.open(root/(name+'-legacy.png')).convert('RGBA')
        assert own.size == legacy.size == (1920, 1200)
        digest = hashlib.sha256(own.tobytes()).hexdigest()
        assert digest == event['rgba_sha256'] and hashlib.sha256(legacy.tobytes()).hexdigest() == event['legacy_rgba_sha256']
        diff = ImageChops.difference(own, legacy).convert('RGB')
        if name == 'panel-minimap-complete':
            pixels = [(x, y) for y in range(1200) for x in range(1920) if diff.getpixel((x, y)) != (0, 0, 0)]
            assert len(pixels) == event['different_pixels'] == 23040
            assert {x//3 for x, _ in pixels} == {96, 97, 98, 99, 380, 381, 382, 383}
            assert {y//6 for _, y in pixels} == set(range(13, 173))
        else:
            assert diff.getbbox() is None and event['different_pixels'] == 0
        next_begin = min((x['begin'] for x in intervals if x['begin'] > event['step']), default=2**64)
        visible = [n for n, step, value in rendered if event['step'] <= step < next_begin and value == digest]
        if gui and name != 'panel-minimap-complete':
            assert visible, (root, name, 'not present in actual Draw')
        completed.append(dict(kind=name, full_pixels=2304000, different_from_legacy=event['different_pixels'],
                              rgba_sha256=digest, actual_frame_ordinals=visible,
                              limit='Minimap marker animation can advance between completion and Draw.' if name == 'panel-minimap-complete' else ''))
    final = read(root/('gui-final.json' if gui else 'final.json'))
    assert len(rendered) == final['recorded_frames']
    if not gui:
        assert final['frame_pure_count'] == len(rendered) == 378
    return dict(frames=len(rendered), staged_frames=staged, renderer_staged_calls=calls,
                intervals=intervals, completed_scenes=completed, stream_sha256=sha(root/'presentation.frames.gz'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    p = args.project
    battle = p/'workplace/probe-20261023/graphics-first/battle-r1'
    run, control = battle/'owned-modal-r12', battle/'owned-modal-control-r1'
    gui = p/'workplace/player/gui/owned-modal-save-r1'
    for name in ('final.state', 'audio.pcm'):
        assert sha(run/name) == sha(control/name)
    files = lambda d: {q.name: sha(q) for q in d.iterdir() if q.is_file()}
    assert files(run/'scratch') == files(control/'scratch')
    old = 'only verified character/army panel and map-return boundaries are atomic; opening, other modal dialogs, mode changes and failure recovery remain research gaps'
    new = 'selected PAM panel and system confirmation boundaries only; opening, other modal dialogs, spell casting, mode changes and failure recovery remain research gaps'
    source12 = (battle/'owned-live-build-r12/src/internal/eightsword/research_owned_scene.go').read_text()
    source13 = (battle/'owned-live-build-r13/src/internal/eightsword/research_owned_scene.go').read_text()
    assert source12.count(old) == 1 and source12.replace(old, new) == source13
    assert (p/'tools/research-owned-scene.go').read_text().replace('//go:build ignore\n', '', 1).lstrip('\n') == source13
    renderer = source13[source13.index('func renderOwnedScene('):source13.index('func (e *Engine) ResearchOwnedScene(')]
    for token in ('Oracle', '.Screen(', '.ScreenRGB(', 'PlanarBytePixels', '.Before', '.owners'):
        assert token not in renderer
    wanted = {'arrange', 'spells', 'minimap', 'items', 'system', 'return-map'}
    result = dict(status='PASS-scoped-owned-modal-staging', production=False, spec_status='DRAFT',
                  headless=audit_run(run, wanted), gui_save=audit_run(gui/'save', wanted | {'army', 'character', 'confirm'}, True),
                  gui_reload=audit_run(gui/'reload', {'character', 'return-map'}, True),
                  state_sha256=sha(run/'final.state'), pcm_sha256=sha(run/'audio.pcm'), scratch_files=len(files(run/'scratch')),
                  save_cycle=read(gui/'save-cycle-audit.json'), research_source_sha256=sha(p/'tools/research-owned-scene.go'),
                  limits=['F3 sampled selection and cancel, without dismissal; F4 only no-spells; F6 only empty search.',
                          'Minimap blink is intentional animation, not an unfinished-panel exposure.',
                          'Opening, other dialogs, casting, mode changes and failure recovery remain DRAFT.'])
    assert result['gui_save']['staged_frames'] > 0
    assert args.out.parent.is_dir() and args.out.parent.stat().st_uid == 1000 and not args.out.exists()
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('headless', 'gui_save', 'gui_reload', 'save_cycle')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
