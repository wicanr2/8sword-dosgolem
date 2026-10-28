#!/usr/bin/env python3
"""054: assemble permanent HD library from verified Go caches and new art."""
import argparse, collections, hashlib, io, json, math, pathlib
from PIL import Image, ImageDraw, ImageFilter, ImageOps

def sha(b): return hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--archive',type=pathlib.Path,required=True);a=p.parse_args()
 root=a.project;archive=a.archive;prefix=pathlib.Path('artwork/approved/registered-textures/all-graphics-hd-r1')
 out=archive/'approved/registered-textures/all-graphics-hd-r1/primary';out.mkdir(parents=True,exist_ok=True)
 rows=json.loads((archive/'all-graphics-sources-r1.json').read_text())['records']; by={(r['source_file'],r['record']):r for r in rows}
 assets=root/'workplace/player/assets-painted-r64';master=archive/'approved/masters/all-graphics-hd-r1';done={}
 def native(r):return Image.open(root/r['native']).convert('RGBA')
 def save(r,im,method,inputs,integrated=False):
  name=r['source_file'].lower().replace('.','-')+f"-{r['record']:02}"+('-display-r2.png' if r['format']=='VGA8 palette+indices' else '.png');dest=out/name
  expected=((640 if r['format']=='VGA8 palette+indices' else r['width'])*3,r['height']*6)
  if im.size!=expected:im=im.resize(expected,Image.Resampling.LANCZOS)
  buf=io.BytesIO();im.save(buf,format='PNG');b=buf.getvalue()
  if dest.exists() and dest.read_bytes()!=b:raise ValueError(f'existing output differs: {dest}')
  dest.write_bytes(b);done[(r['source_file'],r['record'])]=dict(file=str(prefix/'primary'/name),sha256=sha(b),width=im.width,height=im.height,method=method,inputs=inputs,integrated=integrated)
 for ex in json.loads((archive/'approved/registered-textures/all-graphics-hd-r1/go-export/export.json').read_text()):
  key=(ex['source_file'],ex['record']);r=by[key];path=archive/'approved/registered-textures/all-graphics-hd-r1/go-export'/ex['file'];save(r,Image.open(path).convert('RGBA'),ex['method'],[str(prefix/'go-export'/ex['file'])],True)
 def use(file,record,image,method='hand-painted-normalization',split=None):
  r=by[(file,record)];path=master/image;im=Image.open(path).convert('RGBA')
  if split is not None:im=im.crop((im.width*split//2,0,im.width*(split+1)//2,im.height))
  if im.getextrema()[3][0]<255:
   im.putalpha(im.getchannel('A').point(lambda n:0 if n<8 else n));b=im.getbbox();im=im.crop(b)
   target=Image.new('RGBA',(r['width']*3,r['height']*6));b=native(r).getbbox();size=((b[2]-b[0])*3,(b[3]-b[1])*6);im=im.resize(size,Image.Resampling.LANCZOS);target.alpha_composite(im,(b[0]*3,b[1]*6));im=target
  save(r,im,method,['artwork/approved/masters/all-graphics-hd-r1/'+image])
 use('LIVE4.AY',0,'graveyard-background-r1.png');use('LIVE6.AY',0,'courtyard-background-r1.png')
 use('END3.AY',2,'ending-white-flash-r1.png');use('END4.AY',3,'ending-male-stand-r1.png');use('END4.AY',4,'ending-female-stand-r1.png')
 use('END4.AY',2,'ending-scroll-states-r2.png',split=0);use('END6.AY',0,'ending-scroll-states-r2.png',split=1)
 for record in (0,1):
  r=by[('END4.AY',record)];im=Image.new('RGBA',(528*4,r['height']*6*4),(0,0,0,255));d=ImageDraw.Draw(im)
  # Original ellipse is an opaque clearing strip, retaining green/red/yellow bands.
  for box,c in [((0,0,2111,167),(0,170,0,255)),((20,13,2090,153),(170,0,0,255)),((76,24,2035,145),(255,85,85,255)),((260,35,1850,130),(255,255,85,255)),((570,49,1540,111),(255,255,255,255))]:d.ellipse(box,fill=c)
  im=im.resize((528,r['height']*6),Image.Resampling.LANCZOS);save(r,im,'native-supersampled-ellipse-with-opaque-clearing',[r['native']])
 for file in ('END9.AY','END9H.AY'):
  r=by[(file,0)];assert len(set(native(r).getdata()))==1;save(r,Image.new('RGBA',(1920,120),(0,0,0,255)),'native-black-rectangle',[r['native']])
 for record in range(65,68):
  r=by[('PMAP.AY',record)];im=Image.new('RGBA',(24,18));d=ImageDraw.Draw(im);src=native(r)
  for y in range(3):
   assert len(set(src.crop((0,y,8,y+1)).getdata()))==1;d.rectangle((0,y*6,23,y*6+5),fill=src.getpixel((0,y)))
  save(r,im,'native-pure-color-swatch-rows',[r['native']])
 # Four rotations use native vector geometry. Fit phase to the original alpha/white lobe.
 base=Image.new('RGBA',(600,600));d=ImageDraw.Draw(base);d.ellipse((4,4,596,596),fill=(255,255,255,128),outline=(85,85,85,255),width=8);d.pieslice((8,8,592,592),90,270,fill='white');d.ellipse((154,300,446,592),fill='white');d.ellipse((154,8,446,300),fill=(255,255,255,128));d.ellipse((264,117,336,189),fill='white');d.ellipse((264,411,336,483),fill=(255,255,255,128))
 for record in range(4):
  r=by[('MAN27.EGG',record)];src=native(r);b=src.getbbox();sw,sh=b[2]-b[0],b[3]-b[1];orig=src.crop(b);target=Image.new('RGBA',(264,300))
  # Blur removes source dither before choosing the closest quarter-turn.
  old=orig.getchannel('A').filter(ImageFilter.GaussianBlur(1.1));oldp=list(old.getdata());best=None
  for angle in range(0,360,45):
   v=base.rotate(angle,resample=Image.Resampling.BICUBIC).resize((sw,sh),Image.Resampling.LANCZOS);vp=list(v.getchannel('A').filter(ImageFilter.GaussianBlur(1.1)).getdata());cost=sum((x-y)**2 for x,y in zip(oldp,vp))
   if best is None or cost<best[0]:best=(cost,angle)
  v=base.rotate(best[1],resample=Image.Resampling.BICUBIC).resize((sw*3,sh*6),Image.Resampling.LANCZOS);target.alpha_composite(v,(b[0]*3,b[1]*6));save(r,target,'native-taiji-vector-phase-'+str(best[1]),[r['native']])
 # Publisher original is at x64,y20 in the full 640x200 canvas.
 pub=Image.new('RGBA',(1920,1200),(0,0,0,255));pub.alpha_composite(Image.open(assets/'publisher-icon.png').convert('RGBA'));pub.alpha_composite(Image.open(assets/'publisher-noto.png').convert('RGBA'));save(by[('TIT1.AY',0)],pub.crop((192,120,1704,1080)),'publisher-smooth-icon-and-noto',['workplace/player/assets-painted-r64/publisher-icon.json','workplace/player/assets-painted-r64/publisher.json'],True)
 museum=json.loads((assets/'museum.json').read_text());beam=next(v for v in museum['assets'] if v['id']=='beam')
 for record in (10,11):
  im=Image.open(assets/beam['file']).convert('RGBA')
  if record==11:im=Image.merge('RGBA',(*([ImageOps.grayscale(im)]*3),im.getchannel('A')))
  save(by[('TIT4.AY',record)],im,'museum-beam'+('-grayscale' if record==11 else ''),['workplace/player/assets-painted-r64/'+beam['file']],True)
 for file in ('TIT6.AY','TIT6V.AY'):
  r=by[(file,0)];save(r,Image.open(assets/'story-prelude.png').convert('RGBA'),'approved-story-prelude-renderer-variant',['workplace/player/assets-painted-r64/story-prelude.json'],file=='TIT6.AY')
 for r in rows:
  key=(r['source_file'],r['record'])
  if key in done:continue
  name=r['source_file']
  colorname=name.replace('H.AY','.AY').replace('H.EG','.EG')
  if r.get('planes')==1 and (colorname,r['record'])in done:
   parent=done[(colorname,r['record'])];im=Image.open(root/parent['file']).convert('RGBA');g=ImageOps.grayscale(im);im=Image.merge('RGBA',(g,g,g,im.getchannel('A')));save(r,im,'hd-monochrome-renderer-variant',[parent['file']])
  elif name=='TIT6X.AY':
   parent=done[('TIT6.AY',0)];im=Image.open(root/parent['file']).convert('RGBA');g=ImageOps.grayscale(im);zero=Image.new('L',im.size);v=Image.merge('RGBA',(zero,zero,g,Image.new('L',im.size,255)));save(r,v,'hd-original-blue-story-variant',[parent['file']])
 recordlist=[]
 for r in rows:
  q=dict(r);q['hd']=done.get((r['source_file'],r['record']));q['status']='art-ready' if q['hd'] else 'pending-editor-atlas';recordlist.append(q)
 report=dict(schema=1,scope='all 333 decoded records; art readiness is independent of production integration',records=recordlist,counts=dict(collections.Counter(r['status'] for r in recordlist)))
 (archive/'all-graphics-hd-coverage-r1.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report['counts']))
if __name__=='__main__':main()
