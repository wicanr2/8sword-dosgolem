#!/usr/bin/env python3
"""Rust跳躍術的來源核對、素材準備與永久保存。只在Docker執行。"""
import argparse,gzip,hashlib,importlib.util,io,json,os,shutil,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-jump-spell-r1';REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
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
  write(a.out,dict(status='passed-detached-rust-jump-spell',files=len(idx['files']),objects=len(idx['objects'])));return
 r=a.project;q=a.work or r/REL;h=module(r,'prepare-owned-army-ui.py')
 if a.action=='prepare':
  for f in read(r/'preserved/rust-water-spell-r1.json')['files']:
   if '/native/pack/'in f['path']:(q/'native/pack'/Path(f['path']).name).write_bytes(h.stored(r,'rust-water-spell-r1',f['path']))
  (q/'native/legacy-v9.chk').write_bytes(h.stored(r,'rust-water-spell-r1','native/gui/arrival-store/journey.chk'))
  for name in ['entry.state','final.state','receipt.json']:(q/'evidence'/('jump-'+name)).write_bytes(h.stored(r,'remaining-spells-r1','original-map-r8/map-3/'+name))
  return
 if a.action=='reference':
  word=lambda b,at:struct.unpack_from('<H',b,0x1e880+at)[0]
  before=(q/'evidence/jump-entry-ram.bin').read_bytes();after=(q/'evidence/jump-final-ram.bin').read_bytes();offsets=[0x56cc,0x2b2e,0x56da,0x8e12,0x8e44,0x56c4,0x56ce];old=[word(before,n)for n in offsets];new=[word(after,n)for n in offsets]
  assert old[:2]==[0,2]and new[:2]==[1,1]and old[2:]==new[2:]
  table=(q/'evidence/jump-reference.tsv').read_text();assert len(table.splitlines())==1446 and all(len(row.split('\t'))==12 for row in table.splitlines()[1:])
  write(q/'evidence/source.json',dict(status='passed-jump-source',offsets=offsets,before=old,after=new,jump_cases=1445,inputs={p.name:sha(p)for p in(q/'evidence').glob('jump-*.state')},grade='Inherited original map3 activation plus new dosgolem B85/C32/1FBB/2014/3B40 arming/movement/landing and actual700byte exploration masks. Controlled fields; no original GUI or12446 event tail.',limits=['250ms native display cadence, no original wall-clock equivalence','GUI actual shop initial position controlled; no natural cross-area acquisition','Flying F7 native extension; original fourth animation pose reused approved art']));return
 if a.action=='freeze':
  shutil.copytree(r/'internal/remake-rust',q/'rust-source');(q/'tools').mkdir()
  for n in ['rust-jump-spell.py','rust-jump-spell-gui.py','rust-jump-spell-scaled.py','export-rust-jump-ida.py','rust-jump-reference.go','rust-native-player.sh','rust-world.py','decode-rust-world-magic-original.go']:shutil.copy2(r/'tools'/n,q/'tools'/n)
  write(q/'media.json',{p.name:sha(p)for p in(q/'native/pack').iterdir()if p.is_file()});return
 if a.action=='audit':
  counts={k:len(v)for k,v in h.dependencies(r).items()};assert list(counts.values())==[197,7,923,535]
  crate={str(p.relative_to(r/'internal/remake-rust')):sha(p)for p in(r/'internal/remake-rust').rglob('*')if p.is_file()};assert all(sha(q/'rust-source'/p)==v for p,v in crate.items());assert all(sha(q/'native/pack'/p)==v for p,v in read(q/'media.json').items());assert(q/'evidence/jump-reference.tsv').read_bytes()==(r/'internal/remake-rust/jump-reference.tsv').read_bytes()
  tests=(q/'native/tests.log').read_text();assert 'FAILED'not in tests and'109 passed; 0 failed'in tests
  for face in ['noto','lishu','caoshu']:
   raw=(q/f'native/pack/font-{face}.bin').read_bytes();codes={chr(struct.unpack_from('<I',raw,i)[0])for i in range(12,len(raw)-8,4100)};assert set('跳躍中')<=codes
  pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();word=lambda at:struct.unpack_from('<H',pam,at)[0];header=word(8)*16;relocs=[header+word(word(24)+i*4+2)*16+word(word(24)+i*4)for i in range(word(6))];checked=0;j=read(q/'evidence/ida-jump.json');assert hashlib.sha256(pam).hexdigest()==j['probe']['source_sha256'];assert sha(r/'workplace/probe-20261023/text-first/PAM.i64')==j['probe']['database_sha256']
  for f in j['functions']:
   for v in f['lines']:
    at=v['file_offset'];want=bytes.fromhex(v['bytes']);assert at==v['ida_linear']-0x10000+header;raw=bytearray(pam[at:at+len(want)])
    for off in relocs:
     if at<=off and off+2<=at+len(want):struct.pack_into('<H',raw,off-at,(struct.unpack_from('<H',raw,off-at)[0]+0x1000)&65535)
    assert bytes(raw)==want;checked+=1
  gui=read(q/'native/gui/receipt.json');assert gui['status']=='passed-rust-jump-spell-gui'and gui['binary_sha256']==sha(q/'native/8sword-remake');assert len(gui['runs'])==4
  scaled=read(q/'native/scaled/receipt.json');assert scaled['status']=='passed-scaled-jump-spell-mouse'and scaled['binary_sha256']==sha(q/'native/8sword-remake')
  from PIL import Image
  fnv=module(r,'rust-native-player.py').fnv
  for run in gui['runs']:
   assert run['exit']==0
   for cap in run['captures']:
    f=q/'native/gui'/run['name']/f"frame-{cap['number']:03}.ppm";assert f.read_bytes()==f.with_name(f"readback-{cap['number']:03}.ppm").read_bytes();assert cap['captured']['frame_hash']==format(fnv(Image.open(f).convert('RGBA').tobytes()),'016x')
  write(a.out,dict(status='passed-rust-jump-spell-audit',crate=crate,binary_sha256=sha(q/'native/8sword-remake'),baseline=counts,source=read(q/'evidence/source.json'),ida_functions=len(j['functions']),ida_lines_verified=checked,gui=gui,scaled=scaled,execution=read(q/'execution.json')));return
 if a.action=='images':
  from PIL import Image,ImageDraw,ImageFont
  idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));fh=h.FONT_SHA['noto'];raw=gzip.decompress((r/'preserved'/idx['objects'][fh]['path']).read_bytes());font=ImageFont.truetype(io.BytesIO(raw),30,index=3);gui=read(q/'native/gui/receipt.json');canvas=Image.new('RGB',(1920,1440),(9,36,29));draw=ImageDraw.Draw(canvas);sources=[]
  for i,(run,label,title)in enumerate([('purchase','ready','原店實購：跳躍待發與隸書'),('launch','flying','向西越山：沿舊方向自動前進'),('resume','landed','途中冷讀：繼續越山後落地'),('arrival','army','落地冷讀：原式軍隊保持')]):
   row=next(v for v in gui['runs']if v['name']==run);cap=next(v for v in row['captures']if v['label']==label);f=q/'native/gui'/run/f"frame-{cap['number']:03}.ppm";x=i%2*960;y=i//2*720;draw.text((x+12,y+12),title,font=font,fill=(239,216,155));canvas.paste(Image.open(f).resize((960,660),Image.Resampling.LANCZOS),(x,y+60));sources.append(dict(run=run,label=label,sha256=sha(f),captured=cap['captured']))
  assert not a.out.exists();canvas.save(a.out);write(a.out.with_suffix('.json'),dict(platform='Linux Rust SDL2',binary_sha256=gui['binary_sha256'],image_sha256=sha(a.out),scope='Controlled actual shop location from real v9, then ordinary purchase/use/exit; no natural cross-area acquisition',sources=sources));return
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for p in sorted(q.rglob('*')):
  if not p.is_file()or any(n in p.relative_to(q).parts for n in ['rust-target','go-cache']):continue
  assert p.stat().st_uid==1000 and not p.is_symlink();raw=p.read_bytes();v=hashlib.sha256(raw).hexdigest();obj=folder/(v+'.gz')
  if v not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[v]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(Path(REL)/p.relative_to(q)),sha256=v,bytes=len(raw),mode=p.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,rights='Full original-derived assets and binary local only; no Release'))
if __name__=='__main__':main()
