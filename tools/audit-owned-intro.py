#!/usr/bin/env python3
"""047 DRAFT：在 Pillow Docker 核對開場來源場景與正常視窗抽樣。"""
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


def manifest(path, root):
    lines = path.read_text().splitlines()
    for line in lines:
        digest, name = line.split('  ', 1)
        assert sha(root/name) == digest, (path, name)
    return len(lines)


def audit_run(root, decode, gui=False):
    receipt = read(root/'owned-intro-receipt.json')
    counts = receipt['commands']
    assert receipt['bound'] and receipt['retired'] and receipt['active_at_end'] == 0
    assert not receipt['renderer_reads_vga'] and not receipt['production']
    for key in ('native-mismatch-checks', 'writes-outside-command', 'unmapped-glyph', 'missing-hd-glyph'):
        assert counts.get(key, 0) == 0, (root, key, counts.get(key))
    assert counts['reveal-pixels'] == counts['reveal-writes'] == 64000
    assert counts['reveal-begin'] == counts['reveal-complete'] == 1
    assert counts['native-stable-checks'] > 20
    dispatch = read(root/'owned-dispatch-receipt.json')['counts']
    assert dispatch.get('intro-0e', 0) and dispatch.get('intro-13', 0) and dispatch.get('pam-0e', 0)
    assert not any(n for key, n in dispatch.items() if key.startswith('fallback-') and key != 'fallback-03')
    events = [json.loads(line) for line in (root/'owned-intro-commands.jsonl').read_text().splitlines()]
    modes = [e for e in events if e['command'] == 'mode']
    assert sum(e['prelude_bridge'] for e in modes) == 1
    for before, after in zip(modes, modes[1:]):
        if after['prelude_bridge']:
            assert before['mode'] == 0x13 and after['mode'] == 0x0e
    rendered = list(decode(root/'presentation.frames.gz'))
    final = read(root/('gui-final.json' if gui else 'final.json'))
    assert len(rendered) == final['recorded_frames']
    if not gui:
        assert final['frame_pure_count'] == len(rendered) == 561
    captures = []
    for event in events:
        if event['command'] != 'capture':
            continue
        kind = event['kind']
        own = Image.open(root/f'intro-{kind}-owned.png').convert('RGBA')
        legacy = Image.open(root/f'intro-{kind}-legacy.png').convert('RGBA')
        assert own.size == legacy.size == (1920, 1200)
        assert own.tobytes() == legacy.tobytes(), (root, kind)
        digest = hashlib.sha256(own.tobytes()).hexdigest()
        assert digest == event['rgba_sha256'] == event['legacy_rgba_sha256']
        assert event['different_pixels'] == 0
        visible = [n for n, step, h in rendered if step >= event['step'] and h == digest]
        captures.append(dict(kind=kind, pixels=2304000, rgba_sha256=digest, actual_frame_ordinals=visible))
    required = {'publisher', 'title', 'museum-left', 'museum-right', 'museum-portrait', 'museum-beam',
                'prelude-reveal', 'prelude-complete', *(f'story-{i}-text' for i in range(1, 6))}
    assert required <= {c['kind'] for c in captures}
    visible = {c['kind'] for c in captures if c['actual_frame_ordinals']}
    if gui:
        assert {'publisher', 'title'} <= visible
        assert visible & {'museum-portrait', 'museum-right', 'museum-beam'}
        assert any(c.startswith('story-') and c.endswith('-text') for c in visible)
    return dict(frames=len(rendered), counts=counts, dispatch=dispatch, captures=captures,
                actual_visible_capture_kinds=sorted(visible), stream_sha256=sha(root/'presentation.frames.gz'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    p = args.project
    b = p/'workplace/probe-20261023/graphics-first/battle-r1'
    run, control = b/'owned-intro-r22', b/'owned-intro-control-r19'
    gui = p/'workplace/player/gui/owned-intro-save-r2'
    decode = runpy.run_path(str(p/'tools/audit-owned-modal.py'))['frames']
    for name in ('final.state', 'audio.pcm'):
        assert sha(run/name) == sha(control/name), name
    files = lambda d: {q.name: sha(q) for q in d.iterdir() if q.is_file()}
    assert files(run/'scratch') == files(control/'scratch')
    old, new = b/'owned-live-build-r19', b/'owned-live-build-r22'
    for name in ('src/tools/probe-owned.go', 'src/internal/eightsword/engine.go',
                 'src/internal/eightsword/research_owned_scene.go', 'source-inputs.json'):
        assert sha(old/name) == sha(new/name), name
    source = (new/'src/internal/eightsword/research_owned_intro.go').read_text()
    assert (p/'tools/research-owned-intro.go').read_text().replace('//go:build ignore\n', '', 1).lstrip('\n') == source
    pure = source[source.index('func renderOwnedIntro('):source.index('type ownedIntroProbe struct')]
    for token in ('Oracle', '.Screen(', '.ScreenRGB(', 'PlanarBytePixels', 'researchOwnedReference'):
        assert token not in pure
    assert 'bridge := old.Mode == 0x13 && old.Prelude && v.Mode == 0xe' in source
    production = p/'workplace/player/build-friendly21-r1'
    checks = dict(production_sources=manifest(production/'build-inputs.sha256', p),
                  production_programs=manifest(production/'build-outputs.sha256', p/'workplace/player'),
                  research_sources=manifest(new/'build-inputs.sha256', new/'src'),
                  research_programs=manifest(new/'build-outputs.sha256', new))
    for name in ('dosgolem-page-files.sha256', 'dosgolem-presentation-files.sha256'):
        checks[name] = manifest(p/'tools'/name, p/'workplace/dosgolem')
    result = dict(status='PASS-scoped-owned-natural-intro', production=False, spec_status='DRAFT',
                  headless=audit_run(run, decode), gui_save=audit_run(gui/'save', decode, True),
                  gui_reload=audit_run(gui/'reload', decode, True),
                  state_sha256=sha(run/'final.state'), pcm_sha256=sha(run/'audio.pcm'),
                  scratch_files=len(files(run/'scratch')), save_cycle=read(gui/'save-cycle-audit.json'),
                  manifests=checks, source_sha256=sha(p/'tools/research-owned-intro.go'),
                  ida_evidence_sha256=sha(p/'workplace/probe-20261023/graphics-first/ida-intro-graphics-inventory-r3.json'),
                  limits=['Natural complete opening only; early Escape and broken assets are not verified here.',
                          'RNG seed unknown; state equality establishes presentation isolation only.',
                          'Unknown operations, other dialogues, casting and failure recovery remain DRAFT.',
                          'Capture images and actual Draw matches are listed separately; transition timing is sampled.'])
    assert args.out.parent.is_dir() and args.out.parent.stat().st_uid == 1000 and not args.out.exists()
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('headless', 'gui_save', 'gui_reload', 'save_cycle')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
