import hashlib,json,os
from pathlib import Path
import ida_auto,ida_bytes,ida_funcs,ida_loader,idaapi,idautils,idc
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert os.getuid()==1000 and idaapi.get_kernel_version()=="9.4"
assert sha('/game/PAM.AY')=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
assert sha('/source/PAM.i64')=='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac'
ida_auto.auto_wait();functions=list(idautils.Functions());assert len(functions)==521
Path('/out/evidence/ida-probe.json').write_text(json.dumps(dict(schema=1,uid=os.getuid(),version=idaapi.get_kernel_version(),functions=len(functions),source_sha256=sha('/game/PAM.AY'),database_sha256=sha('/source/PAM.i64'))))
semantic_index=json.loads(Path('/index/treasure-address-index-r1.json').read_text(encoding='utf-8'))
def line(at):
 v=dict(ida_linear=at,file_offset=ida_loader.get_fileregion_offset(at),bytes=ida_bytes.get_bytes(at,idc.get_item_size(at)).hex(),instruction=idc.generate_disasm_line(at,0),operands=[dict(index=i,type=idc.get_operand_type(at,i),value=idc.get_operand_value(at,i))for i in range(3)if idc.get_operand_type(at,i)])
 v['semantics']=[dict(note=r['semantic_note'],level=r['level'],evidence=r['evidence'])for r in semantic_index['records']if r['original_location']['ida_linear']==at]
 return v
hits=[];selected=set()
for start in functions:
 for at in idautils.FuncItems(start):
  if any(idc.get_operand_type(at,i)in(idc.o_mem,idc.o_displ,idc.o_imm)and idc.get_operand_value(at,i)&0xffff in [0x8c60,0x8c62]for i in range(3)):
   hits.append(dict(function=start,line=line(at)));selected.add(start)
bodies=[]
for start in sorted(selected):
 f=ida_funcs.get_func(start);bodies.append(dict(name=ida_funcs.get_func_name(start),start=start,end=f.end_ea,lines=[line(at)for at in idautils.FuncItems(start)],xrefs=[dict(source=x.frm,type=x.type,caller=ida_funcs.get_func(x.frm).start_ea if ida_funcs.get_func(x.frm)else None)for x in idautils.XrefsTo(start)]))
Path('/out/evidence/ida-coordinates.json').write_text(json.dumps(dict(schema=1,tool='IDA Pro 9.4',uid=os.getuid(),source_sha256=sha('/game/PAM.AY'),database_sha256=sha('/source/PAM.i64'),exporter_sha256=sha(__file__),semantic_index_sha256=sha('/index/treasure-address-index-r1.json'),address_space='IDA MZ linear base10000h; runtime CS0110 IP=linear-10000h; DS1E88 offsets independent; file offsets separate',function_count=len(functions),queries=hits,functions=bodies),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
idaapi.qexit(0)
