#!/usr/bin/env python3
"""原65守軍：資料還原、來源核對及永久保存。限Docker。"""
import argparse,gzip,hashlib,importlib.util,io,json,os,shutil,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-guards-r1';REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
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
  write(a.out,dict(status='passed-detached-rust-guards',files=len(idx['files']),objects=len(idx['objects'])));return
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
  for f in read(r/'preserved/rust-map-notice-r1.json')['files']:
   if '/native/pack/'in f['path']:(q/'native/pack'/Path(f['path']).name).write_bytes(h.stored(r,'rust-map-notice-r1',f['path']))
  (q/'native/legacy-v13.chk').write_bytes(h.stored(r,'rust-map-notice-r1','native/gui/continued-store/journey.chk'))
  functions=[];provenance=[]
  for name in ['ida-guard-world.json','ida-guard-rewards.json','ida-original-guards-r2.json']:
   raw=h.stored(r,'original-battle-guards-r1','evidence/'+name);j=json.loads(raw);provenance.append(dict(batch='original-battle-guards-r1',file=name,sha256=hashlib.sha256(raw).hexdigest()))
   for f in j['functions']:
    if f['name']in ['sub_12446','sub_12DDE','sub_132E0','sub_132B4','sub_11ABE','sub_19856']and f['name']not in[x['name']for x in functions]:functions.append(f)
  write(q/'evidence/ida-guards.json',dict(source_sha256=j.get('source_sha256',j.get('input_sha256')),database_sha256=j['database_sha256'],functions=functions,inputs=provenance,address_space='IDA9.4 MZ base10000h; runtimeCS0110 IP=IDA-10000h; DS1E88 offsets separate'));return
 if a.action=='freeze':
  shutil.copytree(r/'internal/remake-rust',q/'rust-source');(q/'tools').mkdir()
  for n in ['rust-guards.py','rust-world-exits.py','rust-guards-gui.py','rust-guards-reference.go','rust-native-player.sh','rust-world.py']:shutil.copy2(r/'tools'/n,q/'tools'/n)
  write(q/'media.json',{p.name:sha(p)for p in(q/'native/pack').iterdir()if p.is_file()});return
 if a.action=='audit':
  counts={k:len(v)for k,v in h.dependencies(r).items()};assert list(counts.values())==[197,7,923,535]
  crate={str(p.relative_to(r/'internal/remake-rust')):sha(p)for p in(r/'internal/remake-rust').rglob('*')if p.is_file()};assert all(sha(q/'rust-source'/p)==v for p,v in crate.items());assert all(sha(q/'native/pack'/p)==v for p,v in read(q/'media.json').items());assert '146 passed; 0 failed'in(q/'native/tests.log').read_text();assert(q/'evidence/guard-reference-r3.tsv').read_bytes()==(r/'internal/remake-rust/guard-reference.tsv').read_bytes();assert len((q/'evidence/guard-reference-r3.tsv').read_text().splitlines())==1229
  pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();word=lambda at:struct.unpack_from('<H',pam,at)[0];header=word(8)*16;relocs=[header+word(word(24)+i*4+2)*16+word(word(24)+i*4)for i in range(word(6))];j=read(q/'evidence/ida-guards.json');assert hashlib.sha256(pam).hexdigest()==j['source_sha256'];assert sha(r/'workplace/probe-20261023/text-first/PAM.i64')==j['database_sha256'];checked=0
  for f in j['functions']:
   for v in f['lines']:
    at=v.get('file_offset',v.get('original_file_offset'));want=bytes.fromhex(v['bytes']);assert at==v['ida_linear']-0x10000+header;raw=bytearray(pam[at:at+len(want)])
    for off in relocs:
     if at<=off and off+2<=at+len(want):struct.pack_into('<H',raw,off-at,(struct.unpack_from('<H',raw,off-at)[0]+0x1000)&65535)
    assert bytes(raw)==want;checked+=1
  ds=header+0x1d780;rows=[list(map(int,l.split('\t')))for l in(r/'internal/remake-rust/guard-catalog.tsv').read_text().splitlines()if not l.startswith('#')];assert len(rows)==42
  decode=module(r,'prepare-hd-intro.py').decode
  for area in range(8):
   raw=decode((q/f'native/pack/map{area+1}.ay').read_bytes());points=[(x,y)for y in range(80)for x in range(70)if raw[y*72+x]==113];selected=[v for v in rows if v[0]==area];assert [(v[2],v[3])for v in selected]==points
   for v in selected:assert list(struct.unpack_from('<12H',pam,ds+v[6]))==v[7:]and bool(v[4])==(struct.unpack_from('<HH',pam,ds+0x26bc+area*6)==(v[2],v[3]))
  gui=read(q/'native/gui/receipt.json');assert gui['status']=='passed-rust-guards-gui'and gui['binary_sha256']==sha(q/'native/8sword-remake')and len(gui['runs'])==7
  from PIL import Image
  fnv=module(r,'rust-native-player.py').fnv
  for run in gui['runs']:
   assert run['exit']==0
   for cap in run['captures']:
    f=q/'native/gui'/run['name']/f"frame-{cap['number']:03}.ppm";assert f.read_bytes()==f.with_name(f"readback-{cap['number']:03}.ppm").read_bytes();assert cap['captured']['frame_hash']==format(fnv(Image.open(f).convert('RGBA').tobytes()),'016x')
  write(a.out,dict(status='passed-rust-guards-audit',crate=crate,binary_sha256=sha(q/'native/8sword-remake'),baseline=counts,guard_sites=42,original_entry_cases=1176,original_reward_cases=52,ida_functions=len(j['functions']),ida_lines_verified=checked,gui=gui,execution=read(q/'execution.json')));return
 if a.action=='images':
  from PIL import Image,ImageDraw,ImageFont
  idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));raw=gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes());font=ImageFont.truetype(io.BytesIO(raw),30,index=3);gui=read(q/'native/gui/receipt.json');canvas=Image.new('RGB',(1920,1440),(9,36,29));draw=ImageDraw.Draw(canvas);sources=[]
  for i,(run,label,title)in enumerate([('battle','prompt','原式攻城確認：三字型與鍵鼠'),('cold-battle','cold-battle','原式戰場：戰中F7獨立冷讀'),('cold-win','cleared','守軍殘兵／勝利：重訪不再領獎'),('cold-boss','sword-cold','頭目勝利：名劍與F1冷讀')]):
   row=next(v for v in gui['runs']if v['name']==run);cap=next(v for v in row['captures']if v['label']==label);f=q/'native/gui'/run/f"frame-{cap['number']:03}.ppm";x=i%2*960;y=i//2*720;draw.text((x+12,y+12),title,font=font,fill=(239,216,155));canvas.paste(Image.open(f).resize((960,660),Image.Resampling.LANCZOS),(x,y+60));sources.append(dict(run=run,label=label,sha256=sha(f),captured=cap['captured']))
  assert not a.out.exists();canvas.save(a.out);write(a.out.with_suffix('.json'),dict(platform='Linux Rust SDL2',binary_sha256=gui['binary_sha256'],image_sha256=sha(a.out),scope='Real v13 resources/magic; original guard adjacent position/seed1 and explicit1000militia/200archer combat fixtures. Normal XTest combat/save/cold/revisit. Not natural acquisition or final-ending completion.',sources=sources));return
if __name__=='__main__':main()
