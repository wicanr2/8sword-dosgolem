#!/usr/bin/env python3
"""Preserve the disposable VFX study, original controls and both Go render revisions."""
import argparse,gzip,hashlib,json,os,pathlib
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path);p.add_argument('--archive',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--verify',action='store_true');p.add_argument('--restore',type=pathlib.Path);a=p.parse_args();assert os.getuid()==1000 and not a.out.exists();index=a.archive/'battle-vfx-r1.json';storage=a.archive/'battle-vfx-r1'
 if a.verify or a.restore:
  d=json.loads(index.read_text());checked={}
  if a.restore:assert a.restore.is_dir()and not any(a.restore.iterdir())
  for v in d['files']:
   n=pathlib.PurePosixPath(v['path']);assert not n.is_absolute()and '..'not in n.parts
   if v['sha256']not in checked:
    o=d['objects'][v['sha256']];blob=(storage/o['file']).read_bytes();assert sha(blob)==o['stored_sha256'];raw=gzip.decompress(blob);assert sha(raw)==v['sha256'];checked[v['sha256']]=raw
   raw=checked[v['sha256']];assert len(raw)==v['bytes']
   if a.restore:f=a.restore/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(raw);f.chmod(v['mode'])
  result=dict(status='passed',files=len(d['files']),objects=len(checked),workplace_required=False,restored=bool(a.restore),index_sha256=sha(index.read_bytes()))
 else:
  assert a.project and not index.exists()and not storage.exists();r=a.project;q=r/'workplace/probe-20261023/graphics-first/battle-r1/battle-vfx-r1';audit=json.loads((q/'audit-r1.json').read_text());browser=json.loads((q/'preview-r2/browser-r1.json').read_text());assert audit['status']=='passed-scoped-battle-vfx-observation'and browser['status']=='passed-scoped-vfx-prototype';selected=[p for p in q.rglob('*')if p.is_file()and not p.is_symlink()]
  selected.extend(r/'tools'/n for n in ['probe-battle-vfx.go','prototype-battle-vfx.go','prepare-battle-vfx.py','check-battle-vfx.js','archive-battle-vfx.py']);selected.append(r/'docs/spec/030-battle-expansion-proposal.md')
  for name in ['special0-choice','special2-choice','special5-empty-original']:
   root=q.parent/('ai-policy-extra-r2'if name.startswith('special5')else'ai-policy-r1')/name/'baseline';selected.extend(root/n for n in ['trace.json','before-decision.state','final.state'])
  storage.mkdir();files=[];objects={}
  for f in sorted(set(selected)):
   assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();h=sha(raw)
   if h not in objects:blob=gzip.compress(raw,compresslevel=6,mtime=0);name=h+'.gzip';(storage/name).write_bytes(blob);objects[h]=dict(file=name,stored_sha256=sha(blob),stored_bytes=len(blob))
   files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(raw),mode=f.stat().st_mode&0o777))
  inputs=json.loads((q/'inputs-r1.json').read_text());art=sorted({inputs[k]for k in ['Background','Militia','Dwarf']}|set(inputs['Source'])|set(inputs['PON']));dependencies=[dict(path=str(pathlib.Path(p).relative_to(r)),sha256=sha(pathlib.Path(p).read_bytes()))for p in art]
  d=dict(schema=1,status='preserved',scope='DRAFT animation prototype, not production or named player spells',files=files,objects=objects,artwork_dependencies=dependencies,original_dependencies='Original PAM and 923 core remain in existing permanent catalogs; three exact old state references copied here.');index.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');result=dict(status='preserved',files=len(files),objects=len(objects),stored_bytes=sum(v['stored_bytes']for v in objects.values()))
 a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
