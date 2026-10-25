#!/usr/bin/env python3
"""047 DRAFT：獨立核對直接攔截的單一常式輸出契約，不代替正常玩家驗收。"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import struct


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    p = args.project
    b = p/'workplace/probe-20261023/graphics-first/battle-r1/direct-planar-r2'
    report = json.loads((b/'call-contract-r4.json').read_text())
    fixtures = json.loads((b/'fixtures.json').read_text())
    assert report['status'] == 'PASS-single-routine-direct-source-command-contract'
    assert not report['production'] and not report['normal_player_route'] and not report['timer_irq_enabled']
    assert (b/'go-version-r4.txt').read_text().startswith('go version go1.24.13 linux/amd64')
    # Audit the immutable r4 program, independently of later tool annotations.
    assert sha(b/'probe-direct-r4.go') == '63510e6da295f98bf06798299c8f8a65fc5ff443368bedcf1baf29239b91d639'
    for line in (b/'build-r4.sha256').read_text().splitlines():
        digest, path = line.split('  ', 1)
        assert sha(b/Path(path).name) == digest
    expected, sources = set(), {}
    surfaces = {}
    for fixture in fixtures['fixtures']:
        raw = (b/fixture['file']).read_bytes()
        assert sha(b/fixture['file']) == fixture['sha256']
        w, h = struct.unpack_from('<HH', raw)
        assert len(raw) == 4+w*h*4 and (w, h) == (fixture['width_bytes'], fixture['height'])
        sources[fixture['name']] = fixture
        positions = [(0, 0)] + ([(80-w, 200-h)] if (w, h) != (80, 200) else [])
        for xbyte, y in positions:
            pixels = bytearray(640*200)
            area = w*h
            for row in range(h):
                for col in range(w*8):
                    offset, bit = row*w+col//8, 7-col%8
                    pixels[(y+row)*640+xbyte*8+col] = sum(((raw[4+plane*area+offset] >> bit)&1) << plane for plane in range(4))
            surfaces[fixture['name'], xbyte, y] = hashlib.sha256(pixels).hexdigest()
            expected.update((fixture['name'], xbyte, y, dest, flags)
                            for dest, flags in itertools.product((0xa000, 0xa400), (2, 0xcd7, 0x202)))
    seen = set()
    for case in report['cases']:
        command = case['command']
        source = sources[case['source']]
        key = case['source'], command['XByte'], command['Y'], command['Destination'], case['input_flags']
        assert key in expected and key not in seen
        seen.add(key)
        assert command['SourceSHA256'] == case['source_sha256'] == source['sha256']
        assert (command['WidthBytes'], command['Height']) == (source['width_bytes'], source['height'])
        assert case['original_steps'] == 32*source['height']+82 and case['original_cycles'] > 0
        assert case['original_vga_stores'] == 4*source['width_bytes']*source['height']
        assert case['replacement_emulated_steps'] == case['replacement_vga_stores'] == 0
        # r4 WatchReads bypasses planar VGA; its zero cannot prove no reads.
        for field in ('live_registers_equal', 'flags_equal', 'conventional_ram_equal', 'vga_control_equal',
                      'source_surface_equals_original', 'empty_return_rejected', 'replacement_vga_planes_unchanged'):
            assert case[field] is True, (key, field)
        assert case['original_ram_sha256'] == case['replacement_ram_sha256']
        assert case['original_surface_sha256'] == case['managed_surface_sha256'] == surfaces[case['source'], command['XByte'], command['Y']]
    assert seen == expected and len(seen) == 30
    assert report['pam_sha256'] == fixtures['pam_sha256'] == sha(p/'workplace/intake-20261023/sources/game/8sword/PAM.AY')
    result = dict(status='PASS-independent-direct-planar-contract', production=False, normal_player_route=False,
                  cases=len(seen), empty_return_negative_controls=len(seen), sources=sorted(sources),
                  original_steps=[min(c['original_steps'] for c in report['cases']), max(c['original_steps'] for c in report['cases'])],
                  original_vga_stores=sorted({c['original_vga_stores'] for c in report['cases']}),
                  replacement_emulated_steps=0, replacement_vga_stores=0,
                  report_sha256=sha(b/'call-contract-r4.json'), source_sha256=sha(b/'probe-direct-r4.go'),
                  historical_read_count_is_dynamic_evidence=False,
                  limits=report['limits'])
    assert not args.out.exists() and args.out.parent.stat().st_uid == 1000
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
