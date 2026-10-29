#!/usr/bin/env python3
"""Independent original RAM/state and approved modifier verification."""
import argparse,gzip,hashlib,importlib.util,json,pathlib,struct,subprocess,tempfile
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser()
 for n in ['project','reader','out']:p.add_argument('--'+n,type=pathlib.Path,required=True)
 a=p.parse_args();r=a.project;q=r/'workplace/probe-20261023/graphics-first/battle-r1/tactics-r1';assert not a.out.exists();pam=r/'workplace/intake-20261023/sources/game/8sword/PAM.AY';assert sha(pam)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0';raw=pam.read_bytes();u=lambda at:struct.unpack_from('<H',raw,at)[0];code=bytearray(raw[u(8)*16:])
 for i in range(u(6)):
  at=u(24)+i*4;loc=u(at+2)*16+u(at);struct.pack_into('<H',code,loc,(struct.unpack_from('<H',code,loc)[0]+0x110)&65535)
 mod=importlib.util.spec_from_file_location('old',r/'tools/audit-ai-formation.py');old=importlib.util.module_from_spec(mod);mod.loader.exec_module(old)
 def predict(v,formation,pressure):
  candidates,_=old.evaluate(v,False);units=v['Friendly'];mapping=v['FriendlySlots'];attacker=v['Enemy'][v['EnemySlots'][v['SourceSlot']]]
  for c in candidates:
   if v['Route']=='special':continue
   if pressure and attacker['Kind']==3 and v['SourceSlot']<3 and units[mapping[v['SourceSlot']]]['Count']>0:c['Amount']=c['Amount']*75//100
   if formation and c['Slot']<3 and units[c['Unit']]['Kind']==1 and any(i!=c['Slot']and units[mapping[i]]['Count']>0 for i in range(3)):c['Amount']=c['Amount']*80//100
   encoded=(c['Amount']//v['Factors'][units[c['Unit']]['Kind']*2+1]+1)&65535;c['Loss']=0 if encoded<=1 else c['Count']if encoded>=c['Count']else encoded-1;c['Eliminates']=c['Loss']==c['Count']
  best=next(c for c in candidates if c['Slot']==v['OriginalSlot'])
  for c in candidates:
   better=c['Eliminates']if c['Eliminates']!=best['Eliminates']else c['Loss']*best['Count']>best['Loss']*c['Count']
   if better:best=c
  return candidates,best
 with tempfile.TemporaryDirectory()as tmp:
  indexes={};dirs={}
  for name,count in [('helpers',192),('battles',189)]:
   dest=pathlib.Path(tmp)/name;root=q/(name+'-r1-calls');subprocess.run([str(a.reader),'-calls',str(root),'-out',str(dest)],check=True);indexes[name]=read(dest/'index.json');dirs[name]=dest;assert len(indexes[name])==count
  def mem(group,key):
   item=indexes[group][key];b=gzip.decompress((dirs[group]/(item['memory_sha256']+'.ram.gz')).read_bytes());assert hashlib.sha256(b).hexdigest()==item['memory_sha256'];return b,item
  helper_count=0
  for root in sorted((q/'helpers-r1-calls').glob('*')):
   if not root.is_dir():continue
   t=read(root/'trace.json');name=root.name;b,before=mem('helpers',name+'/before-hook.state');_,after=mem('helpers',name+'/after-hook.state');final,finish=mem('helpers',name+'/final.state');get=lambda off:struct.unpack_from('<H',b,0x1e88*16+off)[0];side=t['side'];target,slots,total,source,sourceSlots=(0x56e8,0x6fb6,0x8ca4,0x5700,0x6fc2)if side=='player'else(0x5700,0x6fc2,0x8e60,0x56e8,0x6fb6);mapping=[get(slots+i*2)for i in range(6)];sourceMapping=[get(sourceSlots+i*2)for i in range(6)];ss=sourceMapping.index(0);ts=mapping.index(0);kind,count=get(source),get(source+2)
   pressure=kind==3 and ss<3 and get(target+mapping[ss]*4+2)>0;formation=ts<3 and get(target)==1 and any(i!=ts and get(target+mapping[i]*4+2)>0 for i in range(3));amount=(get(0x70ce+kind*4)*count)&65535
   if side=='player':amount//=((get(0x26ac)+5)&65535)
   else:amount=((amount//((5-get(0x26b2))&65535))*((get(0x26b8)+1)&65535))&65535
   assert t['raw']==before['registers'][0]==amount;expected=amount
   if t['mode']=='tactics'and pressure:expected=expected*75//100
   if t['mode']!='native'and formation:expected=expected*80//100
   assert t['pressure']==pressure and t['formation']==formation and t['amount']==after['registers'][0]==expected;assert before['normalized_except_ax_sha256']==after['normalized_except_ax_sha256']and before['memory_sha256']==after['memory_sha256']and before['dos_sha256']==after['dos_sha256'];hp=get(0x70d0+get(target)*4);assert finish['registers'][0]==((expected//hp+1)&65535)==t['encoded_return'];assert struct.unpack_from('<H',final,0x1e88*16+total)[0]==((hp*get(target+2)-expected)&65535)==t['remaining_total_hp'];assert struct.unpack_from('<H',final,0x1e88*16+target+2)[0]==get(target+2);assert sha(root/'final.state')==t['final_sha256'];hook=before['ip'];assert b[0xf67*16+hook:0xf67*16+hook+24]==code[0xe57*16+hook:0xe57*16+hook+24];helper_count+=1
  assert helper_count==48
  cases=[];battle_count=0
  for case in ['archer-front','archer-rear-target','archer-open-lane','archer-back','bird-front','melee-locked','special0']:
   summary={}
   for rules in ['native','formation','tactics']:
    d=q/'battles-r1-calls'/(case+'-'+rules);states=[];modes={}
    for mode in ['baseline','blind','aware']:
     root=d/mode;t=read(root/'trace.json');v=t['View'];key=case+'-'+rules+'/'+mode;before,_=mem('battles',key+'/before-decision.state');after,_=mem('battles',key+'/after-decision.state');final,entry=mem('battles',key+'/final.state');get=lambda off:struct.unpack_from('<H',before,0x1e88*16+off)[0]
     assert v['FriendlySlots']==[get(0x6fb6+i*2)for i in range(6)]and v['EnemySlots']==[get(0x6fc2+i*2)for i in range(6)]
     for i in range(6):assert v['Friendly'][i]==dict(Kind=get(0x56e8+i*4),Count=get(0x56ea+i*4))and v['Enemy'][i]==dict(Kind=get(0x5700+i*4),Count=get(0x5702+i*4))
     candidates,best=predict(v,rules!='native',rules=='tactics'and mode=='aware');selected=v['OriginalSlot']if mode=='baseline'else best['Slot']
     if mode!='baseline':assert t['Decision']['Candidates']==candidates and t['Decision']['SuggestedSlot']==selected
     actual,_=predict(v,rules!='native',rules=='tactics');pred=next(c for c in actual if c['Slot']==selected);assert pred==t['Prediction'];want=t['BeforeUnits'].copy();want[pred['Unit']*2+1]-=pred['Loss']
     if want[pred['Unit']*2+1]==0:want[pred['Unit']*2]=0
     assert want==list(struct.unpack_from('<24H',final,0x1e88*16+0x56e8))==t['AfterUnits'];expected=bytearray(before)
     for c in t['Changes']:
      if c['Phase']=='policy-target':assert c['New']==selected+(0 if v['Route']=='special'else 7);struct.pack_into('<H',expected,c['Segment']*16+c['Offset'],c['New'])
     assert bytes(expected)==after and entry['steps']==t['EndStep']and sha(root/'final.state')==t['StateSHA256'];states.append(sha(root/'before-decision.state'));modes[mode]=dict(selected=selected,loss=pred['Loss'],amount=pred['Amount'],final=sha(root/'final.state'));battle_count+=1
    assert len(set(states))==1
    if rules!='tactics':assert modes['blind']==modes['aware']
    elif case in ['archer-front','archer-rear-target']:assert modes['blind']['selected']==0 and modes['aware']['selected']==(1 if case=='archer-front'else 3)and modes['blind']['loss']==9 and modes['aware']['loss']==10
    else:assert modes['blind']==modes['aware']
    summary[rules]=modes
   cases.append(dict(case=case,modes=summary))
  assert battle_count==63
 result=dict(status='passed-controlled-tactics',helper_calls=48,battle_calls=63,decoded_states=381,changed_tactics_cases=2,unchanged_old_rule_cases=14,results=cases,reader_sha256=sha(a.reader),pam_sha256=sha(pam),scope='Controlled approved added rules, not original native parity or natural battle.');a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='results'}))
if __name__=='__main__':main()
