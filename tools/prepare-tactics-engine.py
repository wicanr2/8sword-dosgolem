#!/usr/bin/env python3
"""Approved tactics: append two toolbar glyphs or freeze existing build inputs."""
import argparse,gzip,hashlib,io,json,os,pathlib,shutil
from PIL import Image,ImageDraw,ImageFont,__version__
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['assets','freeze'])
 for n in ['project','player','out']:p.add_argument('--'+n,type=pathlib.Path,required=True)
 a=p.parse_args();r=a.project;old=read(r/'preserved/ai-formation-audit-r1.json');assert os.getuid()==a.player.stat().st_uid==1000 and not a.out.exists()
 for n,h in old['programs'].items():assert sha(a.player/n)==h
 for n,h in old['asset_hashes'].items():assert sha(a.player/'assets-painted-r67'/n)==h
 a.out.mkdir()
 if a.action=='assets':
  assert __version__=='11.3.0';base=a.player/'assets-painted-r67'
  for n in old['asset_hashes']:shutil.copyfile(base/n,a.out/n)
  m=read(base/'poster-toolbar.json');assert m['schema']==3 and len(m['glyphs'])==137
  catalog=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));h=m['source_sha256'];raw=gzip.decompress((r/'preserved'/catalog['objects'][h]['path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==h;font=ImageFont.truetype(io.BytesIO(raw),48,index=3);atlas=Image.open(base/'poster-toolbar-font.png').convert('RGBA');assert atlas.size==(1024,576)
  for c in '戰術':
   assert c not in {g['character']for g in m['glyphs']};i=len(m['glyphs']);x,y=i%16*64,i//16*64;b=font.getbbox(c);w,h=b[2]-b[0],b[3]-b[1];ox,oy=x+(64-w)//2,y+(64-h)//2;ImageDraw.Draw(atlas).text((ox-b[0],oy-b[1]),c,font=font,fill='white');m['glyphs'].append(dict(character=c,ink=[ox,oy,w,h]))
  atlas.save(a.out/'poster-toolbar-font.png');m.update(schema=4,atlas_sha256=sha(a.out/'poster-toolbar-font.png'));(a.out/'poster-toolbar.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(files=525,glyphs=139,atlas_sha256=m['atlas_sha256'])))
 else:
  core=read(a.player/'runtime.json');assert core['total_inputs']==len(core['files'])==923
  for n,h in core['files'].items():assert sha(a.player/'runtime-render-r1/src'/n)==h
  digests={}
  for n in sorted(old['source_inputs']):
   f=r/n;assert f.stat().st_uid==1000;out=a.out/'src'/n;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,out);digests[n]=sha(f)
  assert len(digests)==184
  (a.out/'build-inputs.sha256').write_text(''.join(f'{h}  /project/{n}\n'for n,h in digests.items()));(a.out/'runtime.json').write_text(json.dumps(core,indent=2)+'\n');(a.out/'preparation.json').write_text(json.dumps(dict(source_inputs=digests,source_count=184,core_files=923,previous_programs=old['programs'],changed=[n for n in digests if digests[n]!=old['source_inputs'][n]]),indent=2)+'\n');print('frozen tactics candidate: 184 inputs, 923 core')
if __name__=='__main__':main()
