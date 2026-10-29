#!/usr/bin/env python3
"""Independent original earthquake evidence and actual Go canvas displacement audit."""
import argparse,gzip,hashlib,json,os,pathlib,struct
from PIL import Image,ImageChops
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def draw_audit(gui,phase):
 d=gui/'vfx-draw';m=read(d/(phase+'.json'));assert m['phase']==phase and m['frame_guest_pure']and m['fixture'];assert sha(d/(phase+'-before.state'))==sha(d/(phase+'-after.state'))==m['guest_state_sha256']
 base=Image.open(d/(phase+'-base.png')).convert('RGBA');actual=Image.open(d/(phase+'-central.png')).convert('RGBA');presented=Image.open(d/(phase+'-presented.png')).convert('RGBA');assert base.size==actual.size==(1920,1200)and presented.size==(2944,1264);assert presented.crop((512,64,2432,1264)).tobytes()==actual.tobytes()
 shift=m['vfx']['Shift'][1];assert m['vfx']['Shift'][0]==0 and shift==(6 if phase=='quake-low'else 18)
 raw=gzip.decompress((d/(phase+'-native-text-mask.bin.gz')).read_bytes());assert len(raw)==128000 and set(raw)<={0,1};mask=Image.frombytes('L',(640,200),bytes(v*255 for v in raw)).resize(base.size,Image.Resampling.NEAREST)
 expected=base.copy()
 for y in range(0,1200):expected.paste(base.crop((0,min(y+shift,1199),1920,min(y+shift,1199)+1)),(0,y))
 shifted=Image.new('L',base.size);shifted.paste(mask,(0,-shift))
 for y in range(1200-shift,1200):shifted.paste(mask.crop((0,1199,1920,1200)),(0,y))
 protect=ImageChops.lighter(mask,shifted);expected.paste(base,(0,0),protect)
 assert expected.tobytes()==actual.tobytes(),'independent quake row-copy/text protection mismatch'
 changed=sum(a!=b for a,b in zip(base.getdata(),actual.getdata()));assert changed>0
 return dict(phase=phase,shift=shift,draw=m['draw'],step=m['step'],changed_pixels=changed,frame_sha256=sha(d/(phase+'-central.png')),guest_sha256=m['guest_state_sha256'])
