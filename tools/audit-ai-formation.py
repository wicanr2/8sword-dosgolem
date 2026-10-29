#!/usr/bin/env python3
"""030: independent RAM, integer prediction and original-executor verification."""
import argparse,hashlib,json,pathlib,struct
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def evaluate(v,formation):
 slots=v['FriendlySlots'];u=v['Friendly'];source=v['Enemy'][v['EnemySlots'][v['SourceSlot']]];route=v['Route'];first,last=0,6
 if route=='normal':
  last=3
  if not any(u[slots[i]]['Count']for i in range(3)):first,last=3,6
  elif u[slots[v['SourceSlot']]]['Count']:first,last=v['SourceSlot'],v['SourceSlot']+1
 candidates=[]
 for s in range(first,last):
  id=slots[s];target=u[id];count=target['Count']
  if not count:continue
  eligible=s<3 and target['Kind']==1 and any(i!=s and u[slots[i]]['Count']for i in range(3))
  if route=='special':assert v['Selector']==0;amount=2 if source['Kind']==12 else 5;loss=min(count,amount)
  else:
   amount=((v['Factors'][source['Kind']*2]*source['Count'])&65535)//((v['Divisor']+5)&65535)
   if formation and eligible:amount=amount*80//100
   encoded=(amount//v['Factors'][target['Kind']*2+1]+1)&65535;loss=0 if encoded<=1 else count if encoded>=count else encoded-1
  candidates.append(dict(Slot=s,Unit=id,Count=count,Amount=amount,Loss=loss,Eliminates=loss==count))
 best=next(c for c in candidates if c['Slot']==v['OriginalSlot'])
 for c in candidates:
  if c['Eliminates']!=best['Eliminates']:better=c['Eliminates']
  else:better=c['Loss']*best['Count']>best['Loss']*c['Count']
  if better:best=c
 return candidates,best
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();r=a.project;q=r/'workplace/probe-20261023/graphics-first/battle-r1/ai-formation-r1';batch=q/'original-r2';assert not a.out.exists();summary=read(batch/'summary.json');assert summary['calls']==36 and summary['cases']==6;results=[];pam=r/'workplace/intake-20261023/sources/game/8sword/PAM.AY';assert sha(pam)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0';raw=pam.read_bytes();word=lambda at:struct.unpack_from('<H',raw,at)[0];header=word(8)*16;code=bytearray(raw[header:])
 for i in range(word(6)):
  at=word(24)+i*4;loc=word(at+2)*16+word(at);struct.pack_into('<H',code,loc,(struct.unpack_from('<H',code,loc)[0]+0x110)&65535)
 for case in ['normal-ratio','ranged-ratio','ranged-rear','normal-locked','no-support','special0']:
  allrules={}
  for rules in ['native','formation']:
   d=batch/(case+'-'+rules);states={};modes={}
   for mode in ['baseline','blind','aware']:
    root=d/mode;t=read(root/'trace.json');v=t['View'];mem=(root/'before-decision-ram.bin').read_bytes();after=(root/'after-decision-ram.bin').read_bytes();get=lambda off:struct.unpack_from('<H',mem,0x1e88*16+off)[0]
    for i in range(6):assert v['Friendly'][i]==dict(Kind=get(0x56e8+i*4),Count=get(0x56ea+i*4)) and v['Enemy'][i]==dict(Kind=get(0x5700+i*4),Count=get(0x5702+i*4)) and v['FriendlySlots'][i]==get(0x6fb6+i*2) and v['EnemySlots'][i]==get(0x6fc2+i*2)
    assert v['Factors']==[get(0x70ce+i*2)for i in range(52)] and v['Divisor']==get(0x26ac)
    ip=t['HookIP'];assert mem[0xf67*16+ip:0xf67*16+ip+24]==code[0xe57*16+ip:0xe57*16+ip+24]
    candidates,best=evaluate(v,rules=='formation'and mode=='aware');selected=v['OriginalSlot']if mode=='baseline'else best['Slot']
    if mode!='baseline':assert t['Decision']['Candidates']==candidates and t['Decision']['SuggestedSlot']==selected
    actual_candidates,_=evaluate(v,rules=='formation');pred=next(c for c in actual_candidates if c['Slot']==selected);assert t['Prediction']==pred
    expected=t['BeforeUnits'].copy();expected[pred['Unit']*2+1]-=pred['Loss']
    if expected[pred['Unit']*2+1]==0:expected[pred['Unit']*2]=0
    assert expected==t['AfterUnits'] and sha(root/'final.state')==t['StateSHA256']
    expected_ram=bytearray(mem)
    for change in t['Changes']:
     if change['Phase']=='policy-target':assert change['New']==selected+(0 if v['Route']=='special'else 7);struct.pack_into('<H',expected_ram,change['Segment']*16+change['Offset'],change['New'])
    assert bytes(expected_ram)==after
    if v['Route']=='special':assert t['Damage']==[]
    else:
     assert [taken['InsideExecutor']for taken in t['Damage']]==([False,True]if v['Route']=='normal'else[True])
     amount=((v['Factors'][v['Enemy'][v['EnemySlots'][v['SourceSlot']]]['Kind']*2]*50)&65535)//((v['Divisor']+5)&65535)
     for taken in t['Damage']:assert taken['Unit']==pred['Unit']and taken['Adjusted']==pred['Amount']and taken['Original']==amount
    assert sha(root/'final.state')==sha(q/'original-r1'/(case+'-'+rules)/mode/'final.state')
    states[mode]=sha(root/'before-decision.state');modes[mode]=dict(selected=selected,loss=pred['Loss'],amount=pred['Amount'],final_sha256=sha(root/'final.state'))
   assert len(set(states.values()))==1
   if rules=='native':assert modes['blind']==modes['aware']
   allrules[rules]=modes
  if case in ['normal-ratio','ranged-ratio','ranged-rear']:assert allrules['formation']['blind']['selected']==0 and allrules['formation']['aware']['selected']==(3 if case=='ranged-rear'else 1) and allrules['formation']['aware']['loss']==13 and allrules['formation']['blind']['loss']==12
  else:assert allrules['formation']['blind']==allrules['formation']['aware']
  results.append(dict(case=case,rules=allrules))
 result=dict(schema=1,status='passed-scoped-ai-formation-original-controls',original_calls=36,same_initial_decision_groups=12,formation_changed_cases=3,formation_unchanged_cases=3,native_policies_equal_cases=6,results=results,source_sha256=sha(pam),limits=['Controlled six scenarios with fixed original snapshot; no natural battle or whole-game balance claim.','20 percent formation is the approved added rule, not original game behavior.'])
 a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['results','limits']}))
if __name__=='__main__':main()
