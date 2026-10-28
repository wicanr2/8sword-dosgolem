#!/usr/bin/env python3
"""030 READY: freeze the first formation engine and append toolbar glyphs."""
import argparse,gzip,hashlib,io,json,os,pathlib,shutil
from PIL import Image,ImageDraw,ImageFont,__version__
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['assets','freeze']);p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--player',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();r=a.project;assert os.getuid()==a.player.stat().st_uid==1000 and not a.out.exists();old=read(r/'preserved/ai-toolbar-audit-r1.json')
 for n,h in old['programs'].items():assert sha(a.player/n)==h
 a.out.mkdir()
 if a.action=='assets':
  assert __version__=='11.3.0';base=a.player/'assets-painted-r66'
  for n,h in old['asset_hashes'].items():assert sha(base/n)==h;shutil.copyfile(base/n,a.out/n)
  m=read(base/'poster-toolbar.json');assert m['schema']==2 and len(m['glyphs'])==127
  catalog=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));key=m['source_sha256'];raw=gzip.decompress((r/'preserved'/catalog['objects'][key]['path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==key
  font=ImageFont.truetype(io.BytesIO(raw),48,index=3);atlas=Image.new('RGBA',(1024,576));atlas.paste(Image.open(base/'poster-toolbar-font.png'),(0,0));chars={g['character']for g in m['glyphs']}
  for c in '規則結陣試作本場固定':
   assert c not in chars;i=len(m['glyphs']);x,y=i%16*64,i//16*64;box=font.getbbox(c);w,h=box[2]-box[0],box[3]-box[1];ox,oy=x+(64-w)//2,y+(64-h)//2;ImageDraw.Draw(atlas).text((ox-box[0],oy-box[1]),c,font=font,fill='white');m['glyphs'].append(dict(character=c,ink=[ox,oy,w,h]))
  atlas.save(a.out/'poster-toolbar-font.png');m.update(schema=3,atlas_sha256=sha(a.out/'poster-toolbar-font.png'));(a.out/'poster-toolbar.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(files=525,glyphs=137,atlas_sha256=m['atlas_sha256'])))
 else:
  files=set(old['source_inputs'])|{'internal/eightsword/'+n for n in ['battle_rules.go','battle_rules_test.go','battle_rules_runtime_test.go']};assert len(files)==184;digests={}
  core=read(a.player/'runtime.json');assert core['total_inputs']==923
  for n,h in core['files'].items():assert sha(a.player/'runtime-render-r1/src'/n)==h
  for n in sorted(files):
   source=r/n;assert source.stat().st_uid==1000;target=a.out/'src'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);digests[n]=sha(source)
  (a.out/'build-inputs.sha256').write_text(''.join(f'{h}  /project/{n}\n'for n,h in digests.items()));(a.out/'runtime.json').write_text(json.dumps(core,indent=2)+'\n');(a.out/'preparation.json').write_text(json.dumps(dict(source_inputs=digests,source_count=184,core_files=923,previous_programs=old['programs']),indent=2)+'\n');print('frozen 184 inputs with original 923-file core')
if __name__=='__main__':main()
