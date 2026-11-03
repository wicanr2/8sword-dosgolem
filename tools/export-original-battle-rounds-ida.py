"""Spec030 original round sorting, player dispatch and ordinary actions; no names changed."""
import hashlib,json,os
from pathlib import Path
import ida_auto,ida_bytes,ida_funcs,ida_loader,idaapi,idautils,idc
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source,database=Path('/game/PAM.AY'),Path('/source/PAM.i64')
assert os.getuid()==1000 and idaapi.get_kernel_version()=='9.4'
assert sha(source)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
assert sha(database)=='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac'
ida_auto.auto_wait();count=len(list(idautils.Functions()));assert count==521
Path('/out/probe.json').write_text(json.dumps(dict(tool='IDA Pro9.4',uid=os.getuid(),functions=count,source_sha256=sha(source),database_sha256=sha(database)),indent=2)+'\n')
def line(ea):
 return dict(ida_linear=ea,file_offset=ida_loader.get_fileregion_offset(ea),bytes=ida_bytes.get_bytes(ea,idc.get_item_size(ea)).hex(),instruction=idc.generate_disasm_line(ea,0),operands=[dict(index=i,type=idc.get_operand_type(ea,i),value=idc.get_operand_value(ea,i))for i in range(3)if idc.get_operand_type(ea,i)])
functions=[]
for start in [0x205e6,0x2068a,0x206da,0x20724,0x20ab4,0x1ff1c,0x20dae,0x21ea0,0x217b0,0x1fb02,0x219b0,0x21168,0x210ce,0x21202,0x21712,0x22dbc,0x22b96,0x22af8,0x21274,0x2135a,0x1e578]:
 f=ida_funcs.get_func(start)
 if not f:continue
 start=f.start_ea
 if any(v["start"]==start for v in functions):continue
 functions.append(dict(start=start,end=f.end_ea,name=ida_funcs.get_func_name(start),xrefs=[dict(source=x.frm,type=x.type)for x in idautils.XrefsTo(start)],lines=[line(at)for at in idautils.FuncItems(start)]))
Path('/out/ida-rounds.json').write_text(json.dumps(dict(schema=1,tool='IDA Pro9.4',function_count=count,source_sha256=sha(source),database_sha256=sha(database),exporter_sha256=sha(Path(__file__)),address_space='IDA MZ linear base0x10000; file offsets explicit; runtime code0F67 corresponds relativeE570',functions=functions,limits=['Selected functions only; unexported indirect consumers remain unverified.']),ensure_ascii=False,indent=2)+'\n')
idaapi.qexit(0)
