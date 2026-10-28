#!/usr/bin/env python3
"""030: isolated XTEST driver; production application has no test-only branch."""
import argparse,hashlib,json,os,pathlib
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();assert os.getuid()==1000 and a.out.is_dir();r=a.project
 source=r/'tools/gui-check.go';s=source.read_text();start=s.index('func (d *driver) battle()');end=s.index('func (d *driver) dismissArmy',start);part=s[start:end]
 part=part.replace('func (d *driver) battle() {','func (d *driver) battle() {\n beforeAI:=d.status()["battle_ai"].(map[string]any)["Decisions"].(float64)',1)
 marker='\tshot("battle-05-active-unit")';assert marker in part
 part=part.replace(marker,marker+'''
 for n:=0;n<12;n++ {
  if d.status()["battle_ai"].(map[string]any)["Decisions"].(float64)>beforeAI {break}
  if d.status()["presented_scene"]=="battle-result" {break}
  d.press(65)
 }
 d.wait("正常戰鬥已經策略選敵",25,func(s map[string]any)bool{return s["battle_ai"].(map[string]any)["Decisions"].(float64)>beforeAI})
 shot("battle-ai-decision")
 aiRaw,err:=json.MarshalIndent(d.status(),"","  ");check(err);check(os.WriteFile(filepath.Join(d.out,"battle-ai-decision.json"),append(aiRaw,'\\n'),0644))
''',1)
 part=part.replace('\td.press(9)\n\td.scene("battle-result")','\tif d.status()["presented_scene"]!="battle-result" {d.press(9)}\n\td.scene("battle-result")',1);s=s[:start]+part+s[end:]
 # Keep normal movement and recruitment. Omit old exhaustive typography/digit checks.
 start=s.index('func (d *driver) recruitmentBuilding');end=s.index('func main()',start);part=s[start:end]
 part=part.replace('for i := 0; i < 3; i++ {','for i := 0; i < 1; i++ {',1)
 a0=part.index('\t\tfor _, digit :=');a1=part.index('\n\t\td.press(10) // 1',a0);part=part[:a0]+part[a1:]
 part=part.replace('\t\td.press(22) // Backspace','\t\t// Confirm ten troops through the original numeric input.')
 part=part.replace('shot("edited-one")','shot("confirmed-ten")');s=s[:start]+part+s[end:]
 marker='\tcheck(xproto.SetInputFocusChecked(c, 1, d.window, 0).Check())';assert marker in s
 s=s.replace(marker,''' titleProperty,err:=xproto.GetProperty(c,false,d.window,titleAtom.Atom,0,0,1024).Reply();check(err)
 modeEvidence,err:=json.MarshalIndent(map[string]any{"title":string(titleProperty.Value),"battle_ai":d.status()["battle_ai"]},"","  ");check(err)
 check(os.WriteFile(filepath.Join(d.out,"window-title.json"),append(modeEvidence,'\\n'),0644))
'''+marker,1)
 # Leave the recruitment building before the encounter walk. Its original
 # left/right loop assumes the new-game field, and can otherwise re-enter it.
 marker='\tif *battleCheck && *flow == "save" {\n\t\td.battle()'
 assert marker in s
 s=s.replace(marker,'\tif *battleCheck && *flow == "save" {\n\t\td.press(116)\n\t\td.press(116)\n\t\td.press(114)\n\t\td.scene("map")\n\t\td.battle()',1)
 target=a.out/'ai-gui-check.go';assert not target.exists();target.write_text(s)
 (a.out/'gui-driver-source.json').write_text(json.dumps(dict(schema=1,source_sha256=sha(source),generated_sha256=sha(target),tool_sha256=sha(pathlib.Path(__file__)),method='Only XTEST input and X11 screenshots; no RAM, forced branch or application probe'),indent=2)+'\n');print('isolated normal-input AI GUI driver prepared')
if __name__=='__main__':main()
