#!/usr/bin/env python3
"""Verify immutable AI resolutions still link evidence and the corrected spec."""
import argparse,json,pathlib
p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);a=p.parse_args();r=a.project
d=json.loads((r/'docs/spec/ai-resolution-backlinks-r1.json').read_text());assert d['schema']==1 and len(d['resolutions'])==26
assert len({v['key']for v in d['resolutions']})==26
for v in d['resolutions']:
 assert v['module_sha256']=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'and v['address_space']=='IDA MZ loader linear'and v['level']=='proven-in-sampled-scope'
 assert v['key']==v['module_sha256']+':'+v['original_address']
 evidence=r/v['evidence'];older=r/v['older_spec'];assert evidence.is_file()and older.is_file()
 e=evidence.read_text();s=older.read_text();assert v['original_address']in e and v['original_name']in e and v['original_name']in s and v['required_correction']in s
 assert v['scope']and v['not_closed']
 for extra in v.get('supplemental_resolutions',[]):
  evidence=r/extra['evidence'];older=r/extra['older_spec'];receipt=r/extra['receipt']
  assert extra['level']=='proven-in-sampled-scope'and evidence.is_file()and older.is_file()and receipt.is_file()
  assert v['original_address']in evidence.read_text()and v['original_name']in evidence.read_text()
  assert extra['required_correction']in older.read_text()and extra['scope']and extra['not_closed']
for v in d.get('player_resolutions',[]):
 assert v['module_sha256']=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'and v['address_space']=='IDA MZ loader linear'and v['level']=='proven-in-sampled-scope'
 assert v['key']==v['module_sha256']+':'+v['original_address']
 evidence=r/v['evidence'];older=r/v['older_spec'];receipt=r/v['receipt']
 assert evidence.is_file()and older.is_file()and receipt.is_file()
 assert v['original_address']in evidence.read_text()and v['original_name']in evidence.read_text()
 assert v['required_correction']in older.read_text()and v['scope']and v['not_closed']
 for extra in v.get('supplemental_resolutions',[]):
  evidence=r/extra['evidence'];older=r/extra['older_spec'];receipt=r/extra['receipt']
  assert extra['level']=='proven-in-sampled-scope'and evidence.is_file()and older.is_file()and receipt.is_file()
  assert v['original_address']in evidence.read_text()and v['original_name']in evidence.read_text()
  assert extra['required_correction']in older.read_text()and extra['scope']and extra['not_closed']
assert len(d.get('world_field_resolutions',[]))==3 and len({v['key']for v in d['world_field_resolutions']})==3
for v in d['world_field_resolutions']:
 assert v['platform_module']=='dos16/PAM.AY'and v['module_sha256']=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
 assert v['address_space']=='DS-relative data offset'and v['level']=='proven-in-sampled-scope'
 assert v['key']==v['platform_module']+':'+v['module_sha256']+':DS-relative:'+v['original_offset']
 evidence=r/v['evidence'];older=r/v['older_spec'];receipt=r/v['receipt']
 assert evidence.is_file()and older.is_file()and receipt.is_file()
 assert v['original_offset']in evidence.read_text()and v['original_name']in evidence.read_text()
 assert v['required_correction']in older.read_text()and v['semantic']in evidence.read_text()
 assert v['consumer']in evidence.read_text()and v['scope']and v['not_closed']
runtime_rows=d.get('original_battle_actions_resolutions',[])
assert len(runtime_rows)==6 and len({v['key']for v in runtime_rows})==6
for v in runtime_rows:
 assert v['platform_module']=='dos16/PAM.AY'and v['module_sha256']=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
 assert v['address_space']=='dosgolem runtime CS:IP'and v['level']=='proven-in-sampled-scope'
 assert v['key']==v['platform_module']+':'+v['module_sha256']+':dosgolem-runtime-CS-IP:'+v['original_address']
 evidence=r/v['evidence'];older=r/v['older_spec'];receipt=r/v['receipt']
 assert evidence.is_file()and older.is_file()and receipt.is_file()
 assert v['original_address']in evidence.read_text()and v['original_name']in evidence.read_text()
 assert v['required_correction']in older.read_text()and v['scope']and v['not_closed']
