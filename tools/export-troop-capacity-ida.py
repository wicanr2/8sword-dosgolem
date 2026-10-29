"""030 DRAFT: bounded roster, recruitment and save-capacity evidence, no renaming."""
import hashlib
import json
import os
from pathlib import Path

import ida_auto
import ida_bytes
import ida_funcs
import ida_loader
import ida_segment
import idaapi
import idautils
import idc


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert os.getuid() == 1000 and idaapi.get_kernel_version() == '9.4'
source, db = Path('/game/PAM.AY'), Path('/source/PAM.i64')
assert sha(source) == '83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
assert sha(db) == 'a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac'
ida_auto.auto_wait()
raw = source.read_bytes()
header = int.from_bytes(raw[8:10], 'little') * 16
functions = list(idautils.Functions())
assert len(functions) == 521


def line(ea):
    return dict(ida_linear=ea, file_offset=ida_loader.get_fileregion_offset(ea),
                bytes=ida_bytes.get_bytes(ea, idc.get_item_size(ea)).hex(),
                instruction=idc.generate_disasm_line(ea, 0),
                operands=[dict(index=i, type=idc.get_operand_type(ea, i), value=idc.get_operand_value(ea, i))
                          for i in range(3) if idc.get_operand_type(ea, i)])


tables = []
selected = {0x159c4, 0x154ea, 0x14e7e, 0x15683, 0x1fb6c, 0x22dbc, 0x22b96,
            0x15962, 0x1593c, 0x158f0, 0x15792}
data_base = next(ea for ea in idautils.Segments() if ida_segment.get_segm_name(ida_segment.getseg(ea)) == 'dseg')
assert data_base == 0x2d780
regions = [(0x21472, 260, '25-name-plus-zero-static-table')]
for displacement, size, label in [(0x2986, 52, 'price-index-candidate'),
                                  (0x70ce, 104, 'battle-attack-hp-candidate'),
                                  (0x54a, 24, 'strategic-six-army-records-candidate')]:
    regions.append((ida_loader.get_fileregion_offset(data_base + displacement), size, label))
for offset, size, label in regions:
    ea = 0x10000 + offset - header
    assert ida_loader.get_fileregion_offset(ea) == offset
    assert ida_bytes.get_bytes(ea, size) == raw[offset:offset+size]
    refs = []
    for at in range(ea, ea + size):
        for x in idautils.XrefsTo(at):
            f = ida_funcs.get_func(x.frm)
            refs.append(dict(source=x.frm, target=at, type=x.type,
                             function=f.start_ea if f else None, line=line(x.frm)))
            if f:
                selected.add(f.start_ea)
    tables.append(dict(label=label, level='static bytes proven; semantics need consumer',
                       ida_linear=ea, file_offset=offset, size=size,
                       bytes=ida_bytes.get_bytes(ea, size).hex(), xrefs=refs))

# Full original operands are retained. Data offsets are navigation candidates,
# not renamed fields. Indirect writes can lack a direct xref to the final field.
offsets = {0x56e8, 0x56ea, 0x5700, 0x5702, 0x70ce, 0x70d0, 0x70d2, 0x70d4}
matches = []
for start in functions:
    for at in idautils.FuncItems(start):
        for i in range(3):
            kind, value = idc.get_operand_type(at, i), idc.get_operand_value(at, i)
            if kind in (idc.o_mem, idc.o_displ) and value in offsets:
                matches.append(dict(function=start, operand_index=i, original_offset=value, line=line(at)))
                selected.add(start)

# Seed recruitment functions, their direct callers, and narrow file services.
for seed in list(selected):
    if seed in {0x159c4, 0x154ea, 0x14e7e, 0x15683}:
        for x in idautils.XrefsTo(seed):
            f = ida_funcs.get_func(x.frm)
            if f:
                selected.add(f.start_ea)
for ea, name in idautils.Names():
    if name in {'_fread', '_fwrite', '_read', '_write', '_fopen', '_fclose'}:
        for x in idautils.XrefsTo(ea):
            f = ida_funcs.get_func(x.frm)
            if f:
                selected.add(f.start_ea)

assert len(selected) <= 90, len(selected)
bodies = []
for start in sorted(selected):
    f = ida_funcs.get_func(start)
    if f is None or f.start_ea != start:
        continue
    bodies.append(dict(start=start, end=f.end_ea, name=ida_funcs.get_func_name(start),
        xrefs=[dict(ida_linear=x.frm, type=x.type,
                    caller=ida_funcs.get_func(x.frm).start_ea if ida_funcs.get_func(x.frm) else None)
               for x in idautils.XrefsTo(start)], lines=[line(at) for at in idautils.FuncItems(start)]))
segments = [dict(start=ea, end=ida_segment.getseg(ea).end_ea,
                 name=ida_segment.get_segm_name(ida_segment.getseg(ea))) for ea in idautils.Segments()]
result = dict(schema=1, status='exported-static-capacity-evidence', tool='IDA Pro 9.4',
              source_sha256=sha(source), database_sha256=sha(db), tool_sha256=sha(Path(__file__)),
              address_space='IDA MZ linear base 0x10000; file offsets separate', header_bytes=header,
              function_count=len(functions), segments=segments, tables=tables, operand_matches=matches,
              bodies=bodies, limits=['Static evidence only. No new ID, save format or production changes.',
                                    'Direct xrefs do not enumerate all indirect reads and writes.'])
Path('/out/ida-capacity-r2.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
idaapi.qexit(0)
