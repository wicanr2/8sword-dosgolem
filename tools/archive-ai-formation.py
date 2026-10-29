#!/usr/bin/env python3
"""Permanent formation-aware AI candidate, original controls and actual GUI."""
import argparse,gzip,hashlib,json,os,pathlib
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path);p.add_argument('--archive',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--verify',action='store_true');p.add_argument('--restore',type=pathlib.Path);a=p.parse_args();assert os.getuid()==1000 and not a.out.exists();index=a.archive/'ai-formation-r1.json';storage=a.archive/'ai-formation-r1'
 if a.verify or a.restore:
  d=json.loads(index.read_text());assert d['status']=='preserved';checked={}
  if a.restore:assert a.restore.is_dir() and not any(a.restore.iterdir())
  for v in d['files']:
   n=pathlib.PurePosixPath(v['path']);assert not n.is_absolute() and '..'not in n.parts
   if v['sha256']not in checked:
    o=d['objects'][v['sha256']];blob=(storage/o['file']).read_bytes();assert sha(blob)==o['stored_sha256'];raw=gzip.decompress(blob);assert sha(raw)==v['sha256'];checked[v['sha256']]=raw
   raw=checked[v['sha256']];assert len(raw)==v['bytes']
   if a.restore:f=a.restore/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(raw);f.chmod(v['mode'])
  result=dict(status='passed',files=len(d['files']),objects=len(checked),workplace_required=False,restored=bool(a.restore),index_sha256=sha(index.read_bytes()))
 else:
  assert a.project and not index.exists() and not storage.exists();r=a.project;q=r/'workplace/probe-20261023/graphics-first/battle-r1/ai-formation-r1';audit=q/'engine-audit-r1.json';assert json.loads(audit.read_text())['status']=='passed-scoped-ai-formation-engine';selected=[]
  for root in [q,r/'workplace/player/source-candidate-ai-formation-r1']:selected.extend(f for f in root.rglob('*')if f.is_file() and not f.is_symlink())
  selected.extend(r/'tools'/n for n in ['probe-ai-formation.go','prepare-ai-formation.py','audit-ai-formation.py','prepare-ai-formation-engine.py','check-ai-formation-gui.sh','audit-ai-formation-engine.py','archive-ai-formation.py']);selected.append(r/'docs/spec/030-battle-expansion-proposal.md');storage.mkdir();files=[];objects={}
  for f in sorted(set(selected)):
   assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();h=sha(raw)
   if h not in objects:blob=gzip.compress(raw,compresslevel=6,mtime=0);name=h+'.gzip';(storage/name).write_bytes(blob);objects[h]=dict(file=name,stored_sha256=sha(blob),stored_bytes=len(blob))
   files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(raw),mode=f.stat().st_mode&0o777))
  d=dict(schema=1,status='preserved',files=files,objects=objects,audit_sha256=sha(audit.read_bytes()),dependencies='Original data, fixed snapshot, 923 core, modules, unchanged r67 assets and accepted XTEST helper remain in existing permanent catalogs including formation-engine-r1.json.');index.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');result=dict(status='preserved',files=len(files),objects=len(objects),stored_bytes=sum(v['stored_bytes']for v in objects.values()))
 a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
