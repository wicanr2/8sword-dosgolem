#!/usr/bin/env python3
"""Rust 世界法術：固定資料、素材還原與永久保存。只在 Docker 執行。"""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-world-magic-r1';REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def module(r,n):
 s=importlib.util.spec_from_file_location(n,r/'tools'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['prepare','route','original','reference','freeze','archive','verify','audit','images'])
 for n in ['project','work','out','archive']:ap.add_argument('--'+n,type=Path)
 a=ap.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  idx=read(a.archive/(BATCH+'.json'))
  for f in idx['files']:
   ob=idx['objects'][f['sha256']];p=a.archive/BATCH/ob['file'];assert sha(p)==ob['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-rust-world-magic',files=len(idx['files']),objects=len(idx['objects'])));return
 r=a.project;q=a.work or r/REL;h=module(r,'prepare-owned-army-ui.py')
 if a.action=='reference':
  before=(q/'evidence/bridge-entry-ram.bin').read_bytes();after=(q/'evidence/bridge-final-ram.bin').read_bytes();maps=[]
  for b in [before,after]:
   off,seg=struct.unpack_from('<HH',b,0x1e82a);assert (seg,off)==(0x9a00,0);maps.append(b[seg*16+off:seg*16+off+5760])
  changed=[(i%72,i//72,a-48,b-48)for i,(a,b)in enumerate(zip(*maps))if a!=b];assert [(x,y,n)for x,y,_,n in changed]==[(41,40,52),(42,40,52)]
  scalar=lambda b:[struct.unpack_from('<H',b,0x1e880+i)[0]for i in [0x8e12,0x8e44,0x56da,0x2b28]];assert scalar(before)==[40,40,324,2]and scalar(after)==[40,40,324,1]
  (q/'magic-bridge-reference.tsv').write_text('# x y before after; inherited original-map-r8/map-0, controlled learned+2charges, Right\n'+'\n'.join(f'{x}\t{y}\t{maps[0][y*72+x]-48}\t{maps[1][y*72+x]-48}'for y in range(38,43)for x in range(38,43))+'\n')
  write(q/'evidence/bridge-reference.json',dict(status='passed-inherited-original-bridge',before=scalar(before),after=scalar(after),changed=changed,entry_sha256=sha(q/'evidence/entry.state'),final_sha256=sha(q/'evidence/final.state'),receipt_sha256=sha(q/'evidence/receipt.json'),grade='existing dosgolem controlled receipt; original learned+charges and terrain fixture; no new original execution'));return
 if a.action=='original':
  for n in ['entry.state','final.state','receipt.json']:(q/'evidence'/n).write_bytes(h.stored(r,'remaining-spells-r1','original-map-r8/map-0/'+n))
  (q/'native/legacy-v4.chk').write_bytes(h.stored(r,'rust-minimap-r1','native/gui/fresh-store/journey.chk'));return
 if a.action=='route':
  from collections import deque
  raw=module(r,'prepare-hd-intro.py').decode((q/'native/pack/map1.ay').read_bytes());tile=lambda p:raw[p[1]*72+p[0]]-48
  dirs=[(0,-1,0xff52),(0,1,0xff54),(-1,0,0xff51),(1,0,0xff53),(-1,-1,0xff50),(1,-1,0xff55),(-1,1,0xff57),(1,1,0xff56)]
  def path(start,goal):
   queue=deque([start]);prev={start:None}
   while queue:
    p=queue.popleft()
    if p==goal:
     out=[]
     while prev[p] is not None:
      old,key=prev[p];out.append(dict(key=key,to=list(p)));p=old
     return out[::-1]
    for dx,dy,key in dirs:
     n=((p[0]+dx)%70,(p[1]+dy)%80);t=tile(n)
     if n not in prev and (t in [1,47,48,52]or 3<=t<=10 or 31<=t<=45 or n==goal and t==53):prev[n]=(p,key);queue.append(n)
   raise AssertionError(('unreachable',start,goal))
  book=(50,60);shop=(30,7);p1=path((40,40),book);p2=path(book,shop);candidates=[]
  for y in range(80):
   for x in range(70):
    p=(x,y)
    if not (tile(p)==1 or 3<=tile(p)<=10):continue
    for dx,dy,key in dirs[:4]:
     near=((x+dx)%70,(y+dy)%80);far=((x+dx*2)%70,(y+dy*2)%80)
     if tile(near)not in [2,11,12,13,14]:continue
     try:route=path(shop,p)
     except AssertionError:continue
     candidates.append((len(route),p,key,near,far,route))
  _,shore,key,near,far,p3=min(candidates);write(q/'native/route.json',dict(book=p1,shop=p2,shore=p3,cast_key=key,shore_position=shore,near=near,far=far,total=len(p1)+len(p2)+len(p3)+2,method='BFS only builds normal XTest inputs; no runtime memory/state modification'))
  print(dict(book=len(p1),shop=len(p2),shore=len(p3),cast=key,near=near,far=far));return
 if a.action=='prepare':
  from PIL import Image
  (q/'native/pack').mkdir(parents=True,exist_ok=True)
  for f in read(r/'preserved/rust-minimap-r1.json')['files']:
   if '/native/pack/'in f['path']:(q/'native/pack'/Path(f['path']).name).write_bytes(h.stored(r,'rust-minimap-r1',f['path']))
  ram=h.stored(r,'rust-minimap-r1','evidence/original-ram.bin');(q/'evidence/original-ram.bin').write_bytes(ram)
  pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
  ds=struct.unpack_from('<H',pam,8)[0]*16+0x1d780;word=lambda off:struct.unpack_from('<H',pam,ds+off)[0]
  items=[tuple(word(0x260a+6*i+2*j)for j in range(3))for i in range(8)];assert items[0]==(0,50,60);assert list(struct.unpack_from('<24H',ram,0x1e880+0x260a))==[v for s in items for v in s]
  offers=[word(0x3136+2*i)for i in range(72)];prices=[word(0x2b18+2*i)for i in range(8)];assert prices==[10,100,100,50,100,100,100,200]
  rows=[];decode=module(r,'prepare-hd-intro.py').decode
  for area in range(8):
   raw=decode((q/f'native/pack/map{area+1}.ay').read_bytes());sites=[(x,y)for y in range(80)for x in range(70)if raw[y*72+x]==101];assert len(sites)==[2,4,6,6,6,6,8,8][area]
   if area==0:assert sites==[struct.unpack_from('<HH',ram,0x1e880+0x8d6c+4*i)for i in range(2)]
   for row,(x,y)in enumerate(sites):rows.append((area,row,x,y,offers[area*(area+1)+row]))
  (q/'magic-shops.tsv').write_text('# area row x y offer; PAM DS3136 + actual MAP row scan; area0 RAM DS8D6C checked\n'+'\n'.join('\t'.join(map(str,s))for s in rows)+'\n')
  (q/'magic-items.tsv').write_text('# index area x y; PAM DS260A, original RAM checked\n'+'\n'.join('\t'.join(map(str,(i,*s)))for i,s in enumerate(items))+'\n')
  names=[]
  for off in [0x2ab8,0x2a38]:
   names.append([pam[ds+off+12*i:ds+off+12*(i+1)].split(b'\0')[0].decode('big5')for i in range(8)])
  (q/'magic-names.tsv').write_text('\n'.join(f'{names[0][i]}\t{names[1][i]}\t{prices[i]}'for i in range(8))+'\n')
  fnv=module(r,'rust-native-player.py').fnv;art=r/'workplace/player/assets-painted-r69';assets=[]
  for name,source,size,want in [('magic-building.rgba','live1-hd-r1.png',(1344,600),'a5012d0f66c0c55522df74865b4d9ca5fcaebd174967dd03d3b9adb3afbbb06c'),('magic-book.rgba','man-12-r1.png',(96,96),'cd52b94b43b0200bf86a89564c5b91c1d70dad5e2a28195c70cbd530cdc8a612')]:
   p=art/source;assert sha(p)==want;im=Image.open(p).convert('RGBA').resize(size,Image.Resampling.LANCZOS);raw=b'8SRGBA01'+struct.pack('<II',*size)+im.tobytes();(q/'native/pack'/name).write_bytes(raw+struct.pack('<Q',fnv(raw)));assets.append(dict(file=name,source=source,source_sha256=want,sha256=sha(q/'native/pack'/name)))
  write(q/'evidence/source.json',dict(status='passed-world-magic-source',pam_sha256=hashlib.sha256(pam).hexdigest(),items=items,shops=rows,names=names,prices=prices,assets=assets,grade='PAM fixed tables and IDA control flow; all map shop counts, area0 shop RAM and eight item RAM triples checked'));return
 if a.action=='freeze':
  shutil.copytree(r/'internal/remake-rust',q/'rust-source');(q/'tools').mkdir()
  for n in ['rust-world-magic.py','rust-world-magic-gui.py','rust-native-player.sh','export-rust-world-magic-ida.py','decode-rust-world-magic-original.go']:shutil.copy2(r/'tools'/n,q/'tools'/n)
  write(q/'media.json',{p.name:sha(p)for p in(q/'native/pack').iterdir()if p.is_file()});return
 if a.action=='audit':
  counts={k:len(v)for k,v in h.dependencies(r).items()};assert list(counts.values())==[197,7,923,535]
  crate={str(p.relative_to(r/'internal/remake-rust')):sha(p)for p in(r/'internal/remake-rust').rglob('*')if p.is_file()};assert all(sha(q/'rust-source'/p)==v for p,v in crate.items());assert all(sha(q/'native/pack'/p)==v for p,v in read(q/'media.json').items())
  assert 'FAILED'not in(q/'native/tests.log').read_text()and'test result: ok.'in(q/'native/tests.log').read_text()
  assert '78 passed; 0 failed'in(q/'native/tests.log').read_text()
  for n in ['magic-shops.tsv','magic-items.tsv','magic-names.tsv','magic-bridge-reference.tsv']:assert(q/n).read_bytes()==(r/'internal/remake-rust'/n).read_bytes()
  assert read(q/'evidence/bridge-reference.json')['status']=='passed-inherited-original-bridge'
  ida=read(q/'evidence/ida-world-magic.json');assert ida['probe']['functions']==521 and ida['probe']['version']=='9.4'and ida['exporter_sha256']==sha(r/'tools/export-rust-world-magic-ida.py')
  pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()==ida['probe']['source_sha256'];assert sha(r/'workplace/probe-20261023/text-first/PAM.i64')==ida['probe']['database_sha256'];word=lambda at:struct.unpack_from('<H',pam,at)[0];header=word(8)*16;relocs=[header+word(word(24)+i*4+2)*16+word(word(24)+i*4)for i in range(word(6))];checked=0
  for f in ida['functions']:
   for v in f['lines']:
    at=v['file_offset'];want=bytes.fromhex(v['bytes']);assert at==v['ida_linear']-0x10000+header;raw=bytearray(pam[at:at+len(want)])
    for off in relocs:
     if at<=off and off+2<=at+len(want):struct.pack_into('<H',raw,off-at,(struct.unpack_from('<H',raw,off-at)[0]+0x1000)&65535)
    assert bytes(raw)==want;checked+=1
  gui=read(q/'native/gui/receipt.json');assert gui['status']=='passed-rust-world-magic-gui'and gui['binary_sha256']==sha(q/'native/8sword-remake')
  assert len(gui['runs'])==4 and sum(len(v['captures'])for v in gui['runs'])==11
  scaled=read(q/'native/scaled/receipt.json');assert scaled['status']=='passed-scaled-magic-mouse'and scaled['binary_sha256']==sha(q/'native/8sword-remake')
  from PIL import Image
  fnv=module(r,'rust-native-player.py').fnv
  for run in gui['runs']:
   assert run['exit']==0
   for cap in run['captures']:
    f=q/'native/gui'/run['name']/f"frame-{cap['number']:03}.ppm";assert f.read_bytes()==f.with_name(f"readback-{cap['number']:03}.ppm").read_bytes();assert cap['captured']['frame_hash']==format(fnv(Image.open(f).convert('RGBA').tobytes()),'016x')
  write(a.out,dict(status='passed-rust-world-magic-audit',crate=crate,binary_sha256=sha(q/'native/8sword-remake'),baseline=counts,source=read(q/'evidence/source.json'),ida_lines_verified=checked,gui=gui,execution=read(q/'execution.json'),limits=['Bridge only; other world spells and other item pickups remain boundaries.','No original full journey RNG parity, mobile build or Release.']));return
 if a.action=='images':
  from PIL import Image,ImageDraw,ImageFont
  import io
  idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));fh=h.FONT_SHA['noto'];raw=gzip.decompress((r/'preserved'/idx['objects'][fh]['path']).read_bytes());font=ImageFont.truetype(io.BytesIO(raw),30,index=3);gui=read(q/'native/gui/receipt.json');canvas=Image.new('RGB',(1920,1440),(9,36,29));draw=ImageDraw.Draw(canvas);sources=[]
  for i,(run,label,title)in enumerate([('fresh','book','正常尋得魔法竹簡'),('fresh','shop','原式法術商店'),('pending','bridge','造橋後步行上橋'),('cold','cold','重新開啟：竹簡、次數與橋保持')]):
   row=next(v for v in gui['runs']if v['name']==run);cap=next(v for v in row['captures']if v['label']==label);f=q/'native/gui'/run/f"frame-{cap['number']:03}.ppm";x=i%2*960;y=i//2*720;draw.text((x+12,y+12),title,font=font,fill=(239,216,155));canvas.paste(Image.open(f).resize((960,660),Image.Resampling.LANCZOS),(x,y+60));sources.append(dict(run=run,label=label,sha256=sha(f),captured=cap['captured']))
  assert not a.out.exists();canvas.save(a.out);write(a.out.with_suffix('.json'),dict(platform='Linux Rust SDL2',binary_sha256=gui['binary_sha256'],image_sha256=sha(a.out),sources=sources));return
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for p in sorted(q.rglob('*')):
  if not p.is_file()or any(n in p.relative_to(q).parts for n in ['rust-target','go-cache']):continue
  assert p.stat().st_uid==1000 and not p.is_symlink();raw=p.read_bytes();v=hashlib.sha256(raw).hexdigest();obj=folder/(v+'.gz')
  if v not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[v]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(Path(REL)/p.relative_to(q)),sha256=v,bytes=len(raw),mode=p.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,rights='Full original-derived assets and binary local only; no Release'))
if __name__=='__main__':main()
