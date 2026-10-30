"""030 DRAFT: bounded world/battle ownership boundaries; no database renaming."""
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


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert os.getuid() == 1000 and idaapi.get_kernel_version() == "9.4"
source, database = Path("/game/PAM.AY"), Path("/source/PAM.i64")
assert sha(source) == "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"
assert sha(database) == "a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac"
ida_auto.auto_wait()
assert len(list(idautils.Functions())) == 521


def line(ea):
    return dict(ida_linear=ea, file_offset=ida_loader.get_fileregion_offset(ea),
                bytes=ida_bytes.get_bytes(ea, idc.get_item_size(ea)).hex(),
                instruction=idc.generate_disasm_line(ea, 0),
                operands=[dict(index=i, type=idc.get_operand_type(ea, i),
                               value=idc.get_operand_value(ea, i))
                          for i in range(3) if idc.get_operand_type(ea, i)])


# Known strategic wrapper plus the actual battle entry, return and world consumers.
selected = {0x132e0, 0x13774, 0x1e578, 0x12446, 0x12dde, 70940}
selected.update({0x2031a, 0x215f8, 0x21440, 0x21202, 0x21246, 0x205e6})
selected.add(0x19856)
bodies = []
for start in sorted(selected):
    f = ida_funcs.get_func(start)
    assert f is not None and f.start_ea == start, hex(start)
    bodies.append(dict(start=start, end=f.end_ea, name=ida_funcs.get_func_name(start),
                       xrefs=[dict(source=x.frm, type=x.type,
                                   caller=ida_funcs.get_func(x.frm).start_ea
                                   if ida_funcs.get_func(x.frm) else None)
                              for x in idautils.XrefsTo(start)],
                       lines=[line(at) for at in idautils.FuncItems(start)]))

# Operand hits are candidates. A matching displacement alone proves no semantics.
offsets = {0x4f2, 0x4f8, 0x4fa, 0x54a, 0x54c, 0x56e8, 0x56ea,
           0x5700, 0x5702, 0x26ac, 0x26b8, 0x8e84, 0x8e7e}
matches = []
for start in idautils.Functions():
    for at in idautils.FuncItems(start):
        for i in range(3):
            kind, value = idc.get_operand_type(at, i), idc.get_operand_value(at, i)
            if kind in (idc.o_mem, idc.o_displ) and value in offsets:
                matches.append(dict(function=start, operand_index=i, original_offset=value,
                                    level="candidate; verify base, stride and consumer",
                                    line=line(at)))
result = dict(schema=1, tool="IDA Pro 9.4", uid=os.getuid(),
              input_sha256=sha(source), database_sha256=sha(database),
              exporter_sha256=sha(Path(__file__)), function_count=521,
              address_space="IDA MZ loader linear base 0x10000; file offsets explicit",
              functions=bodies, operand_candidates=matches,
              limits=["Static evidence only; dynamic boundaries require replay.",
                      "Indirect pointer writes need data-flow verification."])
Path("/out/ida-world-r3.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
idaapi.qexit(0)
