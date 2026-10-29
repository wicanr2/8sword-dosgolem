#!/usr/bin/env python3
"""030: independent full-state, real Draw composition and seven-program promotion."""
import argparse,gzip,hashlib,json,os,pathlib
from PIL import Image
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def same(a,b):assert sha(a)==sha(b),(str(a),str(b))
def draw_audit(gui,phase):
 d=gui/'vfx-draw';m=read(d/(phase+'.json'));assert m['phase']==phase and m['frame_guest_pure']and m['fixture']
 same(d/(phase+'-before.state'),d/(phase+'-after.state'));assert sha(d/(phase+'-before.state'))==m['guest_state_sha256']
 base=Image.open(d/(phase+'-base.png')).convert('RGBA');central=Image.open(d/(phase+'-central.png')).convert('RGBA');presented=Image.open(d/(phase+'-presented.png')).convert('RGBA');assert base.size==central.size==(1920,1200)and presented.size==(2944,1264);assert presented.crop((512,64,2432,1264)).tobytes()==central.tobytes()
 x0,y0,w,h=m['layer_rect'];stride=m['layer_stride'];layer=gzip.decompress((d/(phase+'-layer-rgba.bin.gz')).read_bytes());mask=gzip.decompress((d/(phase+'-native-text-mask.bin.gz')).read_bytes());assert len(mask)==128000 and set(mask)<={0,1}and len(layer)==stride*h and stride==w*4 and 0<=x0<x0+w<=1920 and 0<=y0<y0+h<=1200
 original=base.tobytes();expected=bytearray(original);changed=protected=0
 for y in range(h):
  for x in range(w):
   at=y*stride+x*4;a=layer[at+3]
   if not a:continue
   xx,yy=x0+x,y0+y
   if mask[yy//6*640+xx//3]:protected+=1;continue
   dst=(yy*1920+xx)*4
   for c in range(3):expected[dst+c]=min(255,layer[at+c]+(original[dst+c]*(255-a)+127)//255)
 assert bytes(expected)==central.tobytes(),phase+' independent source-over/text-mask mismatch'
 changed=sum(original[i:i+4]!=expected[i:i+4]for i in range(0,len(expected),4));assert changed>0
 return dict(phase=phase,step=m['step'],draw=m['draw'],changed_pixels=changed,protected_pixels=protected,frame_sha256=sha(d/(phase+'-central.png')),guest_sha256=m['guest_state_sha256'])
def main():
 p=argparse.ArgumentParser()
 for n in ['project','out']:p.add_argument('--'+n,type=pathlib.Path,required=True)
 p.add_argument('--player',type=pathlib.Path);p.add_argument('--audit',type=pathlib.Path);p.add_argument('--promote',action='store_true');a=p.parse_args();r=a.project;player=a.player or r/'workplace/player';q=r/'workplace/probe-20261023/graphics-first/battle-r1/battle-vfx-r1';c=player/'source-candidate-vfx-r2';old=read(r/'preserved/tactics-audit-r1.json');prep=read(c/'preparation.json');assert os.getuid()==1000 and not a.out.exists()
 assert len(prep['source_inputs'])==prep['source_count']==188 and prep['core_files']==923
 for n,h in prep['source_inputs'].items():assert sha(r/n)==sha(c/'src'/n)==h,n
 for n,h in old['programs'].items():assert sha(player/n)==sha(player/'source-candidate-tactics-r2'/n)==h,n
 for n,h in old['asset_hashes'].items():assert sha(player/'assets-painted-r68'/n)==h,n
 core=read(player/'runtime.json');assert len(core['files'])==923
 for n,h in core['files'].items():assert sha(player/'runtime-render-r1/src'/n)==h
 programs={n:sha(c/n)for n in old['programs']};assert len(programs)==7
 log=(q/'tests-r2.log').read_text();assert '\nPASS\n'in log and 'FAIL'not in log and 'SKIP'not in log and not(q/'vet-engine-r2.log').read_text()and 'go1.24.13'in(c/'build-go-version.txt').read_text()and(c/'build-source-checks.log').read_text().count(': OK')==188
 for name in ['TestBattleVFXOriginalExecutors','TestBattleVFXRejectBeforeGuestWrites','TestBattleVFXApprovedKernel','TestBattleVFXTextAndImmutableBase','TestBattleVFXUnknownEffectAndLateCommit']:assert '--- PASS: '+name+' 'in log
 runtime=q/'runtime-r2'
 for name in ['special0-choice','special2-choice','special5-empty-original']:
  ref=q.parent/('ai-policy-extra-r2'if name.startswith('special5')else'ai-policy-r1')/name/'baseline';actual=runtime/name;same(actual/'final.state',ref/'final.state');receipt=read(actual/'receipt.json');v=receipt['battle_vfx'];assert receipt['full_original_state_equal']and receipt['frame_guest_pure']and receipt['synthetic_test_base']and v['Started']==v['Completed']==1 and v['SourceCommits']==4 and v['PONCommits']==12 and not v['Active']
  for phase in ['flight','impact']:same(actual/(phase+'-before.state'),actual/(phase+'-after.state'))
 for name in ['code','selector','mapping','geometry']:same(runtime/('guard-'+name+'-before.state'),runtime/('guard-'+name+'-after.state'))
 cli=read(q/'cli-new-r2/receipt.json');previous=read(q/'cli-old/receipt.json');assert all(cli[k]==v for k,v in previous.items());same(q/'cli-new-r2/final.state',q/'cli-old/final.state');assert Image.open(q/'cli-new-r2/final.png').convert('RGBA').tobytes()==Image.open(q/'cli-old/final.png').convert('RGBA').tobytes()
 gui_results=[]
 for name,fixture in [('gui-normal-r2',False),('gui-fixture-r1',True)]:
  gui=q/name/'save';s=read(gui/'gui-final.json');assert s['closed']and s['exited']and s['exit_code']==0 and s['hd']and s['source_renderer']and s['owned_render_fault']is None and not s['unimplemented']and not s['toolbar_error'];assert read(gui/'gui-input-receipt.json')['status']=='passed-input-path'
  for n in ['player.log','gui-check.log']:assert 'panic:'not in(gui/n).read_text()
  v=s['battle_vfx'];assert v['Bound']and not v['Active'];saved=gui/'saved-gamedata.ay';assert len(saved.read_bytes())==2987 and saved.read_bytes()==(gui/'snapshot-readonly/save-buffer-9e000.bin').read_bytes()
  result=dict(case=name,fixture=fixture,save_sha256=sha(saved),final_state_sha256=sha(gui/'gui-final.state'),vfx=v)
  if fixture:
   probe=s['research_vfx'];assert probe['fixture']and probe['mutations']and 1<=probe['forced_selectors']<=8 and probe['seen']['flight']and probe['seen']['impact'];assert v['Started']>=1 and v['Completed']>=1 and v['Frames']>0;result['draws']=[draw_audit(gui,phase)for phase in ['flight','impact']]
  else:
   assert s['battle_rules']['Mode']=='tactics'and not s['battle_rules']['Active'];assert read(gui/'saved-rules.json')==dict(schema=1,rules='tactics',save_sha256=sha(saved),save_bytes=2987)
  gui_results.append(result)
 reload=q/'gui-normal-r2/reload';s=read(reload/'gui-final.json');assert s['closed']and not s['exited']and s['hd']and s['source_renderer']and s['owned_render_fault']is None and not s['unimplemented']and not s['toolbar_error'];assert read(reload/'gui-input-receipt.json')['status']=='passed-input-path'
 assert s['battle_rules']['Mode']=='tactics'and not s['battle_rules']['Active'];v=s['battle_vfx'];assert v['Bound']and not v['Active']and v['Started']==v['Completed']==v['Frames']==0
 saved=reload/'saved-gamedata.ay';same(saved,q/'gui-normal-r2/save/saved-gamedata.ay');assert saved.read_bytes()==(reload/'snapshot-readonly/save-buffer-9e000.bin').read_bytes();assert read(reload/'saved-rules.json')==read(q/'gui-normal-r2/save/saved-rules.json')
 gui_results.append(dict(case='gui-normal-r2/reload',fixture=False,save_sha256=sha(saved),final_state_sha256=sha(reload/'gui-final.state'),vfx=v))
 private=read(q/'gui-build-r1/preparation.json');assert len(private['base_inputs'])==188 and set(private['changed'])=={'cmd/8sword/main.go','internal/eightsword/battle_vfx.go','internal/eightsword/vfx_gui_probe.go'}
 for n,h in private['base_inputs'].items():assert sha(c/'src'/n)==h
 for n,h in private['diagnostic_inputs'].items():assert sha(q/'gui-build-r1/src'/n)==h
 result=dict(schema=1,status='passed-scoped-vfx-engine',candidate=c.name,source_count=188,source_inputs=prep['source_inputs'],changed_sources=prep['changed'],core_files=923,programs=programs,previous_programs=old['programs'],assets='assets-painted-r68',asset_files=525,asset_hashes=old['asset_hashes'],gui=gui_results,original_effects=3,guard_cases=4,frame_guest_pure=True,lifecycle_audit_sha256=sha(q/'lifecycle-audit-r2.json'),limits=['Only approved B visuals for sampled enemy special 0/2/5; player spell catalog remains open.','Original executors and actual GUI Draw are separate gates; controlled GUI fixture is not natural spell casting.','Source-over/text protection independently rebuilt from immutable Go layers; kernel checked against approved prototype.','No original RGB underlay, new gameplay, save fields, graphics pack or core change.'])
 if a.promote:
  assert a.player and a.audit and read(a.audit)==result;staged={}
  try:
   for n in programs:
    tmp=player/('.vfx-'+n+'.tmp');assert not tmp.exists();os.link(c/n,tmp);staged[n]=tmp
   runtime=read(c/'runtime.json');runtime.update(production=True,application_spec='docs/spec/030-battle-expansion-proposal.md',application_source_inputs=188,battle_vfx='B-flight-impact',assets='assets-painted-r68');meta={n:(c/n).read_bytes()for n in ['build-inputs.sha256','build-source-checks.log','build-go-version.txt']};meta['runtime.json']=(json.dumps(runtime,indent=2)+'\n').encode();meta['build-outputs.sha256']=''.join(f'{h}  /out/{n}\n'for n,h in programs.items()).encode()
   for n,raw in meta.items():
    tmp=player/('.vfx-'+n+'.tmp');assert not tmp.exists();tmp.write_bytes(raw);staged[n]=tmp
   for n,tmp in staged.items():os.replace(tmp,player/n)
  finally:
   for tmp in staged.values():
    if tmp.exists():tmp.unlink()
  for n,h in programs.items():assert sha(player/n)==h
  result=dict(status='promoted-scoped-vfx-engine',audit_sha256=sha(a.audit),programs=programs,source_count=188,core_files=923,assets='assets-painted-r68',asset_files=525)
 a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k in ['status','source_count','gui']}))
if __name__=='__main__':main()
