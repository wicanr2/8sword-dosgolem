"""Narrow map unpack/prepare evidence for the already proven origin branch."""
import hashlib,json,os
from pathlib import Path
import ida_auto,ida_bytes,ida_funcs,ida_loader,idaapi,idautils,idc
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert os.getuid()==1000 and idaapi.get_kernel_version()=='9.4'
source=Path('/game/PAM.AY');database=Path('/source/PAM.i64')
assert sha(source)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
assert sha(database)=='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac'
ida_auto.auto_wait();count=len(list(idautils.Functions()));assert count==521
index_path=Path('/index/world-army-consumers-at-origin-export.json');index=json.loads(index_path.read_text());assert index['source_sha256']==sha(source) and index['database_sha256']==sha(database)
annotations=index['functions']+index.get('origin_map_evidence',{}).get('functions',[])
functions=[]
for at in [0x1041e,0x145fa,0x251de,0x252e4]:
    f=ida_funcs.get_func(at);assert f is not None and f.start_ea==at,hex(at)
    entry=next((x for x in annotations if int(x['ida_mz_linear'],16)==at),None)
    note=dict(note=entry['semantic_note']if entry else None,level=entry['level']if entry else 'unknown',source='docs/spec/world-army-consumers-r1.json',warning=None if entry and entry['level']=='proven' else 'UNPROVEN SEMANTIC')
    functions.append(dict(indexed_semantic=note,indexed_operands=[x for x in index.get('origin_map_evidence',{}).get('operands',[])if x['original_name']==ida_funcs.get_func_name(at)],start=at,end=f.end_ea,name=ida_funcs.get_func_name(at),level='unknown',semantic_source='Original bytes only; interpretation reviewed in spec030.',xrefs=[dict(source=x.frm,type=x.type)for x in idautils.XrefsTo(at)],lines=[dict(ida_linear=ea,file_offset=ida_loader.get_fileregion_offset(ea),bytes=ida_bytes.get_bytes(ea,idc.get_item_size(ea)).hex(),instruction=idc.generate_disasm_line(ea,0))for ea in idautils.FuncItems(at)]))
Path('/out/ida-origin-r3.json').write_text(json.dumps(dict(tool='IDA Pro 9.4',uid=os.getuid(),function_count=count,source_sha256=sha(source),database_sha256=sha(database),exporter_sha256=sha(Path(__file__)),index_sha256=sha(index_path),address_space='IDA MZ loader linear base0x10000; file offsets separately recorded',functions=functions),ensure_ascii=False,indent=2)+'\n')
idaapi.qexit(0)
