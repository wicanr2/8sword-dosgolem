#!/usr/bin/env python3
"""Rust F1：固定原欄位、批准頭像、抽驗及本機永久保存。"""
import argparse,gzip,hashlib,importlib.util,io,json,os,shutil,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-character-r1';REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def module(r,n):
 s=importlib.util.spec_from_file_location(n,r/'tools'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['prepare','freeze','audit','archive','verify','images'])
 for n in ['project','work','out','archive']:ap.add_argument('--'+n,type=Path)
 a=ap.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  j=read(a.archive/(BATCH+'.json'))
  for f in j['files']:
   ob=j['objects'][f['sha256']];p=a.archive/BATCH/ob['file'];assert sha(p)==ob['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-rust-character',files=len(j['files']),objects=len(j['objects'])));return
 r=a.project;q=a.work or r/REL;h=module(r,'prepare-owned-army-ui.py')
 if a.action=='prepare':
  from PIL import Image
  assert q.is_dir()and(q/'evidence/ida-character.json').is_file();(q/'native/pack').mkdir(parents=True)
  for f in read(r/'preserved/rust-treasure-r1.json')['files']:
   if '/native/pack/'in f['path']:(q/'native/pack'/Path(f['path']).name).write_bytes(h.stored(r,'rust-treasure-r1',f['path']))
  for name in ['gold','lead']:(q/f'evidence/{name}.chk').write_bytes(h.stored(r,'rust-treasure-r1',f'native/gui/{name}-auto.chk'))
  pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0';ds=struct.unpack_from('<H',pam,8)[0]*16+0x1d780
  labels=[pam[ds+1170+i*12:ds+1182+i*12].split(b'\0')[0].decode('big5')for i in range(8)]
  lines=['# fixed PAM F1 labels; original x-byte *24, y *6 +48']+[f'STAT\t{i}\t72\t{426+i*108}\t336\t{v}'for i,v in enumerate(labels[:6])]+[f'HEADING\t{i}\t{v}'for i,v in enumerate(labels[6:])];(q/'character-layout.tsv').write_text('\n'.join(lines)+'\n')
  idx=read(r/'artwork/manifest.json');art=next(v for v in idx['files']if v['path']=='approved/masters/hero-portrait-r3.png');source=r/'artwork'/art['path'];assert sha(source)==art['sha256']=='b97e3a9c908db0ce66b5579478fa40551e93d8ff9d91622cf89427eed4fa1e41';raw=Image.open(source).convert('RGBA').resize((240,240),Image.Resampling.LANCZOS).tobytes();fnv=module(r,'rust-native-player.py').fnv;body=b'8SRGBA01'+struct.pack('<II',240,240)+raw;(q/'native/pack/hero-portrait.rgba').write_bytes(body+struct.pack('<Q',fnv(body)))
  catalog=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));path='workplace/probe-20261023/graphics-first/battle-r1/choi-source-normal-r1/13-F1-character.json';old=next(v for v in catalog['files']if v['path']==path);raw=gzip.decompress((r/'preserved'/catalog['objects'][old['sha256']]['path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==old['sha256'];(q/'evidence/original-character.json').write_bytes(raw);strings=[v for v in json.loads(raw)['strings']if v['Source']in range(1170,1243,12)];assert len(strings)==7 and [v['Text']for v in strings]==labels[:7]
  write(q/'evidence/source.json',dict(status='passed-character-source',pam_sha256=hashlib.sha256(pam).hexdigest(),labels=labels,original_receipt=old,portrait=art,original_positions=strings,grade='proven static IDA field consumers plus inherited original dosgolem text events; no new original playthrough'));return
 if a.action=='freeze':
  shutil.copytree(r/'internal/remake-rust',q/'rust-source');(q/'tools').mkdir()
  for n in ['rust-character.py','rust-character-gui.py','rust-native-player.sh','export-rust-character-ida.py']:shutil.copy2(r/'tools'/n,q/'tools'/n)
  write(q/'media.json',{p.name:sha(p)for p in(q/'native/pack').iterdir()if p.is_file()});return
 if a.action=='audit':
  counts={k:len(v)for k,v in h.dependencies(r).items()};assert list(counts.values())==[197,7,923,535]
  crate={str(p.relative_to(r/'internal/remake-rust')):sha(p)for p in(r/'internal/remake-rust').rglob('*')if p.is_file()};assert all(sha(q/'rust-source'/p)==v for p,v in crate.items());assert all(sha(q/'native/pack'/p)==v for p,v in read(q/'media.json').items());assert(q/'character-layout.tsv').read_bytes()==(r/'internal/remake-rust/character-layout.tsv').read_bytes();assert'65 passed; 0 failed'in(q/'native/tests.log').read_text()
  ida=read(q/'evidence/ida-character.json');assert ida['probe']['functions']==521 and ida['probe']['uid']==1000 and ida['probe']['version']=='9.4';assert ida['exporter_sha256']==sha(r/'tools/export-rust-character-ida.py');assert ida['functions'][0]['start']==0x17242
  pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()==ida['probe']['source_sha256'];assert sha(r/'workplace/probe-20261023/text-first/PAM.i64')==ida['probe']['database_sha256'];word=lambda at:struct.unpack_from('<H',pam,at)[0];header=word(8)*16;relocs=[header+word(word(24)+i*4+2)*16+word(word(24)+i*4)for i in range(word(6))];checked=0
  for f in ida['functions']:
   for v in f['lines']:
    at=v['file_offset'];want=bytes.fromhex(v['bytes']);assert at==v['ida_linear']-0x10000+header;raw=bytearray(pam[at:at+len(want)])
    for off in relocs:
     if at<=off and off+2<=at+len(want):struct.pack_into('<H',raw,off-at,(struct.unpack_from('<H',raw,off-at)[0]+0x1000)&65535)
    assert bytes(raw)==want;checked+=1
  gui=read(q/'native/gui/receipt.json');assert gui['status']=='passed-rust-character-gui'and gui['binary_sha256']==sha(q/'native/8sword-remake')
  from PIL import Image
  fnv=module(r,'rust-native-player.py').fnv
  for run in gui['runs']:
   assert run['exit']==0
   for cap in run['captures']:
    f=q/'native/gui'/run['name']/f"frame-{cap['number']:03}.ppm";assert f.read_bytes()==f.with_name(f"readback-{cap['number']:03}.ppm").read_bytes();assert cap['captured']['frame_hash']==format(fnv(Image.open(f).convert('RGBA').tobytes()),'016x')
  write(a.out,dict(status='passed-rust-character-audit',crate=crate,binary_sha256=sha(q/'native/8sword-remake'),baseline=counts,source=read(q/'evidence/source.json'),ida_lines_verified=checked,gui=gui,execution=read(q/'execution.json'),limits=['Only six character fields and empty treasure/sword headings; no item ownership or effects ported.','v4 unchanged; native Linux sampled, no mobile or Release.']));return
 if a.action=='images':
  from PIL import Image,ImageDraw,ImageFont
  idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));fh=h.FONT_SHA['noto'];raw=gzip.decompress((r/'preserved'/idx['objects'][fh]['path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==fh;font=ImageFont.truetype(io.BytesIO(raw),30,index=3)
  gui=read(q/'native/gui/receipt.json');canvas=Image.new('RGB',(1920,1440),(9,36,29));draw=ImageDraw.Draw(canvas);sources=[]
  for i,(run,label,title)in enumerate([('fresh','noto','原起點：F1檢視主角'),('fresh','lishu','教育部隸書：保留原版六欄'),('gold','gold','寶箱領金後：現金530'),('lead','lead','寶箱分贈後：領導能力103')]):
   row=next(v for v in gui['runs']if v['name']==run);cap=next(v for v in row['captures']if v['label']==label);f=q/'native/gui'/run/f"frame-{cap['number']:03}.ppm";x=i%2*960;y=i//2*720;draw.text((x+12,y+12),title,font=font,fill=(239,216,155));canvas.paste(Image.open(f).resize((960,660),Image.Resampling.LANCZOS),(x,y+60));sources.append(dict(run=run,label=label,sha256=sha(f),captured=cap['captured']))
  assert not a.out.exists();canvas.save(a.out);write(a.out.with_suffix('.json'),dict(platform='Linux Rust SDL2',binary_sha256=gui['binary_sha256'],image_sha256=sha(a.out),scope='F1 normal input and inherited genuine chest saves; original layout evidence, not original framebuffer parity',sources=sources));return
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for p in sorted(q.rglob('*')):
  if not p.is_file()or'rust-target'in p.relative_to(q).parts:continue
  assert p.stat().st_uid==1000 and not p.is_symlink();raw=p.read_bytes();v=hashlib.sha256(raw).hexdigest();obj=folder/(v+'.gz')
  if v not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[v]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(Path(REL)/p.relative_to(q)),sha256=v,bytes=len(raw),mode=p.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,rights='Full original-derived assets and binary local only; no Release'))
if __name__=='__main__':main()
