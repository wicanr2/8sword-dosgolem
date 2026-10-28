#!/usr/bin/env python3
"""030: independent acceptance of optional target AI, normal GUI and save compatibility."""
import argparse,hashlib,json,os,pathlib
from PIL import Image
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--promotion',type=pathlib.Path);a=p.parse_args();r=a.project;b=r/'workplace/probe-20261023/graphics-first/battle-r1';q=b/'ai-engine-r5';candidate=r/'workplace/player/source-candidate-ai-r5';assert os.getuid()==1000 and not a.out.exists()
 prep=read(q/'preparation.json');assert prep['source_count']==181 and prep['core_files']==923
 for name,digest in prep['source_inputs'].items():assert sha(r/name)==sha(candidate/'src'/name)==digest
 previous=read(r/'preserved/completion-r65-audit.json');assert prep['previous_programs']==previous['programs']
 for name,digest in previous['programs'].items():
  if a.promotion:
   promotion=read(a.promotion);assert promotion['status']=='promoted-scoped-030-optional-target-AI' and sha(r/'workplace/player'/name)==promotion['programs'][name] and sha(r/'workplace/player/source-candidate-completion-r4'/name)==digest
  else:assert sha(r/'workplace/player'/name)==digest
 for name,digest in previous['asset_hashes'].items():assert sha(r/'workplace/player/assets-painted-r65'/name)==digest
 core=read(r/'workplace/player/runtime.json');assert core['total_inputs']==923
 for name,digest in core['files'].items():assert sha(r/'workplace/player/runtime-render-r1/src'/name)==digest
 old_sources=read(b/'ai-engine-r4/preparation.json')['source_inputs'];assert {n for n in old_sources if old_sources[n]!=prep['source_inputs'][n]}=={'internal/eightsword/battle_ai_runtime_test.go'}
 assert 'PASS' in (q/'tests-special5-r5.log').read_text() and 'FAIL' not in (q/'tests-special5-r5.log').read_text()
 assert 'PASS' in (q/'tests-contract-r5.log').read_text() and 'FAIL' not in (q/'tests-contract-r5.log').read_text() and not (q/'vet-r5.log').read_text()
 states=[];names=['normal-locked','normal-choice','normal-rear-only','front-ranged-mixed','rear-ranged-mixed','special0-choice','special2-choice','special5-empty-original']
 for name in names:
  revision=5 if name=='special5-empty-original' else 4;runtime=b/f'ai-engine-r{revision}'/f'runtime-r{revision}'
  for mode,ref in [('native','baseline'),('target','override')]:
   actual=runtime/(name+'-'+mode);receipt=read(actual/'receipt.json');source=b/('ai-policy-extra-r2' if revision==5 else 'ai-policy-r1')/name/ref
   assert receipt['mode']==mode and receipt['same_after_decision_state'] and receipt['same_final_state']
   for file in ['after-decision.state','final.state']:assert sha(actual/file)==sha(source/file)
   info=receipt['battle_ai'];assert info['Mode']==mode and info['Fault'] is None
   if mode=='native':assert not info['Bound'] and info['Decisions']==info['Changed']==0
   else:assert info['Bound'] and info['Decisions']==1 and len(info['Recent'])==1
   states.append(dict(case=name,mode=mode,source_revision=revision,final_state_sha256=sha(actual/'final.state')))
 for fault in ['entry-bytes','mapping','stack']:
  assert sha(q/f'runtime-r5/fault-{fault}-before.state')==sha(q/f'runtime-r5/fault-{fault}-after.state')
 old=read(q/'cli-old/receipt.json');native=read(q/'cli-native/receipt.json')
 for k,v in old.items():assert native[k]==v,k
 assert native['battle_ai']['Mode']=='native' and not native['battle_ai']['Bound'] and native['battle_ai']['Decisions']==0
 assert sha(q/'cli-old/final.state')==sha(q/'cli-native/final.state')
 assert Image.open(q/'cli-old/final.png').convert('RGBA').tobytes()==Image.open(q/'cli-native/final.png').convert('RGBA').tobytes()
 gui=q/'gui-r3';phases={}
 for phase,mode,label in [('save','target','策略 AI'),('reload','native','原版 AI')]:
  root=gui/phase;st=read(root/'gui-final.json');assert st['closed'] and st['hd'] and st['source_renderer'] and st['owned_render_fault'] is None and st['unimplemented']==[]
  if phase=='save':assert st['exited'] and st['exit_code']==0
  ai=st['battle_ai'];assert ai['Mode']==mode and ai['Fault'] is None and len(ai['Recent'] or [])<=32
  title=read(root/'window-title.json');assert label in title['title']
  # X11 can expose the title before the first periodic status file exists.
  if title['battle_ai'] is not None:assert title['battle_ai']['Mode']==mode
  assert read(root/'gui-input-receipt.json')['flow']==phase
  if phase=='save':assert ai['Bound'] and ai['Decisions']>0 and (root/'battle-ai-decision.json').is_file()
  else:assert not ai['Bound'] and ai['Decisions']==ai['Changed']==0
  assert 'panic:' not in (root/'player.log').read_text() and 'panic:' not in (root/'gui-check.log').read_text()
  phases[phase]=dict(mode=mode,decisions=ai['Decisions'],changed=ai['Changed'],draws=st['presented_frames'],final_state_sha256=sha(root/'gui-final.state'),window_title=title['title'])
 saved=gui/'scratch/gamedata.ay';assert saved.stat().st_size==2987 and sha(saved)==read(gui/'save/saved.json')['sha256']
 for phase in ['save','reload']:assert saved.read_bytes()==(gui/phase/'snapshot-readonly/save-buffer-9e000.bin').read_bytes()
 programs={name:sha(candidate/name) for name in previous['programs']};assert len(programs)==7
 for file in ['build-inputs.sha256','build-outputs.sha256','build-source-checks.log','build-go-version.txt','runtime.json']:assert (candidate/file).is_file()
 assert 'go1.24.13' in (candidate/'build-go-version.txt').read_text()
 report=dict(schema=1,status='PASS-scoped-030-optional-target-AI',post_promotion=bool(a.promotion),candidate=candidate.name,source_input_count=181,source_inputs=prep['source_inputs'],core_files=923,programs=programs,previous_programs=previous['programs'],asset_hashes=previous['asset_hashes'],assets='assets-painted-r65',asset_files=525,source_states=states,default_cli_state_sha256=sha(q/'cli-native/final.state'),gui=phases,save_sha256=sha(saved),save_bytes=2987,build_inputs_sha256=sha(candidate/'build-inputs.sha256'),runtime_sha256=sha(candidate/'runtime.json'),tools={n:sha(r/'tools'/n) for n in ['prepare-ai-engine.py','prepare-ai-gui.py','check-ai-engine-gui.sh','audit-ai-engine.py']},limits=['Target-only policy, original executors; no new troops, traits or cross-spell evaluation.','Eight state-controlled cases and one normal GUI battle; no full-game win-rate claim.','First seven runtime samples from r4, selector5 from r5; production sources identical except the test observer.'])
 a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(status=report['status'],programs=7,source_inputs=181,controlled_states=16,normal_gui_battle=True)))
if __name__=='__main__':main()
