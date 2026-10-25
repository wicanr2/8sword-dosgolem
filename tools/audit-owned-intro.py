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


def audit_run(root, decode, gui=False, complete=True):
    receipt = read(root/'owned-intro-receipt.json')
    counts = receipt['commands']
    assert receipt['bound'] and receipt['retired'] and receipt['active_at_end'] == 0
    assert not receipt['renderer_reads_vga'] and not receipt['production']
    for key in ('native-mismatch-checks', 'writes-outside-command', 'unmapped-glyph', 'missing-hd-glyph'):
        assert counts.get(key, 0) == 0, (root, key, counts.get(key))
    revealed = counts.get('reveal-pixels', 0)
    assert revealed == counts.get('reveal-writes', 0) and 0 <= revealed <= 64000
    if complete:
        assert revealed == 64000 and counts['reveal-begin'] == counts['reveal-complete'] == 1
    assert counts['native-stable-checks'] > (20 if complete else 0)
    dispatch = read(root/'owned-dispatch-receipt.json')['counts']
    assert dispatch.get('intro-0e', 0) and dispatch.get('pam-0e', 0)
    if complete:
        assert dispatch.get('intro-13', 0)
    assert not any(n for key, n in dispatch.items() if key.startswith('fallback-') and key != 'fallback-03')
    events = [json.loads(line) for line in (root/'owned-intro-commands.jsonl').read_text().splitlines()]
    modes = [e for e in events if e['command'] == 'mode']
    assert sum(e['prelude_bridge'] for e in modes) <= 1
    if complete:
        assert sum(e['prelude_bridge'] for e in modes) == 1
    for before, after in zip(modes, modes[1:]):
        if after['prelude_bridge']:
            assert before['mode'] == 0x13 and after['mode'] == 0x0e
    rendered = list(decode(root/'presentation.frames.gz'))
    final = read(root/('gui-final.json' if gui else 'final.json'))
    assert len(rendered) == final['recorded_frames']
    if not gui:
        assert final['frame_pure_count'] == len(rendered)
        if complete:
            assert len(rendered) == 561
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
    if complete:
        assert required <= {c['kind'] for c in captures}
    visible = {c['kind'] for c in captures if c['actual_frame_ordinals']}
    if gui:
        assert {'publisher', 'title'} <= visible
        assert visible & {'museum-portrait', 'museum-right', 'museum-beam'}
        if complete:
            assert any(c.startswith('story-') and c.endswith('-text') for c in visible)
    return dict(frames=len(rendered), counts=counts, dispatch=dispatch, captures=captures,
                actual_visible_capture_kinds=sorted(visible), stream_sha256=sha(root/'presentation.frames.gz'))


