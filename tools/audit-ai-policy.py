#!/usr/bin/env python3
"""030: independent candidate sets, raw RAM/register edits and original outcomes."""
import argparse, hashlib, json, os, pathlib, struct
from fractions import Fraction

def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();r=a.project;b=r/'workplace/probe-20261023/graphics-first/battle-r1';assert os.getuid()==1000 and not a.out.exists()
 original_path=r/'workplace/intake-20261023/sources/game/8sword/PAM.AY';assert sha(original_path)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0';raw=original_path.read_bytes();u=lambda at:struct.unpack_from('<H',raw,at)[0];header=u(8)*16;assert u(6)==1301
 def relocate(base):
  data=bytearray(raw[header:])
  for i in range(u(6)):
   off,seg=struct.unpack_from('<HH',raw,u(24)+i*4);at=seg*16+off;struct.pack_into('<H',data,at,(struct.unpack_from('<H',data,at)[0]+base)&65535)
  return data
 runtime=relocate(0x110);ida=relocate(0x1000);source=b/'ai-observation-r1/ida-ai-parents-r2.json';assert sha(source)=='76feaf768b248c99d54c7c3632f898f5199a844895e8312363ea5c6c9af1d7ba';exports=read(source)
 functions=[v for v in exports['functions'] if v['name'] in ['sub_1FB6C','sub_1F266','sub_22B96','sub_21C36']];assert len(functions)==4
 for f in functions:
  for v in f['lines']:
   at=v['file_offset']-header;data=bytes.fromhex(v['bytes']);assert ida[at:at+len(data)]==data
 baseline=next(v for v in read(b/'ai-observation-r1/damage-multi-r3/trace.json')['events'] if v['name']=='sub_206DA')
 wanted={'normal-locked':[0],'normal-choice':[0,1],'normal-rear-only':[3,4],'front-ranged-mixed':[0,3],'rear-ranged-mixed':[0,3],'special0-choice':[0,1],'special2-choice':[0,1],'special5-empty-original':[0,1]}
 replay=read(b/'ai-policy-extra-r2/offline-replay-r1.json');assert replay['status']=='offline-policy-replay-only' and not replay['production_changed'];replayed={(v['name'],v['mode']):v for v in replay['decisions']};assert len(replayed)==16
 pre=set();rows=[];changed=0;predictions=0
 for name,expected_slots in wanted.items():
  directory='ai-policy-extra-r2' if name=='special5-empty-original' else 'ai-policy-r1';folder=b/directory/name;paired=read(folder/'paired.json');sc=paired['scenario'];assert paired['shadow_state_equal'] and paired['shadow_io_equal'] and paired['before_states_equal']
  traces={mode:read(folder/mode/'trace.json') for mode in ['baseline','shadow','override']};control=traces['baseline'];shadow=traces['shadow'];chosen=traces['override'];assert control['Decision'] is None
  assert sha(folder/'baseline/final.state')==sha(folder/'shadow/final.state')==control['StateSHA256']==shadow['StateSHA256']
  assert len({sha(folder/mode/'before-decision.state') for mode in traces})==1
  assert len({sha(folder/mode/'before-fixture.state') for mode in traces})==1;pre.add(sha(folder/'baseline/before-fixture.state'))
  assert len({sha(folder/mode/'after-fixture.state') for mode in traces})==1
  for key in ['OPLSHA256','PortsSHA256','DOSSHA256']:assert control[key]==shadow[key]
  for key in ['View','Scenario','DecisionStep','BeforeRAMSHA256']:assert control[key]==shadow[key]==chosen[key]
  assert shadow['Decision']==chosen['Decision'] and shadow['Decision']['Candidates']
  v=shadow['View'];ds=shadow['TargetSegment'];mem=(folder/'shadow/before-decision-ram.bin').read_bytes()
  def w(off,n=1):return list(struct.unpack_from('<'+'H'*n,mem,ds*16+off))
  assert v['FriendlySlots']==sc['Mapping']==w(0x6fb6,6) and v['EnemySlots']==w(0x6fc2,6) and v['ShiftedSlotZero']==w(0x6fb4)[0] and v['Divisor']==w(0x26ac)[0] and v['Factors']==w(0x70ce,52)
  units=w(0x56e8,24);assert all(v['Friendly'][i]==dict(Kind=units[i*2],Count=units[i*2+1]) and v['Enemy'][i]==dict(Kind=units[12+i*2],Count=units[13+i*2]) for i in range(6))
  fixture_units=baseline['ds_56e8_words'].copy();fixture_map=baseline['ds_6fa8_words'][7:19].copy();wanted_changes=[]
  def edit(off,old,new):
   if old!=new:wanted_changes.append((ds,off,old,new))
  for i in range(6):
   q=50 if i==sc['Source'] else 0;edit(0x5702+i*4,fixture_units[13+i*2],q);fixture_units[13+i*2]=q
  edit(0x5700+sc['Source']*4,fixture_units[12+sc['Source']*2],sc['Kind']);fixture_units[12+sc['Source']*2]=sc['Kind']
  for i in range(2):
   edit(0x56e8+i*4,fixture_units[i*2],sc['Kinds'][i]);fixture_units[i*2]=sc['Kinds'][i];edit(0x56ea+i*4,fixture_units[i*2+1],sc['Counts'][i]);fixture_units[i*2+1]=sc['Counts'][i]
  for i,unit in enumerate(sc['Mapping']):edit(0x6fb6+i*2,fixture_map[i],unit)
  assert fixture_units==units
  source_unit=v['Enemy'][v['EnemySlots'][v['SourceSlot']]];assert source_unit['Count']==50 and source_unit['Kind']==sc['Kind'];ranged=sc['Kind'] in [3,24]
  slots=[s for s in range(6) if v['Friendly'][v['FriendlySlots'][s]]['Count']>0]
  if v['Route']=='normal':
   assert not ranged and v['SourceSlot']<3;front=[s for s in slots if s<3]
   slots=front if front else [s for s in slots if s>=3]
   if v['SourceSlot'] in front:slots=[v['SourceSlot']]
  elif v['Route']=='ranged':assert ranged
  else:
   assert v['Route']=='special' and sc['Kind']==12 and sc['Selector'] in [0,2,5]
   if sc['Selector']==2:slots=[s for s in slots if 6<=v['Friendly'][v['FriendlySlots'][s]]['Kind']<=15]
   if sc['Selector']==5:slots=[s for s in slots if v['Friendly'][v['ShiftedSlotZero'] if s==0 else v['FriendlySlots'][s-1]]['Count']>0]
  assert slots==expected_slots
  def predict(slot):
   unit=v['FriendlySlots'][slot];target=v['Friendly'][unit];q=target['Count'];amount=0;loss=0
   if v['Route'] in ['normal','ranged']:
    amount=((v['Factors'][sc['Kind']*2]*50)&65535)//((v['Divisor']+5)&65535);encoded=(amount//v['Factors'][target['Kind']*2+1]+1)&65535;loss=0 if encoded<=1 else q if encoded>=q else encoded-1
   else:
    amount=2 if sc['Selector']==0 else 6 if sc['Selector']==2 else q//3+1;loss=min(q,amount)
   return dict(Slot=slot,Unit=unit,Count=q,Amount=amount,Loss=loss,Eliminates=loss==q)
  candidates=[predict(s) for s in slots];assert candidates==shadow['Decision']['Candidates']
  original=v['OriginalSlot'];eligible=original in slots;assert eligible==shadow['Decision']['OriginalEligible'];assert eligible or sc['Selector']==5
  best=next((c for c in candidates if c['Slot']==original),candidates[0]);score=lambda c:(c['Eliminates'],Fraction(c['Loss'],c['Count']))
  for c in candidates:
   if score(c)>score(best):best=c
  assert best['Slot']==shadow['Decision']['SuggestedSlot'];changed+=int(best['Slot']!=original)
  for mode,t in traces.items():
   assert t['GoVersion']=='go1.24.13' and t['StartStep']<t['DecisionStep']<t['EndStep']<=t['StartStep']+40000000
   for point in t['Prefixes']:
    at=0xf67*16+point['ip']-0x1100;assert runtime[at:at+24].hex()==point['bytes'] and point['ida_linear']==0x1e570+point['ip'] and point['file_offset']==header+at
   actual=[(c['segment'],c['offset'],c['old'],c['new']) for c in t['Changes'] if c['phase']=='fixture'];assert actual==wanted_changes
   dispatches=[c for c in t['Changes'] if c['phase']=='dispatch'];assert len(dispatches)==int(sc['Selector']>=0)
   if dispatches:assert dispatches[0]['old']==1 and dispatches[0]['new']==sc['Selector']
   before=(folder/mode/'before-decision-ram.bin').read_bytes();after=(folder/mode/'after-decision-ram.bin').read_bytes();assert sha(folder/mode/'before-decision-ram.bin')==t['BeforeRAMSHA256'] and sha(folder/mode/'after-decision-ram.bin')==t['AfterRAMSHA256']
   diffs=[i for i,(x,y) in enumerate(zip(before,after)) if x!=y];changes=[c for c in t['Changes'] if c['phase']=='policy-target'];selected=best['Slot'] if mode=='override' else original
   assert len(changes)==int(mode=='override' and selected!=original)
   if name=='special5-empty-original':
    assert t['HookIP']==0xfbb and not diffs;old=t['BeforeRegisters'];new=t['AfterRegisters'];expected=old.copy();assert old[2]==original
    if mode=='override':expected[2]=selected
    assert new==expected
    if changes:assert changes[0]['register']=='DX' and changes[0]['old']==original and changes[0]['new']==selected
   else:
    allowed={'normal':[0x180a],'ranged':[0x16e7,0x1974],'special':[0xdbd,0xf06]};assert t['HookIP'] in allowed[v['Route']];at=t['TargetSegment']*16+t['TargetOffset'];encoded=v['Route']!='special';old=original+(7 if encoded else 0);new=selected+(7 if encoded else 0);assert struct.unpack_from('<H',before,at)[0]==old and struct.unpack_from('<H',after,at)[0]==new;assert all(i in [at,at+1] for i in diffs)
    if mode!='override':assert not diffs
    if changes:assert(changes[0]['segment'],changes[0]['offset'],changes[0]['old'],changes[0]['new'])==(t['TargetSegment'],t['TargetOffset'],old,new)
   assert t['ExecutorStack'][2:4]==[sc['Source'],selected];assert t['Executor']==('sub_21C36' if v['Route']=='special' else 'sub_22B96')
   expected=t['BeforeUnits'].copy();unit=v['FriendlySlots'][selected];q=expected[unit*2+1]
   if q>0:
    c=predict(selected);expected[unit*2+1]-=c['Loss']
    if expected[unit*2+1]==0:expected[unit*2]=0
   else:assert name=='special5-empty-original' and mode!='override'
   assert t['AfterUnits']==expected and t['Flags']==[0 if i==sc['Source'] else 1 for i in range(6)] and sha(folder/mode/'final.state')==t['StateSHA256']
   if mode!='baseline':
    replayed_row=replayed[(name,mode)];assert replayed_row['trace_sha256']==sha(folder/mode/'trace.json') and replayed_row['decision']==t['Decision']
    if t['Prediction'] is not None:assert t['Prediction']==predict(selected);predictions+=1
  rows.append(dict(name=name,directory=directory,source=sc['Source'],kind=sc['Kind'],selector=sc['Selector'],candidate_slots=slots,original_slot=original,suggested_slot=best['Slot'],original_eligible=eligible,original_counts=shadow['AfterUnits'][1:4:2],suggested_counts=chosen['AfterUnits'][1:4:2],baseline_state_sha256=control['StateSHA256'],suggested_state_sha256=chosen['StateSHA256'],before_state_sha256=sha(folder/'baseline/before-decision.state')))
 assert len(rows)==8 and changed==5 and predictions==15 and pre=={read(r/'preserved/ai-branches-audit-r1.json')['common_before_fixture_sha256']}
 tests=(b/'ai-policy-extra-r2/tests-r1.log').read_text();assert 'PASS' in tests and 'FAIL' not in tests and 'TestPolicyRealCandidateSets' in tests and 'TestPolicyRejectsUnsafeViews' in tests and 'TestPolicyStableTieRetainsOriginal' in tests;assert not (b/'ai-policy-extra-r2/vet-r1.log').read_text()
 official=read(r/'preserved/completion-r65-audit.json')
 for name,digest in official['programs'].items():assert sha(r/'workplace/player'/name)==digest
 core=read(r/'workplace/player/runtime.json');assert core['total_inputs']==923
 for name,digest in core['files'].items():assert sha(r/'workplace/player/runtime-render-r1/src'/name)==digest
 report=dict(schema=1,status='PASS-scoped-live-policy-shadow-and-targets',pam_sha256=sha(original_path),ida_export_sha256=sha(source),cases=rows,distinct_scenarios=8,guest_executions=24,changed_targets=changed,live_effect_predictions=predictions,offline_decisions=16,production_programs_unchanged=official['programs'],core_files_unchanged=923,tests_sha256=sha(b/'ai-policy-extra-r2/tests-r1.log'),tools={n:sha(r/'tools'/n) for n in ['probe-ai-policy.go','research-ai-policy.go','research-ai-policy_test.go','audit-ai-policy.py']},limits=['Research lexicographic target policy only; no production AI, rules, save or UI changes.','Normal/ranged and selectors 0/2/5 only; original bad selector5 target excluded deliberately.','First executor return only, no complete turn, natural encounter, counterattack exchange or win-rate claim.','Initial selector5 word-only experiment rejected; final sample changes only DX before native target store.'])
 a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(status=report['status'],cases=8,executions=24,changed=changed,predictions=predictions)))
if __name__=='__main__':main()
