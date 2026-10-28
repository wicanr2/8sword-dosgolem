#!/usr/bin/env python3
"""054: detached permanent-library audit; never reads workplace."""
import argparse, collections, hashlib, json, pathlib
from PIL import Image, __version__

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--archive',type=pathlib.Path,required=True);p.add_argument('--write-manifest',action='store_true');p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();root=a.archive
 assert __version__=='11.3.0',__version__
 assert sha(root/'manifest.json')=='daaca39e8a5a69e169b089b1155c6e71e57675d6be2d6fac327d04fdcd03e7e1','initial immutable archive index changed'
 coverage=json.loads((root/'all-graphics-hd-coverage-r1.json').read_text());rows=coverage['records'];assert len(rows)==333
 seen=set();categories=collections.Counter();methods=collections.Counter();runtime=0
 def local(name):
  q=pathlib.PurePosixPath(name);q=q.relative_to('artwork')if q.parts[0]=='artwork' else q
  assert not q.is_absolute() and '..'not in q.parts
  result=root/q;assert result.is_file() and not result.is_symlink(),str(q);return result
 old=json.loads((root/'manifest.json').read_text());entries=old['files'];aliases={v['source']:v['path']for v in entries}
 def resolve(name):
  if name.startswith('workplace/'):
   assert name in aliases,'missing permanent input: '+name;return local(aliases[name])
  return local(name)
 for r in rows:
  key=(r['source_file'],r['record']);assert key not in seen;seen.add(key);assert r['status']=='art-ready'
  original=Image.open(local(r['native'])).convert('RGBA');assert sha_bytes(original.tobytes())==r['decoded_rgba_sha256'];assert original.size==(r['width'],r['height'])
  h=r['hd'];path=local(h['file']);assert sha(path)==h['sha256'];im=Image.open(path);im.verify();im=Image.open(path)
  expected=((640 if r['format']=='VGA8 palette+indices'else r['width'])*3,r['height']*6);assert im.size==expected,(key,im.size,expected)
  assert im.size==(h['width'],h['height'])
  for inp in set(h['inputs']):resolve(inp)
  categories[r['category']]+=1;methods[h['method']]+=1;runtime+=bool(h['integrated'])
 additions=json.loads((root/'hd-additions-r1.json').read_text())
 generation=[]
 for item in additions['images']:
  for field,digest in [('image','image_sha256'),('prompt','prompt_sha256'),('receipt','receipt_sha256')]:assert sha(local(item[field]))==item[digest]
  receipt=json.loads(local(item['receipt']).read_text())
  # Receipts preserve the exact source bytes; the new manifest below also covers references.
  assert receipt['prompt_sha256']==item['prompt_sha256']
  generation.append(dict(name=item['name'],scope=item['scope'],image_sha256=item['image_sha256'],prompt_sha256=item['prompt_sha256'],prompt=local(item['prompt']).read_text(),receipt=receipt,selection='historical-replaced' if item['name']=='ending-scroll-states-r1' else 'current-art-preparation'))
 generation_path=root/'all-graphics-hd-generation-r1.json';generation_body=dict(schema=1,rights='private repository artwork documentation; full masters remain local',images=generation)
 if a.write_manifest:generation_path.write_text(json.dumps(generation_body,ensure_ascii=False,indent=2)+'\n')
 else:assert json.loads(generation_path.read_text())==generation_body,'generation prompt mirror differs'
 dirs=['masters','references','provenance','registered-textures'];files=[]
 for kind in dirs:
  base=root/'approved'/kind/'all-graphics-hd-r1'
  assert base.is_dir()
  for f in sorted(base.rglob('*')):
   assert not f.is_symlink(),str(f)
   if f.is_file():
    v=dict(path=str(f.relative_to(root)),bytes=f.stat().st_size,sha256=sha(f),kind=kind)
    if f.suffix.lower()=='.png':
     im=Image.open(f);im.verify();im=Image.open(f);v.update(width=im.width,height=im.height,mode=im.mode)
    files.append(v)
 manifest=root/'all-graphics-hd-files-r1.json';body=dict(schema=1,scope='additive permanent all-graphics artwork; initial974 unchanged',files=files)
 if a.write_manifest:manifest.write_text(json.dumps(body,ensure_ascii=False,indent=2)+'\n')
 else:assert json.loads(manifest.read_text())==body,'detached file list differs'
 result=dict(schema=1,status='passed',scope='all333 identified decoded image records have HD art; editor atlas correspondences remain graded art inference; no gameplay/GUI/runtime promotion assertion',pillow=__version__,original_archive_manifest_sha256=sha(root/'manifest.json'),coverage_sha256=sha(root/'all-graphics-hd-coverage-r1.json'),files_manifest_sha256=sha(manifest),generation_manifest_sha256=sha(generation_path),source_records=len(rows),categories=dict(categories),methods=dict(methods),formal_loader_derived_records=runtime,prepared_not_formally_integrated=len(rows)-runtime,new_masters=len(additions['images']),permanent_files=len(files),permanent_bytes=sum(v['bytes']for v in files),unknown_input_files=['A.A','PAE.RIL','PAF.RIL','PAS.RIL','PAW1.RIL','PAW2.RIL','PAWA.RIL'],workplace_mounted=False)
 a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
if __name__=='__main__':main()
