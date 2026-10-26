#!/usr/bin/env python3
"""053 DRAFT：以原始MZ重定位與字串核對PAM靜態結局呼叫，不冒稱動態交接。"""
import argparse
import hashlib
import json
import os
import struct
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000
    assert not args.out.exists() and args.out.parent.stat().st_uid == 1000
    root = args.project
    batch = root/'workplace/probe-20261023/graphics-first/ending-hd-r1/handoff-ida-r1'
    evidence = json.loads((batch/'ida-handoff-r1.json').read_text())
    source = root/'workplace/intake-20261023/sources/game/8sword/PAM.AY'
    database = root/'workplace/probe-20261023/text-first/PAM.i64'
    tool = root/'tools/export-ending-handoff-ida.py'
    assert evidence['schema'] == 1 and evidence['tool'] == 'IDA 9.4' and evidence['uid'] == 1000
    assert evidence['function_count'] == 521
    assert evidence['source_sha256'] == sha(source)
    assert evidence['database_sha256'] == sha(database)
    assert evidence['tool_sha256'] == sha(tool) == sha(batch/'export-at-run.py')
    raw = source.read_bytes()
    assert raw[:2] == b'MZ'
    header = struct.unpack_from('<H', raw, 8)[0]*16
    count = struct.unpack_from('<H', raw, 6)[0]
    table = struct.unpack_from('<H', raw, 24)[0]
    assert header == 0x1470 and count == 1301
    relocated = bytearray(raw)
    for off, seg in struct.iter_unpack('<HH', raw[table:table+count*4]):
        at = header+seg*16+off
        struct.pack_into('<H', relocated, at, (struct.unpack_from('<H', raw, at)[0]+0x1000)&65535)
    checked = changed = 0
    for fn in evidence['bodies']:
        for row in fn.get('lines', []):
            off = row['original_file_offset']
            data = bytes.fromhex(row['bytes'])
            assert off >= header and row['ida_linear'] == off-header+0x10000
            assert data == relocated[off:off+len(data)]
            checked += 1
            changed += data != raw[off:off+len(data)]
    assert checked == 2512 and changed == 89
    main_fn = next(x for x in evidence['bodies'] if x.get('start') == 0x1020e)
    lines = {x['ida_linear']: x for x in main_fn['lines']}
    # Fixed raw far-call and push sequences support these six argv values.
    # IDA names alone are not used as proof of the ABI or command tail.
    calls = []
    for i, at in enumerate([0x102c0, 0x10302, 0x10344, 0x10386, 0x103c8, 0x1040a]):
        off = at-0x10000+header
        assert raw[off:off+5] == bytes.fromhex('9aae338716')
        assert lines[at]['bytes'] == '9aae338726'
        block = raw[off-44:off]
        assert block[:4] == bytes.fromhex('2bc05050')
        strings, offsets = [], []
        for j in range(8):
            instr = block[4+j*5:9+j*5]
            assert instr[0] == 0xb8 and instr[3:] == bytes.fromhex('1e50')
            pointer = struct.unpack_from('<H', instr, 1)[0]
            # DGROUP IDA base 0x2D780; keep file offset separate.
            source_off = 0x2d780+pointer-0x10000+header
            strings.append(raw[source_off:raw.index(0, source_off)].decode('ascii'))
            offsets.append(source_off)
        values = strings[::-1]
        assert values[:2] == ['pae.ay', 'pae.ay']
        expected = [('v', 'a'), ('h', 'a'), ('v', 'r'), ('h', 'r'), ('v', 'q'), ('h', 'q')][i]
        assert values[2:] == [*expected, 'y', 'a', 'n', 'g']
        condition = raw[off-58:off-44]
        field1, field2 = [1, 3][i % 2], [1, 2, 3][i // 2]
        assert condition == bytes.fromhex('833e8474')+bytes([field1, 0x75, 0x3b])+bytes.fromhex('833e8674')+bytes([field2, 0x75, 0x34])
        calls.append(dict(ida_linear=at, original_file_offset=off,
                          condition_ds_offsets={'0x7484': field1, '0x7486': field2},
                          path=values[0], argv=values[1:], pointer_string_file_offsets=offsets[::-1]))
    output = dict(schema=1, spec='053', production=False, status='verified-static-PAM-ending-callers',
                  tool_sha256=sha(Path(__file__)), ida_report_sha256=sha(batch/'ida-handoff-r1.json'),
                  source_sha256=sha(source), database_sha256=sha(database),
                  ida_tool_sha256=sha(tool), checked_instructions=checked,
                  relocated_instruction_lines=changed, mz_relocations=count,
                  ida_image_base=0x10000, mz_header_bytes=header, calls=calls,
                  limits=['Static source/ABI evidence only; actual PAE load segment remains unknown.',
                          'Field meanings, game completion and normal GUI handoff are not established.',
                          'IDA relocated bytes differ from file bytes at declared MZ relocation words.'])
    with args.out.open('x') as handle:
        handle.write(json.dumps(output, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(instructions=checked, relocation_lines=changed, callers=len(calls), sha256=sha(args.out))))


if __name__ == '__main__':
    main()
