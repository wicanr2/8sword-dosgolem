#!/usr/bin/env python3
"""Approved A: isolated original shops plus Go reinforcement page."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/reinforcement-camps-r1'
BATCH='reinforcement-camps-r1';PARENT='sword-guards-r1'
NEW=['reinforcement-camps.go','reinforcement-ui.go','reinforcement-camps_test.go','prepare-reinforcement-camps.py','check-reinforcement-camps.py','audit-reinforcement-camps.py','reinforcement-camps.sh']
PATCHED=['research-native-checkpoint.go','research-camp-stock-save.go','research-paired-progress.go','research-monthly.go','world-army-review_main.go']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def helper(r):
 s=importlib.util.spec_from_file_location('h',r/'tools/prepare-owned-army-ui.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def replace(p,a,b):
 s=p.read_text();assert s.count(a)==1,(p,a,s.count(a));p.write_text(s.replace(a,b))
def patch(src):
 p=src/'tools/research-camp-stock-save.go'
 replace(p,'const campSchema = "eightsword-owned-world-save/4"','const campSchema = "eightsword-owned-world-save/5"\nconst legacyCampSchema = "eightsword-owned-world-save/4"')
 replace(p,'const campIntent = "eightsword-pair-intent/4"','const campIntent = "eightsword-pair-intent/5"')
 replace(p,'v.Schema != campSchema ||','(v.Schema != campSchema && v.Schema != legacyCampSchema) ||')
 replace(p,'if v.Resume == nil {','if v.Schema==legacyCampSchema && len(reinforcementOffers(v.World.Army))>0{return false}\n if v.Resume == nil {')
 replace(p,'prev.Schema != campSchema && len(offers) == 0','prev.Schema != campSchema && prev.Schema != legacyCampSchema && len(offers) == 0 && len(reinforcementOffers(w.Army))==0')
 replace(p,'old, e := campOffers(b.World.Army)','if changed,e:=checkReinforcementTransition(b,a,c);changed||e!=nil{return e}\n old, e := campOffers(b.World.Army)')
 replace(p,'if v.Schema == campSchema {','if v.Schema == campSchema || v.Schema==legacyCampSchema {')
 p=src/'tools/research-native-checkpoint.go'
 replace(p,'if s.Schema==campSchema {return validCampEnvelope(s)}','if s.Schema==campSchema || s.Schema==legacyCampSchema {return validCampEnvelope(s)}')
 replace(p,'if s.Schema==campSchema{return campIntent}','if s.Schema==campSchema || s.Schema==legacyCampSchema{return campIntent}')
 p=src/'tools/research-paired-progress.go'
 replace(p,'if values != pairWorldResources(saved.World) {','if e=validateReinforcements(b.Native,saved.World.Army,c);e!=nil{return empty,e}\n if values != pairWorldResources(saved.World) {')
 p=src/'tools/research-monthly.go'
 replace(p,'w.Army.Gold = budget.After','if e=refillReinforcements(&w.Army,before.Bytes.Native,c,pam);e!=nil{return w,budget,nil,e}\n w.Army.Gold = budget.After')
 p=src/'tools/world-army-review_main.go'
 replace(p,'if summonCurrent!=nil','if reinforcementCurrent!=nil && reinforcementCurrent.Port.ShopOpen {if reinforcementCurrent.Active{return "reinforcements"};return "recruit"}\n if summonCurrent!=nil')
 s=p.read_text().replace('encounterGuestKey(g,','reinforcementGuestKey(g,').replace('return advanceSummonUI(g)','return advanceReinforcementUI(g)');p.write_text(s)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','archive','verify']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   o=d['objects'][f['sha256']];p=a.archive/BATCH/o['file'];assert sha(p)==o['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-reinforcement-camps',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL;m=helper(r);deps=m.dependencies(r)
 if a.action=='prepare':
  assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir();d=read(r/'preserved'/f'{PARENT}.json')
  for f in d['files']:
   rel=f['path'].split('/'+PARENT+'/',1)[1]
   if not(rel.startswith(('go-src/','inputs/','ui-assets/'))or rel in ['probe.mod','probe.sum','xcheck','sword-guards-execution-r1.json']):continue
   t=q/rel;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(m.stored(r,PARENT,'/'+PARENT+'/'+rel));t.chmod(f['mode'])
  write(q/'baseline.json',deps)
 else:assert deps==read(q/'baseline.json')
 if a.action in ['prepare','freeze']:
  for n in PATCHED:(q/'go-src/tools'/n).write_bytes(m.stored(r,PARENT,'/'+PARENT+'/go-src/tools/'+n))
  patch(q/'go-src')
  for n in NEW:
   if (r/'tools'/n).is_file():shutil.copyfile(r/'tools'/n,q/'go-src/tools'/n)
  old=read(q/'sword-guards-execution-r1.json')['ui_build'];ui=old.replace('/out/sword-guards-ui','/out/reinforcement-ui')+' tools/reinforcement-camps.go tools/reinforcement-ui.go'
  (q/'execution-r1.json').write_text(json.dumps(dict(ui_build=ui,ui_test=ui.replace('go build','go test').replace('-o /out/reinforcement-ui ','')+' tools/reinforcement-camps_test.go -run ^TestReinforcementCamps$ -count=1'),indent=2)+'\n');return
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for f in sorted(q.rglob('*')):
  if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
  assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();h=hashlib.sha256(raw).hexdigest();obj=folder/(h+'.gz')
  if h not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(raw),mode=f.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Original inputs, complete artwork, VM and full frames local-only. Isolated A candidate, no formal promotion.'))
if __name__=='__main__':main()
