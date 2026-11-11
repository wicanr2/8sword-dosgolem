#!/usr/bin/env python3
"""Rust 雙素材組：準備、核對、封存與還原。Docker only。"""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-display-r1';REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
def module(r,n):
 s=importlib.util.spec_from_file_location(n,r/'tools'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','audit','images','freeze','archive','verify','restore'])
 for n in ['project','work','out','archive']:ap.add_argument('--'+n,type=Path)
 a=ap.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=json.loads((a.archive/(BATCH+'.json')).read_text())
  for f in d['files']:
   o=d['objects'][f['sha256']];p=a.archive/BATCH/o['file'];assert sha(p)==o['stored_sha256'];b=gzip.decompress(p.read_bytes());assert len(b)==f['bytes']and hashlib.sha256(b).hexdigest()==f['sha256']
  a.out.write_text(json.dumps(dict(status='passed-rust-display-detached',files=len(d['files']),objects=len(d['objects'])))+'\n');return
 r=a.project;q=a.work or r/REL;h=module(r,'prepare-owned-army-ui.py')
 if a.action=='archive':m=module(r,'rust-world-exits.py');m.BATCH=BATCH;m.REL=REL;m.main();return
 if a.action=='restore':
  for f in json.loads((r/'preserved'/(BATCH+'.json')).read_text())['files']:
   rel=Path(f['path']).relative_to(REL)
   if str(rel)=='native/8sword-remake'or str(rel).startswith('native/pack/'):
    p=q/rel;p.parent.mkdir(parents=True,exist_ok=True);b=h.stored(r,BATCH,f['path'])
    if p.exists()and p.read_bytes()!=b:raise ValueError('還原目的地已有不同資料')
    p.write_bytes(b);p.chmod(f['mode'])
  return
 if a.action=='freeze':
  shutil.copytree(r/'internal/remake-rust',q/'rust-source');(q/'tools').mkdir()
  for n in ['rust-display.py','rust-display-gui.py','rust-display-cli.py','rust-display-smoke.py','rust-native-player.sh','catalog-all-graphics.py','prepare-hd-intro.py']:shutil.copy2(r/'tools'/n,q/'tools'/n)
  return
 if a.action in ['audit','images']:
  from PIL import Image,ImageDraw,ImageFont
  import io
  gui=json.loads((q/'native/gui/receipt.json').read_text());assert gui['status']=='passed-rust-display-gui'and len(gui['runs'])==7 and gui['binary_sha256']==sha(q/'native/8sword-remake')
  if a.action=='images':
   audit=json.loads((r/'preserved/rust-display-audit-r1.json').read_text());assert audit['status']=='passed-rust-display-audit'and audit['gui']['binary_sha256']==gui['binary_sha256'];captures=audit['captures']
   idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),28,index=3);canvas=Image.new('RGB',(1920,1440),(8,36,23));draw=ImageDraw.Draw(canvas);chosen=[]
   for row,(run,left,right,label)in enumerate([('world','world-original','world-hd','地圖與主角'),('world','camp-original','camp-hd','正常進營地與募兵圖示'),('battle','battle-original','battle-hd','同狀態原式戰場')]):
    for col,mark in enumerate([left,right]):
     c=next(c for c in captures if c['run']==run and c['label']==mark);source=q/'native/gui'/run/f'shell-frame-{c["number"]:03}.ppm';assert sha(source)==c['full_sha256'];im=Image.open(source);x=col*960;y=row*480;draw.text((x+8,y+8),label+('：原圖'if col==0 else'：HD'),font=font,fill=(239,216,155));canvas.paste(im.resize((960,430),Image.Resampling.LANCZOS),(x,y+50));chosen.append(c)
   canvas.save(a.out);a.out.with_suffix('.json').write_text(json.dumps(dict(image_sha256=sha(a.out),binary_sha256=gui['binary_sha256'],sources=chosen,scope='Same state/font per pair; original source pictures with shared native UI, not DOS whole-frame restoration. Battle troops explicit; world/camp use true v16 normal inputs.'),ensure_ascii=False,indent=2)+'\n');return
  captures=[]
  for run in gui['runs']:
   assert run['exit']==0
   labels={c['number']:c['label']for c in run['captures']};folder=q/'native/gui'/run['name']
   for meta in sorted(folder.glob('capture-*.tsv')):
    n=int(meta.stem.split('-')[1]);cap=dict(l.split('\t',1)for l in meta.read_text().splitlines());p=folder/f'frame-{n:03}.ppm';full=folder/f'shell-frame-{n:03}.ppm';assert p.read_bytes()==p.with_name(f'readback-{n:03}.ppm').read_bytes();assert full.read_bytes()==full.with_name(f'shell-readback-{n:03}.ppm').read_bytes();im=Image.open(p).convert('RGBA');assert cap['frame_hash']==format(module(r,'rust-native-player.py').fnv(im.tobytes()),'016x');assert Image.open(full).convert('RGB').crop((512,0,2432,1320)).tobytes()==im.convert('RGB').tobytes();captures.append(dict(run=run['name'],label=labels.get(n,'automatic'),number=n,captured=cap,central_sha256=sha(p),full_sha256=sha(full)))
  assert len(captures)==35 and sum(len(v['captures'])for v in gui['runs'])==29
  assert '199 passed; 0 failed'in(q/'native/tests.log').read_text();binding=[l.split('\t')for l in(q/'native/display-images.tsv').read_text().splitlines()if not l.startswith('#')];assert len(binding)==127 and all(v[1]==v[3]for v in binding)
  original=json.loads((q/'evidence/original-assets.json').read_text());assert original['count']==127
  for v in original['rows']:assert sha(q/'native/pack/original'/v['name'])==v['sha256']
  previous=json.loads((r/'preserved/rust-rules-r1.json').read_text());old={Path(f['path']).name:f['sha256']for f in previous['files']if'/native/pack/'in f['path']};assert len(old)==159 and all(sha(q/'native/pack'/n)==v for n,v in old.items()if n!='poster-font.bin')
  def glyphs(b):return{chr(struct.unpack_from('<I',b,12+i*4100)[0]):b[16+i*4100:12+(i+1)*4100]for i in range(struct.unpack_from('<I',b,8)[0])}
  before=glyphs(h.stored(r,'rust-rules-r1','native/pack/poster-font.bin'));after=glyphs((q/'native/pack/poster-font.bin').read_bytes());assert len(before)==34 and len(after)==37 and all(after[ch]==v for ch,v in before.items())
  oldcap=next(v for v in json.loads((r/'preserved/rust-rules-audit-r1.json').read_text())['captures']if v['run']=='journey'and v['label']=='world-native');newcap=next(c for c in captures if c['run']=='world'and c['label']=='world-hd');oldbytes=h.stored(r,'rust-rules-r1',f"native/gui/journey/frame-{oldcap['number']:03}.ppm");assert oldcap['captured']['state_hash']==newcap['captured']['state_hash']and hashlib.sha256(oldbytes).hexdigest()==newcap['central_sha256']
  pairs=[]
  for run,first,last in [('world','world-original','world-hd'),('world','character-original','character-hd'),('world','army-original','army-hd'),('world','camp-original','camp-hd'),('battle','battle-original','battle-hd'),('openkb','battle-original','battle-hd')]:
   x=next(c for c in captures if c['run']==run and c['label']==first);y=next(c for c in captures if c['run']==run and c['label']==last);key='checkpoint_hash'if run in ['battle','openkb']else'state_hash';assert x['captured'][key]==y['captured'][key];assert x['central_sha256']!=y['central_sha256'];pairs.append(dict(run=run,left=first,right=last,state_hash=x['captured'][key]))
  cli=json.loads((q/'native/cli-check/receipt.json').read_text());assert cli['status']=='passed-rust-display-cli'and len(cli['cases'])==7;smoke=json.loads((q/'native/default-gui/receipt.json').read_text());assert smoke['status']=='passed-rust-display-default-scale'and len(smoke['runs'])==2
  assert len(list((q/'native/pack').rglob('*')))-len([p for p in(q/'native/pack').rglob('*')if p.is_dir()])==287
  crate={str(p.relative_to(r/'internal/remake-rust')):sha(p)for p in(r/'internal/remake-rust').rglob('*')if p.is_file()};assert all(sha(q/'rust-source'/n)==v for n,v in crate.items());baseline={k:len(v)for k,v in h.dependencies(r).items()};assert list(baseline.values())==[197,7,923,535]
  a.out.write_text(json.dumps(dict(status='passed-rust-display-audit',tests=199,original_images=127,swap_round_trips_per_image=9,manual_captures=29,all_sdl_captures=35,gui=gui,captures=captures,same_state_pairs=pairs,previous_hd_world_equal=True,cli=cli,default_scale=smoke,unchanged_media=158,old_poster_glyphs=34,new_poster_glyphs=3,runtime_files=288,crate=crate,baseline=baseline,execution=json.loads((q/'execution.json').read_text()),limits=['Original source pictures at existing geometry with shared Rust UI/fonts, not complete DOS frame or animation parity.','OpenKB frame0 is an imported reference; not a DOS-native troop.','Controlled battle and archived ending checkpoint; normal v16 camp and purchase are natural inputs.','Independent display preference; v16/8SBCHK01/rules remain unchanged; old ending hd field honored only absent explicit new choice.','HD OGG remains; dummy audio is not new human listening; no Release/mobile/platform claim.']),ensure_ascii=False,indent=2)+'\n');return
 assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir();(q/'native/pack/original').mkdir(parents=True);(q/'evidence').mkdir()
 old=json.loads((r/'preserved/rust-rules-r1.json').read_text())
 for f in old['files']:
  if '/native/pack/'in f['path']:(q/'native/pack'/Path(f['path']).name).write_bytes(h.stored(r,'rust-rules-r1',f['path']))
 (q/'native/legacy-v16.chk').write_bytes(h.stored(r,'rust-rules-r1','native/legacy-v16.chk'))
 from PIL import Image,ImageDraw,ImageFont
 import io
 planar=module(r,'catalog-all-graphics.py');huff=module(r,'prepare-hd-intro.py');cat=json.loads((r/'docs/images/graphics-inventory-r1.json').read_text());by={(v['source_file'],v['record']):v for v in cat['records']};files={v['file']:v for v in cat['files']};source=r/'workplace/intake-20261023/sources/game/8sword';decoded={};rows=[]
 def original(name,index=0):
  if name not in decoded:
   raw=(source/name).read_bytes();assert hashlib.sha256(raw).hexdigest()==files[name]['sha256'];decoded[name]=huff.decode(raw)if files[name]['packed']else raw
  row=by[name,index];raw=decoded[name][row['decoded_offset']:row['decoded_offset']+row['bytes']];assert hashlib.sha256(raw).hexdigest()==row['record_sha256'];im=planar.planar(raw,(0,row['width']//8,row['height'],row['planes']));assert hashlib.sha256(im.tobytes()).hexdigest()==row['decoded_rgba_sha256'];return im,row
 def save(name,im,size,evidence):
  im=im.resize(size,Image.Resampling.NEAREST);raw=b'8SRGBA01'+struct.pack('<II',*size)+im.convert('RGBA').tobytes();p=q/'native/pack/original'/name;p.write_bytes(raw+struct.pack('<Q',module(r,'rust-native-player.py').fnv(raw)));rows.append(dict(name=name,width=size[0],height=size[1],sha256=sha(p),source=evidence))
 for name,src,size in [('background.rgba','GRO01.EG',(1920,1200)),('world-frame.rgba','CUBE.AY',(1920,1200)),('recruit-building.rgba','LIVE2.AY',(1344,600)),('magic-building.rgba','LIVE1.AY',(1344,600))]:
  im,row=original(src);save(name,im,size,row)
 for i in range(65):
  im,row=original('PMAP.AY',i);save(f'map-tile-{i:02}.rgba',im,(192,150),row)
 for i in range(12):
  im,row=original('MAN.AY',i);save(f'map-hero-{i:02}.rgba',im,(192,150),row)
 for i in range(1,26):
  im,row=original(f'MAN{i:02}.EGG');save(f'unit_native_{i:02}.rgba',im,(264,300),row)
 for i in range(4):
  im,row=original('PON.EGG',i);save(f'spell-impact-{i}.rgba',im,(264,300),row)
 im,row=original('MAN.AY',20);save('hero-portrait.rgba',im,(240,240),row)
 for i in range(8):
  im,row=original('MAN.AY',12+i);save('magic-book.rgba'if i==0 else f'item-{i}.rgba',im,(96,96),row)
 artwork=json.loads((r/'artwork/manifest.json').read_text())
 for name in ['arcr','pike','wolf','skel','troll','drui','vamp','drag']:
  base='trol'if name=='troll'else name;path='approved/references/openkb-hd-r1/'+base+'.png';entry=next(v for v in artwork['files']if v['path']==path);p=r/'artwork'/path;assert sha(p)==entry['sha256'];im=Image.open(p);assert im.mode=='P'and im.size==(192,34)
  tile=im.crop((0,0,32,34));rgba=tile.convert('RGBA');rgba.putalpha(Image.frombytes('L',tile.size,bytes(0 if v==255 else 255 for v in tile.tobytes())));box=rgba.getbbox();assert box;cut=rgba.crop(box);w,h0=cut.size;scale=min(252/w,288/h0);size=(int(w*scale),int(h0*scale));out=Image.new('RGBA',(264,300));out.paste(cut.resize(size,Image.Resampling.NEAREST),((264-size[0])//2,300-size[1]));save('unit_openkb_'+name+'.rgba',out,(264,300),dict(file=path,sha256=entry['sha256'],frame=0,transparent_palette_index=255,role='OpenKB imported original pixels, not DOS-native troop art'))
 assert len(rows)==127
 (q/'native/pack/original/images.tsv').write_text('8SORIG01\n'+''.join(f"{v['name']}\t{v['width']}\t{v['height']}\t{v['sha256']}\n"for v in sorted(rows,key=lambda v:v['name'])))
 (q/'evidence/original-assets.json').write_text(json.dumps(dict(status='passed-original-pixel-projection',count=len(rows),rows=rows,inventory_sha256=sha(r/'docs/images/graphics-inventory-r1.json'),decoder_sha256=sha(r/'tools/catalog-all-graphics.py'),huffman_sha256=sha(r/'tools/prepare-hd-intro.py'),sampling='nearest; raw palette and alpha; shared Rust UI/fonts are not DOS full-frame parity'),ensure_ascii=False,indent=2)+'\n')
 p=q/'native/pack/poster-font.bin';raw=p.read_bytes();old={chr(struct.unpack_from('<I',raw,12+i*4100)[0]):raw[16+i*4100:12+(i+1)*4100]for i in range(struct.unpack_from('<I',raw,8)[0])};glyphs=dict(old);idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),56,index=3)
 for ch in '畫面 HD原版':
  if ch not in glyphs:
   im=Image.new('L',(64,64));ImageDraw.Draw(im).text((32,32),ch,font=font,fill=255,anchor='mm');glyphs[ch]=im.tobytes()
 raw=bytearray(b'8SGLYP01'+struct.pack('<I',len(glyphs)))
 for ch,ink in sorted(glyphs.items()):raw+=struct.pack('<I',ord(ch))+ink
 raw+=struct.pack('<Q',module(r,'rust-native-player.py').fnv(raw));p.write_bytes(raw);assert all(glyphs[ch]==v for ch,v in old.items());print('prepared127 original images; poster glyphs',len(old),len(glyphs))
if __name__=='__main__':main()
