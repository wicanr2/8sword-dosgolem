"""030 DRAFT: preserve original numeric-input and recruitment instructions."""
import hashlib,json,os
from pathlib import Path
import ida_auto,ida_bytes,ida_funcs,ida_loader,idaapi,idautils,idc

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source,database=Path('/game/PAM.AY'),Path('/source/PAM.i64')
assert os.getuid()==1000 and idaapi.get_kernel_version()=='9.4'
assert sha(source)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
assert sha(database)=='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac'
ida_auto.auto_wait();count=len(list(idautils.Functions()));assert count==521
Path('/out/ida-probe-r1.json').write_text(json.dumps(dict(schema=1,tool='IDA Pro 9.4',uid=os.getuid(),function_count=count,source_sha256=sha(source),database_sha256=sha(database)),indent=2)+'\n')
def line(ea):return dict(ida_linear=ea,file_offset=ida_loader.get_fileregion_offset(ea),bytes=ida_bytes.get_bytes(ea,idc.get_item_size(ea)).hex(),instruction=idc.generate_disasm_line(ea,0))
functions=[]
for start in [0x14e7e,0x154ea,0x15792,0x17e28]:
 f=ida_funcs.get_func(start);assert f and f.start_ea==start
 refs=[]
 for x in idautils.XrefsTo(start):
  caller=ida_funcs.get_func(x.frm)
  refs.append(dict(source=x.frm,type=x.type,caller=caller.start_ea if caller else None))
 functions.append(dict(start=start,end=f.end_ea,name=ida_funcs.get_func_name(start),xrefs=refs,lines=[line(at)for at in idautils.FuncItems(start)]))
Path('/out/ida-recruit-quantity-r1.json').write_text(json.dumps(dict(schema=1,tool='IDA Pro 9.4',function_count=count,source_sha256=sha(source),database_sha256=sha(database),exporter_sha256=sha(Path(__file__)),address_space='IDA MZ loader linear base 0x10000; file offsets explicit',functions=functions,limits=['Static source evidence; Go bridge and normal input still require runtime verification.']),ensure_ascii=False,indent=2)+'\n')
idaapi.qexit(0)
