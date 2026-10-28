#!/usr/bin/env python3
"""Permanent rules candidate, original controls, assets and normal GUI receipts."""
import argparse,gzip,hashlib,json,os,pathlib
def digest(b):return hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path);p.add_argument('--archive',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--verify',action='store_true');p.add_argument('--restore',type=pathlib.Path);a=p.parse_args();assert os.getuid()==1000 and not a.out.exists();index=a.archive/'formation-engine-r1.json';storage=a.archive/'formation-engine-r1'
 if a.verify or a.restore:
  d=json.loads(index.read_text());assert d['status']=='preserved';checked={}
  if a.restore:assert a.restore.is_dir() and not any(a.restore.iterdir())
  for v in d['files']:
   n=pathlib.PurePosixPath(v['path']);assert not n.is_absolute() and '..'not in n.parts
   if v['sha256']not in checked:
    o=d['objects'][v['sha256']];blob=(storage/o['file']).read_bytes();assert digest(blob)==o['stored_sha256'];raw=gzip.decompress(blob);assert digest(raw)==v['sha256'];checked[v['sha256']]=raw
   raw=checked[v['sha256']];assert len(raw)==v['bytes']
   if a.restore:f=a.restore/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(raw);f.chmod(v['mode'])
  result=dict(status='passed',files=len(d['files']),objects=len(checked),workplace_required=False,restored=bool(a.restore),index_sha256=digest(index.read_bytes()))
 else:
  assert a.project and not index.exists() and not storage.exists();r=a.project;b=r/'workplace/probe-20261023/graphics-first/battle-r1';q=b/'formation-engine-r1';audit=q/'audit-r1.json';assert json.loads(audit.read_text())['status']=='passed-scoped-030-formation'
  selected=[]
  for root in [q,r/'workplace/player/source-candidate-formation-r1',r/'workplace/player/source-candidate-formation-r2',b/'formation-hooks-r1/calls-r2']:
   selected.extend(f for f in root.rglob('*')if f.is_file() and not f.is_symlink())
  selected.extend(r/'workplace/player/assets-painted-r67'/n for n in ['poster-toolbar.json','poster-toolbar-font.png'])
  selected.extend(b/'formation-hooks-r1'/n for n in ['formation-hooks-probe-r2','build-reference-r2.log','calls-r2.log'])
  selected.extend(r/'tools'/n for n in ['prepare-formation-engine.py','prepare-formation-gui.py','check-formation-gui.sh','audit-formation-engine.py','archive-formation-engine.py','probe-formation-hooks.go'])
  selected.append(r/'docs/spec/030-battle-expansion-proposal.md');storage.mkdir();files=[];objects={}
  for f in sorted(set(selected)):
   assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();h=digest(raw)
   if h not in objects:
    blob=gzip.compress(raw,compresslevel=6,mtime=0);name=h+'.gzip';(storage/name).write_bytes(blob);objects[h]=dict(file=name,stored_sha256=digest(blob),stored_bytes=len(blob))
   files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(raw),mode=f.stat().st_mode&0o777))
  d=dict(schema=1,status='preserved',files=files,objects=objects,audit_sha256=digest(audit.read_bytes()),dependencies='Original data, 923 core, Go modules and unchanged r66 assets use existing permanent catalogs.');index.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');result=dict(status='preserved',files=len(files),objects=len(objects),stored_bytes=sum(v['stored_bytes']for v in objects.values()))
 a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
