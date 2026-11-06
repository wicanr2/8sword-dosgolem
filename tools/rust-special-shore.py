#!/usr/bin/env python3
"""特殊上岸：固定來源、抽驗與本機永久保存。限Docker。"""
import argparse,gzip,hashlib,importlib.util,io,json,os,shutil,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-special-shore-r1';REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
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
  write(a.out,dict(status='passed-detached-rust-special-shore',files=len(idx['files']),objects=len(idx['objects'])));return
 r=a.project;q=a.work or r/REL;h=module(r,'prepare-owned-army-ui.py')
 if a.action in ['archive','restore']:
  base=module(r,'rust-world-exits.py');base.BATCH=BATCH;base.REL=REL;base.main();return
 if a.action=='prepare':
  for f in read(r/'preserved/rust-world-exits-r1.json')['files']:
   if '/native/pack/'in f['path']:(q/'native/pack'/Path(f['path']).name).write_bytes(h.stored(r,'rust-world-exits-r1',f['path']))
  (q/'native/legacy-v10.chk').write_bytes(h.stored(r,'rust-world-exits-r1','native/gui/forward-store/journey.chk'));return
 if a.action=='freeze':
  shutil.copytree(r/'internal/remake-rust',q/'rust-source');(q/'tools').mkdir()
  for n in ['rust-special-shore.py','rust-world-exits.py','rust-special-shore-gui.py','export-rust-special-shore-ida.py','rust-special-shore-reference.go','rust-native-player.sh','rust-world.py']:shutil.copy2(r/'tools'/n,q/'tools'/n)
  write(q/'media.json',{p.name:sha(p)for p in(q/'native/pack').iterdir()if p.is_file()});return
 if a.action=='audit':
  counts={k:len(v)for k,v in h.dependencies(r).items()};assert list(counts.values())==[197,7,923,535]
  crate={str(p.relative_to(r/'internal/remake-rust')):sha(p)for p in(r/'internal/remake-rust').rglob('*')if p.is_file()};assert all(sha(q/'rust-source'/p)==v for p,v in crate.items());assert all(sha(q/'native/pack'/p)==v for p,v in read(q/'media.json').items());assert '122 passed; 0 failed'in(q/'native/tests.log').read_text()
  assert(q/'evidence/special-shore-reference.tsv').read_bytes()==(r/'internal/remake-rust/special-shore-reference.tsv').read_bytes();assert len((q/'evidence/special-shore-reference.tsv').read_text().splitlines())==317
  import struct
  pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();word=lambda at:struct.unpack_from('<H',pam,at)[0];header=word(8)*16;relocs=[header+word(word(24)+i*4+2)*16+word(word(24)+i*4)for i in range(word(6))];j=read(q/'evidence/ida-shore.json');assert hashlib.sha256(pam).hexdigest()==j['probe']['source_sha256'];assert sha(r/'workplace/probe-20261023/text-first/PAM.i64')==j['probe']['database_sha256'];checked=0
  for f in j['functions']:
   for v in f['lines']:
    at=v['file_offset'];want=bytes.fromhex(v['bytes']);assert at==v['ida_linear']-0x10000+header;raw=bytearray(pam[at:at+len(want)])
    for off in relocs:
     if at<=off and off+2<=at+len(want):struct.pack_into('<H',raw,off-at,(struct.unpack_from('<H',raw,off-at)[0]+0x1000)&65535)
    assert bytes(raw)==want;checked+=1
  gui=read(q/'native/gui/receipt.json');assert gui['status']=='passed-rust-special-shore-gui'and gui['binary_sha256']==sha(q/'native/8sword-remake')and len(gui['runs'])==7
  from PIL import Image
  fnv=module(r,'rust-native-player.py').fnv
  for run in gui['runs']:
   assert run['exit']==0
   for cap in run['captures']:
    f=q/'native/gui'/run['name']/f"frame-{cap['number']:03}.ppm";assert f.read_bytes()==f.with_name(f"readback-{cap['number']:03}.ppm").read_bytes();assert cap['captured']['frame_hash']==format(fnv(Image.open(f).convert('RGBA').tobytes()),'016x')
  write(a.out,dict(status='passed-rust-special-shore-audit',crate=crate,binary_sha256=sha(q/'native/8sword-remake'),baseline=counts,original_flow_cases=288,original_lookup_cases=28,ida_functions=len(j['functions']),ida_lines_verified=checked,gui=gui,execution=read(q/'execution.json')));return
 if a.action=='images':
  from PIL import Image,ImageDraw,ImageFont
  idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));raw=gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes());font=ImageFont.truetype(io.BytesIO(raw),30,index=3);gui=read(q/'native/gui/receipt.json');canvas=Image.new('RGB',(1920,1440),(9,36,29));draw=ImageDraw.Draw(canvas);sources=[]
  for i,(run,label,title)in enumerate([('cold-treasure','chest','水岸寶箱：上岸後領取'),('shop','default-bridge','拒絕法術店上岸：原版預設造橋術'),('exit','crossed','拒絕出口上岸：仍跨區且不扣步'),('camp','camp','接受上岸：原式募兵與透明圖示')]):
   row=next(v for v in gui['runs']if v['name']==run);cap=next(v for v in row['captures']if v['label']==label);f=q/'native/gui'/run/f"frame-{cap['number']:03}.ppm";x=i%2*960;y=i//2*720;draw.text((x+12,y+12),title,font=font,fill=(239,216,155));canvas.paste(Image.open(f).resize((960,660),Image.Resampling.LANCZOS),(x,y+60));sources.append(dict(run=run,label=label,sha256=sha(f),captured=cap['captured']))
  assert not a.out.exists();canvas.save(a.out);write(a.out.with_suffix('.json'),dict(platform='Linux Rust SDL2',binary_sha256=gui['binary_sha256'],image_sha256=sha(a.out),scope='Controlled real water positions,boat2,seed1 from actual v10; subsequent normal keyboard/mouse only; no natural water-spell acquisition assertion',sources=sources));return
if __name__=='__main__':main()
