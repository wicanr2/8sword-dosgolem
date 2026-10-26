"""053 DRAFT：IDA9.4匯出PAE原始函式、bytes、xref及實際PC對應，不改名稱。"""
import hashlib
import json
import os
from pathlib import Path
import re

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


root = Path('/source')
out = Path('/out')
preparation = json.loads((root/'preparation.json').read_text())
source = root/preparation['wrapper']
assert os.getuid() == 1000 and idaapi.get_kernel_version() == '9.4'
assert sha(source) == preparation['wrapper_sha256']
ida_auto.auto_wait()
assert ida_bytes.get_bytes(0x1100, 16).hex() == preparation['first16']
report = dict(schema=1, spec='053', tool='IDA '+idaapi.get_kernel_version(), uid=os.getuid(),
              source_sha256=sha(source), preparation_sha256=sha(root/'preparation.json'),
              function_count=len(list(idautils.Functions())),
              address_space=preparation['address_space'])
(out/'ida-minimal.json').write_text(json.dumps(report, indent=2)+'\n')


def refs(ea):
    result = []
    for x in idautils.XrefsTo(ea):
        fn = ida_funcs.get_func(x.frm)
        result.append(dict(ida_linear=x.frm, function=fn.start_ea if fn else None,
                           wrapper_file_offset=ida_loader.get_fileregion_offset(x.frm),
                           instruction=idc.generate_disasm_line(x.frm, 0), type=x.type))
    return result


report['segments'] = [dict(start=ea, end=ida_segment.getseg(ea).end_ea,
                           name=idc.get_segm_name(ea), bitness=ida_segment.getseg(ea).bitness)
                      for ea in idautils.Segments()]
report['functions'] = [dict(name=ida_funcs.get_func_name(ea), start=ea, end=ida_funcs.get_func(ea).end_ea)
                       for ea in idautils.Functions()]
targets = set()
review = os.environ.get('EIGHTSWORD_ENDING_IDA_REVIEW') == '1'
report['queries'] = []
for ea in preparation['query_runtime_linear']:
    fn = ida_funcs.get_func(ea)
    report['queries'].append(dict(runtime_linear=ea, function=fn.start_ea if fn else None))
    if fn:
        targets.add(fn.start_ea)
if review:
    targets.update(ea for ea in idautils.Functions() if 0x1100 <= ea < 0x2771 or 0x3930 <= ea < 0x484b)
raw = source.read_bytes()[32:]
report['resources'] = []
for match in re.finditer(rb'(?i)(?:end[1-9]h?|[ms](?:end|fig)|pa[ef])\.(?:ay|ril)', raw):
    ea = 0x1100+match.start()
    xrefs = refs(ea)
    report['resources'].append(dict(text=match.group().decode(), runtime_linear=ea,
                                    wrapper_file_offset=match.start()+32, xrefs=xrefs))
    targets.update(x['function'] for x in xrefs if x['function'] is not None)
report['bodies'] = []
def instruction(ea):
    return dict(ida_linear=ea, wrapper_file_offset=ida_loader.get_fileregion_offset(ea),
                bytes=ida_bytes.get_bytes(ea, idc.get_item_size(ea)).hex(),
                instruction=idc.generate_disasm_line(ea, 0),
                operands=[dict(index=i, type=idc.get_operand_type(ea, i), value=idc.get_operand_value(ea, i),
                               printed=idc.print_operand(ea, i)) for i in range(3) if idc.get_operand_type(ea, i)])
for start in sorted(targets):
    fn = ida_funcs.get_func(start)
    report['bodies'].append(dict(name=ida_funcs.get_func_name(start), start=start, end=fn.end_ea,
                                xrefs=refs(start), lines=[instruction(ea) for ea in idautils.FuncItems(start)]))
if review:
    report['driver_heads'] = [instruction(ea) for ea in idautils.Heads(0x3930, 0x4772)]
report['tool_sha256'] = sha(Path(__file__))
report['limits'] = ['Raw original names, bytes and references only; semantics require caller and dynamic evidence.',
                    'A resource without direct xrefs may be reached through relative pointers.',
                    'No database rename, type change or patch was applied.']
revision = 'r2' if review else 'r1'
(out/('ida-runtime-'+revision+'.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
assert ida_loader.save_database('/out/PAE-runtime-'+revision+'.i64', 0)
idaapi.qexit(0)
