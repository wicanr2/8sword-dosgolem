#!/usr/bin/env python3
"""030: independent MZ bytes, raw-state amount checks and scoped control pairs."""
import argparse,gzip,hashlib,json,pathlib,struct
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();assert not a.out.exists();r=a.project;q=r/'workplace/probe-20261023/graphics-first/battle-r1/formation-hooks-r1';ida=read(q/'ida-formation-hooks-r2.json');pam=r/'workplace/intake-20261023/sources/game/8sword/PAM.AY';raw=pam.read_bytes();assert sha(pam)==ida['source_sha256'] and ida['function_count']==521 and ida['tool']=='IDA 9.4'
 assert sha(r/'workplace/probe-20261023/text-first/PAM.i64')==ida['database_sha256'] and sha(r/'tools/export-formation-hooks-ida.py')==ida['tool_sha256']
 u16=lambda at:struct.unpack_from('<H',raw,at)[0];header=u16(8)*16
 def relocated(base):
  code=bytearray(raw[header:])
  for i in range(u16(6)):
   p=u16(24)+i*4;at=u16(p+2)*16+u16(p);struct.pack_into('<H',code,at,(struct.unpack_from('<H',code,at)[0]+base)&65535)
  return code
 idacode=relocated(0x1000);runtime=relocated(0x110);lines=0
 for f in ida['bodies']:
  for line in f['lines']:
   offset=line['ida_linear']-0x10000;b=bytes.fromhex(line['bytes']);assert line['original_file_offset']==offset+header and idacode[offset:offset+len(b)]==b;lines+=1
 bodies={f['start']:f for f in ida['bodies']};assert 0x1faa2 in bodies and 0x1fb02 in bodies and any(x['ida_linear']==0x21846 for x in bodies[0x1fb02]['xrefs'])
 index=read(q/'decoded-r1/index.json');assert len(index)==84
 def memory(meta):
  blob=gzip.decompress((q/'decoded-r1'/(meta['memory_sha256']+'.ram.gz')).read_bytes());assert hashlib.sha256(blob).hexdigest()==meta['memory_sha256'];return blob
 changed=0;pairs=[]
 for side in ['player','enemy']:
  units,slots,acc,attack,hook=(0x56e8,0x6fb6,0x8ca4,0x5700,0x1560)if side=='player'else(0x5700,0x6fc2,0x8e60,0x56e8,0x15ca)
  for case in ['front-ally','alone','rear-ally','rear-target','other-kind','two-allies']:
   name=side+'-'+case;root=q/'calls-r1'/name;observe_before=index[name+'/observe/before-hook.state'];mem=memory(observe_before);word=lambda off:struct.unpack_from('<H',mem,0x1e88*16+off)[0]
   mapping=[word(slots+i*2)for i in range(6)];target=mapping.index(0);eligible=target<3 and word(units)==1 and word(units+2)>0 and any(i!=target and word(units+mapping[i]*4+2)>0 for i in range(3))
   amount=(word(0x70ce+word(attack)*4)*word(attack+2))&65535
   if side=='player':amount//=word(0x26ac)+5
   else:amount=((amount//(5-word(0x26b2)))*((word(0x26b8)+1)&65535))&65535
   hp=word(0x70d0+word(units)*4);assert amount==400 and word(units+2)==31
   at=0xe57*16+hook;expected=runtime[at:at+24];actual=mem[0xf67*16+hook:0xf67*16+hook+24];assert actual==expected
   for mode in ['baseline','observe','formation']:
    t=read(root/mode/'trace.json');final=index[name+'/'+mode+'/final.state'];final_mem=memory(final);get_final=lambda off:struct.unpack_from('<H',final_mem,0x1e88*16+off)[0];reduced=amount*80//100 if mode=='formation'and eligible else amount
    assert t['side']==side and t['case']==case and t['mode']==mode and t['eligible']==eligible and t['amount_before']==amount and t['amount_after']==reduced and t['hp']==hp and t['hook_ip']==hook and t['hook_bytes']==expected.hex()
    assert final['registers'][0]==reduced//hp+1==t['encoded_return'] and get_final(acc)==hp*31-reduced==t['remaining_total_hp'] and get_final(units+2)==31
    assert sha(root/mode/'final.state')==t['final_state_sha256']
    if mode!='baseline':
     before=index[name+'/'+mode+'/before-hook.state'];after=index[name+'/'+mode+'/after-hook.state'];assert before['normalized_except_ax_sha256']==after['normalized_except_ax_sha256'] and before['dos_sha256']==after['dos_sha256'] and before['memory_sha256']==after['memory_sha256']
     assert before['registers'][0]==amount and after['registers'][0]==reduced and before['ip']==after['ip']==hook
   assert sha(root/'baseline/final.state')==sha(root/'observe/final.state')
   if eligible:changed+=1;assert sha(root/'baseline/final.state')!=sha(root/'formation/final.state')
   else:assert sha(root/'baseline/final.state')==sha(root/'formation/final.state')
   pairs.append(dict(side=side,case=case,eligible=eligible,amount=amount,formation_amount=amount*80//100 if eligible else amount))
 assert changed==4 and not(q/'vet.log').read_text()
 prod=read(r/'preserved/ai-toolbar-audit-r1.json')
 for n,h in prod['programs'].items():assert sha(r/'workplace/player'/n)==h
 for n,h in prod['source_inputs'].items():assert sha(r/n)==h
 for n,h in prod['asset_hashes'].items():assert sha(r/'workplace/player/assets-painted-r66'/n)==h
 browser=read(q.parent/'troop-traits-r1/toolbar-browser-r1.json');assert browser['status']=='passed-interactions-only' and browser['rules_locked_during_battle'] and browser['ai_independent']
 result=dict(status='passed-scoped-original-helper-controls',ida_lines=lines,ida_sha256=sha(q/'ida-formation-hooks-r2.json'),original_calls=36,decoded_states=84,read_only_pairs=12,mitigated_pairs=4,unaffected_pairs=8,callback_changes='AX only; full serialized machine state excluding AX and DOS section equal',production_programs_unchanged=7,production_source_inputs_unchanged=181,production_assets_unchanged=525,source_sha256=sha(pam),database_sha256=ida['database_sha256'],pairs=pairs,limits=['Isolated helper calls with controlled arguments and fields; no normal battle or final unit-count acceptance.','Toolbar is HTML interaction prototype; its screenshot capture timeout remains outside acceptance.','Rule mode/save lifecycle still DRAFT; no production promotion.'])
 a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k in ['status','ida_lines','original_calls','read_only_pairs','mitigated_pairs']}))
if __name__=='__main__':main()
