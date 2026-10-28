#!/usr/bin/env python3
"""054 READY: frozen additive HD pack, preserve all r64 files."""
import argparse,hashlib,json,os,pathlib,shutil,runpy
from PIL import Image,__version__
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--sources-only',action='store_true');a=p.parse_args();r=a.project
 assert os.getuid()==1000 and pathlib.Path('/.dockerenv').exists() and __version__=='11.3.0'
 assert not a.out.exists() and a.out.parent.is_dir() and a.out.parent.stat().st_uid==1000
 rows=json.loads((r/'artwork/all-graphics-hd-coverage-r1.json').read_text())['records'];inv={v['file']:v for v in json.loads((r/'docs/images/graphics-inventory-r1.json').read_text())['files']};orig=r/'workplace/intake-20261023/sources/game/8sword';base=r/'workplace/player/assets-painted-r64'
 assert len(list(base.iterdir()))==462
 selected=[v for v in rows if not v['hd']['integrated']];assert len(selected)==62
 if a.sources_only:
  a.out.mkdir();decode=runpy.run_path(str(r/'tools/prepare-hd-intro.py'))['decode'];cache={};result=[]
  for v in selected:
   name=v['source_file'];index=v['record']
   if name not in ['END3.AY','END4.AY','END6.AY','END9.AY','LIVE4.AY','LIVE6.AY','MAN27.EGG','PMAP.AY']:continue
   if name not in cache:
    b=(orig/name).read_bytes();cache[name]=decode(b)if inv[name].get('packed')else b
   b=cache[name][v['decoded_offset']:v['decoded_offset']+v['bytes']];assert hashlib.sha256(b).hexdigest()==v['record_sha256'];file=name.lower().replace('.','-')+f'-{index:02}.bin';(a.out/file).write_bytes(b);result.append(dict(source_file=name,record=index,file=file,sha256=v['record_sha256']))
  assert len(result)==17;(a.out/'sources.json').write_text(json.dumps(result,indent=2)+'\n');print('17 verified raw records');return
 a.out.mkdir();old={}
 for f in sorted(base.iterdir()):
  assert f.is_file() and not f.is_symlink();old[f.name]=sha(f);shutil.copyfile(f,a.out/f.name)
 records=[]
 for v in selected:
  name,index=v['source_file'],v['record'];route='archive';ident=0;alias=0
  if name in ['END3.AY','END4.AY','END6.AY','END9.AY']:route='ending'
  if name in ['LIVE4.AY','LIVE6.AY']:route='material';ident=868 if name=='LIVE4.AY' else 869
  if name=='MAN27.EGG':route='actor';ident=870+index;alias=874+index
  if name=='PMAP.AY':route='material';ident=index+1
  assert sha(orig/name)==inv[name]['sha256']
  source=r/v['hd']['file'];assert sha(source)==v['hd']['sha256'];im=Image.open(source);im.verify()
  dest='complete-'+name.lower().replace('.','-')+f'-{index:02}.png';shutil.copyfile(source,a.out/dest)
  records.append(dict(source_file=name,record=index,original_sha256=inv[name]['sha256'],source_sha256=v['record_sha256'],native_sha256=v.get('native_fingerprint',''),native_width=v['width'],native_height=v['height'],planes=v.get('planes',0),route=route,id=ident,alias=alias,image=dest,image_sha256=sha(a.out/dest),width=v['hd']['width'],height=v['hd']['height']))
 assert sum(v['route']!='archive'for v in records)==17
 manifest=dict(schema=1,spec='054',records=records);path=a.out/'completion.json';path.write_text(json.dumps(manifest,indent=2)+'\n')
 assert len(list(a.out.iterdir()))==525
 receipt=dict(schema=1,status='candidate-not-promoted',files=525,old_files=old,manifest_sha256=sha(path),records=records,tool_sha256=sha(pathlib.Path(__file__)))
 (a.out.parent/'registration-r1.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(manifest_sha256=sha(path),files=525,active=17,archive=45)))
if __name__=='__main__':main()
