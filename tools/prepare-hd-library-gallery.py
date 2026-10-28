#!/usr/bin/env python3
"""054: source/HD artwork gallery and README contact sheets, not GUI captures."""
import argparse, base64, collections, hashlib, html, io, json, math, pathlib
from PIL import Image, ImageDraw, ImageFont

LABELS={'ui':'介面','effects':'法術與戰場效果','ending':'結局','map-encounters':'地圖遭遇','battle-backgrounds':'戰場背景','buildings':'建築','hero-and-icons':'主角與器物','troops':'部隊與怪物','special-markers':'太極與標記','map-tiles':'地圖圖塊','opening':'開場','illustrations':'編輯圖集'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--archive',type=pathlib.Path,required=True);p.add_argument('--images',type=pathlib.Path,required=True);a=p.parse_args();root=a.project;arc=a.archive;rows=json.loads((arc/'all-graphics-hd-coverage-r1.json').read_text())['records'];groups=collections.defaultdict(list)
 font=ImageFont.load_default(size=15);small=ImageFont.load_default(size=12)
 def picture(row,box=(560,180)):
  W,H=box;im=Image.new('RGB',box,'#17212a');d=ImageDraw.Draw(im);d.text((8,6),f"{row['source_file']} #{row['record']}",font=font,fill='#f0d68c');d.text((8,29),'ORIGINAL',font=small,fill='#bbc7cc');d.text((W//2+8,29),'HD',font=small,fill='#f0d68c')
  for i,path in enumerate([row['native'],row['hd']['file']]):
   pic=Image.open(root/path).convert('RGBA')
   if i==0:
    factor=6 if row['format']=='VGA8 palette+indices'else 3;pic=pic.resize((pic.width*factor,pic.height*6),Image.Resampling.NEAREST)
   pic.thumbnail((W//2-16,H-55),Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS)
   bg=Image.new('RGBA',pic.size,'#4d5359');bg.alpha_composite(pic);im.paste(bg,(i*W//2+(W//2-pic.width)//2,46+(H-52-pic.height)//2))
  return im
 cards=[];artifacts=[]
 for r in rows:
  groups[r['category']].append(r);thumb=picture(r,(500,180));buf=io.BytesIO();thumb.save(buf,'JPEG',quality=80)
  state='既有正式載入素材' if r['hd']['integrated']else '素材已備，尚未正式接入';rel=str(pathlib.PurePosixPath(r['hd']['file']).relative_to('artwork'));cards.append(f'<article data-category="{r["category"]}" data-key="{r["source_file"].lower()} {r["record"]}" data-integrated="{int(r["hd"]["integrated"])}"><a href="{html.escape(rel)}"><img loading="lazy" alt="{r["source_file"]} {r["record"]} 原版與 HD 素材" src="data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"></a><p>{LABELS[r["category"]]} · {state}</p></article>')
 for category,items in groups.items():
  cols=2 if category in ('illustrations','opening','battle-backgrounds','buildings') else 4;cw=560 if cols==2 else 280;ch=205 if cols==2 else 170;sheet=Image.new('RGB',(cols*cw,50+math.ceil(len(items)/cols)*ch),'#101b23');d=ImageDraw.Draw(sheet);d.text((12,15),f"{category} / {len(items)} source records / ORIGINAL + HD ART",font=font,fill='#f0d68c')
  for i,r in enumerate(items):sheet.paste(picture(r,(cw,ch)),(i%cols*cw,50+i//cols*ch))
  name=f'all-hd-{category}-r1.png';dest=a.images/name;sheet.save(dest,optimize=True);artifacts.append(dict(file='docs/images/'+name,sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),category=category,records=len(items)))
 select=[('LIVE4.AY',0),('LIVE6.AY',0),('END4.AY',2),('END6.AY',0),('END4.AY',3),('END4.AY',4),('END3.AY',2),('MAN27.EGG',0),('X02H.AY',0),('X08.AY',0),('X02.AY',0),('X07.AY',0)];by={(r['source_file'],r['record']):r for r in rows};sheet=Image.new('RGB',(1120,50+6*205),'#101b23');ImageDraw.Draw(sheet).text((12,15),'NEW HD ART / ORIGINAL + PREPARED HD / NOT GUI CAPTURES',font=font,fill='#f0d68c')
 for i,key in enumerate(select):sheet.paste(picture(by[key],(560,205)),(i%2*560,50+i//2*205))
 dest=a.images/'all-graphics-hd-new-art-r1.png';sheet.save(dest,optimize=True);artifacts.append(dict(file='docs/images/'+dest.name,sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),records=len(select)))
 options=''.join(f'<option value="{k}">{v}（{len(groups[k])}）</option>'for k,v in LABELS.items());page='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>神州八劍全圖形 HD 圖庫</title><style>body{margin:24px;background:#101b23;color:#e9e1cc;font:16px system-ui}h1{font-size:26px}a{color:#e9c779}header{position:sticky;top:0;background:#101b23ef;padding:12px 0;z-index:1}input,select{font:inherit;padding:8px;margin:4px;background:#20313d;color:#fff;border:1px solid #52646c}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:14px}article{background:#17212a;border:1px solid #34444d;border-radius:5px;padding:8px}img{width:100%;height:auto}p{font-size:14px;margin:8px}article[hidden]{display:none}</style><h1>神州八劍全圖形 HD 圖庫</h1><p>104 份已辨識圖檔，共 333 筆圖形，包含變體、重複與編輯圖集。左側為原版解碼，右側為 HD 素材；這裡不是遊戲視窗擷取。點圖可開啟本機完整材質。</p><p>既有正式素材與新備素材分開標示。素材完成不等於已接入正式程式。X 圖集含舊版素材，以現有 HD 畫作重組，部分格位與單色對應屬強推論，原始圖和透明資訊均保留。未知 A.A 與六份 RIL 不計入分母。完整原圖及提示均在永久圖庫。</p><header><input id="search" type="search" placeholder="搜尋原檔名，例如 MAN16"><select id="category"><option value="">全部分類</option>OPTIONS</select><select id="state"><option value="">全部接入狀態</option><option value="1">既有正式載入素材</option><option value="0">素材已備，尚未正式接入</option></select><span id="count"></span></header><main>CARDS</main><script>const s=document.querySelector('#search'),c=document.querySelector('#category'),t=document.querySelector('#state'),cards=[...document.querySelectorAll('article')];function filter(){let n=0;for(const a of cards){a.hidden=!(a.dataset.key.includes(s.value.toLowerCase())&&(!c.value||a.dataset.category===c.value)&&(!t.value||a.dataset.integrated===t.value));if(!a.hidden)n++;}document.querySelector('#count').textContent=n+' / 333 筆';}for(const e of[s,c,t])e.addEventListener('input',filter);filter();</script></html>'''.replace('OPTIONS',options).replace('CARDS',''.join(cards))
 (arc/'all-graphics-hd-gallery-r1.html').write_text(page);(a.images/'all-graphics-hd-gallery-r1.json').write_text(json.dumps(dict(schema=1,coverage='artwork/all-graphics-hd-coverage-r1.json',artifacts=artifacts),ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(category_sheets=len(groups),gallery_records=len(cards),comparison=dest.name)))
if __name__=='__main__':main()
