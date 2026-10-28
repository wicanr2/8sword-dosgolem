#!/usr/bin/env python3
"""030: independent audit of controlled ranged/rear/special fixtures and Go replay."""
import argparse,collections,hashlib,json,os,pathlib,struct
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def growth(q,k):
 rate=20 if q<50 else 14 if q<100 else 13 if q<200 else 12 if q<300 else 11 if q<400 else 10
 bound=((q*rate)&65535)//(20 if k==12 else 10);return bound,max(q,bound)
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();r=a.project;b=r/'workplace/probe-20261023/graphics-first/battle-r1';assert os.getuid()==1000 and not a.out.exists()
 original=r/'workplace/intake-20261023/sources/game/8sword/PAM.AY';assert sha(original)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0';raw=original.read_bytes();u=lambda at:struct.unpack_from('<H',raw,at)[0];header=u(8)*16
 def relocate(base):
  code=bytearray(raw[header:])
  for i in range(u(6)):
   off,seg=struct.unpack_from('<HH',raw,u(24)+i*4);at=seg*16+off;struct.pack_into('<H',code,at,(struct.unpack_from('<H',code,at)[0]+base)&65535)
  return bytes(code)
 runtime=relocate(0x110);ida=relocate(0x1000);source=b/'ai-observation-r1/ida-ai-parents-r2.json';assert sha(source)=='76feaf768b248c99d54c7c3632f898f5199a844895e8312363ea5c6c9af1d7ba';functions={}
 for f in read(source)['functions']:
  if f['name']in ['sub_1FB6C','sub_1F266','sub_21C36','sub_22B96']:
   for line in f['lines']:
    data=bytes.fromhex(line['bytes']);at=line['file_offset']-header;assert ida[at:at+len(data)]==data
   functions[f['name']]=dict(start=f['start'],end=f['end'])
 assert len(functions)==4
 prior=read(r/'preserved/ai-observation-audit-r1.json');prior_trace=b/'ai-observation-r1/damage-multi-r3/trace.json';assert sha(prior_trace)==prior['cases'][1]['trace_sha256'];baseline=next(v for v in read(prior_trace)['events']if v['name']=='sub_206DA');base_units=baseline['ds_56e8_words'];base_mapping=baseline['ds_6fa8_words'][7:19]
 outcomes={'front-3':[31,56],'front-24':[31,56],'rear-3':[31,56],'rear-24':[31,56],'rear-10':[26,64],'rear-12':[29,67],'rear-ineligible-6':[31,69],'front-to-rear':[15,69],'ranged-to-rear':[15,69],'special-12-case0':[31,67],'special-12-case6':[31,69],'special-10-case6-49':[31,69],'special-10-case6-50':[31,69]}
 shadow=read(b/'ai-branches-r1/go-shadow-r1.json');assert shadow['status']=='offline-branch-shadow-only'and not shadow['guest_execution']and not shadow['policy_approved_for_production'];assert(shadow['ordinary_predictions'],shadow['special_loss_predictions'],shadow['growth_predictions'])==(6,5,3);go={v['name']:v for v in shadow['cases']};assert set(go)==set(outcomes)
 rows=[];pre_hashes=set();physical=magic=healing=helpers=0
 for name,expected in outcomes.items():
  folder=b/('ai-branches-extra-r2'if name.startswith('special-10-case6')else'ai-branches-r1')/name;paired=read(folder/'paired.json');assert paired['state_equal']and paired['io_equal'];sc=paired['scenario'];t=read(folder/'observed/trace.json');control=read(folder/'control/trace.json');s=t['summary'];assert s==control['summary'];assert s['stop']=='round-return'and not t['overflow'];assert s['end_step']-s['start_step']<=40000000
  assert t['go_version']=='go1.24.13'and t['source_state_sha256']=='88f21ef185d597fee43972aec1d14e9a6811ea072a443aa6be04fe6de999b5bf'and not t['observer_guest_writes'];assert sha(folder/'observed/final.state')==sha(folder/'control/final.state')==s['state_sha256'];assert sha(folder/'observed/before-fixture.state')==sha(folder/'control/before-fixture.state');pre_hashes.add(sha(folder/'observed/before-fixture.state'));assert sha(folder/'observed/after-fixture.state')==sha(folder/'control/after-fixture.state')
  for v in t['prefixes']:
   at=0xf67*16+v['runtime_ip']-0x1100;assert runtime[at:at+24].hex()==v['bytes']and v['ida_linear']==0x1e570+v['runtime_ip']and v['file_offset']==header+at
  events=t['events'];first=next(v for v in events if v['name']=='sub_206DA');ds=first['segments'][3];count=sc.get('Count',50);want=[]
  for unit in range(6):
   target=count if unit==sc['Slot']else 0;old=base_units[13+unit*2]
   if old!=target:want.append(dict(phase='fixture',step=first['step'],segment=ds,offset=0x5702+unit*4,old=old,new=target))
  old=base_units[12+sc['Slot']*2]
  if old!=sc['Kind']:want.append(dict(phase='fixture',step=first['step'],segment=ds,offset=0x5700+sc['Slot']*4,old=old,new=sc['Kind']))
  if sc['PlayerRear']:
   for i,target in enumerate([5,5,5,0,1,5]):
    if base_mapping[i]!=target:want.append(dict(phase='fixture',step=first['step'],segment=ds,offset=0x6fb6+i*2,old=base_mapping[i],new=target))
  changes=s['changes'];assert[v for v in changes if v['phase']=='fixture']==want
  dispatch_changes=[v for v in changes if v['phase']=='dispatch'];assert len(dispatch_changes)==(1 if sc['Variant']>=0 else 0)
  if dispatch_changes:assert dispatch_changes[0]['new']==sc['Variant']and dispatch_changes[0]['segment']==ds
  assert s['units'][1:4:2]==expected;assert sum(s['units'][13:24:2])==(98 if name.endswith('case6-49') else 70 if name.endswith('case6-50') else 50)
  counts=collections.Counter(v['name']for v in events);assert counts['sub_206DA']==counts['sub_206DA:return']==1;inactive=name=='rear-ineligible-6';assert s['action_flags']==[0 if i==sc['Slot']and not inactive else 1 for i in range(6)]
  if inactive:assert counts['sub_22B96']==counts['sub_1F266']==0
  current=None;helper=None;spell=None;helper_rows=[]
  for v in events:
   if v['name']in ['normal-normalize','front-ranged-normalize','rear-ranged-normalize']:current=v
   elif v['name']=='sub_22B96':
    source_slot,target_slot=v['stack_words'][2:4];assert source_slot==current['bp_minus_2_through_12'][2]and target_slot==current['bp_minus_2_through_12'][1]-7
    if current['name']!='normal-normalize':assert v['stack_words'][4:8]==[source_slot//3,source_slot%3,target_slot//3,target_slot%3]
   elif v['name']=='sub_1FAA2':helper=v
   elif v['name']=='sub_1FAA2:return':
    e=helper;source_id,target_id=e['stack_words'][2:4];units=e['ds_56e8_words'];f=e['ds_70ce_words'];damage=((f[units[12+source_id*2]*2]*units[13+source_id*2])&65535)//((e['ds_26ac_word']+5)&65535);encoded=(damage//f[units[target_id*2]*2+1]+1)&65535;assert v['registers'][0]==encoded and v['ds_8ca4_words'][target_id]==(e['ds_8ca4_words'][target_id]-damage)&65535;helpers+=1
   elif v['name']=='sub_22B96:return':
    e=current;source_id=e['ds_6fa8_words'][13+e['bp_minus_2_through_12'][2]];target_slot=e['bp_minus_2_through_12'][1]-7;target_id=e['ds_6fa8_words'][7+target_slot];u=e['ds_56e8_words'];f=e['ds_70ce_words'];damage=((f[u[12+source_id*2]*2]*u[13+source_id*2])&65535)//((e['ds_26ac_word']+5)&65535);encoded=(damage//f[u[target_id*2]*2+1]+1)&65535;q=u[target_id*2+1];loss=0 if encoded<=1 else q if encoded>=q else encoded-1;assert q-v['ds_56e8_words'][target_id*2+1]==loss;physical+=1
   elif v['name']=='sub_21C36':spell=v
   elif v['name']=='sub_21C36:return':
    e=spell;target=e['ds_6fa8_words'][7+e['stack_words'][3]];q=e['ds_56e8_words'][target*2+1];amount=e['ds_8cb0_words'][1];assert q-v['ds_56e8_words'][target*2+1]==min(q,amount);assert amount==(2 if sc['Kind']==12 else 5);magic+=1
  g=go[name];assert g['trace_sha256']==sha(folder/'observed/trace.json')
  for effect in g['effects']:
   if effect['kind']=='own-count-growth':bound,after=growth(effect['before'],sc['Kind']);assert(effect['computed_bound'],effect['predicted_after'],effect['actual_after'])==(bound,after,after);healing+=1
   else:assert effect['predicted_loss']==effect['actual_loss']==min(effect['before'],effect['amount'])
  rows.append(dict(name=name,scenario=sc,events=len(events),step_count=s['end_step']-s['start_step'],state_sha256=s['state_sha256'],units=s['units'],flags=s['action_flags'],selector=g['selector'],fixture_changes=len(want),dispatch_changes=len(dispatch_changes),trace_sha256=sha(folder/'observed/trace.json')))
 assert len(pre_hashes)==1 and(physical,magic,healing,helpers)==(6,5,3,7)
 official=read(r/'preserved/completion-r65-audit.json')
 for name,digest in official['programs'].items():assert sha(r/'workplace/player'/name)==digest
 core=read(r/'workplace/player/runtime.json');assert core['total_inputs']==923
 for name,digest in core['files'].items():assert sha(r/'workplace/player/runtime-render-r1/src'/name)==digest
 result=dict(schema=1,status='PASS-scoped-AI-branches-and-Go-shadow',pam_sha256=sha(original),ida_export_sha256=sha(source),static_functions=functions,source_state_sha256='88f21ef185d597fee43972aec1d14e9a6811ea072a443aa6be04fe6de999b5bf',common_before_fixture_sha256=next(iter(pre_hashes)),cases=rows,paired_rounds=13,physical_predictions=physical,special_loss_predictions=magic,growth_predictions=healing,helper_predictions=helpers,shadow_sha256=sha(b/'ai-branches-r1/go-shadow-r1.json'),production_unchanged=official['programs'],tools={n:sha(r/'tools'/n)for n in ['probe-ai-branches.go','research-ai-branches.go','audit-ai-branches.py']},limits=['Controlled fixtures and dispatch selectors; not natural encounters.','No production AI replacement, new troops, game rules, save changes or GUI claim.','Special dispatch 0/1/6 sampled; 2/3/4/5/7 and whole-policy performance remain unknown.','Growth boundary sampled at 49/50; higher tiers and overflow not dynamically verified.'])
 a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(status=result['status'],cases=13,predictions=14,helpers=helpers)))
if __name__=='__main__':main()
