#!/usr/bin/env python3
"""Fixed-seed Go RNG/refusal candidate; original mode and production stay intact."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,struct,subprocess
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/refusal-rng-r1'
BATCH='refusal-rng-r1'
NEW=['prepare-refusal-rng.py','research-refusal-rng.go','refusal-rng-ui.go','probe-refusal-rng.go','export-refusal-rng-ida.py']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def module(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def common(r):return module(r/'tools/prepare-runtime-enemy.py','old').common(r)+['research-runtime-enemy.go','prepare-runtime-enemy.py']
def patch(r,src,q):
 old=module(r/'tools/prepare-runtime-enemy.py','oldpatch');old.patch(src,q);(q/'adapter-patches.json').rename(q/'enemy-adapter-base.json')
 replacements={
 'research-army-presence.go':[('[]uint16{0x177a, 0x1782}','[]uint16{}')],
 'research-runtime-enemy.go':[('type runtimeEnemyBattle struct {','type runtimeEnemyBattle struct {\n Modifier uint16'),('m.Read16(0x1e880+0x8d6a) != 0','m.Read16(0x1e880+0x8d6a) != x.Modifier'),('m.Read16(ds+0x8d6a) != 0','m.Read16(ds+0x8d6a) != x.Modifier')],
 'research-encounter-ui.go':[
  ('n := uint32(2730)\n\t\te = x.Bridge.settle(DefeatInput{Reason: "retreat", Random: &n})','e = settleRuntimeRetreat(x.Bridge, x.Engine.Oracle)'),
  ('runtimeEnemyState(v)','runtimeEnemyState(v)\n refusalState(v)'),
  ('g.Engine.ReleaseAll()\n\t\treturn nil','g.Engine.ReleaseAll()\n if e:=pursuitOpening(x);e!=nil{return e}\n\t\treturn nil'),
  ('return x, nil','installRefusalUI(x)\n return x, nil'),
 ],
 }
 for n,pairs in replacements.items():
  p=src/'tools'/n;t=p.read_text()
  for a,b in pairs:assert a in t,(n,a);t=t.replace(a,b)
  p.write_text(t)
 changes=[]
 for n in common(r):
  p=r/'tools'/n;t=src/'tools'/n
  if sha(p)!=sha(t):changes.append(dict(file=n,before=sha(p),after=sha(t),scope='bounded candidate adapter; root file unchanged'))
 write(q/'adapter-patches.json',changes)
 # Existing XTEST scaffolding, with exactly two predetermined refusal seeds.
 t=(src/'tools/check-encounter-ui.py').read_text().replace("['win','retreat']","['free','pursuit']").replace("'-controlled-case',name","'-controlled-case','retreat','-seed-set','-refusal-seed',str(seed_map[name])")
 t=t.replace("for name in ['free','pursuit']:","seed_map={\x27free\x27:next(x[\x27seed\x27]for x in read(q/\x27inputs/seeds.json\x27)[\x27boundaries\x27]if x[\x27value\x27]==0),\x27pursuit\x27:next(x[\x27seed\x27]for x in read(q/\x27inputs/seeds.json\x27)[\x27boundaries\x27]if x[\x27value\x27]==8192)}\n  for name in ['free','pursuit']:")
 start=t.index("   key('Return');s=wait(lambda s:s.get('battle_opened')")
 end=t.index('   final=wait',start)
 t=t[:start]+'''   key('Right');key('Return')
   if name=='free':
    wait(lambda s:s.get('refusal_returned')and not s.get('refusal_pursued'));paused=dict(not_applicable=True)
   else:
    s=wait(lambda s:s.get('battle_opened')and s.get('refusal_pursued')and s['world']['battle']is not None and s['canvas_sha256']==s['presented_sha256']);steps=s['battle_guest_steps'];cycles=s['battle_guest_cycles'];held=s['battle_held_updates'];wait(lambda s:s['battle_held_updates']>=held+3);s=state();paused=dict(steps_equal=s['battle_guest_steps']==steps,cycles_equal=s['battle_guest_cycles']==cycles,updates=s['battle_held_updates']-held);snap('battle-start',screens)
    n=len(state()['battle_events']);call('click',280,225);wait(lambda s:len(s['battle_events'])>n or s.get('battle_finished'))
''' +t[end:]
 t=t.replace('passed-controlled-confirmation-go-ui','passed-refusal-live-rng-ui')
 (q/'gui-check.py').write_text(t)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','audit','archive','verify']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   o=d['objects'][f['sha256']];p=a.archive/BATCH/o['file'];assert sha(p)==o['stored_sha256'];b=gzip.decompress(p.read_bytes());assert len(b)==f['bytes']and hashlib.sha256(b).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-refusal-rng',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL;m=module(r/'tools/prepare-owned-army-ui.py','prior');deps=m.dependencies(r)
 if a.action=='prepare':
  assert(q/'ida/identity.json').is_file()and(q/'ida/ida-refusal-rng-r1.json').is_file()and not(q/'go-src').exists();(q/'inputs').mkdir();(q/'ui-assets').mkdir();src=q/'go-src'
  for n in deps['source_inputs']:
   t=src/n;t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,t)
  (src/'tools').mkdir(exist_ok=True)
  for n in common(r):shutil.copyfile(r/'tools'/n,src/'tools'/n)
  t=(r/'tools/research-owned-army.go').read_text().removeprefix('//go:build ignore\n');t=t[:t.index('func main()')].replace('\n\t"flag"\n','\n');(src/'tools/owned-army-model.go').write_text(t)
  for ext in ['mod','sum']:shutil.copyfile(src/('go.'+ext),q/('probe.'+ext))
  with(q/'probe.mod').open('a')as f:f.write('\nrequire github.com/wicanr2/dosgolem v0.0.0\nreplace github.com/wicanr2/dosgolem => /core\n')
  for n in ['army-catalog.json','combat-catalog.json','original-save.ay','battle-before.state','PAM.AY']:(q/'inputs'/n).write_bytes(m.stored(r,'controlled-owned-battle-r1','/inputs/'+n))
  w=json.loads(m.stored(r,'runtime-enemy-r1','/inputs/world-runtime.json'));w['army']['slots'][0]['count']=2500;w['army']['leadership']=30000
  for n in ['world-runtime.json','world-free.json','world-pursuit.json']:write(q/'inputs'/n,w)
  (q/'inputs/map01.ay').write_bytes(m.stored(r,'owned-world-army-r1','/port-r2/scratch/map01.ay'))
  inv=pow(214013,-1,2**32);boundaries=[dict(value=v,seed=(((v<<16)-2531011)*inv)%(2**32))for v in [0,8191,8192,16383,16384,32767]]
  write(q/'inputs/seeds.json',dict(boundaries=boundaries,seeds=[0,1,0xffffffff,0x12345678]+[v['seed']for v in boundaries],method='algebraic modular inverse; fixed before original execution, no rerolls'))
  d=read(r/'preserved/owned-encounter-ui-r1.json')
  for f in d['files']:
   if '/ui-assets/'not in f['path']:continue
   target=q/'ui-assets'/f['path'].split('/ui-assets/',1)[1];target.parent.mkdir(parents=True,exist_ok=True);o=d['objects'][f['sha256']];target.write_bytes(gzip.decompress((r/'preserved/owned-encounter-ui-r1'/o['file']).read_bytes()));assert sha(target)==f['sha256']
  patch(r,src,q);write(q/'baseline.json',deps);return
 assert deps==read(q/'baseline.json')
 if a.action=='freeze':
  for n in NEW:shutil.copyfile(r/'tools'/n,q/'go-src/tools'/n)
  return
 if a.action=='audit':
  raw=(q/'inputs/PAM.AY').read_bytes();ida=read(q/'ida/ida-refusal-rng-r1.json');assert sha(q/'inputs/PAM.AY')==ida['source_sha256'];header=struct.unpack_from('<H',raw,8)[0]*16;relocs=[];lines=0
  assert ida['index_sha256']==sha(r/'docs/spec/world-army-consumers-r1.json')and ida['exporter_sha256']==sha(r/'tools/export-refusal-rng-ida.py')
  for f in ida['functions']:
   note=f['indexed_semantic'];assert note['source']=='docs/spec/world-army-consumers-r1.json'and(note['level']=='proven'or note['warning'])
  for i in range(struct.unpack_from('<H',raw,6)[0]):off,seg=struct.unpack_from('<HH',raw,struct.unpack_from('<H',raw,24)[0]+i*4);relocs.append(header+seg*16+off)
  for f in ida['functions']:
   for line in f['lines']:
    pos=line['file_offset'];want=bytes.fromhex(line['bytes']);b=bytearray(raw[pos:pos+len(want)]);assert pos==line['ida_linear']-0x10000+header
    for loc in relocs:
     if pos<=loc and loc+2<=pos+len(want):struct.pack_into('<H',b,loc-pos,(struct.unpack_from('<H',b,loc-pos)[0]+0x1000)&65535)
    assert bytes(b)==want;lines+=1
  receipt=read(q/'probe/receipt.json');assert receipt['status']=='passed-original-rng-and-refusal-handoffs'and len(receipt['rng'])==160 and len(receipt['decisions'])==12 and len(receipt['handoffs'])==2
  assert len(receipt['rejections'])==4 and all(v['memory_unchanged']and v['disk_unchanged']for v in receipt['rejections'])
  for v in receipt['rng']:n=(v['seed']*214013+2531011)&0xffffffff;assert n==v['next']and(n>>16)&32767==v['value']
  for v in receipt['decisions']:assert v['next_seed']==(v['seed']*214013+2531011)&0xffffffff and v['gate']==(0x1752 if v['value']//8192==1 else 0x1782)
  gui=read(q/'gui-r1/receipt.json');assert gui['status']=='passed-refusal-live-rng-ui'and len(gui['cases'])==2
  decoded={};ram_cache={}
  for folder in sorted({p.parent for base in [q/'probe',q/'gui-r1']for p in base.rglob('*.state')}):
   target=folder/'decoded'
   if not target.exists():subprocess.run([str(q/'state-reader'),'-all','-calls',str(folder),'-out',str(target)],check=True)
   decoded[str(folder.relative_to(q))]=read(target/'index.json')
  def memory(folder,name):
   key=(folder,name)
   if key not in ram_cache:ram_cache[key]=gzip.decompress((q/folder/'decoded'/decoded[folder][name]['memory_file']).read_bytes())
   return ram_cache[key]
  def seed(b):return struct.unpack_from('<I',b,0x26a3c)[0]
  def check_injection(folder,ip,go):
   old=decoded[folder]['before-commit.state'];new=decoded[folder]['after-commit.state'];before=memory(folder,'before-commit.state');after=memory(folder,'after-commit.state');ds=0x1e880;bp=old['registers'][5];allowed=set(range(ds+0x4f2,ds+0x4fe))
   if ip==0x173a:allowed|=set(range(0x26a3c,0x26a40))
   if go:allowed|=set(range(ds+0x54a,ds+0x562))|set(range(ds+0x56e8,ds+0x5700))
   assert all(x==y or i in allowed for i,(x,y)in enumerate(zip(before,after)))and old['ip']==0x3733 and new['ip']==ip
   assert new['registers'][4]==bp+6 and new['registers'][5]==struct.unpack_from('<H',before,ds+bp)[0]and new['registers'][6]==struct.unpack_from('<H',before,ds+bp-0x12)[0]and new['registers'][7]==struct.unpack_from('<H',before,ds+bp-0x10)[0]
  for fixture in read(q/'inputs/seeds.json')['boundaries']:
   for mode in ['original','go']:
    folder='probe/gate-%d-%s'%(fixture['value'],mode);check_injection(folder,0x173a,mode=='go');gate=memory(folder,'gate.state');assert seed(gate)==(fixture['seed']*214013+2531011)&0xffffffff and decoded[folder]['gate.state']['ip']==(0x1752 if fixture['value']//8192==1 else 0x1782)
  for initial in read(q/'inputs/seeds.json')['seeds']:
   expected=initial
   for _ in range(16):expected=(expected*214013+2531011)&0xffffffff
   assert seed(memory('probe','rng-%d.state'%initial))==expected
  for folder,index in decoded.items():
   if 'before-reject.state'in index:
    assert memory(folder,'before-reject.state')==memory(folder,'after-reject.state')
    for k in ['registers','segments','ip','flags','steps']:assert index['before-reject.state'][k]==index['after-reject.state'][k]
  profiles=read(q/'inputs/combat-catalog.json')['profiles']
  def replay_opening(initial,enemy,events):
   count=initial['army']['slots'][0]['count'];hp=profiles['openkb:wolf']['hp']
   for event in events:
    action=event['action'];source=enemy[action['source']];damage=source['count']*profiles[source['unit']]['attack']//5;quotient=damage//hp;loss=0 if quotient==0 else count if quotient>=count-1 else quotient
    assert action['side']==1 and action['target']==0 and event['damage']==damage and event['loss']==loss and event['before']==count and event['after']==count-loss;count-=loss
   return count
  for v in receipt['handoffs']:
   folder='probe/'+v['name'];check_injection(folder,0x173a,True);final_mem=memory(folder,'final-map.state');assert decoded[folder]['final-map.state']['ip']==0xbd3 and final_mem[0x1edca:0x1ede2]==final_mem[0x23f68:0x23f80]==bytes([255])*24 and v['native_calls']==0
   expected=json.loads(json.dumps(v['world_before']))
   if v['pursued']:
    p=v['retreat'];assert seed(memory(folder,'held.state'))==p['Before']and seed(memory(folder,'settled.state'))==p['After']==(p['Before']*214013+2531011)&0xffffffff and p['Value']==(p['After']>>16)&32767
    next_seed=p['After']
    for draw in v['return_rng']:assert draw['seed_before']==next_seed;next_seed=(next_seed*214013+2531011)&0xffffffff
    assert seed(final_mem)==next_seed and [(d['return_cs'],d['return_ip'])for d in v['return_rng']]==[(0x110,0x71b3)]
    expected['army']['slots'][0]['count']=replay_opening(expected,v['enemy'],v['opening']);expected['army']['gold']-=expected['army']['gold']//(p['Value']//2730+3);expected['revision']+=2;assert v['modifier']==1
   assert expected==v['world_after']
  for n in NEW+common(r):
   patch_info=next((v for v in read(q/'adapter-patches.json')if v['file']==n),None)
   if patch_info:assert sha(r/'tools'/n)==patch_info['before']and sha(q/'go-src/tools'/n)==patch_info['after']
   else:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n)
  from PIL import Image
  screens=0
  for case in gui['cases']:
   final=case['final'];assert final['world']==case['cold']['snapshot']['world']and final['battle_native_calls']==0
   folder='gui-r1/'+case['case'];check_injection(folder,0x16e0,True);before=memory(folder,'before-seed.state');after=memory(folder,'after-seed.state');assert all(x==y or 0x26a3c<=i<0x26a40 for i,(x,y)in enumerate(zip(before,after)))
   plan=final['refusal_rng'];decision=memory(folder,'decision.state');assert seed(after)==plan['Before']and seed(decision)==plan['After']==(plan['Before']*214013+2531011)&0xffffffff and plan['Value']==(plan['After']>>16)&32767 and final['refusal_pursued']==(plan['Value']//8192==1)
   if case['case']=='free':assert final['refusal_returned']and not final['refusal_pursued']and final['world']==read(q/'inputs/world-runtime.json')
   else:
    p=final['retreat_rng'];assert p['After']==(p['Before']*214013+2531011)&0xffffffff and p['Value']==(p['After']>>16)&32767
    assert final['refusal_pursued']and final['pursuit_modifier']==1 and final['world']['army']['gold']==5000-5000//(p['Value']//2730+3)and len(final['combat_events'])>0 and all(e['action']['side']==1 for e in final['combat_events'])
    expected=read(q/'inputs/world-runtime.json');enemy=read(q/'gui-r1'/case['case']/'battle-start.json')['world']['battle']['state']['initial'][1];expected['army']['slots'][0]['count']=replay_opening(expected,enemy,final['combat_events']);expected['army']['gold']-=expected['army']['gold']//(p['Value']//2730+3);expected['revision']+=2;assert expected==final['world']and seed(memory(folder,'final-map.state'))==(p['After']*214013+2531011)&0xffffffff and case['paused']['steps_equal']and case['paused']['cycles_equal']
   native=(q/('session-'+case['case'])/'gamedata.ay').read_bytes();assert native[12:]==(q/'inputs/original-save.ay').read_bytes()[12:];w=final['world'];words=[w['progress']['rank'],w['progress']['merit'],w['progress']['legacy_04f6'],w['army']['gold'],w['army']['leadership'],w['progress']['legacy_04fc']];assert words==[(struct.unpack_from('<H',native,i*2)[0]-i*2-3)&65535 for i in range(6)]
   for v in case['screens']:
    folder=q/'gui-r1'/case['case'];im=Image.open(folder/v['canvas']);screen=Image.open(folder/v['screen']);meta=read(folder/v['metadata']);assert im.size==screen.size==(1920,1200)and im.convert('RGB').tobytes()==screen.convert('RGB').tobytes()and hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()==meta['canvas_sha256']==meta['presented_sha256'];screens+=1
    for t in meta['text_fields']or[]:
     box,ink=t['Rect'],t['Ink']
     if ink[2]>ink[0]:assert box[0]<=ink[0]<ink[2]<=box[2]and box[1]<=ink[1]<ink[3]<=box[3]
  write(a.out,dict(status='passed-live-go-rng-refusal',dependencies=deps,source_tools={n:sha(r/'tools'/n)for n in NEW+common(r)},original=receipt,gui=gui,ida_lines=lines,screens=screens,decoded_states=sum(len(v)for v in decoded.values()),production_changed=False,controlled_memory=True,normal_player_path=False));return
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for f in sorted(q.rglob('*')):
  if not f.is_file()or 'build-cache'in f.relative_to(q).parts:continue
  assert f.stat().st_uid==1000 and not f.is_symlink();b=f.read_bytes();h=hashlib.sha256(b).hexdigest();obj=folder/(h+'.gz')
  if h not in objects:obj.write_bytes(gzip.compress(b,compresslevel=6,mtime=0));objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(b),mode=f.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Local original evidence; full objects excluded from Git.'))
if __name__=='__main__':main()
