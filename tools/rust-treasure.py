#!/usr/bin/env python3
"""Rust寶箱資源：固定資料、Go向量、核對與永久保存。"""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-treasure-r1';REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def module(r,n):
 s=importlib.util.spec_from_file_location(n,r/'tools'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','audit','archive','verify','images'])
 for n in ['project','work','out','archive']:p.add_argument('--'+n,type=Path)
 a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  j=read(a.archive/(BATCH+'.json'))
  for f in j['files']:
   o=j['objects'][f['sha256']];b=(a.archive/BATCH/o['file']).read_bytes();assert hashlib.sha256(b).hexdigest()==o['stored_sha256'];raw=gzip.decompress(b);assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  v=dict(status='passed-detached-rust-treasure',files=len(j['files']),objects=len(j['objects']));write(a.out,v);print(json.dumps(v));return
 r=a.project;q=a.work or r/REL;h=module(r,'prepare-owned-army-ui.py')
 if a.action=='prepare':
  assert q.is_dir()and(q/'evidence').is_dir();(q/'native/pack').mkdir(parents=True)
  for f in read(r/'preserved/rust-monthly-r1.json')['files']:
   if '/native/pack/'in f['path']:(q/'native/pack'/Path(f['path']).name).write_bytes(h.stored(r,'rust-monthly-r1',f['path']))
  for name,key in [('legacy-v3.chk','native/gui/cold-store/journey.chk'),('legacy-v2.chk','evidence/legacy-v2.chk')]:
   (q/'evidence'/name).write_bytes(h.stored(r,'rust-monthly-r1',key))
  pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0';ds=struct.unpack_from('<H',pam,8)[0]*16+0x1d780;values=struct.unpack_from('<80H',pam,ds+0x4490)
  def decode(raw):
   word=lambda at:struct.unpack_from('<H',raw,at)[0];node=root=word(2);out=[]
   for byte in raw[4+(root-255)*4:]:
    for bit in range(8):
     node=word(4+(node-256)*4+(0 if byte&(1<<bit)else 2))
     if node<256:out.append(node);node=root
     if len(out)==5761:return [v-48 for i,v in enumerate(out[:5760])if i%72<70]
   raise AssertionError('map truncated')
  maps=[decode((q/f'native/pack/map{i+1}.ay').read_bytes())for i in range(8)];coords=[[(x,y)for y in range(80)for x in range(70)if m[y*70+x]==59]for m in maps];assert all(len(v)==10 for v in coords)
  ix=json.loads(h.stored(r,'treasure-r1','decoded-input-r1/index.json'))['before-commit.state'];ram=gzip.decompress(h.stored(r,'treasure-r1','decoded-input-r1/'+ix['memory_file']));assert hashlib.sha256(ram).hexdigest()==ix['memory_sha256'];assert coords[0]==[struct.unpack_from('<HH',ram,0x1e880+0x8c60+i*4)for i in range(10)];assert values==struct.unpack_from('<80H',ram,0x1e880+0x4490)
  lines=['# area row x y initial_amount; IDA145FA row-major ASCII107 scan']
  for area,points in enumerate(coords):
   for row,(x,y)in enumerate(points):lines.append('\t'.join(map(str,[area,row,x,y,values[area*10+row]])))
  (q/'treasure-catalog.tsv').write_text('\n'.join(lines)+'\n');proof=json.loads(h.stored(r,'treasure-r1','candidate-r2/receipt.json'));original=json.loads(h.stored(r,'treasure-r1','original-r1/receipt.json'));write(q/'evidence/go-treasure.json',proof);write(q/'evidence/original-treasure.json',original);refs=['# name gold lead amount choice after_gold after_lead consumed']
  for c in proof['cases']:refs.append('\t'.join(map(str,[c['name'],c['before']['gold'],c['before']['leadership'],c['amount'],c['choice'],c['after']['gold'],c['after']['leadership'],int(c['amount']>0 and c['choice']in[1,2])])))
  (q/'treasure-reference.tsv').write_text('\n'.join(refs)+'\n');(q/'evidence/ida-prior.json').write_bytes(h.stored(r,'treasure-r1','ida2/ida-story-resources-r1.json'))
  # A shortest safe walking route is only normal keyboard/mouse input, no engine pathfinding.
  from collections import deque
  m=maps[0];start=(40,40);todo=deque([start]);seen={start:[]};target=None
  while todo:
   at=todo.popleft()
   if at in coords[0]:target=at;break
   for dx,dy in [(0,1),(-1,0),(0,-1),(1,0)]:
    nxt=((at[0]+dx)%70,(at[1]+dy)%80);tile=m[nxt[1]*70+nxt[0]]
    if nxt in seen or tile in [2,46,49,50,51,53,54,55,56,57,58,60,61,62,65]or 11<=tile<=30:continue
    seen[nxt]=seen[at]+[[dx,dy]];todo.append(nxt)
  assert target;write(q/'route.json',dict(start=start,target=target,row=coords[0].index(target),amount=values[coords[0].index(target)],moves=seen[target]));write(q/'evidence/source.json',dict(status='passed-treasure-source',cases=7,records=80,all_treasure_tiles_match=True,map1_runtime_coordinates_equal=True,coordinates=coords,pam_sha256=hashlib.sha256(pam).hexdigest(),ida_coordinates_sha256=sha(q/'evidence/ida-coordinates.json'),grade='proven row-major scan from IDA145FA plus original map1 runtime anchor',original_oracle='Inherited seven original/Go cases; no new full original playthrough'));return
 if a.action=='freeze':
  shutil.copytree(r/'internal/remake-rust',q/'rust-source');(q/'tools').mkdir()
  for n in ['rust-treasure.py','rust-treasure-gui.py','rust-native-player.sh','export-rust-treasure-ida.py']:shutil.copy2(r/'tools'/n,q/'tools'/n)
  write(q/'media.json',{p.name:sha(p)for p in(q/'native/pack').iterdir()if p.is_file()});return
 if a.action=='audit':
  baseline={k:len(v)for k,v in h.dependencies(r).items()};assert list(baseline.values())==[197,7,923,535];crate={str(p.relative_to(r/'internal/remake-rust')):sha(p)for p in(r/'internal/remake-rust').rglob('*')if p.is_file()};assert all(sha(q/'rust-source'/p)==v for p,v in crate.items());assert all(sha(q/'native/pack'/p)==v for p,v in read(q/'media.json').items());assert all((q/n).read_bytes()==(r/'internal/remake-rust'/n).read_bytes()for n in ['treasure-catalog.tsv','treasure-reference.tsv']);log=(q/'native/tests.log').read_text();assert 'FAILED'not in log and '63 passed; 0 failed'in log;source=read(q/'evidence/source.json');assert source['cases']==7 and source['records']==80;gui=read(q/'native/gui/receipt.json');assert gui['status']=='passed-rust-treasure-gui'and gui['binary_sha256']==sha(q/'native/8sword-remake')
  ida=read(q/'evidence/ida-coordinates.json');probe=read(q/'evidence/ida-probe.json');pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()==probe['source_sha256']==ida['source_sha256'];assert sha(r/'workplace/probe-20261023/text-first/PAM.i64')==ida['database_sha256'];assert probe['functions']==ida['function_count']==521 and probe['uid']==1000 and probe['version']=='9.4';assert sha(q/'export-coordinates.py')==ida['exporter_sha256']==sha(r/'tools/export-rust-treasure-ida.py');assert ida['semantic_index_sha256']==sha(r/'docs/spec/treasure-address-index-r1.json');assert source['ida_coordinates_sha256']==sha(q/'evidence/ida-coordinates.json');word=lambda off:struct.unpack_from('<H',pam,off)[0];header=word(8)*16;relocs=[header+word(word(24)+i*4+2)*16+word(word(24)+i*4)for i in range(word(6))];checked=0
  for f in ida['functions']:
   for v in f['lines']:
    at=v['file_offset'];want=bytes.fromhex(v['bytes']);assert at==v['ida_linear']-0x10000+header;raw=bytearray(pam[at:at+len(want)])
    for off in relocs:
     if at<=off and off+2<=at+len(want):struct.pack_into('<H',raw,off-at,(struct.unpack_from('<H',raw,off-at)[0]+0x1000)&65535)
    assert bytes(raw)==want;checked+=1
  assert any(f['start']==0x145fa and len(f['lines'])==124 for f in ida['functions']);source=dict(source,ida_lines_verified=checked)
  from PIL import Image
  for row in gui['runs']:
   assert row['exit']==0
   for cap in row['captures']:
    p=q/'native/gui'/row['name']/f"frame-{cap['number']:03}.ppm";assert p.read_bytes()==p.with_name(f"readback-{cap['number']:03}.ppm").read_bytes();assert cap['captured']['frame_hash']==format(module(r,'rust-native-player.py').fnv(Image.open(p).convert('RGBA').tobytes()),'016x')
  write(a.out,dict(status='passed-rust-treasure-audit',crate=crate,binary_sha256=sha(q/'native/8sword-remake'),baseline=baseline,gui=gui,source=source,execution=read(q/'execution.json'),limits=['Chest gold/leadership only; other story events and NPC/calendar remain unported.','Development v4 checkpoint; reads v1-v3, no Go save import or complete world schema.']));return
 if a.action=='images':
  from PIL import Image,ImageDraw,ImageFont
  import io
  ix=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));fh=h.FONT_SHA['noto'];face=gzip.decompress((r/'preserved'/ix['objects'][fh]['path']).read_bytes());assert hashlib.sha256(face).hexdigest()==fh;font=ImageFont.truetype(io.BytesIO(face),30,index=3)
  gui=read(q/'native/gui/receipt.json');picks=[('natural','treasure-choice'),('gold','gold-collected'),('lead','leadership-collected'),('gold-cold','collected-cold')];canvas=Image.new('RGB',(1920,1440),(9,36,29));sources=[];draw=ImageDraw.Draw(canvas);titles=['原式寶箱：價值30，取消後仍可再開','納入財產：500 → 530金','分贈部隊：領導力100 → 103','關閉重開：已領寶箱不再給獎勵']
  for i,(name,label)in enumerate(picks):
   row=next(v for v in gui['runs']if v['name']==name);cap=next(v for v in row['captures']if v['label']==label);p=q/'native/gui'/name/f"frame-{cap['number']:03}.ppm";x=(i%2)*960;y=(i//2)*720;draw.text((x+12,y+12),titles[i],font=font,fill=(239,216,155));canvas.paste(Image.open(p).resize((960,660),Image.Resampling.LANCZOS),(x,y+60));sources.append(dict(run=name,label=label,sha256=sha(p),captured=cap['captured']))
  assert not a.out.exists();canvas.save(a.out);write(a.out.with_suffix('.json'),dict(platform='Linux Rust SDL2',seed=1,binary_sha256=gui['binary_sha256'],image_sha256=sha(a.out),scope='Natural walk to chest, both choices and cold saves; no RAM/IP injection. Original rules use inherited paired receipts.',sources=sources));return
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for p in sorted(q.rglob('*')):
  if not p.is_file()or'rust-target'in p.relative_to(q).parts:continue
  assert not p.is_symlink()and p.stat().st_uid==1000;raw=p.read_bytes();v=hashlib.sha256(raw).hexdigest();obj=folder/(v+'.gz')
  if v not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[v]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(Path(REL)/p.relative_to(q)),sha256=v,bytes=len(raw),mode=p.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,rights='Full original-derived assets and binary local only; no Release'))
if __name__=='__main__':main()
