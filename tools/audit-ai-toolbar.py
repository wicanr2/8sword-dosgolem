#!/usr/bin/env python3
"""Independent scoped acceptance and promotion of the live AI toolbar."""
import argparse, gzip, hashlib, io, json, os, pathlib
from PIL import Image, ImageDraw, ImageFont

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
 p=argparse.ArgumentParser()
 for n in ['project','out']:p.add_argument('--'+n,type=pathlib.Path,required=True)
 p.add_argument('--player',type=pathlib.Path);p.add_argument('--audit',type=pathlib.Path);p.add_argument('--promote',action='store_true');a=p.parse_args();r=a.project;player=a.player or r/'workplace/player';study=r/'workplace/probe-20261023/graphics-first/battle-r1/ai-toolbar-r1';c=player/'source-candidate-ai-toolbar-r1'
 assert os.getuid()==1000 and not a.out.exists()
 old=read(r/'preserved/ai-engine-audit-r1.json');prep=read(c/'preparation.json');assert prep['source_count']==181 and prep['core_files']==923
 for n,h in prep['source_inputs'].items():assert sha(r/n)==sha(c/'src'/n)==h,n
 changed={n for n,h in old['source_inputs'].items()if h!=prep['source_inputs'][n]};assert changed=={'cmd/8sword/main.go','internal/eightsword/poster_toolbar.go','internal/eightsword/poster_toolbar_test.go'},changed
 core=read(player/'runtime.json');assert len(core['files'])==core['total_inputs']==923
 for n,h in core['files'].items():assert sha(player/'runtime-render-r1/src'/n)==h,n
 for n,h in old['programs'].items():assert sha(player/n)==h,n
 programs={n:sha(c/n)for n in old['programs']};assert len(programs)==7
 assets=player/'assets-painted-r66';assert len(list(assets.iterdir()))==525
 asset_hashes={f.name:sha(f)for f in assets.iterdir()if f.is_file() and not f.is_symlink()};assert len(asset_hashes)==525
 for n,h in old['asset_hashes'].items():assert sha(player/'assets-painted-r65'/n)==h,n
 assert {n for n,h in old['asset_hashes'].items()if asset_hashes[n]!=h}=={'poster-toolbar.json','poster-toolbar-font.png'}
 m=read(assets/'poster-toolbar.json');prior=read(player/'assets-painted-r65/poster-toolbar.json');assert m['schema']==2 and m['source_sha256']==prior['source_sha256'] and m['glyphs'][:123]==prior['glyphs'] and len(m['glyphs'])==127
 im=Image.open(assets/'poster-toolbar-font.png').convert('RGBA');base=Image.open(player/'assets-painted-r65/poster-toolbar-font.png').convert('RGBA');assert im.size==base.size==(1024,512) and sha(assets/'poster-toolbar-font.png')==m['atlas_sha256']
 catalog=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));fontsha=m['source_sha256'];raw=gzip.decompress((r/'preserved'/catalog['objects'][fontsha]['path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==fontsha
 font=ImageFont.truetype(io.BytesIO(raw),48,index=3)
 for i,g in enumerate(m['glyphs']):
  if i<123:
   box=(i%16*64,i//16*64,i%16*64+64,i//16*64+64);assert im.crop(box).tobytes()==base.crop(box).tobytes()
  else:
   assert g['character']=='原版策略'[i-123];x,y,w,h=g['ink'];expected=Image.new('RGBA',(w,h));bbox=font.getbbox(g['character']);ImageDraw.Draw(expected).text((-bbox[0],-bbox[1]),g['character'],font=font,fill='white');assert expected.tobytes()==im.crop((x,y,x+w,y+h)).tobytes()
 for name in ['tests-r65.log','tests-r66.log']:
  s=(study/name).read_text();assert '\nPASS\n' in s and 'FAIL' not in s and 'SKIP' not in s,name
 assert not (study/'vet.log').read_text() and 'go1.24.13' in (c/'build-go-version.txt').read_text()
 gui=study/'gui-r1';final=read(gui/'gui-final.json');check=read(gui/'ai-toolbar-check.json');decision=read(gui/'battle-ai-decision.json');assert final['closed'] and final['owned_render_fault'] is None and final['unimplemented']==[] and final['toolbar_error']==''
 ai=final['battle_ai'];assert ai['Mode']=='target' and ai['Bound'] and ai['Decisions']>0 and ai['Fault'] is None and decision['battle_ai']['Decisions']>0
 assert check['before_guest_inputs']==check['after_guest_inputs'] and check['final_mode']=='target'
 expected=[('ai-toolbar-cancel','native','原版 AI'),('ai-toolbar-target','target','策略 AI'),('ai-toolbar-native','native','原版 AI'),('ai-toolbar-after-font','target','策略 AI')]
 assert len(check['evidence'])==4
 for e,(name,mode,label)in zip(check['evidence'],expected):
  assert e['name']==name and e['status']['battle_ai']['Mode']==mode and label in e['title'] and (gui/(name+'.png')).is_file()
 assert check['evidence'][-1]['status']['font_id']!=check['evidence'][-2]['status']['font_id']
 assert 'panic:' not in (gui/'player.log').read_text() and 'panic:' not in (gui/'gui-check.log').read_text()
 result=dict(status='passed-scoped-ai-toolbar',candidate=c.name,programs=programs,previous_programs=old['programs'],source_inputs=prep['source_inputs'],source_count=181,core_files=923,assets='assets-painted-r66',asset_files=525,asset_hashes=asset_hashes,unchanged_r65_assets=523,glyphs=127,gui_decisions=ai['Decisions'],gui_changed=ai['Changed'],guest_menu_inputs_leaked=0,gui_final_sha256=sha(gui/'gui-final.state'),gui_check_sha256=sha(gui/'ai-toolbar-check.json'),source_changed=sorted(changed),default='native',optional='target',limitations=['HD toolbar only; native graphics keeps command-line mode selection.','No new traits or cross-spell policy; no new full-game or platform acceptance.','Original save/load acceptance inherited from the previous AI engine gate.'])
 if a.promote:
  assert a.audit and a.player and player.stat().st_uid==1000;accepted=read(a.audit);assert accepted==result
  staged={}
  try:
   for n in programs:
    tmp=player/('.ai-toolbar-'+n+'.tmp');assert not tmp.exists();os.link(c/n,tmp);staged[n]=tmp
   metadata={n:(c/n).read_bytes()for n in ['build-inputs.sha256','build-source-checks.log','build-go-version.txt']};runtime=read(c/'runtime.json');runtime.update(production=True,application_spec='docs/spec/030-battle-expansion-proposal.md',application_source_inputs=181,battle_ai_toolbar=True,assets='assets-painted-r66');metadata['runtime.json']=(json.dumps(runtime,indent=2)+'\n').encode();metadata['build-outputs.sha256']=''.join(f'{h}  /out/{n}\n'for n,h in programs.items()).encode()
   for n,data in metadata.items():
    tmp=player/('.ai-toolbar-'+n+'.tmp');assert not tmp.exists();tmp.write_bytes(data);staged[n]=tmp
   for n,tmp in staged.items():os.replace(tmp,player/n)
  finally:
   for tmp in staged.values():
    if tmp.exists():tmp.unlink()
  for n,h in programs.items():assert sha(player/n)==h
  result=dict(status='promoted-scoped-ai-toolbar',audit_sha256=sha(a.audit),programs=programs,assets='assets-painted-r66',asset_files=525,source_count=181,core_files=923)
 write(a.out,result);print(json.dumps({k:v for k,v in result.items()if k in ['status','gui_decisions','guest_menu_inputs_leaked','unchanged_r65_assets']}))
if __name__=='__main__':main()
