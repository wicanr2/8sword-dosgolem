#!/usr/bin/env python3
"""031原式開始選單的來源準備與永久保存。限Docker。"""
import argparse,gzip,hashlib,importlib.util,io,json,os,shutil,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-start-r1';REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def module(r,n):
 s=importlib.util.spec_from_file_location(n,r/'tools'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def write(p,v):
 assert p.parent.stat().st_uid==1000
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['prepare','assets','freeze','audit','images','archive','verify','restore'])
 for n in ['project','work','out','archive']:ap.add_argument('--'+n,type=Path)
 a=ap.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  j=json.loads((a.archive/(BATCH+'.json')).read_text())
  for f in j['files']:
   ob=j['objects'][f['sha256']];p=a.archive/BATCH/ob['file'];assert sha(p)==ob['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-rust-start-detached',files=len(j['files']),objects=len(j['objects'])));return
 r=a.project;q=a.work or r/REL;h=module(r,'prepare-owned-army-ui.py')
 if a.action=='archive':
  base=module(r,'rust-world-exits.py');base.BATCH=BATCH;base.REL=REL;base.main();return
 if a.action=='restore':
  for f in json.loads((r/'preserved'/(BATCH+'.json')).read_text())['files']:
   rel=Path(f['path']).relative_to(REL)
   if str(rel)=='native/8sword-remake'or str(rel).startswith('native/pack/'):
    p=q/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(h.stored(r,BATCH,f['path']));p.chmod(f['mode'])
  return
 if a.action=='freeze':
  shutil.copytree(r/'internal/remake-rust',q/'rust-source');(q/'tools').mkdir()
  for n in ['rust-start.py','export-rust-start-ida.py','rust-start-reference.go','rust-start-gui.py','rust-world.py','rust-native-player.sh','check-ai-resolution-backlinks.py']:shutil.copy2(r/'tools'/n,q/'tools'/n)
  write(q/'media.json',{p.name:sha(p)for p in(q/'native/pack').iterdir()if p.is_file()});return
 if a.action in ['audit','images']:
  from PIL import Image,ImageDraw,ImageFont
  baseline=h.dependencies(r);assert list(map(len,baseline.values()))==[197,7,923,535]
  log=(q/'native/tests.log').read_text();assert '167 passed; 0 failed'in log and 'FAILED'not in log
  assert(q/'reference-r2/start-input-reference.tsv').read_bytes()==(r/'internal/remake-rust/start-input-reference.tsv').read_bytes()
  source=json.loads((q/'reference-r2/receipt.json').read_text());assert source['local_input_vectors']==92
  initial=source['initial'];assert initial['resources']==[1,0,100,500,100,0]and initial['army_words']==[1,30]+[0]*10
  gui=json.loads((q/'native/gui/receipt.json').read_text());assert gui['status']=='passed-rust-start-gui'and len(gui['runs'])==5 and gui['binary_sha256']==sha(q/'native/8sword-remake')
  fnv=module(r,'rust-native-player.py').fnv;captures=[]
  for run in gui['runs']:
   assert run['exit']==0
   for cap in run['captures']:
    n=cap['number'];p=q/'native/gui'/run['name']/f'frame-{n:03}.ppm';assert p.read_bytes()==p.with_name(f'readback-{n:03}.ppm').read_bytes();assert cap['captured']['readback_equal']=='true'and cap['captured']['frame_hash']==format(fnv(Image.open(p).convert('RGBA').tobytes()),'016x');captures.append(dict(run=run['name'],label=cap['label'],sha256=sha(p),captured=cap['captured']))
  assert len(captures)==17
  if a.action=='images':
   idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),28,index=3);canvas=Image.new('RGB',(1920,1440),(9,36,29));draw=ImageDraw.Draw(canvas);chosen=[]
   for i,(name,label,title)in enumerate([('fresh','main-lishu','原式三項開始選單：隸書'),('fresh','new-confirm','新遊戲先確認，取消保留舊進度'),('fresh','music-last','十首 HD 音樂欣賞：草書與曲目循環'),('cold','continued-world','新遊戲正常移動、保存與獨立程序續玩')]):
    run=next(v for v in gui['runs']if v['name']==name);cap=next(v for v in run['captures']if v['label']==label);p=q/'native/gui'/name/f"frame-{cap['number']:03}.ppm";x=i%2*960;y=i//2*720;draw.text((x+12,y+12),title,font=font,fill=(239,216,155));canvas.paste(Image.open(p).resize((960,660),Image.Resampling.LANCZOS),(x,y+60));chosen.append(dict(run=name,label=label,sha256=sha(p),captured=cap['captured']))
   assert not a.out.exists();canvas.save(a.out);write(a.out.with_suffix('.json'),dict(image_sha256=sha(a.out),binary_sha256=gui['binary_sha256'],sources=chosen,scope=gui['source']));return
  crate={str(p.relative_to(r/'internal/remake-rust')):sha(p)for p in(r/'internal/remake-rust').rglob('*')if p.is_file()};assert all(sha(q/'rust-source'/p)==v for p,v in crate.items());assert all(sha(q/'native/pack'/p)==v for p,v in json.loads((q/'media.json').read_text()).items())
  ida=json.loads((q/'evidence/ida-start.json').read_text());pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()==ida['probe']['source_sha256']==source['source_sha256'];loaded=bytearray(pam);header=struct.unpack_from('<H',pam,8)[0]*16
  for i in range(struct.unpack_from('<H',pam,6)[0]):
   off,seg=struct.unpack_from('<HH',pam,struct.unpack_from('<H',pam,24)[0]+4*i);at=header+seg*16+off;struct.pack_into('<H',loaded,at,(struct.unpack_from('<H',pam,at)[0]+0x1000)&65535)
  checked=0
  for f in ida['functions']:
   for v in f['lines']:
    raw=bytes.fromhex(v['bytes']);at=v['file_offset'];assert loaded[at:at+len(raw)]==raw;checked+=1
  font_records=[]
  for name in ['noto','lishu','caoshu']:
   old=h.stored(r,'rust-items-r1',f'native/pack/font-{name}.bin');new=(q/f'native/pack/font-{name}.bin').read_bytes();entries=lambda b:{struct.unpack_from('<I',b,i)[0]:b[i+4:i+4100]for i in range(12,len(b)-8,4100)};before=entries(old);after=entries(new);assert all(after[k]==v for k,v in before.items());font_records.append(dict(name=name,old=len(before),new=len(after),old_cells_unchanged=True))
  media=json.loads((q/'evidence/media-start.json').read_text());assert len(media['tracks'])==10
  for t in media['tracks']:assert sha(q/'native/pack'/t['native_file'])==t['sha256']
  assert len(list((q/'native/pack').iterdir()))==155
  write(a.out,dict(status='passed-rust-start-audit',tests=167,original_input_vectors=92,original_initial=initial,ida_functions=len(ida['functions']),ida_byte_lines=checked,binary_sha256=gui['binary_sha256'],crate=crate,baseline={k:len(v)for k,v in baseline.items()},fonts=font_records,media_files=155,hd_music_tracks=10,gui=gui,sdl_captures=captures,execution=json.loads((q/'execution.json').read_text()),limits=['Native menu simplifies original striped backing; source strings and positions retained, not pixel parity.','Native audio uses approved HD OGG; original Magic Sound hardware advertisements omitted as platform adaptation.','Original seed fixed before tested main-menu actions; not global UI RNG-call parity.','Original full PREDELLA opening, remaining toolbar and release packaging remain separate.','SDL dummy audio proves decoding/queue output, not a fresh human listening acceptance.']));return
 if a.action=='assets':
  pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0';ds=struct.unpack_from('<H',pam,8)[0]*16+0x1d780
  string=lambda off,n:pam[ds+off:ds+off+n].split(b'\0')[0].decode('big5')
  rows=['# kind index x_byte y text; original PAM source text/coordinates']
  for i in range(3):rows.append(f'MAIN\t{i}\t26\t{63+i*20}\t'+string(158+i*60,60))
  for kind,off,x,y in [('WARN',338,17,133),('ASK',398,17,153),('YES',0x42,49,153),('NO',0x48,55,153)]:rows.append(f'{kind}\t0\t{x}\t{y}\t'+string(off,60 if kind in ['WARN','ASK']else 6))
  art=r/'workplace/player/assets-painted-r69';cues=json.loads((art/'music.json').read_text())['cues'];assert len(cues)==10
  music=['# id title file fnv64; approved HD OGG, original order'];records=[];fnv=module(r,'rust-native-player.py').fnv
  for i,v in enumerate(cues):
   assert v['id']==i+1;title=string(0x2f6+i*20,20);assert ''.join(title.split())==v['title'];rows.append(f'MUSIC\t{i}\t31\t{3+i*20}\t'+title)
   name={2:'world-music.ogg',3:'music.ogg',10:'music-ending.ogg'}.get(v['id'],f'start-music-{v["id"]}.ogg');p=art/v['file'];assert sha(p)==v['sha256'];target=q/'native/pack'/name
   if target.exists():assert sha(target)==v['sha256']
   else:shutil.copy2(p,target)
   music.append(f'{v["id"]}\t{v["title"]}\t{name}\t{fnv(target.read_bytes()):016x}');records.append(dict(**v,native_file=name))
  for name,data in [('start-layout.tsv','\n'.join(rows)+'\n'),('start-music.tsv','\n'.join(music)+'\n')]:
   (q/name).write_text(data);shutil.copy2(q/name,r/'internal/remake-rust'/name)
  shutil.copy2(q/'reference-r2/start-input-reference.tsv',r/'internal/remake-rust/start-input-reference.tsv');write(q/'evidence/media-start.json',dict(status='passed-approved-start-media',tracks=records,original_menu_layout=rows));return
 assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir()
 for n in ['native/pack','evidence','ida','probe']:(q/n).mkdir(parents=True)
 for f in json.loads((r/'preserved/rust-items-r1.json').read_text())['files']:
  if '/native/pack/'in f['path']:(q/'native/pack'/Path(f['path']).name).write_bytes(h.stored(r,'rust-items-r1',f['path']))
 (q/'native/legacy-v16.chk').write_bytes(h.stored(r,'rust-items-r1','native/gui/cold-store/journey.chk'))

 db=r/'workplace/probe-20261023/text-first/PAM.i64';assert sha(db)=='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac';shutil.copy2(db,q/'ida/PAM.i64')
 write(q/'evidence/baseline.json',h.dependencies(r));(q/'probe/go.mod').write_text('module start-probe\n\ngo 1.24.0\n\nrequire github.com/wicanr2/dosgolem v0.0.0\nreplace github.com/wicanr2/dosgolem => /core\n')
 print('prepared',q)
if __name__=='__main__':main()
