#!/usr/bin/env python3
"""Rust F5：探索總覽、原收據核對及本機永久保存。"""
import argparse,gzip,hashlib,importlib.util,io,json,os,shutil,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-minimap-r1';REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
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
  write(a.out,dict(status='passed-detached-rust-minimap',files=len(j['files']),objects=len(j['objects'])));return
 r=a.project;q=a.work or r/REL;h=module(r,'prepare-owned-army-ui.py')
 if a.action=='prepare':
  from PIL import Image
  assert q.is_dir()and(q/'evidence/ida-minimap.json').is_file();(q/'native/pack').mkdir(parents=True,exist_ok=True)
  for f in read(r/'preserved/rust-character-r1.json')['files']:
   if '/native/pack/'in f['path']:(q/'native/pack'/Path(f['path']).name).write_bytes(h.stored(r,'rust-character-r1',f['path']))
  def color(t):
   if t in [0,47,48]:return 0
   if t==1 or 3<=t<=10 or t==59:return 10
   if t==2 or 11<=t<=14:return 9
   if 15<=t<=30:return 6
   if 31<=t<=45:return 14
   if t==46:return 2
   if t==52:return 7
   if 49<=t<=65:return 12
   raise AssertionError(t)
  rgb=[(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),(170,85,0),(170,170,170),(85,85,85),(85,85,255),(85,255,85),(85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]
  ram=(q/'evidence/original-ram.bin').read_bytes();assert len(ram)==1048576;off,seg=struct.unpack_from('<HH',ram,0x1e84a);assert(seg,off)==(0x9c00,0);raw=ram[seg*16+off:seg*16+off+5760];assert all(raw[y*72+70:y*72+72]==bytes([13,10])for y in range(80));position=[struct.unpack_from('<H',ram,0x1e880+n)[0]for n in [0x8e12,0x8e44]];assert position==[41,40]
  im=Image.open(q/'evidence/13-minimap-native.png').convert('RGB');assert im.size==(1920,1200);rows=['# x y tile captured_R G B marker; original dosgolem owned-modal-r12'];tiles=[];pixels=0
  for y in range(80):
   for x in range(70):
    t=raw[y*72+x]-48;assert 0<=t<=65;c=color(t);marker=[x,y]==position;colors=im.crop((300+x*12,78+y*12,312+x*12,90+y*12)).getcolors();actual=im.getpixel((305+x*12,83+y*12))
    if not marker:assert colors==[(144,rgb[c])];pixels+=144
    else:assert all(v in [rgb[0],rgb[15]]for _,v in colors)
    if t:rows.append('\t'.join(map(str,[x,y,t,*actual,int(marker)])));tiles.append(t)
  assert len(tiles)==12 and pixels==806256
  (q/'minimap-reference.tsv').write_text('\n'.join(rows)+'\n');(q/'minimap-colors.tsv').write_text('# tile original_palette_index; IDA182D3..18363\n'+'\n'.join(f'{t}\t{color(t)}'for t in range(66))+'\n')
  write(q/'evidence/source.json',dict(status='passed-minimap-source',position=position,visible_cells=12,masked_cells=5588,original_pixels_verified=pixels,original_marker_pixels=144,source_state_sha256=sha(q/'evidence/final.state'),original_png_sha256=sha(q/'evidence/13-minimap-native.png'),ram_sha256=sha(q/'evidence/original-ram.bin'),grade='proven IDA color/geometry + inherited original RAM/PNG; no new original execution',original_address_space='runtime linear ptr1E84A; DS1E88 offsets8E12/8E44; source frame1920x1200 without Rust toolbar48'));return
 if a.action=='freeze':
  shutil.copytree(r/'internal/remake-rust',q/'rust-source');(q/'tools').mkdir()
  for n in ['rust-minimap.py','rust-minimap-gui.py','rust-native-player.sh','export-rust-minimap-ida.py','decode-rust-minimap-original.go']:shutil.copy2(r/'tools'/n,q/'tools'/n)
  write(q/'media.json',{p.name:sha(p)for p in(q/'native/pack').iterdir()if p.is_file()});return
 if a.action=='audit':
  counts={k:len(v)for k,v in h.dependencies(r).items()};assert list(counts.values())==[197,7,923,535]
  crate={str(p.relative_to(r/'internal/remake-rust')):sha(p)for p in(r/'internal/remake-rust').rglob('*')if p.is_file()};assert all(sha(q/'rust-source'/p)==v for p,v in crate.items());assert all(sha(q/'native/pack'/p)==v for p,v in read(q/'media.json').items());assert all((q/n).read_bytes()==(r/'internal/remake-rust'/n).read_bytes()for n in ['minimap-colors.tsv','minimap-reference.tsv']);assert'68 passed; 0 failed'in(q/'native/tests.log').read_text()
  ida=read(q/'evidence/ida-minimap.json');assert ida['probe']['functions']==521 and ida['probe']['uid']==1000 and ida['probe']['version']=='9.4';assert ida['exporter_sha256']==sha(r/'tools/export-rust-minimap-ida.py');assert ida['functions'][0]['start']==0x18292
  pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()==ida['probe']['source_sha256'];assert sha(r/'workplace/probe-20261023/text-first/PAM.i64')==ida['probe']['database_sha256'];word=lambda at:struct.unpack_from('<H',pam,at)[0];header=word(8)*16;relocs=[header+word(word(24)+i*4+2)*16+word(word(24)+i*4)for i in range(word(6))];checked=0
  for f in ida['functions']:
   for v in f['lines']:
    at=v['file_offset'];want=bytes.fromhex(v['bytes']);assert at==v['ida_linear']-0x10000+header;raw=bytearray(pam[at:at+len(want)])
    for off in relocs:
     if at<=off and off+2<=at+len(want):struct.pack_into('<H',raw,off-at,(struct.unpack_from('<H',raw,off-at)[0]+0x1000)&65535)
    assert bytes(raw)==want;checked+=1
  gui=read(q/'native/gui/receipt.json');assert gui['status']=='passed-rust-minimap-gui'and gui['binary_sha256']==sha(q/'native/8sword-remake')
  from PIL import Image
  fnv=module(r,'rust-native-player.py').fnv
  for run in gui['runs']:
   assert run['exit']==0
   for cap in run['captures']:
    f=q/'native/gui'/run['name']/f"frame-{cap['number']:03}.ppm";assert f.read_bytes()==f.with_name(f"readback-{cap['number']:03}.ppm").read_bytes();assert cap['captured']['frame_hash']==format(fnv(Image.open(f).convert('RGBA').tobytes()),'016x')
  from PIL import ImageChops
  fresh=next(row for row in gui['runs']if row['name']=='fresh');caps={v['label']:v['number']for v in fresh['captures']};images=[Image.open(q/'native/gui/fresh'/f"frame-{caps[label]:03}.ppm").convert('RGB')for label in ['initial','dark']];diff=ImageChops.difference(*images);assert diff.getbbox()==(780,606,792,618);assert sum(v!=(0,0,0)for v in diff.getdata())==144
  source=read(q/'evidence/source.json');assert source['visible_cells']==12 and source['original_pixels_verified']==806256;assert source['source_state_sha256']==sha(q/'evidence/final.state')and source['ram_sha256']==sha(q/'evidence/original-ram.bin')and source['original_png_sha256']==sha(q/'evidence/13-minimap-native.png')
  write(a.out,dict(status='passed-rust-minimap-audit',crate=crate,binary_sha256=sha(q/'native/8sword-remake'),baseline=counts,source=read(q/'evidence/source.json'),ida_lines_verified=checked,gui=gui,execution=read(q/'execution.json'),limits=['F5 current explored area only; original RAM/PNG receipt inherited, no new original execution.','v4 unchanged; native Linux sampled, no mobile or Release.']));return
 if a.action=='images':
  from PIL import Image,ImageDraw,ImageFont
  idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));fh=h.FONT_SHA['noto'];raw=gzip.decompress((r/'preserved'/idx['objects'][fh]['path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==fh;font=ImageFont.truetype(io.BytesIO(raw),30,index=3)
  gui=read(q/'native/gui/receipt.json');canvas=Image.new('RGB',(1920,1440),(9,36,29));draw=ImageDraw.Draw(canvas);sources=[]
  for i,(run,label,title)in enumerate([('fresh','initial','原起點：只顯示已探索區域'),('fresh','walked','正常行走後：探索紀錄展開'),('fresh','caoshu','草書與原式座標欄'),('cold','cold','重新開啟：探索與位置保持')]):
   row=next(v for v in gui['runs']if v['name']==run);cap=next(v for v in row['captures']if v['label']==label);f=q/'native/gui'/run/f"frame-{cap['number']:03}.ppm";x=i%2*960;y=i//2*720;draw.text((x+12,y+12),title,font=font,fill=(239,216,155));canvas.paste(Image.open(f).resize((960,660),Image.Resampling.LANCZOS),(x,y+60));sources.append(dict(run=run,label=label,sha256=sha(f),captured=cap['captured']))
  assert not a.out.exists();canvas.save(a.out);write(a.out.with_suffix('.json'),dict(platform='Linux Rust SDL2',binary_sha256=gui['binary_sha256'],image_sha256=sha(a.out),scope='F5 normal start, walk and cold save; source colors/geometry verified, no whole original same-state claim',sources=sources));return
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for p in sorted(q.rglob('*')):
  if not p.is_file()or any(n in p.relative_to(q).parts for n in ['rust-target','go-cache']):continue
  assert p.stat().st_uid==1000 and not p.is_symlink();raw=p.read_bytes();v=hashlib.sha256(raw).hexdigest();obj=folder/(v+'.gz')
  if v not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[v]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(Path(REL)/p.relative_to(q)),sha256=v,bytes=len(raw),mode=p.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,rights='Full original-derived assets and binary local only; no Release'))
if __name__=='__main__':main()
