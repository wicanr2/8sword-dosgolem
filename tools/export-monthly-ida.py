"""Narrow monthly producer/consumer evidence; preserve original names and operands."""
import hashlib,json,os
from pathlib import Path
import ida_auto,ida_bytes,ida_funcs,ida_loader,idaapi,idautils,idc
assert os.getuid()==1000 and idaapi.get_kernel_version()=='9.4'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source,database=Path('/game/PAM.AY'),Path('/source/PAM.i64')
assert sha(source)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
assert sha(database)=='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac'
ida_auto.auto_wait();functions=list(idautils.Functions());assert len(functions)==521
index=json.loads(Path('/project/docs/spec/world-army-consumers-r1.json').read_text());indexed={int(v['ida_mz_linear'],16):v for v in index['functions']}
def line(at):return dict(ida_linear=at,file_offset=ida_loader.get_fileregion_offset(at),bytes=ida_bytes.get_bytes(at,idc.get_item_size(at)).hex(),instruction=idc.generate_disasm_line(at,0),operands=[dict(index=i,type=idc.get_operand_type(at,i),value=idc.get_operand_value(at,i))for i in range(3)if idc.get_operand_type(at,i)])
selected=[0x12446,0x12856,0x16058,0x16226,0x19856]
bodies=[]
for start in selected:
    f=ida_funcs.get_func(start);assert f and f.start_ea==start,(hex(start),f.start_ea if f else None)
    tag=indexed.get(start,{});bodies.append(dict(start=start,end=f.end_ea,name=ida_funcs.get_func_name(start),indexed_semantic=dict(note=tag.get('semantic_note'),level=tag.get('level','unknown'),source='docs/spec/world-army-consumers-r1.json',warning='Monthly semantics remain unproven until this slice is reviewed.'),xrefs=[dict(source=x.frm,type=x.type,caller=ida_funcs.get_func(x.frm).start_ea if ida_funcs.get_func(x.frm)else None)for x in idautils.XrefsTo(start)],lines=[line(at)for at in idautils.FuncItems(start)]))
raw_offsets={0x56da,0x56dc,0x4f6,0x4f8,0x2986,0x3efe,0x3f06,0x3fee,0x3ff6,0x40de,0x40e6,0x41ce,0x41d6,0x42be,0x42c6}
linear={0x2d780+v:v for v in raw_offsets};hits=[]
for start in functions:
    for at in idautils.FuncItems(start):
        for i in range(3):
            kind,value=idc.get_operand_type(at,i),idc.get_operand_value(at,i)
            if kind in [idc.o_mem,idc.o_displ,idc.o_imm]and(value in raw_offsets or value in linear):hits.append(dict(function=start,operand=i,value=value,ds_offset_candidate=linear.get(value,value),level='candidate; register/base provenance not inferred',line=line(at)))
result=dict(schema=1,tool='IDA Pro 9.4',uid=os.getuid(),source_sha256=sha(source),database_sha256=sha(database),exporter_sha256=sha(Path(__file__)),index_sha256=sha(Path('/project/docs/spec/world-army-consumers-r1.json')),function_count=len(functions),address_space='IDA MZ loader linear base0x10000; file offsets separate; runtime load0110, DS1E88',functions=bodies,candidates=hits)
Path('/out/ida-monthly-r1.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');idaapi.qexit(0)
