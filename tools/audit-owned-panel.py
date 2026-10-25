#!/usr/bin/env python3
"""047 DRAFT：獨立核對面板交易期間的完整畫面及正常視窗存退讀。"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct

from PIL import Image


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frames(path):
    with gzip.open(path, 'rb') as stream:
        def take(n):
            data = stream.read(n)
            assert len(data) == n, 'truncated frame stream'
            return data
        assert take(8) == b'8SFRM001'
        width, height = struct.unpack('<II', take(8))
        assert (width, height) in ((1920, 1200), (2944, 1264))
        rgba = bytearray(width * height * 4)
        prior_step = 0
        ordinal = 0
        while header := stream.read(24):
            assert len(header) == 24
            number, step, rows = struct.unpack('<QQQ', header)
            ordinal += 1
            assert number == ordinal and prior_step <= step and rows <= height
            assert ordinal > 1 or rows == height
            seen = set()
            for _ in range(rows):
                y, = struct.unpack('<H', take(2))
                assert y < height and y not in seen
                seen.add(y)
                at = y * width * 4
                rgba[at:at + width * 4] = take(width * 4)
            image = Image.frombytes('RGBA', (width, height), bytes(rgba))
            if width == 2944:
                image = image.crop((512, 64, 2432, 1264))
            yield number, step, hashlib.sha256(image.tobytes()).hexdigest()
            prior_step = step


def audit_run(root, gui=False):
    events = [json.loads(line) for line in (root / 'owned-commands.jsonl').read_text().splitlines()]
    pending = None
    intervals = []
    for event in events:
        if event['command'] == 'panel-begin':
            assert pending is None
            pending = event
        elif event['command'] == 'panel-commit':
            assert pending and event['kind'] == pending['kind']
            assert event['start_step'] == pending['step'] < event['step']
            assert event['primitive_pending'] == 0
            intervals.append({'kind': event['kind'], 'begin': pending['step'], 'commit': event['step'], 'staged_frames': 0})
            pending = None
    receipt = read(root / 'owned-receipt.json')
    assert pending is None and receipt['panel_at_end'] is None and receipt['active_at_end'] == 0
    assert receipt['commands'].get('writes-outside-command', 0) == 0
    assert not any('reject' in key for key in receipt['commands'])
    assert {x['kind'] for x in intervals} == {'character', 'army', 'return-map'}
    rendered = list(frames(root / 'presentation.frames.gz'))
    prior = None
    for number, step, digest in rendered:
        for interval in intervals:
            if interval['begin'] <= step < interval['commit']:
                assert prior is not None and digest == prior, (root, number, interval)
                interval['staged_frames'] += 1
        prior = digest
    staged = sum(x['staged_frames'] for x in intervals)
    calls = receipt['commands']['panel-staged-frames']
    # Headless shots also invoke the renderer; GUI Update and Draw need not
    # have equal counts. Assert every recorded frame, retaining both counts.
    assert staged > 0 and staged <= calls
    if not gui:
        commands = [json.loads(line) for line in (root / 'commands.jsonl').read_text().splitlines()]
        shots = sum(x['command'].startswith('shot ') and
                    any(i['begin'] <= x['step'] < i['commit'] for i in intervals) for x in commands)
        assert calls == staged + shots
    completed = []
    for event in events:
        if event['command'] != 'completed-capture' or not event['kind'].startswith('panel-'):
            continue
        name = event['kind']
        own = Image.open(root / (name + '-owned.png')).convert('RGBA')
        legacy = Image.open(root / (name + '-legacy.png')).convert('RGBA')
        assert own.size == legacy.size == (1920, 1200) and own.tobytes() == legacy.tobytes()
        digest = hashlib.sha256(own.tobytes()).hexdigest()
        assert digest == event['rgba_sha256'] == event['legacy_rgba_sha256']
        assert event['different_pixels'] == 0
        next_begin = min((x['begin'] for x in intervals if x['begin'] > event['step']), default=2**64)
        visible = [n for n, step, value in rendered if event['step'] <= step < next_begin and value == digest]
        # The headless army sample queues Escape before a subsequent Frame.
        # Its complete working-state capture alone is not an actual Draw receipt.
        if gui:
            assert visible, (root, name, 'completed panel absent from actual Draw')
        completed.append({'kind': name, 'step': event['step'], 'rgba_sha256': digest,
                          'full_pixels': 2304000, 'actual_frame_ordinals': visible})
    assert len(completed) == 3
    final = read(root / ('gui-final.json' if gui else 'final.json'))
    assert len(rendered) == final['recorded_frames']
    if not gui:
        assert final['frame_pure_count'] == len(rendered) == 249
    return {'frames': len(rendered), 'staged_frames': staged, 'staged_renderer_calls': calls, 'intervals': intervals,
            'completed_scenes': completed, 'stream_sha256': sha(root / 'presentation.frames.gz')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    battle = args.project / 'workplace/probe-20261023/graphics-first/battle-r1'
    run, control = battle / 'owned-panel-r11', battle / 'owned-panel-r9'
    gui = args.project / 'workplace/player/gui/owned-panel-save-r4'
    for name in ('final.state', 'audio.pcm'):
        assert sha(run / name) == sha(control / name)
    files = lambda d: {p.name: sha(p) for p in d.iterdir() if p.is_file()}
    assert files(run / 'scratch') == files(control / 'scratch')
    result = {'status': 'PASS-scoped-owned-panel-staging', 'production': False, 'spec_status': 'DRAFT',
              'headless': audit_run(run), 'gui_save': audit_run(gui / 'save', True),
              'gui_reload': audit_run(gui / 'reload', True),
              'guest_isolation': {'state_sha256': sha(run / 'final.state'), 'pcm_sha256': sha(run / 'audio.pcm'),
                                  'scratch_files': len(files(run / 'scratch'))},
              'save_cycle': read(gui / 'save-cycle-audit.json'),
              'research_source_sha256': sha(args.project / 'tools/research-owned-scene.go'),
              'limits': ['Only character, army and their map return boundaries are covered.',
                         'Opening, other dialogs, mode changes and failure recovery remain DRAFT.',
                         'No new battle or RNG parity claim.']}
    assert args.out.parent.is_dir() and args.out.parent.stat().st_uid == 1000 and not args.out.exists()
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('headless', 'gui_save', 'gui_reload')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
