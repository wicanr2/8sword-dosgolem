#!/usr/bin/env python3
"""Private, bounded normal-input VFX GUI fixture; production source remains frozen."""
import argparse,hashlib,json,os,pathlib,shutil,subprocess
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser()
 for n in ['project','source','out']:p.add_argument('--'+n,type=pathlib.Path,required=True)
 a=p.parse_args();assert os.getuid()==1000 and not a.out.exists();a.out.mkdir();shutil.copytree(a.source,a.out/'src');root=a.out/'src';before={str(p.relative_to(root)):sha(p)for p in root.rglob('*')if p.is_file()}
 def replace(name,old,new):
  p=root/name;s=p.read_text();assert s.count(old)==1,(name,old);p.write_text(s.replace(old,new))
 replace('cmd/8sword/main.go','status := g.engine.Status()','status := g.engine.Status()\n status["research_vfx"]=g.engine.ResearchVFXStatus()')
 replace('cmd/8sword/main.go','started := time.Now()\n\tif err := g.engine.AdvanceCycles','if err:=g.engine.ResearchVFXTick();err!=nil{return err}\n started := time.Now()\n\tif err := g.engine.AdvanceCycles')
 replace('cmd/8sword/main.go','g.frame = g.engine.Frame()','g.frame = g.engine.Frame()\n if err:=g.engine.ResearchVFXFrame(g.capture,g.frame);err!=nil{return err}')
 replace('cmd/8sword/main.go','g.draws++','g.draws++\n if err:=g.engine.ResearchVFXDraw(g.capture,g.frame,g.draws);err!=nil{g.recordErr=err}')
 replace('internal/eightsword/battle_vfx.go','visible := p.cachedScene.Pixels[','researchVFXScene=p.cachedScene\n visible := p.cachedScene.Pixels[')
 (root/'internal/eightsword/vfx_gui_probe.go').write_text((a.project/'tools/vfx-gui-probe.go').read_text().removeprefix('//go:build ignore\n'))
 subprocess.run(['python',str(a.project/'tools/prepare-ai-gui.py'),'--project',str(a.project),'--out',str(a.out)],check=True);s=(a.out/'ai-gui-check.go').read_text();s=s.replace('deadline := time.Now().Add(30 * time.Second)','deadline := time.Now().Add(120 * time.Second)');marker='shot("battle-ai-decision")';assert s.count(marker)==1
 extension='''
 seen:=func(s map[string]any)bool{r,_:=s["research_vfx"].(map[string]any);m,_:=r["seen"].(map[string]any);return m["flight"]==true&&m["impact"]==true}
 for n:=0;n<8&&!seen(d.status());n++ {
  r:=d.status()["battle_vfx"].(map[string]any)
  if r["Started"].(float64)>r["Completed"].(float64)+r["Cancelled"].(float64){before:=r["Completed"].(float64);d.wait("目前特殊效果返回",45,func(s map[string]any)bool{return s["battle_vfx"].(map[string]any)["Completed"].(float64)>before})}
  if seen(d.status()){break}
  before:=d.status()["battle_vfx"].(map[string]any)["Completed"].(float64);d.press(65)
  d.wait("固定下一次特殊效果返回",45,func(s map[string]any)bool{return s["battle_vfx"].(map[string]any)["Completed"].(float64)>before||s["presented_scene"]=="battle-result"})
 }
 if !seen(d.status()){panic("VFX flight/impact actual Draw absent")}
 '''
 (a.out/'vfx-gui-check.go').write_text(s.replace(marker,extension+marker));after={str(p.relative_to(root)):sha(p)for p in root.rglob('*')if p.is_file()};(a.out/'preparation.json').write_text(json.dumps(dict(base_inputs=before,diagnostic_inputs=after,changed=[n for n in after if after[n]!=before.get(n)],production=False,fixture='First original enemy round: keep loaded unit 0 as a kind-12 rear caster, force selector 0 up to 8 times; no production branch.'),indent=2)+'\n');print('private GUI source prepared')
if __name__=='__main__':main()
