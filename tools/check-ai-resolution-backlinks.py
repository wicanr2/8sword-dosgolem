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

support_rows=d.get('original_battle_support_resolutions',[])
assert len(support_rows)==10 and len({v['key']for v in support_rows})==10
for v in support_rows:
 assert v['platform_module']=='dos16/PAM.AY'and v['module_sha256']=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
 assert v['address_space']=='dosgolem runtime CS:IP'and v['level']=='proven-in-sampled-scope'
 assert v['key']==v['platform_module']+':'+v['module_sha256']+':dosgolem-runtime-CS-IP:'+v['original_address']
 evidence=r/v['evidence'];older=r/v['older_spec'];receipt=r/v['receipt']
 assert evidence.is_file()and older.is_file()and receipt.is_file()
 assert v['original_address']in evidence.read_text()and v['original_name']in evidence.read_text()
 assert v['required_correction']in older.read_text()and v['scope']and v['not_closed']
print('Original freeze/clone data backlinks passed:',len(support_rows))

enemy_rows=d.get('original_battle_enemy_resolutions',[])
assert len(enemy_rows)==10 and len({v['key']for v in enemy_rows})==10
for v in enemy_rows:
 assert v['platform_module']=='dos16/PAM.AY'and v['module_sha256']=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
 assert v['address_space']=='dosgolem runtime CS:IP'and v['level']=='proven-in-sampled-scope'
 assert v['key']==v['platform_module']+':'+v['module_sha256']+':dosgolem-runtime-CS-IP:'+v['original_address']
 evidence=r/v['evidence'];older=r/v['older_spec'];receipt=r/v['receipt']
 assert evidence.is_file()and older.is_file()and receipt.is_file()
 assert v['original_address']in evidence.read_text()and v['original_name']in evidence.read_text()
 assert v['required_correction']in older.read_text()and v['scope']and v['not_closed']
print('Original enemy-special/rear-target motion backlinks passed:',len(enemy_rows))

guard_rows=d.get('original_battle_guard_resolutions',[])
assert len(guard_rows)==9 and len({v['key']for v in guard_rows})==9
for v in guard_rows:
 assert v['platform_module']=='dos16/PAM.AY'and v['module_sha256']=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
 assert v['address_space']=='dosgolem runtime CS:IP'and v['level']=='proven-in-sampled-scope'
 assert v['key']==v['platform_module']+':'+v['module_sha256']+':dosgolem-runtime-CS-IP:'+v['original_address']
 evidence=r/v['evidence'];older=r/v['older_spec'];receipt=r/v['receipt']
 assert evidence.is_file()and older.is_file()and receipt.is_file()
 assert v['original_address']in evidence.read_text()and v['original_name']in evidence.read_text()
 assert v['required_correction']in older.read_text()and v['scope']and v['not_closed']
print('Original guard/boss battlefield backlinks passed:',len(guard_rows))

ending_rows=d.get('original_battle_ending_resolutions',[])
assert len(ending_rows)==2 and len({v['key']for v in ending_rows})==2
for v in ending_rows:
 assert v['platform_module']=='dos16/PAM.AY'and v['module_sha256']=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
 assert v['address_space']=='dosgolem runtime CS:IP'and v['level']=='proven-in-sampled-scope'
 assert v['key']==v['platform_module']+':'+v['module_sha256']+':dosgolem-runtime-CS-IP:'+v['original_address']
 evidence=r/v['evidence'];older=r/v['older_spec'];receipt=r/v['receipt']
 assert evidence.is_file()and older.is_file()and receipt.is_file()
 assert v['original_address']in evidence.read_text()and v['original_name']in evidence.read_text()
 assert v['required_correction']in older.read_text()and v['scope']and v['not_closed']
print('Original final-guard/ending backlinks passed:',len(ending_rows))

session_rows=d.get('original_battle_session_resolutions',[])
assert len(session_rows)==4 and len({v['key']for v in session_rows})==4
for v in session_rows:
 assert v['platform_module']=='dos16/PAM.AY'and v['module_sha256']=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
 assert v['address_space']=='dosgolem runtime CS:IP'and v['level']=='proven-in-sampled-scope'
 assert v['key']==v['platform_module']+':'+v['module_sha256']+':dosgolem-runtime-CS-IP:'+v['original_address']
 evidence=r/v['evidence'];older=r/v['older_spec'];receipt=r/v['receipt']
 assert evidence.is_file()and older.is_file()and receipt.is_file()
 assert v['original_address']in evidence.read_text()and v['original_name']in evidence.read_text()
 assert v['required_correction']in older.read_text()and v['scope']and v['not_closed']
