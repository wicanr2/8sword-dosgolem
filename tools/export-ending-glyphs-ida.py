"""053 DRAFT：窄查PAE字模、字碼與前景／背景欄位，保留原名與原始定位。"""
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
source = Path('/source/PAE-runtime-analysis.exe')
assert sha(source) == '1896b5b2c321f0b3c6c49e144ff27a261cc94befd4fcb9d3e7977030ef09ff1a'
ida_auto.auto_wait()
report = dict(schema=1, spec='053', tool='IDA 9.4', uid=1000, source_sha256=sha(source),
              address_space='IDA runtime-linear of -b110 PAE wrapper; not packed PAE file offsets', bodies=[])
for at in [0x37d0, 0x446c, 0x44b0, 0x439a, 0x4668, 0x3ac6, 0x3b9e]:
    fn = ida_funcs.get_func(at)
    if not fn:
        report['bodies'].append(dict(query=at, function=None))
        continue
    report['bodies'].append(dict(query=at, name=ida_funcs.get_func_name(fn.start_ea), start=fn.start_ea, end=fn.end_ea,
        xrefs=[dict(from_linear=x.frm, instruction=idc.generate_disasm_line(x.frm,0)) for x in idautils.XrefsTo(fn.start_ea)],
        lines=[dict(linear=ea, wrapper_file_offset=ida_loader.get_fileregion_offset(ea),
                    bytes=ida_bytes.get_bytes(ea,idc.get_item_size(ea)).hex(), instruction=idc.generate_disasm_line(ea,0),
                    operands=[dict(index=i,type=idc.get_operand_type(ea,i),value=idc.get_operand_value(ea,i))
                              for i in range(3) if idc.get_operand_type(ea,i)]) for ea in idautils.FuncItems(fn.start_ea)]))
report['tool_sha256'] = sha(Path(__file__))
report['limits'] = ['Automatic data names are navigation only; raw offsets and dynamic reads are authoritative.',
                    'No rename, byte patch or type change. This query does not prove natural completion.']
Path('/out/ida-glyphs-r1.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
idaapi.qexit(0)
