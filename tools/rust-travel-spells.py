#!/usr/bin/env python3
"""Rust傳送術的來源核對、素材準備與永久保存。只在Docker執行。"""
import argparse,gzip,hashlib,importlib.util,io,json,os,shutil,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-travel-spells-r1';REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def module(r,n):
 s=importlib.util.spec_from_file_location(n,r/'tools'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['prepare','reference','freeze','audit','images','archive','verify'])
 for n in ['project','work','out','archive']:ap.add_argument('--'+n,type=Path)
 a=ap.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  idx=read(a.archive/(BATCH+'.json'))
  for f in idx['files']:
   ob=idx['objects'][f['sha256']];p=a.archive/BATCH/ob['file'];assert sha(p)==ob['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-rust-travel-spells',files=len(idx['files']),objects=len(idx['objects'])));return
 r=a.project;q=a.work or r/REL;h=module(r,'prepare-owned-army-ui.py')
 if a.action=='prepare':
  for f in read(r/'preserved/rust-survey-spells-r1.json')['files']:
   if '/native/pack/'in f['path']:(q/'native/pack'/Path(f['path']).name).write_bytes(h.stored(r,'rust-survey-spells-r1',f['path']))
  (q/'native/legacy-v7.chk').write_bytes(h.stored(r,'rust-survey-spells-r1','native/fixture-stop/journey.chk'))
  for suffix in ['entry.state','final.state','receipt.json']:(q/'evidence'/('teleport-'+suffix)).write_bytes(h.stored(r,'remaining-spells-r1','original-map-r8/map-7/'+suffix))
  return
 if a.action=='reference':
  pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();header=struct.unpack_from('<H',pam,8)[0]*16;ds=header+0x1d780
  names=[pam[ds+0x2c1c+12*i:ds+0x2c1c+12*i+12].split(b'\0')[0].decode('cp950')for i in range(8)]
  assert len(set(names))==8 and all(len(s.replace(' ',''))==3 for s in names)
  (q/'teleport-regions.tsv').write_text('# Original PAM.AY runtime DS:2C1C + 12*area, IDA sub_16EF6\n'+''.join(f'{i}\t{s}\n'for i,s in enumerate(names)))
  word=lambda b,at:struct.unpack_from('<H',b,0x1e880+at)[0]
  before=(q/'evidence/teleport-entry-ram.bin').read_bytes();after=(q/'evidence/teleport-final-ram.bin').read_bytes();offsets=[0x56d6,0x8e12,0x8e44,0x56ce,0x56da,0x56c4,0x2b36];old=[word(before,n)for n in offsets];new=[word(after,n)for n in offsets]
  assert new[0]==0 and new[1:3]==[word(after,0x3be),word(after,0x3c0)] and new[3]==0 and old[4:6]==new[4:6] and old[6]-new[6]==1
  write(q/'evidence/source.json',dict(status='passed-teleport-source',offsets=offsets,before=old,after=new,regions=names,inputs={p.name:sha(p)for p in(q/'evidence').glob('teleport-*.state')},grade='Inherited controlled original map-7 Enter-default snapshot plus new IDA9.4 data-flow review; other destinations statically derived',limits=['Jump/water consumers exported only; no implementation promotion','GUI begins with explicit relocation of real v7 progress','No new original execution or complete RNG parity']));return
 if a.action=='freeze':
  shutil.copytree(r/'internal/remake-rust',q/'rust-source');(q/'tools').mkdir()
  for n in ['rust-travel-spells.py','rust-travel-spells-gui.py','rust-travel-spells-scaled.py','export-rust-travel-spells-ida.py','rust-native-player.sh','rust-world.py','decode-rust-world-magic-original.go']:shutil.copy2(r/'tools'/n,q/'tools'/n)
  write(q/'media.json',{p.name:sha(p)for p in(q/'native/pack').iterdir()if p.is_file()});return
 if a.action=='audit':
  counts={k:len(v)for k,v in h.dependencies(r).items()};assert list(counts.values())==[197,7,923,535]
  crate={str(p.relative_to(r/'internal/remake-rust')):sha(p)for p in(r/'internal/remake-rust').rglob('*')if p.is_file()};assert all(sha(q/'rust-source'/p)==v for p,v in crate.items());assert all(sha(q/'native/pack'/p)==v for p,v in read(q/'media.json').items());assert(q/'teleport-regions.tsv').read_bytes()==(r/'internal/remake-rust/teleport-regions.tsv').read_bytes()
  tests=(q/'native/tests.log').read_text();assert 'FAILED'not in tests and'96 passed; 0 failed'in tests
  for face in ['noto','lishu','caoshu']:
   raw=(q/f'native/pack/font-{face}.bin').read_bytes();codes={chr(struct.unpack_from('<I',raw,i)[0])for i in range(12,len(raw)-8,4100)};assert set(''.join(read(q/'evidence/source.json')['regions']))<=codes
  pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();word=lambda at:struct.unpack_from('<H',pam,at)[0];header=word(8)*16;relocs=[header+word(word(24)+i*4+2)*16+word(word(24)+i*4)for i in range(word(6))];checked=0;j=read(q/'evidence/ida-travel.json');assert hashlib.sha256(pam).hexdigest()==j['probe']['source_sha256'];assert sha(r/'workplace/probe-20261023/text-first/PAM.i64')==j['probe']['database_sha256']
  for f in j['functions']:
   for v in f['lines']:
    at=v['file_offset'];want=bytes.fromhex(v['bytes']);assert at==v['ida_linear']-0x10000+header;raw=bytearray(pam[at:at+len(want)])
    for off in relocs:
     if at<=off and off+2<=at+len(want):struct.pack_into('<H',raw,off-at,(struct.unpack_from('<H',raw,off-at)[0]+0x1000)&65535)
    assert bytes(raw)==want;checked+=1
  gui=read(q/'native/gui/receipt.json');assert gui['status']=='passed-rust-travel-spells-gui'and gui['binary_sha256']==sha(q/'native/8sword-remake');assert len(gui['runs'])==4
  scaled=read(q/'native/scaled/receipt.json');assert scaled['status']=='passed-scaled-travel-spells-mouse'and scaled['binary_sha256']==sha(q/'native/8sword-remake')
  ds=header+0x1d780;regions=read(q/'evidence/source.json')['regions'];expected=''.join(f'TELEPORT\t{i}\t{word(ds+0x3be+4*i)}\t{word(ds+0x3c0+4*i)}\t{regions[i]}\n'for i in range(8));assert(q/'native/source-check.tsv').read_text()==expected
  from PIL import Image
  fnv=module(r,'rust-native-player.py').fnv
  for run in gui['runs']:
   assert run['exit']==0
   for cap in run['captures']:
    f=q/'native/gui'/run['name']/f"frame-{cap['number']:03}.ppm";assert f.read_bytes()==f.with_name(f"readback-{cap['number']:03}.ppm").read_bytes();assert cap['captured']['frame_hash']==format(fnv(Image.open(f).convert('RGBA').tobytes()),'016x')
  write(a.out,dict(status='passed-rust-travel-spells-audit',crate=crate,binary_sha256=sha(q/'native/8sword-remake'),baseline=counts,source=read(q/'evidence/source.json'),ida_functions=len(j['functions']),ida_lines_verified=checked,gui=gui,scaled=scaled,execution=read(q/'execution.json')));return
 if a.action=='images':
  from PIL import Image,ImageDraw,ImageFont
  idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));fh=h.FONT_SHA['noto'];raw=gzip.decompress((r/'preserved'/idx['objects'][fh]['path']).read_bytes());font=ImageFont.truetype(io.BytesIO(raw),30,index=3);gui=read(q/'native/gui/receipt.json');canvas=Image.new('RGB',(1920,1440),(9,36,29));draw=ImageDraw.Draw(canvas);sources=[]
  for i,(run,label,title)in enumerate([('purchase','shop','原式法術商店：購買傳送'),('pending','lishu','隸書：八區傳送選單冷讀'),('pending','arrived','確認傳送：落在原版起點'),('arrival','continued','新程序讀檔：區域與軍隊保持')]):
   row=next(v for v in gui['runs']if v['name']==run);cap=next(v for v in row['captures']if v['label']==label);f=q/'native/gui'/run/f"frame-{cap['number']:03}.ppm";x=i%2*960;y=i//2*720;draw.text((x+12,y+12),title,font=font,fill=(239,216,155));canvas.paste(Image.open(f).resize((960,660),Image.Resampling.LANCZOS),(x,y+60));sources.append(dict(run=run,label=label,sha256=sha(f),captured=cap['captured']))
  assert not a.out.exists();canvas.save(a.out);write(a.out.with_suffix('.json'),dict(platform='Linux Rust SDL2',binary_sha256=gui['binary_sha256'],image_sha256=sha(a.out),scope='Controlled shop relocation from real v7; no natural route claim',sources=sources));return
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for p in sorted(q.rglob('*')):
  if not p.is_file()or any(n in p.relative_to(q).parts for n in ['rust-target','go-cache']):continue
  assert p.stat().st_uid==1000 and not p.is_symlink();raw=p.read_bytes();v=hashlib.sha256(raw).hexdigest();obj=folder/(v+'.gz')
  if v not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[v]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(Path(REL)/p.relative_to(q)),sha256=v,bytes=len(raw),mode=p.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,rights='Full original-derived assets and binary local only; no Release'))
if __name__=='__main__':main()
