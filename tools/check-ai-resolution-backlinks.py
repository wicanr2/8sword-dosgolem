#!/usr/bin/env python3
"""Verify immutable AI resolutions still link evidence and the corrected spec."""
import argparse,json,pathlib
p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);a=p.parse_args();r=a.project
d=json.loads((r/'docs/spec/ai-resolution-backlinks-r1.json').read_text());assert d['schema']==1 and len(d['resolutions'])==6
for v in d['resolutions']:
 assert v['module_sha256']=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'and v['address_space']=='IDA MZ loader linear'and v['level']=='proven-in-sampled-scope'
 assert v['key']==v['module_sha256']+':'+v['original_address']
 evidence=r/v['evidence'];older=r/v['older_spec'];assert evidence.is_file()and older.is_file()
 e=evidence.read_text();s=older.read_text();assert v['original_address']in e and v['original_name']in e and v['original_name']in s and v['required_correction']in s
 assert v['scope']and v['not_closed']
print('AI resolution backlinks passed: 6 sampled resolutions')
