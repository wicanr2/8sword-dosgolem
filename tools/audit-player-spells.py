#!/usr/bin/env python3
"""Independent original MZ/IDA spell catalog and paired real-menu fireball evidence."""
import argparse
import hashlib
import json
import os
import pathlib
import struct


def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
 p=argparse.ArgumentParser()
 for n in ['project','out','catalog']:p.add_argument('--'+n,type=pathlib.Path,required=True)
 a=p.parse_args();r=a.project;q=r/'workplace/probe-20261023/graphics-first/battle-r1/player-spells-r1';assert os.getuid()==1000 and not a.out.exists()and not a.catalog.exists()
 original=r/'workplace/intake-20261023/sources/game/8sword/PAM.AY';assert sha(original)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0';raw=original.read_bytes();u=lambda at:struct.unpack_from('<H',raw,at)[0];header=u(8)*16;code=bytearray(raw[header:]);assert u(6)==1301
 for i in range(u(6)):
  off,seg=struct.unpack_from('<HH',raw,u(24)+i*4);at=seg*16+off;struct.pack_into('<H',code,at,(struct.unpack_from('<H',code,at)[0]+0x1000)&65535)
 ida=read(q/'ida-r4/ida-spells-r4.json');assert ida['tool']=='IDA 9.4'and ida['function_count']==521 and ida['source_sha256']==sha(original)and ida['tool_sha256']==sha(q/'export-ida-r4-at-run.py');lines=0
 for f in ida['functions']:
  for v in f['lines']:
   b=bytes.fromhex(v['bytes']);at=v['original_file_offset']-header;assert code[at:at+len(b)]==b;lines+=1
 names=[['火球術','雷火術','殺鬼術','暗殺術','凝滯術','滅半術','複製術','地震術'],['造橋術','煉金術','召兵術','跳躍術','停時術','鳥瞰術','涉水術','傳送術']];entries=[]
 for group,base,counts,wanted in zip(['battle','map'],[0x2a38,0x2ab8],[0x2aa8,0x2b28],names):
  for i,name in enumerate(wanted):
   offset=header+0x1d780+base+i*12;b=raw[offset:offset+12];text=b.split(b'\0')[0].decode('big5');assert text.replace(' ','')==name
   entries.append(dict(group=group,index=i,name=name,text=text,ds_offset=base+i*12,file_offset=offset,raw_hex=b.hex(),uses_ds_offset=counts+i*2,level='proven-string-and-counter-consumer-only'))
 receipt=read(q/'cast-r5/receipt.json');assert receipt['state_equal']and receipt['go']=='go1.24.13';c=read(q/'cast-r5/control/trace.json');v=read(q/'cast-r5/observed/trace.json');assert c['configured']and c['completed']and v['completed']and c['keys']==v['keys']and c['mutations']==v['mutations']and c['initial']==v['initial']and c['charges']==v['charges']==[1,0,0,0,0,0,0,0]
 for n in ['before-fixture.state','after-fixture.state','final.state']:assert sha(q/'cast-r5/control'/n)==sha(q/'cast-r5/observed'/n)
 events=v['events'];effect=next(x for x in events if x['name']=='player-effect');assert effect['stack'][:8]==[0x74a,0xf67,3,1,1,0,0,1]and effect['bp_minus_4']==0 and effect['charges'][0]==1
 inside=[x for x in v['bitmaps']if effect['step']<=x['entry_step']<events[-1]['step']];pon=[x for x in inside if x['entry']==0x4f2];source=[x for x in inside if x['entry']==0x626 and x['args'][2:]==[12,75]]
 records=['a69fc9dfe79641d9ac4d3eb8d1d543d74c521be9c957e9c926fd0e6c9bcca256','940308e27b760d7c09c4afae871556192d593682c8bc40a757382be41c9c766d','61a5081819badb113d7f199757a5a81e8a27a6f308f2b7f9952c9cffb744b42d','969a56a413cc4bcb87bf4f4ed4917045168ded8cc0d4237de8ca0fa8d09f82dc']
 assert len(pon)==12 and [x['source_sha256']for x in pon]==[records[i]for i in [1,2,3,0]*3]and all(x['args'][2:]==[46,100]for x in pon)
 before=[x for x in source if x['return_step']<pon[0]['entry_step']];assert len(before)==4
 assert v['enemy'][2:4]==[0,0]and c['enemy']==v['enemy']and v['initial']['enemy'][2:4]==[6,10]
 cancelled=read(q/'cast-r4/observed/trace.json');assert cancelled['completed']and cancelled['charges'][0]==2 and not any(x['name']=='player-effect'for x in cancelled['events'])
 catalog=dict(schema=1,input='PAM.AY',input_sha256=sha(original),address_space='Original file offsets and runtime DS-relative offsets separately labelled',entries=entries,limits=['Names/counter consumers only; map effects and seven other battle spells not dynamically verified.'])
 a.catalog.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
 result=dict(status='passed-scoped-player-fireball-research',original_sha256=sha(original),ida_functions=len(ida['functions']),ida_lines_verified=lines,catalog_entries=16,full_state_equal=True,fixture_explicit=True,charges_before=2,charges_after=1,target_kind=6,target_count_before=10,target_count_after=0,source_commits_before_impact=4,pon_commits=12,source_xy=[96,75],target_xy=[368,100],effect_entry='runtime fixed load0110:0F67:345C / IDA MZ linear0x219CC',caller_return='runtime0F67:074A',effect_retf='runtime0F67:3661',cancel_refunds_charge=True,original_rng='Fixed complete source snapshot, no reroll; numeric seed unknown.',limits=['Controlled learned flag/resources/rear caster; not natural learning.','Four original source poses then twelve PON commits; reuse B timing contract with swapped side tables.','Production unchanged.'])
 a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
