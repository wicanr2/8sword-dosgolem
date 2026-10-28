#!/usr/bin/env python3
"""030: independent original MZ, dispatch, paired state and sampled special effects."""
import argparse, collections, hashlib, json, os, pathlib, struct

def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
 assert os.getuid()==1000 and not a.out.exists();r=a.project;b=r/'workplace/probe-20261023/graphics-first/battle-r1';folder=b/'ai-specials-r1'
 original=r/'workplace/intake-20261023/sources/game/8sword/PAM.AY';assert sha(original)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
 raw=original.read_bytes();u=lambda at:struct.unpack_from('<H',raw,at)[0];header=u(8)*16;assert u(6)==1301
 def relocated(base):
  code=bytearray(raw[header:])
  for i in range(u(6)):
   off,seg=struct.unpack_from('<HH',raw,u(24)+i*4);at=seg*16+off;struct.pack_into('<H',code,at,(struct.unpack_from('<H',code,at)[0]+base)&65535)
  return bytes(code)
 runtime=relocated(0x110);ida=relocated(0x1000)
 old=b/'ai-observation-r1/ida-ai-parents-r2.json';assert sha(old)=='76feaf768b248c99d54c7c3632f898f5199a844895e8312363ea5c6c9af1d7ba'
 caller=next(f for f in read(old)['functions'] if f['name']=='sub_1F266')
 fresh=read(folder/'ida-specials-r1.json');assert fresh['schema']==1 and fresh['tool']=='IDA 9.4' and fresh['uid']==1000 and fresh['function_count']==521 and fresh['source_sha256']==sha(original) and fresh['database_sha256']=='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac'
 assert fresh['tool_sha256']==sha(r/'tools/export-ai-specials-ida.py')
 for v in caller['lines']:
  at=v['file_offset']-header;data=bytes.fromhex(v['bytes']);assert ida[at:at+len(data)]==data
 assert len(fresh['bodies'])==1 and fresh['bodies'][0]['name']=='sub_21E3C' and fresh['bodies'][0]['start']==0x21e3c
 for v in fresh['bodies'][0]['lines']:
  at=v['original_file_offset']-header;data=bytes.fromhex(v['bytes']);assert ida[at:at+len(data)]==data
 table=fresh['dispatch_table'];assert table['ida_linear']==0x1fa14 and table['original_file_offset']==0x10e84
 data=bytes.fromhex(table['bytes']);assert ida[0xfa14:0xfa24]==data and list(struct.unpack('<8H',data))==[0xd9c,0xe16,0xe90,0xf2c,0xf8a,0xfb0,0x1016,0x1134]
 baseline=next(v for v in read(b/'ai-observation-r1/damage-multi-r3/trace.json')['events'] if v['name']=='sub_206DA');base_units=baseline['ds_56e8_words'];base_map=baseline['ds_6fa8_words'][7:19]
 shadow=read(folder/'go-shadow-r1.json');assert shadow['status']=='offline-special-shadow-only' and not shadow['guest_execution'] and not shadow['policy_approved_for_production'];go={v['name']:v for v in shadow['cases']}
 unique={};all_runs=[];pre_hashes=set();effects_total=flags_total=0
 for directory in ['ai-specials-r1','ai-specials-extra-r2']:
  summary=read(b/directory/'summary.json');assert summary['controlled_fixtures'] and not summary['production_changed']
  for case in summary['cases']:
   sc=case['scenario'];name=sc['Name'];d=b/directory/name;t=read(d/'observed/trace.json');c=read(d/'control/trace.json');s=t['summary'];assert s==c['summary'] and case['results']['observed']==s==case['results']['control']
   assert case['state_equal'] and case['io_equal'] and s['stop']=='special-return' and s['special_started'] and s['variant_forced'] and not t['overflow'] and not t['observer_guest_writes'] and t['go_version']=='go1.24.13'
   assert s['end_step']-s['start_step']<=120000000 and t['source_state_sha256']=='88f21ef185d597fee43972aec1d14e9a6811ea072a443aa6be04fe6de999b5bf'
   assert sha(d/'observed/final.state')==sha(d/'control/final.state')==s['state_sha256']
   for f in ['before-fixture.state','after-fixture.state']:assert sha(d/'observed'/f)==sha(d/'control'/f)
   pre_hashes.add(sha(d/'observed/before-fixture.state'))
   for v in t['prefixes']:
    at=0xf67*16+v['runtime_ip']-0x1100;assert runtime[at:at+24].hex()==v['bytes'] and v['ida_linear']==0x1e570+v['runtime_ip'] and v['file_offset']==header+at
   events=t['events'];counts=collections.Counter(v['name'] for v in events);assert counts['sub_1F266']==counts['special-dispatch']==counts['sub_1F266:return']==1
   entry=next(v for v in events if v['name']=='sub_1F266');dispatch=next(v for v in events if v['name']=='special-dispatch');finish=events[-1];assert finish['name']=='sub_1F266:return'
   ds=entry['segments'][3];first=events[0];assert first['name']=='sub_206DA';want=[];units=base_units.copy();mapping=base_map.copy()
   def change(seg,off,old,new,phase):
    if old!=new:want.append(dict(segment=seg,offset=off,old=old,new=new,phase=phase))
   for unit in range(6):
    q=sc['Count'] if unit==sc['Slot'] else 0;change(ds,0x5702+unit*4,units[13+unit*2],q,'fixture');units[13+unit*2]=q
   change(ds,0x5700+sc['Slot']*4,units[12+sc['Slot']*2],sc['Kind'],'fixture');units[12+sc['Slot']*2]=sc['Kind']
   for i,kind in enumerate(sc['FriendlyKinds'] or []):change(ds,0x56e8+i*4,units[i*2],kind,'fixture');units[i*2]=kind
   if sc['Gate']>=0:change(ds,0x26ae,0,sc['Gate'],'fixture')
   for i,v in enumerate(sc.get('FriendlyMap') or []):change(ds,0x6fb6+i*2,mapping[i],v,'fixture');mapping[i]=v
   assert not sc['PlayerRear'] and first['ds_56e8_words']==entry['ds_56e8_words']==units and first['ds_6fa8_words'][7:19]==entry['ds_6fa8_words'][7:19]==mapping
   actual=[{k:v[k] for k in ['segment','offset','old','new','phase']} for v in s['changes'] if v['phase']=='fixture'];assert actual==want
   mods=[v for v in s['changes'] if v['phase']=='dispatch'];assert len(mods)==1 and mods[0]['new']==sc['Variant'] and mods[0]['old']==1 and mods[0]['segment']==dispatch['segments'][2] and mods[0]['offset']==dispatch['registers'][5]-4 and mods[0]['step']==dispatch['step']
   assert dispatch['bp_minus_2_through_24'][1]==sc['Variant'];selector=sc['Variant'];expected=entry['ds_56e8_words'].copy();flags=entry['ds_8e78_words'].copy();pending=None;shifted=None;gate=None;effects=[]
   for v in events:
    if v['name']=='case3-gate':gate=v
    if v['name']=='case5-shifted-check':
     shifted=v;slot=v['bp_minus_2_through_24'][3];guard_unit=v['ds_6fa8_words'][6+slot];assert v['registers'][3]==guard_unit*4
    if v['name'] in ['sub_21C36','sub_21E3C']:pending=v
    if v['name'] in ['sub_21C36:return','sub_21E3C:return']:
     assert pending is not None;e=pending;slot=e['stack_words'][3];unit=e['ds_6fa8_words'][7+slot];q=expected[unit*2+1];assert q==e['ds_56e8_words'][unit*2+1]
     amount=0
     if selector==2:
      assert 6<=expected[unit*2]<=15 and q>0;amount=6 if sc['Kind']==12 else 15
     elif selector==3:
      assert gate is not None;field=gate['ds_26ae_word'];random=gate['bp_minus_2_through_24'][4];threshold=(field*10+10)&65535;assert gate['registers'][0]==threshold and gate['registers'][2]==random and threshold>random;amount=q
     elif selector==5:
      assert shifted is not None and shifted['bp_minus_2_through_24'][3]==slot;guard_unit=shifted['ds_6fa8_words'][6+slot];assert shifted['ds_56e8_words'][guard_unit*2+1]>0;amount=q//(3 if sc['Kind']==12 else 2)+1
     elif selector==7:
      assert e['name']=='sub_21E3C';amount=q if q<50 else (((q*6)&65535)//(20 if sc['Kind']==12 else 10)+1)&65535
     else:raise AssertionError(selector)
     assert e['ds_8cb0_words'][1]==amount;after=q-min(q,amount);expected[unit*2+1]=after
     if after==0:expected[unit*2]=0
     assert v['ds_56e8_words']==expected
     effects.append(dict(slot=slot,unit=unit,before=q,amount=amount,after=after));pending=None
   assert pending is None
   if selector==2:
    eligible=any(6<=entry['ds_56e8_words'][entry['ds_6fa8_words'][7+slot]*2]<=15 for slot in range(6));assert len(effects)==int(eligible)
    if directory=='ai-specials-extra-r2' and eligible:assert counts['case2-kind-check']>=1
   if selector==3:
    assert gate is not None;threshold=(gate['ds_26ae_word']*10+10)&65535;random=gate['bp_minus_2_through_24'][4];assert random==23 and len(effects)==int(threshold>random)
   if selector==4:
    assert not effects
    for slot in range(6):flags[entry['ds_6fa8_words'][13+slot]]=(flags[entry['ds_6fa8_words'][13+slot]]+1)&65535
    if directory=='ai-specials-extra-r2':assert counts['case4-increment']==6
   assert finish['ds_56e8_words']==s['units']==expected and finish['ds_8e78_words']==s['action_flags']==flags
   if directory=='ai-specials-extra-r2' and name in unique:assert unique[name]['state_sha256']==s['state_sha256']
   row=dict(name=name,directory=directory,selector=selector,kind=sc['Kind'],trace_sha256=sha(d/'observed/trace.json'),state_sha256=s['state_sha256'],step_count=s['end_step']-s['start_step'],counts=s['units'][1:4:2],flags=flags,effects=effects)
   all_runs.append(row);unique[name]=row
 assert len(all_runs)==17 and len(unique)==13 and len(pre_hashes)==1 and pre_hashes=={read(r/'preserved/ai-branches-audit-r1.json')['common_before_fixture_sha256']}
 assert set(go)==set(unique)
 for name,v in unique.items():
  g=go[name];assert g['directory']==v['directory'] and g['trace_sha256']==v['trace_sha256'] and g['complete_units_match'] and g['predicted_flags']==g['actual_flags']==v['flags']
  assert len(g['effects'])==len(v['effects'])
  for x,y in zip(g['effects'],v['effects']):assert(x['slot'],x['unit'],x['before'],x['amount'],x['predicted_after'],x['actual_after'])==(y['slot'],y['unit'],y['before'],y['amount'],y['after'],y['after'])
  effects_total+=len(v['effects']);flags_total+=int(v['selector']==4)
 assert effects_total==12 and flags_total==1 and shadow['predictions']==13
 expected_counts={'special-12-case2-kind6':[25,69],'special-10-case2-kind15':[16,69],'special-12-case2-none':[31,69],'special-12-case3-gate0':[31,69],'special-12-case3-gate4':[31,0],'special-10-case3-gate4':[31,0],'special-12-case4':[31,69],'special-12-case5':[31,69],'special-10-case5':[31,69],'special-12-case7':[0,48],'special-10-case7':[0,27],'special-12-case5-live':[31,45],'special-10-case5-live':[31,34]}
 assert {n:v['counts'] for n,v in unique.items()}==expected_counts
 official=read(r/'preserved/completion-r65-audit.json')
 for name,digest in official['programs'].items():assert sha(r/'workplace/player'/name)==digest
 core=read(r/'workplace/player/runtime.json');assert core['total_inputs']==923
 for name,digest in core['files'].items():assert sha(r/'workplace/player/runtime-render-r1/src'/name)==digest
 result=dict(schema=1,status='PASS-scoped-AI-specials-and-Go-shadow',source_sha256=sha(original),ida_export_sha256=sha(folder/'ida-specials-r1.json'),old_ida_export_sha256=sha(old),common_before_fixture_sha256=next(iter(pre_hashes)),paired_executions=17,distinct_cases=13,effect_predictions=effects_total,flag_predictions=flags_total,cases=list(unique.values()),runs=all_runs,shadow_sha256=sha(folder/'go-shadow-r1.json'),production_unchanged=official['programs'],core_unchanged=923,tools={n:sha(r/'tools'/n) for n in ['probe-ai-specials.go','research-ai-specials.go','export-ai-specials-ida.py','audit-ai-specials.py']},limits=['Controlled selector and fixture; first special return only, not full round or natural encounter.','Selectors 2/3/4/5/7 sampled, not full legality, timing, spell names or production strategy.','Selector 5 retains original shifted guard; no bug fix silently applied.','Original action flag increases are observed, not a complete extra-turn scheduling claim.'])
 a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(status=result['status'],runs=17,cases=13,effects=effects_total,flags=flags_total)))
if __name__=='__main__': main()