print('Original guard session backlinks passed:',len(session_rows))

art_rows=d.get('original_battle_art_resolutions',[])
assert len(art_rows)==4 and len({v['key']for v in art_rows})==4
for v in art_rows:
 assert v['platform_module']=='dos16/PAM.AY'and v['module_sha256']=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
 assert v['address_space']=='dosgolem runtime CS:IP'and v['level']=='proven-in-sampled-scope'
 assert v['key']==v['platform_module']+':'+v['module_sha256']+':dosgolem-runtime-CS-IP:'+v['original_address']
 evidence=r/v['evidence'];older=r/v['older_spec'];receipt=r/v['receipt']
 assert evidence.is_file()and older.is_file()and receipt.is_file()
 assert v['original_address']in evidence.read_text()and v['original_name']in evidence.read_text()
 assert v['required_correction']in older.read_text()and v['scope']and v['not_closed']
print('Original battle artwork backlinks passed:',len(art_rows))

rust_ending=d.get('rust_ending_resolutions',[])
assert len(rust_ending)==1
for v in rust_ending:
 assert v['platform_module']=='dos16/PAM.AY'and v['module_sha256']=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
 assert v['address_space']=='IDA MZ loader linear'and v['level']=='proven-in-sampled-scope'
 assert v['key']==v['platform_module']+':'+v['module_sha256']+':IDA-MZ-loader-linear:'+v['original_address']
 evidence=r/v['evidence'];older=r/v['older_spec'];receipt=r/v['receipt']
 assert evidence.is_file()and older.is_file()and receipt.is_file()
 assert v['original_address']in evidence.read_text()and v['original_name']in evidence.read_text()
 assert v['required_correction']in older.read_text()and v['scope']and v['not_closed']
print('Rust final-guard/ending backlinks passed:',len(rust_ending))

rust_month=d.get('rust_npc_month_resolutions',[])
assert len(rust_month)==2
for v in rust_month:
 assert v['platform_module']=='dos16/PAM.AY'and v['module_sha256']=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
 assert v['address_space']=='IDA MZ loader linear'and v['level']=='proven-in-sampled-scope'
 assert v['key']==v['platform_module']+':'+v['module_sha256']+':IDA-MZ-loader-linear:'+v['original_address']
 evidence=r/v['evidence'];older=r/v['older_spec'];receipt=r/v['receipt']
 assert evidence.is_file()and older.is_file()and receipt.is_file()
 assert v['original_address']in evidence.read_text()and v['original_name']in evidence.read_text()
 assert v['required_correction']in older.read_text()and v['scope']and v['not_closed']
print('Rust NPC month/counter backlinks passed:',len(rust_month))

rust_items=d.get('rust_item_resolutions',[])
assert len(rust_items)==2
for v in rust_items:
 assert v['platform_module']=='dos16/PAM.AY'and v['module_sha256']=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
 assert v['address_space']=='IDA MZ loader linear'and v['level']=='proven-in-sampled-scope'
 assert v['key']==v['platform_module']+':'+v['module_sha256']+':IDA-MZ-loader-linear:'+v['original_address']
 evidence=r/v['evidence'];older=r/v['older_spec'];receipt=r/v['receipt']
 assert evidence.is_file()and older.is_file()and receipt.is_file()
 assert v['original_address']in evidence.read_text()and v['original_name']in evidence.read_text()
 assert v['required_correction']in older.read_text()and v['scope']and v['not_closed']
print('Rust item/search backlinks passed:',len(rust_items))

rust_start=d.get('rust_start_resolutions',[])
assert len(rust_start)==3
for v in rust_start:
 assert v['platform_module']=='dos16/PAM.AY'and v['module_sha256']=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
 assert v['address_space']=='IDA MZ loader linear'and v['level']=='proven-in-sampled-scope'
 assert v['key']==v['platform_module']+':'+v['module_sha256']+':IDA-MZ-loader-linear:'+v['original_address']
 evidence=r/v['evidence'];older=r/v['older_spec'];receipt=r/v['receipt']
 assert evidence.is_file()and older.is_file()and receipt.is_file()
 assert v['original_address']in evidence.read_text()and v['original_name']in evidence.read_text()
 assert v['required_correction']in older.read_text()and v['scope']and v['not_closed']
print('Rust start-menu backlinks passed:',len(rust_start))
