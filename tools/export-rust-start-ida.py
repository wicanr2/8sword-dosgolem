"""PAM開始選單／初始化的非破壞性證據匯出。只跑一次性DB。"""
import hashlib,json,os
from pathlib import Path
import ida_auto,ida_bytes,ida_funcs,ida_loader,idaapi,idautils,idc
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert os.getuid()==1000 and idaapi.get_kernel_version()=='9.4'
assert sha('/game/PAM.AY')=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
assert sha('/source/PAM.i64')=='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac'
ida_auto.auto_wait();assert len(list(idautils.Functions()))==521
probe=dict(schema=1,uid=os.getuid(),version=idaapi.get_kernel_version(),functions=521,source_sha256=sha('/game/PAM.AY'),database_sha256=sha('/source/PAM.i64'))
Path('/out/evidence/ida-probe.json').write_text(json.dumps(probe)+'\n')
def line(at):
 return dict(ida_linear=at,file_offset=ida_loader.get_fileregion_offset(at),bytes=ida_bytes.get_bytes(at,idc.get_item_size(at)).hex(),instruction=idc.generate_disasm_line(at,0),operands=[dict(index=i,type=idc.get_operand_type(at,i),value=idc.get_operand_value(at,i))for i in range(3)if idc.get_operand_type(at,i)])
selected=set()
for at in [0x1020e,0x1041e,0x104a6,0x1055f,0x10622,0x106b7,0x1090c,0x109b5,0x10b38,0x1430e,0x1434e,0x171d8,0x18d38,0x184c0]:
 f=ida_funcs.get_func(at);assert f;selected.add(f.start_ea)
functions=[]
for at in sorted(selected):
 f=ida_funcs.get_func(at);functions.append(dict(name=ida_funcs.get_func_name(at),start=f.start_ea,end=f.end_ea,lines=[line(ea)for ea in idautils.FuncItems(at)],xrefs=[dict(source=x.frm,type=x.type)for x in idautils.XrefsTo(at)]))
Path('/out/evidence/ida-start.json').write_text(json.dumps(dict(probe=probe,tool='IDA Pro 9.4',exporter_sha256=sha(__file__),address_space='IDA MZ loader base10000h; runtime CS0110 IP=linear-10000h; DS1E88 offsets separate',functions=functions),ensure_ascii=False,indent=2)+'\n')
idaapi.qexit(0)
