#!/usr/bin/env python3
"""Rust煉金／召兵資料、原收據核對與永久保存。只在Docker執行。"""
import argparse,ast,gzip,hashlib,importlib.util,io,json,os,shutil,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-resource-spells-r1';REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def module(r,n):
 s=importlib.util.spec_from_file_location(n,r/'tools'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['prepare','freeze','audit','images','archive','verify'])
 for n in ['project','work','out','archive']:ap.add_argument('--'+n,type=Path)
 a=ap.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  idx=read(a.archive/(BATCH+'.json'))
  for f in idx['files']:
   ob=idx['objects'][f['sha256']];p=a.archive/BATCH/ob['file'];assert sha(p)==ob['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-rust-resource-spells',files=len(idx['files']),objects=len(idx['objects'])));return
 r=a.project;q=a.work or r/REL;h=module(r,'prepare-owned-army-ui.py')
 if a.action=='prepare':
  for f in read(r/'preserved/rust-world-magic-r1.json')['files']:
   if '/native/pack/'in f['path']:(q/'native/pack'/Path(f['path']).name).write_bytes(h.stored(r,'rust-world-magic-r1',f['path']))
  (q/'native/legacy-v5.chk').write_bytes(h.stored(r,'rust-world-magic-r1','native/gui/pending-store/journey.chk'))
  rows=['# inherited controlled original receipts: A gold roll bonus amount after; S rank roll bonus kind count case']
  sources=[]
  for b,n in [('alchemy-r1','original-r3/receipt.json'),('summon-r1','original-r1/receipt.json')]:
   raw=h.stored(r,b,n);(q/'evidence'/(b+'-original.json')).write_bytes(raw);j=json.loads(raw);sources.append(dict(batch=b,path=n,sha256=hashlib.sha256(raw).hexdigest(),status=j['status']))
   for c in j['cases']:
    if b.startswith('alchemy'):rows.append('\t'.join(map(str,['A',c['before']['gold'],c['roll'],int(c['bonus']),c['amount'],c['after']['gold']])))
    else:rows.append('\t'.join(map(str,['S',c['rank'],c['roll'],int(c['bonus']),c['kind'],c['count'],c['name']])))
  (q/'resource-spells-reference.tsv').write_text('\n'.join(rows)+'\n')
  raw=h.stored(r,'summon-r1','inputs/ida-map-spells.json');(q/'evidence/ida-resource-spells.json').write_bytes(raw)
  prev=h.stored(r,'rust-world-magic-r1','evidence/ida-world-magic.json');(q/'evidence/ida-shop.json').write_bytes(prev)
  for n in ['alchemy-data.go','summon-data.go','owned-army-model.go']:(q/'evidence'/n).write_bytes((r/'internal/ownedworld'/n).read_bytes())
  write(q/'evidence/source.json',dict(status='passed-resource-spells-source',sources=sources,ida_sha256=hashlib.sha256(raw).hexdigest(),shop_ida_sha256=hashlib.sha256(prev).hexdigest(),cases=5,grade='Inherited controlled original receipts + reviewed Go rules; no new original execution',limits=['bonus payload checked only; no bonus item acquisition','GUI relocation fixture; cross-area natural progression not connected']));return
 if a.action=='freeze':
  shutil.copytree(r/'internal/remake-rust',q/'rust-source');(q/'tools').mkdir()
  for n in ['rust-resource-spells.py','rust-resource-spells-gui.py','rust-native-player.sh']:shutil.copy2(r/'tools'/n,q/'tools'/n)
  write(q/'media.json',{p.name:sha(p)for p in(q/'native/pack').iterdir()if p.is_file()});return
 if a.action=='audit':
  counts={k:len(v)for k,v in h.dependencies(r).items()};assert list(counts.values())==[197,7,923,535]
  crate={str(p.relative_to(r/'internal/remake-rust')):sha(p)for p in(r/'internal/remake-rust').rglob('*')if p.is_file()};assert all(sha(q/'rust-source'/p)==v for p,v in crate.items());assert all(sha(q/'native/pack'/p)==v for p,v in read(q/'media.json').items());assert(q/'resource-spells-reference.tsv').read_bytes()==(r/'internal/remake-rust/resource-spells-reference.tsv').read_bytes()
  tests=(q/'native/tests.log').read_text();assert 'FAILED'not in tests and'test result: ok.'in tests
  assert '85 passed; 0 failed'in tests
  pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();word=lambda at:struct.unpack_from('<H',pam,at)[0];header=word(8)*16;relocs=[header+word(word(24)+i*4+2)*16+word(word(24)+i*4)for i in range(word(6))];checked={}
  for n,starts in [('ida-resource-spells.json',[0x16b20,0x16bea,0x168ce]),('ida-shop.json',[0x1512c,0x15354,0x154b0])]:
   j=read(q/'evidence'/n);assert hashlib.sha256(pam).hexdigest()==j.get('source_sha256',j.get('probe',{}).get('source_sha256'));assert sha(r/'workplace/probe-20261023/text-first/PAM.i64')==j.get('database_sha256',j.get('probe',{}).get('database_sha256'));checked[n]=0
   assert {f['start']for f in j['functions']if f['start']in starts}==set(starts)
   for f in j['functions']:
    if f['start']not in starts:continue
    for v in f['lines']:
     at=v.get('file_offset',v.get('original_file_offset'));want=bytes.fromhex(v['bytes']);assert at==v['ida_linear']-0x10000+header;raw=bytearray(pam[at:at+len(want)])
     for off in relocs:
      if at<=off and off+2<=at+len(want):struct.pack_into('<H',raw,off-at,(struct.unpack_from('<H',raw,off-at)[0]+0x1000)&65535)
     assert bytes(raw)==want;checked[n]+=1
   assert checked[n]>0
  gui=read(q/'native/gui/receipt.json');assert gui['status']=='passed-rust-resource-spells-gui'and gui['binary_sha256']==sha(q/'native/8sword-remake')
  assert len(gui['runs'])==5 and sum(len(v['captures'])for v in gui['runs'])==12
  scaled=read(q/'native/scaled/receipt.json');assert scaled['status']=='passed-scaled-resource-spells-mouse'and scaled['binary_sha256']==sha(q/'native/8sword-remake')
  from PIL import Image
  fnv=module(r,'rust-native-player.py').fnv
  for run in gui['runs']:
   assert run['exit']==0
   for cap in run['captures']:
    f=q/'native/gui'/run['name']/f"frame-{cap['number']:03}.ppm";assert f.read_bytes()==f.with_name(f"readback-{cap['number']:03}.ppm").read_bytes();assert cap['captured']['frame_hash']==format(fnv(Image.open(f).convert('RGBA').tobytes()),'016x')
  write(a.out,dict(status='passed-rust-resource-spells-audit',crate=crate,binary_sha256=sha(q/'native/8sword-remake'),baseline=counts,source=read(q/'evidence/source.json'),ida_lines_verified=checked,gui=gui,execution=read(q/'execution.json')));return
 if a.action=='images':
  from PIL import Image,ImageDraw,ImageFont
  idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));fh=h.FONT_SHA['noto'];raw=gzip.decompress((r/'preserved'/idx['objects'][fh]['path']).read_bytes());font=ImageFont.truetype(io.BytesIO(raw),30,index=3);gui=read(q/'native/gui/receipt.json');canvas=Image.new('RGB',(1920,1440),(9,36,29));draw=ImageDraw.Draw(canvas);sources=[]
  for i,(run,label,title)in enumerate([('alchemy','result','煉金術：金錢與次數一次提交'),('alchemy-cold','cold','新程序讀回同一結果'),('summon','result','召兵術：合併原式部隊'),('summon-cold','review','F2檢閱召得部隊與透明圖示')]):
   row=next(v for v in gui['runs']if v['name']==run);cap=next(v for v in row['captures']if v['label']==label);f=q/'native/gui'/run/f"frame-{cap['number']:03}.ppm";x=i%2*960;y=i//2*720;draw.text((x+12,y+12),title,font=font,fill=(239,216,155));canvas.paste(Image.open(f).resize((960,660),Image.Resampling.LANCZOS),(x,y+60));sources.append(dict(run=run,label=label,sha256=sha(f),captured=cap['captured']))
  assert not a.out.exists();canvas.save(a.out);write(a.out.with_suffix('.json'),dict(platform='Linux Rust SDL2',binary_sha256=gui['binary_sha256'],image_sha256=sha(a.out),scope='Controlled relocation from real v5; no natural cross-area acquisition claim',sources=sources));return
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for p in sorted(q.rglob('*')):
  if not p.is_file()or any(n in p.relative_to(q).parts for n in ['rust-target','go-cache']):continue
  assert p.stat().st_uid==1000 and not p.is_symlink();raw=p.read_bytes();v=hashlib.sha256(raw).hexdigest();obj=folder/(v+'.gz')
  if v not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[v]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(Path(REL)/p.relative_to(q)),sha256=v,bytes=len(raw),mode=p.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,rights='Full original-derived assets and binary local only; no Release'))
if __name__=='__main__':main()
