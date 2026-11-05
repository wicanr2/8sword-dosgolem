"""031：唯讀來源的F1人物頁資料流；只寫一次性DB的外部匯出。"""
import hashlib,json,os
from pathlib import Path
import ida_auto,ida_bytes,ida_funcs,ida_loader,idaapi,idautils,idc
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert os.getuid()==1000 and idaapi.get_kernel_version()=="9.4"
assert sha('/game/PAM.AY')=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
assert sha('/source/PAM.i64')=='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac'
ida_auto.auto_wait();functions=list(idautils.Functions());assert len(functions)==521
probe=dict(schema=1,uid=os.getuid(),version=idaapi.get_kernel_version(),functions=len(functions),source_sha256=sha('/game/PAM.AY'),database_sha256=sha('/source/PAM.i64'))
Path('/out/evidence/ida-probe.json').write_text(json.dumps(probe),encoding='utf-8')
def line(at):
 return dict(ida_linear=at,file_offset=ida_loader.get_fileregion_offset(at),bytes=ida_bytes.get_bytes(at,idc.get_item_size(at)).hex(),instruction=idc.generate_disasm_line(at,0),operands=[dict(index=i,type=idc.get_operand_type(at,i),value=idc.get_operand_value(at,i))for i in range(3)if idc.get_operand_type(at,i)])
f=ida_funcs.get_func(0x173f0);assert f
body=dict(name=ida_funcs.get_func_name(f.start_ea),start=f.start_ea,end=f.end_ea,lines=[line(at)for at in idautils.FuncItems(f.start_ea)],xrefs=[dict(source=x.frm,type=x.type)for x in idautils.XrefsTo(f.start_ea)])
wait=ida_funcs.get_func(0x1844c);assert wait
wait_body=dict(name=ida_funcs.get_func_name(wait.start_ea),start=wait.start_ea,end=wait.end_ea,lines=[line(at)for at in idautils.FuncItems(wait.start_ea)])
Path('/out/evidence/ida-character.json').write_text(json.dumps(dict(probe=probe,tool='IDA Pro 9.4',exporter_sha256=sha(__file__),address_space='IDA MZ base10000h; runtime CS0110 IP=linear-10000h; DS1E88 independent; file offsets explicit',query_173f0=line(0x173f0),functions=[body,wait_body]),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
idaapi.qexit(0)
