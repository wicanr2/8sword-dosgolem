#!/usr/bin/env python3
"""Scoped player target-spells audit, permanent archive, detached verification and promotion."""
import argparse,ast,gzip,hashlib,json,os,pathlib,re,subprocess,tempfile,urllib.parse

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def equal(a,b):assert sha(a)==sha(b),(str(a),str(b))
def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['audit','archive','verify','promote','integrity']);p.add_argument('--project',type=pathlib.Path);p.add_argument('--archive',type=pathlib.Path);p.add_argument('--player',type=pathlib.Path);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();assert os.getuid()==1000 and not a.out.exists()
 if a.action=='verify':
  d=read(a.archive/'player-target-spells-r1.json');storage=a.archive/'player-target-spells-r1';checked=set()
  for v in d['files']:
   n=pathlib.PurePosixPath(v['path']);assert not n.is_absolute()and '..'not in n.parts
   obj=d['objects'][v['sha256']];f=storage/obj['file'];assert sha(f)==obj['stored_sha256'];raw=gzip.decompress(f.read_bytes());assert hashlib.sha256(raw).hexdigest()==v['sha256']and len(raw)==v['bytes'];checked.add(v['sha256'])
  result=dict(status='passed-detached-player-target-spells-archive',files=len(d['files']),objects=len(checked),workplace_required=False,index_sha256=sha(a.archive/'player-target-spells-r1.json'))
 else:
  r=a.project;assert r;q=r/'workplace/probe-20261023/graphics-first/battle-r1/player-spells-r1/target-spells-r1';player=a.player or r/'workplace/player';candidate=player/'source-candidate-player-target-spells-r1';previous=read(r/'preserved/player-exorcism-audit-r1.json')
  if a.action=='integrity':
   audit=read(a.archive/'player-target-spells-audit-r1.json');promotion=read(a.archive/'player-target-spells-promotion-r1.json');assert promotion['status']=='promoted-scoped-player-target-spells'and promotion['audit_sha256']==sha(a.archive/'player-target-spells-audit-r1.json')
   for n,h in audit['programs'].items():assert sha(player/n)==sha(candidate/n)==h
   for n,h in audit['source_inputs'].items():assert sha(r/n)==sha(candidate/'src'/n)==h
   for n,h in audit['previous_programs'].items():assert sha(player/'source-candidate-player-exorcism-r2'/n)==h
   for n,h in audit['asset_hashes'].items():assert sha(player/'assets-painted-r68'/n)==h
   runtime=read(player/'runtime.json');assert len(runtime['files'])==923 and runtime['application_source_inputs']==188 and runtime['battle_vfx']=='B-enemy-player-fireball-thunder-exorcism-assassination-half'
   for n,h in runtime['files'].items():assert sha(player/'runtime-render-r1/src'/n)==h
   verification=read(a.archive/'player-target-spells-verification-r1.json');assert verification['workplace_required']is False and verification['index_sha256']==sha(a.archive/'player-target-spells-r1.json')
   art=read(r/'artwork/manifest.json');assert len(art['files'])==1040
   for row in art['files']:assert sha(r/'artwork'/row['path'])==row['sha256']
   checker=r/'tools/check-ai-resolution-backlinks.py';subprocess.run(['python',str(checker),'--project',str(r)],check=True);ledger=read(r/'docs/spec/ai-resolution-backlinks-r1.json');extra=next(v for v in ledger['resolutions']if v['original_address']=='0x21C36')['supplemental_resolutions'];player_extra=ledger['player_resolutions'][0]['supplemental_resolutions'];assert len(ledger['resolutions'])==26 and len(extra)==1 and len(ledger['player_resolutions'])==1 and len(player_extra)==3
   with tempfile.TemporaryDirectory(prefix='player-fire-backlinks-')as name:
    tmp=pathlib.Path(name);paths={'docs/spec/ai-resolution-backlinks-r1.json'}
    for row in ledger['resolutions']+extra+ledger['player_resolutions']+player_extra:
     paths.update(row[k]for k in ['evidence','older_spec'])
     if 'receipt'in row:paths.add(row['receipt'])
    for n in paths:dest=tmp/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((r/n).read_bytes())
    for row in ledger['resolutions'][:5]+extra+ledger['player_resolutions']+player_extra:
     f=tmp/row['older_spec'];text=f.read_text();assert row['required_correction']in text;f.write_text(text.replace(row['required_correction'],'REMOVED-FOR-NEGATIVE-TEST'));failed=subprocess.run(['python',str(checker),'--project',str(tmp)],capture_output=True);assert failed.returncode!=0;f.write_text(text)
   docs=list(r.glob('*.md'))
   for folder in ['docs','artwork','preserved']:docs.extend((r/folder).rglob('*.md'))
   links=[]
   for doc in docs:
    if not doc.is_file()or'restore-checks'in doc.relative_to(r).parts:continue
    for target in re.findall(r'\[[^\]]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)',doc.read_text()):
     path=urllib.parse.unquote(target.strip('<>').split('#',1)[0])
     if not path or re.match(r'[a-zA-Z][a-zA-Z0-9+.-]*:',path)or path.startswith('/'):continue
     dest=doc.parent/path;assert dest.exists()or dest.resolve()==(r/'preserved'/a.out.name).resolve(),(str(doc),target);links.append((doc.relative_to(r).as_posix(),target))
   assert('README.md','CONTEXT.md')in links
   for n in ['finalize-player-target-spells.py','prepare-player-fireball.py','audit-player-target-spells.py','probe-player-spells.go']:
    if n.endswith('.py'):ast.parse((r/'tools'/n).read_text())
   subprocess.run(['bash','-n',str(r/'tools/check-player-fire-gui.sh')],check=True)
   for root in [q,candidate,a.archive/'player-target-spells-r1']:
    hygiene=subprocess.run(['find',str(root),'-user','root','-o','-type','d','-name','*.md'],capture_output=True,text=True,check=True);assert not hygiene.stdout,hygiene.stdout
   assert not any(f.is_file()for f in(r/'workplace/gocache').rglob('*'))
   result=dict(status='passed-scoped-player-target-spells-integrity',production_programs=7,source_count=188,assets_unchanged=525,core_unchanged=923,previous_programs_preserved=7,original_executor_cases=11,original_effect_calls=14,guards=19,actual_draws_independently_rebuilt=2,catalog_names=16,permanent_files=verification['files'],permanent_objects=verification['objects'],approved_artwork_files=1040,original_AI_resolution_keys=26,enemy_supplemental_backlinks=1,player_resolution_keys=1,player_supplemental_backlinks=3,missing_correction_cases_rejected=10,markdown_links=len(links),root_owned_outputs=0,invalid_markdown_directories=0,workspace_go_cache_files=0,limits=audit['limits'])
  elif a.action=='archive':
   audit=q/'engine-audit-r1.json';assert read(audit)['status']=='passed-scoped-player-target-spells';index=a.archive/'player-target-spells-r1.json';storage=a.archive/'player-target-spells-r1';assert not index.exists()and not storage.exists();selected=[]
   for folder in [q,candidate]:selected.extend(f for f in folder.rglob('*')if f.is_file())
   for n in ['probe-player-spells.go','audit-player-target-spells.py','prepare-player-fireball.py','player-fire-fixture.go','check-player-fire-gui.sh','finalize-player-target-spells.py','prepare-vfx-gui.py','vfx-gui-probe.go','audit-vfx-engine.py']:selected.append(r/'tools'/n)
   selected.append(r/'docs/spec/030-battle-expansion-proposal.md');storage.mkdir();files=[];objects={}
   selected.extend(r/n for n in ['docs/spec/ai-resolution-backlinks-r1.json','docs/spec/027-battle-pon-effects.md','tools/check-ai-resolution-backlinks.py'])
   for f in sorted(set(selected)):
    assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();h=hashlib.sha256(raw).hexdigest()
    if h not in objects:
     blob=gzip.compress(raw,compresslevel=6,mtime=0);name=h+'.gzip';(storage/name).write_bytes(blob);objects[h]=dict(file=name,stored_sha256=hashlib.sha256(blob).hexdigest(),stored_bytes=len(blob))
    files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(raw),mode=f.stat().st_mode&0o777))
   data=dict(schema=1,status='preserved',files=files,objects=objects,audit_sha256=sha(audit),dependencies=['Prior player exorcism uses preserved/player-exorcism-r1.json.','Prior player thunder and fixed controls use preserved/player-thunder-r1.json; earlier IDA uses player-fireball-r1.json.','Original PAM/core/modules use preserved/catalog.json.gz.','r68 uses completion-r65 and tactics catalogs.','Approved B artwork uses artwork/manifest.json; no new generated art.']);index.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');result=dict(status='preserved-player-target-spells',files=len(files),objects=len(objects),stored_bytes=sum(o['stored_bytes']for o in objects.values()))
  elif a.action=='promote':
   audit=read(q/'engine-audit-r1.json');assert audit['status']=='passed-scoped-player-target-spells';verification=read(a.archive/'player-target-spells-verification-r1.json');assert verification['status']=='passed-detached-player-target-spells-archive'and verification['index_sha256']==sha(a.archive/'player-target-spells-r1.json');assert read(a.archive/'player-target-spells-r1.json')['audit_sha256']==sha(q/'engine-audit-r1.json')
   for n,h in audit['previous_programs'].items():assert sha(player/n)==h
   for n,h in audit['source_inputs'].items():assert sha(r/n)==sha(candidate/'src'/n)==h
   staged={}
   try:
    for n,h in audit['programs'].items():
     assert sha(candidate/n)==h;temp=player/('.player-fire-'+n+'.tmp');assert not temp.exists();os.link(candidate/n,temp);staged[n]=temp
    runtime=read(candidate/'runtime.json');runtime.update(production=True,application_source_inputs=188,application_spec='docs/spec/030-battle-expansion-proposal.md',battle_vfx='B-enemy-player-fireball-thunder-exorcism-assassination-half',assets='assets-painted-r68');metadata={n:(candidate/n).read_bytes()for n in ['build-inputs.sha256','build-source-checks.log','build-go-version.txt']};metadata['runtime.json']=(json.dumps(runtime,indent=2)+'\n').encode();metadata['build-outputs.sha256']=''.join(f'{h}  /out/{n}\n'for n,h in audit['programs'].items()).encode()
    for n,b in metadata.items():temp=player/('.player-fire-'+n+'.tmp');assert not temp.exists();temp.write_bytes(b);staged[n]=temp
    for n,temp in staged.items():os.replace(temp,player/n)
   finally:
    for temp in staged.values():
     if temp.exists():temp.unlink()
   for n,h in audit['programs'].items():assert sha(player/n)==h
   result=dict(status='promoted-scoped-player-target-spells',audit_sha256=sha(q/'engine-audit-r1.json'),programs=audit['programs'],source_count=188,core_files=923,assets='r68',asset_files=525)
  else:
   prep=read(candidate/'preparation.json');assert prep['source_count']==len(prep['source_inputs'])==188
   for n,h in prep['source_inputs'].items():assert sha(r/n)==sha(candidate/'src'/n)==h
   for n,h in previous['programs'].items():assert sha(player/n)==sha(player/'source-candidate-player-exorcism-r2'/n)==h
   for n,h in previous['asset_hashes'].items():assert sha(player/'assets-painted-r68'/n)==h
   core=read(player/'runtime.json');assert len(core['files'])==923
   for n,h in core['files'].items():assert sha(player/'runtime-render-r1/src'/n)==h
   programs={n:sha(candidate/n)for n in previous['programs']};assert len(programs)==7
   log=(q/'tests-r1.log').read_text();assert '\nPASS\n'in log and 'FAIL'not in log and 'SKIP'not in log and not(q/'vet-r1.log').read_text();assert(candidate/'build-source-checks.log').read_text().count(': OK')==188 and 'go1.24.13'in(candidate/'build-go-version.txt').read_text()
   for name in ['special0-choice','special2-choice','special5-empty-original','player-fireball','player-thunder-mixed','player-thunder-sparse','player-exorcism-ghost','player-exorcism-ordinary','player-assassination-high','player-half-even','player-half-odd']:
    ref=r/'workplace/probe-20261023/graphics-first/battle-r1'/('ai-policy-extra-r2'if name.startswith('special5')else'ai-policy-r1')/name/'baseline';expected=1
    if name=='player-fireball':ref=q.parent/'cast-r5/observed'
    if name.startswith('player-thunder-'):ref=q.parent/'thunder-r1'/name.removeprefix('player-thunder-')/'observed';expected=4 if name.endswith('mixed')else 1
    if name=='player-thunder-sparse':ref=q.parent/'thunder-r1/sparse-resumed'
    if name.startswith('player-exorcism-'):ref=q.parent/'exorcism-r1/original-r4'/name.removeprefix('player-exorcism-')/'observed'
    if name.startswith('player-assassination-')or name.startswith('player-half-'):ref=q/'original-r1'/name.removeprefix('player-')/'observed'
    actual=q/'runtime-r1'/name;equal(actual/'final.state',ref/'final.state');v=read(actual/'receipt.json');s=v['battle_vfx'];assert v['full_original_state_equal']and v['frame_guest_pure']and v['synthetic_test_base']and s['Started']==s['Completed']==expected and s['SourceCommits']==4*expected and s['PONCommits']==12*expected and not s['Active']
    for phase in ['flight','impact']:equal(actual/(phase+'-before.state'),actual/(phase+'-after.state'))
   for name in ['code','selector','mapping','geometry','player-code','player-selector','player-caster','player-geometry','thunder-code','thunder-caller','thunder-selector','thunder-geometry','exorcism-code','exorcism-caller','exorcism-selector','exorcism-geometry','assassination-caller','half-caller','player-unbound-selector']:equal(q/'runtime-r1'/('guard-'+name+'-before.state'),q/'runtime-r1'/('guard-'+name+'-after.state'))
   gui=q/'gui-r1';s=read(gui/'gui-final.json');assert s['closed']and not s['exited']and s['hd']and s['source_renderer']and not s['owned_render_fault']and not s['toolbar_error']and not s['unimplemented'];assert read(gui/'gui-input-receipt.json')['status']=='passed-input-path';v=s['battle_vfx'];assert v['Bound']and v['Completed']>=1 and not v['Active'];assert s['research_vfx']['fixture']and s['research_vfx']['mutations']and s['research_vfx']['forced_selectors']==0
   probe=s['research_vfx'];assert probe['player_spell_complete']and probe['player_expected_effects']==1 and v['Started']==v['Completed']==probe['player_expected_effects']and v['Cancelled']==0 and v['SourceCommits']==v['Completed']*4 and v['PONCommits']==v['Completed']*12
   ns={'__name__':'vfx_audit_helpers'};exec(compile((r/'tools/audit-vfx-engine.py').read_text(),'audit-vfx-engine.py','exec'),ns);draws=[ns['draw_audit'](gui,phase)for phase in ['flight','impact']]
   for phase in ['flight','impact']:
    m=read(gui/'vfx-draw'/(phase+'.json'));assert m['vfx']['Source'][0]<m['vfx']['Target'][0]
   private=read(q/'gui-build-r1/preparation.json');assert len(private['base_inputs'])==188 and set(private['changed'])=={'cmd/8sword/main.go','internal/eightsword/battle_vfx.go','internal/eightsword/vfx_gui_probe.go'}
   for n,h in private['base_inputs'].items():
    assert sha(player/'source-candidate-player-target-spells-r1/src'/n)==h
    if not n.endswith('_test.go'):assert sha(candidate/'src'/n)==h
   for n,h in private['diagnostic_inputs'].items():assert sha(q/'gui-build-r1/src'/n)==h
   research=read(q/'research-audit-r1.json');assert research['status']=='passed-scoped-player-target-spells-research'and len(research['cases'])==6
   for row in research['cases']:
    for phase in ['control','observed']:assert sha(q/'original-r1'/row['case']/phase/'final.state')==row['final_state_sha256']
   limit=previous['snapshot_resume_limit']
   for f in (r/'tools').glob('*player*fire*.py'):ast.parse(f.read_text())
   result=dict(schema=1,status='passed-scoped-player-target-spells',source_count=188,source_inputs=prep['source_inputs'],changed_sources=prep['changed'],programs=programs,previous_programs=previous['programs'],core_files=923,assets='assets-painted-r68',asset_files=525,asset_hashes=previous['asset_hashes'],original_executor_cases=11,continuous_control_cases=10,resumed_control_cases=1,original_effect_calls=14,guards=19,real_draws=draws,gui_effects=probe['player_expected_effects'],gui_wrapper_complete=True,gui_final_state_sha256=sha(gui/'gui-final.state'),research_audit_sha256=sha(q/'research-audit-r1.json'),snapshot_resume_limit=limit,limits=['Controlled rear caster/learned flag/charges; half GUI and new Engine cases, not natural learning. Assassination failed die not dynamically sampled.','Sparse case matches unhooked original resume from identical snapshot; continuous snapshot equivalence remains unknown. No core change or seed reroll.','Five player battle effects presented; selectors4/6/7 and eight map effects remain open.','No game rules, save fields, original display path, assets or core changes.','Normal save/load uses prior B acceptance; no new save GUI claim.'])
 a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k in ['status','source_count','files','objects','stored_bytes','real_draws']},ensure_ascii=False))
if __name__=='__main__':main()
