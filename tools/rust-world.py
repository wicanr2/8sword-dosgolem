#!/usr/bin/env python3
"""Rust世界移動預覽：字型、來源核對與本機永久保存。只在Docker執行。"""
import argparse,gzip,hashlib,importlib.util,io,json,os,shutil,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-world-r1'
REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def module(r,n):
 s=importlib.util.spec_from_file_location(n,r/'tools'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['prepare','fonts','freeze','audit','archive','verify'])
 for n in ['project','work','archive','out','game','assets']:ap.add_argument('--'+n,type=Path)
 a=ap.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  idx=read(a.archive/(BATCH+'.json'))
  for row in idx['files']:
   ob=idx['objects'][row['sha256']];p=a.archive/BATCH/ob['file'];assert sha(p)==ob['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==row['bytes']and hashlib.sha256(raw).hexdigest()==row['sha256']
  write(a.out,dict(status='passed-detached-rust-world',files=len(idx['files']),objects=len(idx['objects'])));return
 r=a.project;q=a.work or r/REL
 if a.action=='prepare':
  assert not q.exists();q.mkdir();(q/'native/pack').mkdir(parents=True);(q/'evidence').mkdir();helper=module(r,'prepare-owned-army-ui.py');parent='rust-battle-checkpoint-r1';prefix=REL.replace(BATCH,parent)+'/native/pack/'
  for row in read(r/f'preserved/{parent}.json')['files']:
   if row['path'].startswith(prefix):(q/'native/pack'/Path(row['path']).name).write_bytes(helper.stored(r,parent,row['path']))
  pam=(a.game/'PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0';ds=struct.unpack_from('<H',pam,8)[0]*16+0x1d780
  word=lambda off:struct.unpack_from('<H',pam,ds+off)[0];lines=[];maps={}
  for i in range(8):
   p=a.game/f'MAP{i+1}.AY';maps[p.name]=sha(p);shutil.copy2(p,q/f'native/pack/map{i+1}.ay');lines.append(f'START\t{i}\t{word(0x3be+i*4)}\t{word(0x3c0+i*4)}')
  assert[word(o)for o in [0x56da,0x4f2,0x56c4,0x56cc,0x56ce]]==[324,1,3,0,0];lines.append('CLOCK\t324\t1\t3')
  for i in range(7):
   raw=pam[ds+0x3de+20*i:ds+0x3de+20*(i+1)];label=raw.split(b'\0')[0].decode('big5');lines.append(f'MENU\t{word(0x46a+i*4)}\t{word(0x46c+i*4)}\t{label}')
  (q/'native/pack/world-start.tsv').write_text('\n'.join(lines)+'\n');music=next(v for v in read(a.assets/'music.json')['cues']if v['id']==2);p=a.assets/music['file'];assert sha(p)==music['sha256'];shutil.copy2(p,q/'native/pack/world-music.ogg');write(q/'evidence/world-inputs.json',dict(maps=maps,pam_sha256=hashlib.sha256(pam).hexdigest(),music=music,initial_data=lines));return
 if a.action=='fonts':
  from PIL import Image,ImageFont,ImageDraw
  helper=module(r,'prepare-owned-army-ui.py');idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));faces={}
  for key,h in helper.FONT_SHA.items():
   raw=gzip.decompress((r/'preserved'/idx['objects'][h]['path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==h;faces[key]=ImageFont.truetype(io.BytesIO(raw),48,index=3 if key in ['noto','serif']else 0)
  wanted=(q/'native/pack/world-start.tsv').read_text()
  for p in(r/'internal/remake-rust/src').glob('*.rs'):wanted+=''.join(c for c in p.read_text()if ord(c)>127 and c.isprintable())
  old=(q/'native/pack/font-noto.bin').read_bytes();chars={chr(struct.unpack_from('<I',old,i)[0])for i in range(12,len(old)-8,4100)}|set(wanted)-set('\n\t')
  rows=[]
  for key in ['noto','lishu','caoshu']:
   face=faces[key];missing=face.getmask('\U0010ffff');missing=(missing.size,bytes(missing));raw=bytearray(b'8SGLYP01'+struct.pack('<I',len(chars)));fallbacks=[]
   for ch in sorted(chars):
    mask=face.getmask(ch);cjk=0x3400<=ord(ch)<=0x9fff;native=key=='noto'or(cjk and(mask.size,bytes(mask))!=missing and bool(mask.getbbox()));chosen=face if native else faces['serif']if key=='lishu'and cjk else faces['noto']
    if not native:fallbacks.append(ch)
    cell=Image.new('L',(64,64));b=chosen.getbbox(ch);w,h=b[2]-b[0],b[3]-b[1];ImageDraw.Draw(cell).text(((64-w)//2-b[0],(64-h)//2-b[1]),ch,font=chosen,fill=255);raw.extend(struct.pack('<I',ord(ch)));raw.extend(cell.tobytes())
   raw.extend(struct.pack('<Q',module(r,'rust-native-player.py').fnv(raw)));(q/f'native/pack/font-{key}.bin').write_bytes(raw);rows.append(dict(id=key,glyphs=len(chars),fallbacks=''.join(fallbacks)))
  write(a.out,dict(fonts=rows,sources=helper.FONT_SHA));return
 if a.action=='freeze':
  shutil.copytree(r/'internal/remake-rust',q/'rust-source');(q/'tools').mkdir()
  for n in ['rust-world.py','rust-world-gui.py','export-rust-world-ida.py','rust-native-player.sh']:shutil.copy2(r/'tools'/n,q/'tools'/n)
  for n in ['internal/ownedworld/rust_world_reference_test.go','internal/eightsword/rust_world_media_test.go']:shutil.copy2(r/n,q/'evidence'/Path(n).name)
  write(q/'media.json',{p.name:sha(p)for p in(q/'native/pack').iterdir()if p.is_file()});return
 if a.action=='audit':
  counts={k:len(v)for k,v in module(r,'prepare-owned-army-ui.py').dependencies(r).items()};assert list(counts.values())==[197,7,923,535]
  crate={str(p.relative_to(r/'internal/remake-rust')):sha(p)for p in(r/'internal/remake-rust').rglob('*')if p.is_file()};assert all(sha(q/'rust-source'/n)==h for n,h in crate.items())
  assert all(sha(q/'native/pack'/n)==h for n,h in read(q/'media.json').items())
  log=(q/'native/tests.log').read_text();assert 'FAILED'not in log and 'test result: ok.'in log
  assert '40 passed'in log
  assert(q/'world-oracle.log').read_text().rstrip().endswith('PASS')or'PASS\n'in(q/'world-oracle.log').read_text()
  original=(q/'world-reference.tsv').read_bytes();assert original==(r/'internal/remake-rust/world-reference.tsv').read_bytes();assert len(original.decode().splitlines())==881
  decode=module(r,'prepare-hd-intro.py').decode;fnv=module(r,'rust-native-player.py').fnv
  expected={str(i):format(fnv(bytes(v-48 for row in[decode((q/f'native/pack/map{i}.ay').read_bytes())[y*72:y*72+70]for y in range(80)]for v in row)),'016x')for i in range(1,9)}
  got={f[1]:f[2]for line in(q/'native/world-check.tsv').read_text().splitlines()if(f:=line.split('\t'))[0]=='MAP'};assert got==expected
  assert 'MEDIA\t65\t12\t3\t3840000'in(q/'native/world-check.tsv').read_text()
  gui=read(q/'native/gui/receipt.json');assert gui['status']=='passed-rust-world-gui'and gui['binary_sha256']==sha(q/'native/8sword-remake')
  from PIL import Image
  for row in gui['runs']:
   assert row['exit']==0
   for cap in row['captures']:
    p=q/'native/gui'/row['name']/f"frame-{cap['number']:03}.ppm";assert p.read_bytes()==p.with_name(f"readback-{cap['number']:03}.ppm").read_bytes()
    assert cap['captured']['frame_hash']==format(module(r,'rust-native-player.py').fnv(Image.open(p).convert('RGBA').tobytes()),'016x')
  write(a.out,dict(status='passed-rust-world-audit',crate=crate,binary_sha256=sha(q/'native/8sword-remake'),baseline_counts=counts,gui=gui,inputs=read(q/'evidence/world-inputs.json'),execution=read(q/'execution.json'),limits=['Bounded world movement preview; events, monthly and battle handoff remain DRAFT.','880 controlled original CPU cases; no original full world same-state or natural new-game claim.','RNG excludes original UI ambient calls. Event preflight keeps previous state and halts.','Development world checkpoint separate from battle/Go save; no army/resources or old save import.','Approved HD caches and OGG; no new human listening or animation timing acceptance.']));return
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for p in sorted(q.rglob('*')):
  if not p.is_file()or any(n in p.relative_to(q).parts for n in ['go-cache','rust-target']):continue
  assert p.stat().st_uid==1000 and not p.is_symlink();raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();obj=folder/(h+'.gz')
  if h not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(Path(REL)/p.relative_to(q)),bytes=len(raw),sha256=h,mode=p.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,rights='Full original-derived media, maps, binary and IDA evidence local only; no Release'))
if __name__=='__main__':main()