def lifecycle(p, out):
    b = p/'workplace/probe-20261023/graphics-first/battle-r1'
    decode = runpy.run_path(str(p/'tools/audit-owned-modal.py'))['frames']
    files = lambda d: {q.name: sha(q) for q in d.iterdir() if q.is_file()}
    cases = {}
    for kind, requested in [('museum', 26000000), ('prelude', 44000000)]:
        run, control = (b/f'owned-intro-escape-{kind}-{side}-r1' for side in ('candidate', 'control'))
        for name in ('final.state', 'audio.pcm'):
            assert sha(run/name) == sha(control/name), (kind, name)
        assert files(run/'scratch') == files(control/'scratch')
        candidate_final, control_final = (read(d/'final.json') for d in (run, control))
        for field in ('file_ops', 'exec_log', 'input_events', 'steps', 'irq1_delivered', 'strings', 'clock_baseline'):
            assert candidate_final[field] == control_final[field], (kind, field)
        assert candidate_final['normal_input_replay'] and not candidate_final['guest_injection'] and not candidate_final['snapshot_loaded']
        escape = read(run/'intro-escape.json')
        assert escape == read(control/'intro-escape.json') and escape['requested_step'] == requested
        result = audit_run(run, decode, complete=False)
        kinds = {c['kind'] for c in result['captures']}
        assert ('museum-portrait' if kind == 'museum' else 'prelude-reveal') in kinds
        assert result['frames'] == control_final['recorded_frames'] == control_final['frame_pure_count']
        result.update(escape=escape, state_sha256=sha(run/'final.state'), pcm_sha256=sha(run/'audio.pcm'),
                      scratch_files=len(files(run/'scratch')))
        cases[kind] = result
    bad = b/'owned-intro-background-bad-r2'
    reference = b/'owned-intro-control-r19'
    fault = audit_run(bad, decode)
    for name in ('final.state', 'audio.pcm'):
        assert sha(bad/name) == sha(reference/name)
    assert files(bad/'scratch') == files(reference/'scratch')
    final = read(bad/'final.json')
    original_final = read(reference/'final.json')
    for field in ('file_ops', 'exec_log', 'input_events', 'steps', 'irq1_delivered', 'strings', 'clock_baseline'):
        assert final[field] == original_final[field], field
    assert final['intro_story']['background_error'] == '故事背景圖片 SHA-256 不符'
    assert final['intro_story']['hd_background'] is False and not final['intro_story']['load_error']
    asset = b/'owned-intro-story-background-bad-r1'
    original = p/'workplace/player/assets-painted-r48'
    base_files = files(original)
    changed = {name for name, digest in base_files.items() if sha(asset/name) != digest}
    assert changed == {'story-background.png'}
    failed = b/'owned-intro-background-bad-r1.log'
    assert 'invalid memory address or nil pointer dereference' in failed.read_text()
    assert 'image.(*RGBA).Bounds' in failed.read_text()
    assert not (b/'owned-intro-background-bad-r1/final.json').exists()
    before = reference.parent/'owned-intro-r22'
    for capture in fault['captures']:
        name = f'intro-{capture["kind"]}-owned.png'
        same = Image.open(bad/name).convert('RGBA').tobytes() == Image.open(before/name).convert('RGBA').tobytes()
        assert same == (not capture['kind'].startswith('story-')), capture['kind']
    gui_results = {}
    for name, stage, broken in [('owned-intro-escape-save-r1', 'museum-portrait', False),
                                ('owned-intro-background-bad-save-r2', 'story-1-text', True)]:
        root = p/'workplace/player/gui'/name
        phases = {}
        for phase in ('save', 'reload'):
            d = root/phase
            result = audit_run(d, decode, True, False)
            request = read(d/'owned-intro-escape-request.json')
            assert request['stage'] == stage
            assert stage in result['actual_visible_capture_kinds']
            status = read(d/'gui-final.json')['intro_story']
            assert bool(status['background_error']) == broken
            assert status['hd_background'] != broken and not status['load_error']
            phases[phase] = result
        phases['save_cycle'] = read(root/'save-cycle-audit.json')
        gui_results[name] = phases
    old, new = b/'owned-live-build-r23', b/'owned-live-build-r24'
    source_name = 'src/internal/eightsword/research_owned_intro.go'
    a, z = ((d/source_name).read_text() for d in (old, new))
    assert a == (b/'owned-live-build-r22'/source_name).read_text()
    # The fix guards optional asset pointers before assigning image.Image interfaces.
    split = lambda s: (s[:s.index('func (p *ownedIntroProbe) art()')], s[s.index('func (p *ownedIntroProbe) bind()'):])
    assert split(a) == split(z)
    assert (p/'tools/research-owned-intro.go').read_text().replace('//go:build ignore\n', '', 1).lstrip('\n') == z
    for name in ('src/tools/probe-owned.go', 'src/tools/gui-check.go', 'src/internal/eightsword/engine.go', 'source-inputs.json'):
        assert sha(old/name) == sha(new/name)
    for build in (old, new):
        manifest(build/'build-inputs.sha256', build/'src')
        manifest(build/'build-outputs.sha256', build)
    result = dict(status='PASS-scoped-owned-intro-escape-and-background-failure', production=False, spec_status='DRAFT',
                  escape_cases=cases, background_failure=fault, gui=gui_results,
                  source_sha256=sha(p/'tools/research-owned-intro.go'), fault=read(asset/'research-fault.json'),
                  negative_failure_log_sha256=sha(failed),
                  limits=['Two headless Escape phases and one actual GUI phase per asset condition are sampled.',
                          'One true background corruption only; other asset failures remain unverified.',
                          'Unknown operations, other dialogues and casting remain DRAFT; production is unchanged.'])
    assert not out.exists() and out.parent.stat().st_uid == 1000
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(status=result['status'], cases=list(cases), gui=list(gui_results), source_sha256=result['source_sha256']), ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--lifecycle', action='store_true', help='抽驗開場Esc、真正背景故障及其實際視窗存退讀')
    args = parser.parse_args()
    p = args.project
    if args.lifecycle:
        lifecycle(p, args.out)
        return
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
    # Natural r22 receipts describe this immutable build, independently of later tool edits.
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
                  manifests=checks, source_sha256=sha(new/'src/internal/eightsword/research_owned_intro.go'),
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
