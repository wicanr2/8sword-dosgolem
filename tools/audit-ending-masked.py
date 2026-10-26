#!/usr/bin/env python3
"""053 DRAFT：獨立核對六平面Go接管、原版讀回與完整結局成對輸出。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import statistics

from PIL import __version__


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    a = parser.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    b = a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    preparation = read(b/'masked-build-r1/preparation.json')
    assert preparation['masked_source_sha256'] == sha(a.project/'tools/research-ending-masked.go')
    assert preparation['tool_sha256'] == sha(a.project/'tools/prepare-ending-masked.py')
    for name, expected in preparation['files'].items():
        assert sha(b/'masked-build-r1'/name) == expected
    source = (b/'masked-build-r1/ending-masked.go').read_text()
    assert '.Step(' not in source and '.Run(' not in source and '.Stub(' not in source
    assert '&^mask' in source and 'm.ReadHostPlanar(' in source
    call = read(b/'masked-call-audit-r1.json')
    assert len(call['full_cases']) == 12 and len(call['run_cases']) == 12
    for row in call['full_cases']+call['run_cases']:
        assert row['full_state_equal'] and row['ordered_events_equal']
        assert row['replacement_x86_pixel_instructions'] == 0
    assert sum(r['partial_row'] for r in call['run_cases']) == 6
    assert all(r['tiny_quota_rejected_without_effects'] for r in call['run_cases'])
    catalog = read(b/'source.json')
    sources = {r['record_sha256'] for r in catalog['records'] if r['color_variant'] and r['planes'] == 6}
    for row in call['full_cases']:
        assert row['source_sha256'] in sources and sha(b/row['source']) == row['source_sha256']
    normal_dir, fast_dir = b/'masked-control-r1', b/'masked-direct-r1'
    normal, fast = read(normal_dir/'owned-result.json'), read(fast_dir/'owned-result.json')
    assert normal['direct_enabled'] is False and fast['direct_enabled'] is True
    assert normal['production'] is False and fast['production'] is False
    assert fast['steps'] == 96283141 and fast['clock_cycles_per_ms'] == 3000
    assert '回傳碼 0' in fast['run_error']
    assert fast['unknown_writes'] == {} and fast['unimplemented'] == []
    for key in normal:
        if key not in ('counts', 'direct_enabled'):
            assert normal[key] == fast[key], key
    for key, value in normal['counts'].items():
        assert fast['counts'][key] == value, key
    prior = read(b/'direct-direct-r3/owned-result.json')
    for key, value in prior['counts'].items():
        assert fast['counts'][key] == value, ('previous direct route', key)
    masked = {k: v for k, v in fast['counts'].items() if k.startswith('masked-')}
    assert masked == {'masked-full-fallback-quota-or-event': 1462, 'masked-indexed-bytes': 4296701,
        'masked-partial-row-batches': 6614, 'masked-run-batches': 290354,
        'masked-run-fallback-quota-or-event': 6388, 'masked-skipped-x86': 38670309}
    assert normal['flips'] == 1049 and normal['frame_purity'] == 41
    assert normal['counts']['native-full-frame-checked'] == 1050
    tree = lambda root: {str(p.relative_to(root)): sha(p) for p in root.rglob('*')
                         if p.is_file() and p.name != 'owned-result.json'}
    originals, replaced = tree(normal_dir), tree(fast_dir)
    assert originals == replaced == tree(b/'direct-control-r3'), 'complete outputs or original baseline differ'
    assert sha(fast_dir/'final.state') == '6ba949eba04aacfe090837dced381e1caaaeab341cda974aaff53410b7f46919'
    assert (fast_dir/'before.state').read_bytes() == (fast_dir/'after.state').read_bytes()
    # Reuse the already independent Pillow reconstruction, pinned to its actual source.
    verifier_path = a.project/'tools/audit-ending-direct.py'
    previous_audit = read(b/'direct-runtime-audit-r1.json')
    assert sha(verifier_path) == previous_audit['tool_sha256']
    spec = importlib.util.spec_from_file_location('ending_direct_reference', verifier_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    hd = module.verify_rendering(b, normal_dir)
    assert len(hd) == 12
    assert len(call['benchmarks']) == 9
    benchmark = []
    for name in sorted({r['source'] for r in call['benchmarks']}):
        rows = [r for r in call['benchmarks'] if r['source'] == name]
        assert len(rows) == 3 and all(r['calls'] == 8 for r in rows)
        benchmark.append(dict(source=name, native_ns=statistics.median(r['native_ns_per_call'] for r in rows),
            go_ns=statistics.median(r['go_ns_per_call'] for r in rows), median_ratio=statistics.median(r['ratio'] for r in rows)))
    result = dict(schema=1, spec='053', production=False, status='research-native-Go-masked-ending-verified',
        tool_sha256=sha(Path(__file__)), independent_verifier_sha256=sha(verifier_path),
        source_preparation_sha256=sha(b/'masked-build-r1/preparation.json'),
        binary_sha256=sha(b/'ending-masked-scene-r1'), call_binary_sha256=sha(b/'ending-masked-call-r1'),
        call_report_sha256=sha(b/'masked-call-audit-r1.json'), control_report_sha256=sha(normal_dir/'owned-result.json'),
        direct_report_sha256=sha(fast_dir/'owned-result.json'), full_state_sha256=sha(fast_dir/'final.state'),
        full_call_cases=12, masked_run_cases=12, independent_native_frames=41, independent_hd_frames=hd,
        matched_files=len(originals), matched_png=164, masked_counts=masked,
        total_skipped_x86=masked['masked-skipped-x86']+fast['counts']['direct-skipped-x86-instructions'],
        benchmark=benchmark, go='1.24.13', pillow=__version__,
        limits=['Standalone same-clock PAE diagnostic pair, not normal PAM handoff or natural completion.',
                'Admitted masked whole calls and partial rows use native Go; glyphs, clear/copy and event-boundary residues remain native.',
                'Historical owned-inputs-r1 used solely for CPU/scene oracle. END7 r1 art is rejected, not promoted or approved.',
                'No production, GUI, PCM listening, save/reload or whole-game FPS claim.'])
    with a.out.open('x') as f:
        f.write(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(files=len(originals), png=164, masked_skipped=masked['masked-skipped-x86'],
        total_skipped=result['total_skipped_x86'], sha256=sha(a.out))))


if __name__ == '__main__':
    main()
