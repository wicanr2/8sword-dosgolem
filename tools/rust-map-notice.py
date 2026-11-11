#!/usr/bin/env python3
"""地圖51：原圖／文字來源核對、還原與永久保存。限Docker。"""
import argparse,gzip,hashlib,importlib.util,io,json,os,shutil,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-map-notice-r1';REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def module(r,n):
 s=importlib.util.spec_from_file_location(n,r/'tools'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['prepare','restore','freeze','audit','images','archive','verify'])
 for n in ['project','work','out','archive']:ap.add_argument('--'+n,type=Path)
 a=ap.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  idx=read(a.archive/(BATCH+'.json'))
  for f in idx['files']:
   ob=idx['objects'][f['sha256']];p=a.archive/BATCH/ob['file'];assert sha(p)==ob['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-rust-map-notice',files=len(idx['files']),objects=len(idx['objects'])));return
 r=a.project;q=a.work or r/REL;h=module(r,'prepare-owned-army-ui.py')
 if a.action=='archive':
  base=module(r,'rust-world-exits.py');base.BATCH=BATCH;base.REL=REL;base.main();return
 if a.action=='restore':
  n=0
  for f in read(r/'preserved'/(BATCH+'.json'))['files']:
   rel=Path(f['path']).relative_to(REL)
   if str(rel)=='native/8sword-remake'or str(rel).startswith('native/pack/'):
    p=q/rel;p.parent.mkdir(parents=True,exist_ok=True);raw=h.stored(r,BATCH,str(rel));assert hashlib.sha256(raw).hexdigest()==f['sha256'];p.write_bytes(raw);p.chmod(f['mode']);n+=1
  assert n==140;return
 if a.action=='prepare':
  (q/'native/pack').mkdir(parents=True,exist_ok=True);(q/'evidence').mkdir(exist_ok=True)
  for f in read(r/'preserved/rust-empty-army-r1.json')['files']:
   if '/native/pack/'in f['path']:(q/'native/pack'/Path(f['path']).name).write_bytes(h.stored(r,'rust-empty-army-r1',f['path']))
  (q/'native/legacy-v12.chk').write_bytes(h.stored(r,'rust-empty-army-r1','native/gui/continued-store/journey.chk'))
  pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0';ds=struct.unpack_from('<H',pam,8)[0]*16+0x1d780;decode=module(r,'prepare-hd-intro.py').decode;fnv=module(r,'rust-native-player.py').fnv;bases=[0x5be,0x9f6,0xcc6,0x10fe,0x140a,0x19e6,0x1da6,0x21de];rows=[];texts=[];notes=[]
  for area,base in enumerate(bases):
   raw=decode((q/f'native/pack/map{area+1}.ay').read_bytes());points=[(x,y)for y in range(80)for x in range(70)if raw[y*72+x]==99]
   for i,(x,y)in enumerate(points):
    at=ds+base+60*i;rawtext=pam[at:at+60].split(bytes([0]),1)[0];text=rawtext.decode('big5');assert '\n'not in text and '\t'not in text;rows.append(f'{area}\t{i}\t{x}\t{y}\t{fnv(text.encode())}');texts.append(text);notes.append(dict(area=area,index=i,x=x,y=y,ds_offset=base+60*i,file_offset=at,raw_hex=rawtext.hex(),text=text,text_sha256=hashlib.sha256(text.encode()).hexdigest()))
  assert len(rows)==131;assert (r/'internal/remake-rust/notice-catalog.tsv').read_text().splitlines()[1:]==rows
  (q/'native/pack/map-notices.tsv').write_text('\n'.join(texts)+'\n');write(q/'evidence/notice-texts.json',notes);(q/'evidence/ida-scan.json').write_bytes(h.stored(r,'rust-treasure-r1','evidence/ida-coordinates.json'));return
 if a.action=='freeze':
  shutil.copytree(r/'internal/remake-rust',q/'rust-source');(q/'tools').mkdir()
  for n in ['rust-map-notice.py','rust-world-exits.py','rust-map-notice-gui.py','rust-map-notice-reference.go','export-rust-map-notice-ida.py','rust-native-player.sh','rust-world.py']:shutil.copy2(r/'tools'/n,q/'tools'/n)
  write(q/'media.json',{p.name:sha(p)for p in(q/'native/pack').iterdir()if p.is_file()});return
 if a.action=='audit':
  counts={k:len(v)for k,v in h.dependencies(r).items()};assert list(counts.values())==[197,7,923,535]
  crate={str(p.relative_to(r/'internal/remake-rust')):sha(p)for p in(r/'internal/remake-rust').rglob('*')if p.is_file()};assert all(sha(q/'rust-source'/p)==v for p,v in crate.items());assert all(sha(q/'native/pack'/p)==v for p,v in read(q/'media.json').items());assert '136 passed; 0 failed'in(q/'native/tests.log').read_text();assert(q/'evidence/notice-reference-r2.tsv').read_bytes()==(r/'internal/remake-rust/notice-reference.tsv').read_bytes();assert len((q/'evidence/notice-reference-r2.tsv').read_text().splitlines())==240
  pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();word=lambda at:struct.unpack_from('<H',pam,at)[0];header=word(8)*16;relocs=[header+word(word(24)+i*4+2)*16+word(word(24)+i*4)for i in range(word(6))];j=read(q/'evidence/ida-notice.json');assert hashlib.sha256(pam).hexdigest()==j['probe']['source_sha256'];assert sha(r/'workplace/probe-20261023/text-first/PAM.i64')==j['probe']['database_sha256'];functions=j['functions']+[f for f in read(q/'evidence/ida-scan.json')['functions']if f['name']=='sub_145FA'];checked=0
  for f in functions:
   for v in f['lines']:
    at=v['file_offset'];want=bytes.fromhex(v['bytes']);assert at==v['ida_linear']-0x10000+header;raw=bytearray(pam[at:at+len(want)])
    for off in relocs:
     if at<=off and off+2<=at+len(want):struct.pack_into('<H',raw,off-at,(struct.unpack_from('<H',raw,off-at)[0]+0x1000)&65535)
    assert bytes(raw)==want;checked+=1
  notes=read(q/'evidence/notice-texts.json');assert len(notes)==131;assert(q/'native/pack/map-notices.tsv').read_text().splitlines()==[n['text']for n in notes]
  for n in notes:assert bytes.fromhex(n['raw_hex'])==pam[n['file_offset']:n['file_offset']+60].split(bytes([0]),1)[0]and hashlib.sha256(n['text'].encode()).hexdigest()==n['text_sha256']
  gui=read(q/'native/gui/receipt.json');assert gui['status']=='passed-rust-map-notice-gui'and gui['binary_sha256']==sha(q/'native/8sword-remake')and len(gui['runs'])==3
  from PIL import Image
  fnv=module(r,'rust-native-player.py').fnv
  for run in gui['runs']:
   assert run['exit']==0
   for cap in run['captures']:
    f=q/'native/gui'/run['name']/f"frame-{cap['number']:03}.ppm";assert f.read_bytes()==f.with_name(f"readback-{cap['number']:03}.ppm").read_bytes();assert cap['captured']['frame_hash']==format(fnv(Image.open(f).convert('RGBA').tobytes()),'016x')
  write(a.out,dict(status='passed-rust-map-notice-audit',crate=crate,binary_sha256=sha(q/'native/8sword-remake'),baseline=counts,notice_sites=131,original_pointer_cases=131,original_flow_cases=108,ida_functions=len(functions),ida_lines_verified=checked,gui=gui,execution=read(q/'execution.json')));return
 if a.action=='images':
  from PIL import Image,ImageDraw,ImageFont
  idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));raw=gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes());font=ImageFont.truetype(io.BytesIO(raw),30,index=3);gui=read(q/'native/gui/receipt.json');canvas=Image.new('RGB',(1920,1440),(9,36,29));draw=ImageDraw.Draw(canvas);sources=[]
  for i,(run,label,title)in enumerate([('notice','before','從原提示鄰格正常走入'),('notice','pending','隸書：原版地圖提示'),('cold-notice','cold-pending','F7獨立冷讀：時間尚未提交'),('continued','walk','確認後冷讀：繼續正常移動')]):
   row=next(v for v in gui['runs']if v['name']==run);cap=next(v for v in row['captures']if v['label']==label);f=q/'native/gui'/run/f"frame-{cap['number']:03}.ppm";x=i%2*960;y=i//2*720;draw.text((x+12,y+12),title,font=font,fill=(239,216,155));canvas.paste(Image.open(f).resize((960,660),Image.Resampling.LANCZOS),(x,y+60));sources.append(dict(run=run,label=label,sha256=sha(f),captured=cap['captured']))
  assert not a.out.exists();canvas.save(a.out);write(a.out.with_suffix('.json'),dict(platform='Linux Rust SDL2',binary_sha256=gui['binary_sha256'],image_sha256=sha(a.out),scope='Real v12 progress, only original notice adjacent position and seed1 controlled; normal walk/F7/cold confirmation. No runtime memory/IP injection.',sources=sources));return
if __name__=='__main__':main()
