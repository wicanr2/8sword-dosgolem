#!/usr/bin/env python3
"""030/032: reproducible AI toolbar glyphs, frozen candidate and scoped audit."""
import argparse, gzip, hashlib, io, json, os, pathlib, shutil
from PIL import Image, ImageDraw, ImageFont, __version__

FONT = '3cffb10242b4b7e6edd439ebf3bd7e392345525e093ea08149e0a0158a1b5151'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def write(p, value): p.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['assets','freeze','gui']);p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--player',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();r=a.project
 assert os.getuid()==1000 and a.player.stat().st_uid==1000 and not a.out.exists() and a.out.parent.is_dir()
 previous=read(r/'preserved/ai-engine-audit-r1.json')
 for n,h in previous['programs'].items(): assert sha(a.player/n)==h,n
 if a.action=='gui':
  a.out.mkdir();source=r/'workplace/probe-20261023/graphics-first/battle-r1/ai-engine-r5/gui-driver-r3/ai-gui-check.go';s=source.read_text();assert 'shot("battle-05-active-unit")' in s
  s=s.replace('shot("battle-05-active-unit")','shot("battle-05-active-unit")\n d.aiToolbar()',1)
  marker='\t\td.battle()\n\t}';assert marker in s;s=s.replace(marker,'\t\td.battle()\n d.receipt("ai-toolbar");d.quit();return\n\t}',1)
  s+='''
func (d *driver) aiToolbar() {
 before:=len(d.status()["input_events"].([]any))
 mode:=func()string{return d.status()["battle_ai"].(map[string]any)["Mode"].(string)}
 checkMode:=func(want string){d.wait("工具列AI已切換",15,func(s map[string]any)bool{return s["battle_ai"].(map[string]any)["Mode"]==want && s["toolbar_menu"]==""})}
 evidence:=[]map[string]any{}
 capture:=func(name,label string){
  atom,err:=xproto.InternAtom(d.c,false,uint16(len("_NET_WM_NAME")),"_NET_WM_NAME").Reply();check(err)
  prop,err:=xproto.GetProperty(d.c,false,d.window,atom.Atom,0,0,1024).Reply();check(err)
  if !strings.Contains(string(prop.Value),label){panic("AI標題不同步："+string(prop.Value))}
  evidence=append(evidence,map[string]any{"name":name,"title":string(prop.Value),"status":d.status()});d.shot(name)
 }
 if mode()!="native"{panic("GUI未從預設原版AI開始")}
 d.toolbarClick(1800,28);d.wait("AI選單已開啟",15,func(s map[string]any)bool{return s["toolbar_menu"]=="ai"});d.shot("ai-toolbar-menu")
 d.press(116);d.press(9);checkMode("native");capture("ai-toolbar-cancel","原版 AI")
 d.toolbarClick(1800,28);d.toolbarClick(1800,140);checkMode("target");capture("ai-toolbar-target","策略 AI")
 d.toolbarClick(1800,28);d.press(111);d.press(36);checkMode("native");capture("ai-toolbar-native","原版 AI")
 d.toolbarClick(1800,28);d.press(116);d.press(36);checkMode("target")
 after:=len(d.status()["input_events"].([]any));if before!=after{panic("AI選單按鍵洩漏到客體")}
 font:=d.status()["font_id"];d.press(76);d.wait("F10字型已切換",15,func(s map[string]any)bool{return s["font_id"]!=font});checkMode("target");capture("ai-toolbar-after-font","策略 AI")
 raw,err:=json.MarshalIndent(map[string]any{"before_guest_inputs":before,"after_guest_inputs":after,"evidence":evidence,"final_mode":mode()},"","  ");check(err);check(os.WriteFile(filepath.Join(d.out,"ai-toolbar-check.json"),append(raw,'\\n'),0644))
}
'''
  (a.out/'ai-toolbar-gui.go').write_text(s);write(a.out/'source.json',dict(source_sha256=sha(source),generated_sha256=sha(a.out/'ai-toolbar-gui.go')));print('XTEST-only toolbar battle helper prepared')
 elif a.action=='assets':
  assert __version__=='11.3.0';base=a.player/'assets-painted-r65'
  for n,h in previous['asset_hashes'].items(): assert sha(base/n)==h,n
  catalog=read_gzip(r/'preserved/catalog.json.gz');obj=catalog['objects'][FONT];fontdata=gzip.decompress((r/'preserved'/obj['path']).read_bytes());assert hashlib.sha256(fontdata).hexdigest()==FONT
  font=ImageFont.truetype(io.BytesIO(fontdata),48,index=3);assert font.getname()==('Noto Sans CJK TC','Black')
  a.out.mkdir()
  for f in base.iterdir(): assert f.is_file() and not f.is_symlink();shutil.copyfile(f,a.out/f.name)
  m=read(base/'poster-toolbar.json');assert m['schema']==1 and len(m['glyphs'])==123
  atlas=Image.open(base/'poster-toolbar-font.png').convert('RGBA')
  for c in '原版策略':
   i=len(m['glyphs']);x,y=i%16*64,i//16*64;box=font.getbbox(c);w,h=box[2]-box[0],box[3]-box[1];ox,oy=x+(64-w)//2,y+(64-h)//2
   ImageDraw.Draw(atlas).text((ox-box[0],oy-box[1]),c,font=font,fill='white');m['glyphs'].append(dict(character=c,ink=[ox,oy,w,h]))
  atlas.save(a.out/'poster-toolbar-font.png');m.update(schema=2,atlas_sha256=sha(a.out/'poster-toolbar-font.png'));write(a.out/'poster-toolbar.json',m)
  print(json.dumps(dict(assets=a.out.name,files=525,atlas_sha256=m['atlas_sha256'],glyphs=127)))
 else:
  core=read(a.player/'runtime.json');assert core['total_inputs']==923
  for n,h in core['files'].items(): assert sha(a.player/'runtime-render-r1/src'/n)==h,n
  a.out.mkdir();digests={}
  for n in sorted(previous['source_inputs']):
   source=r/n;target=a.out/'src'/n;assert source.stat().st_uid==1000;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);digests[n]=sha(source)
  assert len(digests)==181
  (a.out/'build-inputs.sha256').write_text(''.join(f'{h}  /project/{n}\n'for n,h in digests.items()));write(a.out/'runtime.json',core)
  write(a.out/'preparation.json',dict(source_inputs=digests,source_count=181,core_files=923,previous_programs=previous['programs']))
  print('frozen 181 inputs, existing 923-file core')
def read_gzip(p): return json.loads(gzip.decompress(p.read_bytes()))
if __name__=='__main__':main()
