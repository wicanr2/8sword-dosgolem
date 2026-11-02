#!/usr/bin/env python3
"""Promote the verified Go adapter into a buildable command, preserving init order."""
import argparse,gzip,hashlib,importlib.util,json,os,re,shutil
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/owned-player-r1'
BATCH='owned-player-r1';PARENT='reinforcement-camps-r1'
NEW=['prepare-owned-player.py','owned-player.sh','check-owned-player.py','audit-owned-player.py']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def helper(r):
 s=importlib.util.spec_from_file_location('h',r/'tools/prepare-owned-army-ui.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def translate(name,raw,index):
 s=raw.decode().removeprefix('//go:build ignore\n').replace('package main','package ownedworld',1)
 count=s.count('func init()');assert count<=1,name
 if count:s=s.replace('func init()',f'func initializeLayer{index:02d}()',1)
 if name=='world-army-review_main.go':
  start=s.index('func main()');s=s[:start]+'// Run handles import-only operations while the original battlefield bridge is pending.\nfunc Run() error { return runArmyReview() }\n'
  s=s.replace('var armyReviewTitle = "神州八劍・軍隊試作・檢閱"','var armyReviewTitle = "神州八劍・軍隊試作・檢閱"\n// Player combat must use the original battlefield. The former card UI remains\n// research source until its backend can drive the verified original interface.\nvar ErrOriginalBattlefieldPending = errors.New("原版／原版HD戰場的Go後端橋接尚未完成；卡片戰鬥入口已停用，既有進度保留")')
  s=s.replace('flag.Parse()','flag.Parse()\n if !*owned{return errors.New("Go軍隊命令不接受owned=false，原版模式請用8sword")}\n if !*nativeImportOnly{return ErrOriginalBattlefieldPending}')
  s=s.replace('*scratch == "" ||','(*scratch == "" && !*nativeImportOnly) ||')
  needle='store, snap, e := openProgressPair(*session, c, cc)'
  assert s.count(needle)==1;s=s.replace(needle,'if *nativeImportSource!="" { if e:=importNativeProgress(*root,*nativeImportSource,*session,*input,c,cc);e!=nil{return e};if *nativeImportOnly{return nil} } else if *nativeImportOnly{return errors.New("import-only requires import-native")}\n '+needle)
 return s,count
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','battle-input','archive','verify']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   o=d['objects'][f['sha256']];p=a.archive/BATCH/o['file'];assert sha(p)==o['stored_sha256'];b=gzip.decompress(p.read_bytes());assert len(b)==f['bytes']and hashlib.sha256(b).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-owned-player',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL;m=helper(r);deps=m.dependencies(r)
 if a.action=='battle-input':
  batch='reinforcement-battle-r1';folder=q/'session-battle-r1';assert not folder.exists();folder.mkdir();(folder/'.native-resume').mkdir()
  raw=m.stored(r,batch,'/'+batch+'/gui-r1/warm/pair-after-action.json');native=m.stored(r,batch,'/'+batch+'/initial-session/gamedata.ay');d=json.loads(raw);assert d['original_sha256']==hashlib.sha256(native).hexdigest();ref=d['native_resume'];state=m.stored(r,batch,'/'+batch+'/session/.native-resume/'+ref['sha256']+'.state');assert hashlib.sha256(state).hexdigest()==ref['sha256']and len(state)==ref['bytes']
  (folder/'gamedata.ay').write_bytes(native);(folder/'gamedata.ay.army.json').write_bytes(raw);(folder/'.native-resume'/(ref['sha256']+'.state')).write_bytes(state);return
 if a.action=='prepare':
  assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir();target=r/'internal/ownedworld'
  if not target.exists():target.mkdir()
  rows=[];layers=[]
  execution=json.loads(m.stored(r,PARENT,'/'+PARENT+'/execution-r1.json'));files=[n for n in execution['ui_build'].split()if n.endswith('.go')]
  assert len(files)==66
  for i,n in enumerate(files):
   raw=m.stored(r,PARENT,'/'+PARENT+'/go-src/'+n);s,count=translate(Path(n).name,raw,i);dst=target/Path(n).name
   if not dst.exists():dst.write_text(s)
   rows.append(dict(parent_path=n,parent_sha256=hashlib.sha256(raw).hexdigest(),path=str(dst.relative_to(r)),layer=i if count else None))
   if count:layers.append(i)
  if not(target/'initialization.go').exists():(target/'initialization.go').write_text('package ownedworld\n\n// Preserve the verified explicit-file compilation order.\nfunc init(){\n'+''.join(f'initializeLayer{i:02d}()\n'for i in layers)+'}\n')
  icon=m.stored(r,PARENT,'/'+PARENT+'/go-src/internal/eightsword/recruit_icons_candidate.go').decode().replace('// Copied without the ignore tag into the isolated candidate\'s game package.','// Read-only HD recruitment portraits; source mapping follows spec 030.')
  if not(r/'internal/eightsword/recruitment_icons.go').exists():(r/'internal/eightsword/recruitment_icons.go').write_text(icon)
  write(q/'adapter-origin.json',dict(parent=PARENT,parent_archive_sha256=sha(r/'preserved'/f'{PARENT}.json'),files=rows,init_layers=layers))
  (q/'inputs').mkdir();(q/'ui-assets').mkdir()
  for n in ['army-catalog.json','combat-catalog.json','origin-terrain-packed.ay']:(q/'inputs'/n).write_bytes(m.stored(r,PARENT,'/'+PARENT+'/inputs/'+n))
  for n,src in [('PAM.AY','PAM.AY'),('map01.ay','MAP01.AY')]:shutil.copyfile(r/'workplace/intake-20261023/sources/game/8sword'/src,q/'inputs'/n)
  d=read(r/'preserved'/f'{PARENT}.json')
  for f in d['files']:
   marker='/'+PARENT+'/ui-assets/'
   if marker in f['path']:(q/'ui-assets'/f['path'].split(marker,1)[1]).write_bytes(m.stored(r,PARENT,marker+f['path'].split(marker,1)[1]))
  for n in ['probe.mod','probe.sum','xcheck']:
   p=q/n;p.write_bytes(m.stored(r,PARENT,'/'+PARENT+'/'+n));p.chmod(493 if n=='xcheck' else 420)
  write(q/'baseline.json',deps)
 else:assert deps==read(q/'baseline.json')
 if a.action in ['prepare','freeze']:
  for name in deps['source_inputs']:
   p=q/'source'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/name,p)
  for p in list((r/'internal/ownedworld').glob('*.go'))+[r/'internal/eightsword/recruitment_icons.go']+list((r/'cmd/8sword-owned').glob('*.go')):
   dst=q/'source'/p.relative_to(r);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
  for n in NEW:
   if(r/'tools'/n).is_file():shutil.copyfile(r/'tools'/n,q/n)
  sources={str(p.relative_to(q/'source')):sha(p)for p in sorted((q/'source').rglob('*'))if p.is_file()}
  (q/'source-manifest.json').write_text(json.dumps(sources,indent=2)+'\n');return
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={};links=[]
 for f in sorted(q.rglob('*')):
  if f.is_symlink():links.append(dict(path=str(f.relative_to(r)),target=os.readlink(f),classification='diagnostic-test-link-not-followed'));continue
  if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
  assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();h=hashlib.sha256(raw).hexdigest();obj=folder/(h+'.gz')
  if h not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(f.relative_to(r)),bytes=len(raw),sha256=h,mode=f.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,diagnostic_links=links,dependencies=deps,rights='Original data, complete UI art, VM and full screenshots local-only. New command, no Release or default-player promotion.'))
if __name__=='__main__':main()
