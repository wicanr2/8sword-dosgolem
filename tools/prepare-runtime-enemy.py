#!/usr/bin/env python3
"""Original-generated random enemies -> Go army/combat/UI, isolated research."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,struct,subprocess
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/runtime-enemy-r1'
BATCH='runtime-enemy-r1'
NEW=['prepare-runtime-enemy.py','research-runtime-enemy.go','probe-runtime-enemy.go']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def module(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def common(r):return module(r/'tools/prepare-encounter-ui.py','old').COMMON+['research-encounter-ui.go','check-encounter-ui.py','read-world-army-states.go','prepare-encounter-ui.py','prepare-owned-army-ui.py']
def patch(src,q):
 changes=[]
 replacements={
 'world-army-review_main.go':[('return g.Engine.AdvanceCycles(100000)','return advanceEncounterUI(g)'),('g.Engine.Key(','encounterGuestKey(g, ')],
 'research-army-presence.go':[('[]uint16{0x1713, 0x177a, 0x1782}','[]uint16{0x177a, 0x1782}')],
 'research-encounter-ui.go':[
  ('x.Bridge = installControlledBattle(e.Oracle, p.Store, p.Current, code)','runtimeEnemyCurrent = installRuntimeEnemyBattle(e.Oracle, p.Store, p.Current, code)\n\t\tx.Bridge = runtimeEnemyCurrent.controlledBattle'),
  ('{ds + 0x56e8, 48}','{ds + 0x56e8, 24}'),
  ('v["controlled_memory"], v["normal_player_path"] = true, false','runtimeEnemyState(v)\n\tv["controlled_memory"], v["normal_player_path"] = true, false'),
 ],
 }
 for n,pairs in replacements.items():
  p=src/'tools'/n;old=p.read_text();t=old
  for a,b in pairs:assert a in t;t=t.replace(a,b)
  p.write_text(t);changes.append(dict(file=n,before=hashlib.sha256(old.encode()).hexdigest(),after=sha(p),replacements=pairs))
 write(q/'adapter-patches.json',changes)
 t=(src/'tools/check-encounter-ui.py').read_text().replace("['win','retreat']","['runtime']").replace("'-controlled-case',name","'-controlled-case','retreat'")
 start=t.index("   if name=='win':");end=t.index('   final=wait',start)
 t=t[:start]+"   n=len(state()['battle_events']);click_wait(200,900,n);snap('after-player-action',screens);n=len(state()['battle_events']);click_wait(280,225,n)\n"+t[end:]
 t=t.replace('passed-controlled-confirmation-go-ui','passed-runtime-enemy-ui')
 (q/'gui-check.py').write_text(t)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','audit','archive','verify']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   o=d['objects'][f['sha256']];p=a.archive/BATCH/o['file'];assert sha(p)==o['stored_sha256'];b=gzip.decompress(p.read_bytes());assert len(b)==f['bytes']and hashlib.sha256(b).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-runtime-enemy',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL;m=module(r/'tools/prepare-owned-army-ui.py','prior');deps=m.dependencies(r)
 if a.action=='prepare':
  assert not q.exists();q.mkdir();(q/'inputs').mkdir();(q/'ui-assets').mkdir();src=q/'go-src'
  for n in deps['source_inputs']:
   t=src/n;t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,t)
  (src/'tools').mkdir(exist_ok=True)
  for n in common(r):shutil.copyfile(r/'tools'/n,src/'tools'/n)
  t=(r/'tools/research-owned-army.go').read_text().removeprefix('//go:build ignore\n');t=t[:t.index('func main()')].replace('\n\t"flag"\n','\n');(src/'tools/owned-army-model.go').write_text(t)
  for ext in ['mod','sum']:shutil.copyfile(src/('go.'+ext),q/('probe.'+ext))
  with(q/'probe.mod').open('a')as f:f.write('\nrequire github.com/wicanr2/dosgolem v0.0.0\nreplace github.com/wicanr2/dosgolem => /core\n')
  for n in ['army-catalog.json','combat-catalog.json','original-save.ay','battle-before.state','PAM.AY']:(q/'inputs'/n).write_bytes(m.stored(r,'controlled-owned-battle-r1','/inputs/'+n))
  w=json.loads(m.stored(r,'controlled-owned-battle-r1','/cases/win/receipt.json'))['world_before'];w['encounters']={};write(q/'inputs/world-runtime.json',w)
  (q/'inputs/map01.ay').write_bytes(m.stored(r,'owned-world-army-r1','/port-r2/scratch/map01.ay'))
  (q/'inputs/ida-world-army.json').write_bytes(m.stored(r,'owned-world-army-r1','/ida/ida-world-army-r1.json'))
  (q/'inputs/original-boundaries.json').write_bytes(m.stored(r,'owned-world-r1','/normal-r4/receipt.json'))
  d=read(r/'preserved/owned-encounter-ui-r1.json')
  for f in d['files']:
   if '/ui-assets/'not in f['path']:continue
   target=q/'ui-assets'/f['path'].split('/ui-assets/',1)[1];target.parent.mkdir(parents=True,exist_ok=True);o=d['objects'][f['sha256']];target.write_bytes(gzip.decompress((r/'preserved/owned-encounter-ui-r1'/o['file']).read_bytes()));assert sha(target)==f['sha256']
  patch(src,q);write(q/'baseline.json',deps);return
 assert deps==read(q/'baseline.json')
 if a.action=='freeze':
  for n in NEW:shutil.copyfile(r/'tools'/n,q/'go-src/tools'/n)
  return
 if a.action=='audit':
  receipt=read(q/'pairs/receipt.json');assert receipt['status']=='passed-runtime-enemy-import-pairs'and len(receipt['pairs'])==2 and len(receipt['parser_cases'])==12
  raw=(q/'inputs/PAM.AY').read_bytes();ida=read(q/'inputs/ida-world-army.json');assert sha(q/'inputs/PAM.AY')==ida['source_sha256']=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0';header=struct.unpack_from('<H',raw,8)[0]*16;relocs=[];ida_lines=0
  for i in range(struct.unpack_from('<H',raw,6)[0]):off,seg=struct.unpack_from('<HH',raw,struct.unpack_from('<H',raw,24)[0]+i*4);relocs.append(header+seg*16+off)
  for f in ida['functions']:
   if f['start']not in [0x1151c,0x132e0]:continue
   for line in f['lines']:
    pos=line['file_offset'];want=bytes.fromhex(line['bytes']);b=bytearray(raw[pos:pos+len(want)]);assert pos==line['ida_linear']-0x10000+header
    for loc in relocs:
     if pos<=loc and loc+2<=pos+len(want):struct.pack_into('<H',b,loc-pos,(struct.unpack_from('<H',b,loc-pos)[0]+0x1000)&65535)
    assert bytes(b)==want;ida_lines+=1
  for v in receipt['parser_cases']:
   raw=bytes.fromhex(v['raw_hex']);valid=len(raw)==24;rows=[];seen=set()
   if valid:
    for i in range(6):
     kind,count=struct.unpack_from('<HH',raw,i*4)
     if kind==count==0:rows.append(dict(unit='',count=0));continue
     valid=valid and 1<=kind<=25 and 1<=count<=32767 and kind not in seen;seen.add(kind);rows.append(dict(unit='native:%02d'%kind,count=count))
    valid=valid and bool(seen)
   assert valid==v['accepted']
   if valid:assert rows==v['rows']
  for n in NEW+common(r):
   patch_info=next((v for v in read(q/'adapter-patches.json')if v['file']==n),None)
   if patch_info:assert sha(r/'tools'/n)==patch_info['before']and sha(q/'go-src/tools'/n)==patch_info['after']
   else:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n)
  decoded={}
  for folder in sorted((q/'pairs').iterdir()):
   if not folder.is_dir():continue
   out=folder/'decoded'
   if not out.exists():subprocess.run([str(q/'state-reader'),'-all','-calls',str(folder),'-out',str(out)],check=True)
   decoded[folder.name]=read(out/'index.json')
  for pair in receipt['pairs']:
   name=pair['case'];orig=read(q/'pairs'/(name+'-original')/'generation.json');v=read(q/'pairs'/(name+'-go')/'generation.json');assert orig['enemy_hex']==v['enemy_hex']==pair['enemy_hex']and orig['rng']==v['rng']
   for mode in ['original','go']:
    folder=q/'pairs'/(name+'-'+mode);index=decoded[folder.name];item=index['generated.state'];ram=gzip.decompress((folder/'decoded'/item['memory_file']).read_bytes());assert ram[0x23f80:0x23f98].hex()==pair['enemy_hex'];raw=bytes.fromhex(pair['enemy_hex']);expected=[]
    for i in range(6):
     k,n=struct.unpack_from('<HH',raw,i*4);expected.append(dict(unit=('native:%02d'%k)if k else'',count=n))
    assert v['rows']==expected
    old=index['before-commit.state'];new=index['after-commit.state'];before=gzip.decompress((folder/'decoded'/old['memory_file']).read_bytes());after=gzip.decompress((folder/'decoded'/new['memory_file']).read_bytes());ds=0x1e880;bp=old['registers'][5];u16=lambda b,p:struct.unpack_from('<H',b,p)[0]
    boundary=next(v for v in read(q/'inputs/original-boundaries.json')['events']if v['name']=='battle-call-before');assert list(struct.unpack_from('<12H',before,ds+0x5700))==boundary['battle_56e8'][12:]
    allowed=set(range(ds+0x4f2,ds+0x4fe))|set(range(ds+0x56d6,ds+0x56d8))
    if mode=='go':allowed|=set(range(ds+0x54a,ds+0x562))|set(range(ds+0x56e8,ds+0x5700))
    assert all(x==y or i in allowed for i,(x,y)in enumerate(zip(before,after)))
    assert old['ip']==0x3733 and new['ip']==0x32e0 and new['registers'][4]==bp+2 and new['registers'][5]==u16(before,ds+bp)and new['registers'][6]==u16(before,ds+bp-0x12)and new['registers'][7]==u16(before,ds+bp-0x10)and old['registers'][:4]==new['registers'][:4]
    if mode=='go':
     for state in ['generated.state','held.state','final-map.state']:
      item=index[state];b=gzip.decompress((folder/'decoded'/item['memory_file']).read_bytes());assert b[0x1edca:0x1ede2]==b[0x23f68:0x23f80]==bytes([255])*24
     result=read(folder/'result.json');assert result['rows']==expected and result['return_ip']==0xbd3 and result['native_calls']==0 and result['copy_skipped']==1
     before=read(q/'inputs/world-runtime.json');before['progress']['rank']=v['rank'];before['army']['recruit_rank']=v['rank'];before['revision']+=2;before['army']['gold']=3750;assert result['world']==before
     event=result['event'];source=read(q/'inputs/combat-catalog.json')['profiles']['openkb:wolf'];target=read(q/'inputs/combat-catalog.json')['profiles'][expected[0]['unit']];damage=30*source['attack']//5;quotient=damage//target['hp'];loss=0 if quotient==0 else expected[0]['count']if quotient>=expected[0]['count']-1 else quotient;assert event['damage']==damage and event['loss']==loss and event['before']==expected[0]['count']and event['after']==expected[0]['count']-loss
  compatibility=q/'reader-default'
  if not compatibility.exists():subprocess.run([str(q/'state-reader'),'-calls',str(q/'pairs/rank1-region0-go'),'-out',str(compatibility)],check=True)
  assert all(v==decoded['rank1-region0-go'][n]for n,v in read(compatibility/'index.json').items())and len(read(compatibility/'index.json'))==3
  gui=read(q/'gui-r1/receipt.json');assert gui['status']=='passed-runtime-enemy-ui'and len(gui['cases'])==1
  from PIL import Image
  case=gui['cases'][0];final=case['final'];assert final['battle_finished']and final['runtime_enemy_copy_skipped']==1 and final['battle_native_calls']==0 and final['world']==case['cold']['snapshot']['world']
  folder=q/'gui-r1/runtime';decoded_gui=folder/'decoded'
  if not decoded_gui.exists():subprocess.run([str(q/'state-reader'),'-all','-calls',str(folder),'-out',str(decoded_gui)],check=True)
  idx=read(decoded_gui/'index.json');ram=gzip.decompress((decoded_gui/idx['final-map.state']['memory_file']).read_bytes());assert idx['final-map.state']['ip']==0xbd3 and ram[0x1edca:0x1ede2]==ram[0x23f68:0x23f80]==bytes([255])*24 and ram[0x23f80:0x23f98].hex()==final['runtime_enemy_hex']
  enemy=bytes.fromhex(final['runtime_enemy_hex']);assert final['runtime_enemy_rows']==[dict(unit=('native:%02d'%struct.unpack_from('<H',enemy,i*4)[0])if struct.unpack_from('<H',enemy,i*4)[0]else'',count=struct.unpack_from('<H',enemy,i*4+2)[0])for i in range(6)]
  initial=read(q/'inputs/world-runtime.json');initial['revision']+=2;initial['army']['gold']=3750;assert initial==final['world']
  native=(q/'session-runtime/gamedata.ay').read_bytes();assert native[12:]==(q/'inputs/original-save.ay').read_bytes()[12:];w=final['world'];words=[w['progress']['rank'],w['progress']['merit'],w['progress']['legacy_04f6'],w['army']['gold'],w['army']['leadership'],w['progress']['legacy_04fc']];assert [struct.unpack_from('<H',ram,0x1ed72+i*2)[0]for i in range(6)]==words==[(struct.unpack_from('<H',native,i*2)[0]-i*2-3)&65535 for i in range(6)]
  assert final['world']['army']['gold']==3750 and final['world']['army']['slots'][0]['count']==30 and final['runtime_enemy_rows']==read(q/'gui-r1/runtime/battle-start.json')['world']['battle']['state']['initial'][1]
  for v in case['screens']:
   folder=q/'gui-r1/runtime';im=Image.open(folder/v['canvas']);screen=Image.open(folder/v['screen']);meta=read(folder/v['metadata']);assert im.size==screen.size==(1920,1200)and im.convert('RGB').tobytes()==screen.convert('RGB').tobytes()and hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()==meta['canvas_sha256']==meta['presented_sha256']
   for t in meta['text_fields']or[]:
    box,ink=t['Rect'],t['Ink']
    if ink[2]>ink[0]:assert box[0]<=ink[0]<ink[2]<=box[2]and box[1]<=ink[1]<ink[3]<=box[3]
  assert case['paused']['steps_equal']and case['paused']['cycles_equal']
  write(a.out,dict(status='passed-original-runtime-enemy-import',dependencies=deps,source_tools={n:sha(r/'tools'/n)for n in NEW+common(r)},pairs=receipt,gui=gui,decoded_states=sum(len(v)for v in decoded.values())+len(idx),reader_default_compatibility=3,ida_lines=ida_lines,production_changed=False,controlled_memory=True,normal_player_path=False,limits=['Original RNG/generation retained; Go owns player army/combat/settlement.','Fixed original RNG snapshot and controlled rank/region; no rerolls.','5/5 divisors and retreat2730 remain explicit prototype inputs.']));return
 folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
 for f in sorted(q.rglob('*')):
  if not f.is_file()or 'build-cache'in f.relative_to(q).parts:continue
  assert f.stat().st_uid==1000 and not f.is_symlink();b=f.read_bytes();h=hashlib.sha256(b).hexdigest();obj=folder/(h+'.gz')
  if h not in objects:obj.write_bytes(gzip.compress(b,compresslevel=6,mtime=0));objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
  files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(b),mode=f.stat().st_mode&0o777))
 write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Local original snapshots; full objects excluded from Git.'))
if __name__=='__main__':main()
