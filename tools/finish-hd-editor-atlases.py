#!/usr/bin/env python3
"""054 art preparation only: editor variants, masks, geometric atlas controls."""
import argparse, collections, hashlib, itertools, json, pathlib, runpy
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps, ImageStat

def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--archive',type=pathlib.Path,required=True);a=p.parse_args();root=a.project;arc=a.archive
 coverage=json.loads((arc/'all-graphics-hd-coverage-r1.json').read_text());by={(v['source_file'],v['record']):v for v in coverage['records']};mapping=json.loads((arc/'editor-atlas-mapping-r1.json').read_text());maps={v['source_file']:v for v in mapping['atlases']};folder=arc/'approved/registered-textures/all-graphics-hd-r1/editor-final';folder.mkdir(parents=True,exist_ok=True);unresolved=[]
 lut=[min((0,85,170,255),key=lambda v:abs(v-n)) for n in range(256)];decode=runpy.run_path(str(root/'tools/prepare-hd-intro.py'))['decode'];inv={v['file']:v for v in json.loads((root/'docs/images/graphics-inventory-r1.json').read_text())['files']};raws={};candidates=[]
 def gethd(file,record):return Image.open(root/by[(file,record)]['hd']['file']).convert('RGBA')
 def original(file,record):return Image.open(root/by[(file,record)]['native']).convert('RGBA')
 for (name,record),r in by.items():
  if r['width']!=64 or r['height']!=25 or not r['hd']:continue
  im=original(name,record);hd=gethd(name,record);v=Image.new('RGBA',im.size,'black');v.alpha_composite(im);candidates.append((name,record,'color',v.convert('RGB'),hd))
  if r.get('planes',0)>=5:
   if name not in raws:
    b=(root/'workplace/intake-20261023/sources/game/8sword'/name).read_bytes();raws[name]=decode(b) if inv[name].get('packed') else b
   area=8*25;at=r['decoded_offset']
   for plane in range(4,r['planes']):
    im=Image.frombytes('1',(64,25),raws[name][at+4+plane*area:at+4+(plane+1)*area]).convert('RGB')
    if plane==5:
     v=Image.new('RGBA',hd.size,'white');v.putalpha(hd.getchannel('A'));h=Image.new('RGBA',hd.size,'black');h.alpha_composite(v);kind='alpha-mask'
    else:
     g=ImageOps.grayscale(hd);h=Image.merge('RGBA',(g,g,g,hd.getchannel('A')));kind='monochrome-plane'
    candidates.append((name,record,kind,im,h))
 # Pixelwise matching remains in the first pass. Legacy variants use low-frequency
 # structure because independently dithered grass otherwise overwhelms buildings.
 def feature(im):return im.filter(ImageFilter.GaussianBlur(1.5)).resize((16,12),Image.Resampling.LANCZOS)
 candidates += [(n,i,k+'-mirror',ImageOps.mirror(v),ImageOps.mirror(h))for n,i,k,v,h in list(candidates)]
 def components(im):
  pix=list(im.convert('RGB').getdata());W,H=im.size;seen=set();boxes=[]
  for at,c in enumerate(pix):
   if c==(255,255,255)or at in seen:continue
   seen.add(at);todo=[at];xs=[];ys=[]
   while todo:
    v=todo.pop();x=v%W;y=v//W;xs.append(x);ys.append(y)
    for nx,ny in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
     n=ny*W+nx
     if 0<=nx<W and 0<=ny<H and n not in seen and pix[n]!=(255,255,255):seen.add(n);todo.append(n)
   if len(xs)>30:boxes.append((min(xs),min(ys),max(xs)+1,max(ys)+1))
  return boxes
 for name,entry in maps.items():
  r=by[(name,0)];src=original(name,0).convert('RGB').point(lut*3);canvas=Image.open(root/entry['preview']).convert('RGBA');extra=[]
  # Recreate rectangular empty cells using native shapes; never copy the source pixels.
  d=ImageDraw.Draw(canvas)
  for y in range(200):
   row=[src.getpixel((x,y)) for x in range(640)]
   for color,g in itertools.groupby(enumerate(row),lambda v:v[1]):
    part=list(g)
    if color in [(0,0,0),(255,255,255)] and len(part)>=16:
     x0,x1=part[0][0],part[-1][0]+1
     # Do not cover already reconstructed HD regions.
     if not any(y>=q['target_rect'][1] and y<q['target_rect'][3] and x0<q['target_rect'][2] and x1>q['target_rect'][0] for q in entry['placements']):d.rectangle((x0*3,y*6,x1*3-1,y*6+5),fill=color+(255,))
  def put(im,rect,method,source,confidence='art preparation; not a runtime contract'):
   x0,y0,x1,y1=rect;im=im.resize(((x1-x0)*3,(y1-y0)*6),Image.Resampling.LANCZOS)
   if method in ('hand-painted-extra-editor-pose','visually-identified-editor-character-family','male-stand-editor-variant','female-stand-editor-variant','heroine-dissolve-editor-state','male-monochrome-editor-state','pair-editor-color-variant','existing-hd-energy-editor-variant','book-editor-rotation'):ImageDraw.Draw(canvas).rectangle((x0*3,y0*6,x1*3-1,y1*6-1),fill='black')
   canvas.alpha_composite(im,(x0*3,y0*6));extra.append(dict(target_rect=list(rect),method=method,source=source,evidence_level=confidence))
  def cell(x,y):
   target=src.crop((x,y,x+64,y+25));colors=target.getcolors(1601)
   if colors and len(colors)==1:
    blank=Image.new('RGBA',(192,150),colors[0][1]+(255,));put(blank,(x,y,x+64,y+25),'native-empty-cell',[]);return blank,[]
   colored=any(c[0]!=c[1] or c[1]!=c[2] for _,c in colors or [])
   ranks=[]
   for file,index,kind,im,hd in candidates:
    if colored!=kind.startswith('color'):continue
    cost=sum(ImageStat.Stat(ImageChops.difference(feature(target),feature(im))).mean);ranks.append((cost,file,index,kind,hd))
   ranks.sort(key=lambda v:v[:4]);cost,file,index,kind,hd=ranks[0]
   if cost>100:unresolved.append(dict(file=name,x=x,y=y,cost=cost,nearest_file=file,nearest_record=index,kind=kind))
   bg=Image.new('RGBA',hd.size,'black');bg.alpha_composite(hd);inputs=[by[(file,index)]['hd']['file']];put(bg,(x,y,x+64,y+25),'editor-variant-'+kind,inputs,f'strong inference; visual variant blurred16x12 RGB sum {cost:.6f}; second {ranks[1][0]:.6f}; no game semantics');return hd,inputs
  if name in ('X03.AY','X04H.AY','X07.AY','X09H.AY'):
   for x0,y0,x1,y1 in components(src):
    if name=='X03.AY' and (x0,y0)==(10,41):continue
    if name in ('X07.AY','X09H.AY') and (x0,y0)in [(111,14),(243,14)]:continue
    if name in ('X07.AY','X09H.AY') and (x0,y0)in [(10,40),(10,66),(10,92),(75,92),(140,92),(10,118),(75,118),(335,118),(400,118),(465,118)]:continue
    if 63<=x1-x0<=65 and y1-y0==25:cell(x0+(1 if x1-x0==65 else 0),y0)
   if name=='X04H.AY':
    for y in range(0,175,25):
     hd,inputs=cell(0,y);g=ImageOps.grayscale(hd);put(Image.merge('RGBA',(g,g,g,hd.getchannel('A'))),(64,y,128,y+25),'paired-terrain-editor-monochrome-variant',inputs)
  if name in ('X03.AY','X09.AY'):
   hd=gethd('ENEMY.AY',0);v=Image.new('RGBA',(192,150),'white');v.alpha_composite(hd.resize((96,150),Image.Resampling.LANCZOS));v.alpha_composite(ImageOps.mirror(hd).resize((96,150),Image.Resampling.LANCZOS),(96,0));put(v,(10,41,74,66),'legacy-editor-paired-red-figures',[by[('ENEMY.AY',0)]['hd']['file']],'strong inference; visual family reuse, no runtime identity assertion')
  if name in ('X07.AY','X09H.AY','X10.AY'):
   art=Image.open(arc/'approved/masters/all-graphics-hd-r1/editor-two-buildings-r1.png').convert('RGBA')
   for i,x in enumerate([111,243]):
    v=art.crop((art.width*i//2,0,art.width*(i+1)//2,art.height))
    if name=='X10.AY':g=ImageOps.grayscale(v);v=Image.merge('RGBA',(g,g,g,v.getchannel('A')))
    put(v,(x,14,x+64,39),'hand-painted-editor-architecture',['artwork/approved/masters/all-graphics-hd-r1/editor-two-buildings-r1.png'])
  if name in ('X07.AY','X09H.AY'):
   art=Image.open(arc/'approved/masters/all-graphics-hd-r1/editor-two-buildings-r1.png').convert('RGBA')
   for x,y,i in [(10,40,0),(10,118,1)]:put(art.crop((art.width*i//2,0,art.width*(i+1)//2,art.height)),(x,y,x+64,y+25),'hand-painted-architecture-editor-background-variant',['artwork/approved/masters/all-graphics-hd-r1/editor-two-buildings-r1.png'])
   for x,y,index in [(10,66,53),(10,92,55),(75,92,57),(140,92,58),(75,118,52)]:put(gethd('PMAP.AY',index),(x,y,x+64,y+25),'visually-identified-editor-building-family',[by[('PMAP.AY',index)]['hd']['file']],'strong inference; same visible structure, alternate editor backdrop; art only')
   art=Image.open(arc/'approved/masters/all-graphics-hd-r1/editor-front-warrior-poses-r1.png').convert('RGBA')
   for i,x in enumerate([335,400,465]):
    v=art.crop((art.width*i//3,0,art.width*(i+1)//3,art.height));v.putalpha(v.getchannel('A').point(lambda n:0 if n<8 else n));v=v.crop(v.getbbox());put(v,(x,118,x+64,143),'hand-painted-frontal-editor-pose',['artwork/approved/masters/all-graphics-hd-r1/editor-front-warrior-poses-r1.png'])
  if name=='X02.AY':
   positions=[(30,5),(103,5),(174,3),(247,3),(30,33),(103,33),(173,33),(246,33),(30,61),(103,61),(174,63),(247,63),(28,92),(102,92),(178,92),(251,91),(28,121),(102,122),(177,122),(251,122),(28,153),(101,153),(174,153),(248,153)]
   identities=[0,0,None,None,1,1,None,None,2,2,None,None,3,4,5,None,6,7,8,9,10,11,12,13]
   six=Image.open(arc/'approved/masters/all-graphics-hd-r1/editor-six-poses-r2.png').convert('RGBA')
   for ordinal,(x,y) in enumerate(positions):
    identity=identities[ordinal]
    if identity is None:hd,inputs=cell(x,y)
    elif ordinal<12:
     row=ordinal//4;col=ordinal%4;ys=[0,424,790,six.height];hd=six.crop((six.width*col//2,ys[row],six.width*(col+1)//2,ys[row+1]));hd.putalpha(hd.getchannel('A').point(lambda n:0 if n<8 else n));hd=hd.crop(hd.getbbox());target=src.crop((x,y,x+64,y+25));mask=ImageChops.difference(target,Image.new('RGB',target.size,'black')).convert('L');b=mask.getbbox();v=Image.new('RGBA',(192,150));v.alpha_composite(hd.resize(((b[2]-b[0])*3,(b[3]-b[1])*6),Image.Resampling.LANCZOS),(b[0]*3,b[1]*6));hd=v;inputs=['artwork/approved/masters/all-graphics-hd-r1/editor-six-poses-r2.png'];put(hd,(x,y,x+64,y+25),'hand-painted-extra-editor-pose',inputs)
    else:
     hd=gethd('ENEMY.AY',identity);inputs=[by[('ENEMY.AY',identity)]['hd']['file']];put(hd,(x,y,x+64,y+25),'visually-identified-editor-character-family',inputs,'strong inference from decoded silhouette and color; legacy alternate pose not runtime ABI')
    mask=Image.new('RGBA',hd.size,'white');mask.putalpha(hd.getchannel('A'));v=Image.new('RGBA',hd.size,'black');v.alpha_composite(mask)
    if not inputs:v=Image.new('RGBA',hd.size,'black')
    put(v,(x+306,y+4,x+370,y+29),'paired-editor-mask-from-hd-alpha',inputs)
  if name=='X09.AY':
   # The first three rows are old rock variants. Correspondence follows the
   # adjacent color editor row order, with the last two rows anchored by eleven
   # exact monochrome source matches. Do not invent runtime source identities.
   groups=[(13,[79,149,222,296,365,435,506],[0,16,29,27,17,26,28]),(41,[89,159,232,301,371,442,513],[14,22,23,24,25,18,19]),(68,[166,238,309,382,458,533],[20,21,15,33,34,35]),(95,[85,166,238,310,382,453,523],[31,36,39,40,37,38,32]),(122,[167,237,306,375,452],[44,42,41,43,30])]
   for y,xs,indices in groups:
    for x,index in zip(xs,indices):
     hd=gethd('PMAP.AY',index);g=ImageOps.grayscale(hd);put(Image.merge('RGBA',(g,g,g,hd.getchannel('A'))),(x,y,x+64,y+25),'monochrome-editor-row-order-variant',[by[('PMAP.AY',index)]['hd']['file']],'strong inference from adjacent color atlas row order; exact source assignment only where initial pixel receipt confirms')
  if name=='X10.AY':
   parent=Image.open(folder/'x07-ay-00.png').convert('RGBA');g=ImageOps.grayscale(parent);canvas=Image.merge('RGBA',(g,g,g,parent.getchannel('A')));extra=[dict(target_rect=[0,0,640,200],method='monochrome-color-editor-counterpart',source=['artwork/'+str((folder/'x07-ay-00.png').relative_to(arc))],evidence_level='strong inference from shared cell layout and six exact MAN source anchors; art only')]
  if name=='X06H.AY':
   for record,x,y in [(1,442,5),(2,437,56),(3,437,103),(4,440,135)]:put(gethd('END6.AY',record),(x,y,x+136,y+50),'pair-editor-color-variant',[by[('END6.AY',record)]['hd']['file']])
  if name=='X01.AY':
   # Standalone portraits, dissolving heroine, rotating book and growing light domes.
   male=gethd('END4.AY',3);female=gethd('END4.AY',4)
   put(male,(1,147,81,197),'male-stand-editor-variant',[by[('END4.AY',3)]['hd']['file']]);put(female,(94,147,174,197),'female-stand-editor-variant',[by[('END4.AY',4)]['hd']['file']]);put(male,(520,49,600,99),'male-stand-editor-variant',[by[('END4.AY',3)]['hd']['file']])
   for i,rect in enumerate([(186,50,258,95),(261,50,333,95),(334,50,406,95),(407,50,467,90),(468,50,515,82)]):
    v=female.copy();v.putalpha(v.getchannel('A').point(lambda n:n*(5-i)//5));put(v,rect,'heroine-dissolve-editor-state',[by[('END4.AY',4)]['hd']['file']])
   v=male.copy();g=ImageOps.grayscale(v);v=Image.merge('RGBA',(g,g,g,v.getchannel('A').point(lambda n:n//2)));put(v,(125,49,163,96),'male-monochrome-editor-state',[by[('END4.AY',3)]['hd']['file']])
   # Original smaller dialog window is a geometric interface element.
   v=Image.new('RGBA',(288,264),(255,255,255,255));dv=ImageDraw.Draw(v)
   for inset,c in [(0,'#282070'),(3,'#a2a6ff'),(8,'#5d4fc0'),(13,'#7f829a')]:dv.rectangle((inset,inset,287-inset,263-inset),outline=c,width=3)
   put(v,(6,50,102,94),'native-purple-dialog-frame',[])
   for x,y,w,h in [(190,157,35,12),(238,152,46,18),(299,150,56,22),(375,147,63,29),(491,145,136,51)]:
    v=Image.new('RGBA',(w*12,h*24));dv=ImageDraw.Draw(v);dv.ellipse((0,0,w*12-1,h*48-1),fill=(255,255,255,140));put(v,(x,y,x+w,y+h),'native-translucent-half-ellipse',[])
   for x,y,angle in [(466,100,35),(512,100,75),(558,100,120)]:
    v=gethd('MAN.AY',12).rotate(angle,Image.Resampling.BICUBIC,expand=True);put(v,(x,y,x+40,y+21),'book-editor-rotation',[by[('MAN.AY',12)]['hd']['file']])
   energy=Image.open(arc/'approved/masters/all-graphics-hd-r1/editor-blue-energy-bursts-r1.png').convert('RGBA')
   for i,rect in enumerate([(200,100,272,145),(278,100,398,147)]):
    x0,y0,x1,y1=rect;ImageDraw.Draw(canvas).rectangle((x0*3,y0*6,x1*3-1,y1*6-1),fill='black');b=ImageChops.difference(src.crop(rect),Image.new('RGB',(x1-x0,y1-y0),'black')).getbbox();v=energy.crop((energy.width*i//2,0,energy.width*(i+1)//2,energy.height));v.putalpha(v.getchannel('A').point(lambda n:0 if n<8 else n));v=v.crop(v.getbbox());put(v,(x0+b[0],y0+b[1],x0+b[2],y0+b[3]),'hand-painted-original-cyan-blue-energy',['artwork/approved/masters/all-graphics-hd-r1/editor-blue-energy-bursts-r1.png'])
  if name=='X02H.AY':
   canvas=Image.new('RGBA',(1920,1200),'white');put(Image.open(arc/'approved/masters/all-graphics-hd-r1/editor-cloud-sky-r1.png').convert('RGBA'),(0,0,640,118),'hand-painted-cloud-sky',['artwork/approved/masters/all-graphics-hd-r1/editor-cloud-sky-r1.png'])
  if name=='X08.AY':
   canvas=Image.new('RGBA',(1920,1200),'white');put(Image.open(arc/'approved/masters/all-graphics-hd-r1/editor-ocean-wave-r1.png').convert('RGBA'),(62,74,510,174),'hand-painted-ocean-wave',['artwork/approved/masters/all-graphics-hd-r1/editor-ocean-wave-r1.png'])
  dest=folder/(name.lower().replace('.','-')+'-00.png');canvas.save(dest);data=dest.read_bytes();r['hd']=dict(file='artwork/'+str(dest.relative_to(arc)),sha256=hashlib.sha256(data).hexdigest(),width=1920,height=1200,method='editor-hd-art-recomposition',integrated=False,inputs=[q['hd']for q in entry['placements']]+[s for q in extra for s in q['source']],alpha_contract='opaque visual HD atlas; original IFF alpha preserved in native reference, not a runtime mask contract')
  r['status']='art-ready';entry['additional_art_operations']=extra;entry['final']=r['hd']['file'];print(name,len(extra))
 if unresolved:raise ValueError('Unresolved editor variants; coverage not promoted: '+json.dumps(unresolved))
 # Identical editor files share the same image after all variant operations.
 for original_name,copy_name in [('X04.AY','X08H.AY'),('X07.AY','X09H.AY')]:
  one=by[(original_name,0)]['hd'];two=by[(copy_name,0)]['hd'];b=(root/one['file']).read_bytes();(arc/pathlib.Path(two['file']).relative_to('artwork')).write_bytes(b);two['sha256']=hashlib.sha256(b).hexdigest();two['inputs']=[one['file']]
 coverage['counts']=dict(collections.Counter(v['status']for v in coverage['records']));(arc/'all-graphics-hd-coverage-r1.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n');(arc/'editor-atlas-mapping-final-r1.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n');print(coverage['counts'])
if __name__=='__main__':main()
