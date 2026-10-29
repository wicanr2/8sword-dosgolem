#!/usr/bin/env python3
"""Approved VFX artwork and frozen candidate inputs; no executable or gameplay edits."""
import argparse,hashlib,json,os,pathlib,shutil,tempfile
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['approved','freeze'])
 for n in ['project','out']:p.add_argument('--'+n,type=pathlib.Path,required=True)
 p.add_argument('--artwork',type=pathlib.Path);p.add_argument('--player',type=pathlib.Path);a=p.parse_args();r=a.project;assert os.getuid()==1000 and not a.out.exists()
 if a.action=='approved':
  art=a.artwork;assert art and art.stat().st_uid==1000;q=r/'workplace/probe-20261023/graphics-first/battle-r1/battle-vfx-r1';old=read(art/'manifest.json');prior=sha(art/'manifest.json');rows=[]
  for f in sorted((q/'render-r2').glob('b-*.png')):rows.append(dict(source=str(f.relative_to(r)),path='approved/masters/battle-vfx-b-r1/'+f.name,role='master',basis='User explicitly selected B on 2026-10-29; procedural Go source preserved, not image_gen.'))
  for name in ['battle-vfx-flight-r1.png','battle-vfx-impact-r1.png']:rows.append(dict(source='docs/images/'+name,path='approved/masters/battle-vfx-b-r1/'+name,role='approved-reference',basis='Approved B prototype screenshot; HD scene is illustrative, not production same-state.'))
  rows.extend([dict(source=str((q/'render-r2/frames.json').relative_to(r)),path='approved/provenance/battle-vfx-b-r1/frames.json',role='provenance',basis='Original prototype frame geometry; three-second timing is not the live contract.'),dict(source='tools/prototype-battle-vfx.go',path='approved/provenance/battle-vfx-b-r1/generator.go',role='provenance',basis='Exact procedural drawing source for approved B.')]);assert len(rows)==65
  for v in rows:v.update(sha256=sha(r/v['source']),bytes=(r/v['source']).stat().st_size)
  decision=dict(schema=1,choice='B',selected='飛焰＋命中符光',date='2026-10-29',scope='Appearance only; live event lifecycle is specified separately in spec030.',files=rows);decisionpath=art/'battle-vfx-b-approved-r1.json';assert not decisionpath.exists();decisionpath.write_text(json.dumps(decision,ensure_ascii=False,indent=2)+'\n');rows.append(dict(source='artwork/battle-vfx-b-approved-r1.json',path='approved/provenance/battle-vfx-b-r1/decision.json',role='provenance',basis='Explicit user B selection; no generated-image prompt.',sha256=sha(decisionpath),bytes=decisionpath.stat().st_size))
  for v in rows:
   source=r/v['source'];target=art/v['path'];assert source.stat().st_uid==1000 and not source.is_symlink();target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists();shutil.copyfile(source,target);assert sha(target)==v['sha256']and source.stat().st_ino!=target.stat().st_ino
   if target.suffix=='.png':
    from PIL import Image
    with Image.open(target)as im:v['image']=dict(size=list(im.size),mode=im.mode)
  assert sha(art/'manifest.json')==prior;old['files'].extend(rows);old.setdefault('additions',[]).append(dict(index='battle-vfx-b-approved-r1.json',sha256=sha(decisionpath),previous_manifest_sha256=prior,files=len(rows)));fd,name=tempfile.mkstemp(prefix='.vfx-manifest-',dir=art);os.close(fd);tmp=pathlib.Path(name);tmp.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,art/'manifest.json');result=dict(status='preserved-approved-vfx-b',added_files=len(rows),added_pngs=63,manifest_files=len(old['files']),prior_manifest_sha256=prior,manifest_sha256=sha(art/'manifest.json'))
 else:
  player=a.player;old=read(r/'preserved/tactics-audit-r1.json');assert player and player.stat().st_uid==1000
  for n,h in old['programs'].items():assert sha(player/n)==h
  names=set(old['source_inputs'])|{'internal/eightsword/battle_vfx.go','internal/eightsword/battle_vfx_draw.go','internal/eightsword/battle_vfx_test.go','internal/eightsword/battle_vfx_runtime_test.go'};a.out.mkdir();digests={}
  for n in sorted(names):f=r/n;assert f.stat().st_uid==1000;target=a.out/'src'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target);digests[n]=sha(f)
  assert len(digests)==188;(a.out/'preparation.json').write_text(json.dumps(dict(source_count=188,source_inputs=digests,core_files=923,previous_programs=old['programs'],changed=[n for n,h in digests.items()if old['source_inputs'].get(n)!=h]),indent=2)+'\n');(a.out/'build-inputs.sha256').write_text(''.join(f'{h}  /project/{n}\n'for n,h in digests.items()));shutil.copyfile(player/'runtime.json',a.out/'runtime.json');result=dict(status='frozen-vfx-candidate',source_count=188,core_files=923)
 a.out.write_text(json.dumps(result,indent=2)+'\n')if a.action=='approved'else None;print(json.dumps(result))
if __name__=='__main__':main()
