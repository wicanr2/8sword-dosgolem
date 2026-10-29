#!/usr/bin/env python3
"""Freeze the 190-input quake candidate and adapt the existing private player GUI."""
import argparse,hashlib,json,os,pathlib,shutil,subprocess
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','gui'])
 for n in ['project','out']:p.add_argument('--'+n,type=pathlib.Path,required=True)
 p.add_argument('--source',type=pathlib.Path);a=p.parse_args();r=a.project;assert os.getuid()==1000 and not a.out.exists()
 if a.action=='freeze':
  old=json.loads((r/'preserved/player-target-spells-audit-r1.json').read_text());player=r/'workplace/player'
  for n,h in old['programs'].items():assert sha(player/n)==h
  names=set(old['source_inputs'])|{'internal/eightsword/battle_quake.go','internal/eightsword/battle_quake_test.go'};a.out.mkdir();inputs={}
  for n in sorted(names):
   f=r/n;assert f.stat().st_uid==1000;target=a.out/'src'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target);inputs[n]=sha(f)
  assert len(inputs)==190;shutil.copyfile(player/'runtime.json',a.out/'runtime.json');(a.out/'preparation.json').write_text(json.dumps(dict(source_inputs=inputs,source_count=190,core_files=923,previous_programs=old['programs'],changed=[n for n,h in inputs.items()if old['source_inputs'].get(n)!=h]),indent=2)+'\n');(a.out/'build-inputs.sha256').write_text(''.join(f'{h}  /project/{n}\n'for n,h in inputs.items()));print('Frozen190 inputs');return
 assert a.source
 subprocess.run(['python',str(r/'tools/prepare-player-fireball.py'),'gui','--spell','7','--project',str(r),'--source',str(a.source),'--out',str(a.out)],check=True)
 root=a.out/'src';probe=root/'internal/eightsword/vfx_gui_probe.go';s=probe.read_text();s=s.replace('if v == nil || !v.Active || frame != v.cached || researchVFXScene == nil {','if v == nil || !v.Active || !v.quake || frame != v.cached || researchVFXScene == nil {',1);s=s.replace('key := v.cachedPhase','key := "quake-low"\n if v.Shift[1]==18 {key="quake-high"} else if v.Shift[1]!=6 {return nil}',1)
 start=s.index('\tlayer := drawBattleVFX(');end=s.index('\tmask := make(',start);s=s[:start]+'\tlayer := image.NewRGBA(image.Rect(0,0,1,1))\n'+s[end:];probe.write_text(s)
 quake=root/'internal/eightsword/battle_quake.go';s=quake.read_text();needle='visible := p.cachedScene.Pixels[';assert s.count(needle)==1;s=s.replace(needle,'researchVFXScene=p.cachedScene\n '+needle,1);quake.write_text(s)
 driver=a.out/'player-fire-gui-check.go';s=driver.read_text().replace('seen["flight"]','seen["quake-low"]').replace('seen["impact"]','seen["quake-high"]').replace('受控火球','受控地震').replace('player-fire-complete','player-quake-complete');driver.write_text(s)
 meta=json.loads((a.out/'preparation.json').read_text());meta['diagnostic_inputs']={str(f.relative_to(root)):sha(f)for f in root.rglob('*')if f.is_file()};meta['changed']=[n for n,h in meta['diagnostic_inputs'].items()if meta['base_inputs'].get(n)!=h];meta['fixture']='Rear caster, learned and spell7 resources only; original menu IRQ1, no selector/target/RNG/damage writes.';(a.out/'preparation.json').write_text(json.dumps(meta,indent=2)+'\n');print('Private quake GUI prepared')
if __name__=='__main__':main()
