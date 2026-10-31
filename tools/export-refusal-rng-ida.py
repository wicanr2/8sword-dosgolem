"""Bounded original refusal/RNG consumer evidence, without renaming the database."""
import hashlib,json,os
from pathlib import Path
import ida_auto,ida_bytes,ida_funcs,ida_loader,idaapi,idautils,idc
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source,database=Path('/game/PAM.AY'),Path('/source/PAM.i64')
assert os.getuid()==1000 and idaapi.get_kernel_version()=='9.4'
assert sha(source)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
assert sha(database)=='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac'
ida_auto.auto_wait()
count=len(list(idautils.Functions()));assert count==521
Path('/out/identity.json').write_text(json.dumps(dict(kernel=idaapi.get_kernel_version(),uid=os.getuid(),function_count=count,source_sha256=sha(source),database_sha256=sha(database)))+'\n')
functions=[]
index_path=Path('/index/world-army-consumers-r1.json')
index=json.loads(index_path.read_text(encoding='utf-8'));assert index['source_sha256']==sha(source)and index['database_sha256']==sha(database)
for at in [0x10ee8,0x111fe,0x1151c,0x11796,0x205e6,0x215f8,0x2953e]:
 f=ida_funcs.get_func(at);assert f is not None and f.start_ea==at,hex(at)
 entry=next((v for v in index['functions']if int(v['ida_mz_linear'],16)==at),None)
 annotation=dict(note=entry['semantic_note']if entry else None,level=entry['level']if entry else'unknown',source='docs/spec/world-army-consumers-r1.json',resolution=entry.get('resolution')if entry else None,warning=None if entry and entry['level']=='proven'else'UNPROVEN SEMANTIC: original function name and bytes only')
 functions.append(dict(start=at,end=f.end_ea,name=ida_funcs.get_func_name(at),indexed_semantic=annotation,xrefs=[dict(source=x.frm,type=x.type)for x in idautils.XrefsTo(at)],lines=[dict(ida_linear=ea,file_offset=ida_loader.get_fileregion_offset(ea),bytes=ida_bytes.get_bytes(ea,idc.get_item_size(ea)).hex(),instruction=idc.generate_disasm_line(ea,0))for ea in idautils.FuncItems(at)]))
Path('/out/ida-refusal-rng-r1.json').write_text(json.dumps(dict(tool='IDA Pro 9.4',uid=os.getuid(),source_sha256=sha(source),database_sha256=sha(database),exporter_sha256=sha(Path(__file__)),index_sha256=sha(index_path),address_space='IDA MZ loader linear base 0x10000; file offsets explicit',functions=functions,level='static bytes; dynamic controls required'),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
idaapi.qexit(0)
