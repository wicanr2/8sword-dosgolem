"""在固定 IDA 9.4 的唯讀 PAM 資料庫副本匯出圖像載入線索與面板呼叫邊界。"""
import hashlib
import json
import os
import re
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


ida_auto.auto_wait()
intro = os.environ.get('EIGHTSWORD_IDA_GRAPHICS_TARGET') == 'intro'
source = Path('/source/PREDELLA-runtime-analysis.exe') if intro else Path('/game/PAM.AY')
database = Path('/source/PREDELLA-runtime.i64') if intro else Path('/source/PAM.i64')
revision = os.environ.get('EIGHTSWORD_IDA_GRAPHICS_REV', 'r2')
assert revision in ('r2', 'r3', 'r4')
slug = 'intro-graphics-inventory-r1' if intro else 'graphics-inventory-' + revision
report = dict(schema='8sword-graphics-inventory-ida-r1', tool='IDA ' + idaapi.get_kernel_version(),
              uid=os.getuid(), source_file='PAM.AY', source_sha256=sha(source), database_sha256=sha(database),
              function_count=len(list(idautils.Functions())),
              address_space='IDA MZ loader linear; original file offsets retained separately')
assert report['uid'] == 1000 and report['tool'] == 'IDA 9.4'
assert report['function_count'] == (185 if intro else 521)
assert report['source_sha256'] == ('28dbc38d4ef65326ee281b684bf3a7a304ea41c00bfc00410076bce31b1b247a' if intro else '83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0')
assert report['database_sha256'] == ('dccb45c43ec22165a50422e6dbb46bf0c9f8ce7005c570000b29b8f296614616' if intro else 'a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac')
if intro:
    report['source_file'] = source.name
    report['address_space'] = 'IDA runtime-linear -b110 mapping of extracted PREDELLA; file offsets refer to synthetic analysis wrapper, not packed original EXE'
Path('/out/ida-' + slug + '-min.json').write_text(json.dumps(report, indent=2) + '\n')


def refs(ea):
    result = []
    for x in idautils.XrefsTo(ea):
        fn = ida_funcs.get_func(x.frm)
        result.append(dict(from_ida_linear=x.frm, from_file_offset=ida_loader.get_fileregion_offset(x.frm),
                           type=x.type, function=fn.start_ea if fn else None,
                           instruction=idc.generate_disasm_line(x.frm, 0)))
    return result


raw = source.read_bytes()
pattern = re.compile(rb'(?i)[A-Z0-9_%?*\\./-]{1,100}\.(?:EGG?|AY|RIL)')
resources = []
starts = set()
for match in pattern.finditer(raw):
    ea = ida_loader.get_fileregion_ea(match.start())
    xrefs = refs(ea) if ea != idaapi.BADADDR else []
    starts.update(x['function'] for x in xrefs if x['function'] is not None)
    resources.append(dict(text=match.group().decode('ascii'), file_offset=match.start(),
                          ida_linear=ea if ea != idaapi.BADADDR else None, xrefs=xrefs))

# Existing IDA graphic primitives and return addresses observed during the
# ordinary F1/F2 path. get_func selects real database boundaries, not guessed
# prologue scanning. Keep all original names and raw operands.
queries = [] if intro else [0x24112, 0x24246, 0x2438f, 0x245bc, 0x2495e,
                            0x171ab, 0x17266, 0x17d02, 0x13eae, 0x13ebf, 0x11f5b,
                            0x175c6, 0x1844c, 0x24c14, 0x24c58]
if not intro and revision in ('r3','r4'):
    queries += [0x13c18,0x13d74,0x11f60,0x268aa,0x26b1f]
if not intro and revision == 'r4':
    queries += [0x13df0,0x13e4a,0x1720e]
query_functions = []
for ea in queries:
    fn = ida_funcs.get_func(ea)
    query_functions.append(dict(query=ea, function=fn.start_ea if fn else None))
    if fn:
        starts.add(fn.start_ea)
report['resources'] = resources
offsets = set()
for resource in resources:
    if resource['ida_linear'] is not None:
        segment = ida_segment.getseg(resource['ida_linear'])
        if segment:
            offsets.add(resource['ida_linear'] - segment.start_ea)
report['relative_filename_operand_candidates'] = []
for start in idautils.Functions():
    for ea in idautils.FuncItems(start):
        for operand in range(3):
            kind = idc.get_operand_type(ea, operand)
            if kind not in (idc.o_imm, idc.o_displ):
                continue
            value = idc.get_operand_value(ea, operand) & 0xffff
            if value in offsets:
                report['relative_filename_operand_candidates'].append(dict(ida_linear=ea, function=start,
                    file_offset=ida_loader.get_fileregion_offset(ea), operand=operand, value=value,
                    instruction=idc.generate_disasm_line(ea, 0), evidence_level='candidate, not confirmed filename use'))
                starts.add(start)
report['runtime_query_functions'] = query_functions
report['function_bounds'] = [dict(name=ida_funcs.get_func_name(ea), start=ea, end=ida_funcs.get_func(ea).end_ea)
                             for ea in idautils.Functions()]
report['functions'] = []
assert len(starts) < 100
for start in sorted(starts):
    fn = ida_funcs.get_func(start)
    report['functions'].append(dict(name=ida_funcs.get_func_name(start), start=start, end=fn.end_ea,
                                    xrefs=refs(start),
                                    lines=[dict(ida_linear=ea, file_offset=ida_loader.get_fileregion_offset(ea),
                                                bytes=ida_bytes.get_bytes(ea, idc.get_item_size(ea)).hex(),
                                                instruction=idc.generate_disasm_line(ea, 0))
                                           for ea in idautils.FuncItems(start)]))
report['limits'] = ['Filename xrefs alone do not classify every AY file as graphics.',
                    'No direct xref is not proof of an unused resource; indexed tables may be indirect.',
                    'Function bounds cover the database; exported bodies are limited to resource consumers and panel candidates.',
                    'No database names, types or bytes were modified.']
Path('/out/ida-' + slug + '.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
idaapi.qexit(0)
