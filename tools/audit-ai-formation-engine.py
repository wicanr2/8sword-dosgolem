#!/usr/bin/env python3
"""030: independent candidate gate and scoped seven-program promotion."""
import argparse,hashlib,json,os,pathlib
from PIL import Image
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 p=argparse.ArgumentParser()
 for n in ['project','out']:p.add_argument('--'+n,type=pathlib.Path,required=True)
 p.add_argument('--player',type=pathlib.Path);p.add_argument('--audit',type=pathlib.Path);p.add_argument('--promote',action='store_true');a=p.parse_args();r=a.project;player=a.player or r/'workplace/player';q=r/'workplace/probe-20261023/graphics-first/battle-r1/ai-formation-r1';c=player/'source-candidate-ai-formation-r1';old=read(r/'preserved/formation-engine-audit-r1.json');prep=read(c/'preparation.json');assert os.getuid()==1000 and not a.out.exists()
 assert prep['source_count']==len(prep['source_inputs'])==184 and prep['core_files']==923
 for n,h in prep['source_inputs'].items():assert sha(r/n)==sha(c/'src'/n)==h,n
 for n,h in old['programs'].items():assert sha(player/n)==h,n
 for n,h in old['asset_hashes'].items():assert sha(player/'assets-painted-r67'/n)==h,n
 core=read(player/'runtime.json');assert core['total_inputs']==len(core['files'])==923
 for n,h in core['files'].items():assert sha(player/'runtime-render-r1/src'/n)==h,n
 programs={n:sha(c/n)for n in old['programs']};assert len(programs)==7
 log=(q/'tests-r1.log').read_text();assert '\nPASS\n'in log and 'FAIL'not in log and 'SKIP'not in log and '--- PASS: TestBattleAIFormationEstimate 'in log and '--- PASS: TestBattleAIFormationOriginalExecutors 'in log and not(q/'vet-r1.log').read_text() and 'go1.24.13'in(c/'build-go-version.txt').read_text()
 controls=read(q/'research-audit-r1.json');assert controls['status']=='passed-scoped-ai-formation-original-controls'and controls['original_calls']==36 and controls['formation_changed_cases']==3
 runtime=q/'engine-runtime-r1';states=[]
 for case in ['normal-ratio','ranged-ratio','ranged-rear','normal-locked','no-support','special0']:
  for rules in ['native','formation']:
   for mode in ['native','target']:
    name=case+'-'+rules+'-'+mode;actual=runtime/name;ref=q/'original-r2'/(case+'-'+rules)/('baseline'if mode=='native'else'aware');receipt=read(actual/'receipt.json');assert receipt['full_states_equal']and receipt['active_fixture']
    for n in ['after-decision.state','final.state']:assert sha(actual/n)==sha(ref/n),name
    ai=receipt['battle_ai'];assert ai['Mode']==mode and ai['Fault']is None
    if mode=='target':
     assert ai['Bound']and ai['Decisions']==1 and ai['Recent'][0]['Decision'].get('Formation',False)==(rules=='formation');d=ai['Recent'][0]['Decision'];expected=read(ref/'trace.json')['Decision'];assert d['Candidates']==expected['Candidates']and d['SuggestedSlot']==expected['SuggestedSlot']
    else:assert not ai['Bound']and ai['Decisions']==0
    rule=receipt['rules'];t=read(ref/'trace.json');assert rule['Mode']==rules and rule['Fault']is None and rule['Applied']==(sum(v['Eligible']for v in t['Damage'])if rules=='formation'else 0)
    states.append(dict(case=case,rules=rules,mode=mode,final_sha256=sha(actual/'final.state')))
 inactive=runtime/'ranged-ratio-formation-target-inactive';reference=q/'original-r2/ranged-ratio-native/aware';d=read(inactive/'receipt.json');assert not d['active_fixture']and not d['battle_ai']['Recent'][0]['Decision'].get('Formation',False)
 for n in ['after-decision.state','final.state']:assert sha(inactive/n)==sha(reference/n)
 for fault in ['entry-bytes','mapping','stack']:assert sha(runtime/f'fault-{fault}-before.state')==sha(runtime/f'fault-{fault}-after.state')
 rule_runtime=q/'rules-runtime-r1'
 for side in ['player','enemy']:
  for case in ['front-ally','alone','rear-ally','rear-target','other-kind','two-allies']:
   for mode,ref in [('native','baseline'),('formation','formation')]:assert sha(rule_runtime/(side+'-'+case+'-'+mode)/'final.state')==sha(q.parent/'formation-hooks-r1/calls-r2'/(side+'-'+case)/ref/'final.state')
 for fault in ['bytes','mapping','stack']:assert sha(rule_runtime/f'fault-{fault}-before.state')==sha(rule_runtime/f'fault-{fault}-after.state')
 cli=read(q/'cli-native/receipt.json');previous=read(q/'cli-old/receipt.json');assert all(cli[k]==v for k,v in previous.items());assert sha(q/'cli-native/final.state')==sha(q/'cli-old/final.state');assert Image.open(q/'cli-native/final.png').convert('RGBA').tobytes()==Image.open(q/'cli-old/final.png').convert('RGBA').tobytes()
 gui=q/'gui-r1/save';s=read(gui/'gui-final.json');assert s['closed']and s['exited']and s['exit_code']==0 and s['hd']and s['source_renderer']and s['owned_render_fault']is None and s['unimplemented']==[]and not s['toolbar_error']
 ai=s['battle_ai'];rule=s['battle_rules'];assert ai['Mode']=='target'and ai['Decisions']>0 and ai['Fault']is None and all(d['Decision'].get('Formation',False)for d in ai['Recent']);assert rule['Mode']=='formation'and rule['Started']==rule['Finished']==1 and not rule['Active']and rule['Fault']is None and rule['Markers']>0
 assert read(gui/'gui-input-receipt.json')['status']=='passed-input-path';assert 'panic:'not in(gui/'player.log').read_text() and 'panic:'not in(gui/'gui-check.log').read_text()
 saved=gui/'saved-gamedata.ay';marker=read(gui/'saved-rules.json');assert marker==dict(schema=1,rules='formation',save_sha256=sha(saved),save_bytes=2987) and saved.read_bytes()==(gui/'snapshot-readonly/save-buffer-9e000.bin').read_bytes()
 result=dict(schema=1,status='passed-scoped-ai-formation-engine',candidate=c.name,programs=programs,previous_programs=old['programs'],source_count=184,source_inputs=prep['source_inputs'],changed_sources=prep['changed'],core_files=923,assets='assets-painted-r67',asset_files=525,asset_hashes=old['asset_hashes'],controlled_states=states,inactive_state_equal=True,prior_ai_cases_passed=16,formation_helper_cases_passed=24,gui=dict(decisions=ai['Decisions'],changed=ai['Changed'],formation_estimate_used=True,rule_applied=rule['Applied'],save_sha256=sha(saved),final_state_sha256=sha(gui/'gui-final.state')),research_audit_sha256=sha(q/'research-audit-r1.json'),limits=['Six controlled scenarios and one normal GUI battle; no whole-game balance claim.','Natural battle does not require a qualifying formation target; controlled states prove changed targets.','No new rules, troop IDs, spell strategy, toolbar layout or save schema.'])
 if a.promote:
  assert a.player and a.audit and read(a.audit)==result;staged={}
  try:
   for n in programs:
    tmp=player/('.ai-formation-'+n+'.tmp');assert not tmp.exists();os.link(c/n,tmp);staged[n]=tmp
   runtime=read(c/'runtime.json');runtime.update(production=True,application_spec='docs/spec/030-battle-expansion-proposal.md',application_source_inputs=184,battle_ai_formation_aware=True,assets='assets-painted-r67');meta={n:(c/n).read_bytes()for n in ['build-inputs.sha256','build-source-checks.log','build-go-version.txt']};meta['runtime.json']=(json.dumps(runtime,indent=2)+'\n').encode();meta['build-outputs.sha256']=''.join(f'{h}  /out/{n}\n'for n,h in programs.items()).encode()
   for n,data in meta.items():
    tmp=player/('.ai-formation-'+n+'.tmp');assert not tmp.exists();tmp.write_bytes(data);staged[n]=tmp
   for n,tmp in staged.items():os.replace(tmp,player/n)
  finally:
   for tmp in staged.values():
    if tmp.exists():tmp.unlink()
  for n,h in programs.items():assert sha(player/n)==h
  result=dict(status='promoted-scoped-ai-formation-engine',audit_sha256=sha(a.audit),programs=programs,source_count=184,core_files=923,assets='assets-painted-r67',asset_files=525)
 a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k in ['status','source_count','gui']}))
if __name__=='__main__':main()
