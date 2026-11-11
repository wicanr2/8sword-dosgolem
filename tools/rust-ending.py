#!/usr/bin/env python3
"""031 Rust最終戰／結局：資料準備與來源封存。限Docker。"""
import argparse,gzip,hashlib,importlib.util,io,json,os,shutil,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-ending-r1'
REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
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
  write(a.out,dict(status='passed-rust-ending-detached',files=len(j['files']),objects=len(j['objects'])));return
 r=a.project;q=a.work or r/REL;h=module(r,'prepare-owned-army-ui.py')
 if a.action=='archive':
  base=module(r,'rust-world-exits.py');base.BATCH=BATCH;base.REL=REL;base.main();return
 if a.action=='restore':
  j=json.loads((r/'preserved'/(BATCH+'.json')).read_text())
  for f in j['files']:
   rel=Path(f['path']).relative_to(REL)
   if str(rel)=='native/8sword-remake'or str(rel).startswith('native/pack/'):
    p=q/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(h.stored(r,BATCH,f['path']));p.chmod(f['mode'])
  return
 if a.action in ['audit','images']:
  from PIL import Image,ImageDraw,ImageFont
  baseline=h.dependencies(r);assert list(map(len,baseline.values()))==[197,7,923,535]
  assert '150 passed; 0 failed'in(q/'native/tests.log').read_text()
  assert(q/'export/captures/hd/ending-reference.tsv').read_bytes()==(r/'internal/remake-rust/ending-reference.tsv').read_bytes()
  expected={}
  for line in(r/'internal/remake-rust/ending-reference.tsv').read_text().splitlines():
   if line.startswith('#'):continue
   v=line.split('\t')
   for mode in range(4):expected[(v[2],v[0],str(mode))]=v[mode+3]
  actual={tuple(v[:3]):v[3]for l in(q/'native/ending-renders.tsv').read_text().splitlines()if(v:=l.split('\t'))};assert actual==expected and len(actual)==36
  gui=json.loads((q/'native/gui/receipt.json').read_text());assert gui['status']=='passed-rust-ending-gui'and len(gui['runs'])==5 and gui['binary_sha256']==sha(q/'native/8sword-remake')
  byrun={v['name']:v for v in gui['runs']};assert byrun['cold-ending']['final']['state_hash']==byrun['completed']['final']['state_hash'];assert byrun['cold-battle']['final']['resources']==byrun['cold-ending']['final']['resources']=='[1, 0, 120, 38, 1000, 4]';assert byrun['cold-ending']['final']['steps']=='101'
  fnv=module(r,'rust-native-player.py').fnv;captures=[]
  for run in gui['runs']:
   assert run['exit']==0
   for p in(q/'native/gui'/run['name']).glob('capture-*.tsv'):
    n=int(p.stem.split('-')[1]);meta=dict(l.split('\t',1)for l in p.read_text().splitlines());img=p.with_name(f'frame-{n:03}.ppm');back=p.with_name(f'readback-{n:03}.ppm');assert img.read_bytes()==back.read_bytes();assert meta['readback_equal']=='true'and meta['frame_hash']==format(fnv(Image.open(img).convert('RGBA').tobytes()),'016x');captures.append(dict(run=run['name'],number=n,meta=meta,image_sha256=sha(img)))
  if a.action=='images':
   idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),30,index=3);canvas=Image.new('RGB',(1920,1440),(9,36,29));draw=ImageDraw.Draw(canvas);chosen=[]
   for i,(name,label,title)in enumerate([('battle','final-six','Rust原式最終戰：原六隊守軍'),('cold-battle','original','結局原版像素：隸書工具列'),('cold-ending','end7','Rust HD結局：男女主角'),('cold-ending','title','HD片尾：正常播放至退出')]):
    run=next(v for v in gui['runs']if v['name']==name);cap=next(v for v in run['captures']if v['label']==label);p=q/'native/gui'/name/f"frame-{cap['number']:03}.ppm";x=i%2*960;y=i//2*720;draw.text((x+12,y+12),title,font=font,fill=(239,216,155));canvas.paste(Image.open(p).resize((960,660),Image.Resampling.LANCZOS),(x,y+60));chosen.append(dict(run=name,label=label,sha256=sha(p),meta=cap['captured']))
   assert not a.out.exists();canvas.save(a.out);write(a.out.with_suffix('.json'),dict(image_sha256=sha(a.out),binary_sha256=gui['binary_sha256'],sources=chosen,scope='Actual Linux Rust SDL captures at different moments, not a same-frame comparison. True v14 resources preserved; six explicit original player rows, eight swords, seed1 and original east neighbor terrain27 standing position controlled. Final NPC roster unchanged. No natural campaign clear claim.'));return
  crate={str(p.relative_to(r/'internal/remake-rust')):sha(p)for p in(r/'internal/remake-rust').rglob('*')if p.is_file()};assert all(sha(q/'rust-source'/p)==v for p,v in crate.items());assert all(sha(q/'native/pack'/p)==v for p,v in json.loads((q/'media.json').read_text()).items())
  original=json.loads(h.stored(r,'rust-guards-r1','evidence/ida-guards.json'));f=next(v for v in original['functions']if v['name']=='sub_12DDE');by={v['ida_linear']:v for v in f['lines']};pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0';header=struct.unpack_from('<H',pam,8)[0]*16
  for at,raw in [(0x13295,'c706e2560100'),(0x1329b,'0e'),(0x1329c,'e86fcf'),(0x132a7,'e814e8')]:assert by[at]['bytes']==raw and pam[at-0x10000+header:at-0x10000+header+len(bytes.fromhex(raw))]==bytes.fromhex(raw)
  write(a.out,dict(status='passed-rust-ending-audit',crate=crate,baseline={k:len(v)for k,v in baseline.items()},plan_sha256=sha(q/'native/pack/ending.bin'),plan_bytes=(q/'native/pack/ending.bin').stat().st_size,render_checks=36,tests=150,original_handoff_bytes_checked=4,gui=gui,sdl_captures=captures,execution=json.loads((q/'execution.json').read_text()),limits=['Controlled starting army/eight swords/terrain27 standing position, not natural acquisition or campaign completion.','Stable10ms source nodes and3000cycle time approximation, not every original page flip or hardware wall-clock parity.','MFIG is presented using approved HD battle music; MEND uses approved HD ending music. SDL dummy is technical audio validation only.']));return
 if a.action=='freeze':
  shutil.copytree(r/'internal/remake-rust',q/'rust-source');(q/'tools').mkdir()
  for n in ['rust-ending.py','rust-ending-export.go','capture-ending-overview.py','rust-ending-gui.py','rust-native-player.sh','rust-world.py','check-ai-resolution-backlinks.py']:shutil.copy2(r/'tools'/n,q/'tools'/n)
  write(q/'media.json',{p.name:sha(p)for p in(q/'native/pack').iterdir()if p.is_file()});return
 assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir();(q/'native/pack').mkdir(parents=True);(q/'evidence').mkdir()
 for f in json.loads((r/'preserved/rust-guards-r1.json').read_text())['files']:
  if '/native/pack/'in f['path']:(q/'native/pack'/Path(f['path']).name).write_bytes(h.stored(r,'rust-guards-r1',f['path']))
 (q/'native/legacy-v14.chk').write_bytes(h.stored(r,'rust-guards-r1','native/gui/cold-boss-store/journey.chk'))
 baseline=h.dependencies(r);assert list(map(len,baseline.values()))==[197,7,923,535];write(q/'evidence/baseline.json',baseline)
 prep=module(r,'capture-ending-overview.py');saved=sys.argv;sys.argv=['capture','prepare','--project',str(r),'--out',str(q/'export')];prep.main();sys.argv=saved
 p=q/'export/source/internal/eightsword/ending_overview_test.go';s=p.read_text().replace('TestEndingReadmeOverview','TestRustEndingExport')
 s=s.replace('defer e.Close()','defer e.Close()\n var export *rustEndingExport\n if hd { export = newRustEndingExport(t,e,dir) }',1)
 s=s.replace('overview := func() {','overview := func() {',1).replace('targets[e.Oracle.Steps()] = stage','export.sample(stage)\n targets[e.Oracle.Steps()] = stage',1)
 s=s.replace('overview()\n','if export != nil { export.capture() }\n overview()\n',1)
 s=s.replace('stateFile := filepath.Join(dir, "final.state")','if export != nil { export.finish() }\n stateFile := filepath.Join(dir, "final.state")',1);p.write_text(s)
 raw=(r/'tools/rust-ending-export.go').read_text().replace('//go:build ignore\n','',1);(p.parent/'rust_ending_export_test.go').write_text(raw)
 for n in ['PAM.AY','PAE.AY','MFIG.AY','MEND.AY']:
  p=r/'workplace/intake-20261023/sources/game/8sword'/n;shutil.copy2(p,q/'evidence'/n)if n in ['MFIG.AY','MEND.AY']else None
 print('prepared',q)
if __name__=='__main__':main()
