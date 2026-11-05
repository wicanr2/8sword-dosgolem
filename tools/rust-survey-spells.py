#!/usr/bin/env python3
"""Rust停時／鳥瞰資料、原收據核對與永久保存。只在Docker執行。"""
import argparse,ast,gzip,hashlib,importlib.util,io,json,os,shutil,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-survey-spells-r1';REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
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
  write(a.out,dict(status='passed-detached-rust-survey-spells',files=len(idx['files']),objects=len(idx['objects'])));return
 r=a.project;q=a.work or r/REL;h=module(r,'prepare-owned-army-ui.py')
 if a.action=='prepare':
  for f in read(r/'preserved/rust-resource-spells-r1.json')['files']:
   if '/native/pack/'in f['path']:(q/'native/pack'/Path(f['path']).name).write_bytes(h.stored(r,'rust-resource-spells-r1',f['path']))
  (q/'native/legacy-v6.chk').write_bytes(h.stored(r,'rust-resource-spells-r1','native/gui/alchemy-cold-store/journey.chk'))
  for index,label in [(4,'stop'),(5,'bird')]:
   for suffix in ['entry.state','final.state','receipt.json']:
    dest=label+'-'+('original.json'if suffix=='receipt.json'else suffix);(q/'evidence'/dest).write_bytes(h.stored(r,'remaining-spells-r1',f'original-map-r8/map-{index}/'+suffix))
  for old,new in [('ida-resource-spells.json','ida-survey.json'),('ida-shop.json','ida-world.json')]:
   (q/'evidence'/new).write_bytes(h.stored(r,'rust-resource-spells-r1','evidence/'+old))
  return
 if a.action=='reference':
  def word(b,at):return struct.unpack_from('<H',b,0x1e880+at)[0]
  before=(q/'evidence/stop-entry-ram.bin').read_bytes();after=(q/'evidence/stop-final-ram.bin').read_bytes();rank=word(before,0x4f2);values=lambda b:[word(b,n)for n in [0x56da,0x56dc,0x56ca,0x2b30]]
  old=values(before);new=values(after);assert rank==1 and old==[324,6,0,2]and new==[432,8,1,1]
  (q/'survey-stop-reference.tsv').write_text('# rank before_remaining before_tempo before_flag before_uses after_remaining after_tempo after_flag after_uses; inherited controlled original map-4\n'+'\t'.join(map(str,[rank,*old,*new]))+'\n')
  before=(q/'evidence/bird-entry-ram.bin').read_bytes();after=(q/'evidence/bird-final-ram.bin').read_bytes()
  def far(b,at):
   off,seg=struct.unpack_from('<HH',b,at);return b[seg*16+off:seg*16+off+5760]
  full=far(before,0x1e82a);assert full==far(after,0x1e82a) and far(before,0x1e84a)==far(after,0x1e84a);assert word(before,0x2b32)==2 and word(after,0x2b32)==1
  original=module(r,'prepare-hd-intro.py').decode((q/'native/pack/map1.ay').read_bytes());assert full==original[:5760]
  colors={int(f[0]):int(f[1])for line in(r/'internal/remake-rust/minimap-colors.tsv').read_text().splitlines()if not line.startswith('#')and(f:=line.split('\t'))};pixels=bytes(colors[full[y*72+x]-48]for y in range(80)for x in range(70));fnv=module(r,'rust-native-player.py').fnv
  write(q/'evidence/source.json',dict(status='passed-survey-spells-source',stop=dict(rank=rank,before=old,after=new),bird=dict(cells=5600,palette_hash=format(fnv(pixels),'016x'),exploration_unchanged=True,mask_sha256=hashlib.sha256(far(before,0x1e84a)).hexdigest()),grade='Inherited controlled original map-4/map-5 snapshots and IDA9.4; no new original execution',inputs={p.name:sha(p)for p in(q/'evidence').glob('*.state')},limits=['GUI uses explicit relocated previous v6 progress; natural cross-area not connected','300ms marker is native UI approximation']));return
 if a.action=='freeze':
  shutil.copytree(r/'internal/remake-rust',q/'rust-source');(q/'tools').mkdir()
  for n in ['rust-survey-spells.py','rust-survey-spells-gui.py','rust-native-player.sh','decode-rust-world-magic-original.go']:shutil.copy2(r/'tools'/n,q/'tools'/n)
  write(q/'media.json',{p.name:sha(p)for p in(q/'native/pack').iterdir()if p.is_file()});return
 if a.action=='audit':
  counts={k:len(v)for k,v in h.dependencies(r).items()};assert list(counts.values())==[197,7,923,535]
  crate={str(p.relative_to(r/'internal/remake-rust')):sha(p)for p in(r/'internal/remake-rust').rglob('*')if p.is_file()};assert all(sha(q/'rust-source'/p)==v for p,v in crate.items());assert all(sha(q/'native/pack'/p)==v for p,v in read(q/'media.json').items());assert(q/'survey-stop-reference.tsv').read_bytes()==(r/'internal/remake-rust/survey-stop-reference.tsv').read_bytes()
  tests=(q/'native/tests.log').read_text();assert 'FAILED'not in tests and'test result: ok.'in tests
  assert '91 passed; 0 failed'in tests
  pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();word=lambda at:struct.unpack_from('<H',pam,at)[0];header=word(8)*16;relocs=[header+word(word(24)+i*4+2)*16+word(word(24)+i*4)for i in range(word(6))];checked={}
  for n,starts in [('ida-survey.json',[0x16e32,0x180d8,0x168ce]),('ida-world.json',[0x1512c,0x15354,0x154b0,0x12446])]:
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
  gui=read(q/'native/gui/receipt.json');assert gui['status']=='passed-rust-survey-spells-gui'and gui['binary_sha256']==sha(q/'native/8sword-remake')
  assert len(gui['runs'])==4
  scaled=read(q/'native/scaled/receipt.json');assert scaled['status']=='passed-scaled-survey-spells-mouse'and scaled['binary_sha256']==sha(q/'native/8sword-remake')
  from PIL import Image
  fnv=module(r,'rust-native-player.py').fnv
  for run in gui['runs']:
   assert run['exit']==0
   for cap in run['captures']:
    f=q/'native/gui'/run['name']/f"frame-{cap['number']:03}.ppm";assert f.read_bytes()==f.with_name(f"readback-{cap['number']:03}.ppm").read_bytes();assert cap['captured']['frame_hash']==format(fnv(Image.open(f).convert('RGBA').tobytes()),'016x')
  source=read(q/'evidence/source.json');assert (q/'native/source-check.tsv').read_text().strip().split('\t')==['BIRD',source['bird']['palette_hash']]
  write(a.out,dict(status='passed-rust-survey-spells-audit',crate=crate,binary_sha256=sha(q/'native/8sword-remake'),baseline=counts,source=read(q/'evidence/source.json'),ida_lines_verified=checked,gui=gui,execution=read(q/'execution.json')));return
 if a.action=='images':
  from PIL import Image,ImageDraw,ImageFont
  idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));fh=h.FONT_SHA['noto'];raw=gzip.decompress((r/'preserved'/idx['objects'][fh]['path']).read_bytes());font=ImageFont.truetype(io.BytesIO(raw),30,index=3);gui=read(q/'native/gui/receipt.json');canvas=Image.new('RGB',(1920,1440),(9,36,29));draw=ImageDraw.Draw(canvas);sources=[]
  for i,(run,label,title)in enumerate([('stop','once','停時術：剩餘步數延長'),('stop-cold','repeat','重複施放耗次，步數保持'),('bird','full','鳥瞰術：暫時顯示目前全圖'),('bird-cold','explored','關閉後F5：探索紀錄保持')]):
   row=next(v for v in gui['runs']if v['name']==run);cap=next(v for v in row['captures']if v['label']==label);f=q/'native/gui'/run/f"frame-{cap['number']:03}.ppm";x=i%2*960;y=i//2*720;draw.text((x+12,y+12),title,font=font,fill=(239,216,155));canvas.paste(Image.open(f).resize((960,660),Image.Resampling.LANCZOS),(x,y+60));sources.append(dict(run=run,label=label,sha256=sha(f),captured=cap['captured']))
  assert not a.out.exists();canvas.save(a.out);write(a.out.with_suffix('.json'),dict(platform='Linux Rust SDL2',binary_sha256=gui['binary_sha256'],image_sha256=sha(a.out),scope='Controlled relocation from real v6; no natural cross-area acquisition claim',sources=sources));return
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for p in sorted(q.rglob('*')):
  if not p.is_file()or any(n in p.relative_to(q).parts for n in ['rust-target','go-cache']):continue
  assert p.stat().st_uid==1000 and not p.is_symlink();raw=p.read_bytes();v=hashlib.sha256(raw).hexdigest();obj=folder/(v+'.gz')
  if v not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[v]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(Path(REL)/p.relative_to(q)),sha256=v,bytes=len(raw),mode=p.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,rights='Full original-derived assets and binary local only; no Release'))
if __name__=='__main__':main()