print('Resolution backlinks passed: 26 AI sampled resolutions,',len(d.get('player_resolutions',[])),'player resolutions,',len(d.get('world_field_resolutions',[])),'world fields,',len(runtime_rows),'battle presence resolutions')
casualty_rows=d.get('original_battle_casualty_resolutions',[])
assert len(casualty_rows)==5 and len({v['key']for v in casualty_rows})==5
for v in casualty_rows:
 assert v['platform_module']=='dos16/PAM.AY'and v['module_sha256']=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
 assert v['address_space']=='dosgolem runtime CS:IP'and v['level']=='proven-in-sampled-scope'
 assert v['key']==v['platform_module']+':'+v['module_sha256']+':dosgolem-runtime-CS-IP:'+v['original_address']
 evidence=r/v['evidence'];older=r/v['older_spec'];receipt=r/v['receipt']
 assert evidence.is_file()and older.is_file()and receipt.is_file()
 assert v['original_address']in evidence.read_text()and v['original_name']in evidence.read_text()
 assert v['required_correction']in older.read_text()and v['scope']and v['not_closed']
print('Original first-melee casualty backlinks passed:',len(casualty_rows))

round_rows=d.get('original_battle_rounds_resolutions',[])
assert len(round_rows)==7 and len({v['key']for v in round_rows})==7
for v in round_rows:
 assert v['platform_module']=='dos16/PAM.AY'and v['module_sha256']=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
 assert v['address_space']=='dosgolem runtime CS:IP'and v['level']=='proven-in-sampled-scope'
 assert v['key']==v['platform_module']+':'+v['module_sha256']+':dosgolem-runtime-CS-IP:'+v['original_address']
 evidence=r/v['evidence'];older=r/v['older_spec'];receipt=r/v['receipt']
 assert evidence.is_file()and older.is_file()and receipt.is_file()
 assert v['original_address']in evidence.read_text()and v['original_name']in evidence.read_text()
 assert v['required_correction']in older.read_text()and v['scope']and v['not_closed']
print('Original continuous-round backlinks passed:',len(round_rows))

world_rows=d.get('original_battle_world_resolutions',[])
assert len(world_rows)==7 and len({v['key']for v in world_rows})==7
for v in world_rows:
 assert v['platform_module']=='dos16/PAM.AY'and v['module_sha256']=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
 assert v['address_space']=='dosgolem runtime CS:IP'and v['level']=='proven-in-sampled-scope'
 assert v['key']==v['platform_module']+':'+v['module_sha256']+':dosgolem-runtime-CS-IP:'+v['original_address']
 evidence=r/v['evidence'];older=r/v['older_spec'];receipt=r/v['receipt']
 assert evidence.is_file()and older.is_file()and receipt.is_file()
 assert v['original_address']in evidence.read_text()and v['original_name']in evidence.read_text()
 assert v['required_correction']in older.read_text()and v['scope']and v['not_closed']
print('Original battle world/F7 backlinks passed:',len(world_rows))

spell_rows=d.get('original_battle_spell_resolutions',[])
assert len(spell_rows)==5 and len({v['key']for v in spell_rows})==5
for v in spell_rows:
 assert v['platform_module']=='dos16/PAM.AY'and v['module_sha256']=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
 assert v['address_space']=='dosgolem runtime CS:IP'and v['level']=='proven-in-sampled-scope'
 assert v['key']==v['platform_module']+':'+v['module_sha256']+':dosgolem-runtime-CS-IP:'+v['original_address']
 evidence=r/v['evidence'];older=r/v['older_spec'];receipt=r/v['receipt']
 assert evidence.is_file()and older.is_file()and receipt.is_file()
 assert v['original_address']in evidence.read_text()and v['original_name']in evidence.read_text()
 assert v['required_correction']in older.read_text()and v['scope']and v['not_closed']
print('Original player-spell data backlinks passed:',len(spell_rows))
