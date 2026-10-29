#!/usr/bin/env python3
"""Independent MZ/caller and original multi-target thunder observations."""
import argparse,hashlib,json,os,pathlib,struct
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser()
 for n in ['project','out']:p.add_argument('--'+n,type=pathlib.Path,required=True)
 a=p.parse_args();r=a.project;q=r/'workplace/probe-20261023/graphics-first/battle-r1/player-spells-r1';t=q/'thunder-r1';assert os.getuid()==1000 and not a.out.exists()
 original=r/'workplace/intake-20261023/sources/game/8sword/PAM.AY';assert sha(original)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0';raw=original.read_bytes();u=lambda at:struct.unpack_from('<H',raw,at)[0];header=u(8)*16;code=bytearray(raw[header:])
 for i in range(u(6)):
  off,seg=struct.unpack_from('<HH',raw,u(24)+i*4);at=seg*16+off;struct.pack_into('<H',code,at,(struct.unpack_from('<H',code,at)[0]+0x1000)&65535)
 ida=read(q/'ida-r4/ida-spells-r4.json');assert ida['source_sha256']==sha(original)and ida['tool']=='IDA 9.4';lines=0
 for f in ida['functions']:
  for v in f['lines']:
   data=bytes.fromhex(v['bytes']);at=v['original_file_offset']-header;assert code[at:at+len(data)]==data;lines+=1
 caller=next(f for f in ida['functions']if f['start']==0x1e8a4);call=next(v for v in caller['lines']if v['ida_linear']==0x1ea83);assert 'sub_219CC'in call['instruction']and call['bytes']=='e8462f';assert 0x1ea86-0x1e570==0x516
 records=['a69fc9dfe79641d9ac4d3eb8d1d543d74c521be9c957e9c926fd0e6c9bcca256','940308e27b760d7c09c4afae871556192d593682c8bc40a757382be41c9c766d','61a5081819badb113d7f199757a5a81e8a27a6f308f2b7f9952c9cffb744b42d','969a56a413cc4bcb87bf4f4ed4917045168ded8cc0d4237de8ca0fa8d09f82dc'];cases=[]
 for name,expected in [('mixed',4),('sparse',1),('cancel',0)]:
  folder=t/name;c=read(folder/'control/trace.json');v=read(folder/'observed/trace.json');receipt=read(folder/'receipt.json');assert receipt['state_equal']and receipt['go']=='go1.24.13'and c['completed']and v['completed']and c['configured']and c['keys']==v['keys']and c['mutations']==v['mutations']and c['initial']==v['initial']
  for n in ['before-fixture.state','after-fixture.state','final.state']:assert sha(folder/'control'/n)==sha(folder/'observed'/n)
  charges=[0]*8;charges[1]=2 if name=='cancel'else 1;assert c['charges']==v['charges']==charges and c['enemy']==v['enemy']
  events=v['events'];effects=[e for e in events if e['name']=='player-effect'];assert len(effects)==expected
  turn=next(e for e in events if e['name']=='player-turn');mapping=turn['enemy_map'];live=[i for i,id in enumerate(mapping)if id<6 and turn['enemy'][id*2+1]>0];slots=[]
  point=lambda table,row,col: [(table[row*3+col]&255)*8,table[row*3+col]>>8]
  targets=[]
  for ordinal,e in enumerate(effects):
   args=e['stack'][2:8];assert e['stack'][:2]==[0x516,0xf67]and e['bp_minus_4']==1 and args[0]==3 and args[2:4]==[1,0]and args[1]==args[4]*3+args[5];slots.append(args[1]);end=effects[ordinal+1]['step']if ordinal+1<len(effects)else events[-1]['step'];inside=[b for b in v['bitmaps']if e['step']<=b['entry_step']<end];pon=[b for b in inside if b['entry']==0x4f2];source=point(e['player_positions'],args[2],args[3]);target=point(e['enemy_positions'],args[4],args[5]);poses=[b for b in inside if b['entry']==0x626 and b['args'][2:]==[source[0]//8,source[1]]and b['return_step']<pon[0]['entry_step']]
   assert len(poses)==4 and len(pon)==12 and [b['source_sha256']for b in pon]==[records[i]for i in [1,2,3,0]*3];assert all(b['args'][2:]==[target[0]//8,target[1]]for b in pon);assert all(b['entry_cycles']<b['return_cycles']for b in poses+pon);targets.append(dict(slot=args[1],source=source,target=target,poses=4,pon=12,source_cycle_intervals=[poses[i+1]['return_cycles']-poses[i]['return_cycles']for i in range(3)]))
  if name!='cancel':assert slots==live and len(live)==expected and not any(e['name']=='target-selection'for e in events)
  else:assert c['enemy']==turn['enemy']
  cases.append(dict(case=name,spell=1,effects=expected,charged_once=name!='cancel',final_charges=charges,targets=targets,initial_enemy=turn['enemy'],final_enemy=v['enemy'],full_state_equal=True,final_state_sha256=sha(folder/'observed/final.state')))
 result=dict(status='passed-scoped-player-thunder-research',pam_sha256=sha(original),ida_lines_verified=lines,cases=cases,source_and_target_tables='Player DS:703C, enemy DS:701E',caller_return='fixed-load runtime0F67:0516, spell selector1',rng='Fixed full original snapshot, no reroll; numeric seed unknown',limits=['Controlled rear caster, learned flag and two thunder uses. No natural-learning claim.','Mixed four live/two empty; sparse one live/five empty; original wrapper charges once and skips empty slots.','No production changes authorized until READY.'])
 resumed=t/'resume-r1'
 if resumed.exists():
  source=t/'sparse/observed/player-effect.state'
  for name in ['machine','PAM','PRE']:assert sha(resumed/name/'loaded.state')==sha(source)and sha(resumed/name/'final.state')==sha(resumed/'machine/final.state')
  assert sha(resumed/'machine/final.state')==sha(t/'runtime-r1/player-thunder-sparse/final.state')and sha(resumed/'machine/final.state')!=sha(t/'sparse/observed/final.state')
  result['snapshot_resume_limit']=dict(loaded_states_equal=True,three_unhooked_original_runners_equal=True,hd_observer_matches_resumed_original=True,continuous_original_different=True,resumed_sha256=sha(resumed/'machine/final.state'),continuous_sha256=sha(t/'sparse/observed/final.state'),cause='unknown',production_rendering_changed_to_fit=False)
 a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
