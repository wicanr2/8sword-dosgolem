#!/usr/bin/env python3
"""Independent v5 identity, wolf arithmetic, retreat, save and X11 checks."""
import argparse,copy,hashlib,importlib.util,json,os,struct
from pathlib import Path
from PIL import Image
REL='workplace/probe-20261023/graphics-first/battle-r1/reinforcement-battle-r1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--images',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000;r=a.project;q=r/REL
 sp=importlib.util.spec_from_file_location('prep',r/'tools/prepare-reinforcement-battle.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);h=m.helper(r);deps=h.dependencies(r);assert deps==read(q/'baseline.json');parent=read(q/'parent.json');assert parent['archive_sha256']==sha(r/'preserved/reinforcement-camps-r1.json')
 assert parent['binary_sha256']==sha(q/'reinforcement-ui')==hashlib.sha256(h.stored(r,m.PARENT,'/'+m.PARENT+'/reinforcement-ui')).hexdigest()
 original=read(q/'initial-session/gamedata.ay.army.json');assert original['schema']=='eightsword-owned-world-save/5';assert sha(q/'initial-session/gamedata.ay.army.json')==parent['initial_world_sha256']
 for f in read(r/'preserved/reinforcement-camps-r1.json')['files']:
  if '/reinforcement-camps-r1/go-src/'not in f['path']:continue
  rel=f['path'].split('/reinforcement-camps-r1/',1)[1];assert sha(q/rel)==f['sha256'],rel
 for n in m.NEW:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n),n
 gui=read(q/'gui-r1/receipt.json');assert gui['status']=='passed-purchased-reinforcement-v5-battle'and not gui['memory_injected']and not gui['pregranted_openkb_units'];assert gui['initial']['world']==original['world']
 opened,acted,cold,returned,saved=[gui[k]for k in ['opened','acted','cold_battle','returned','saved']];assert opened['world']['army']==original['world']['army'];assert opened['battle_native_calls']==0
 enemy=[];raw=bytes.fromhex(opened['runtime_enemy_hex']);assert len(raw)==24
 for i in range(6):
  kind,n=struct.unpack_from('<HH',raw,i*4);assert kind<=25;enemy.append(dict(unit=f'native:{kind:02d}'if kind else'',count=n))
 assert enemy==opened['runtime_enemy_rows']==opened['world']['battle']['state']['rows'][1]
 profiles=read(q/'inputs/combat-catalog.json')['profiles'];before=opened['world']['battle']['state'];target=gui['target'];source=before['rows'][0][1];victim=before['rows'][1][target];assert source==dict(unit='openkb:wolf',count=1);config=before['config']
 damage=source['count']*profiles[source['unit']]['attack']//config['divisors'][0]*config['multipliers'][0]
 if config['rules']in ['formation','tactics']and profiles[victim['unit']]['native_kind']==1 and target<3 and any(v['count']for i,v in enumerate(before['rows'][1][:3])if i!=target):damage=damage*80//100
 loss=damage//profiles[victim['unit']]['hp'];loss=0 if loss==0 else victim['count']if loss>=victim['count']-1 else loss
 expected=copy.deepcopy(opened['world']);state=expected['battle']['state'];state['rows'][1][target]['count']-=loss;state['acted'][0][1]=True;state['result']='win'if not any(v['count']for v in state['rows'][1])else'';assert expected==acted['world']==cold['world'];assert cold['pair_token']==acted['pair_token']
 rng=returned['retreat_rng'];next_seed=(rng['Before']*214013+2531011)&0xffffffff;assert next_seed==rng['After']and((next_seed>>16)&32767)==rng['Value'];fee=acted['world']['army']['gold']//(rng['Value']//2730+3)
 expected=copy.deepcopy(acted['world']);del expected['encounters'][expected['battle']['encounter']];expected['battle']=None;expected['revision']+=1;expected['army']['gold']-=fee
 assert expected==returned['world']==gui['cold_return']['world'];assert gui['cold_return']['pair_token']==returned['pair_token'];assert returned['world']['army']['gold']==460-fee
 expected=copy.deepcopy(returned['world']);expected['revision']+=1;assert expected==saved['world']==gui['final']['world']==gui['army']['world']
 offers=original['world']['army']['offers']
 for n in ['initial','prompt','opened','acted','cold_battle','returned','cold_return','saved','final','army']:
  s=gui[n];assert s['world']['army']['offers']==offers;assert s['native_rows_hex']==gui['initial']['native_rows_hex'];assert s.get('battle_native_calls',0)==0
 for phase,name,w,ref in [('warm','pair-after-action.json',acted['world'],'battle'),('cold-battle','pair-after-return.json',returned['world'],'return')]:
  v=read(q/'gui-r1'/phase/name);assert v['schema']=='eightsword-owned-world-save/5'and v['world']==w and v['native_resume']['phase']==ref
 final=read(q/'session/gamedata.ay.army.json');assert final['schema']=='eightsword-owned-world-save/5'and final['world']==saved['world']and final.get('native_resume')is None;assert final['original_sha256']==sha(q/'session/gamedata.ay')
 assert(q/'session/gamedata.ay').read_bytes()[12:1236]==(q/'initial-session/gamedata.ay').read_bytes()[12:1236]
 frames=[]
 for v in gui['screens']:
  folder=q/'gui-r1'/v['phase'];meta=read(folder/v['metadata']);im=Image.open(folder/v['canvas']).convert('RGBA');x11=Image.open(folder/v['screen']).convert('RGBA');assert im.size==x11.size==(1920,1200);assert hashlib.sha256(x11.tobytes()).hexdigest()==meta['canvas_sha256']==meta['presented_sha256'];assert im.tobytes()==x11.tobytes(),v;frames.append(dict(name=v['name'],sha256=sha(folder/v['canvas'])))
 if a.images:
  images=[]
  for name in ['purchased-wolf-battle','cold-wolf-action','cold-recruited-army']:
   v=next(v for v in gui['screens']if v['name']==name);source=q/'gui-r1'/v['phase']/v['canvas'];dest=a.images/('reinforcement-battle-'+name+'-r1.png');assert not dest.exists();im=Image.open(source);im.thumbnail((960,600),Image.Resampling.LANCZOS);im.save(dest);images.append(dict(source=str(source.relative_to(r)),source_sha256=sha(source),published=dest.name,published_sha256=sha(dest)))
  with(a.images/'reinforcement-battle-runtime-r1.json').open('x')as f:json.dump(dict(images=images,pregranted_openkb_units=False,memory_injected=False,fixed_initial_native_army=True,natural_encounter=True,original_parity=False),f,ensure_ascii=False,indent=2);f.write('\n')
 result=dict(status='passed-independent-purchased-reinforcement-battle',parent=parent,dependencies=deps,source_tools={n:sha(r/'tools'/n)for n in m.NEW},runtime_unchanged=True,damage=damage,loss=loss,retreat_rng=rng,retreat_fee=fee,frames=frames,offers_preserved=True,v5_battle_return_f7=True,formal_promoted=False,limits=['One purchased wolf from the approved camp fixture; no natural new game or high-rank campaign claim.','Natural RNG was not fixed and this is not an original/remake RNG parity comparison.'])
 with a.out.open('x')as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
if __name__=='__main__':main()
