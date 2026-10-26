"""047 DRAFT：從正式PAM資料庫副本窄查仍由CPU執行的繪圖原語。"""
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
report = dict(schema=1, spec='047', tool='IDA 9.4', uid=os.getuid(),
              source_sha256=sha(source), database_sha256=sha(database), tool_sha256=sha(Path(__file__)),
              address_space='IDA MZ loader linear; runtime addresses and file offsets are separate',
              function_count=len(list(idautils.Functions())), bodies=[])
assert report['function_count'] == 521
Path('/out/ida-render-min-r1.json').write_text(json.dumps(report, indent=2)+'\n')
for at in [0x1e418, 0x247a6, 0x2495e, 0x23f5d, 0x23fd0, 0x24043, 0x23e94]:
    fn = ida_funcs.get_func(at)
    assert fn is not None, hex(at)
    report['bodies'].append(dict(query=at, name=ida_funcs.get_func_name(fn.start_ea),
        start=fn.start_ea, end=fn.end_ea,
        contiguous_code_sha256=hashlib.sha256(ida_bytes.get_bytes(fn.start_ea,fn.end_ea-fn.start_ea)).hexdigest(),
        xrefs=[dict(from_linear=x.frm, instruction=idc.generate_disasm_line(x.frm,0))
               for x in idautils.XrefsTo(fn.start_ea)],
        lines=[dict(linear=ea, file_offset=ida_loader.get_fileregion_offset(ea),
                    bytes=ida_bytes.get_bytes(ea,idc.get_item_size(ea)).hex(), instruction=idc.generate_disasm_line(ea,0),
                    operands=[dict(index=i,type=idc.get_operand_type(ea,i),value=idc.get_operand_value(ea,i))
                              for i in range(3) if idc.get_operand_type(ea,i)])
               for ea in idautils.FuncItems(fn.start_ea)]))
report['limits'] = ['Original names and addresses retained; automatic names are navigation, not semantic evidence.',
                    'No database modification. Static export alone does not establish normal-player parity.']
Path('/out/ida-render-primitives-r1.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
idaapi.qexit(0)
