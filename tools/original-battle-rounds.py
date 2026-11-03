#!/usr/bin/env python3
"""Spec030 continuous ordinary rounds and Go current data; preparation and preservation."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,sys
from pathlib import Path
sys.dont_write_bytecode=True
REL='workplace/probe-20261023/graphics-first/battle-r1/original-battle-rounds-r1';BATCH='original-battle-rounds-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')

def audit_sites(q,r,ida):
 import re
 admitted={'sub_20724','sub_20AB4','sub_1FF1C','sub_20DAE','sub_21EA0','sub_21274','sub_2135A'};comps=[];writes=[];motions=[]
 for f in ida['functions']:
  for l in f['lines']:
   s=l['instruction'];at=l['ida_linear']
   if f['name']in admitted:
    m=re.fullmatch(r'cmp\s+word ptr \[(si|di|bx)\+(56E8|56EA|5700|5702)h\], ([0-9A-F]+h|[0-9]+)',s);rev=re.fullmatch(r'cmp\s+ax, \[(si|di|bx)\+(56E8|56EA|5700|5702)h\]',s)
    if m or rev:
     z=m or rev;offset=int(z[2],16);imm=int(m[3][:-1],16)if m and m[3].endswith('h')else int(m[3])if m else 0
     if imm!=24:comps.append(dict(ida=at,start=f['start'],end=f['end'],side=int(offset>=0x5700),reg=z[1],kind=offset in[0x56e8,0x5700],reverse=bool(rev),immediate=imm,length=len(bytes.fromhex(l['bytes']))))
   if f['name']in['sub_20724','sub_20AB4']and l['bytes']in['8907','8904']:writes.append(dict(ida=at,side=int(f['name']=='sub_20AB4'),reg='bx'if l['bytes']=='8907'else'si'))
   if f['name']in['sub_21EA0','sub_22DBC']:
    m=re.fullmatch(r'mov\s+word_([0-9A-F]+), ax',s)
    if m:
     offset=int(m[1],16)-0x2d780;side=int(f['name']=='sub_22DBC');base=0x6fb6+side*12
     if base<=offset<base+6 and(offset-base)%2==0:motions.append(dict(ida=at,side=side,slot=(offset-base)//2))
 assert(len(comps),len(writes),len(motions))==(69,16,20)
 assert comps==read(q/'site-receipt.json')and motions==read(q/'motion-sites.json')
 s=(r/'internal/ownedworld/original_battle_rounds_sites.go').read_text();c,z=s.split('var originalRoundWrites = ',1);w,m=z.split('var originalRoundMotions = ',1)
 actual=re.findall(r'\{0x([0-9a-f]+), 0x([0-9a-f]+), 0x([0-9a-f]+), ([01]), dg\.(SI|DI|BX), (true|false), (true|false), (\d+), (\d+)\}',c)
 assert actual==[(f"{v['ida']-0x1e570:x}",f"{v['start']:x}",f"{v['end']:x}",str(v['side']),v['reg'].upper(),str(v['kind']).lower(),str(v['reverse']).lower(),str(v['immediate']),str(v['length']))for v in comps]
 assert re.findall(r'\{0x([0-9a-f]+), ([01]), dg\.(SI|BX)\}',w)==[(f"{v['ida']-0x1e570:x}",str(v['side']),v['reg'].upper())for v in writes]
 assert re.findall(r'\{0x([0-9a-f]+), ([01]), ([012])\}',m)==[(f"{v['ida']-0x1e570:x}",str(v['side']),str(v['slot']))for v in motions]

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','audit','publish','archive','verify'])
 for n in ['project','archive','out']:p.add_argument('--'+n,type=Path)
 a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   o=d['objects'][f['sha256']];z=(a.archive/BATCH/o['file']).read_bytes();assert hashlib.sha256(z).hexdigest()==o['stored_sha256'];raw=gzip.decompress(z);assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-original-battle-rounds',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL;s=importlib.util.spec_from_file_location('helper',r/'tools/prepare-owned-army-ui.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h);deps=h.dependencies(r)
 if a.action=='prepare':
  parent=q.parent/'original-battle-casualties-r1';assert q.is_dir()and not(q/'inputs').exists();shutil.copytree(parent/'inputs',q/'inputs');shutil.copytree(parent/'ui-assets',q/'ui-assets')
  for n in ['probe.mod','probe.sum']:shutil.copyfile(parent/n,q/n)
  write(q/'baseline.json',deps)
 if a.action in ['prepare','freeze']:
  assert deps==read(q/'baseline.json');names=set(read(r/'preserved/owned-player-source-manifest-r1.json'))|{str(p.relative_to(r))for p in(r/'internal/ownedworld').glob('*.go')}
  for n in sorted(names):dst=q/'source'/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,dst)
  (q/'source-manifest.json').write_text(json.dumps({n:sha(q/'source'/n)for n in sorted(names)},ensure_ascii=False,indent=2)+'\n')
  for n in ['original-battle-rounds.py','export-original-battle-rounds-ida.py']:shutil.copyfile(r/'tools'/n,q/n)
  return
 if a.action=='audit':
  from PIL import Image
  assert deps==read(q/'baseline.json')
  for n,d in read(q/'source-manifest.json').items():assert sha(r/n)==sha(q/'source'/n)==d
  ida=read(q/'ida/ida-rounds.json');assert ida['function_count']==521 and len(ida['functions'])==20 and ida['exporter_sha256']==sha(r/'tools/export-original-battle-rounds-ida.py')
  pam=(q/'inputs/PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()==ida['source_sha256'];im=bytearray(pam);word=lambda at:int.from_bytes(pam[at:at+2],'little');header=word(8)*16
  for i in range(word(6)):
   at=word(24)+i*4;off=header+word(at+2)*16+word(at);im[off:off+2]=((word(off)+0x1000)&65535).to_bytes(2,'little')
  for f in ida['functions']:
   for l in f['lines']:
    raw=bytes.fromhex(l['bytes']);assert im[l['file_offset']:l['file_offset']+len(raw)]==raw
  audit_sites(q,r,ida)
  catalog=read(q/'inputs/combat-catalog.json')['profiles']
  def record(v):
   t=v['target'];hp=catalog[t['Target']['unit']]['hp'];damage=catalog[t['Source']['unit']]['attack']*t['Source']['count']//5;encoded=damage//hp+1;before=v['Before'];player=v.get('player',False)
   after=max(0,before-encoded)if player else before if encoded==1 else 0 if encoded>=before else before-encoded+1
   assert(v['After'],v['Loss'],v['updates'])==(after,before-after,1)
   assert len(v['calls'])in([1]if player else[1,2])
   for c in v['calls']:
    assert c['damage']==damage and c['encoded']==encoded and c['AfterHP']==max(0,c['BeforeHP']-damage)
    native=catalog[t['Target']['unit']].get('native_kind',0)!=0
    assert c['AfterWord']==((c['BeforeWord']-damage)&65535 if native else c['BeforeWord'])
   display=[]
   if player or encoded>1:
    start=min(before,5)if after==0 else before if encoded<5 else before-encoded+5;display=list(range(start,after-1,-1))
   assert(v['Display']or[])==(v['PlannedDisplay']or[])==display
  cold=read(q/'cold-receipt.json');assert cold['normal_cold_start']and cold['seed']==0x12345678
  for hd in[False,True]:
   rows=[v for v in cold['rows']if v['hd']==hd];assert len(rows)==2
   for key in['units_hex','hp_hex','frame_rgba_sha256','seed_after','AX']:assert rows[0][key]==rows[1][key]
   assert len(rows[1]['history'])==9
   for v in rows[1]['history']:record(v)
   frames=[Image.open(q/'cold-r1'/f'hd-{str(hd).lower()}-mode-{i}/frame.png').convert('RGBA')for i in[0,1]]
   assert frames[0].tobytes()==frames[1].tobytes()and hashlib.sha256(frames[0].tobytes()).hexdigest()==rows[0]['frame_rgba_sha256']
  expanded=read(q/'expanded-receipt.json');assert not expanded['playable']and len(expanded['rows'])==3
  for i,row in enumerate(expanded['rows']):
   assert row['case']==i and row['result']==['win','loss','retreat'][i]and len(row['history']or[])==[32,8,0][i]
   assert row['held_retries']==5 and not row['controlled_enemy_first_argument']and row['world_wrapper_returned']and row['army_store_cold_read']
   assert row['controlled_store_rules']=='formation'and row['controlled_store_leadership']==30000 and not row['world_rewards_committed']
   current={s['unit']:s['count']for s in row['initial']if s['unit']}
   for v in row['history']or[]:
    record(v)
    if v.get('player',False):assert current[v['target']['Source']['unit']]==v['target']['Source']['count']
    else:
     unit=v['target']['Target']['unit'];assert current[unit]==v['Before'];current[unit]=v['After']
   assert{s['unit']:s['count']for s in row['remaining']if s['unit']}=={u:n for u,n in current.items()if n}
   raw=bytes.fromhex(row['native_rows_hex'])
   for n,stack in enumerate(row['rows'][0]):
    if stack['unit'].startswith('openkb:'):assert raw[n*4:n*4+4]==bytes(4)
   frame=Image.open(q/'expanded-r1'/str(i)/'frame.png').convert('RGBA');assert hashlib.sha256(frame.tobytes()).hexdigest()==row['frame_rgba_sha256']
  assert[v['count']for v in expanded['rows'][0]['remaining'][:2]]==[603,10]
  for name in['tests-r1.log','regression-r1.log']:assert(q/name).read_text().rstrip().endswith('PASS')
  controls=read(q/'round-controls.json');assert controls['native_pairs']==138 and controls['refusals']==8
  write(a.out,dict(status='passed-original-battle-rounds-audit',source_files=len(read(q/'source-manifest.json')),ida_functions=20,comparison_sites=69,sort_write_sites=16,motion_write_sites=20,native_comparison_pairs=138,comparison_refusals=8,cold_native_HD_pairs=2,expanded_results=['win','loss','retreat'],expanded_actions=[32,8,0],army_store_cold_read_cases=3,world_wrapper_returned_cases=3,army_only_store_fixture_rules='formation',army_only_store_fixture_leadership=30000,original_seed=0x12345678,original_player_damage_differs_from_enemy=True,new_ids_in_original_tables=0,ordinary_player_entry_disabled=True,not_verified=['special/caster actions and spells','world rewards, defeat reset and F7 checkpoint','formation/tactics and target AI in expanded rounds','new unit hit/death poses','actual GUI window','word-wide encounter bounds','general player entry']));return
 if a.action=='publish':
  import io
  from PIL import Image,ImageDraw,ImageFont
  assert read(r/'preserved/original-battle-rounds-audit-r1.json')['status']=='passed-original-battle-rounds-audit';idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),28,index=3)
  out=Image.new('RGB',(1920,530),'#11251f');draw=ImageDraw.Draw(out);receipt=read(q/'expanded-receipt.json');sources=[]
  for i,title in enumerate(['勝利：野狼剩603、弓箭手10','全滅：Go剩兵為0','撤退：原兵數保持']):
   source=q/'expanded-r1'/str(i)/'frame.png';out.paste(Image.open(source).resize((640,400),Image.Resampling.NEAREST),(i*640,52));draw.text((i*640+12,8),title,font=font,fill='#fff1b5');sources.append(dict(path=str(source.relative_to(r)),sha256=sha(source),result=receipt['rows'][i]['result']))
  draw.text((20,470),'原版HD戰場；明示測試編成。Go普通回合與剩兵保存，世界獎勵及完整玩家入口仍待接。',font=font.font_variant(size=25),fill='#fff1b5');dest=a.out/'original-battle-go-rounds-r1.png';assert not dest.exists();out.save(dest);write(a.out/'original-battle-go-rounds-r1.json',dict(schema=1,output_sha256=sha(dest),inputs=sources,actual_window_verified=False,playable=False,controlled_typed_override=True,scope='Ordinary rounds to win/loss/retreat; world wrapper army capture; paired Store army-only cold read with explicit owned-rules/leadership fixture.'));return
 if a.action=='archive':
  assert read(r/'preserved/original-battle-rounds-audit-r1.json')['status']=='passed-original-battle-rounds-audit';folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
  for f in sorted(q.rglob('*')):
   if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
   assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();digest=hashlib.sha256(raw).hexdigest();obj=folder/(digest+'.gz')
   if digest not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[digest]=dict(file=obj.name,stored_sha256=sha(obj))
   files.append(dict(path=str(f.relative_to(r)),bytes=len(raw),sha256=digest,mode=f.stat().st_mode&0o777))
  write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Full original data, complete frames, states and binaries local only. Continuous ordinary battle candidate; general player entry blocked.'))
if __name__=='__main__':main()
