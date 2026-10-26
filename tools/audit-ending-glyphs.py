#!/usr/bin/env python3
"""053 DRAFT：核對Go字模列批次與完整結局，不擴張為正式交接驗收。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

from PIL import __version__


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    b = a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    prep = read(b/'glyph-build-r1/preparation.json')
    assert prep['tool_sha256'] == sha(a.project/'tools/prepare-ending-glyphs.py')
    assert prep['glyph_source_sha256'] == sha(a.project/'tools/research-ending-glyphs.go')
    for file, expected in prep['files'].items():
        assert sha(b/'glyph-build-r1'/file) == expected
    source = (b/'glyph-build-r1/ending-glyphs.go').read_text()
    assert '.Step(' not in source and '.Run(' not in source and '.Stub(' not in source
    calls = read(b/'glyph-call-audit-r1.json')
    assert len(calls['cases']) == 24
    assert {r['source'] for r in calls['cases']} == {'CJK-index0', 'CJK-comma', 'ASCII-space', 'ASCII-A'}
    assert {(r['fg'], r['bg']) for r in calls['cases']} == {(14, 255), (0, 0), (15, 4)}
    assert {r['destination'] for r in calls['cases']} == {0xa000, 0xa400}
    for row in calls['cases']:
        assert row['full_machine_equal'] and row['ordered_events_equal'] and row['short_quota_rejected']
        assert row['rows'] == 15 and row['replacement_x86_pixel_instructions'] == 0
    control, direct = b/'glyph-control-r1', b/'glyph-direct-r1'
    normal, fast = read(control/'owned-result.json'), read(direct/'owned-result.json')
    assert normal['direct_enabled'] is False and fast['direct_enabled'] is True
    assert fast['steps'] == 96283141 and fast['clock_cycles_per_ms'] == 3000
    assert '回傳碼 0' in fast['run_error']
    assert fast['unknown_writes'] == {} and fast['unimplemented'] == []
    for key in normal:
        if key not in ('counts', 'direct_enabled'):
            assert normal[key] == fast[key], key
    for key, value in normal['counts'].items():
        assert fast['counts'][key] == value, key
    previous = read(b/'masked-direct-r1/owned-result.json')
    for key, value in previous['counts'].items():
        assert fast['counts'][key] == value, ('previous native Go', key)
    glyph = {k: v for k, v in fast['counts'].items() if k.startswith('glyph-')}
    assert glyph == {'glyph-ascii-rows': 201800, 'glyph-cjk-rows': 115921,
        'glyph-fallback-quota-or-event': 1959, 'glyph-go-batches': 23055,
        'glyph-go-rows': 317721, 'glyph-skipped-x86': 11211126}
    native_rows = (normal['counts']['cjk']+normal['counts']['ascii'])*15-glyph['glyph-go-rows']
    assert native_rows == 1959
    tree = lambda root: {str(p.relative_to(root)): sha(p) for p in root.rglob('*')
                         if p.is_file() and p.name != 'owned-result.json'}
    outputs = tree(control)
    assert outputs == tree(direct) == tree(b/'masked-control-r1'), 'complete output trees differ'
    assert sha(direct/'final.state') == '6ba949eba04aacfe090837dced381e1caaaeab341cda974aaff53410b7f46919'
    assert (direct/'before.state').read_bytes() == (direct/'after.state').read_bytes()
    verifier = a.project/'tools/audit-ending-direct.py'
    assert sha(verifier) == read(b/'direct-runtime-audit-r1.json')['tool_sha256']
    spec = importlib.util.spec_from_file_location('ending_glyph_reference', verifier)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    hd = module.verify_rendering(b, control)
    assert len(hd) == 12
    total = glyph['glyph-skipped-x86']+fast['counts']['masked-skipped-x86']+fast['counts']['direct-skipped-x86-instructions']
    report = dict(schema=1, spec='053', production=False, status='research-native-Go-ending-glyphs-verified',
        tool_sha256=sha(Path(__file__)), verifier_sha256=sha(verifier),
        preparation_sha256=sha(b/'glyph-build-r1/preparation.json'), binary_sha256=sha(b/'ending-glyph-scene-r1'),
        call_binary_sha256=sha(b/'ending-glyph-call-r1'), call_report_sha256=sha(b/'glyph-call-audit-r1.json'),
        control_report_sha256=sha(control/'owned-result.json'), direct_report_sha256=sha(direct/'owned-result.json'),
        full_state_sha256=sha(direct/'final.state'), controlled_calls=24, matched_files=len(outputs), matched_png=164,
        independent_native_frames=41, independent_hd_frames=hd, glyph_counts=glyph,
        native_boundary_rows=native_rows, total_skipped_x86=total, go='1.24.13', pillow=__version__,
        limits=['Standalone same-clock diagnostic, not normal PAM handoff or natural completion.',
                'Opaque backgrounds verified in controlled calls; actual ending sample uses transparent backgrounds.',
                'Clear/copy, glyph boundary rows and outer control still have native x86 work.',
                'Historical rejected END7 art retained solely as technical oracle; no art approval or promotion.',
                'No production, GUI, save/reload, PCM listening or overall FPS claim.'])
    with a.out.open('x') as f:
        f.write(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(files=len(outputs), png=164, glyph_skipped=glyph['glyph-skipped-x86'],
        total_skipped=total, native_boundary_rows=native_rows, sha256=sha(a.out))))


if __name__ == '__main__':
    main()
