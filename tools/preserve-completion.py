#!/usr/bin/env python3
"""054: preserve r65 code/programs/evidence and a detached asset recipe."""
import argparse,gzip,hashlib,json,os,pathlib,shutil,subprocess
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path);p.add_argument('--archive',type=pathlib.Path,required=True);p.add_argument('--artwork',type=pathlib.Path,required=True);p.add_argument('--verify',action='store_true');p.add_argument('--restore-assets',type=pathlib.Path);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();assert os.getuid()==1000
 index=a.archive/'completion-r65.json';storage=a.archive/'completion-r65'
 if a.verify or a.restore_assets:
  d=read(index)
  for v in d['files']:
   blob=(storage/v['stored']).read_bytes();assert sha(blob)==v['stored_sha256'];raw=gzip.decompress(blob);assert sha(raw)==v['sha256']and len(raw)==v['bytes']
  for v in d['asset_additions']:
   raw=(a.artwork/v['permanent']).read_bytes();assert sha(raw)==v['sha256']
  if a.restore_assets:
   target=a.restore_assets;assert target.is_dir() and not any(target.iterdir());assert a.project
   subprocess.run(['python',str(a.project/'tools/preserve-project-data.py'),'--restore','--archive',str(a.archive),'--artwork',str(a.artwork),'--out',str(target),'--prefix','workplace/player/assets-painted-r64'],check=True)
   folder=target/'workplace/player/assets-painted-r64';folder.rename(target/'workplace/player/assets-painted-r65');folder=target/'workplace/player/assets-painted-r65'
   for v in d['asset_additions']:shutil.copyfile(a.artwork/v['permanent'],folder/v['name'])
   assert len(list(folder.iterdir()))==525
   for v in d['asset_files']:assert sha((folder/v['name']).read_bytes())==v['sha256']
  a.out.write_text(json.dumps(dict(schema=1,status='passed',files=len(d['files']),asset_files=525,workplace_required=False,restored_assets=bool(a.restore_assets),index_sha256=sha(index.read_bytes())),indent=2)+'\n');print('preservation verified');return
 r=a.project;assert r and not storage.exists() and not index.exists();storage.mkdir();player=r/'workplace/player';candidate=player/'source-candidate-completion-r4';assets=player/'assets-painted-r65';batch=r/'workplace/probe-20261023/graphics-first/all-graphics-integration-r1';files=[]
 selected=[]
 for line in (candidate/'build-outputs.sha256').read_text().splitlines():
  digest,name=line.split(None,1);name=pathlib.Path(name).name;assert sha((player/name).read_bytes())==digest;selected.append((candidate/name,'programs/'+name))
 for line in (candidate/'build-inputs.sha256').read_text().splitlines():
  digest,name=line.split(None,1);name=name.removeprefix('/project/');assert sha((candidate/'src'/name).read_bytes())==digest;selected.append((candidate/'src'/name,'sources/'+name))
 for name in ['build-inputs.sha256','build-outputs.sha256','build-source-checks.log','build-go-version.txt','runtime.json']:selected.append((player/name,'metadata/'+name))
 # Keep the exact pre-fix source/programs used by the independent audit.
 for revision in [1,2,3]:
  old=player/('source-candidate-completion-r'+str(revision))
  for f in old.rglob('*'):
   if f.is_file()and not f.is_symlink():selected.append((f,'previous-candidates/r'+str(revision)+'/'+str(f.relative_to(old))))
 for f in batch.rglob('*'):
  if not f.is_file()or f.is_symlink():continue
  rel=f.relative_to(batch)
  if rel.parts[0]=='assets-candidate-r1'or f.name in ['cpu.pprof','presentation.frames.gz']:continue
  selected.append((f,'evidence/'+str(rel)))
 for src,name in selected:
  raw=src.read_bytes();dest=storage/(name+'.gz');dest.parent.mkdir(parents=True,exist_ok=True);blob=gzip.compress(raw,compresslevel=6,mtime=0);dest.write_bytes(blob);files.append(dict(path=name,stored=str(dest.relative_to(storage)),sha256=sha(raw),stored_sha256=sha(blob),bytes=len(raw),mode=src.stat().st_mode&0o777))
 coverage=read(a.artwork/'all-graphics-hd-coverage-r1.json');lookup={(v['source_file'],v['record']):v for v in coverage['records']};manifest=read(assets/'completion.json');add=[]
 for v in manifest['records']:
  source=lookup[(v['source_file'],v['record'])]['hd']['file'].removeprefix('artwork/');assert sha((a.artwork/source).read_bytes())==v['image_sha256'];add.append(dict(name=v['image'],permanent=source,sha256=v['image_sha256']))
 permanent=a.artwork/'completion-r65.json';assert not permanent.exists();shutil.copyfile(assets/'completion.json',permanent);add.append(dict(name='completion.json',permanent='completion-r65.json',sha256=sha(permanent.read_bytes())))
 d=dict(schema=1,status='preserved',files=files,asset_additions=add,asset_files=[dict(name=f.name,sha256=sha(f.read_bytes()))for f in sorted(assets.iterdir())],base_restore_prefix='workplace/player/assets-painted-r64',base_catalog_sha256=sha((a.archive/'catalog.json.gz').read_bytes()),source_core='existing preserved workplace/player/runtime-render-r1/src (923 files)',tool_sha256=sha(pathlib.Path(__file__).read_bytes()))
 index.write_text(json.dumps(d,indent=2)+'\n');a.out.write_text(json.dumps(dict(status='preserved',files=len(files),asset_files=525,stored_bytes=sum((storage/v['stored']).stat().st_size for v in files)),indent=2)+'\n');print('r65 preservation captured')
if __name__=='__main__':main()
