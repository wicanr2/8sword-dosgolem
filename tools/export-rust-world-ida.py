"""031: bounded world movement evidence; original names and operands retained."""
import hashlib,json,os
from pathlib import Path
import ida_auto,ida_bytes,ida_funcs,ida_loader,idaapi,idautils,idc
assert os.getuid()==1000 and idaapi.get_kernel_version()=="9.4"
source=Path('/game/PAM.AY');database=Path('/source/PAM.i64')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
assert sha(database)=='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac'
ida_auto.auto_wait();functions=list(idautils.Functions());assert len(functions)==521
def line(ea):
 return dict(ida_linear=ea,original_file_offset=ida_loader.get_fileregion_offset(ea),bytes=ida_bytes.get_bytes(ea,idc.get_item_size(ea)).hex(),instruction=idc.generate_disasm_line(ea,0),operands=[dict(index=i,type=idc.get_operand_type(ea,i),value=idc.get_operand_value(ea,i))for i in range(3)if idc.get_operand_type(ea,i)])
selected={ida_funcs.get_func(ea).start_ea for ea in [0x15f7e,0x15fe6,0x11f20]}
queries=[]
for off in [0x56da,0x56dc,0x8e12,0x8e44]:
 hits=[]
 for start in functions:
  for at in idautils.FuncItems(start):
   for i in range(3):
    if idc.get_operand_type(at,i)in(idc.o_mem,idc.o_displ)and idc.get_operand_value(at,i)==off:hits.append(dict(function=start,line=line(at)))
 queries.append(dict(original_runtime_ds_offset=off,level='candidate; verify complete data flow',hits=hits))
bodies=[]
for start in sorted(selected):
 f=ida_funcs.get_func(start);bodies.append(dict(name=ida_funcs.get_func_name(start),start=start,end=f.end_ea,xrefs=[dict(source=x.frm,type=x.type,caller=ida_funcs.get_func(x.frm).start_ea if ida_funcs.get_func(x.frm)else None)for x in idautils.XrefsTo(start)],lines=[line(at)for at in idautils.FuncItems(start)]))
result=dict(schema=1,tool='IDA Pro 9.4',uid=os.getuid(),source_sha256=sha(source),database_sha256=sha(database),tool_sha256=sha(Path(__file__)),function_count=521,address_space='IDA MZ linear base10000h; world runtime CS0110 IP=linear-10000h; DS1E88 offsets separately labelled',functions=bodies,queries=queries,inventory=[dict(start=s,end=ida_funcs.get_func(s).end_ea,name=ida_funcs.get_func_name(s))for s in functions])
Path('/out/ida-world-movement-r5.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');idaapi.qexit(0)
