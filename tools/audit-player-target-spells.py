#!/usr/bin/env python3
"""Independent original MZ/IDA and fixed-state assassination/halve audit."""
import argparse,hashlib,json,os,pathlib,struct
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser()
 for n in ['project','out']:p.add_argument('--'+n,type=pathlib.Path,required=True)
 a=p.parse_args();r=a.project;q=r/'workplace/probe-20261023/graphics-first/battle-r1/player-spells-r1';t=q/'target-spells-r1/original-r1';assert os.getuid()==1000 and not a.out.exists()
 original=r/'workplace/intake-20261023/sources/game/8sword/PAM.AY';assert sha(original)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0';raw=original.read_bytes();u=lambda at:struct.unpack_from('<H',raw,at)[0];header=u(8)*16;code=bytearray(raw[header:])
 for i in range(u(6)):
  off,seg=struct.unpack_from('<HH',raw,u(24)+i*4);at=seg*16+off;struct.pack_into('<H',code,at,(struct.unpack_from('<H',code,at)[0]+0x1000)&65535)
 ida=read(q/'ida-r4/ida-spells-r4.json');assert ida['source_sha256']==sha(original)and ida['tool']=='IDA 9.4';lines=0
 for f in ida['functions']:
  for v in f['lines']:
   data=bytes.fromhex(v['bytes']);at=v['original_file_offset']-header;assert code[at:at+len(data)]==data;lines+=1
 by={v['ida_linear']:v for f in ida['functions']if f['start']==0x1e8a4 for v in f['lines']}
 for at,b in [(0x1ec54,'9ace2c8726'),(0x1ec5a,'b93200'),(0x1ec62,'a1ae26'),(0x1ec6f,'050a00'),(0x1ec74,'7703'),(0x1ed61,'d1e8'),(0x1ed63,'40'),(0x1ecb7,'e8122d')]:assert by[at]['bytes']==b
 assert 'sub_219CC'in by[0x1ecb7]['instruction']and 0x1ecba-0x1e570==0x74a
 records=['a69fc9dfe79641d9ac4d3eb8d1d543d74c521be9c957e9c926fd0e6c9bcca256','940308e27b760d7c09c4afae871556192d593682c8bc40a757382be41c9c766d','61a5081819badb113d7f199757a5a81e8a27a6f308f2b7f9952c9cffb744b42d','969a56a413cc4bcb87bf4f4ed4917045168ded8cc0d4237de8ca0fa8d09f82dc'];cases=[];dice=[];input_hashes=set()
 for name in ['assassination-low','assassination-high','assassination-cancel','half-even','half-odd','half-cancel']:
  folder=t/name;c=read(folder/'control/trace.json');v=read(folder/'observed/trace.json');receipt=read(folder/'receipt.json');input_hashes.add(receipt['input_sha256']);assert receipt['state_equal']and receipt['go']=='go1.24.13'and c['completed']and v['completed']and c['configured']and c['keys']==v['keys']and c['mutations']==v['mutations']and c['initial']==v['initial']
  for n in ['before-fixture.state','after-fixture.state','final.state']:assert sha(folder/'control'/n)==sha(folder/'observed'/n)
  spell=3 if name.startswith('assassination')else 5;charges=[0]*8;charges[spell]=1;assert c['charges']==v['charges']==charges and c['enemy']==v['enemy']
  events=v['events'];effects=[e for e in events if e['name']=='player-effect'];die_events=[e for e in events if e['name']=='assassination-die'];chance=None;expected=0 if name.endswith('cancel')else 1
  if spell==3 and not name.endswith('cancel'):
   assert len(die_events)==1;e=die_events[0];die=e['registers'][2];stat=0 if name.endswith('low')else 4;assert 0<=die<50 and e['chance_stat']==stat;threshold=stat*10+10;expected=int(threshold>die);dice.append(die);chance=dict(stat=stat,die=die,threshold=threshold,success=bool(expected))
  else:assert not die_events
  assert len(effects)==expected;turn=next(e for e in events if e['name']=='player-turn');target=None
  if expected:
   e=effects[0];args=e['stack'][2:8];assert e['stack'][:2]==[0x74a,0xf67]and e['bp_minus_4']==spell and args[0]==3 and args[2:4]==[1,0]and args[1]==args[4]*3+args[5]
   id=turn['enemy_map'][args[1]];before=turn['enemy'][id*2+1];after=v['enemy'][id*2+1];assert before>0
   assert after==(0 if spell==3 else before-(before//2+1))
   if spell==5:assert before%2==int(name.endswith('odd'))
   inside=[b for b in v['bitmaps']if e['step']<=b['entry_step']<events[-1]['step']];pon=[b for b in inside if b['entry']==0x4f2];point=lambda table,row,col:[(table[row*3+col]&255)*8,table[row*3+col]>>8]
   source=point(e['player_positions'],args[2],args[3]);dest=point(e['enemy_positions'],args[4],args[5]);poses=[b for b in inside if b['entry']==0x626 and b['args'][2:]==[source[0]//8,source[1]]and b['return_step']<pon[0]['entry_step']]
   assert len(poses)==4 and len(pon)==12 and [b['source_sha256']for b in pon]==[records[i]for i in [1,2,3,0]*3];assert all(b['args'][2:]==[dest[0]//8,dest[1]]for b in pon)
   assert [i for i in range(6)if turn['enemy'][i*2:i*2+2]!=v['enemy'][i*2:i*2+2]]==[id]
   target=dict(slot=args[1],unit=id,source=source,target=dest,before_count=before,after_count=after,poses=4,pon=12)
  else:assert c['enemy']==turn['enemy']
  if name.endswith('cancel'):assert any(k['why']=='cancel original target menu'for k in v['keys'])
  cases.append(dict(case=name,spell=spell,effects=expected,chance=chance,final_charges=charges,target=target,full_state_equal=True,final_state_sha256=sha(folder/'observed/final.state')))
 assert len(input_hashes)==1 and len(dice)==2 and dice[0]==dice[1]
 result=dict(status='passed-scoped-player-target-spells-research',pam_sha256=sha(original),ida_lines_verified=lines,ida_export_sha256=sha(q/'ida-r4/ida-spells-r4.json'),initial_state_sha256=input_hashes.pop(),fixed_die=dice[0],cases=cases,caller_return='fixed-load runtime0F67:074A, selectors3/5',rng='Same full original initial state, predeclared stats0/4, original rand return untouched, no reroll; numeric seed unknown',limits=['Controlled rear caster, learned/resources, stat0/4 or odd enemy counts; not natural learning.','Original threshold and half-count observations only; HD does not implement damage or RNG.','Same shared B kernel; one representative new spell GUI, not per-spell natural-use proof.'])
 a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
