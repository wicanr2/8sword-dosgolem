#!/usr/bin/env python3
"""User-authorized cleanup, fixed plans and verified archived cold data only."""
import argparse,collections,gzip,hashlib,json,os,pathlib,time
CATALOG='8ab4fd7c02d82e23ac45a475ab2e0bfa7283d0f4ca53f4234525d7796e458b6b'
def digest(p,codec='raw'):
 h=hashlib.sha256();op=gzip.open if codec=='gzip'else open
 with op(p,'rb')as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--phase',choices=['quick','archived'],required=True);p.add_argument('--plan',type=pathlib.Path,required=True);p.add_argument('--apply',action='store_true');p.add_argument('--out',type=pathlib.Path);a=p.parse_args();r=a.project;work=r/'workplace';assert os.getuid()==1000 and work.is_dir() and work.stat().st_uid==1000;archive=r/'preserved';catalog=archive/'catalog.json.gz';assert digest(catalog)==CATALOG
 protected=['workplace/probe-20261023/graphics-first/all-graphics-integration-r1/','workplace/probe-20261023/graphics-first/ending-hd-r1/','workplace/player/gui/compat-pixels-save-r2/']
 def retired(name):
  if any(name.startswith(v)for v in protected):return False
  if name=='workplace/probe-20261023/graphics-first/map-interaction-r1/buildings-registration-r1/gro02-native.bin':return False
  parts=pathlib.PurePosixPath(name).parts
  if len(parts)<3 or parts[0]!='workplace':return False
  if parts[1]=='player':
   top=parts[2]
   return ((top.startswith('assets')and top not in ['assets','assets-painted-r64','assets-painted-r65'])or(top.startswith('source-candidate-')and top not in ['source-candidate-ring-r3','source-candidate-completion-r1','source-candidate-completion-r2','source-candidate-completion-r3','source-candidate-completion-r4'])or top in ['gui','replays'])
  return name.startswith('workplace/probe-20261023/graphics-first/')
 if a.apply:
  plan=json.loads(gzip.decompress(a.plan.read_bytes()));assert plan['phase']==a.phase and plan['catalog_sha256']==CATALOG;assert a.out and not a.out.exists();before=os.statvfs(work);removed=0;size=0;skipped=[];parents=set()
  for v in plan['files']:
   rel=pathlib.PurePosixPath(v['path']);assert not rel.is_absolute()and '..'not in rel.parts and rel.parts[0]=='workplace';f=r/rel
   assert all(not(r/pathlib.PurePosixPath(*rel.parts[:n])).is_symlink()for n in range(1,len(rel.parts)))
   try:s=f.lstat()
   except FileNotFoundError:continue
   assert s.st_uid==1000
   if (s.st_size,s.st_mtime_ns,s.st_ino)!=(v['bytes'],v['mtime_ns'],v['inode']):skipped.append(str(rel));continue
   if v['kind']=='archived-link':assert f.is_symlink()and os.readlink(f)==v['target']
   else:assert f.is_file()and not f.is_symlink()
   f.unlink();removed+=1;size+=v['bytes'];parents.add(f.parent)
  for parent in sorted(parents,key=lambda p:len(p.parts),reverse=True):
   while parent!=work and parent!=work/'gocache':
    try:parent.rmdir()
    except OSError:break
    parent=parent.parent
  after=os.statvfs(work);result=dict(schema=1,status='completed',phase=a.phase,removed_files=removed,removed_logical_bytes=size,free_bytes_before=before.f_bavail*before.f_frsize,free_bytes_after=after.f_bavail*after.f_frsize,changed_files_kept=skipped,plan_sha256=digest(a.plan),catalog_sha256=CATALOG,protected=protected)
  a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False));return
 assert not a.plan.exists();rows=[];verified=set();counts=collections.Counter();started=time.monotonic()
 def include(f,kind,extra=None):
  rel=f.relative_to(r);assert all(not(r/pathlib.Path(*rel.parts[:n])).is_symlink()for n in range(1,len(rel.parts)))
  s=f.lstat();assert s.st_uid==1000;v=dict(path=str(rel),kind=kind,bytes=s.st_size,mtime_ns=s.st_mtime_ns,inode=s.st_ino);v.update(extra or {});rows.append(v);counts[kind]+=1
 if a.phase=='quick':
  exclusions=json.loads(gzip.decompress((archive/'exclusions.json.gz').read_bytes()))
  for v in exclusions:
   if v['path'].endswith('.frames.gz'):
    f=r/v['path']
    if f.is_file()and not f.is_symlink()and f.stat().st_size==v['bytes']:include(f,'expired-recording')
  cache=work/'gocache'
  for folder,dirs,names in os.walk(cache,followlinks=False):
   for name in names:
    f=pathlib.Path(folder)/name;assert not f.is_symlink();include(f,'rebuildable-go-cache')
 else:
  data=json.loads(gzip.decompress(catalog.read_bytes()));objects=data['objects']
  for index,v in enumerate(data['files']):
   if not retired(v['path']):continue
   f=r/v['path']
   if not f.is_file()or f.is_symlink()or f.stat().st_size!=v['bytes']:continue
   if digest(f)!=v['sha256']:continue
   key=v['sha256'];o=objects[key]
   if key not in verified:
    saved=r/'artwork'/o['path']if o['codec']=='artwork'else archive/o['path'];assert saved.is_file()and not saved.is_symlink();assert digest(saved,o['codec'])==key;verified.add(key)
   include(f,'verified-archived',dict(sha256=key))
   if len(rows)%10000==0:print(json.dumps(dict(verified_files=len(rows),unique_objects=len(verified),seconds=round(time.monotonic()-started))),flush=True)
  for v in data['links']:
   f=r/v['path']
   if retired(v['path'])and f.is_symlink()and os.readlink(f)==v['target']:include(f,'archived-link',dict(target=v['target']))
 result=dict(schema=1,phase=a.phase,catalog_sha256=CATALOG,files=rows,counts=dict(counts),logical_bytes=sum(v['bytes']for v in rows),verified_archive_objects=len(verified),protected=protected)
 a.plan.write_bytes(gzip.compress(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode(),compresslevel=6,mtime=0));print(json.dumps({k:v for k,v in result.items()if k!='files'},ensure_ascii=False))
if __name__=='__main__':main()