def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['research','draw']);p.add_argument('--project',type=pathlib.Path);p.add_argument('--gui',type=pathlib.Path);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();assert os.getuid()==1000 and not a.out.exists()
 if a.action=='draw':result=dict(status='passed-quake-actual-draw',draws=[draw_audit(a.gui,k)for k in ['quake-low','quake-high']])
 else:
  r=a.project;q=r/'workplace/probe-20261023/graphics-first/battle-r1/player-spells-r1';t=q/'quake-r1/original-r2';original=r/'workplace/intake-20261023/sources/game/8sword/PAM.AY';assert sha(original)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0';raw=original.read_bytes();u=lambda at:struct.unpack_from('<H',raw,at)[0];header=u(8)*16;code=bytearray(raw[header:])
  for i in range(u(6)):
   off,seg=struct.unpack_from('<HH',raw,u(24)+i*4);at=seg*16+off;struct.pack_into('<H',code,at,(struct.unpack_from('<H',code,at)[0]+0x1000)&65535)
  ida=read(q/'ida-r4/ida-spells-r4.json');assert ida['source_sha256']==sha(original)and ida['tool']=='IDA 9.4';lines=0
  for f in ida['functions']:
   for v in f['lines']:
    data=bytes.fromhex(v['bytes']);at=v['original_file_offset']-header;assert code[at:at+len(data)]==data;lines+=1
  by={v['ida_linear']:v for f in ida['functions']if f['start']==0x1e8a4 for v in f['lines']}
  for at,b in [(0x1ef69,'b80d50'),(0x1efd2,'b80df0'),(0x1f03b,'b80da0'),(0x1f0a4,'b80d50'),(0x1f10d,'b80d00'),(0x1f11f,'837ef432'),(0x1f1c6,'e8092a')]:assert by[at]['bytes']==b
  records={'a69fc9dfe79641d9ac4d3eb8d1d543d74c521be9c957e9c926fd0e6c9bcca256','940308e27b760d7c09c4afae871556192d593682c8bc40a757382be41c9c766d','61a5081819badb113d7f199757a5a81e8a27a6f308f2b7f9952c9cffb744b42d','969a56a413cc4bcb87bf4f4ed4917045168ded8cc0d4237de8ca0fa8d09f82dc'};cases=[]
  for name in ['mixed','sparse','cancel']:
   folder=t/name;c=read(folder/'control/trace.json');v=read(folder/'observed/trace.json');receipt=read(folder/'receipt.json');assert receipt['state_equal']and receipt['go']=='go1.24.13'and c['completed']and v['completed']and c['keys']==v['keys']and c['mutations']==v['mutations']and c['initial']==v['initial']
   for n in ['before-fixture.state','after-fixture.state','final.state']:assert sha(folder/'control'/n)==sha(folder/'observed'/n)
   assert sha(folder/'observed/final.state')==sha(q/'quake-r1/original-r1'/name/'observed/final.state')
   charges=[0]*8;charges[7]=2 if name=='cancel'else 1;assert c['charges']==v['charges']==charges;start=next(e for e in v['events']if e['name']=='player-turn');entries=[e for e in v['events']if e['name']=='player-quake'];pans=v['quake_pans'];damage=[e for e in v['events']if e['name']=='quake-damage'];targets=[]
   if name=='cancel':assert not entries and not pans and not damage and v['enemy']==start['enemy']
   else:
    assert len(entries)==1 and entries[0]['bp_minus_4']==7 and len(pans)==250;assert [x['phase']for x in pans]==[1,2,3,4,5]*50;assert [x['port_value']for x in pans]==[[980,x]for x in [0x500d,0xf00d,0xa00d,0x500d,0x000d]]*50
    pon=[b for b in v['bitmaps']if b['entry']==0x4f2 and entries[0]['step']<=b['entry_step']<pans[-1]['step']];assert len(pon)==250
    positions=[[(x&255),(x>>8)]for x in entries[0]['enemy_positions']]
    for i,b in enumerate(pon):assert b['source_sha256']in records and b['args'][2:]in positions and b['return_step']<pans[i]['step']and(i==249 or pans[i]['step']<pon[i+1]['entry_step'])
    live=[i for i,id in enumerate(start['enemy_map'])if id<6 and start['enemy'][id*2+1]>0];assert len(damage)==len(live)
    for e in damage:
     args=e['stack'][2:8];assert e['stack'][:2]==[0xc59,0xf67]and args[0]==3;targets.append(args[1]);id=start['enemy_map'][args[1]];assert v['enemy'][id*2:id*2+2]==[0,0]
    assert targets==live
   cases.append(dict(case=name,pans=len(pans),pon=0 if name=='cancel'else 250,targets=targets,charges=charges,full_state_equal=True,final_state_sha256=sha(folder/'observed/final.state')))
  result=dict(status='passed-scoped-player-quake-research',pam_sha256=sha(original),ida_lines_verified=lines,cases=cases,phases=[0x50,0xf0,0xa0,0x50,0],hd_vertical_shifts=[6,18,12,6,0],original_damage_helper='IDA MZ loader sub_21BD2; runtime0F67:3662, parent return0F67:0C59',limits=['Controlled rear caster/learned/charges and sparse counts; no natural-learning claim.','Original RNG unchanged; original r1/r2 full final states agree.','r1 missed one of five pan hooks; source PON evidence always contained250.'])
  resumed=q/'quake-r1/resume-r1'
  if resumed.exists():
   source=t/'sparse/observed/player-quake.state';native=resumed/'machine/final.state'
   for runner in ['machine','PAM','PRE']:assert sha(resumed/runner/'loaded.state')==sha(source)and sha(resumed/runner/'final.state')==sha(native)
   assert sha(native)==sha(q/'quake-r1/focused-r1/quake-sparse/final.state')and sha(native)!=sha(t/'sparse/observed/final.state')
   result['snapshot_resume_limit']=dict(loaded_states_equal=True,three_unhooked_original_runners_equal=True,hd_observer_matches_resumed_original=True,continuous_original_different=True,resumed_sha256=sha(native),continuous_sha256=sha(t/'sparse/observed/final.state'),cause='unknown',production_rendering_changed_to_fit=False)
  events_path=q/'quake-r1/duplicate-events-r1/receipt.json'
  if events_path.exists():
   observed=read(events_path);duplicates=[e for e in observed['events']if e['duplicate']];assert len(duplicates)==observed['duplicate_notifications']==1
   pos=observed['events'].index(duplicates[0]);previous=observed['events'][pos-1]
   for key in ['phase','pon_returns','ss','bp','sp','port','value']:assert previous[key]==duplicates[0][key]
   result['duplicate_notifications']=dict(count=1,phase=duplicates[0]['phase'],native_event=duplicates[0],receipt_sha256=sha(events_path),method=observed['method'])
 a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
