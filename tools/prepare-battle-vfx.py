#!/usr/bin/env python3
"""030 DRAFT: independently audit observed calls; prepare a disposable Go animation page."""
import argparse,base64,hashlib,json,os,pathlib
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['audit','inputs','page'])
 for n in ['project','study','out']:p.add_argument('--'+n,type=pathlib.Path,required=True)
 p.add_argument('--render',default='render-r1')
 a=p.parse_args();r=a.project;q=a.study;assert os.getuid()==q.stat().st_uid==1000 and not a.out.exists();coverage=read(r/'artwork/all-graphics-hd-coverage-r1.json')['records'];aliases={}
 for v in coverage:
  rec=dict(file=v['source_file'],record=v['record'])
  for key in ['record_sha256','native_fingerprint']:
   if v.get(key):aliases[v[key]]=rec
 # The original primary index excludes mirrored runtime aliases; validated production manifests retain them.
 for path in (r/'workplace/player/assets-painted-r68').glob('*.json'):
  d=read(path)
  if not isinstance(d,dict):continue
  source=d.get('source_file')
  if path.name.startswith('battle-friendly-man21'):source='MAN21.EGG'
  if not source:continue
  for frame in d.get('frames',[]):
   if not isinstance(frame,dict)or 'record'not in frame:continue
   for key in ['native_sha256','record_sha256']:
    values=frame.get(key,[]);values=values if isinstance(values,list)else[values]
    for h in values:
     if isinstance(h,str)and len(h)==64:aliases.setdefault(h,dict(file=source,record=frame['record']))
 if a.action=='audit':
  summary=read(q/'calls-r1/summary.json');rows=[];bitmaps=0
  for case in summary['results']:
   name=case['case'];source=r/'workplace/probe-20261023/graphics-first/battle-r1'/('ai-policy-extra-r2'if name.startswith('special5')else'ai-policy-r1')/name/'baseline';old=read(source/'trace.json');directory=q/'calls-r1'/name
   assert sha(source/'trace.json')==case['source_trace_sha256']and case['start_step']==old['DecisionStep']and case['end_step']==old['EndStep']
   assert sha(directory/'control/final.state')==sha(directory/'observed/final.state')==sha(source/'final.state')==old['StateSHA256'];assert not case['observer_guest_writes']
   events=[]
   for ev in case['events']:
    if 'native_sha256'not in ev:assert ev['effect_entry']==0x36c6;continue
    rec=aliases.get(ev['source_sha256'],aliases.get(ev['native_sha256']));assert rec,(name,ev['source_sha256']);assert case['start_step']<=ev['entry_step']<ev['return_step']<=case['end_step']and ev['runtime_segment']==0x14d2 and ev['xywh'][2:]==[88,50];assert ev['destination']==0xa000
    if ev.get('png'):assert(directory/'observed'/ev['png']).is_file()
    events.append(dict(ev,**rec));bitmaps+=1
   pon=[v for v in events if v['file']=='PON.EGG'];assert len(pon)==12 and [v['record']for v in pon]==[1,2,3,0]*3 and all(v['entry']==0x4f2 and v['planes']==6 for v in pon)
   rows.append(dict(case=name,start=case['start_step'],end=case['end_step'],final_sha256=sha(source/'final.state'),events=events,pon_calls=12))
  result=dict(schema=1,status='passed-scoped-battle-vfx-observation',controlled_cases=3,bitmap_calls=bitmaps,pon_calls=36,full_states_equal=True,reference_states_equal=True,cases=rows,limits=['Enemy controlled special 0/2/5 only; names and player spells remain unknown.','PON rendering was already complete; this establishes caller context, not new spell identities.','Fixture troop kind changes do not reload the old source sprite; observed graphic is MAN17, not evidence of kind-to-art mapping.'])
 elif a.action=='inputs':
  audit=read(q/'audit-r1.json');assert audit['status']=='passed-scoped-battle-vfx-observation';case=audit['cases'][0]
  def texture(name,record=0):
   v=next(v for v in coverage if v['source_file']==name and v['record']==record);p=r/v['hd']['file'];assert sha(p)==v['hd']['sha256'];return str(p)
  result=dict(Background=texture('GRO02.EG'),Militia=texture('MAN01.EGG'),Dwarf=texture('MAN21.EGG'),Source=[texture('MAN17.EGG',i)for i in range(4)],PON=[texture('PON.EGG',i)for i in range(4)],Start=case['start'],End=case['end'],Events=case['events'])
 else:
  rendered=q/a.render;d=read(rendered/'frames.json');assert len(d['frames'])==61 and d['renderer'].startswith('native Go');images={}
  def embed(key,path):images[key]='data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()
  for path in rendered.glob('*.png'):embed(path.name,path)
  original=q/'calls-r1/special0-choice/observed'
  for path in original.glob('*.png'):embed('native/'+path.name,path)
  payload=dict(d,images=images);html=PAGE.replace('__PAYLOAD__',json.dumps(payload,separators=(',',':')));a.out.write_text(html);print('self-contained animation page',a.out.stat().st_size);return
 a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(a.action,'passed')
