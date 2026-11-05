#!/usr/bin/env python3
"""Rust原式管理與滑鼠：準備、核對及永久保存。只在Docker執行。"""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-controls-r1';REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def module(r,n):
 s=importlib.util.spec_from_file_location(n,r/'tools'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['prepare','evidence','images','freeze','audit','archive','verify'])
 for n in['project','work','archive','out']:ap.add_argument('--'+n,type=Path)
 a=ap.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   o=d['objects'][f['sha256']];p=a.archive/BATCH/o['file'];assert sha(p)==o['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-rust-controls',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=a.work or r/REL;helper=module(r,'prepare-owned-army-ui.py')
 if a.action=='prepare':
  q.mkdir();(q/'native/pack').mkdir(parents=True);(q/'evidence').mkdir()
  for f in read(r/'preserved/rust-journey-r1.json')['files']:
   if '/native/pack/'in f['path']:(q/'native/pack'/Path(f['path']).name).write_bytes(helper.stored(r,'rust-journey-r1',f['path']))
  pam=r/'workplace/intake-20261023/sources/game/8sword/PAM.AY';assert sha(pam)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0';raw=pam.read_bytes();ds=struct.unpack_from('<H',raw,8)[0]*16+0x1d780;lines=['# Fixed PAM DS3EFE five groups,24 rows; group row area x y kind stock']
  for g in range(5):
   for row in range(24):lines.append('\t'.join(map(str,[g,row,*struct.unpack_from('<5H',raw,ds+0x3efe+g*240+row*10)])))
  (q/'camp-catalog.tsv').write_text('\n'.join(lines)+'\n')
  from PIL import Image
  import io
  art=json.loads(helper.stored(r,'original-player-integration-r1','ui-assets/unit-art.json'));sources={}
  for row in art['rows']:
   p=q/'native/pack'/('unit_'+row['id'].replace(':','_')+'.rgba')
   if p.exists():continue
   raw=helper.stored(r,'original-player-integration-r1','ui-assets/'+row['file']);assert hashlib.sha256(raw).hexdigest()==row['sha256'];im=Image.open(io.BytesIO(raw)).convert('RGBA');box=im.getchannel('A').getbbox();assert box;cut=im.crop(box);bw,bh=cut.size;w,h=252,288
   if w*bh>h*bw:w=h*bw//bh
   else:h=w*bh//bw
   tile=Image.new('RGBA',(264,300));tile.paste(cut.resize((w,h),Image.Resampling.NEAREST),((264-w)//2,300-h));b=b'8SRGBA01'+struct.pack('<II',264,300)+tile.tobytes();p.write_bytes(b+struct.pack('<Q',module(r,'rust-native-player.py').fnv(b)));sources[row['id']]=row
  assets=r/'workplace/player/assets-painted-r69';meta=read(assets/'recruitment-building.json')['image'];p=assets/meta['file'];assert sha(p)==meta['sha256'];im=Image.open(p).convert('RGBA').resize((1344,600),Image.Resampling.BILINEAR);b=b'8SRGBA01'+struct.pack('<II',1344,600)+im.tobytes();(q/'native/pack/recruit-building.rgba').write_bytes(b+struct.pack('<Q',module(r,'rust-native-player.py').fnv(b)));write(q/'evidence/media-source.json',dict(extra_units=sources,building=meta));return
 if a.action=='evidence':
  sources=[('camp-stock-r1','mapping-r1.json'),('reinforcement-camps-r1','model-final-r1/model-r1.json'),('original-recruit-quantity-r1','second-models-r1/receipt.json'),('original-army-dismiss-r1','runtime-hd-true/receipt.json')];rows=[]
  for batch,key in sources:
   b=helper.stored(r,batch,key);p=q/'evidence'/(batch+'.json');p.write_bytes(b);rows.append(dict(batch=batch,path=key,sha256=sha(p)))
  mapping=read(q/'evidence/camp-stock-r1.json');native=[list(map(int,l.split('\t')))for l in(q/'camp-catalog.tsv').read_text().splitlines()if not l.startswith('#')]
  assert native==[[v['group'],v['row'],*v['words']]for v in mapping['rows']]
  legacy=helper.stored(r,'rust-journey-r1','native/gui/battle-store/journey.chk');assert legacy[:8]==b'8SJRN001';(q/'evidence/legacy-v1.chk').write_bytes(legacy)
  # Independent legacy compression decode; compare every active record to actual terrain.
  def decode(raw):
   word=lambda p:struct.unpack_from('<H',raw,p)[0];node=root=word(2);out=[]
   for byte in raw[4+(root-255)*4:]:
    for bit in range(8):
     node=word(4+(node-256)*4+(0 if byte&(1<<bit)else 2))
     if node<256:out.append(node);node=root
     if len(out)==5761:return [v-48 for i,v in enumerate(out[:5760])if i%72<70]
   raise AssertionError('map truncated')
  maps=[decode((q/f'native/pack/map{i+1}.ay').read_bytes())for i in range(8)]
  active=[f for f in native if f[5]>0]
  assert all(maps[f[2]][f[4]*70+f[3]]==54+f[0]for f in active)
  coords={(f[2],f[3],f[4],54+f[0])for f in active};tiles={(a,x,y,t)for a,m in enumerate(maps)for y in range(80)for x in range(70)if 54<=(t:=m[y*70+x])<=58};assert coords==tiles
  write(q/'evidence/source-receipt.json',dict(status='passed-inherited-camp-evidence',records=len(native),active=len(active),all_recruitment_tiles_match=True,sources=rows,legacy_sha256=sha(q/'evidence/legacy-v1.chk')));return
 if a.action=='images':
  from PIL import Image,ImageDraw,ImageFont
  import io
  ix=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));h=helper.FONT_SHA['noto'];face=gzip.decompress((r/'preserved'/ix['objects'][h]['path']).read_bytes());assert hashlib.sha256(face).hexdigest()==h;font=ImageFont.truetype(io.BytesIO(face),30,index=3)
  picks=[('purchase','wolf-purchased','滑鼠招募：野狼1，金錢460，獨立庫存74'),('camp-cold','original-six-stack-review','原式檢閱：31民兵＋1野狼，隸書'),('camp-cold','original-six-stack-dismiss','原式解雇：點選整隊後確認，不退款'),('world-cold','mouse-selected-enemy','滑鼠戰鬥：點選敵隊，再確認出手')];gui=read(q/'native/gui/receipt.json');canvas=Image.new('RGB',(1920,1440),(9,36,29));draw=ImageDraw.Draw(canvas);sources=[]
  for i,(name,label,title)in enumerate(picks):
   row=next(v for v in gui['runs']if v['name']==name);cap=next(v for v in row['captures']if v['label']==label);p=q/'native/gui'/name/f"frame-{cap['number']:03}.ppm";assert cap['captured']['readback_equal']=='true';x=(i%2)*960;y=(i//2)*720;draw.text((x+12,y+12),title,font=font,fill=(239,216,155));canvas.paste(Image.open(p).resize((960,660),Image.Resampling.LANCZOS),(x,y+60));sources.append(dict(run=name,label=label,path=str(p.relative_to(q)),sha256=sha(p),captured=cap['captured']))
  assert not a.out.exists();canvas.save(a.out);write(a.out.with_suffix('.json'),dict(platform='Linux x86_64 Rust SDL2',input='XTest mouse; F12 capture only',seed=1,origin='PAM initial 30 militia/500 gold; no RAM/IP injection',comparison='remake captures only; not original same-state parity',binary_sha256=gui['binary_sha256'],image_sha256=sha(a.out),sources=sources));return
 if a.action=='freeze':
  shutil.copytree(r/'internal/remake-rust',q/'rust-source');(q/'tools').mkdir()
  for n in['rust-controls.py','rust-controls-gui.py','rust-native-player.sh']:shutil.copy2(r/'tools'/n,q/'tools'/n)
  write(q/'media.json',{p.name:sha(p)for p in(q/'native/pack').iterdir()if p.is_file()});return
 if a.action=='audit':
  counts={k:len(v)for k,v in helper.dependencies(r).items()};assert list(counts.values())==[197,7,923,535]
  crate={str(p.relative_to(r/'internal/remake-rust')):sha(p)for p in(r/'internal/remake-rust').rglob('*')if p.is_file()};assert all(sha(q/'rust-source'/n)==h for n,h in crate.items());assert all(sha(q/'native/pack'/n)==h for n,h in read(q/'media.json').items());assert(q/'camp-catalog.tsv').read_bytes()==(r/'internal/remake-rust/camp-catalog.tsv').read_bytes()
  log=(q/'native/tests.log').read_text();assert 'FAILED'not in log and '53 passed; 0 failed'in log;assert read(q/'evidence/source-receipt.json')['status']=='passed-inherited-camp-evidence'
  gui=read(q/'native/gui/receipt.json');assert gui['status']=='passed-rust-controls-gui'and gui['binary_sha256']==sha(q/'native/8sword-remake')
  from PIL import Image
  for row in gui['runs']:
   assert row['exit']==0
   for cap in row['captures']:
    p=q/'native/gui'/row['name']/f"frame-{cap['number']:03}.ppm";assert p.read_bytes()==p.with_name(f"readback-{cap['number']:03}.ppm").read_bytes();assert cap['captured']['frame_hash']==format(module(r,'rust-native-player.py').fnv(Image.open(p).convert('RGBA').tobytes()),'016x')
  write(a.out,dict(status='passed-rust-controls-audit',crate=crate,binary_sha256=sha(q/'native/8sword-remake'),baseline=counts,gui=gui,execution=read(q/'execution.json'),limits=['Native management/recruit and Linux mouse only; mobile build and real touch device unverified.','v2 development checkpoint imports prior no-camp v1, not Go saves or full world schema.','Camp data and arithmetic inherit current Go evidence; no new full original playthrough.']));return
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for p in sorted(q.rglob('*')):
  if not p.is_file()or any(n in p.relative_to(q).parts for n in['rust-target','go-cache']):continue
  assert not p.is_symlink()and p.stat().st_uid==1000;raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();o=folder/(h+'.gz')
  if h not in objects:o.write_bytes(gzip.compress(raw,6,mtime=0));objects[h]=dict(file=o.name,stored_sha256=sha(o))
  files.append(dict(path=str(Path(REL)/p.relative_to(q)),sha256=h,bytes=len(raw),mode=p.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,rights='Full original-derived media and binary local only; no release'))
if __name__=='__main__':main()
