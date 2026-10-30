"""030 DRAFT: narrow native save pack/unpack anchors, no database renaming."""
import hashlib,json,os
from pathlib import Path
import ida_auto,ida_bytes,ida_funcs,ida_loader,idaapi,idautils,idc
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=Path('/game/PAM.AY');database=Path('/source/PAM.i64')
assert os.getuid()==1000 and idaapi.get_kernel_version()=='9.4'
assert sha(source)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
assert sha(database)=='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac'
ida_auto.auto_wait();functions=list(idautils.Functions());assert len(functions)==521
def line(ea):
 return dict(ida_linear=ea,file_offset=ida_loader.get_fileregion_offset(ea),bytes=ida_bytes.get_bytes(ea,idc.get_item_size(ea)).hex(),instruction=idc.generate_disasm_line(ea,0),operands=[dict(index=i,type=idc.get_operand_type(ea,i),value=idc.get_operand_value(ea,i))for i in range(3)if idc.get_operand_type(ea,i)])
selected=set();anchors=[]
for start in functions:
 for ea in idautils.FuncItems(start):
  for i in range(3):
   if idc.get_operand_type(ea,i)==idc.o_imm and idc.get_operand_value(ea,i)==2987:
    selected.add(start);anchors.append(dict(level='candidate; immediate length alone does not prove save semantics',function=start,line=line(ea)))
raw=source.read_bytes();header=int.from_bytes(raw[8:10],'little')*16
for spelling in [b'gamedata.ay',b'GAMEDATA.AY']:
 at=0
 while True:
  at=raw.find(spelling,at)
  if at<0:break
  ea=0x10000+at-header;refs=[]
  for x in idautils.XrefsTo(ea):
   f=ida_funcs.get_func(x.frm)
   if f:selected.add(f.start_ea)
   refs.append(dict(source=x.frm,type=x.type,function=f.start_ea if f else None,line=line(x.frm)))
  anchors.append(dict(level='proven bytes; caller semantics candidate',string=spelling.decode(),ida_linear=ea,file_offset=at,xrefs=refs));at+=1
for start in list(selected):
 for x in idautils.XrefsTo(start):
  f=ida_funcs.get_func(x.frm)
  if f:selected.add(f.start_ea)
assert 0<len(selected)<=32,len(selected)
bodies=[]
for start in sorted(selected):
 f=ida_funcs.get_func(start);assert f and f.start_ea==start
 bodies.append(dict(start=start,end=f.end_ea,name=ida_funcs.get_func_name(start),xrefs=[dict(source=x.frm,type=x.type,caller=ida_funcs.get_func(x.frm).start_ea if ida_funcs.get_func(x.frm)else None)for x in idautils.XrefsTo(start)],lines=[line(ea)for ea in idautils.FuncItems(start)]))
result=dict(schema=1,tool='IDA Pro 9.4',uid=os.getuid(),source_sha256=sha(source),database_sha256=sha(database),exporter_sha256=sha(Path(__file__)),function_count=len(functions),address_space='IDA MZ loader linear base 0x10000; file offsets separately recorded',anchors=anchors,bodies=bodies,limits=['Anchor candidates only; pack/unpack and normal read/write must be independently validated.','No production hooks, renaming or changes to the authoritative database.'])
Path('/out/ida-save-r1.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');idaapi.qexit(0)
