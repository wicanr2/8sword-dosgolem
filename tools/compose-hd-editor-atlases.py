#!/usr/bin/env python3
"""054: exact source-rectangle matching, then recompose IFF editor sheets."""
import argparse, collections, hashlib, json, pathlib, runpy
from PIL import Image, ImageChops, ImageOps

def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--archive',type=pathlib.Path,required=True);a=p.parse_args();root=a.project;arc=a.archive
 report=json.loads((arc/'all-graphics-hd-coverage-r1.json').read_text());rows=report['records'];sources=[r for r in rows if r['hd']];targets=[r for r in rows if not r['hd']]
 out=arc/'approved/registered-textures/all-graphics-hd-r1/editor';out.mkdir(parents=True,exist_ok=True)
 inv=json.loads((root/'docs/images/graphics-inventory-r1.json').read_text());meta={v['file']:v for v in inv['files']};decode=runpy.run_path(str(root/'tools/prepare-hd-intro.py'))['decode'];raws={}
 # IFF stores the EGA 85/170 DAC colors as 87/171. Match palette identities.
 lut=[min((0,85,170,255),key=lambda v:abs(v-n)) for n in range(256)]
 def rgb(im):return im.convert('RGB').point(lut*3)
 def matches(big,small):
  w,h=small.size;W,H=big.size
  if w>W or h>H:return []
  b=big.tobytes();s=small.tobytes();stride=W*3;row=w*3
  anchors=sorted(set([0,h//4,h//2,h*3//4,h-1]+sorted(range(h),key=lambda y:-len(set(s[y*row:(y+1)*row])))[:4]))
  candidates=set()
  if small.size==big.size:candidates.add((0,0))
  for anchor in anchors:
   needle=s[anchor*row:(anchor+1)*row]
   if len(set(needle))<2:continue
   at=0;hits=0
   while True:
    at=b.find(needle,at)
    if at<0:break
    yy,xbyte=divmod(at,stride);x=xbyte//3;y=yy-anchor;at+=1;hits+=1
    if xbyte%3 or x+w>W or y<0 or y+h>H:continue
    candidates.add((x,y))
    if hits>200:break
  found=[];limit=max(3,w*h//500)
  for x,y in sorted(candidates):
   errors=0
   for j in range(h):
    one=b[(y+j)*stride+x*3:(y+j)*stride+(x+w)*3];two=s[j*row:(j+1)*row]
    if one!=two:errors+=sum(one[k:k+3]!=two[k:k+3] for k in range(0,row,3))
    if errors>limit:break
   if errors<=limit:found.append((x,y,errors))
  return found if len(found)<=100 else []
 patterns=[]
 for r in sources:
  im=Image.open(root/r['native']).convert('RGBA');hd=Image.open(root/r['hd']['file']).convert('RGBA');vs=[]
  for bg in ((0,0,0),(255,255,255)):
   v=Image.new('RGBA',im.size,bg+(255,));v.alpha_composite(im);vs.append(('color',rgb(v),hd,None))
  if r['format']=='planar' and r.get('planes',0)>=5:
   name=r['source_file']
   if name not in raws:
    raw=(root/'workplace/intake-20261023/sources/game/8sword'/name).read_bytes();raws[name]=decode(raw) if meta[name].get('packed') else raw
   at=r['decoded_offset'];wb=r['width']//8;area=wb*r['height']
   for plane in range(4,r['planes']):
    bits=raws[name][at+4+plane*area:at+4+(plane+1)*area];v=Image.frombytes('1',im.size,bits).convert('RGB')
    if plane==5:
     ah=hd.getchannel('A');white=Image.new('RGBA',hd.size,'white');white.putalpha(ah);vhd=Image.new('RGBA',hd.size,'black');vhd.alpha_composite(white);kind='alpha-mask'
    else:
     gray=ImageOps.grayscale(hd);vhd=Image.merge('RGBA',(gray,gray,gray,hd.getchannel('A')));kind='monochrome-plane'
    vs.append((kind,v,vhd,None))
  seen=set()
  for kind,v,vhd,_ in vs:
   boxes=[(0,0,im.width,im.height)]
   b=im.getbbox()
   if b and b not in boxes:boxes.append(b)
   for box in boxes:
    v2=v.crop(box);signature=(v2.size,v2.tobytes())
    if signature in seen:continue
    seen.add(signature)
    if len(v2.getcolors(65536) or [])<=1:continue
    bh=(box[0]*3,box[1]*6,box[2]*3,box[3]*6)
    patterns.append((r,kind,v2,vhd.crop(bh),box))
 atlas_reports=[]
 for t in targets:
  native=Image.open(root/t['native']).convert('RGBA');big=rgb(native);colors=collections.Counter(big.getdata());bg=colors.most_common(1)[0][0];canvas=Image.new('RGBA',(1920,1200),bg+(255,));covered=Image.new('1',big.size);placements=[];rects=set()
  # Whole rectangles first. Larger parts win overlapping matches.
  found=[]
  for r,kind,v,hd,box in patterns:
   for x,y,errors in matches(big,v):found.append((v.width*v.height,r,kind,hd,box,x,y,v.size,errors))
  found.sort(key=lambda v:-v[0])
  for area,r,kind,hd,box,x,y,size,errors in found:
   rect=(x,y,x+size[0],y+size[1]);region=covered.crop(rect)
   if region.getextrema()==(1,1) or rect in rects:continue
   rects.add(rect);canvas.alpha_composite(hd,(x*3,y*6));covered.paste(1,rect)
   placements.append(dict(source_file=r['source_file'],record=r['record'],source_crop=list(box),target_rect=list(rect),kind=kind,hd=r['hd']['file'],different_native_pixels=errors,evidence_level='confirmed exact pixel rectangle' if errors==0 else 'strong inference; near-identical editor variant, art only'))
  # Native atlas blank regions are rectangles, not scaled pixel art.
  missing=0;total=0
  for (c,m) in zip(big.getdata(),covered.getdata()):
   if c!=bg:total+=1;missing+=not m
  filename=t['source_file'].lower().replace('.','-')+'-00.png';canvas.save(out/filename)
  detail=dict(source_file=t['source_file'],background=list(bg),matched_regions=len(placements),unmatched_nonbackground=missing,total_nonbackground=total,placements=placements,preview='artwork/approved/registered-textures/all-graphics-hd-r1/editor/'+filename)
  atlas_reports.append(detail);print(t['source_file'],len(placements),'unmatched',missing,'/',total)
 (arc/'editor-atlas-mapping-r1.json').write_text(json.dumps(dict(schema=1,atlases=atlas_reports),ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
