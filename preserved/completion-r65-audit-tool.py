#!/usr/bin/env python3
"""054: independent source/frame audit and gated local promotion."""
import argparse,hashlib,importlib.util,json,os,pathlib,shutil
from PIL import Image,__version__
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def rgba(p):return Image.open(p).convert('RGBA')
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--promote',action='store_true');p.add_argument('--player',type=pathlib.Path);p.add_argument('--audit',type=pathlib.Path);a=p.parse_args();r=a.project;b=r/'workplace/probe-20261023/graphics-first/all-graphics-integration-r1';assets=b/'assets-candidate-r1';candidate=r/'workplace/player/source-candidate-completion-r4';base=r/'workplace/player/assets-painted-r64'
 assert os.getuid()==1000 and __version__=='11.3.0' and not a.out.exists()
 if a.promote:
  report=read(a.audit);assert report['status']=='PASS-scoped-054-completion' and a.player and a.player.stat().st_uid==1000;target=a.player/'assets-painted-r65';assert not target.exists()
  for name,digest in report['asset_hashes'].items():assert sha(assets/name)==digest
  for name,digest in report['programs'].items():assert sha(candidate/name)==digest and sha(a.player/name)==report['previous_programs'][name]
  stage=a.player/'.completion-r65.tmp';assert not stage.exists();stage.mkdir()
  for name in report['asset_hashes']:shutil.copyfile(assets/name,stage/name)
  assert len(list(stage.iterdir()))==525;stage.rename(target)
  for name in report['programs']:
   temp=a.player/('.completion-'+name+'.tmp');assert not temp.exists();os.link(candidate/name,temp);os.replace(temp,a.player/name)
  for name in ['build-inputs.sha256','build-outputs.sha256','build-source-checks.log','build-go-version.txt','runtime.json']:shutil.copyfile(candidate/name,a.player/name)
  meta=read(a.player/'runtime.json');meta.update(production=True,spec='docs/spec/054-all-graphics-hd.md',assets='assets-painted-r65',source_inputs=len(report['inputs']),core_files=923);(a.player/'runtime.json').write_text(json.dumps(meta,indent=2)+'\n')
  a.out.write_text(json.dumps(dict(schema=1,status='promoted-scoped-054-completion',assets=target.name,files=525,programs=report['programs'],previous_programs=report['previous_programs'],audit_sha256=sha(a.audit),core_files=923,source_inputs=len(report['inputs'])),indent=2)+'\n');print('promoted r65');return
 registration=read(b/'registration-r1.json');assert len(list(assets.iterdir()))==525
 for name,digest in registration['old_files'].items():assert sha(assets/name)==sha(base/name)==digest
 manifest=read(assets/'completion.json');assert sha(assets/'completion.json')==registration['manifest_sha256']=='f19fd53de76b27e7b6ba36aa0f517957871b73a7bec4372579285404908d3f94'
 assert len(manifest['records'])==62
 for v in manifest['records']:
  assert sha(assets/v['image'])==v['image_sha256'];assert rgba(assets/v['image']).size==(v['width'],v['height']);assert sha(r/'workplace/intake-20261023/sources/game/8sword'/v['source_file'])==v['original_sha256']
  assert (assets/v['image']).is_file() and not(assets/v['image']).is_symlink()
 inputs={}
 for line in (candidate/'build-inputs.sha256').read_text().splitlines():
  digest,name=line.split(None,1);name=name.removeprefix('/project/');assert sha(r/name)==sha(candidate/'src'/name)==digest;inputs[name]=digest
 assert len(inputs)==177
 programs={}
 for line in (candidate/'build-outputs.sha256').read_text().splitlines():
  digest,name=line.split(None,1);name=pathlib.Path(name).name;assert sha(candidate/name)==digest;programs[name]=digest
 assert len(programs)==7
 for name,digest in programs.items():
  assert sha(r/'workplace/player'/name)==sha(r/'workplace/player/source-candidate-ring-r3'/name)
 core=read(candidate/'runtime.json');assert core['total_inputs']==923 and len(core['files'])==923
 for name,digest in core['files'].items():assert sha(r/'workplace/player/runtime-render-r1/src'/name)==digest
 # Compared with r1: status classification, test fixes, and Go solid fills.
 earlier=r/'workplace/player/source-candidate-completion-r1/src'
 for name in inputs:
  if name=='internal/eightsword/completion_assets.go':
   old=(earlier/name).read_text();old=old.replace('"player_records": 17, "archive_records": 45','"new_player_records": 17, "existing_intro_records": 2, "archive_records": 43');assert old==(r/name).read_text()
  elif name=='internal/eightsword/source_render.go':
   assert sha(earlier/name)=='46d443d9c60197f899ec11213b32ebcdcc99b32bd3aed3f54cd557858070c37e'
   assert sha(r/name)=='285cd010d7a31795e8dc995f2c851d8eb898a5ab533ad551f5fbb67370ad5ff0'
  elif name!='internal/eightsword/completion_assets_test.go':assert sha(earlier/name)==sha(r/name)
 for name,required in [('final-tests-r4.log',['TestCompletionSolidPalette','TestCompletionControlledPAM','TestCompletionEndingRuntime','TestCompletionLoadAndAtomicFallback','TestCompletionEndingSourceReplay'])]:
  log=(b/name).read_text();assert '\nPASS\n'in log and '--- FAIL:'not in log
  for test in required:assert '--- PASS: '+test in log
 assert (b/'vet-r4.log').read_text()==''
 spec=importlib.util.spec_from_file_location('completion_ending_model',r/'tools/audit-ending-gui.py');model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
 sources={v['record_sha256']:rgba(r/v['native'])for v in read(r/'artwork/all-graphics-sources-r1.json')['records']if v['category']=='ending'};sources['base']=Image.new('RGBA',(640,200),(255,85,85,255));frame_results=[]
 for path in sorted((b/'runtime-final-r4/ending-controlled').glob('*.json')):
  meta=read(path)
  for font in ['noto','lishu','caoshu']:
   actual=path.with_name(path.stem+'-'+font+'.png');expected=model.reconstruct(dict(meta,font=font),assets,sources);assert expected.tobytes()==rgba(actual).tobytes(),str(actual);frame_results.append(dict(image=str(actual.relative_to(r)),sha256=sha(actual),kind='controlled-ending'))
 pam=b/'runtime-final-r4/pam-controlled'
 for v in read(pam/'receipt.json'):
  out=rgba(pam/v['base']);tex=rgba(assets/v['texture']);x,y,w,h=v['rect']
  if not v['blend']:out.paste(tex,(x,y))
  else:
   dst=bytearray(out.crop((x,y,x+w,y+h)).tobytes());src=tex.tobytes()
   for at in range(0,len(src),4):
    alpha=src[at+3]
    for ch in range(3):
     premul=(src[at+ch]*alpha*257//255)>>8;dst[at+ch]=min(255,premul+(dst[at+ch]*(255-alpha)+127)//255)
    dst[at+3]=255
   out.paste(Image.frombytes('RGBA',(w,h),bytes(dst)),(x,y))
  actual=pam/v['image'];assert out.tobytes()==rgba(actual).tobytes(),str(actual);assert v['guest_equal']and v['Frame_pure'];frame_results.append(dict(image=str(actual.relative_to(r)),sha256=sha(actual),kind='controlled-PAM'))
 runtime=b/'runtime-final-r4';seen={}
 for suffix in ['', '-escape']:
  native=read(runtime/('native'+suffix)/'runtime.json');hd=read(runtime/('hd'+suffix)/'runtime.json')
  for key in ['steps','state_sha256','native_pcm_sha256','inputs','file_ops','mutations','overlays','unimplemented']:assert native[key]==hd[key],key
  assert sha(runtime/('native'+suffix)/'final.state')==sha(runtime/('hd'+suffix)/'final.state')==hd['state_sha256'];assert hd['ending']['counts']['completion-source-commands']>0
  seen[suffix or 'full']={k.removeprefix('completion-'):v for k,v in hd['ending']['counts'].items()if k.startswith('completion-')and k!='completion-source-commands'}
  directory=runtime/('hd'+suffix)
  for path in sorted(directory.glob('sample-*.json')):
   meta=read(path)
   for font in ['noto','lishu','caoshu']:
    actual=path.with_name(path.stem+'-'+font+'.png');assert model.reconstruct(dict(meta,font=font),assets,sources).tobytes()==rgba(actual).tobytes(),str(actual);frame_results.append(dict(image=str(actual.relative_to(r)),sha256=sha(actual),kind='ending-runtime'))
 for name in ['01-main-menu.png','02-map.png','03-character.png','04-army.png']:assert rgba(runtime/'hd'/name).tobytes()==rgba(r/'workplace/probe-20261023/graphics-first/ending-hd-r1/runtime-ring-r3/hd'/name).tobytes()
 gui=b/'gui-r3/menus';state=read(gui/'gui-final.json');assert state['completion_error']=='' and state['completion_assets']['records']==62;assert state['completion_assets']['archive_records']==43;assert 'panic:'not in (gui/'gui-check.log').read_text();assert state['hd']and state['source_renderer'];assert state['owned_render_fault']is None
 for name in programs:assert sha(r/'workplace/player/source-candidate-completion-r4'/name)==programs[name]
 assert len(frame_results)==47
 result=dict(schema=1,status='PASS-scoped-054-completion',files=525,preserved_files=462,new_runtime_records=17,existing_intro_records=2,archive_records=43,player_source_records=290,inputs=inputs,programs=programs,previous_programs={k:sha(r/'workplace/player'/k)for k in programs},asset_hashes={f.name:sha(f)for f in assets.iterdir()},frames=frame_results,actual_ending_sources=seen,gui_final_sha256=sha(gui/'gui-final.json'),core_files=923,manifest_sha256=sha(assets/'completion.json'),tool_sha256=sha(pathlib.Path(__file__)),limits=['Controlled ending branch, not natural victory.','PAM geometry is controlled after ordinary menus, not natural encounter.','Monochrome and IFF archives are packaged, not new game display modes.'])
 a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(status=result['status'],frames=len(frame_results),new_runtime=17)))
if __name__=='__main__':main()
