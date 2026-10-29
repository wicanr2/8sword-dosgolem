"""030 DRAFT: remaining spell entry/return bytes. Read-only original DB copy."""
import hashlib,json,os
from pathlib import Path
import ida_auto,ida_bytes,ida_funcs,ida_loader,idaapi,idautils,idc
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert os.getuid()==1000 and idaapi.get_kernel_version()=='9.4'
source=Path('/game/PAM.AY');db=Path('/source/PAM.i64')
assert sha(source)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
assert sha(db)=='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac'
ida_auto.auto_wait()
selected={0x1844c,0x1716c,0x13c18,0x13d74,0x168ce,0x1693c,0x16b20,0x16bea,0x16e32,0x180d8,0x16ef6,0x1e8a4,0x21000,0x21168}
def line(ea):return dict(ida_linear=ea,original_file_offset=ida_loader.get_fileregion_offset(ea),bytes=ida_bytes.get_bytes(ea,idc.get_item_size(ea)).hex(),instruction=idc.generate_disasm_line(ea,0))
rows=[]
for at in sorted(selected):
 f=ida_funcs.get_func(at);assert f and f.start_ea==at
 rows.append(dict(name=ida_funcs.get_func_name(at),start=at,end=f.end_ea,xrefs=[dict(source=x.frm,type=x.type)for x in idautils.XrefsTo(at)],lines=[line(ea)for ea in idautils.FuncItems(at)]))
Path('/out/ida-remaining.json').write_text(json.dumps(dict(schema=1,tool='IDA 9.4',tool_sha256=sha(Path(__file__)),source_sha256=sha(source),database_sha256=sha(db),address_space='IDA MZ loader linear base 0x10000; original file offsets separate',functions=rows,limits=['Static evidence; dynamic casts required. No rename or patch.']),indent=2)+'\n')
idaapi.qexit(0)
