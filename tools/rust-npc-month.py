#!/usr/bin/env python3
"""031：守軍月結來源準備與永久保存。限Docker。"""
import argparse,gzip,hashlib,importlib.util,io,json,os,shutil,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-npc-month-r1';REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def module(r,n):
 s=importlib.util.spec_from_file_location(n,r/'tools'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def write(p,v):
 assert p.parent.stat().st_uid==1000
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['prepare','freeze','audit','images','archive','verify','restore'])
 for n in ['project','work','out','archive']:ap.add_argument('--'+n,type=Path)
 a=ap.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  j=json.loads((a.archive/(BATCH+'.json')).read_text())
  for f in j['files']:
   ob=j['objects'][f['sha256']];p=a.archive/BATCH/ob['file'];assert sha(p)==ob['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-rust-npc-month-detached',files=len(j['files']),objects=len(j['objects'])));return
 r=a.project;q=a.work or r/REL;h=module(r,'prepare-owned-army-ui.py')
 if a.action=='archive':
  base=module(r,'rust-world-exits.py');base.BATCH=BATCH;base.REL=REL;base.main();return
 if a.action=='restore':
  for f in json.loads((r/'preserved'/(BATCH+'.json')).read_text())['files']:
   rel=Path(f['path']).relative_to(REL)
   if str(rel)=='native/8sword-remake'or str(rel).startswith('native/pack/'):
    p=q/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(h.stored(r,BATCH,f['path']));p.chmod(f['mode'])
  return
 if a.action in ['audit','images']:
  from PIL import Image,ImageDraw,ImageFont
  baseline=h.dependencies(r);assert list(map(len,baseline.values()))==[197,7,923,535]
  assert '153 passed; 0 failed'in(q/'native/tests.log').read_text()and 'FAILED'not in(q/'native/tests.log').read_text()
  assert(q/'reference/npc-month-reference.tsv').read_bytes()==(r/'internal/remake-rust/npc-month-reference.tsv').read_bytes()
  source=json.loads((q/'reference/receipt.json').read_text());caps=json.loads((q/'evidence/caps.json').read_text());assert source['scalar_vectors']==2520 and caps['slots']==252
  for v in source['controls']:
   assert v['counter_after']==(v['counter_before']+1)&65535 and v['seed_after']==0x5b3f58b2 and v['remaining']==324 and v['tempo']==6
   calls=v['rand_calls'];assert len(calls)==2 and [(n['return_segment'],n['return_offset'])for n in calls]==[(0x110,0x6494),(0x110,0x71b3)]
   seed=0x12345678
   for n in calls:assert n['seed_before']==seed;seed=(seed*214013+2531011)&0xffffffff
   assert seed==v['seed_after']
  gui=json.loads((q/'native/gui/receipt.json').read_text());assert gui['status']=='passed-rust-npc-month-gui'and len(gui['runs'])==3 and gui['binary_sha256']==sha(q/'native/8sword-remake')
  fnv=module(r,'rust-native-player.py').fnv;captures=[]
  for run in gui['runs']:
   assert run['exit']==0
   for cap in run['captures']:
    n=cap['number'];p=q/'native/gui'/run['name']/f'frame-{n:03}.ppm';assert p.read_bytes()==p.with_name(f'readback-{n:03}.ppm').read_bytes();assert cap['captured']['readback_equal']=='true'and cap['captured']['frame_hash']==format(fnv(Image.open(p).convert('RGBA').tobytes()),'016x');captures.append(dict(run=run['name'],label=cap['label'],sha256=sha(p),captured=cap['captured']))
  if a.action=='images':
   idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),30,index=3);canvas=Image.new('RGB',(1920,1440),(9,36,29));draw=ImageDraw.Draw(canvas);chosen=[]
   for i,(name,label,title)in enumerate([('month','before-month','月結前：守軍20／5／1'),('month','monthly-lishu','Rust月報：守軍26／10／10已提交'),('cold-report','regrown-battle','重新攻城：補兵後原式六隊戰場'),('cold-battle','battle-cold','獨立程序冷讀：兵數與畫布相同')]):
    run=next(v for v in gui['runs']if v['name']==name);cap=next(v for v in run['captures']if v['label']==label);p=q/'native/gui'/name/f"frame-{cap['number']:03}.ppm";x=i%2*960;y=i//2*720;draw.text((x+12,y+12),title,font=font,fill=(239,216,155));canvas.paste(Image.open(p).resize((960,660),Image.Resampling.LANCZOS),(x,y+60));chosen.append(dict(run=name,label=label,sha256=sha(p),captured=cap['captured']))
   assert not a.out.exists();canvas.save(a.out);write(a.out.with_suffix('.json'),dict(image_sha256=sha(a.out),binary_sha256=gui['binary_sha256'],sources=chosen,scope=gui['source']));return
  crate={str(p.relative_to(r/'internal/remake-rust')):sha(p)for p in(r/'internal/remake-rust').rglob('*')if p.is_file()};assert all(sha(q/'rust-source'/p)==v for p,v in crate.items());assert all(sha(q/'native/pack'/p)==v for p,v in json.loads((q/'media.json').read_text()).items())
  pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();ida=json.loads((q/'evidence/ida-monthly.json').read_text());assert hashlib.sha256(pam).hexdigest()==ida['source_sha256']==source['source_sha256'];checked=0
  # IDA MZ loader base10000h adds1000h to relocated segment words.
  # Apply only the source MZ relocation table; never skip differing operands.
  loaded=bytearray(pam);header=struct.unpack_from('<H',pam,8)[0]*16
  for i in range(struct.unpack_from('<H',pam,6)[0]):
   off,seg=struct.unpack_from('<HH',pam,struct.unpack_from('<H',pam,24)[0]+4*i);at=header+seg*16+off;struct.pack_into('<H',loaded,at,(struct.unpack_from('<H',pam,at)[0]+0x1000)&65535)
  for f in ida['functions']:
   for line in f['lines']:
    raw=bytes.fromhex(line['bytes']);at=line['file_offset'];assert loaded[at:at+len(raw)]==raw,(f['name'],line);checked+=1
  write(a.out,dict(status='passed-rust-npc-month-audit',tests=153,scalar_vectors=2520,slot_caps=252,original_month_controls=4,ida_byte_lines=checked,binary_sha256=sha(q/'native/8sword-remake'),crate=crate,baseline={k:len(v)for k,v in baseline.items()},gui=gui,sdl_captures=captures,source=source,execution=json.loads((q/'execution.json').read_text()),limits=['Explicit remaining1/seed1/30militia/partial guard and original adjacent position; not natural acquisition.','Month-local two RNG calls observed; no global UI RNG sequence parity claim.','No invented date/phase calendar; original travel-bar presentation remains later UI work.','Native v15 schema unchanged; existing pending reports are not retroactively refilled.']));return
 if a.action=='freeze':
  shutil.copytree(r/'internal/remake-rust',q/'rust-source');(q/'tools').mkdir()
  for n in ['rust-npc-month.py','rust-npc-month-reference.go','rust-npc-month-gui.py','rust-native-player.sh','check-ai-resolution-backlinks.py']:shutil.copy2(r/'tools'/n,q/'tools'/n)
  write(q/'media.json',{p.name:sha(p)for p in(q/'native/pack').iterdir()if p.is_file()});return
 assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir();(q/'native/pack').mkdir(parents=True);(q/'evidence').mkdir();(q/'probe').mkdir()
 for f in json.loads((r/'preserved/rust-ending-r1.json').read_text())['files']:
  if '/native/pack/'in f['path']:(q/'native/pack'/Path(f['path']).name).write_bytes(h.stored(r,'rust-ending-r1',f['path']))
 (q/'native/legacy-v15.chk').write_bytes(h.stored(r,'rust-ending-r1','native/gui/retreat-store/journey.chk'))
 (q/'evidence/ida-monthly.json').write_bytes(h.stored(r,'rust-monthly-r1','evidence/ida-monthly.json'));(q/'evidence/ida-exits.json').write_bytes(h.stored(r,'rust-world-exits-r1','evidence/ida-exits.json'));(q/'evidence/before-commit.state').write_bytes(h.stored(r,'monthly-r1','inputs/before-commit.state'))
 write(q/'evidence/baseline.json',h.dependencies(r));(q/'probe/go.mod').write_text('module npc-month-probe\n\ngo 1.24.0\n\nrequire github.com/wicanr2/dosgolem v0.0.0\nreplace github.com/wicanr2/dosgolem => /core\n');shutil.copy2(r/'tools/rust-npc-month-reference.go',q/'probe/main.go')
 print('prepared',q)
if __name__=='__main__':main()
