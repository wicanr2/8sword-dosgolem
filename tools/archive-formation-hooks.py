#!/usr/bin/env python3
"""030: permanent storage of confirmed-rule hookup research, not production."""
import argparse,gzip,hashlib,json,os,pathlib
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path);p.add_argument('--archive',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--verify',action='store_true');p.add_argument('--restore',type=pathlib.Path);a=p.parse_args();assert os.getuid()==1000 and not a.out.exists();index=a.archive/'formation-hooks-r1.json';storage=a.archive/'formation-hooks-r1'
 if a.verify or a.restore:
  d=json.loads(index.read_text());assert d['status']=='preserved-scoped-DRAFT';checked={}
  if a.restore:assert a.restore.is_dir() and not any(a.restore.iterdir())
  for v in d['files']:
   n=pathlib.PurePosixPath(v['path']);assert not n.is_absolute() and '..'not in n.parts
   if v['sha256']not in checked:
    o=d['objects'][v['sha256']];b=(storage/o['file']).read_bytes();assert sha(b)==o['stored_sha256'];raw=gzip.decompress(b);assert sha(raw)==v['sha256'];checked[v['sha256']]=raw
   raw=checked[v['sha256']];assert len(raw)==v['bytes']
   if a.restore:f=a.restore/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(raw);f.chmod(v['mode'])
  result=dict(status='passed',files=len(d['files']),objects=len(checked),workplace_required=False,restored=bool(a.restore),index_sha256=sha(index.read_bytes()))
 else:
  assert a.project and not index.exists() and not storage.exists();r=a.project;b=r/'workplace/probe-20261023/graphics-first/battle-r1';q=b/'formation-hooks-r1';assert json.loads((q/'audit-r1.json').read_text())['status']=='passed-scoped-original-helper-controls'
  selected=[f for f in q.rglob('*')if f.is_file() and not f.is_symlink()]
  selected.extend(b/'troop-traits-r1'/n for n in ['formation-toolbar-prototype-r1.html','toolbar-browser-r1.json','toolbar-browser-debug.jsonl'])
  selected.extend(r/'tools'/n for n in ['export-formation-hooks-ida.py','probe-formation-hooks.go','inspect-formation-states.go','audit-formation-hooks.py','archive-formation-hooks.py','check-formation-page.js','prepare-troop-traits.py'])
  storage.mkdir();files=[];objects={}
  for f in sorted(set(selected)):
   assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();h=sha(raw)
   if h not in objects:
    blob=gzip.compress(raw,compresslevel=6,mtime=0);name=h+'.gzip';(storage/name).write_bytes(blob);objects[h]=dict(file=name,stored_sha256=sha(blob),stored_bytes=len(blob))
   files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(raw),mode=f.stat().st_mode&0o777))
  d=dict(schema=1,status='preserved-scoped-DRAFT',files=files,objects=objects,scope='Rule value confirmed; isolated helper and HTML toolbar research only.');index.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');result=dict(status=d['status'],files=len(files),objects=len(objects),stored_bytes=sum(v['stored_bytes']for v in objects.values()))
 a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
