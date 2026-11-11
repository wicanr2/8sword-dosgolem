#!/usr/bin/env python3
"""原行程條：來源準備、核對與永久保存。限Docker。"""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-travelbar-r1';REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def module(r,n):
 s=importlib.util.spec_from_file_location(n,r/'tools'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','audit','images','freeze','archive','verify','restore'])
 for n in ['project','work','out','archive']:ap.add_argument('--'+n,type=Path)
 a=ap.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=json.loads((a.archive/(BATCH+'.json')).read_text())
  for f in d['files']:
   ob=d['objects'][f['sha256']];p=a.archive/BATCH/ob['file'];assert sha(p)==ob['stored_sha256'];b=gzip.decompress(p.read_bytes());assert len(b)==f['bytes']and hashlib.sha256(b).hexdigest()==f['sha256']
  a.out.write_text(json.dumps(dict(status='passed-rust-travelbar-detached',files=len(d['files']),objects=len(d['objects'])))+'\n');return
 r=a.project;q=a.work or r/REL;h=module(r,'prepare-owned-army-ui.py')
 if a.action=='archive':m=module(r,'rust-world-exits.py');m.BATCH=BATCH;m.REL=REL;m.main();return
 if a.action=='restore':
  for f in json.loads((r/'preserved'/(BATCH+'.json')).read_text())['files']:
   rel=Path(f['path']).relative_to(REL)
   if str(rel)=='native/8sword-remake'or str(rel).startswith('native/pack/'):
    p=q/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(h.stored(r,BATCH,f['path']));p.chmod(f['mode'])
  return
 if a.action=='freeze':
  shutil.copytree(r/'internal/remake-rust',q/'rust-source');(q/'tools').mkdir()
  for n in ['rust-travelbar.py','rust-travelbar-reference.go','rust-travelbar-gui.py','export-rust-travelbar-ida.py','rust-native-player.sh','check-ai-resolution-backlinks.py']:shutil.copy2(r/'tools'/n,q/'tools'/n)
  (q/'media.json').write_text(json.dumps({p.name:sha(p)for p in(q/'native/pack').iterdir()if p.is_file()},indent=2)+'\n');return
 if a.action in ['audit','images']:
  from PIL import Image,ImageDraw,ImageFont,ImageChops
  import io,struct
  baseline=h.dependencies(r);assert list(map(len,baseline.values()))==[197,7,923,535]
  assert '173 passed; 0 failed'in(q/'native/tests.log').read_text();assert(q/'reference/travelbar-reference.tsv').read_bytes()==(r/'internal/remake-rust/travelbar-reference.tsv').read_bytes()
  source=json.loads((q/'reference/receipt.json').read_text());assert source['vectors']==84
  gui=json.loads((q/'native/gui/receipt.json').read_text());assert gui['status']=='passed-rust-travelbar-gui'and len(gui['runs'])==3 and gui['binary_sha256']==sha(q/'native/8sword-remake');captures=[];tiles=(q/'evidence/travel-ticks-source.bin').read_bytes();palette=[(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),(170,85,0),(170,170,170),(85,85,85),(85,85,255),(85,255,85),(85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]
  for run in gui['runs']:
   assert run['exit']==0
   for c in run['captures']:
    p=q/'native/gui'/run['name']/f'frame-{c["number"]:03}.ppm';assert p.read_bytes()==p.with_name(f'readback-{c["number"]:03}.ppm').read_bytes();assert c['captured']['readback_equal']=='true';im=Image.open(p).convert('RGB');state=c['captured'];n=min(54,(int(state['steps'])+int(state['tempo'])-1)//int(state['tempo']));assert n==int(state['travel_ticks']);tile=tiles[(2 if state['stopped']=='true'else 1)*19:];expected=Image.new('RGB',(1296,18));d=ImageDraw.Draw(expected)
    for y in range(3):
     color=sum(((tile[4+plane*3+y]>>7)&1)<<plane for plane in range(4));d.rectangle((0,y*6,n*24-1,y*6+5),fill=palette[color])
    visible=state['phase']=='world'
    if visible:assert im.crop((48,1206,1344,1224)).tobytes()==expected.tobytes()
    else:assert state['phase']=='monthly'and len(set(im.crop((48,1206,1344,1224)).getdata()))==1
    captures.append(dict(run=run['name'],**c,sha256=sha(p),bar_visible=visible,source_strip_equal=True if visible else None))
  assert len(captures)==8
  if a.action=='images':
   idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),28,index=3);canvas=Image.new('RGB',(1920,1608),(9,36,29));draw=ImageDraw.Draw(canvas);chosen=[]
   for i,(run,label,title)in enumerate([('normal','323-54','323步／54格：原版正常三列配色'),('normal','318-53','318步／53格：末格已清除'),('stop','stopped-one','正常F4停時：暖色一格，F7與冷讀保持'),('cold','new-month','正常走入月結：恢復324步與正常54格')]):
    v=next(v for v in captures if v['run']==run and v['label']==label);p=q/'native/gui'/run/f'frame-{v["number"]:03}.ppm';im=Image.open(p);x=i%2*960;y=i//2*804;draw.text((x+12,y+8),title,font=font,fill=(239,216,155));canvas.paste(im.resize((960,660),Image.Resampling.LANCZOS),(x,y+48));canvas.paste(im.crop((48,1206,1344,1224)).resize((960,72),Image.Resampling.NEAREST),(x,y+720));chosen.append(v)
   canvas.save(a.out);a.out.with_suffix('.json').write_text(json.dumps(dict(image_sha256=sha(a.out),binary_sha256=gui['binary_sha256'],sources=chosen,scope=gui['source'],strip_insets='Nearest-neighbor enlargement of the actual SDL bar;full screenshots otherwise unchanged.'),ensure_ascii=False,indent=2)+'\n');return
  crate={str(p.relative_to(r/'internal/remake-rust')):sha(p)for p in(r/'internal/remake-rust').rglob('*')if p.is_file()};assert all(sha(q/'rust-source'/n)==v for n,v in crate.items())
  previous=json.loads((r/'preserved/rust-intro-r1.json').read_text());before={Path(f['path']).name:f['sha256']for f in previous['files']if'/native/pack/'in f['path']};assert len(before)==156 and before=={p.name:sha(p)for p in(q/'native/pack').iterdir()};assert before==json.loads((q/'media.json').read_text())
  # Independent previous-version SDL frame at the identical genuine saved world.
  prior=json.loads((r/'preserved/rust-intro-audit-r1.json').read_text());oldcap=next(c for c in prior['gui']['runs'][0]['captures']if c['label']=='opening-new-world');newcap=next(c for c in captures if c['label']=='323-54');assert oldcap['captured']['state_hash']==newcap['captured']['state_hash'];oldraw=h.stored(r,'rust-intro-r1',f'native/gui/natural/frame-{oldcap["number"]:03}.ppm');(q/'evidence/previous-same-state.ppm').write_bytes(oldraw);old=Image.open(io.BytesIO(oldraw)).convert('RGB');new=Image.open(q/'native/gui/normal'/f'frame-{newcap["number"]:03}.ppm').convert('RGB');diff=ImageChops.difference(old,new);allowed=Image.new('L',old.size);d=ImageDraw.Draw(allowed);d.rectangle((24,1194,263,1229),fill=255);d.rectangle((48,1206,1343,1223),fill=255);inverse=ImageChops.invert(allowed);outside=ImageChops.multiply(diff,Image.merge('RGB',(inverse,inverse,inverse)));assert outside.getbbox()is None
  ida=json.loads((q/'evidence/ida-travelbar.json').read_text());pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();loaded=bytearray(pam);header=struct.unpack_from('<H',pam,8)[0]*16
  for i in range(struct.unpack_from('<H',pam,6)[0]):
   off,seg=struct.unpack_from('<HH',pam,struct.unpack_from('<H',pam,24)[0]+4*i);at=header+seg*16+off;struct.pack_into('<H',loaded,at,(struct.unpack_from('<H',pam,at)[0]+0x1000)&65535)
  checked=0
  for f in ida['functions']:
   for v in f['lines']:
    b=bytes.fromhex(v['bytes']);assert loaded[v['file_offset']:v['file_offset']+len(b)]==b;checked+=1
  a.out.write_text(json.dumps(dict(status='passed-rust-travelbar-audit',tests=173,source=source,ida_functions=len(ida['functions']),ida_byte_lines=checked,baseline={k:len(v)for k,v in baseline.items()},binary_sha256=gui['binary_sha256'],crate=crate,media_files=156,all_media_unchanged=True,same_state_before_after=dict(state_hash=newcap['captured']['state_hash'],outside_bar_and_old_number_different_pixels=0),gui=gui,sdl_captures=captures,execution=json.loads((q/'execution.json').read_text()),limits=['Original local arithmetic and call geometry;primitive pixel contract inherits047,no fresh VGA oracle.','Fixture explicitly grants book/one stop charge/capacity3 and sets remaining1/seed1,then normalF4/walk/month/F7/cold.','Native presentation clamps illegal overlong bars to54 without changing world state;not original parity for illegal states.']),ensure_ascii=False,indent=2)+'\n');return
 assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir()
 for n in ['native/pack','evidence','ida','probe']:(q/n).mkdir(parents=True)
 for f in json.loads((r/'preserved/rust-intro-r1.json').read_text())['files']:
  if '/native/pack/'in f['path']:(q/'native/pack'/Path(f['path']).name).write_bytes(h.stored(r,'rust-intro-r1',f['path']))
 (q/'native/legacy-v16.chk').write_bytes(h.stored(r,'rust-intro-r1','native/gui/natural-store/journey.chk'))
 (q/'evidence/ida-monthly.json').write_bytes(h.stored(r,'rust-npc-month-r1','evidence/ida-monthly.json'));(q/'evidence/travel-ticks-source.bin').write_bytes(h.stored(r,'rust-npc-month-r1','reference/travel-ticks-source.bin'))
 shutil.copy2(r/'workplace/probe-20261023/text-first/PAM.i64',q/'ida/PAM.i64');(q/'probe/go.mod').write_text('module travelbar-probe\n\ngo 1.24.0\n\nrequire github.com/wicanr2/dosgolem v0.0.0\nreplace github.com/wicanr2/dosgolem => /core\n');(q/'evidence/baseline.json').write_text(json.dumps(h.dependencies(r),indent=2)+'\n')
 print('prepared',q)
if __name__=='__main__':main()
