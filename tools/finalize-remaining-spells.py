"""Audit, preserve, verify without workplace, then atomically promote ten Go cues."""
import argparse,ast,gzip,hashlib,json,os,pathlib,re,subprocess,urllib.parse
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['audit','archive','verify','promote','integrity']);p.add_argument('--project',type=pathlib.Path);p.add_argument('--archive',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();assert os.getuid()==1000 and not a.out.exists()
 if a.action=='verify':
  index=a.archive/'remaining-spells-r1.json';d=read(index);objects=set()
  for row in d['files']:
   n=pathlib.PurePosixPath(row['path']);assert not n.is_absolute()and '..'not in n.parts;obj=d['objects'][row['sha256']];f=a.archive/'remaining-spells-r1'/obj['file'];assert sha(f)==obj['stored_sha256'];raw=gzip.decompress(f.read_bytes());assert hashlib.sha256(raw).hexdigest()==row['sha256']and len(raw)==row['bytes'];objects.add(row['sha256'])
  result=dict(status='passed-detached-remaining-spells',files=len(d['files']),objects=len(objects),index_sha256=sha(index),workplace_required=False)
 else:
  r=a.project;q=r/'workplace/probe-20261023/graphics-first/battle-r1/player-spells-r1/remaining-r1';player=r/'workplace/player';candidate=player/'source-candidate-remaining-spells-r2';old=read(r/'preserved/player-quake-audit-r1.json')
  if a.action=='audit':
   prep=read(candidate/'preparation.json');inputs=prep['source_inputs'];assert len(inputs)==193 and prep['source_count']==193
   for n,h in inputs.items():assert sha(r/n)==sha(candidate/'src'/n)==h
   for n,h in old['programs'].items():assert sha(player/n)==sha(player/'source-candidate-player-quake-r4'/n)==h
   assert 'go1.24.13'in(candidate/'build-go-version.txt').read_text();programs={n:sha(candidate/n)for n in old['programs']};assert len(programs)==7
   research=read(q/'research-audit-r1.json');presentation=read(q/'presentation-audit-r2.json');assert research['status']=='passed-remaining-ten-spell-research'and len(research['cases'])==10;assert presentation['status']=='passed-independent-remaining-presentation'and presentation['actual_window_draws']==4 and presentation['normal_map_frames']==8
   log=(q/'tests-r2.log').read_text();assert 'PASS'in log and 'FAIL'not in log and 'SKIP'not in log and not(q/'vet-r2.log').read_text().strip();assert 'pcm[0] != pcm[1]'in(candidate/'src/internal/eightsword/spell_cues_test.go').read_text()
   cases=[]
   for kind in range(10):
    name='map-'+str(kind)if kind<8 else ['freeze','clone'][kind-8];folder=q/'tests-r2'/('cue-'+name);d=read(folder/'receipt.json');assert d['full_state_equal']and d['same_snapshot_control']and d['cue']['Started']>0;assert sha(folder/'final-0.state')==sha(folder/'final-1.state');assert sha(folder/'frame-before.state')==sha(folder/'frame-after.state');cases.append(d)
   for name in ['code','selector','caller','charge','learned']:assert sha(q/'tests-r2'/('guard-cue-'+name+'-before.state'))==sha(q/'tests-r2'/('guard-cue-'+name+'-after.state'))
   for folder in ['gui-build-r1','gui-freeze-build-r1','normal-build-r2']:
    d=read(q/folder/'preparation.json');assert d['base_inputs']==inputs
    for n,h in d['diagnostic_inputs'].items():assert sha(q/folder/'src'/n)==h
   runtime=read(player/'runtime.json');assert len(runtime['files'])==923
   for n,h in runtime['files'].items():assert sha(player/'runtime-render-r1/src'/n)==h
   for n,h in old['asset_hashes'].items():assert sha(player/'assets-painted-r68'/n)==h
   result=dict(schema=1,status='passed-remaining-ten-spells',source_count=193,source_inputs=inputs,changed_sources=prep['changed'],programs=programs,previous_programs=old['programs'],core_files=runtime['files'],asset_hashes=old['asset_hashes'],asset_files=525,research_sha256=sha(q/'research-audit-r1.json'),presentation_sha256=sha(q/'presentation-audit-r2.json'),new_original_cases=cases,guards=5,normal_map_frames=8,actual_draws=4,limits=['Ten new presentation cues; original outcomes/charges/RNG/timing/save and original mode unchanged.','All ten use paired same-snapshot native controls; five match prior continuous references, five map snapshot/continuous equivalences remain unknown. Prior thunder/quake sparse limitations remain.','Resources/learned fixtures, not natural acquisition. Original bridge rejection/teleport cancellation may still consume a charge. Cue means dispatch, not success.','No new save/load, balance, core repair or all-game fidelity claim.'])
  elif a.action=='archive':
   audit=q/'engine-audit-r1.json';assert read(audit)['status']=='passed-remaining-ten-spells';index=a.archive/'remaining-spells-r1.json';storage=a.archive/'remaining-spells-r1';assert not index.exists()and not storage.exists();selected=[]
   for folder in [q,candidate,player/'source-candidate-remaining-spells-r1']:selected.extend(f for f in folder.rglob('*')if f.is_file())
   selected.extend(r/'tools'/n for n in ['export-remaining-spells-ida.py','probe-remaining-map-spells.go','probe-player-spells.go','audit-remaining-spells.py','prepare-remaining-spells.py','prepare-remaining-gui.py','prepare-remaining-normal.py','research-remaining-spells_test.go','audit-remaining-presentation.py','finalize-remaining-spells.py','player-fire-fixture.go','check-player-fire-gui.sh'])
   selected.extend(r/n for n in ['docs/spec/030-battle-expansion-proposal.md','docs/spec/027-battle-pon-effects.md','docs/spec/ai-resolution-backlinks-r1.json']);storage.mkdir();files=[];objects={}
   for f in sorted(set(selected)):
    assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();h=hashlib.sha256(raw).hexdigest()
    if h not in objects:
     blob=gzip.compress(raw,compresslevel=6,mtime=0);name=h+'.gzip';(storage/name).write_bytes(blob);objects[h]=dict(file=name,stored_sha256=hashlib.sha256(blob).hexdigest(),stored_bytes=len(blob))
    files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(raw),mode=f.stat().st_mode&0o777))
   index.write_text(json.dumps(dict(schema=1,status='preserved',files=files,objects=objects,audit_sha256=sha(audit),dependencies=['preserved/player-quake-r1.json and earlier catalogs preserve fixed originals, modules and 923 core.','r68 asset hashes/old program hashes in remaining-spells-audit-r1.json.','artwork/manifest.json preserves all 1040 approved artwork files.','Current Git documents supersede historical snapshot documents.']),indent=2)+'\n');result=dict(status='preserved-remaining-ten-spells',files=len(files),objects=len(objects),stored_bytes=sum(v['stored_bytes']for v in objects.values()))
  elif a.action=='promote':
   audit=read(q/'engine-audit-r1.json');verification=read(a.archive/'remaining-spells-verification-r1.json');assert audit['status']=='passed-remaining-ten-spells'and verification['workplace_required']is False and verification['index_sha256']==sha(a.archive/'remaining-spells-r1.json');assert read(a.archive/'remaining-spells-r1.json')['audit_sha256']==sha(q/'engine-audit-r1.json')
   for n,h in audit['previous_programs'].items():assert sha(player/n)==h
   for n,h in audit['source_inputs'].items():assert sha(r/n)==sha(candidate/'src'/n)==h
   staged={}
   try:
    for n,h in audit['programs'].items():
     assert sha(candidate/n)==h;dest=player/('.remaining-'+n+'.tmp');assert not dest.exists();os.link(candidate/n,dest);staged[n]=dest
    runtime=read(candidate/'runtime.json');runtime.update(production=True,application_source_inputs=193,application_source_candidate='source-candidate-remaining-spells-r2',application_spec='docs/spec/030-battle-expansion-proposal.md',battle_vfx='B-enemy-player-complete-spell-cues');temp=player/'.remaining-runtime.tmp';assert not temp.exists();temp.write_text(json.dumps(runtime,indent=2)+'\n')
    for n,f in staged.items():os.replace(f,player/n)
    os.replace(temp,player/'runtime.json')
   finally:
    for f in staged.values():f.unlink(missing_ok=True)
   result=dict(status='promoted-remaining-ten-spells',source_count=193,programs=audit['programs'],audit_sha256=sha(q/'engine-audit-r1.json'),previous_preserved=True,assets_unchanged=525,core_unchanged=923)
  else:
   audit=read(a.archive/'remaining-spells-audit-r1.json');promotion=read(a.archive/'remaining-spells-promotion-r1.json');assert promotion['audit_sha256']==sha(a.archive/'remaining-spells-audit-r1.json')and promotion['status']=='promoted-remaining-ten-spells'
   for n,h in audit['source_inputs'].items():assert sha(r/n)==sha(candidate/'src'/n)==h
   for n,h in audit['programs'].items():assert sha(player/n)==sha(candidate/n)==h
   for n,h in audit['previous_programs'].items():assert sha(player/'source-candidate-player-quake-r4'/n)==h
   for n,h in audit['core_files'].items():assert sha(player/'runtime-render-r1/src'/n)==h
   for n,h in audit['asset_hashes'].items():assert sha(player/'assets-painted-r68'/n)==h
   art=read(r/'artwork/manifest.json');assert len(art['files'])==1040
   for v in art['files']:assert sha(r/'artwork'/v['path'])==v['sha256']
   subprocess.run(['python',str(r/'tools/check-ai-resolution-backlinks.py'),'--project',str(r)],check=True)
   links=0
   for doc in list(r.glob('*.md'))+[p for folder in ['docs','artwork','preserved']for p in(r/folder).rglob('*.md')]:
    for target in re.findall(r'\[[^\]]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)',doc.read_text()):
     path=urllib.parse.unquote(target.strip('<>').split('#',1)[0])
     if not path or re.match(r'[a-zA-Z][a-zA-Z0-9+.-]*:',path)or path.startswith('/'):continue
     dest=doc.parent/path;assert dest.exists()or dest.resolve()==a.out.resolve(),(doc,target);links+=1
   for f in(r/'tools').glob('*remaining*.py'):ast.parse(f.read_text())
   subprocess.run(['bash','-n',str(r/'tools/check-player-fire-gui.sh')],check=True)
   for root in [q,candidate,a.archive/'remaining-spells-r1']:
    check=subprocess.run(['find',str(root),'-user','root','-o','-type','d','-name','*.md'],capture_output=True,text=True,check=True);assert not check.stdout
   assert not any(f.is_file()for f in(r/'workplace/gocache').rglob('*'));v=read(a.archive/'remaining-spells-verification-r1.json');assert v['index_sha256']==sha(a.archive/'remaining-spells-r1.json')
   result=dict(status='passed-remaining-ten-spells-integrity',source_count=193,programs=7,core_unchanged=923,assets_unchanged=525,artwork_unchanged=1040,permanent_files=v['files'],permanent_objects=v['objects'],markdown_links=links,root_owned_outputs=0,workspace_go_cache_files=0,limits=audit['limits'])
 a.out.write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
if __name__=='__main__':main()
