#!/usr/bin/env python3
"""Check source relocation, actual native import, UI and legacy save continuity."""
import argparse,base64,copy,hashlib,importlib.util,json,os,re,struct
from pathlib import Path
from PIL import Image
REL='workplace/probe-20261023/graphics-first/battle-r1/owned-player-r1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['expected','audit']);p.add_argument('--project',type=Path,required=True);p.add_argument('--out',type=Path);p.add_argument('--images',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000;r=a.project;q=r/REL
 sp=importlib.util.spec_from_file_location('prep',r/'tools/prepare-owned-player.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);h=m.helper(r);deps=h.dependencies(r);assert deps==read(q/'baseline.json')
 origin=read(q/'adapter-origin.json');assert origin['parent_archive_sha256']==sha(r/'preserved/reinforcement-camps-r1.json')
 layers=[13,15,20,24,27,38,39,44,49,54,60,62,65];assert origin['init_layers']==layers
 if a.action=='expected':
  folder=q/'expected';assert not folder.exists();folder.mkdir()
  for i,row in enumerate(origin['files']):
   raw=h.stored(r,m.PARENT,'/'+m.PARENT+'/go-src/'+row['parent_path']);assert hashlib.sha256(raw).hexdigest()==row['parent_sha256']
   s=raw.decode().removeprefix('//go:build ignore\n').replace('package main','package ownedworld',1)
   if i in layers:assert s.count('func init()')==1;s=s.replace('func init()',f'func initializeLayer{i:02d}()')
   else:assert 'func init()'not in s
   if row['parent_path'].endswith('/world-army-review_main.go'):
    s=s[:s.index('func main()')]+'// Run starts the Go-owned army command. Call once per process.\nfunc Run() error { return runArmyReview() }\n'
    s=s.replace('flag.Parse()','flag.Parse()\n if !*owned{return errors.New("Go軍隊命令不接受owned=false，原版模式請用8sword")}')
    s=s.replace('*scratch == "" ||','(*scratch == "" && !*nativeImportOnly) ||')
    s=s.replace('store, snap, e := openProgressPair(*session, c, cc)','if *nativeImportSource!="" { if e:=importNativeProgress(*root,*nativeImportSource,*session,*input,c,cc);e!=nil{return e};if *nativeImportOnly{return nil} } else if *nativeImportOnly{return errors.New("import-only requires import-native")}\n store, snap, e := openProgressPair(*session, c, cc)')
   (folder/Path(row['path']).name).write_text(s)
  (folder/'initialization.go').write_text('package ownedworld\n\n// Preserve the verified explicit-file compilation order.\nfunc init(){\n'+''.join(f'initializeLayer{i:02d}()\n'for i in layers)+'}\n')
  raw=h.stored(r,m.PARENT,'/'+m.PARENT+'/go-src/internal/eightsword/recruit_icons_candidate.go').decode().replace("// Copied without the ignore tag into the isolated candidate's game package.",'// Read-only HD recruitment portraits; source mapping follows spec 030.')
  (folder/'recruitment_icons.go').write_text(raw);return
 for row in origin['files']:
  assert(q/'expected'/Path(row['path']).name).read_bytes()==(r/row['path']).read_bytes(),row['path']
 assert(q/'expected/initialization.go').read_bytes()==(r/'internal/ownedworld/initialization.go').read_bytes()
 assert(q/'expected/recruitment_icons.go').read_bytes()==(r/'internal/eightsword/recruitment_icons.go').read_bytes()
 for n,d in read(q/'source-manifest.json').items():assert sha(r/n)==d==sha(q/'source'/n),n
 for n in m.NEW:assert sha(r/'tools'/n)==sha(q/n),n
 native_root=r/'workplace/intake-20261023/sources/game/8sword';raw=(native_root/'GAMEDATA.AY').read_bytes();assert len(raw)==2987
 words=[(struct.unpack_from('<H',raw,i*2)[0]-i*2-3)&65535 for i in range(18)]
 slots=[dict(unit=f'native:{words[6+i*2]:02d}'if words[6+i*2]else'',count=words[7+i*2])for i in range(6)]
 pam=(q/'inputs/PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0';header=struct.unpack_from('<H',pam,8)[0]*16
 thresholds=list(struct.unpack_from('<6H',pam,header+0x1d780+0x5b2))
 expected=dict(schema='eightsword-owned-world/1',revision=0,army=dict(gold=words[3],leadership=words[4],recruit_rank=words[0],rules='native',slots=slots,offers={}),progress=dict(rank=words[0],merit=words[1],legacy_04f6=words[2],legacy_04fc=words[5],thresholds=thresholds),encounters={},battle=None)
 saved=read(q/'initial-import/gamedata.ay.army.json');assert saved['schema']=='eightsword-owned-world-save/5'and saved['world']==expected
 assert(q/'initial-import/gamedata.ay').read_bytes()==raw and saved['original_sha256']==hashlib.sha256(raw).hexdigest()
 for i in range(9):assert base64.b64decode(saved['native_files'][f'map{i:02d}.ay'])==(native_root/f'MAP{i:02d}.AY').read_bytes()
 unit=read(q/'import-test-r1.json');assert unit['status']=='passed-native-import'and len(unit['refusals'])==10 and unit['saved_map_preferred']
 gui=read(q/'gui-r1/receipt.json');assert gui['status']=='passed-owned-player-native-import-ui'and not gui['native_import_fixture_army_used']and gui['legacy_battle_origin_controlled_initial_army']and not gui['memory_injected']
 assert gui['initial']['world']==expected==gui['army']['world']
 catalog={u['id']:u for u in read(q/'inputs/army-catalog.json')['profiles']};expected=copy.deepcopy(expected);expected['revision']=3;expected['army']['rules']='tactics';expected['army']['offers']['native-camp:00:01']=dict(unit='native:01',stock=3000)
 for suffix in ['arcr','pike','wolf','skel','troll','drui','vamp','drag']:
  u=catalog['openkb:'+suffix];expected['army']['offers'][f'reinforce:00:01:01:{suffix}']=dict(unit=u['id'],stock=3000//u['gold'])
 assert expected==gui['camp']['world'];expected['revision']+=1;expected['army']['gold']-=40;expected['army']['slots'][1]=dict(unit='openkb:wolf',count=1);expected['army']['offers']['reinforce:00:01:01:wolf']['stock']-=1
 assert expected==gui['purchased']['world'];expected['revision']+=1;assert expected==gui['checkpoint']['world']==gui['cold']['world']==gui['cold_army']['world']
 battle=read(q/'session-battle-r1/gamedata.ay.army.json');assert battle['world']==gui['battle']['world']and battle['native_resume']['phase']=='battle'and gui['battle']['world']['battle']['state']['acted'][0][1];assert gui['battle']['battle_native_calls']==0
 frames=[]
 for v in gui['screens']:
  folder=q/'gui-r1'/v['phase'];meta=read(folder/v['metadata']);im=Image.open(folder/v['canvas']).convert('RGBA');x11=Image.open(folder/v['screen']).convert('RGBA');assert im.size==x11.size==(1920,1200);assert im.tobytes()==x11.tobytes();assert hashlib.sha256(x11.tobytes()).hexdigest()==meta['canvas_sha256']==meta['presented_sha256'];frames.append(dict(name=v['name'],sha256=sha(folder/v['canvas'])))
 if a.images:
  pubs=[]
  for name in ['native-import-army','native-import-cold-army','owned-command-cold-battle']:
   v=next(v for v in gui['screens']if v['name']==name);source=q/'gui-r1'/v['phase']/v['canvas'];dest=a.images/('owned-player-'+name+'-r1.png');assert not dest.exists();im=Image.open(source);im.thumbnail((960,600),Image.Resampling.LANCZOS);im.save(dest);pubs.append(dict(source=str(source.relative_to(r)),source_sha256=sha(source),published=dest.name,published_sha256=sha(dest)))
  write(a.images/'owned-player-runtime-r1.json',dict(images=pubs,native_import_fixture_army_used=False,legacy_battle_origin_controlled_initial_army=True,memory_injected=False,old_battle_from_previous_real_save=True,default_original_player_unchanged=True))
 cli=read(q/'cli-controls-r1.json');assert cli['status']=='passed-owned-player-cli-controls'
 write(a.out,dict(status='passed-owned-player-command-and-native-import',source_files=len(origin['files']),init_order=layers,program_sha256=sha(q/'8sword-owned'),source_manifest=read(q/'source-manifest.json'),source_tools={n:sha(r/'tools'/n)for n in m.NEW},dependencies=deps,native_sha256=hashlib.sha256(raw).hexdigest(),thresholds=thresholds,refusals=unit['refusals'],frames=frames,cli=cli,default_original_player_unchanged=True,old_v5_battle_read=True,release=False,limits=['Native save import and Continue, not direct Go new-game creation.','Native import uses no fixture army; the legacy battle retains its previous controlled starting army.','One imported army/recruit/F7 path and one legacy v5 battle resume; no replay of all mechanics or new campaign parity.']))
if __name__=='__main__':main()
