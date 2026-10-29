#!/usr/bin/env python3
"""Independent original MZ, menu/target and sampled exorcism event audit."""
import argparse,hashlib,json,os,pathlib,struct
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser()
 for n in ['project','out']:p.add_argument('--'+n,type=pathlib.Path,required=True)
 a=p.parse_args();r=a.project;q=r/'workplace/probe-20261023/graphics-first/battle-r1/player-spells-r1';t=q/'exorcism-r1/original-r4';assert os.getuid()==1000 and not a.out.exists()
 original=r/'workplace/intake-20261023/sources/game/8sword/PAM.AY';assert sha(original)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0';raw=original.read_bytes();u=lambda at:struct.unpack_from('<H',raw,at)[0];header=u(8)*16;code=bytearray(raw[header:])
 for i in range(u(6)):
  off,seg=struct.unpack_from('<HH',raw,u(24)+i*4);at=seg*16+off;struct.pack_into('<H',code,at,(struct.unpack_from('<H',code,at)[0]+0x1000)&65535)
 ida=read(q/'ida-r4/ida-spells-r4.json');assert ida['source_sha256']==sha(original)and ida['tool']=='IDA 9.4';lines=0
 for f in ida['functions']:
  for v in f['lines']:
   data=bytes.fromhex(v['bytes']);at=v['original_file_offset']-header;assert code[at:at+len(data)]==data;lines+=1
 caller=next(f for f in ida['functions']if f['start']==0x1e8a4);by={v['ida_linear']:v for v in caller['lines']}
 for at,b in [(0x1eae2,'83fe06'),(0x1eae7,'83fe0f'),(0x1ebb4,'83fe06'),(0x1ebbc,'83fe0f'),(0x1ecb7,'e8122d')]:assert by[at]['bytes']==b
 assert 'sub_219CC'in by[0x1ecb7]['instruction']and 0x1ecba-0x1e570==0x74a
 records=['a69fc9dfe79641d9ac4d3eb8d1d543d74c521be9c957e9c926fd0e6c9bcca256','940308e27b760d7c09c4afae871556192d593682c8bc40a757382be41c9c766d','61a5081819badb113d7f199757a5a81e8a27a6f308f2b7f9952c9cffb744b42d','969a56a413cc4bcb87bf4f4ed4917045168ded8cc0d4237de8ca0fa8d09f82dc'];cases=[]
 for name,expected in [('ghost',1),('ordinary',1),('no-ghost',0),('cancel',0)]:
  folder=t/name;c=read(folder/'control/trace.json');v=read(folder/'observed/trace.json');receipt=read(folder/'receipt.json');assert receipt['state_equal']and receipt['go']=='go1.24.13'and c['completed']and v['completed']and c['configured']and c['keys']==v['keys']and c['mutations']==v['mutations']and c['initial']==v['initial']
  for n in ['before-fixture.state','after-fixture.state','final.state']:assert sha(folder/'control'/n)==sha(folder/'observed'/n)
  charges=[0]*8;charges[2]=1;assert c['charges']==v['charges']==charges and c['enemy']==v['enemy']
  events=v['events'];effects=[e for e in events if e['name']=='player-effect'];assert len(effects)==expected
  turn=next(e for e in events if e['name']=='player-turn');target=None
  if expected:
   e=effects[0];args=e['stack'][2:8];assert e['stack'][:2]==[0x74a,0xf67]and e['bp_minus_4']==2 and args[0]==3 and args[2:4]==[1,0]and args[1]==args[4]*3+args[5]
   id=turn['enemy_map'][args[1]];kind=turn['enemy'][id*2];assert (6<=kind<=15)==(name=='ghost')
   inside=[b for b in v['bitmaps']if e['step']<=b['entry_step']<events[-1]['step']];pon=[b for b in inside if b['entry']==0x4f2]
   point=lambda table,row,col:[(table[row*3+col]&255)*8,table[row*3+col]>>8]
   source=point(e['player_positions'],args[2],args[3]);dest=point(e['enemy_positions'],args[4],args[5]);poses=[b for b in inside if b['entry']==0x626 and b['args'][2:]==[source[0]//8,source[1]]and b['return_step']<pon[0]['entry_step']]
   assert len(poses)==4 and len(pon)==12 and [b['source_sha256']for b in pon]==[records[i]for i in [1,2,3,0]*3];assert all(b['args'][2:]==[dest[0]//8,dest[1]]for b in pon);assert all(b['entry_cycles']<b['return_cycles']for b in poses+pon)
   changed=[i for i in range(6)if turn['enemy'][i*2:i*2+2]!=v['enemy'][i*2:i*2+2]];assert changed==[id]
   target=dict(slot=args[1],unit=id,kind=kind,source=source,target=dest,before_count=turn['enemy'][id*2+1],after_count=v['enemy'][id*2+1],poses=4,pon=12)
  else:
   assert c['enemy']==turn['enemy']
   if name=='no-ghost':assert not any(e['name']=='target-selection'for e in events)and not any(6<=k<=15 for k in turn['enemy'][::2])
   else:assert any(e['name']=='target-selection'for e in events)and any(k['why']=='cancel original target menu'for k in v['keys'])
  cases.append(dict(case=name,spell=2,effects=expected,final_charges=charges,target=target,full_state_equal=True,final_state_sha256=sha(folder/'observed/final.state')))
 result=dict(status='passed-scoped-player-exorcism-research',pam_sha256=sha(original),ida_lines_verified=lines,ida_export_sha256=sha(q/'ida-r4/ida-spells-r4.json'),cases=cases,source_and_target_tables='Player DS:703C, enemy DS:701E',caller_return='fixed-load runtime0F67:074A, selector2',rng='Fixed full original snapshot, no reroll; numeric seed unknown',limits=['Controlled rear caster, learned flag/resources and no-ghost fixture; not natural learning.','Original allows ordinary target when a kind6..15 exists; original damage-word semantics outside eligible branch are not reimplemented or corrected.','No-ghost and target Escape consume once without effect in sampled original; no refund assumed.','No production changes authorized until READY.'])
 a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
