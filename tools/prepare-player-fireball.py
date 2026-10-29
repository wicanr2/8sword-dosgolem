#!/usr/bin/env python3
"""188-input player fireball candidate and isolated original-menu GUI diagnostic."""
import argparse,hashlib,json,os,pathlib,shutil,subprocess
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','gui'])
 for n in ['project','out']:p.add_argument('--'+n,type=pathlib.Path,required=True)
 p.add_argument('--source',type=pathlib.Path);p.add_argument('--spell',type=int,choices=[0,1,2],default=0);a=p.parse_args();r=a.project;assert os.getuid()==1000 and not a.out.exists()
 if a.action=='freeze':
  old=json.loads((r/({0:'preserved/vfx-engine-audit-r1.json',1:'preserved/player-fireball-audit-r1.json',2:'preserved/player-thunder-audit-r1.json'}[a.spell])).read_text());player=r/'workplace/player'
  for n,h in old['programs'].items():assert sha(player/n)==h
  a.out.mkdir();inputs={}
  for n in old['source_inputs']:
   f=r/n;target=a.out/'src'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target);inputs[n]=sha(f)
  assert len(inputs)==188;shutil.copyfile(player/'runtime.json',a.out/'runtime.json');(a.out/'preparation.json').write_text(json.dumps(dict(source_inputs=inputs,source_count=188,core_files=923,previous_programs=old['programs'],changed=[n for n,h in inputs.items()if old['source_inputs'][n]!=h]),indent=2)+'\n');(a.out/'build-inputs.sha256').write_text(''.join(f'{h}  /project/{n}\n'for n,h in inputs.items()));print('Frozen 188 inputs');return
 assert a.source
 subprocess.run(['python',str(r/'tools/prepare-vfx-gui.py'),'--project',str(r),'--source',str(a.source),'--out',str(a.out)],check=True)
 root=a.out/'src';probe=root/'internal/eightsword/vfx_gui_probe.go';text=probe.read_text();start=text.index('func (e *Engine) ResearchVFXTick()');end=text.index('func (e *Engine) ResearchVFXFrame(',start);fragment=(r/'tools/player-fire-fixture.go').read_text();fragment=fragment[fragment.index('var playerFireMenu'):];text=text[:start]+fragment+'\n'+text[end:];assert text.count('"armed": researchVFX.armed')==1;text=text.replace('"armed": researchVFX.armed','"player_expected_effects":playerFireExpected,"player_spell_complete":playerFireFinished,"armed": researchVFX.armed');probe.write_text(text)
 s=(a.out/'ai-gui-check.go').read_text();s=s.replace('deadline := time.Now().Add(30 * time.Second)','deadline := time.Now().Add(120 * time.Second)');start=s.index('func (d *driver) battle()');end=s.index('func (d *driver) dismissArmy',start);part=s[start:end];mark='shot("battle-02-selected-yes")';at=part.index(mark)+len(mark)
 tail='''
 d.press(36)
 d.wait("受控火球完整返回與兩張實際Draw",120,func(s map[string]any)bool{
  v:=s["battle_vfx"].(map[string]any);r,_:=s["research_vfx"].(map[string]any);seen,_:=r["seen"].(map[string]any)
  return r["player_spell_complete"]==true&&v["Completed"].(float64)>=1&&seen["flight"]==true&&seen["impact"]==true
 })
 shot("player-fire-complete")
 d.receipt("controlled-player-fire")
 d.quit()
 os.Exit(0)
}

'''
 part=part[:at]+tail;s=s[:start]+part+s[end:];s=s.replace(' beforeAI:=d.status()["battle_ai"].(map[string]any)["Decisions"].(float64)','');s=s.replace('beforeAI := d.status()["battle_ai"].(map[string]any)["Decisions"].(float64)','');part=s[s.index('func (d *driver) battle()'):s.index('func (d *driver) dismissArmy')];part=part.replace('stableText := func()', '_ = func()');s=s[:s.index('func (d *driver) battle()')]+part+s[s.index('func (d *driver) dismissArmy'):];(a.out/'player-fire-gui-check.go').write_text(s)
 if a.spell==1:
  s=s.replace('受控火球','受控雷火').replace('player-fire-complete','player-thunder-complete');(a.out/'player-fire-gui-check.go').write_text(s)
 if a.spell==2:
  s=s.replace('受控火球','受控殺鬼').replace('player-fire-complete','player-exorcism-complete');(a.out/'player-fire-gui-check.go').write_text(s)
 meta=json.loads((a.out/'preparation.json').read_text());meta['diagnostic_inputs']={str(p.relative_to(root)):sha(p)for p in root.rglob('*')if p.is_file()};meta['changed']=[n for n,h in meta['diagnostic_inputs'].items()if meta['base_inputs'].get(n)!=h];meta['spell']=a.spell;meta['fixture']='First original player round: rear kind10/count50, learned flag and two uses of spell '+str(a.spell)+'; original spell menu IRQ1 input. No production test branch.';(a.out/'preparation.json').write_text(json.dumps(meta,indent=2)+'\n');print('Private player spell GUI prepared:',a.spell)
if __name__=='__main__':main()
