#!/usr/bin/env python3
"""空軍隊遇劫：來源核對、素材還原與永久保存。限Docker。"""
import argparse,gzip,hashlib,importlib.util,io,json,os,shutil,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-empty-army-r1';REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def module(r,n):
 s=importlib.util.spec_from_file_location(n,r/'tools'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['prepare','restore','freeze','audit','images','archive','verify'])
 for n in ['project','work','out','archive']:ap.add_argument('--'+n,type=Path)
 a=ap.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  idx=read(a.archive/(BATCH+'.json'))
  for f in idx['files']:
   ob=idx['objects'][f['sha256']];p=a.archive/BATCH/ob['file'];assert sha(p)==ob['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-rust-empty-army',files=len(idx['files']),objects=len(idx['objects'])));return
 r=a.project;q=a.work or r/REL;h=module(r,'prepare-owned-army-ui.py')
 if a.action in ['archive','restore']:
  base=module(r,'rust-world-exits.py');base.BATCH=BATCH;base.REL=REL;base.main();return
 if a.action=='prepare':
  for f in read(r/'preserved/rust-special-shore-r1.json')['files']:
   if '/native/pack/'in f['path']:(q/'native/pack'/Path(f['path']).name).write_bytes(h.stored(r,'rust-special-shore-r1',f['path']))
  (q/'native/legacy-v11.chk').write_bytes(h.stored(r,'rust-special-shore-r1','native/gui/cold-exit-store/journey.chk'))
  functions=[];inputs=[]
  for batch,name,fn in [('rust-world-exits-r1','evidence/ida-exits.json','sub_1151C'),('rust-character-r1','evidence/ida-character.json','sub_1844C')]:
   raw=h.stored(r,batch,name);v=json.loads(raw);functions.append(next(f for f in v['functions']if f['name']==fn));inputs.append(dict(batch=batch,path=name,sha256=hashlib.sha256(raw).hexdigest(),exporter_sha256=v['exporter_sha256']))
  write(q/'evidence/ida-theft.json',dict(probe=v['probe'],tool='IDA Pro9.4 archived exports, no new DB mutation',address_space='IDA MZ base10000h; runtime CS0110 IP=linear-10000h; runtime DS1E88 offsets separate',inputs=inputs,functions=functions));return
 if a.action=='freeze':
  shutil.copytree(r/'internal/remake-rust',q/'rust-source');(q/'tools').mkdir()
  for n in ['rust-empty-army.py','rust-world-exits.py','rust-empty-army-gui.py','rust-empty-army-reference.go','rust-native-player.sh','rust-world.py']:shutil.copy2(r/'tools'/n,q/'tools'/n)
  write(q/'media.json',{p.name:sha(p)for p in(q/'native/pack').iterdir()if p.is_file()});return
 if a.action=='audit':
  counts={k:len(v)for k,v in h.dependencies(r).items()};assert list(counts.values())==[197,7,923,535]
  crate={str(p.relative_to(r/'internal/remake-rust')):sha(p)for p in(r/'internal/remake-rust').rglob('*')if p.is_file()};assert all(sha(q/'rust-source'/p)==v for p,v in crate.items());assert all(sha(q/'native/pack'/p)==v for p,v in read(q/'media.json').items());assert '130 passed; 0 failed'in(q/'native/tests.log').read_text();assert(q/'evidence/theft-reference.tsv').read_bytes()==(r/'internal/remake-rust/theft-reference.tsv').read_bytes();assert len((q/'evidence/theft-reference.tsv').read_text().splitlines())==305
  import struct
  pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();word=lambda at:struct.unpack_from('<H',pam,at)[0];header=word(8)*16;relocs=[header+word(word(24)+i*4+2)*16+word(word(24)+i*4)for i in range(word(6))];j=read(q/'evidence/ida-theft.json');assert hashlib.sha256(pam).hexdigest()==j['probe']['source_sha256'];assert sha(r/'workplace/probe-20261023/text-first/PAM.i64')==j['probe']['database_sha256'];checked=0
  for f in j['functions']:
   for v in f['lines']:
    at=v['file_offset'];want=bytes.fromhex(v['bytes']);assert at==v['ida_linear']-0x10000+header;raw=bytearray(pam[at:at+len(want)])
    for off in relocs:
     if at<=off and off+2<=at+len(want):struct.pack_into('<H',raw,off-at,(struct.unpack_from('<H',raw,off-at)[0]+0x1000)&65535)
    assert bytes(raw)==want;checked+=1
  strings={}
  for offset in [0x4555,0x4658]:strings[hex(offset)]=pam[header+0x1d780+offset:].split(bytes([0]),1)[0].decode('big5')
  gui=read(q/'native/gui/receipt.json');assert gui['status']=='passed-rust-empty-army-gui'and gui['binary_sha256']==sha(q/'native/8sword-remake')and len(gui['runs'])==3
  from PIL import Image
  fnv=module(r,'rust-native-player.py').fnv
  for run in gui['runs']:
   assert run['exit']==0
   for cap in run['captures']:
    f=q/'native/gui'/run['name']/f"frame-{cap['number']:03}.ppm";assert f.read_bytes()==f.with_name(f"readback-{cap['number']:03}.ppm").read_bytes();assert cap['captured']['frame_hash']==format(fnv(Image.open(f).convert('RGBA').tobytes()),'016x')
  write(a.out,dict(status='passed-rust-empty-army-audit',crate=crate,binary_sha256=sha(q/'native/8sword-remake'),baseline=counts,original_loss_cases=286,original_army_cases=18,ida_functions=len(j['functions']),ida_lines_verified=checked,source_strings=strings,gui=gui,execution=read(q/'execution.json')));return
 if a.action=='images':
  from PIL import Image,ImageDraw,ImageFont
  idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));raw=gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes());font=ImageFont.truetype(io.BytesIO(raw),30,index=3);gui=read(q/'native/gui/receipt.json');canvas=Image.new('RGB',(1920,1440),(9,36,29));draw=ImageDraw.Draw(canvas);sources=[]
  for i,(run,label,title)in enumerate([('dismiss','dismissed','原F3解雇：六隊皆空'),('dismiss','pending','正常遇敵：空軍隊失金提示'),('cold-theft','cold-pending','F7獨立冷讀：同提示且不重扣'),('continued','walk','確認後冷讀：仍可正常移動')]):
   row=next(v for v in gui['runs']if v['name']==run);cap=next(v for v in row['captures']if v['label']==label);f=q/'native/gui'/run/f"frame-{cap['number']:03}.ppm";x=i%2*960;y=i//2*720;draw.text((x+12,y+12),title,font=font,fill=(239,216,155));canvas.paste(Image.open(f).resize((960,660),Image.Resampling.LANCZOS),(x,y+60));sources.append(dict(run=run,label=label,sha256=sha(f),captured=cap['captured']))
  assert not a.out.exists();canvas.save(a.out);write(a.out.with_suffix('.json'),dict(platform='Linux Rust SDL2',binary_sha256=gui['binary_sha256'],image_sha256=sha(a.out),scope='Real v11 progress, original start position and fixed seed controlled; army actually dismissed using F3; normal Space encounter and F7/cold confirmation; no runtime memory/IP injection',sources=sources));return
if __name__=='__main__':main()
