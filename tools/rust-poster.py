#!/usr/bin/env python3
"""原行程條：來源準備、核對與永久保存。限Docker。"""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-poster-r1';REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
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
  a.out.write_text(json.dumps(dict(status='passed-rust-poster-detached',files=len(d['files']),objects=len(d['objects'])))+'\n');return
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
  for n in ['rust-poster.py','rust-poster-gui.py','rust-native-player.sh']:shutil.copy2(r/'tools'/n,q/'tools'/n)
  (q/'media.json').write_text(json.dumps({p.name:sha(p)for p in(q/'native/pack').iterdir()if p.is_file()},indent=2)+'\n');return
 if a.action in ['audit','images']:
  from PIL import Image,ImageDraw,ImageFont
  import io
  gui=json.loads((q/'native/gui/receipt.json').read_text());assert gui['status']=='passed-rust-poster-gui'
  captures=[]
  for run in gui['runs']:
   assert run['exit']==0
   for cap in run['captures']:
    folder=q/'native/gui'/run['name'];n=cap['number'];frame=folder/f'frame-{n:03}.ppm';full=folder/f'shell-frame-{n:03}.ppm';assert frame.read_bytes()==frame.with_name(f'readback-{n:03}.ppm').read_bytes();assert full.read_bytes()==full.with_name(f'shell-readback-{n:03}.ppm').read_bytes();im=Image.open(full).convert('RGB');assert im.size==(2944,1320);assert im.crop((512,0,2432,1320)).tobytes()==Image.open(frame).convert('RGB').tobytes();captures.append(dict(run=run['name'],**cap,full_sha256=sha(full)))
  if a.action=='images':
   idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),28,index=3);canvas=Image.new('RGB',(1920,980),(8,36,23));draw=ImageDraw.Draw(canvas);chosen=[]
   for i,(run,label,title)in enumerate([('play','menu-cover','同視窗主選單：經典封面'),('world','lishu','地圖／隸書：經典封面'),('battle','battle-off','原式戰場：海報關閉'),('ending','ending-cover','結局：經典封面')]):
    c=next(c for c in captures if c['run']==run and c['label']==label);im=Image.open(q/'native/gui'/run/f'shell-frame-{c["number"]:03}.ppm');x=i%2*960;y=i//2*490;draw.text((x+8,y+8),title,font=font,fill=(239,216,155));canvas.paste(im.resize((960,430),Image.Resampling.LANCZOS),(x,y+50));chosen.append(c)
   canvas.save(a.out);a.out.with_suffix('.json').write_text(json.dumps(dict(sources=chosen,image_sha256=sha(a.out),scope=gui['scope']),ensure_ascii=False,indent=2)+'\n');return
  tests=(q/'native/tests.log').read_text();assert '177 passed; 0 failed'in tests
  # Independent previous-version SDL world at the identical genuine checkpoint.
  prior=json.loads((r/'preserved/rust-travelbar-audit-r1.json').read_text());pc=next(c for c in prior['gui']['runs'][0]['captures']if c['label']=='323-54');nc=next(c for c in captures if c['run']=='world'and c['label']=='wings');assert pc['captured']['state_hash']==nc['captured']['state_hash'];oldraw=h.stored(r,'rust-travelbar-r1',f'native/gui/normal/frame-{pc["number"]:03}.ppm');(q/'evidence/previous-world.ppm').write_bytes(oldraw);assert Image.open(io.BytesIO(oldraw)).convert('RGB').tobytes()==Image.open(q/'native/gui/world'/f'frame-{nc["number"]:03}.ppm').convert('RGB').tobytes()
  previous=json.loads((r/'preserved/rust-travelbar-r1.json').read_text());old={Path(f['path']).name:f['sha256']for f in previous['files']if'/native/pack/'in f['path']};assert len(old)==156 and all(sha(q/'native/pack'/n)==v for n,v in old.items());crate={str(p.relative_to(r/'internal/remake-rust')):sha(p)for p in(r/'internal/remake-rust').rglob('*')if p.is_file()};assert all(sha(q/'rust-source'/n)==v for n,v in crate.items())
  a.out.write_text(json.dumps(dict(status='passed-rust-poster-audit',tests=177,runtime_files=160,unchanged_media=156,crate=crate,gui=gui,captures=captures,same_state_previous_world_equal=True,assets=json.loads((q/'evidence/assets.json').read_text()),execution=json.loads((q/'execution.json').read_text()),limits=['Presentation-only; full-game original/HD, AI and rules switches remain separate work.','Ending starts from the preserved real v15 ending checkpoint; not natural completion.','Audio uses dummy; no new listening or platform validation.']),ensure_ascii=False,indent=2)+'\n');return
 assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir()
 for n in ['native/pack','evidence']:(q/n).mkdir(parents=True)
 for f in json.loads((r/'preserved/rust-travelbar-r1.json').read_text())['files']:
  if '/native/pack/'in f['path']:(q/'native/pack'/Path(f['path']).name).write_bytes(h.stored(r,'rust-travelbar-r1',f['path']))
 (q/'native/legacy-v16.chk').write_bytes(h.stored(r,'rust-travelbar-r1','native/legacy-v16.chk'))
 # Genuine saved ending, retained in the previously verified native ending batch.
 end=json.loads((r/'preserved/rust-ending-r1.json').read_text());candidates=[f['path']for f in end['files']if f['path'].endswith('journey.chk')];print('ending candidates',candidates)
 (q/'evidence/ending-candidates.json').write_text(json.dumps(candidates))
 (q/'native/ending-v15.chk').write_bytes(h.stored(r,'rust-ending-r1','native/gui/ending.chk'))
 # Execute the exact established Go panel builder as a development exporter only.
 src=(r/'internal/eightsword/poster_toolbar.go').read_text();start=src.index('func makePosterPanels(');stop=src.index('\nfunc ',start+10);body=src[start:stop];(q/'evidence/poster-go-source.txt').write_text(src)
 go='package main\nimport("image";"image/color";_ "image/png";"math";"os";"encoding/binary")\nvar posterMatte=color.RGBA{8,36,23,255}\n'+body+'\nfunc main(){for _,s:=range []struct{id,file string;roi [2]image.Rectangle}{{"wings","poster-wings-approved-r1.png",[2]image.Rectangle{image.Rect(160,0,469,724),image.Rect(1640,0,1949,724)}},{"cover","poster-cover-approved-r1.png",[2]image.Rectangle{image.Rect(0,0,600,1402),image.Rect(522,0,1122,1402)}}}{f,e:=os.Open("/images/"+s.file);if e!=nil{panic(e)};im,_,e:=image.Decode(f);f.Close();if e!=nil{panic(e)};p:=makePosterPanels(im,s.roi);b:=[]byte("8SRGBA01");b=binary.LittleEndian.AppendUint32(b,1024);b=binary.LittleEndian.AppendUint32(b,1200);b=append(b,p.Pix...);h:=uint64(14695981039346656037);for _,v:=range b{h=(h^uint64(v))*1099511628211};b=binary.LittleEndian.AppendUint64(b,h);if e=os.WriteFile("/out/native/pack/poster-"+s.id+".rgba",b,0644);e!=nil{panic(e)}}}\n'
 (q/'panels.go').write_text(go)
 from PIL import Image,ImageDraw,ImageFont
 import io,struct
 idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),56,index=3)
 chars=sorted(set('海報龍虎延展經典封面關閉錯誤* '));b=bytearray(b'8SGLYP01'+struct.pack('<I',len(chars)))
 for ch in chars:
  im=Image.new('L',(64,64));d=ImageDraw.Draw(im);d.text((32,32),ch,font=font,fill=255,anchor='mm');b+=struct.pack('<I',ord(ch))+im.tobytes()
 b+=struct.pack('<Q',module(r,'rust-native-player.py').fnv(b));(q/'native/pack/poster-font.bin').write_bytes(b)
 assert sha(r/'docs/images/poster-cover-approved-r1.png')=='2d666efbb2b1fc714e92b82f078c3fd4139b7c690fce794b95c99c8b2725c55d'and sha(r/'docs/images/poster-wings-approved-r1.png')=='f14552801e98d4171befeb1220a9626c9e2e7a25efdad011896d2d3abfcba341'
 (q/'evidence/assets.json').write_text(json.dumps(dict(cover_sha256=sha(r/'docs/images/poster-cover-approved-r1.png'),wings_sha256=sha(r/'docs/images/poster-wings-approved-r1.png'),go_source_sha256=sha(q/'evidence/poster-go-source.txt'),font_source_sha256=h.FONT_SHA['noto'],font_index=3,chars=chars),ensure_ascii=False,indent=2)+'\n')
 print('prepared',q)
if __name__=='__main__':main()
