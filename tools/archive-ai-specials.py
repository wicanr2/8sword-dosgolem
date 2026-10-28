#!/usr/bin/env python3
"""030: deduplicated permanent storage for the bounded AI special-dispatch study."""
import argparse,gzip,hashlib,json,os,pathlib
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path);p.add_argument('--archive',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--verify',action='store_true');p.add_argument('--restore',type=pathlib.Path);a=p.parse_args();assert os.getuid()==1000 and not a.out.exists();index=a.archive/'ai-specials-r1.json';storage=a.archive/'ai-specials-r1'
 if a.verify or a.restore:
  d=json.loads(index.read_text());assert d['status']=='preserved';checked={}
  if a.restore:assert a.restore.is_dir()and not any(a.restore.iterdir())
  for v in d['files']:
   name=pathlib.PurePosixPath(v['path']);assert not name.is_absolute()and '..'not in name.parts
   if v['sha256']not in checked:
    o=d['objects'][v['sha256']];blob=(storage/o['file']).read_bytes();assert sha(blob)==o['stored_sha256'];raw=gzip.decompress(blob);assert sha(raw)==v['sha256'];checked[v['sha256']]=raw
   raw=checked[v['sha256']];assert len(raw)==v['bytes']
   if a.restore:f=a.restore/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(raw);f.chmod(v['mode'])
  result=dict(status='passed',files=len(d['files']),objects=len(checked),workplace_required=False,restored=bool(a.restore),index_sha256=sha(index.read_bytes()))
 else:
  assert a.project and not index.exists()and not storage.exists();r=a.project;b=r/'workplace/probe-20261023/graphics-first/battle-r1';audit=b/'ai-specials-r1/audit-r1.json';assert json.loads(audit.read_text())['status']=='PASS-scoped-AI-specials-and-Go-shadow';storage.mkdir();selected=[]
  for top in ['ai-specials-r1','ai-specials-extra-r2']:
   for f in sorted((b/top).rglob('*')):
    if f.is_file()and not f.is_symlink():selected.append((f,str(f.relative_to(b))))
  for n in ['ai-specials-probe-r1','ai-specials-probe-r2','ai-specials-shadow-r1']:selected.append((b/n,n))
  for n in ['ida-ai-parents-r2.json','damage-multi-r3/trace.json','input-multi-r1/choi-hd-r1/multi-ready-before.state']:selected.append((b/'ai-observation-r1'/n,'references/'+n))
  for n in ['probe-ai-specials.go','research-ai-specials.go','export-ai-specials-ida.py','audit-ai-specials.py','archive-ai-specials.py']:selected.append((r/'tools'/n,'tools/'+n))
  rows=[];objects={}
  for f,name in selected:
   assert f.stat().st_uid==1000;raw=f.read_bytes();digest=sha(raw)
   if digest not in objects:
    blob=gzip.compress(raw,compresslevel=6,mtime=0);filename=digest+'.gz';(storage/filename).write_bytes(blob);objects[digest]=dict(file=filename,stored_sha256=sha(blob),stored_bytes=len(blob))
   rows.append(dict(path=name,sha256=digest,bytes=len(raw),mode=f.stat().st_mode&0o777))
  index.write_text(json.dumps(dict(schema=1,status='preserved',files=rows,objects=objects,audit_sha256=sha(audit.read_bytes()),core='existing preserved runtime-render-r1/src, 923 files',base_catalog_sha256='8ab4fd7c02d82e23ac45a475ab2e0bfa7283d0f4ca53f4234525d7796e458b6b'),indent=2)+'\n');result=dict(status='preserved',files=len(rows),objects=len(objects),stored_bytes=sum(v['stored_bytes']for v in objects.values()))
 a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
