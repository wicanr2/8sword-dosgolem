#!/usr/bin/env python3
"""030: independently compare frozen inputs, complete original states and GUI saves."""
import argparse,hashlib,json,os,pathlib
from PIL import Image
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def same(a,b):assert sha(a)==sha(b),(str(a),str(b))
def main():
 p=argparse.ArgumentParser()
 for n in ['project','out']:p.add_argument('--'+n,type=pathlib.Path,required=True)
 p.add_argument('--player',type=pathlib.Path);p.add_argument('--audit',type=pathlib.Path);p.add_argument('--promote',action='store_true');a=p.parse_args();r=a.project;player=a.player or r/'workplace/player';q=r/'workplace/probe-20261023/graphics-first/battle-r1/tactics-r1';c=player/'source-candidate-tactics-r2';old=read(r/'preserved/ai-formation-audit-r1.json');prep=read(c/'preparation.json');assert os.getuid()==1000 and not a.out.exists()
 assert prep['source_count']==len(prep['source_inputs'])==184 and prep['core_files']==923
 for n,h in prep['source_inputs'].items():assert sha(r/n)==sha(c/'src'/n)==h,n
 for n,h in old['programs'].items():assert sha(player/n)==h,n
 for n,h in old['asset_hashes'].items():assert sha(player/'assets-painted-r67'/n)==h,n
 core=read(player/'runtime.json');assert core['total_inputs']==len(core['files'])==923
 for n,h in core['files'].items():assert sha(player/'runtime-render-r1/src'/n)==h,n
 assets=player/'assets-painted-r68';hashes={str(f.relative_to(assets)):sha(f)for f in assets.rglob('*')if f.is_file()};assert len(hashes)==525 and hashes.keys()==old['asset_hashes'].keys()
 assert {n for n,h in hashes.items()if old['asset_hashes'][n]!=h}=={'poster-toolbar.json','poster-toolbar-font.png'}
 toolbar=read(assets/'poster-toolbar.json');prior=read(player/'assets-painted-r67/poster-toolbar.json');assert toolbar['schema']==4 and len(toolbar['glyphs'])==139 and toolbar['glyphs'][:137]==prior['glyphs'] and [g['character']for g in toolbar['glyphs'][137:]]==list('戰術')
 assert toolbar['atlas_sha256']==hashes['poster-toolbar-font.png']=='0ac21b4a848eb6a901c72faf9f5f363006632ea033a0180e65db82a6c5fed3d7'
 im=Image.open(assets/'poster-toolbar-font.png').convert('RGBA');before=Image.open(player/'assets-painted-r67/poster-toolbar-font.png').convert('RGBA');assert im.size==before.size==(1024,576)
 for i in range(137):box=(i%16*64,i//16*64,i%16*64+64,i//16*64+64);assert im.crop(box).tobytes()==before.crop(box).tobytes()
 programs={n:sha(c/n)for n in old['programs']};assert len(programs)==7
 for n in ['tests-r3.log','tests-r67-r3.log']:
  log=(q/n).read_text();assert '\nPASS\n'in log and 'FAIL'not in log and 'SKIP'not in log,n
 log=(q/'tests-r3.log').read_text()
 for name in ['TestBattleAITacticsEstimate','TestBattleAITacticsOriginalExecutors','TestBattleTacticsOriginalHelpers','TestBattleTacticsSourceFaults','TestBattleRulesAutomaticThreeModes','TestPosterTacticsSelectionAndLock']:assert '--- PASS: '+name+' 'in log,name
 assert not(q/'vet-r3.log').read_text()and 'go1.24.13'in(c/'build-go-version.txt').read_text()and(c/'build-source-checks.log').read_text().count(': OK')==184
 controls=read(q/'controls-audit-r1.json');assert controls['status']=='passed-controlled-tactics'and controls['helper_calls']==48 and controls['battle_calls']==63 and controls['decoded_states']==381
 runtime=q/'engine-runtime-r3';rulesout=q/'rules-runtime-r3';states=[]
 cases=['archer-front','archer-rear-target','archer-open-lane','archer-back','bird-front','melee-locked','special0']
 for case in cases:
  for rules in ['native','formation','tactics']:
   for mode in ['native','target']:
    name=case+'-'+rules+'-'+mode;actual=runtime/'tactics'/name;ref=q/'battles-r1-calls'/(case+'-'+rules)/('baseline'if mode=='native'else'aware');receipt=read(actual/'receipt.json');assert receipt['full_states_equal']and receipt['active_fixture']
    for n in ['after-decision.state','final.state']:same(actual/n,ref/n)
    ai=receipt['battle_ai'];assert ai['Mode']==mode and ai['Fault']is None
    if mode=='target':
     d=ai['Recent'][0]['Decision'];expected=read(ref/'trace.json')['Decision'];assert ai['Decisions']==1 and d.get('Formation',False)==(rules!='native')and d.get('ArcherPressure',False)==(rules=='tactics')and d['Candidates']==expected['Candidates']and d['SuggestedSlot']==expected['SuggestedSlot']
    else:assert not ai['Bound']and ai['Decisions']==0
    rule=receipt['rules'];trace=read(ref/'trace.json');assert rule['Fault']is None and rule['Applied']==(sum(v['Eligible']or(rules=='tactics'and v['PressureEligible'])for v in trace['Damage'])if rules!='native'else 0)and rule.get('Suppressed',0)==(sum(v['PressureEligible']for v in trace['Damage'])if rules=='tactics'else 0)
    states.append(dict(case=case,rules=rules,ai=mode,final_sha256=sha(actual/'final.state')))
 inactive=runtime/'tactics/archer-front-tactics-target-inactive';ref=q/'battles-r1-calls/archer-front-native/aware';d=read(inactive/'receipt.json');assert not d['active_fixture']and not d['battle_ai']['Recent'][0]['Decision'].get('ArcherPressure',False)
 for n in ['after-decision.state','final.state']:same(inactive/n,ref/n)
 for side in ['player','enemy']:
  for case in ['front-opposed','rear-archer','open-lane','other-ranged','combined','other-kind','rear-target','threshold']:
   for rules in ['native','formation','tactics']:
    name=side+'-'+case+'-'+rules;actual=rulesout/'tactics-helpers'/name;ref=q/'helpers-r1-calls'/name;same(actual/'final.state',ref/'final.state');d=read(actual/'rules.json');t=read(ref/'trace.json');suppressed=rules=='tactics'and t['pressure'];applied=(rules!='native'and t['formation'])or suppressed;assert d['Fault']is None and d['Applied']==int(applied)and d.get('Suppressed',0)==int(suppressed),name
 # Existing original-mode and formation executors must retain full serialized states.
 for case in ['normal-ratio','ranged-ratio','ranged-rear','normal-locked','no-support','special0']:
  for rules in ['native','formation']:
   for mode in ['native','target']:
    actual=runtime/(case+'-'+rules+'-'+mode);ref=q.parent/'ai-formation-r1/original-r2'/(case+'-'+rules)/('baseline'if mode=='native'else'aware')
    for n in ['after-decision.state','final.state']:same(actual/n,ref/n)
 for side in ['player','enemy']:
  for case in ['front-ally','alone','rear-ally','rear-target','other-kind','two-allies']:
   for mode,ref in [('native','baseline'),('formation','formation')]:same(rulesout/(side+'-'+case+'-'+mode)/'final.state',q.parent/'formation-hooks-r1/calls-r2'/(side+'-'+case)/ref/'final.state')
 for root,names in [(runtime,['fault-entry-bytes','fault-mapping','fault-stack']),(rulesout,['fault-bytes','fault-mapping','fault-stack','tactics-fault-range','tactics-fault-duplicate','tactics-fault-unmapped'])]:
  for name in names:same(root/(name+'-before.state'),root/(name+'-after.state'))
 cli=read(q/'cli-native/receipt.json');previous=read(q/'cli-old/receipt.json');assert all(cli[k]==v for k,v in previous.items());same(q/'cli-native/final.state',q/'cli-old/final.state');assert Image.open(q/'cli-native/final.png').convert('RGBA').tobytes()==Image.open(q/'cli-old/final.png').convert('RGBA').tobytes()
 guis=[]
 for phase,expected,savedmode in [('save','native','tactics'),('restore-tactics','tactics','native'),('restore-native','native','native')]:
  gui=q/'gui-r1'/phase;s=read(gui/'gui-final.json');assert s['closed']and s['exit_code']==0 and s['hd']and s['source_renderer']and s['owned_render_fault']is None and s['unimplemented']==[]and not s['toolbar_error']
  assert read(gui/'rules-startup.json')['status']['battle_rules']['Mode']==expected
  ai=s['battle_ai'];rule=s['battle_rules'];assert ai['Mode']=='target'and ai['Fault']is None and rule['Mode']==savedmode and rule['Fault']is None
  if phase=='save':
   assert s['exited'] # Save path uses the original DOS quit; cold-load checks close the window.
   assert ai['Decisions']>0 and all(d['Decision'].get('Formation',False)and d['Decision'].get('ArcherPressure',False)for d in ai['Recent'])and rule['Started']==rule['Finished']==1 and not rule['Active']and rule['Markers']>0
   assert read(gui/'rules-battle-locked.json')['status']['battle_rules']['Active']
   both={v['Side']for v in rule['Recent']};assert both=={'player','enemy'}
  assert read(gui/'gui-input-receipt.json')['status']=='passed-input-path';assert 'panic:'not in(gui/'player.log').read_text()and 'panic:'not in(gui/'gui-check.log').read_text()
  saved=gui/'saved-gamedata.ay';marker=read(gui/'saved-rules.json');assert marker==dict(schema=1,rules=savedmode,save_sha256=sha(saved),save_bytes=2987)and saved.read_bytes()==(gui/'snapshot-readonly/save-buffer-9e000.bin').read_bytes()
  guis.append(dict(phase=phase,startup_rules=expected,saved_rules=savedmode,closed=s['closed'],dos_exited=s['exited'],decisions=ai['Decisions'],changed=ai['Changed'],applied=rule['Applied'],suppressed=rule.get('Suppressed',0),save_sha256=sha(saved),final_state_sha256=sha(gui/'gui-final.state')))
 result=dict(schema=1,status='passed-scoped-tactics-engine',candidate=c.name,programs=programs,previous_programs=old['programs'],source_count=184,source_inputs=prep['source_inputs'],changed_sources=prep['changed'],core_files=923,assets='assets-painted-r68',asset_files=525,asset_hashes=hashes,controlled_states=states,helper_calls=48,inactive_state_equal=True,prior_ai_cases_passed=16,prior_formation_executors=24,formation_helper_cases_passed=24,faults_without_guest_mutation=9,gui=guis,controls_audit_sha256=sha(q/'controls-audit-r1.json'),limits=['Approved added 25 percent archer pressure and existing 20 percent formation, not original game rules.','Seven controlled battle scenarios and one normal GUI battle; no whole-game balance claim.','Natural battle need not contain an archer. Controlled states prove reduction and changed targets.','Original 2987-byte save format and four-field schema-1 marker retained with tactics enum added.'])
 if a.promote:
  assert a.player and a.audit and read(a.audit)==result;staged={}
  try:
   for n in programs:
    tmp=player/('.tactics-'+n+'.tmp');assert not tmp.exists();os.link(c/n,tmp);staged[n]=tmp
   runtime=read(c/'runtime.json');runtime.update(production=True,application_spec='docs/spec/030-battle-expansion-proposal.md',application_source_inputs=184,battle_ai_formation_aware=True,battle_ai_pressure_aware=True,battle_rules=['native','formation','tactics'],assets='assets-painted-r68');meta={n:(c/n).read_bytes()for n in ['build-inputs.sha256','build-source-checks.log','build-go-version.txt']};meta['runtime.json']=(json.dumps(runtime,indent=2)+'\n').encode();meta['build-outputs.sha256']=''.join(f'{h}  /out/{n}\n'for n,h in programs.items()).encode()
   for n,data in meta.items():
    tmp=player/('.tactics-'+n+'.tmp');assert not tmp.exists();tmp.write_bytes(data);staged[n]=tmp
   for n,tmp in staged.items():os.replace(tmp,player/n)
  finally:
   for tmp in staged.values():
    if tmp.exists():tmp.unlink()
  for n,h in programs.items():assert sha(player/n)==h
  result=dict(status='promoted-scoped-tactics-engine',audit_sha256=sha(a.audit),programs=programs,source_count=184,core_files=923,assets='assets-painted-r68',asset_files=525)
 a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k in ['status','source_count','gui']}))
if __name__=='__main__':main()
