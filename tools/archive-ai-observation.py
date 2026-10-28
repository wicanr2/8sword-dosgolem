#!/usr/bin/env python3
"""030: preserve bounded research evidence, with detached verification/restore."""
import argparse,gzip,hashlib,json,os,pathlib
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path);p.add_argument('--archive',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--verify',action='store_true');p.add_argument('--restore',type=pathlib.Path);a=p.parse_args();assert os.getuid()==1000 and not a.out.exists();index=a.archive/'ai-observation-r1.json';storage=a.archive/'ai-observation-r1'
 if a.verify or a.restore:
  d=json.loads(index.read_text());assert d['status']=='preserved'
  if a.restore:assert a.restore.is_dir()and not any(a.restore.iterdir())
  for v in d['files']:
   name=pathlib.PurePosixPath(v['path']);assert not name.is_absolute()and '..'not in name.parts;blob=(storage/v['stored']).read_bytes();assert sha(blob)==v['stored_sha256'];raw=gzip.decompress(blob);assert sha(raw)==v['sha256']and len(raw)==v['bytes']
   if a.restore:
    f=a.restore/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(raw);f.chmod(v['mode'])
  result=dict(status='passed',files=len(d['files']),workplace_required=False,restored=bool(a.restore),index_sha256=sha(index.read_bytes()))
 else:
  assert a.project and not index.exists()and not storage.exists();r=a.project;batch=r/'workplace/probe-20261023/graphics-first/battle-r1/ai-observation-r1';audit=json.loads((batch/'audit-r2.json').read_text());assert audit['status']=='PASS-scoped-read-only-AI-observation-and-offline-shadow';storage.mkdir();selected=[]
  for f in sorted(batch.rglob('*')):
   if f.is_file()and not f.is_symlink():selected.append((f,str(f.relative_to(batch))))
  for name in ['prepare-ai-observation.py','probe-ai-observation.go','research-ai-shadow.go','probe-ai-target-experiment.go','audit-ai-observation.py','archive-ai-observation.py']:selected.append((r/'tools'/name,'tools/'+name))
  rows=[]
  for f,name in selected:
   assert f.stat().st_uid==1000;raw=f.read_bytes();blob=gzip.compress(raw,compresslevel=6,mtime=0);dest=storage/(name+'.gz');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(blob);rows.append(dict(path=name,stored=str(dest.relative_to(storage)),sha256=sha(raw),stored_sha256=sha(blob),bytes=len(raw),mode=f.stat().st_mode&0o777))
  d=dict(schema=1,status='preserved',files=rows,audit_sha256=sha((batch/'audit-r2.json').read_bytes()),original_core='existing preserved runtime-render-r1/src, 923 files',production_assets='unchanged r65',tool_sha256=sha(pathlib.Path(__file__).read_bytes()));index.write_text(json.dumps(d,indent=2)+'\n');result=dict(status='preserved',files=len(rows),stored_bytes=sum((storage/v['stored']).stat().st_size for v in rows))
 a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
