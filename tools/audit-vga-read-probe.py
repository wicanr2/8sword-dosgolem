#!/usr/bin/env python3
"""047 DRAFT：獨立重建延遲背板，並核對正常路徑觀測前後狀態。"""
import argparse
import gzip
import hashlib
import itertools
import json
import os
from pathlib import Path
import struct


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def stream_sha(stream):
    digest = hashlib.sha256()
    for raw in iter(lambda: stream.read(1024*1024), b''):
        digest.update(raw)
    return digest.hexdigest()


def tree(path):
    return {str(p.relative_to(path)): sha(p.read_bytes()) for p in sorted(path.rglob('*')) if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000
    p = args.project
    b = p/'workplace/probe-20261023/graphics-first/battle-r1'
    report = json.loads((b/'shadow-contract-r3/receipt-uncharged.json').read_text())
    core = b/'core-direct-r1'
    source_manifest = json.loads((core/'source-manifest.json').read_text())
    assert sha((core/'video-read.patch').read_bytes()) == source_manifest['patch_sha256']
    for name, digest in source_manifest['base_inputs'].items():
        assert sha((p/'workplace/dosgolem'/name).read_bytes()) == digest
        if name not in source_manifest['changed']:
            assert sha((core/'src'/name).read_bytes()) == digest
    for name, digest in source_manifest['changed'].items():
        assert sha((core/'src'/name).read_bytes()) == digest
    assert set(tree(core/'src')) == set(source_manifest['base_inputs']) | set(source_manifest['changed'])
    assert report['status'] == 'PASS-lazy-planar-backing-native-consumer'
    assert not report['production'] and not report['normal_player_route'] and not report['timer_irq_enabled']
    fixture_root = b/'direct-planar-r2'
    fixtures = json.loads((fixture_root/'fixtures.json').read_text())['fixtures']
    expected, surfaces = set(), {}
    for source in fixtures:
        raw = (fixture_root/source['file']).read_bytes()
        assert sha(raw) == source['sha256']
        w, h = struct.unpack_from('<HH', raw)
        assert len(raw) == 4+w*h*4
        positions = [(0, 0)]+([(80-w, 200-h)] if (w, h) != (80, 200) else [])
        for (x, y), dest in itertools.product(positions, (0xa000, 0xa400)):
            planes = [bytearray(65536) for _ in range(4)]
            start = (dest-0xa000)*16
            base = start+y*80+x
            for plane in range(4):
                for row in range(h):
                    at = 4+plane*w*h+row*w
                    planes[plane][base+row*80:base+row*80+w] = raw[at:at+w]
            # One read loads all latches; the next write retains those old low bits.
            planes[0][base+1] = 0xa0 | (planes[0][base] & 15)
            target = 0x4000 if dest == 0xa000 else 0
            for plane in planes:
                plane[target:target+16000] = plane[start:start+16000]
            surfaces[source['name'], x, y, dest] = [sha(bytes(a)) for a in planes]
            for cost in (False, True):
                expected.add((source['name'], x, y, dest, cost))
    seen = set()
    for case in report['cases']:
        key = (case['source'], case['x_byte'], case['y'], case['destination'], case['dosbox_cost'])
        assert key not in seen
        seen.add(key)
        assert case['all_planes_cpu_ram_control_equal']
        assert case['native_ram_sha256'] == case['direct_ram_sha256']
        assert case['native_planes_sha256'] == case['direct_planes_sha256'] == surfaces[key[:-1]]
        for name in ('opaque_vga_reads', 'replacement_draw_steps', 'replacement_draw_vga_writes',
                     'materialized_before_read', 'remaining'):
            assert case[name] == 0, (key, name)
        assert case['copy_vga_reads'] == 16000
        assert case['positive_read_materialized'] == case['positive_write_materialized'] == case['write_fills'] == 1
        assert case['pending_after_command'] == case['materialized_total'] == case['width_bytes']*case['height']
        assert case['read_fills']+case['write_fills'] == case['materialized_total']
    assert seen == expected and len(seen) == 20
    build = json.loads((b/'shadow-contract-r3/build.json').read_text())
    assert build['go'].startswith('go version go1.24.13 linux/amd64')
    for name, digest in build['files'].items():
        assert sha((b/'shadow-contract-r3'/name).read_bytes()) == digest
    base, candidate = b/'owned-hire-baseline-r1', b/'owned-hire-vga-read-r2'
    comparisons = {}
    for name in ('final.state', 'audio.pcm', 'commands.jsonl', 'frames.jsonl', 'owned-commands.jsonl',
                 'owned-intro-commands.jsonl', 'intro-escape.json'):
        left, right = (base/name).read_bytes(), (candidate/name).read_bytes()
        assert left == right, name
        comparisons[name] = sha(right)
    with gzip.open(base/'presentation.frames.gz', 'rb') as f:
        left = stream_sha(f)
    with gzip.open(candidate/'presentation.frames.gz', 'rb') as f:
        right = stream_sha(f)
    assert left == right
    comparisons['decompressed_presentation_frames'] = right
    assert tree(base/'scratch') == tree(candidate/'scratch')
    original, observed = [json.loads((root/'final.json').read_text()) for root in (base, candidate)]
    assert original == observed
    assert observed['recorded_frames'] == 542
    trace = json.loads((candidate/'vga-reads.json').read_text())
    assert not trace['production'] and not trace['drawing_replaced']
    assert trace['total'] > 0 and sum(s['Count'] for s in trace['sites']) == trace['total']
    assert sum(trace['classes'].values()) == trace['total']
    assert trace['classes'].get('opaque-four-plane-bitmap', 0) == 0
    clock_root = b/'shadow-contract-r3'
    clock = json.loads((clock_root/'receipt-clock.json').read_text())
    assert clock['clock_accounting'] and clock['timer_irq_enabled']
    assert not clock['normal_player_route'] and not clock['production']
    clock_seen = set()
    for case in clock['cases']:
        key = (case['source'], case['x_byte'], case['y'], case['destination'], case['dosbox_cost'])
        assert key not in clock_seen
        clock_seen.add(key)
        assert case['clock_accounting'] and case['cycle_clock_enabled'] == case['dosbox_cost']
        assert case['native_final_steps'] == case['direct_final_steps']
        assert case['native_final_cycles'] == case['direct_final_cycles']
        assert case['native_frames'] == case['direct_frames'] == 0
        assert case['native_ticks'] == case['direct_ticks'] == 0
        assert case['replacement_draw_steps'] == case['replacement_draw_vga_writes'] == 0
        assert case['copy_emulated_steps'] == 32 and case['copy_vga_reads'] == 16000
        assert case['native_planes_sha256'] == case['direct_planes_sha256'] == surfaces[key[:-1]]
        assert case['native_ram_sha256'] == case['direct_ram_sha256']
        assert case['all_planes_cpu_ram_control_equal'] and case['remaining'] == 0
    assert clock_seen == expected
    core_clock = b/'core-direct-r4'
    clock_sources = json.loads((core_clock/'source-manifest.json').read_text())
    for name, digest in clock_sources['changed'].items():
        assert sha((core_clock/'src'/name).read_bytes()) == digest
    for name, digest in clock_sources['base_inputs'].items():
        assert sha((p/'workplace/dosgolem'/name).read_bytes()) == digest
        if name not in clock_sources['changed']:
            assert sha((core_clock/'src'/name).read_bytes()) == digest
    clock_build = json.loads((clock_root/'build.json').read_text())
    for name, digest in clock_build['files'].items():
        assert sha((clock_root/name).read_bytes()) == digest
    tests = (core_clock/'event-budget-tests-r1.log').read_text()
    assert sum(line.startswith('--- PASS: TestResearchHostWork') for line in tests.splitlines()) == 3
    assert tests.count('--- PASS: TestResearchHostWorkNativeEventsAtExactBoundary/') == 12
    assert '\nFAIL' not in tests and '\nPASS\n' in tests
    result = dict(schema=1, status='PASS-lazy-backing-and-read-observer-isolation', production=False,
                  native_consumer_cases=len(seen), normal_route_frames=542,
                  clock_accounted_consumer_cases=len(clock_seen), event_boundary_cases=12,
                  normal_route_drawing_replaced=False, paired_hashes=comparisons,
                  scratch_files=len(tree(candidate/'scratch')), total_reads=trace['total'],
                  read_classes=trace['classes'], read_sites=len(trace['sites']),
                  shadow_receipt_sha256=sha((b/'shadow-contract-r3/receipt-uncharged.json').read_bytes()),
                  clock_receipt_sha256=sha((clock_root/'receipt-clock.json').read_bytes()),
                  read_receipt_sha256=sha((candidate/'vga-reads.json').read_bytes()))
    with args.out.open('x') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
