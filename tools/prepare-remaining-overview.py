"""Publish small crops of verified actual Engine/GUI frames; masters stay preserved."""
import argparse,hashlib,json,pathlib
from PIL import Image,ImageDraw,ImageFont
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--font',type=pathlib.Path,required=True);a=p.parse_args();r=a.project;q=r/'workplace/probe-20261023/graphics-first/battle-r1/player-spells-r1/remaining-r1';assert read(q/'presentation-audit-r2.json')['status']=='passed-independent-remaining-presentation';out=r/'docs/images';target=out/'remaining-spell-cues-r1.png';assert not target.exists();names=['造橋術','煉金術','召兵術','跳躍術','停時術','鳥瞰術','涉水術','傳送術','凝滯術','複製術'];font=ImageFont.truetype(str(a.font),26);small=ImageFont.truetype(str(a.font),17);title=ImageFont.truetype(str(a.font),34);sheet=Image.new('RGB',(1840,790),(12,32,30));draw=ImageDraw.Draw(sheet);draw.text((24,12),'神州八劍　十術 HD 光效',(255,236,181),font=title);draw.text((24,57),'原版判定與消耗維持；學習／次數為受控條件。以下為實際畫面近景。',(208,216,205),font=small);sources=[]
 for kind,name in enumerate(names):
  if kind<8:folder=q/'normal-r2'/str(kind);f=folder/'frame.png';m=read(folder/'receipt.json');anchor=m['cue']['Anchor'];method='F4 選單／引擎畫面'
  else:folder=q/('gui-freeze-r1'if kind==8 else'gui-r1')/'vfx-draw';f=folder/'cue-late-central.png';m=read(folder/'cue-late.json');anchor=m['vfx']['Anchor'];method='戰場／實際視窗'
  cx,cy=anchor[0]*3,anchor[1]*6;box=(max(0,min(1320,cx-300)),max(0,min(720,cy-240)));crop=(box[0],box[1],box[0]+600,box[1]+480);im=Image.open(f).convert('RGB').crop(crop).resize((352,282),Image.Resampling.LANCZOS);x=16+(kind%5)*366;y=98+(kind//5)*342;sheet.paste(im,(x,y));draw.text((x,y+286),name,(255,236,181),font=font);draw.text((x+118,y+294),method,(190,204,195),font=small);sources.append(dict(kind=kind,name=name,source=str(f.relative_to(r)),source_sha256=sha(f),crop=list(crop),method=method,sample=m['sample'],step=m['step']))
 sheet.save(target);previews=[]
 for name,folder in [('freeze','gui-freeze-r1'),('clone','gui-r1')]:
  f=q/folder/'vfx-draw/cue-late-presented.png';dest=out/('player-'+name+'-hd-r1.png');assert not dest.exists();Image.open(f).convert('RGB').resize((1600,687),Image.Resampling.LANCZOS).save(dest);previews.append(dict(file=dest.name,sha256=sha(dest),source=str(f.relative_to(r)),source_sha256=sha(f)))
 meta=dict(schema=1,status='verified-ten-cue-overview',audit_sha256=sha(q/'presentation-audit-r2.json'),font_sha256=sha(a.font),sources=sources,overview_sha256=sha(target),previews=previews,limits=['Cropped/resized previews; full frames, masks and renderer sources preserved outside workplace.','Resources and learning fixtures; not natural learning or new save/load.']);(out/'remaining-spell-cues-r1.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');print('Saved verified ten-cue overview and two actual-window previews')
if __name__=='__main__':main()
