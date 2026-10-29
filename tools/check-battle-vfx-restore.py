#!/usr/bin/env python3
"""Rebuild the exact Go prototype using restored files and permanent artwork only."""
import argparse,hashlib,json,os,pathlib,subprocess,tempfile
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 p=argparse.ArgumentParser()
 for n in ['archive','restore','artwork','out']:p.add_argument('--'+n,type=pathlib.Path,required=True)
 a=p.parse_args();assert os.getuid()==1000 and not a.out.exists();assert a.restore.resolve()==(a.archive/'restore-checks/battle-vfx-r1').resolve();index=read(a.archive/'battle-vfx-r1.json');assert read(a.archive/'battle-vfx-restoration-r1.json')['restored'];q=a.restore/'workplace/probe-20261023/graphics-first/battle-r1/battle-vfx-r1'
 for d in index['artwork_dependencies']:
  rel=pathlib.PurePosixPath(d['path']);assert rel.parts[0]=='artwork'and sha(a.artwork/pathlib.Path(*rel.parts[1:]))==d['sha256']
 inputs=read(q/'inputs-r1.json')
 def remap(s):
  path=pathlib.PurePosixPath(s);assert path.parts[:3]==('/','project','artwork');return str(a.artwork/pathlib.Path(*path.parts[3:]))
 for k in ['Background','Militia','Dwarf']:inputs[k]=remap(inputs[k])
 for k in ['Source','PON']:inputs[k]=[remap(s)for s in inputs[k]]
 with tempfile.TemporaryDirectory(prefix='battle-vfx-')as tmp:
  tmp=pathlib.Path(tmp);(tmp/'inputs.json').write_text(json.dumps(inputs));subprocess.run([str(q/'prototype-r2'),'-inputs',str(tmp/'inputs.json'),'-out',str(tmp/'render')],check=True,timeout=45)
  expected={p.name:sha(p)for p in(q/'render-r2').iterdir()if p.is_file()};actual={p.name:sha(p)for p in(tmp/'render').iterdir()if p.is_file()};assert expected==actual and len(expected)==132
 files={p.relative_to(a.restore).as_posix():p for p in a.restore.rglob('*')if p.is_file()};expected={v['path']:v for v in index['files']};assert files.keys()==expected.keys();total=0
 for n,f in files.items():assert not f.is_symlink()and f.stat().st_uid==1000 and sha(f)==expected[n]['sha256'];total+=f.stat().st_size
 for f in files.values():f.unlink()
 for d in sorted((p for p in a.restore.rglob('*')if p.is_dir()),key=lambda p:len(p.parts),reverse=True):d.rmdir()
 a.restore.rmdir();result=dict(status='passed-detached-go-vfx-reproduction',workplace_required=False,original_game_required=False,permanent_artwork_files=len(index['artwork_dependencies']),rebuilt_outputs_equal=132,restored_files_verified=len(files),verified_restore_copy_cleaned=True,bytes_cleaned=total);a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
