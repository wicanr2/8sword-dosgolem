"""Narrow event-resource evidence; original names and operands remain intact."""
import hashlib,json,os
from pathlib import Path
import ida_auto,ida_bytes,ida_funcs,ida_loader,idaapi,idautils,idc
assert os.getuid()==1000 and idaapi.get_kernel_version()=='9.4'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source,database=Path('/game/PAM.AY'),Path('/source/PAM.i64')
assert sha(source)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
assert sha(database)=='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac'
ida_auto.auto_wait();functions=list(idautils.Functions());assert len(functions)==521
def line(at):return dict(ida_linear=at,file_offset=ida_loader.get_fileregion_offset(at),bytes=ida_bytes.get_bytes(at,idc.get_item_size(at)).hex(),instruction=idc.generate_disasm_line(at,0),operands=[dict(index=i,type=idc.get_operand_type(at,i),value=idc.get_operand_value(at,i))for i in range(3)if idc.get_operand_type(at,i)])
def body(start):
    f=ida_funcs.get_func(start);assert f and f.start_ea==start
    return dict(start=start,end=f.end_ea,name=ida_funcs.get_func_name(start),level='unknown; inspect source flow and executable controls',xrefs=[dict(source=x.frm,type=x.type,caller=ida_funcs.get_func(x.frm).start_ea if ida_funcs.get_func(x.frm)else None)for x in idautils.XrefsTo(start)],lines=[line(at)for at in idautils.FuncItems(start)])
raw=set(range(0x4f2,0x4fe,2));hits=[]
for start in functions:
    for at in idautils.FuncItems(start):
        for i in range(3):
            kind,value=idc.get_operand_type(at,i),idc.get_operand_value(at,i)
            if kind in[idc.o_mem,idc.o_displ]and(value in raw or value-0x2d780 in raw):hits.append(dict(function=start,operand=i,value=value,level='candidate; operand provenance and write direction not inferred',line=line(at)))
result=dict(schema=1,tool='IDA Pro 9.4',uid=os.getuid(),function_count=len(functions),source_sha256=sha(source),database_sha256=sha(database),exporter_sha256=sha(Path(__file__)),address_space='IDA MZ linear base0x10000; runtime0110,DS1E88; file offsets separate',functions=[body(s)for s in[0x120b0,0x1649a,0x16b20,0x13aec,0x1479a]],candidates=hits)
Path('/out/ida-story-resources-r1.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');idc.qexit(0)
