#!/usr/bin/env python3
"""054: publish current integration labels without rewriting the frozen art ledger."""
import argparse,collections,hashlib,json,os,pathlib,re
from PIL import Image,__version__
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--artwork',type=pathlib.Path,required=True);p.add_argument('--images',type=pathlib.Path,required=True);p.add_argument('--audit',type=pathlib.Path,required=True);a=p.parse_args();r=a.project;art=a.artwork
 assert os.getuid()==1000 and __version__=='11.3.0'
 report=read(a.audit);assert report['status']=='PASS-scoped-054-completion'
 manifest=read(art/'completion-r65.json');new={(v['source_file'],v['record']):v for v in manifest['records']}
 coverage=read(art/'all-graphics-hd-coverage-r1.json');records=[];counts=collections.Counter()
 for v in coverage['records']:
  key=(v['source_file'],v['record']);added=new.get(key)
  if v['hd']['integrated']:status='existing-player'
  elif added['route']!='archive':status='added-player'
  elif v['source_file']in ['TIT6V.AY','TIT6X.AY']:status='existing-intro'
  else:status='packaged-archive'
  counts[status]+=1
  records.append(dict(source_file=key[0],record=key[1],source_sha256=v['record_sha256'],category=v['category'],status=status,hd_file=v['hd']['file'],hd_sha256=v['hd']['sha256'],runtime_file=added['image']if added else None))
 assert dict(counts)=={'existing-player':271,'packaged-archive':43,'added-player':17,'existing-intro':2}or counts==collections.Counter({'existing-player':271,'packaged-archive':43,'added-player':17,'existing-intro':2})
 labels={'existing-player':'正式來源已對應','added-player':'本輪新增正式對應','existing-intro':'既有開場專用路由','packaged-archive':'素材已入包，非現行顯示路徑'}
 lookup={f"{v['source_file'].lower()} {v['record']}":v for v in records}
 html=(art/'all-graphics-hd-gallery-r1.html').read_text();seen=[]
 def update(match):
  card=match.group();key=re.search(r'data-key="([^"]+)"',card).group(1);v=lookup[key];seen.append(key);state='0'if v['status']=='packaged-archive'else'1'
  card=re.sub(r'data-integrated="[01]"',f'data-integrated="{state}"',card)
  return re.sub(r' · (?:既有正式載入素材|素材已備，尚未正式接入)</p>',f" · {labels[v['status']]}</p>",card)
 html=re.sub(r'<article\b.*?</article>',update,html);assert len(seen)==333
 html=html.replace('既有正式素材與新備素材分開標示。素材完成不等於已接入正式程式。','r65已登錄290筆彩色來源對應；43筆單色與編輯圖集已入包，不新增顯示模式。新增17筆採代表抽驗，兩筆前導／故事原已有專用路由。這不是333筆自然使用的聲明。')
 html=html.replace('<option value="1">既有正式載入素材</option>','<option value="1">正式來源已對應（290）</option>').replace('<option value="0">素材已備，尚未正式接入</option>','<option value="0">非現行顯示路徑，已入包（43）</option>')
 gallery=art/'all-graphics-hd-gallery-r2.html';index=art/'graphics-integration-r65.json';image=a.images/'completion-runtime-lishu-r65.png';assert not gallery.exists()and not index.exists()and not image.exists()
 gallery.write_text(html)
 gui=r/'workplace/probe-20261023/graphics-first/all-graphics-integration-r1/gui-r3/menus/11-final-map.png'
 im=Image.open(gui).convert('RGB');im.thumbnail((1280,900),Image.Resampling.LANCZOS);im.save(image)
 result=dict(schema=1,assets='assets-painted-r65',files=525,counts=dict(counts),player_source_correspondences=290,packaged_noncurrent_records=43,records=records,frozen_coverage_sha256=sha(art/'all-graphics-hd-coverage-r1.json'),audit_sha256=sha(a.audit),gallery_sha256=sha(gallery),gui_source_sha256=sha(gui),gui_preview_sha256=sha(image),limits=report['limits'])
 index.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(status='published',counts=dict(counts))))
if __name__=='__main__':main()
