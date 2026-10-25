#!/usr/bin/env python3
"""047 DRAFT：主選單、新遊戲交接與地圖重畫的獨立逐幀核對。"""
import argparse
import hashlib
import json
from pathlib import Path
import runpy

from PIL import Image


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_run(root, required, decode, gui=False):
    events = [json.loads(line) for line in (root/'owned-commands.jsonl').read_text().splitlines()]
    pending, intervals = None, []
    for event in events:
        if event['command'] == 'panel-begin':
            assert pending is None
            pending = event
        elif event['command'] == 'panel-commit':
            assert pending and event['kind'] == pending['kind'] and event['start_step'] == pending['step']
            assert event['primitive_pending'] == 0 and pending['step'] < event['step']
            intervals.append(dict(kind=event['kind'], begin=pending['step'], commit=event['step'], staged_frames=0))
            pending = None
    receipt = read(root/'owned-receipt.json')
    assert pending is None and receipt['panel_at_end'] is None and receipt['active_at_end'] == 0
    assert receipt['commands'].get('writes-outside-command', 0) == 0
    assert not any('reject' in key for key in receipt['commands'])
    assert required <= {x['kind'] for x in intervals}
    rendered = list(decode(root/'presentation.frames.gz'))
    previous = None
    for ordinal, step, digest in rendered:
        for interval in intervals:
            if interval['begin'] <= step < interval['commit']:
                assert previous == digest, (root, ordinal, interval)
                interval['staged_frames'] += 1
        previous = digest
    staged = sum(x['staged_frames'] for x in intervals)
    assert staged <= receipt['commands'].get('panel-staged-frames', 0)
    if not gui:
        assert staged > 0
    captures = []
    for event in events:
        if event['command'] != 'completed-capture' or not event['kind'].startswith('panel-'):
            continue
        name = event['kind']
        own = Image.open(root/(name+'-owned.png')).convert('RGBA')
        legacy = Image.open(root/(name+'-legacy.png')).convert('RGBA')
        assert own.size == legacy.size == (1920, 1200) and own.tobytes() == legacy.tobytes()
        digest = hashlib.sha256(own.tobytes()).hexdigest()
        assert digest == event['rgba_sha256'] == event['legacy_rgba_sha256'] and event['different_pixels'] == 0
        next_begin = min((x['begin'] for x in intervals if x['begin'] > event['step']), default=2**64)
        visible = [ordinal for ordinal, step, value in rendered if event['step'] <= step < next_begin and value == digest]
        if gui:
            assert visible, (root, name, 'completed scene absent from actual Draw')
        captures.append(dict(kind=name, full_pixels=2304000, rgba_sha256=digest, actual_frame_ordinals=visible))
    final = read(root/('gui-final.json' if gui else 'final.json'))
    assert len(rendered) == final['recorded_frames']
    if not gui:
        assert final['frame_pure_count'] == len(rendered) == 454
    return dict(frames=len(rendered), staged_frames=staged, intervals=intervals, completed_scenes=captures,
                stream_sha256=sha(root/'presentation.frames.gz'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    p = args.project
    battle = p/'workplace/probe-20261023/graphics-first/battle-r1'
    run, control = battle/'owned-main-r15', battle/'owned-main-control-r14'
    gui = p/'workplace/player/gui/owned-main-save-r1'
    decode = runpy.run_path(str(p/'tools/audit-owned-modal.py'))['frames']
    for name in ('final.state', 'audio.pcm'):
        assert sha(run/name) == sha(control/name)
    files = lambda d: {q.name: sha(q) for q in d.iterdir() if q.is_file()}
    assert files(run/'scratch') == files(control/'scratch')
    old, new = battle/'owned-live-build-r14', battle/'owned-live-build-r15'
    assert (old/'src/internal/eightsword/research_owned_scene.go').read_bytes() == (battle/'owned-live-build-r13/src/internal/eightsword/research_owned_scene.go').read_bytes()
    for name in ('source-inputs.json', 'src/tools/probe-owned.go', 'src/tools/gui-check.go', 'src/internal/eightsword/engine.go'):
        assert sha(old/name) == sha(new/name), name
    source = (new/'src/internal/eightsword/research_owned_scene.go').read_text()
    assert (p/'tools/research-owned-scene.go').read_text().replace('//go:build ignore\n', '', 1).lstrip('\n') == source
    pure = source[source.index('func renderOwnedScene('):source.index('func (e *Engine) ResearchOwnedScene(')]
    for token in ('Oracle', '.Screen(', '.ScreenRGB(', 'PlanarBytePixels', '.Before', '.owners'):
        assert token not in pure
    required = {'main-menu', 'music-menu', 'new-game-confirm', 'main-menu-restore', 'first-map', 'map-refresh'}
    result = dict(status='PASS-scoped-owned-main-menu-staging', production=False, spec_status='DRAFT',
                  headless=audit_run(run, required | {'side-menu', 'army', 'character'}, decode),
                  gui_save=audit_run(gui/'save', required | {'character', 'system'}, decode, True),
                  gui_reload=audit_run(gui/'reload', {'main-menu', 'first-map', 'character'}, decode, True),
                  state_sha256=sha(run/'final.state'), pcm_sha256=sha(run/'audio.pcm'), scratch_files=len(files(run/'scratch')),
                  save_cycle=read(gui/'save-cycle-audit.json'), research_source_sha256=sha(p/'tools/research-owned-scene.go'),
                  limits=['PAM source commands only; PREDELLA opening is not yet owned.',
                          'No new RNG, music arrangement, dismissal or casting rule claim.',
                          'Unknown operations, display-mode changes and failure recovery remain DRAFT.'])
    assert result['gui_save']['staged_frames'] > 0
    assert args.out.parent.is_dir() and args.out.parent.stat().st_uid == 1000 and not args.out.exists()
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('headless', 'gui_save', 'gui_reload', 'save_cycle')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
