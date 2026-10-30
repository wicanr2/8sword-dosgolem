"""030 DRAFT: strategic six-row consumers and callers, retaining original locators."""
import hashlib
import json
import os
from pathlib import Path

import ida_auto
import ida_bytes
import ida_funcs
import ida_loader
import idaapi
import idautils
import idc

assert os.getuid() == 1000 and idaapi.get_kernel_version() == '9.4'
source, database = Path('/game/PAM.AY'), Path('/source/PAM.i64')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source) == '83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
assert sha(database) == 'a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac'
ida_auto.auto_wait()
functions = list(idautils.Functions())
assert len(functions) == 521


def line(ea):
    return dict(ida_linear=ea, file_offset=ida_loader.get_fileregion_offset(ea),
                bytes=ida_bytes.get_bytes(ea, idc.get_item_size(ea)).hex(),
                instruction=idc.generate_disasm_line(ea, 0),
                operands=[dict(index=i, type=idc.get_operand_type(ea, i), value=idc.get_operand_value(ea, i))
                          for i in range(3) if idc.get_operand_type(ea, i)])


selected = {0x158f0, 0x1593c, 0x15962}
hits = []
for start in functions:
    for at in idautils.FuncItems(start):
        for i in range(3):
            kind, value = idc.get_operand_type(at, i), idc.get_operand_value(at, i)
            if kind in (idc.o_mem, idc.o_displ, idc.o_imm) and 0x54a <= value < 0x562:
                hits.append(dict(function=start, operand_index=i, raw_value=value,
                                 level='candidate; inspect operand base and data flow', line=line(at)))
                selected.add(start)
for seed in [0x158f0, 0x1593c, 0x15962]:
    for x in idautils.XrefsTo(seed):
        f = ida_funcs.get_func(x.frm)
        if f:
            selected.add(f.start_ea)
assert len(selected) <= 40, len(selected)
bodies = []
for start in sorted(selected):
    f = ida_funcs.get_func(start)
    assert f and f.start_ea == start
    bodies.append(dict(start=start, end=f.end_ea, name=ida_funcs.get_func_name(start),
                       xrefs=[dict(source=x.frm, type=x.type,
                                   caller=ida_funcs.get_func(x.frm).start_ea if ida_funcs.get_func(x.frm) else None)
                              for x in idautils.XrefsTo(start)],
                       lines=[line(at) for at in idautils.FuncItems(start)]))
result = dict(schema=1, tool='IDA Pro 9.4', source_sha256=sha(source), database_sha256=sha(database),
              exporter_sha256=sha(Path(__file__)), function_count=521,
              address_space='IDA MZ loader linear base 0x10000; file offsets separate',
              functions=bodies, candidates=hits,
              limits=['Direct references do not enumerate arbitrary indirect accesses.',
                      'Immediate values may be unrelated constants; candidates are not semantic claims.'])
Path('/out/ida-world-army-r1.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
idaapi.qexit(0)
