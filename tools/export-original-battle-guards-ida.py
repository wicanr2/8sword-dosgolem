"""Spec030 DRAFT: original guard return and cleanup; preserve names and operands."""
import hashlib,json,os
from pathlib import Path
import ida_auto,ida_bytes,ida_funcs,ida_loader,idaapi,idautils,idc
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert os.getuid()==1000 and idaapi.get_kernel_version()=='9.4'
source=Path('/game/PAM.AY');database=Path('/source/PAM.i64')
assert sha(source)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
assert sha(database)=='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac'
ida_auto.auto_wait();functions=[]
index_path=Path('/index/world-army-consumers-r1.json');index=json.loads(index_path.read_text(encoding='utf-8'))
assert index['source_sha256']==sha(source)and index['database_sha256']==sha(database)
for at in [0x12dde,0x132b4,0x132e0,0x11abe]:
 f=ida_funcs.get_func(at);assert f and f.start_ea==at
 lines=[]
 for ea in idautils.FuncItems(at):
  lines.append(dict(ida_linear=ea,original_file_offset=ida_loader.get_fileregion_offset(ea),bytes=ida_bytes.get_bytes(ea,idc.get_item_size(ea)).hex(),instruction=idc.generate_disasm_line(ea,0),operands=[dict(index=i,type=idc.get_operand_type(ea,i),value=idc.get_operand_value(ea,i))for i in range(3)if idc.get_operand_type(ea,i)]))
 refs=[]
 for x in idautils.XrefsTo(at):
  parent=ida_funcs.get_func(x.frm);refs.append(dict(source=x.frm,type=x.type,function=parent.start_ea if parent else None,instruction=idc.generate_disasm_line(x.frm,0)))
 entry=next((v for v in index['functions']if int(v['ida_mz_linear'],16)==at),None)
 note=dict(level=entry['level']if entry else 'unknown',semantic=entry['semantic_note']if entry else None,source='docs/spec/world-army-consumers-r1.json',warning=None if entry and entry['level']=='proven'else 'UNPROVEN SEMANTIC')
 functions.append(dict(name=ida_funcs.get_func_name(at),start=at,end=f.end_ea,xrefs=refs,lines=lines,indexed_semantic=note,indexed_operands=[]))
Path('/out/ida-original-guards-r2.json').write_text(json.dumps(dict(schema=1,tool='IDA 9.4',uid=os.getuid(),exporter_sha256=sha(Path(__file__)),index_sha256=sha(index_path),source_sha256=sha(source),database_sha256=sha(database),address_space='IDA MZ loader linear, base 0x10000; file offsets labelled separately',function_count=len(list(idautils.Functions())),functions=functions,limits=['Static source and xrefs only. No renaming, patching or gameplay completion claim.','Functions without a graded index entry remain explicitly unknown. No ungraded prose imported.']),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
idaapi.qexit(0)
