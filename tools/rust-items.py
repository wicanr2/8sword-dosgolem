#!/usr/bin/env python3
"""031八寶物的來源準備、核對及永久保存。限Docker。"""
import argparse,gzip,hashlib,importlib.util,io,json,os,shutil,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-items-r1';REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def module(r,n):
 s=importlib.util.spec_from_file_location(n,r/'tools'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def write(p,v):
 assert p.parent.stat().st_uid==1000
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['prepare','assets','audit','images','freeze','archive','verify','restore'])
 for n in ['project','work','out','archive']:ap.add_argument('--'+n,type=Path)
 a=ap.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  j=json.loads((a.archive/(BATCH+'.json')).read_text())
  for f in j['files']:
   ob=j['objects'][f['sha256']];p=a.archive/BATCH/ob['file'];assert sha(p)==ob['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-rust-items-detached',files=len(j['files']),objects=len(j['objects'])));return
 r=a.project;q=a.work or r/REL;h=module(r,'prepare-owned-army-ui.py')
 if a.action=='archive':
  base=module(r,'rust-world-exits.py');base.BATCH=BATCH;base.REL=REL;base.main();return
 if a.action=='restore':
  for f in json.loads((r/'preserved'/(BATCH+'.json')).read_text())['files']:
   rel=Path(f['path']).relative_to(REL)
   if str(rel)=='native/8sword-remake'or str(rel).startswith('native/pack/'):
    p=q/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(h.stored(r,BATCH,f['path']));p.chmod(f['mode'])
  return
 if a.action=='assets':
  from PIL import Image
  pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0';ds=struct.unpack_from('<H',pam,8)[0]*16+0x1d780
  names=[''.join(pam[ds+0x263a+14*i:ds+0x263a+14*(i+1)].split(b'\0')[0].decode('big5').split())for i in range(8)];assert all(1<=len(n)<=4 for n in names);(q/'item-names.tsv').write_text('\n'.join(names)+'\n')
  for name in ['items-reference.tsv','recruit-token-reference.tsv']:shutil.copy2(q/'reference'/name,r/'internal/remake-rust'/name)
  shutil.copy2(q/'item-names.tsv',r/'internal/remake-rust/item-names.tsv');art=r/'workplace/player/assets-painted-r69';manifest=json.loads((art/'man-items.json').read_text());rows=[];fnv=module(r,'rust-native-player.py').fnv
  for i in range(1,8):
   entry=next(v for v in manifest['entries']if v['source_index']==12+i);p=art/entry['image']['file'];assert sha(p)==entry['image']['sha256'];im=Image.open(p).convert('RGBA').resize((96,96),Image.Resampling.LANCZOS);raw=b'8SRGBA01'+struct.pack('<II',96,96)+im.tobytes();out=q/f'native/pack/item-{i}.rgba';out.write_bytes(raw+struct.pack('<Q',fnv(raw)));rows.append(dict(item=i,source=entry,sha256=sha(out)))
  write(q/'evidence/assets.json',dict(status='passed-approved-item-media',names=names,items=rows));return
 if a.action=='freeze':
  shutil.copytree(r/'internal/remake-rust',q/'rust-source');(q/'tools').mkdir()
  for n in ['rust-items.py','export-rust-items-ida.py','rust-items-reference.go','rust-items-gui.py','rust-world.py','rust-native-player.sh','check-ai-resolution-backlinks.py']:shutil.copy2(r/'tools'/n,q/'tools'/n)
  write(q/'media.json',{p.name:sha(p)for p in(q/'native/pack').iterdir()if p.is_file()});return
 if a.action in ['audit','images']:
  from PIL import Image,ImageDraw,ImageFont
  baseline=h.dependencies(r);assert list(map(len,baseline.values()))==[197,7,923,535]
  log=(q/'native/tests-final.log').read_text();assert '160 passed; 0 failed'in log and 'FAILED'not in log
  for name in ['items-reference.tsv','recruit-token-reference.tsv']:assert(q/'reference'/name).read_bytes()==(r/'internal/remake-rust'/name).read_bytes()
  assert(q/'item-names.tsv').read_bytes()==(r/'internal/remake-rust/item-names.tsv').read_bytes()
  source=json.loads((q/'reference/receipt.json').read_text());assert source['acquisition_cases']==32 and source['recruitment_vectors']==192
  for v in source['records']:
   assert v['rand_calls']==1 and v['seed_after']==0xb3e97b5b;want=v['flags_before'][:]
   if v['mode']==0:want[v['item']]=1
   assert v['flags_after']==want and v['found']==(v['mode']==0)and v['capacity']==(3 if v['mode']==0 and v['item']==0 else 9)
  gui=json.loads((q/'native/gui/receipt.json').read_text());assert gui['status']=='passed-rust-items-gui'and len(gui['runs'])==3 and gui['binary_sha256']==sha(q/'native/8sword-remake')
  fnv=module(r,'rust-native-player.py').fnv;captures=[]
  for run in gui['runs']:
   assert run['exit']==0
   for cap in run['captures']:
    n=cap['number'];p=q/'native/gui'/run['name']/f'frame-{n:03}.ppm';assert p.read_bytes()==p.with_name(f'readback-{n:03}.ppm').read_bytes();assert cap['captured']['readback_equal']=='true'and cap['captured']['frame_hash']==format(fnv(Image.open(p).convert('RGBA').tobytes()),'016x');captures.append(dict(run=run['name'],label=cap['label'],sha256=sha(p),captured=cap['captured']))
  assert len(captures)==9
  if a.action=='images':
   idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),30,index=3);canvas=Image.new('RGB',(1920,1440),(9,36,29));draw=ImageDraw.Draw(canvas);chosen=[]
   for i,(name,label,title)in enumerate([('gold','gold-found','F6實際尋得黃金令牌'),('gold','eight-items-lishu','F1八寶物：隸書與透明圖示'),('cold','eight-items-caoshu','獨立程序冷讀：草書與八寶物'),('battle','first-attack','原式戰場：寶物效果下正常出手')]):
    run=next(v for v in gui['runs']if v['name']==name);cap=next(v for v in run['captures']if v['label']==label);p=q/'native/gui'/name/f"frame-{cap['number']:03}.ppm";x=i%2*960;y=i//2*720;draw.text((x+12,y+12),title,font=font,fill=(239,216,155));canvas.paste(Image.open(p).resize((960,660),Image.Resampling.LANCZOS),(x,y+60));chosen.append(dict(run=name,label=label,sha256=sha(p),captured=cap['captured']))
   assert not a.out.exists();canvas.save(a.out);write(a.out.with_suffix('.json'),dict(image_sha256=sha(a.out),binary_sha256=gui['binary_sha256'],sources=chosen,scope=gui['source']));return
  crate={str(p.relative_to(r/'internal/remake-rust')):sha(p)for p in(r/'internal/remake-rust').rglob('*')if p.is_file()};assert all(sha(q/'rust-source'/p)==v for p,v in crate.items());assert all(sha(q/'native/pack'/p)==v for p,v in json.loads((q/'media.json').read_text()).items())
  ida=json.loads((q/'evidence/ida-items.json').read_text());pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()==ida['probe']['source_sha256']==source['source_sha256'];loaded=bytearray(pam);header=struct.unpack_from('<H',pam,8)[0]*16
  for i in range(struct.unpack_from('<H',pam,6)[0]):
   off,seg=struct.unpack_from('<HH',pam,struct.unpack_from('<H',pam,24)[0]+4*i);at=header+seg*16+off;struct.pack_into('<H',loaded,at,(struct.unpack_from('<H',pam,at)[0]+0x1000)&65535)
  checked=0
  for f in ida['functions']:
   for v in f['lines']:
    raw=bytes.fromhex(v['bytes']);at=v['file_offset'];assert loaded[at:at+len(raw)]==raw;checked+=1
  font_records=[]
  for name in ['noto','lishu','caoshu']:
   old=h.stored(r,'rust-npc-month-r1',f'native/pack/font-{name}.bin');new=(q/f'native/pack/font-{name}.bin').read_bytes();entries=lambda b:{struct.unpack_from('<I',b,i)[0]:b[i+4:i+4100]for i in range(12,len(b)-8,4100)};before=entries(old);after=entries(new);assert all(after[k]==v for k,v in before.items());font_records.append(dict(name=name,old=len(before),new=len(after),old_cells_unchanged=True))
  assert len(list((q/'native/pack').iterdir()))==148
  for i in range(1,8):
   raw=(q/f'native/pack/item-{i}.rgba').read_bytes();assert raw[:8]==b'8SRGBA01'and struct.unpack_from('<II',raw,8)==(96,96);alpha=raw[19:-8:4];assert 0 in alpha and 255 in alpha
  write(a.out,dict(status='passed-rust-items-audit',tests=160,original_acquisition_cases=32,original_recruit_vectors=192,ida_functions=len(ida['functions']),ida_byte_lines=checked,binary_sha256=gui['binary_sha256'],crate=crate,baseline={k:len(v)for k,v in baseline.items()},fonts=font_records,media_files=148,gui=gui,sdl_captures=captures,execution=json.loads((q/'execution.json').read_text()),limits=['Explicit previous items/coordinates/seed and battle militia fixture; not natural acquisition of all items.','Original local acquisition skips graphics/input; one search RNG call proven, not global UI RNG parity.','Golden-token recruitment preserves post-division signed word behavior within native supported resource domain.','Runtime item caches use existing Rust Pillow LANCZOS presentation; not Go-cache pixel parity.']));return
 assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir()
 for n in ['native/pack','evidence','ida','probe']:(q/n).mkdir(parents=True)
 for f in json.loads((r/'preserved/rust-npc-month-r1.json').read_text())['files']:
  if '/native/pack/'in f['path']:(q/'native/pack'/Path(f['path']).name).write_bytes(h.stored(r,'rust-npc-month-r1',f['path']))
 (q/'native/legacy-v15.chk').write_bytes(h.stored(r,'rust-npc-month-r1','native/gui/cold-battle-store/journey.chk'))
 (q/'evidence/ida-world-magic.json').write_bytes(h.stored(r,'rust-world-magic-r1','evidence/ida-world-magic.json'))
 db=r/'workplace/probe-20261023/text-first/PAM.i64';assert sha(db)=='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac';shutil.copy2(db,q/'ida/PAM.i64')
 write(q/'evidence/baseline.json',h.dependencies(r));(q/'probe/go.mod').write_text('module items-probe\n\ngo 1.24.0\n\nrequire github.com/wicanr2/dosgolem v0.0.0\nreplace github.com/wicanr2/dosgolem => /core\n')
 print('prepared',q)
if __name__=='__main__':main()
