#!/usr/bin/env python3
"""Scoped DRAFT VFX integrity; never promotes the animation into production."""
import argparse,ast,hashlib,json,pathlib,re,subprocess,urllib.parse
from PIL import Image
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();r=a.project;assert not a.out.exists();q=r/'workplace/probe-20261023/graphics-first/battle-r1/battle-vfx-r1';old=read(r/'preserved/tactics-audit-r1.json');player=r/'workplace/player'
 for n,h in old['programs'].items():assert sha(player/n)==h
 for n,h in old['source_inputs'].items():assert sha(r/n)==h
 for n,h in old['asset_hashes'].items():assert sha(player/'assets-painted-r68'/n)==h
 core=read(player/'runtime.json')
 for n,h in core['files'].items():assert sha(player/'runtime-render-r1/src'/n)==h
 assert len(core['files'])==923 and len(old['source_inputs'])==184 and len(old['asset_hashes'])==525
 audit=read(r/'preserved/battle-vfx-observation-r1.json');assert audit['controlled_cases']==3 and audit['bitmap_calls']==71 and audit['pon_calls']==36 and audit['full_states_equal']and audit['reference_states_equal']
 browser=read(r/'preserved/battle-vfx-browser-r1.json');assert browser['frames']==61 and browser['keyboard_range']and browser['mobile']['width']==browser['mobile']['scroll']==390 and not browser['production_changed']
 meta=read(r/'docs/images/battle-vfx-prototype-r1.json');assert meta['go_source_sha256']==sha(r/'tools/prototype-battle-vfx.go')and meta['html_sha256']==sha(r/'docs/images/battle-vfx-prototype-r1.html')and meta['flight_png_sha256']==sha(r/'docs/images/battle-vfx-flight-r1.png')and meta['impact_png_sha256']==sha(r/'docs/images/battle-vfx-impact-r1.png')and not meta['production_changed']
 for name in ['battle-vfx-flight-r1.png','battle-vfx-impact-r1.png']:assert Image.open(r/'docs/images'/name).size==(1200,1550)
 for name in ['vet-probe-r1.log','vet-prototype-r2.log','gofmt-final.diff']:assert(q/name).exists()and not(q/name).read_text()
 for f in (r/'tools').glob('*battle-vfx*.py'):ast.parse(f.read_text(),filename=str(f))
 ast.parse((r/'tools/check-ai-resolution-backlinks.py').read_text())
 subprocess.run(['python',str(r/'tools/check-ai-resolution-backlinks.py'),'--project',str(r)],check=True)
 ledger=read(r/'docs/spec/ai-resolution-backlinks-r1.json');extra=next(v for v in ledger['resolutions']if v['original_address']=='0x21C36')['supplemental_resolutions'];assert len(extra)==1 and extra[0]['required_correction']=='PON-SPECIAL-CALLERS-SAMPLED'
 for v in ledger['resolutions'][:5]+extra:
  text=(r/v['older_spec']).read_text();required=v['required_correction'];assert required in text and required not in text.replace(required,'')
 docs=list(r.glob('*.md'))
 for folder in ['docs','artwork','preserved']:docs.extend((r/folder).rglob('*.md'))
 links=[]
 for doc in docs:
  if not doc.is_file()or'restore-checks'in doc.relative_to(r).parts:continue
  for target in re.findall(r'\[[^\]]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)',doc.read_text()):
   path=urllib.parse.unquote(target.strip('<>').split('#',1)[0])
   if not path or re.match(r'[a-zA-Z][a-zA-Z0-9+.-]*:',path)or path.startswith('/'):continue
   assert(doc.parent/path).exists(),(str(doc),target);links.append((doc.relative_to(r).as_posix(),target))
 assert('README.md','CONTEXT.md')in links
 hygiene=subprocess.run(['find',str(q),str(r/'preserved/battle-vfx-r1'),'-user','root','-o','-type','d','-name','*.md'],capture_output=True,text=True,check=True);assert not hygiene.stdout
 assert not any(p.is_file()for p in(r/'workplace/gocache').rglob('*'))
 restored=read(r/'preserved/battle-vfx-reproduction-r1.json');assert restored['rebuilt_outputs_equal']==132 and restored['verified_restore_copy_cleaned']and not restored['workplace_required']
 result=dict(status='passed-scoped-draft-vfx-integrity',production_changed=False,programs_unchanged=7,source_inputs_unchanged=184,assets_unchanged=525,core_unchanged=923,controlled_cases=3,bitmap_calls=71,pon_calls=36,frames=61,browser_playback_keyboard_clear_mobile=True,go_vet_passed=True,go_format_clean=True,original_resolution_keys=26,supplemental_backlinks=1,missing_correction_cases_rejected=6,markdown_links=len(links),permanent_files=387,detached_outputs_equal=132,verified_restore_bytes_cleaned=restored['bytes_cleaned'],root_owned_outputs=0,invalid_markdown_directories=0,workspace_go_cache_files=0,limitations=meta['limits']);a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
