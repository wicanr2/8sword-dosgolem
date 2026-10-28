"""030 DRAFT：窄查特殊分派7效果執行器，保留原名、位址、bytes與operand。"""
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


assert os.getuid() == 1000 and idaapi.get_kernel_version() == '9.4'
source = Path('/game/PAM.AY')
database = Path('/source/PAM.i64')
assert sha(source) == '83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
assert sha(database) == 'a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac'
ida_auto.auto_wait()


def line(ea):
    return dict(ida_linear=ea, original_file_offset=ida_loader.get_fileregion_offset(ea),
                bytes=ida_bytes.get_bytes(ea, idc.get_item_size(ea)).hex(),
                instruction=idc.generate_disasm_line(ea, 0),
                operands=[dict(index=i, type=idc.get_operand_type(ea, i),
                               value=idc.get_operand_value(ea, i))
                          for i in range(3) if idc.get_operand_type(ea, i)])


bodies=[]
for at in [0x21e3c]:
    fn=ida_funcs.get_func(at)
    assert fn is not None and fn.start_ea==at
    bodies.append(dict(query=at,name=ida_funcs.get_func_name(at),start=fn.start_ea,end=fn.end_ea,
                       lines=[line(ea) for ea in idautils.FuncItems(at)]))
table=dict(ida_linear=0x1fa14,original_file_offset=ida_loader.get_fileregion_offset(0x1fa14),
           bytes=ida_bytes.get_bytes(0x1fa14,16).hex())
report = dict(schema=1, spec='030', tool='IDA 9.4', uid=1000,
              tool_sha256=sha(Path(__file__)), source_sha256=sha(source),
              database_sha256=sha(database), function_count=len(list(idautils.Functions())),
              address_space='IDA MZ linear, image base 0x10000; original file offsets separate',
              bodies=bodies, dispatch_table=table,
              limits=['Read-only source/database copied to temporary IDB. No rename or patch.',
                      'Raw operand matches and automatic names are navigation, not semantic proof.',
                      'Static caller/executor bytes do not prove spell names or natural encounters.'])
Path('/out/ida-specials-r1.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
idaapi.qexit(0)
