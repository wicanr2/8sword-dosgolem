"""030 DRAFT: narrow damage helpers and their direct callers; no renaming."""
import hashlib,json,os
from pathlib import Path
import ida_auto,ida_bytes,ida_funcs,ida_loader,idaapi,idautils,idc
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert os.getuid()==1000 and idaapi.get_kernel_version()=='9.4'
source=Path('/game/PAM.AY');db=Path('/source/PAM.i64')
assert sha(source)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
assert sha(db)=='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac'
ida_auto.auto_wait()
def line(ea):
 return dict(ida_linear=ea,original_file_offset=ida_loader.get_fileregion_offset(ea),bytes=ida_bytes.get_bytes(ea,idc.get_item_size(ea)).hex(),instruction=idc.generate_disasm_line(ea,0),operands=[dict(index=i,type=idc.get_operand_type(ea,i),value=idc.get_operand_value(ea,i))for i in range(3)if idc.get_operand_type(ea,i)])
helpers=[0x1fa2a,0x1faa2,0x1fb02]
callers=set()
for ea in helpers:
 for x in idautils.XrefsTo(ea):
  f=ida_funcs.get_func(x.frm)
  if f:callers.add(f.start_ea)
bodies=[]
for at in sorted(set(helpers)|callers):
 f=ida_funcs.get_func(at);assert f and f.start_ea==at
 bodies.append(dict(start=at,end=f.end_ea,name=ida_funcs.get_func_name(at),role='helper-candidate'if at in helpers else 'direct-caller',xrefs=[dict(ida_linear=x.frm,type=x.type,caller=ida_funcs.get_func(x.frm).start_ea if ida_funcs.get_func(x.frm)else None)for x in idautils.XrefsTo(at)],lines=[line(ea)for ea in idautils.FuncItems(at)]))
result=dict(schema=1,spec='030 DRAFT',tool='IDA 9.4',source_sha256=sha(source),database_sha256=sha(db),tool_sha256=sha(Path(__file__)),address_space='IDA MZ loader linear base 0x10000; file offsets separate',function_count=len(list(idautils.Functions())),helper_candidates=helpers,bodies=bodies,limits=['Static bytes and direct xrefs only; no dynamic side or eligibility claim.','No rename, patch or production change.'])
Path('/out/ida-formation-hooks-r2.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');idaapi.qexit(0)
