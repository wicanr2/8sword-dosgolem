#!/usr/bin/env python3
"""030: independent MZ, paired snapshot, formula and offline Go shadow audit."""
import argparse,collections,hashlib,json,os,pathlib,struct
from PIL import Image
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();r=a.project;b=r/'workplace/probe-20261023/graphics-first/battle-r1/ai-observation-r1';assert os.getuid()==1000 and not a.out.exists()
 original=r/'workplace/intake-20261023/sources/game/8sword/PAM.AY';assert sha(original)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0';raw=original.read_bytes();u16=lambda off:struct.unpack_from('<H',raw,off)[0];header=u16(8)*16;count=u16(6);table=u16(24);assert count==1301
 def relocated(base):
  code=bytearray(raw[header:])
  for i in range(count):
   off,seg=struct.unpack_from('<HH',raw,table+i*4);at=seg*16+off;v=struct.unpack_from('<H',code,at)[0];struct.pack_into('<H',code,at,(v+base)&65535)
  return bytes(code)
 runtime=relocated(0x110);ida=relocated(0x1000)
 exports={}
 for name in ['ida-ai-entry-r3.json','ida-ai-parents-r2.json','ida-ai-candidates-r1.json']:
  d=read(b/name);assert d['input_sha256']==sha(original)and d['database_sha256']=='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac'
  for f in d['functions']:
   if f['name']in ['sub_206DA','sub_1FB6C','sub_1FAA2','sub_22DBC','sub_22B96']:
    for line in f['lines']:
     at=line['file_offset']-header;data=bytes.fromhex(line['bytes']);assert ida[at:at+len(data)]==data
    exports[f['name']]=dict(start=f['start'],end=f['end'],export=name,export_sha256=sha(b/name))
 assert len(exports)==5
 cases=[];all_damage=[];suggestions=[]
 for name,shadow,source_sha,losses in [('damage-single-r3','shadow-single-r2.json','5f59ebd624bb3603fd381f71699ad43e489d699c090a8805121b79dd7a10945e',[5,3,7]),('damage-multi-r3','shadow-multi-r2.json','88f21ef185d597fee43972aec1d14e9a6811ea072a443aa6be04fe6de999b5bf',[16,5,12])]:
  folder=b/name;trace=read(folder/'trace.json');assert trace['source_state_sha256']==source_sha and trace['tool_go_version']=='go1.24.13'and trace['state_equal']and trace['io_equal']and not trace['overflow'];assert len(trace['events'])==40
  assert sha(folder/'observed/final.state')==sha(folder/'control/final.state')==trace['observed']['State'];assert trace['observed']==trace['control']
  assert read(folder/'planned-inputs.json')==[dict(offset=i*2000000,scan=57)for i in range(6)]
  assert len(trace['prefixes'])==14
  for v in trace['prefixes']:
   seg,off=[int(x,16)for x in v['runtime'].split(':')];at=seg*16+off-0x1100;assert runtime[at:at+24].hex()==v['bytes']
  for file in ['initial.png','final.png']:assert Image.open(folder/'observed'/file).tobytes()==Image.open(folder/'control'/file).tobytes()
  events=trace['events'];counts=collections.Counter(v['name']for v in events);assert counts['sub_206DA']==counts['sub_206DA:return']==1 and counts['sub_1FB6C']==counts['sub_1FB6C:return']==4 and counts['sub_1FAA2']==counts['sub_1FAA2:return']==6
  helper=None;normal=None;observed_losses=[];original_actions=[];damage_rows=[]
  for v in events:
   if v['name']=='IDA 0x1FD7A before target normalization':normal=v
   elif v['name']=='sub_22DBC':
    assert v['stack_words'][2]==normal['bp_minus_2_through_12'][2]and v['stack_words'][3]==normal['bp_minus_2_through_12'][1]-7;original_actions.append(v['stack_words'][2:4])
   elif v['name']=='sub_1FAA2':helper=v
   elif v['name']=='sub_1FAA2:return':
    e=helper;source,target=e['stack_words'][2:4];units=e['ds_56e8_words'];factors=e['ds_70ce_words'];product=(factors[units[12+source*2]*2]*units[13+source*2])&65535;damage=product//((e['ds_26ac_word']+5)&65535);returned=(damage//factors[units[target*2]*2+1]+1)&65535;pool=(e['ds_8ca4_words'][target]-damage)&65535
    assert v['registers'][0]==returned and v['ds_8ca4_words'][target]==pool;damage_rows.append(dict(entry_step=e['step'],return_step=v['step'],source_unit=source,target_unit=target,raw_damage=damage,returned_value=returned,opaque_accumulator_before=e['ds_8ca4_words'][target],opaque_accumulator_after=pool))
   elif v['name']=='sub_22B96:return':
    slot=normal['bp_minus_2_through_12'][1]-7;target=normal['ds_6fa8_words'][7+slot];before=normal['ds_56e8_words'][target*2+1];after=v['ds_56e8_words'][target*2+1];actual=before-after;assert actual==min(before,damage_rows[-1]['returned_value']-1);observed_losses.append(actual)
  assert observed_losses==losses and original_actions==([[0,0],[1,0],[2,0]]if name=='damage-single-r3'else[[0,0],[1,1],[2,1]])
  writes=trace['writes'];flag_init=[v for v in writes if v['cs']==0xf67 and v['ip']==0x2184];assert len(flag_init)==12 and {v['offset']for v in flag_init}==set(range(0x8e78,0x8e84));assert len([v for v in writes if v['ip']==0x1699 and v['offset']in [0x8e78,0x8e7a,0x8e7c]])==3
  data=read(b/shadow);assert data['trace_sha256']==sha(folder/'trace.json')and data['status']=='offline-shadow-only'and not data['guest_executed']and not data['policy_approved_for_production'];assert len(data['decisions'])==3
  for row in data['decisions']:
   e=next(v for v in events if v['step']==row['Step']and v['name']=='IDA 0x1FD7A before target normalization');candidates=row['Candidates'];original_candidate=next(c for c in candidates if c['Slot']==row['OriginalSlot']);assert original_candidate['PredictedLoss']==row['ObservedOriginalLoss']
   for c in candidates:
    units=e['ds_56e8_words'];f=e['ds_70ce_words'];source=e['ds_6fa8_words'][13+row['SourceSlot']];target=e['ds_6fa8_words'][7+c['Slot']];assert target==c['Unit'];damage=((f[units[12+source*2]*2]*units[13+source*2])&65535)//((e['ds_26ac_word']+5)&65535);returned=(damage//f[units[target*2]*2+1]+1)&65535;quantity=units[target*2+1];pred=0 if returned<=1 else quantity if returned>=quantity else returned-1;assert(c['RawDamage'],c['PredictedLoss'],c['Count'])==(damage,pred,quantity)
   if row['SuggestedSlot']!=row['OriginalSlot']:suggestions.append(dict(case=name,decision=row))
  cases.append(dict(case=name,source_sha256=source_sha,start_step=read(folder/'observed/result.json')['start_step'],end_step=trace['observed']['Steps'],round_return_step=next(v['step']for v in events if v['name']=='sub_206DA:return'),events=len(events),writes=len(writes),original_actions=original_actions,casualties=losses,state_sha256=trace['observed']['State'],trace_sha256=sha(folder/'trace.json'),shadow_sha256=sha(b/shadow)));all_damage.extend(damage_rows)
 assert len(all_damage)==12 and len(suggestions)==1
 experiment=b/'target-experiment-r2';trial=read(experiment/'experiment.json');assert trial['controlled_experiment']and not trial['production_changed']and trial['before_states_equal']
 assert sha(experiment/'original/before.state')==sha(experiment/'suggested/before.state')==trial['before_state_sha256']
 baseline=trial['results']['original'];suggested=trial['results']['suggested'];assert baseline['controller_writes']==[]and len(suggested['controller_writes'])==1;change=suggested['controller_writes'][0];assert(change['cs'],change['ip'],change['old'],change['new'])==(0xf67,0x180a,8,7)
 pre=(experiment/'original/before-ram.bin').read_bytes();assert pre==(experiment/'original/after-write-ram.bin').read_bytes()==(experiment/'suggested/before-ram.bin').read_bytes();post=(experiment/'suggested/after-write-ram.bin').read_bytes();assert len(pre)==len(post)
 changed=[i for i,(x,y)in enumerate(zip(pre,post))if x!=y];assert changed==[change['segment']*16+change['offset']]and pre[changed[0]]==8 and post[changed[0]]==7
 assert sha(experiment/'original/final.state')==baseline['final_state_sha256']==cases[1]['state_sha256'];assert sha(experiment/'suggested/final.state')==suggested['final_state_sha256']
 assert baseline['decision_after_units'][1:4:2]==[15,52]and suggested['decision_after_units'][1:4:2]==[0,64]
 alt=next(c for c in suggestions[0]['decision']['Candidates']if c['Slot']==0);assert alt['Eliminates']and alt['PredictedLoss']==15 and suggestions[0]['decision']['SuggestedSlot']==0
 core=read(r/'workplace/player/runtime.json');assert core['total_inputs']==923
 for name,digest in core['files'].items():assert sha(r/'workplace/player/runtime-render-r1/src'/name)==digest
 official=read(r/'preserved/completion-r65-promotion.json')
 for name,digest in official['programs'].items():assert sha(r/'workplace/player'/name)==digest
 for name in ['probe-ai-observation.go','research-ai-shadow.go']:
  source=(r/'tools'/name).read_text();assert not any(forbidden in source for forbidden in ['m.Write8(', 'm.Write16('])
 result=dict(schema=1,status='PASS-scoped-read-only-AI-observation-and-offline-shadow',pam_sha256=sha(original),ida_database_sha256='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac',module_load_paragraph=272,core_files=923,static_functions=exports,cases=cases,helper_predictions=all_damage,shadow_suggestions=suggestions,controlled_target_experiment=trial,controlled_target_experiment_sha256=sha(experiment/'experiment.json'),production_programs_unchanged=official['programs'],tools={n:sha(r/'tools'/n)for n in ['probe-ai-observation.go','prepare-ai-observation.py','research-ai-shadow.go','probe-ai-target-experiment.go','audit-ai-observation.py']},limits=['Snapshot diagnostics from previously recorded normal paths; no new cold-start claim.','No AI decision replacement or new rules in production.','Only sampled front-row selection is evaluated; ranged, rear-row and special actions rejected.','DS:26AC and DS:8CA4 gameplay meanings remain unknown; arithmetic and writes are confirmed.','One controlled target substitution confirms the boundary, not a complete AI policy or improved win rate.'])
 a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(status=result['status'],paired_rounds=2,helper_predictions=12,casualty_predictions=6,alternate_suggestions=1)))
if __name__=='__main__':main()