PAGE='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>神州八劍：特殊攻擊動畫原型</title><style>*{box-sizing:border-box}body{margin:0;background:#101d18;color:#f1e4bf;font:16px/1.65 "Noto Sans CJK TC",sans-serif}main{max-width:1200px;padding:20px;margin:auto}h1{font-size:26px;margin:4px 0}p{margin:9px 0}.note{background:#24372b;border-left:3px solid #c8a156;padding:10px 14px}.muted{color:#c5bca0;font-size:14px}.controls{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin:16px 0}button{font:inherit;padding:9px 18px;color:#ffe6a3;background:#304731;border:1px solid #c3a35f;cursor:pointer}input[type=range]{flex:1;min-width:180px;accent-color:#d2a75b}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}article{background:#182d23;border:1px solid #826e45;padding:10px}h2{font-size:18px;margin:0 0 8px}canvas{display:block;width:100%;height:auto;background:#000}table{width:100%;border-collapse:collapse;margin-top:15px}th,td{padding:8px;border-bottom:1px solid #40543e;text-align:left}@media(max-width:650px){main{padding:12px}.grid{grid-template-columns:1fr}h1{font-size:22px}}</style><main><div class="muted">動畫樣式原型，尚未接入正式遊戲</div><h1>特殊攻擊：保留金紅火花，補清楚來源與落點</h1><p>三組原版特殊攻擊都呼叫同一套火花，每次「1、2、3、0」重複三輪。這裡先比較共用效果，不替未知法術命名。</p><div class="note">原版欄為受控客體截圖。HD各欄以既有定稿素材重建示意場景，並非同狀態的正式引擎畫面。時軸保留原版事件順序，三秒播放只供比較，不代表原版速度。沒有改傷害、資源或遊戲規則。</div><div class="controls"><button id="play">播放</button><button id="launch">看飛行</button><button id="impact">看命中光效</button><button id="clear">看清除</button><input id="time" type="range" min="0" max="60" value="24" aria-label="動畫影格"><span id="phase"></span></div><div class="grid"><article><h2>原版受控截圖</h2><canvas id="native" width="960" height="600"></canvas><p class="muted">原版圖片呼叫返回點，低解析度保留。</p></article><article><h2>現有 HD 素材示意</h2><canvas id="base" width="960" height="600"></canvas><p class="muted">既有角色、戰場與四張火花，照原順序累積。</p></article><article><h2>A：命中符光</h2><canvas id="a" width="960" height="600"></canvas><p class="muted">保留火花，落點加金色符圈與朱紅餘燼，畫面較收斂。</p></article><article><h2>B：飛焰＋命中符光</h2><canvas id="b" width="960" height="600"></canvas><p class="muted">同A，另加金紅飛焰，較容易看清從哪一隊發出。</p></article></div><table><tr><th>來源</th><th>已證實</th><th>仍未知</th></tr><tr><td>敵方特殊0／2／5</td><td>36次火花呼叫、三組完整返回狀態相同</td><td>玩家法術名稱、資源與完整施法目錄</td></tr></table><p class="muted">所有效果像素與位置由Go預先產生。網頁只播放已算好的透明材質；正式接入仍須事件生命週期與無副作用驗收。符圈是視覺設計，不表示新增陣法規則。</p></main><script id="payload" type="application/json">__PAYLOAD__</script><script>
const data=JSON.parse(document.getElementById('payload').textContent),images={},contexts={};let current=24,playing=false,anchor=0;
for(const id of ['native','base','a','b'])contexts[id]=document.getElementById(id).getContext('2d');
const ready=Promise.all(Object.entries(data.images).map(([key,src])=>new Promise((resolve,reject)=>{const i=new Image();i.onload=()=>{images[key]=i;resolve()};i.onerror=()=>reject(Error(key));i.src=src})));
function hd(ctx,f,overlay,box){ctx.clearRect(0,0,960,600);ctx.drawImage(images['base.png'],0,0);ctx.drawImage(images['source-'+f.SourcePose+'.png'],684,225);for(const id of f.PON)ctx.drawImage(images['pon-'+id+'.png'],276,300);if(overlay)ctx.drawImage(images[overlay],box[0],box[1]);}
function setFrame(index){current=Math.max(0,Math.min(60,index));const f=data.frames[current];contexts.native.imageSmoothingEnabled=false;contexts.native.drawImage(images['native/'+f.Native],0,0,960,600);hd(contexts.base,f);hd(contexts.a,f,f.A,f.ABox);hd(contexts.b,f,f.B,f.BBox);document.getElementById('time').value=current;document.getElementById('phase').textContent=current+' / 60';document.body.dataset.frame=current;}
function stop(){playing=false;document.getElementById('play').textContent='播放';}
function tick(now){if(!playing)return;setFrame(Math.min(60,Math.floor((now-anchor)/50)));if(current>=60){stop();return;}requestAnimationFrame(tick);}
document.getElementById('play').onclick=()=>{if(playing){stop();return;}playing=true;anchor=performance.now();document.getElementById('play').textContent='暫停';requestAnimationFrame(tick);};
document.getElementById('time').oninput=e=>{stop();setFrame(Number(e.target.value));};
for(const [id,frame]of [['launch',12],['impact',24],['clear',60]])document.getElementById(id).onclick=()=>{stop();setFrame(frame);};
ready.then(()=>{setFrame(24);document.body.dataset.ready='true';}).catch(e=>{document.body.dataset.error=e.message;});window.vfx={ready,setFrame,stop};
</script></html>'''.replace('\n+','\n')
if __name__=='__main__':main()
