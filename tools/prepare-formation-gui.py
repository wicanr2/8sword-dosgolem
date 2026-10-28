#!/usr/bin/env python3
"""030: isolated normal-input rules toolbar, battle and save driver."""
import argparse, hashlib, json, os, pathlib, subprocess

def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();assert os.getuid()==1000 and a.out.is_dir()
 subprocess.run(['python',str(a.project/'tools/prepare-ai-gui.py'),'--project',str(a.project),'--out',str(a.out)],check=True)
 s=(a.out/'ai-gui-check.go').read_text()
 s=s.replace('\tflag.Parse()', '\texpectRule := flag.String("expect-rules", "native", "expected auto-restored rules")\n\trewriteNative := flag.Bool("rewrite-native", false, "select native and save again")\n\tflag.Parse()',1)
 s=s.replace('\td.console("display-config")','\td.console("display-config")\n\tif d.rules()["Mode"] != *expectRule {panic("startup rules mismatch")}\n\td.ruleShot("rules-startup")',1)
 s=s.replace('\td.shot("05-map")','\td.shot("05-map")\n\tif *flow == "save" {d.rulesBeforeBattle()}',1)
 s=s.replace('\tshot("battle-05-active-unit")','\tshot("battle-05-active-unit")\n\td.rulesDuringBattle()\n\td.press(114) // Manual p9: move cursor to opposing front unit.\n\td.press(36) // Original attack, rather than resting every turn.\n\td.ruleShot("rules-player-attack")',1)
 s=s.replace('\t\td.battle()','\t\td.battle()\n\t\td.rulesAfterBattle()',1)
 start=s.index('\tif *flow == "reload" {\n\t\td.press(36)');end=s.index('\n\td.press(116)',start);part=s[start:end]
 part=part.replace('\t\td.shot("04-loaded-map")','\t\td.shot("04-loaded-map")\n\t\tif d.rules()["Mode"] != *expectRule {panic("loaded rules mismatch")}\n\t\td.ruleShot("rules-restored-map")\n\t\tif *rewriteNative {d.selectRules("native")}',1)
 part=part.replace('\t\td.receipt(*flow)','\t\tif *rewriteNative {d.saveRuleProgress(*saves)}\n\t\td.receipt(*flow)',1);s=s[:start]+part+s[end:]
 s+=r'''
func (d *driver) rules() map[string]any {return d.status()["battle_rules"].(map[string]any)}
func (d *driver) ruleShot(name string) {
 d.shot(name)
 atom,err:=xproto.InternAtom(d.c,false,12,"_NET_WM_NAME").Reply();check(err)
 prop,err:=xproto.GetProperty(d.c,false,d.window,atom.Atom,0,0,1024).Reply();check(err)
 raw,err:=json.MarshalIndent(map[string]any{"title":string(prop.Value),"status":d.status()},"","  ");check(err)
 check(os.WriteFile(filepath.Join(d.out,name+".json"),append(raw,'\n'),0644))
}
func (d *driver) selectRules(mode string) {
 d.toolbarClick(2400,28)
 d.wait("規則選單",15,func(s map[string]any)bool{return s["toolbar_menu"]=="rules"})
 d.ruleShot("rules-menu-"+mode)
 y:=88;if mode=="formation" {y=140}
 d.toolbarClick(2400,y)
 d.wait("規則選擇",15,func(s map[string]any)bool{return s["toolbar_menu"]=="" && s["battle_rules"].(map[string]any)["Mode"]==mode})
}
func (d *driver) rulesBeforeBattle() {
 before:=len(d.status()["input_events"].([]any))
 d.toolbarClick(2400,28);d.press(116);d.press(9)
 if d.rules()["Mode"]!="native" || d.status()["toolbar_menu"]!="" {panic("rules cancellation changed mode")}
 d.selectRules("formation")
 if len(d.status()["input_events"].([]any))!=before {panic("rules toolbar leaked DOS input")}
 d.ruleShot("rules-before-battle")
}
func (d *driver) rulesDuringBattle() {
 if d.rules()["Mode"]!="formation" || d.rules()["Active"]!=true {panic("normal battle did not lock formation rules")}
 before:=len(d.status()["input_events"].([]any))
 d.toolbarClick(2400,28)
 if d.status()["toolbar_menu"]!="" || d.rules()["Mode"]!="formation" {panic("battle rules unlocked")}
 d.toolbarClick(1800,28);d.press(111);d.press(36)
 d.wait("戰鬥中獨立切換原版AI",15,func(s map[string]any)bool{return s["battle_ai"].(map[string]any)["Mode"]=="native"})
 d.toolbarClick(1800,28);d.press(116);d.press(36)
 d.wait("戰鬥中恢復策略AI",15,func(s map[string]any)bool{return s["battle_ai"].(map[string]any)["Mode"]=="target"})
 if len(d.status()["input_events"].([]any))!=before {panic("locked rules or AI toolbar leaked DOS input")}
 d.ruleShot("rules-battle-locked")
}
func (d *driver) rulesAfterBattle() {
 d.wait("正常戰鬥返回解除規則鎖定",25,func(s map[string]any)bool{r:=s["battle_rules"].(map[string]any);return r["Active"]==false && r["Started"].(float64)>=1 && r["Finished"].(float64)>=1 && r["Calls"].(float64)>=1})
 sides:=map[string]bool{};for _,v:=range d.rules()["Recent"].([]any){sides[v.(map[string]any)["Side"].(string)]=true}
 if !sides["player"] || !sides["enemy"] {panic("normal battle did not call both damage directions")}
 d.ruleShot("rules-after-battle")
}
func (d *driver) saveRuleProgress(saves string) {
 d.press(73);d.scene("system-menu");before:=d.status()["steps"].(float64);d.press(36);d.confirmation(before);d.press(36);d.scene("map")
 d.wait("原版F7寫入原版規則標記",20,func(s map[string]any)bool{return s["battle_rules"].(map[string]any)["Markers"].(float64)>0})
 raw,err:=os.ReadFile(filepath.Join(saves,"gamedata.ay.rules.json"));check(err);var m map[string]any;check(json.Unmarshal(raw,&m));if m["rules"]!="native" {panic("saved native rules mismatch")}
 d.ruleShot("rules-native-saved")
}
'''
 target=a.out/'formation-gui-check.go';target.write_text(s)
 (a.out/'formation-driver-source.json').write_text(json.dumps(dict(schema=1,generated_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),tool_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),method='XTEST input and real X11 window only; no RAM or forced game branches'),indent=2)+'\n')
 print('formation normal-input GUI driver prepared')
if __name__=='__main__':main()
