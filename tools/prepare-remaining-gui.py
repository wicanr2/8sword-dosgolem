"""One representative actual-window clone cast using the existing original-menu driver."""
import argparse,hashlib,json,pathlib,subprocess
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser()
 for n in ['project','source','out']:p.add_argument('--'+n,type=pathlib.Path,required=True)
 p.add_argument("--spell",choices=["clone","freeze"],default="clone");a=p.parse_args();r=a.project
 subprocess.run(['python',str(r/'tools/prepare-player-fireball.py'),'gui','--spell','5','--project',str(r),'--source',str(a.source),'--out',str(a.out)],check=True)
 root=a.out/'src';probe=root/'internal/eightsword/vfx_gui_probe.go';s=probe.read_text();s=s.replace('v := e.battleVFX\n\tif v == nil || !v.Active || frame != v.cached || researchVFXScene == nil {','v := e.spellCues\n\tif v == nil || !v.Active || frame != v.cached || researchVFXScene == nil || v.sample < 12 {',1);s=s.replace('key := v.cachedPhase','key := "cue-early"\n if v.sample >= 60 {key="cue-late"}',1);s=s.replace('e.battleVFX = nil\n\tbase := e.sourceRender()\n\te.battleVFX = v','e.spellCues = nil\n\tbase := e.sourceRender()\n\te.spellCues = v',1);s=s.replace('drawBattleVFX(key, float64(v.cachedSample)/120, v.Source, v.Target)','drawSpellCue(v.Kind, float64(v.sample)/120, v.Anchor)',1).replace('"sample": v.cachedSample, "vfx": v.BattleVFXInfo','"sample": v.sample, "vfx": v.SpellCueInfo',1);probe.write_text(s)
 cue=root/'internal/eightsword/spell_cues.go';s=cue.read_text();needle='pixels := p.cachedScene.Pixels[';assert s.count(needle)==1;s=s.replace(needle,'researchVFXScene=p.cachedScene\n '+needle,1);cue.write_text(s)
 driver=a.out/'player-fire-gui-check.go';s=driver.read_text().replace('s["battle_vfx"]','s["spell_cues"]').replace('v["Completed"].(float64)>=1','v["Started"].(float64)>=1').replace('seen["flight"]','seen["cue-early"]').replace('seen["impact"]','seen["cue-late"]').replace('受控滅半','受控複製').replace('player-half-complete','player-clone-complete');driver.write_text(s)
 if a.spell=="freeze":
  s=probe.read_text();assert "spell = 6"in s;s=s.replace("spell = 6","spell = 4",1);probe.write_text(s);s=driver.read_text().replace("複製","凝滯").replace("player-clone-complete","player-freeze-complete");driver.write_text(s)
 meta=json.loads((a.out/'preparation.json').read_text());meta['spell']=6 if a.spell=="clone"else 4;meta['diagnostic_inputs']={str(f.relative_to(root)):sha(f)for f in root.rglob('*')if f.is_file()};meta['changed']=[n for n,h in meta['diagnostic_inputs'].items()if meta['base_inputs'].get(n)!=h];meta['fixture']='Rear caster/learned/selected spell resources only; original cursor to live friendly; no target/selector/count/RNG writes.';(a.out/'preparation.json').write_text(json.dumps(meta,indent=2)+'\n');print('Private clone GUI prepared')
if __name__=='__main__':main()
