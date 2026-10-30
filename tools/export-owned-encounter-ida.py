"""030 DRAFT: fixed versus random encounter ownership; preserve original names."""
import hashlib
import json
import os
from pathlib import Path
import ida_auto
import ida_bytes
import ida_funcs
import ida_loader
import idaapi
import idautils
import idc

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

assert os.getuid() == 1000 and idaapi.get_kernel_version() == "9.4"
source, database = Path("/game/PAM.AY"), Path("/source/PAM.i64")
assert sha(source) == "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"
assert sha(database) == "a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac"
ida_auto.auto_wait()
assert len(list(idautils.Functions())) == 521
functions = []
for start in [0x11abe, 0x13aec]:
    f = ida_funcs.get_func(start)
    assert f is not None and f.start_ea == start
    functions.append(dict(start=start,end=f.end_ea,name=ida_funcs.get_func_name(start),
        xrefs=[dict(source=x.frm,type=x.type) for x in idautils.XrefsTo(start)],
        lines=[dict(ida_linear=ea,file_offset=ida_loader.get_fileregion_offset(ea),
                    bytes=ida_bytes.get_bytes(ea,idc.get_item_size(ea)).hex(),
                    instruction=idc.generate_disasm_line(ea,0)) for ea in idautils.FuncItems(start)]))
result=dict(schema=1,tool="IDA Pro 9.4",input_sha256=sha(source),database_sha256=sha(database),
            exporter_sha256=sha(Path(__file__)),address_space="IDA MZ loader linear base 0x10000; file offsets separate",
            functions=functions,level="static bytes; dynamic contracts require explicit controls")
Path("/out/ida-encounter-r1.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
idaapi.qexit(0)
