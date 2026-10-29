#!/usr/bin/env python3
"""Permanent offline prototype and evidence, separate from future production."""
import argparse,gzip,hashlib,json,os,pathlib
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path);p.add_argument('--archive',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--verify',action='store_true');p.add_argument('--restore',type=pathlib.Path);a=p.parse_args();assert os.getuid()==1000 and not a.out.exists();index=a.archive/'archer-pressure-r1.json';storage=a.archive/'archer-pressure-r1'
 if a.verify or a.restore:
  d=json.loads(index.read_text());assert d['status']=='preserved-prototype';checked={}
  if a.restore:assert a.restore.is_dir() and not any(a.restore.iterdir())
  for v in d['files']:
   n=pathlib.PurePosixPath(v['path']);assert not n.is_absolute()and'..'not in n.parts
   if v['sha256']not in checked:
    o=d['objects'][v['sha256']];blob=(storage/o['file']).read_bytes();assert sha(blob)==o['stored_sha256'];raw=gzip.decompress(blob);assert sha(raw)==v['sha256'];checked[v['sha256']]=raw
   raw=checked[v['sha256']];assert len(raw)==v['bytes']
   if a.restore:f=a.restore/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(raw);f.chmod(v['mode'])
  result=dict(status='passed',files=len(d['files']),objects=len(checked),workplace_required=False,restored=bool(a.restore),index_sha256=sha(index.read_bytes()))
 else:
  assert a.project and not index.exists()and not storage.exists();r=a.project;q=r/'workplace/probe-20261023/graphics-first/battle-r1/archer-pressure-r1';assert json.loads((q/'audit-r1.json').read_text())['calculations']==60 and json.loads((q/'browser-r1.json').read_text())['interactions']==60
  selected=[f for f in q.rglob('*')if f.is_file()and not f.is_symlink()];selected.extend(r/n for n in json.loads((q/'preparation-r1.json').read_text())['sources']);selected.extend(r/'tools'/n for n in ['research-archer-pressure.go','research-archer-pressure_test.go','prepare-archer-pressure.py','check-archer-pressure.js','archive-archer-pressure.py']);storage.mkdir();files=[];objects={}
  for f in sorted(set(selected)):
   assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();h=sha(raw)
   if h not in objects:blob=gzip.compress(raw,compresslevel=6,mtime=0);name=h+'.gzip';(storage/name).write_bytes(blob);objects[h]=dict(file=name,stored_sha256=sha(blob),stored_bytes=len(blob))
   files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(raw),mode=f.stat().st_mode&0o777))
  index.write_text(json.dumps(dict(schema=1,status='preserved-prototype',files=files,objects=objects,scope='25 percent plus independent tactics mode approved; only offline prototype captured, no formal implementation yet.'),ensure_ascii=False,indent=2)+'\n');result=dict(status='preserved-prototype',files=len(files),objects=len(objects),stored_bytes=sum(v['stored_bytes']for v in objects.values()))
 a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
