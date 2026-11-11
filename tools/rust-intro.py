#!/usr/bin/env python3
"""031完整開場：固定來源準備、宣告式媒體與永久保存。限Docker。"""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-intro-r1';REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def module(r,n):
 s=importlib.util.spec_from_file_location(n,r/'tools'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','assets','audit','images','freeze','archive','verify','restore'])
 for k in ['project','work','out','archive']:ap.add_argument('--'+k,type=Path)
 a=ap.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=json.loads((a.archive/(BATCH+'.json')).read_text())
  for f in d['files']:
   ob=d['objects'][f['sha256']];p=a.archive/BATCH/ob['file'];assert sha(p)==ob['stored_sha256'];b=gzip.decompress(p.read_bytes());assert len(b)==f['bytes']and hashlib.sha256(b).hexdigest()==f['sha256']
  a.out.write_text(json.dumps(dict(status='passed-rust-intro-detached',files=len(d['files']),objects=len(d['objects'])))+'\n');return
 r=a.project;q=a.work or r/REL;h=module(r,'prepare-owned-army-ui.py')
 if a.action=='archive':
  m=module(r,'rust-world-exits.py');m.BATCH=BATCH;m.REL=REL;m.main();return
 if a.action=='restore':
  for f in json.loads((r/'preserved'/(BATCH+'.json')).read_text())['files']:
   rel=Path(f['path']).relative_to(REL)
   if str(rel)=='native/8sword-remake'or str(rel).startswith('native/pack/'):
    p=q/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(h.stored(r,BATCH,f['path']));p.chmod(f['mode'])
  return
 if a.action=='assets':
  from PIL import Image
  raw=(q/'export/captures/intro.bin').read_bytes();assert raw[:8]==b'8SINTRO1';at=20+64000*2;n=struct.unpack_from('<I',raw,at)[0];at+=4;out=bytearray(raw[:at]);out[:8]=b'8SINTRO2';shapes=[]
  for i in range(n):
   w,height,kind=struct.unpack_from('<HHB',raw,at);at+=5;stride=8 if kind==0 else 4;b=raw[at:at+w*height*stride];at+=len(b);bbox=Image.frombytes('L',(w,height),b[stride-1::stride]).getbbox()or(0,0,1,1);x,y,z,t=bbox;crop=b''.join(b[(yy*w+x)*stride:(yy*w+z)*stride]for yy in range(y,t));out.extend(struct.pack('<HHBHHHH',w,height,kind,x,y,z-x,t-y));out.extend(crop)
   rebuilt=bytearray(len(b))
   for yy in range(y,t):rebuilt[(yy*w+x)*stride:(yy*w+z)*stride]=crop[(yy-y)*(z-x)*stride:(yy-y+1)*(z-x)*stride]
   assert bytes(rebuilt)==b,('alpha zero RGB must also be zero',i);shapes.append([w,height,kind,x,y,z-x,t-y])
  tail=at
  nb=struct.unpack_from('<I',raw,at)[0];at+=4
  for _ in range(nb):_,z=struct.unpack_from('<II',raw,at);at+=8+z
  no=struct.unpack_from('<I',raw,at)[0];at+=4
  for _ in range(no):z=struct.unpack_from('<H',raw,at)[0];at+=2+z
  frames_at=at;nf=struct.unpack_from('<I',raw,at)[0];at+=4;frames=[]
  for i in range(nf):
   begin=at;ms,l=struct.unpack_from('<IB',raw,at);at+=5+l+2+16;nop=struct.unpack_from('<H',raw,at)[0];at+=2+4*nop;frames.append((ms,i,bytearray(raw[begin:at])))
  receipt=json.loads((q/'export/captures/receipt.json').read_text());clock=receipt if 'begin_cycle'in receipt else json.loads((q/'export/clock.json').read_text());events=[(max(0,(e['cycles']-clock['begin_cycle'])//3000),1 if e['kind']=='start'else 0)for e in receipt['music_events']if e['valid']and e['kind']in ['start','stop']];assert len(events)==2 and events[0][1]==1 and events[1][1]==0
  source_frames=frames[:]
  for ms,cue in events:
   if not any(f[0]==ms for f in frames):
    prior=max((f for f in source_frames if f[0]<=ms),key=lambda f:f[0]);node=bytearray(prior[2]);struct.pack_into('<I',node,0,ms);frames.append((ms,None,node))
  frames.sort(key=lambda f:f[0]);mapping={};out.extend(raw[tail:frames_at]);out.extend(struct.pack('<I',len(frames)))
  for index,(ms,origin,node)in enumerate(frames):
   cue=0
   for t,value in events:
    if t<=ms:cue=value
   node[6+node[4]]=cue;out.extend(node)
   if origin is not None:mapping[origin]=index
  refs=[]
  for line in(q/'export/captures/intro-reference.tsv').read_text().splitlines():
   if not line.startswith('#'):v=line.split('\t');v[0]=str(mapping[int(v[0])]);line='\t'.join(v)
   refs.append(line)
  (r/'internal/remake-rust/intro-reference.tsv').write_text('\n'.join(refs)+'\n');(q/'evidence/audio-timeline.json').write_text(json.dumps(dict(status='passed-original-start-stop-events',clock=clock,events_ms=events,source_nodes=nf,runtime_nodes=len(frames),silent_source_field_ignored=True),indent=2)+'\n')
  out.extend(b'');fnv=module(r,'rust-native-player.py').fnv;v=fnv(out);out.extend(struct.pack('<Q',v));(q/'native/pack/intro.bin').write_bytes(out);receipt=json.loads((q/'export/captures/receipt.json').read_text());plan=f'{receipt["duration_ms"]}\t{v:016x}\t{len(frames)}\n';(r/'internal/remake-rust/intro-plan.tsv').write_text(plan);(q/'evidence/texture-crop.json').write_text(json.dumps(dict(status='passed-lossless-transparent-crop',textures=n,source_sha256=hashlib.sha256(raw).hexdigest(),output_sha256=sha(q/'native/pack/intro.bin'),source_bytes=len(raw),output_bytes=len(out),reconstructed_all_source_texels=True,shapes=shapes),indent=2)+'\n');print('intro bytes',len(out));return
 if a.action in ['audit','images']:
  from PIL import Image,ImageDraw,ImageFont
  import io
  baseline=h.dependencies(r);assert list(map(len,baseline.values()))==[197,7,923,535]
  assert '171 passed; 0 failed'in(q/'native/tests.log').read_text()
  source=json.loads((q/'export/captures/receipt.json').read_text());assert(source['duration_ms'],source['frames'],source['prelude_order'],source['samples'])==(21254,588,64000,18)
  expected={}
  for line in(r/'internal/remake-rust/intro-reference.tsv').read_text().splitlines():
   if line.startswith('#'):continue
   v=line.split('\t')
   for i in range(4):expected[(v[2],v[0],str(i))]=v[i+3]
  actual={tuple(v[:3]):v[3]for l in(q/'native/intro-renders.tsv').read_text().splitlines()if(v:=l.split('\t'))};assert actual==expected and len(actual)==72
  gui=json.loads((q/'native/gui/receipt.json').read_text());assert gui['status']=='passed-rust-intro-gui'and len(gui['runs'])==3 and gui['binary_sha256']==sha(q/'native/8sword-remake');captures=[]
  for run in gui['runs']:
   assert run['exit']==0
   for c in run['captures']:
    p=q/'native/gui'/run['name']/f'frame-{c["number"]:03}.ppm';assert Image.open(p).size==(1920,1320)and p.read_bytes()==p.with_name(f'readback-{c["number"]:03}.ppm').read_bytes();assert c['captured']['readback_equal']=='true';captures.append(dict(run=run['name'],**c,sha256=sha(p)))
  assert any(v['run']=='natural'and v['captured'].get('phase')=='intro'and int(v['captured']['queued_bytes'])>0 for v in captures)
  assert len(captures)==15 and any(v['captured'].get('skip_pending')=='true'and v['captured'].get('revealed')=='64000'for v in captures)
  if a.action=='images':
   idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),28,index=3);canvas=Image.new('RGB',(1920,1440),(9,36,29));draw=ImageDraw.Draw(canvas);chosen=[]
   for i,(run,label,title)in enumerate([('natural','museum-portrait','Rust完整開場：古典美女與紫藍館景'),('skip','completed-before-skip','迎龍前導：略過仍先完成原揭圖順序'),('natural','story-5-text','第五頁故事：Rust直接合成背景與文字'),('natural','opening-to-menu','自然播完，同視窗回原式開始選單')]):
    v=next(v for v in captures if v['run']==run and v['label']==label);p=q/'native/gui'/run/f'frame-{v["number"]:03}.ppm';x=i%2*960;y=i//2*720;draw.text((x+12,y+12),title,font=font,fill=(239,216,155));canvas.paste(Image.open(p).resize((960,660),Image.Resampling.LANCZOS),(x,y+60));chosen.append(v)
   assert not a.out.exists();canvas.save(a.out);a.out.with_suffix('.json').write_text(json.dumps(dict(image_sha256=sha(a.out),binary_sha256=gui['binary_sha256'],sources=chosen,scope='Actual native Linux SDL captures at different moments. Natural full opening and menu; controlled world seed1 for new-game, no RAM/IP injection. Original/HD same-state checks use separate18-source-scene/72-render receipt.'),ensure_ascii=False,indent=2)+'\n');return
  crate={str(p.relative_to(r/'internal/remake-rust')):sha(p)for p in(r/'internal/remake-rust').rglob('*')if p.is_file()};assert all(sha(q/'rust-source'/n)==v for n,v in crate.items());assert all(sha(q/'native/pack'/n)==v for n,v in json.loads((q/'media.json').read_text()).items())
  fonts=[]
  for name in ['noto','lishu','caoshu']:
   before=h.stored(r,'rust-start-r1',f'native/pack/font-{name}.bin');after=(q/f'native/pack/font-{name}.bin').read_bytes();cells=lambda b:{struct.unpack_from('<I',b,i)[0]:b[i+4:i+4100]for i in range(12,len(b)-8,4100)};old,new=cells(before),cells(after);assert all(new[k]==v for k,v in old.items());fonts.append(dict(name=name,old=len(old),new=len(new),old_cells_unchanged=True))
  assert len(list((q/'native/pack').iterdir()))==156
  result=dict(status='passed-rust-intro-audit',tests=171,render_checks=72,source=source,audio_timeline=json.loads((q/'evidence/audio-timeline.json').read_text()),packet_crop=json.loads((q/'evidence/texture-crop.json').read_text()),crate=crate,baseline={k:len(v)for k,v in baseline.items()},binary_sha256=gui['binary_sha256'],fonts=fonts,media_files=156,gui=gui,sdl_captures=captures,execution=json.loads((q/'execution.json').read_text()),limits=['18 source-owned original indexed scenes and three-font HD renders from normal dosgolem run; source primitive/native parity inherits047. Not a fresh independent ScreenRGB pair per node.','10ms nodes/3000cycle/ms are presentation approximation, not hardware wall-clock.','Other-stage skip is immediate native UI; reveal skip waits complete image.','SDL dummy proves decode and queue, not new human listening.','Remaining toolbar,journey bar and release/platform verification remain separate.']);a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return
 if a.action=='freeze':
  shutil.copytree(r/'internal/remake-rust',q/'rust-source',dirs_exist_ok=True);(q/'tools').mkdir(exist_ok=True)
  for n in ['rust-intro.py','rust-intro-export.go','rust-intro-gui.py','rust-native-player.sh','check-ai-resolution-backlinks.py']:shutil.copy2(r/'tools'/n,q/'tools'/n)
  (q/'media.json').write_text(json.dumps({p.name:sha(p)for p in(q/'native/pack').iterdir()if p.is_file()},indent=2)+'\n');return
 assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir()
 for n in ['native/pack','evidence','export/source/internal','export/captures']:(q/n).mkdir(parents=True)
 for f in json.loads((r/'preserved/rust-start-r1.json').read_text())['files']:
  if '/native/pack/'in f['path']:(q/'native/pack'/Path(f['path']).name).write_bytes(h.stored(r,'rust-start-r1',f['path']))
 baseline=h.dependencies(r);assert list(map(len,baseline.values()))==[197,7,923,535];(q/'evidence/baseline.json').write_text(json.dumps(baseline,indent=2)+'\n')
 src=q/'export/source'
 for n in ['eightsword','ownedworld']:shutil.copytree(r/'internal'/n,src/'internal'/n)
 for n in ['go.mod','go.sum']:shutil.copy2(r/n,src/n)
 p=src/'go.mod';p.write_text(p.read_text()+'\nrequire github.com/wicanr2/dosgolem v0.0.0\nreplace github.com/wicanr2/dosgolem => /core\n')
 p=src/'internal/eightsword/source_intro.go';s=p.read_text();assert s.count('return p.cached')==1;s=s.replace('return p.cached','if rustIntroObserve != nil { rustIntroObserve(p,state,kind) }; return p.cached');p.write_text(s)
 raw=(r/'tools/rust-intro-export.go').read_text().replace('//go:build ignore\n','',1);(src/'internal/eightsword/rust_intro_export_test.go').write_text(raw)
 (q/'evidence/export-inputs.json').write_text(json.dumps(dict(go_inputs={str(p.relative_to(r)):sha(p)for n in ['eightsword','ownedworld']for p in(r/'internal'/n).rglob('*.go')},exporter_sha256=sha(r/'tools/rust-intro-export.go'),formal_sources_unchanged=True),indent=2)+'\n')
 print('prepared',q)
if __name__=='__main__':main()
