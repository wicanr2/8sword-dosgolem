"""030 DRAFT: player spell UI/callers, no rename, patch or production hooks."""
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


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


assert os.getuid() == 1000 and idaapi.get_kernel_version() == '9.4'
source, database = Path('/game/PAM.AY'), Path('/source/PAM.i64')
assert sha(source) == '83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
assert sha(database) == 'a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac'
ida_auto.auto_wait()


def line(ea):
    return dict(ida_linear=ea, original_file_offset=ida_loader.get_fileregion_offset(ea),
                bytes=ida_bytes.get_bytes(ea, idc.get_item_size(ea)).hex(),
                instruction=idc.generate_disasm_line(ea, 0),
                operands=[dict(index=i, type=idc.get_operand_type(ea, i), value=idc.get_operand_value(ea, i))
                          for i in range(3) if idc.get_operand_type(ea, i)])


def refs(ea):
    rows = []
    for x in idautils.XrefsTo(ea):
        fn = ida_funcs.get_func(x.frm)
        rows.append(dict(source=x.frm, type=x.type, function=fn.start_ea if fn else None,
                         instruction=idc.generate_disasm_line(x.frm, 0)))
    return rows


targets = [0x301a2, 0x21c36, 0x21e3c]
queries = [dict(ida_linear=at, level='candidate', xrefs=refs(at)) for at in targets]
selected = {0x21c36, 0x21e3c, 0x168ce, 0x16638, 0x219cc, 0x21bd2, 0x2055e, 0x1e88e, 0x20dae}
selected.update(v['function'] for q in queries for v in q['xrefs'] if v['function'])
operand_candidates = []
for at in idautils.Functions():
    for ea in idautils.FuncItems(at):
        for i in range(3):
            if idc.get_operand_type(ea, i) and idc.get_operand_value(ea, i) in [0x2a22, 0x2a38, 0x2ab8, 0x2b28]:
                operand_candidates.append(dict(function=at, line=line(ea), level='candidate'))
                selected.add(at)
for at in list(selected):
    selected.update(v['function'] for v in refs(at) if v['function'])
assert len(selected) <= 40
bodies = []
for at in sorted(selected):
    fn = ida_funcs.get_func(at)
    assert fn and fn.start_ea == at
    bodies.append(dict(name=ida_funcs.get_func_name(at), start=at, end=fn.end_ea,
                       xrefs=refs(at), lines=[line(ea) for ea in idautils.FuncItems(at)]))
report = dict(schema=1, tool='IDA 9.4', tool_sha256=sha(Path(__file__)), uid=1000,
              source_sha256=sha(source), database_sha256=sha(database),
              address_space='IDA MZ loader linear, image base 0x10000; file offsets separately labelled',
              function_count=len(list(idautils.Functions())), queries=queries, operand_candidates=operand_candidates, functions=bodies,
              limits=['Static candidates only; UI, spell names and lifecycle require executable observation.',
                      'Indirect register-based references may be absent. No rename or patch.'])
Path('/out/ida-spells-r4.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
idaapi.qexit(0)
