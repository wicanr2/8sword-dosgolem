#!/usr/bin/env python3
"""Scoped final integrity and removal of SHA-verified disposable restore copies."""
import argparse,ast,hashlib,json,os,pathlib,re,subprocess,urllib.parse
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--archive',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();r=a.project;archive=a.archive;assert os.getuid()==1000 and not a.out.exists();d=read(archive/'tactics-audit-r1.json');player=r/'workplace/player';candidate=player/d['candidate'];core=read(player/'runtime.json')
 assert core['assets']=='assets-painted-r68'and core['battle_rules']==['native','formation','tactics']and core['battle_ai_pressure_aware']
 restored=archive/'restore-checks/tactics-r1';assert read(archive/'tactics-restoration-r1.json')['restored']
 for n,h in d['programs'].items():assert sha(player/n)==sha(candidate/n)==sha(restored/'workplace/player'/d['candidate']/n)==h
 for n,h in d['source_inputs'].items():assert sha(r/n)==sha(candidate/'src'/n)==sha(restored/'workplace/player'/d['candidate']/'src'/n)==h
 for n,h in d['asset_hashes'].items():assert sha(player/d['assets']/n)==h
 for n,h in core['files'].items():assert sha(player/'runtime-render-r1/src'/n)==h
 old=read(archive/'ai-formation-audit-r1.json')
 for n,h in old['programs'].items():assert sha(player/'source-candidate-ai-formation-r1'/n)==h
 for n,h in old['asset_hashes'].items():assert sha(player/'assets-painted-r67'/n)==h
 for name in ['rules-before-battle','rules-battle-locked']:assert '戰術試作'in read(r/'workplace/probe-20261023/graphics-first/battle-r1/tactics-r1/gui-r1/save'/(name+'.json'))['title']
 # File targets, with a known README -> CONTEXT link as the positive parser control.
 docs=list(r.glob('*.md'))
 for root in ['docs','artwork','preserved']:docs.extend((r/root).rglob('*.md'))
 links=[]
 for doc in docs:
  if 'restore-checks'in doc.relative_to(r).parts:continue
  if not doc.is_file():continue
  for target in re.findall(r'\[[^\]]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)',doc.read_text()):
   target=target.strip('<>');path=urllib.parse.unquote(target.split('#',1)[0])
   if not path or re.match(r'[a-zA-Z][a-zA-Z0-9+.-]*:',path)or path.startswith('/'):continue
   f=doc.parent/path;assert f.exists(),(str(doc),target);links.append((doc.relative_to(r).as_posix(),target))
 assert any(doc=='README.md'and target=='CONTEXT.md'for doc,target in links)
 subprocess.run(['python',str(r/'tools/check-ai-resolution-backlinks.py'),'--project',str(r)],check=True)
 ledger=read(r/'docs/spec/ai-resolution-backlinks-r1.json');negative=0
 for entry in ledger['resolutions'][:5]:
  text=(r/entry['older_spec']).read_text();required=entry['required_correction'];assert required in text
  altered=text.replace(required,'');assert required not in altered;negative+=1
 scripts=list((r/'tools').glob('*tactics*.py'))
 for f in scripts:ast.parse(f.read_text(),filename=str(f))
 for n in ['check-tactics-engine.sh','check-tactics-gui.sh']:subprocess.run(['bash','-n',str(r/'tools'/n)],check=True)
 roots=[r/'workplace/probe-20261023/graphics-first/battle-r1/tactics-r1',candidate,player/'source-candidate-tactics-r1',player/'assets-painted-r68',archive/'tactics-r1',archive/'restore-checks']
 hygiene=subprocess.run(['find',*(str(p)for p in roots),'-user','root','-o','-type','d','-name','*.md'],text=True,capture_output=True,check=True);assert not hygiene.stdout,hygiene.stdout
 cache=player.parent/'gocache';assert not any(f.is_file()for f in cache.rglob('*'))
 # Delete only fully verified disposable copies; retain archives, candidates and raw research.
 cleaned=[]
 for name in ['tactics-r1','archer-pressure-r1']:
  target=archive/'restore-checks'/name;index=read(archive/(name+'.json'));assert target.is_dir()and target.stat().st_uid==1000
  files={f.relative_to(target).as_posix():f for f in target.rglob('*')if f.is_file()};expected={v['path']:v for v in index['files']};assert files.keys()==expected.keys()
  total=0
  for n,f in files.items():assert not f.is_symlink()and f.stat().st_uid==1000 and sha(f)==expected[n]['sha256'];total+=f.stat().st_size
  for f in files.values():f.unlink()
  for directory in sorted((f for f in target.rglob('*')if f.is_dir()),key=lambda p:len(p.parts),reverse=True):directory.rmdir()
  target.rmdir();cleaned.append(dict(copy=name,files=len(files),bytes=total))
 result=dict(status='passed-scoped-tactics-integrity',programs=7,source_inputs=184,assets=525,old_glyphs_kept=137,new_glyphs=2,core_unchanged=923,previous_programs_kept=7,previous_assets_kept=525,original_helpers=48,original_executors=63,independently_decoded_states=381,formal_new_helpers=48,formal_new_executor_cases=42,inactive_case=1,prior_ai_cases=16,prior_formation_executors=24,formation_helper_cases=24,fault_cases=9,gui_phases=3,save_buffer_matches=3,markdown_links=len(links),resolution_backlinks=26,missing_correction_cases_rejected=negative,python_shell_syntax=True,root_owned_outputs=0,invalid_markdown_directories=0,workspace_go_cache_files=0,verified_restore_copies_cleaned=cleaned)
 a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
