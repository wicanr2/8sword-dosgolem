#!/usr/bin/env python3
"""030: independent scoped rules acceptance; optional seven-program promotion."""
import argparse,gzip,hashlib,io,json,os,pathlib
from PIL import Image,ImageDraw,ImageFont
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
 p=argparse.ArgumentParser()
 for n in ['project','out']:p.add_argument('--'+n,type=pathlib.Path,required=True)
 p.add_argument('--player',type=pathlib.Path);p.add_argument('--audit',type=pathlib.Path);p.add_argument('--promote',action='store_true');a=p.parse_args();r=a.project;player=a.player or r/'workplace/player';q=r/'workplace/probe-20261023/graphics-first/battle-r1/formation-engine-r1';c=player/'source-candidate-formation-r2';old=read(r/'preserved/ai-toolbar-audit-r1.json');prep=read(c/'preparation.json');assert os.getuid()==1000 and not a.out.exists()
 assert prep['source_count']==len(prep['source_inputs'])==184 and prep['core_files']==923
 for n,h in prep['source_inputs'].items():assert sha(r/n)==sha(c/'src'/n)==h,n
 core=read(player/'runtime.json');assert len(core['files'])==core['total_inputs']==923
 for n,h in core['files'].items():assert sha(player/'runtime-render-r1/src'/n)==h,n
 for n,h in old['programs'].items():assert sha(player/n)==h,n
 programs={n:sha(c/n)for n in old['programs']};assert len(programs)==7
 assets=player/'assets-painted-r67';asset_hashes={f.name:sha(f)for f in assets.iterdir()if f.is_file() and not f.is_symlink()};assert len(list(assets.iterdir()))==len(asset_hashes)==525
 for n,h in old['asset_hashes'].items():assert sha(player/'assets-painted-r66'/n)==h
 assert {n for n,h in old['asset_hashes'].items()if asset_hashes[n]!=h}=={'poster-toolbar.json','poster-toolbar-font.png'}
 m=read(assets/'poster-toolbar.json');prior=read(player/'assets-painted-r66/poster-toolbar.json');assert m['schema']==3 and m['source_sha256']==prior['source_sha256'] and m['glyphs'][:127]==prior['glyphs'] and len(m['glyphs'])==137
 im=Image.open(assets/'poster-toolbar-font.png').convert('RGBA');base=Image.open(player/'assets-painted-r66/poster-toolbar-font.png').convert('RGBA');assert im.size==(1024,576) and base.size==(1024,512) and sha(assets/'poster-toolbar-font.png')==m['atlas_sha256']
 catalog=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));h=m['source_sha256'];raw=gzip.decompress((r/'preserved'/catalog['objects'][h]['path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==h;font=ImageFont.truetype(io.BytesIO(raw),48,index=3)
 for i,g in enumerate(m['glyphs']):
  if i<127:
   box=(i%16*64,i//16*64,i%16*64+64,i//16*64+64);assert im.crop(box).tobytes()==base.crop(box).tobytes()
  else:
   assert g['character']=='規則結陣試作本場固定'[i-127];x,y,w,h=g['ink'];expected=Image.new('RGBA',(w,h));bbox=font.getbbox(g['character']);ImageDraw.Draw(expected).text((-bbox[0],-bbox[1]),g['character'],font=font,fill='white');assert expected.tobytes()==im.crop((x,y,x+w,y+h)).tobytes()
 for name in ['tests-poster-r67-r2.log','tests-poster-r66-r2.log']:
  s=(q/name).read_text();assert '\nPASS\n'in s and 'FAIL'not in s and 'SKIP'not in s,name
 s=(q/'tests-r2.log').read_text();assert '\nPASS\n'in s and 'FAIL'not in s and '--- PASS: TestBattleRulesOriginalHelpers 'in s and '--- PASS: TestBattleRulesFaultsAndAuto 'in s and '--- PASS: TestRulesMarkerBindingAndCorruption 'in s
 assert not(q/'vet-r2.log').read_text() and 'go1.24.13'in(c/'build-go-version.txt').read_text()
 calls=r/'workplace/probe-20261023/graphics-first/battle-r1/formation-hooks-r1/calls-r2';states=[]
 for side in ['player','enemy']:
  for case in ['front-ally','alone','rear-ally','rear-target','other-kind','two-allies']:
   for mode,ref in [('native','baseline'),('formation','formation')]:
    n=side+'-'+case;actual=q/'runtime-r2'/(n+'-'+mode);source=calls/n/ref;info=read(actual/'rules.json');t=read(source/'trace.json');assert sha(actual/'final.state')==sha(source/'final.state')
    assert info['Mode']==mode and info['Fault']is None
    assert info['Calls']==(mode=='formation') and info['Applied']==(mode=='formation'and t['eligible'])
    # The earlier sealed oracle and new pre-Step fixture must agree at return.
    assert sha(source/'final.state')==sha(calls.parent/'calls-r1'/n/ref/'final.state')
    states.append(dict(case=n,mode=mode,sha256=sha(actual/'final.state')))
 for fault in ['bytes','mapping','stack']:assert sha(q/f'runtime-r2/fault-{fault}-before.state')==sha(q/f'runtime-r2/fault-{fault}-after.state')
 cli=read(q/'cli-native-r2/receipt.json');prior_cli=read(q/'cli-old/receipt.json')
 for k,v in prior_cli.items():assert cli[k]==v,k
 assert sha(q/'cli-native-r2/final.state')==sha(q/'cli-old/final.state') and Image.open(q/'cli-native-r2/final.png').convert('RGBA').tobytes()==Image.open(q/'cli-old/final.png').convert('RGBA').tobytes()
 gui=q/'gui-r2';phases={}
 for phase,start,end in [('save','native','formation'),('restore-formation','formation','native'),('restore-native','native','native')]:
  d=gui/phase;s=read(d/'gui-final.json');assert s['closed'] and s['hd'] and s['source_renderer'] and s['owned_render_fault']is None and s['unimplemented']==[] and s['toolbar_error']==''
  rule=s['battle_rules'];assert rule['Mode']==end and rule['Fault']is None and not rule['Active']
  initial=read(d/'rules-startup.json');assert initial['status']['battle_rules']['Mode']==start
  assert ('原版規則'if start=='native'else'結陣試作')in initial['title']
  marker=read(d/'saved-rules.json');data=d/'saved-gamedata.ay';assert marker==dict(schema=1,rules=end,save_sha256=sha(data),save_bytes=2987) and data.stat().st_size==2987
  assert data.read_bytes()==(d/'snapshot-readonly/save-buffer-9e000.bin').read_bytes()
  assert 'panic:'not in(d/'player.log').read_text() and 'panic:'not in(d/'gui-check.log').read_text()
  if phase=='save':
   assert s['exited']and s['exit_code']==0 and rule['Started']>=1 and rule['Finished']>=1 and rule['Calls']>0 and rule['Markers']>0
   locked=read(d/'rules-battle-locked.json')['status'];assert locked['battle_rules']['Active'] and locked['battle_rules']['Mode']=='formation' and locked['battle_ai']['Mode']=='target'
   after=read(d/'rules-after-battle.json')['status']['battle_rules'];assert {v['Side']for v in after['Recent']}=={'player','enemy'}
  elif phase=='restore-formation':assert rule['Markers']>0
  phases[phase]=dict(start=start,end=end,started=rule['Started'],finished=rule['Finished'],calls=rule['Calls'],applied=rule['Applied'],markers=rule['Markers'],save_sha256=sha(data),final_state_sha256=sha(d/'gui-final.state'),draws=s['presented_frames'])
 result=dict(schema=1,status='passed-scoped-030-formation',candidate=c.name,programs=programs,previous_programs=old['programs'],source_inputs=prep['source_inputs'],source_count=184,core_files=923,assets='assets-painted-r67',asset_files=525,asset_hashes=asset_hashes,unchanged_r66_assets=523,glyphs=137,controlled_states=states,gui=phases,default='auto',missing_marker='native',optional='formation',default_cli_state_sha256=sha(q/'cli-native-r2/final.state'),limits=['One normal GUI battle and 24 controlled complete helper states; no whole-campaign balance claim.','Original integer damage resolver retained; no new troop IDs, spell traits or game save fields.','Native video has CLI rules selection; toolbar follows existing HD video.'])
 if a.promote:
  assert a.player and a.audit and read(a.audit)==result;staged={}
  try:
   for n in programs:
    tmp=player/('.formation-'+n+'.tmp');assert not tmp.exists();os.link(c/n,tmp);staged[n]=tmp
   runtime=read(c/'runtime.json');runtime.update(production=True,application_spec='docs/spec/030-battle-expansion-proposal.md',application_source_inputs=184,battle_rules_modes=['auto','native','formation'],battle_rules_toolbar=True,battle_ai_toolbar=True,assets='assets-painted-r67')
   meta={n:(c/n).read_bytes()for n in ['build-inputs.sha256','build-source-checks.log','build-go-version.txt']};meta['runtime.json']=(json.dumps(runtime,indent=2)+'\n').encode();meta['build-outputs.sha256']=''.join(f'{h}  /out/{n}\n'for n,h in programs.items()).encode()
   for n,data in meta.items():
    tmp=player/('.formation-'+n+'.tmp');assert not tmp.exists();tmp.write_bytes(data);staged[n]=tmp
   for n,tmp in staged.items():os.replace(tmp,player/n)
  finally:
   for tmp in staged.values():
    if tmp.exists():tmp.unlink()
  for n,h in programs.items():assert sha(player/n)==h
  result=dict(status='promoted-scoped-030-formation',audit_sha256=sha(a.audit),programs=programs,assets='assets-painted-r67',asset_files=525,source_count=184,core_files=923)
 write(a.out,result);print(json.dumps({k:v for k,v in result.items()if k in ['status','source_count','glyphs','unchanged_r66_assets']}))
if __name__=='__main__':main()
