#!/usr/bin/env python3
"""030 DRAFT: source-backed roster, offline formation cases and review page."""
import argparse,configparser,hashlib,json,os,pathlib,shutil
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def loss(amount,hp,count):
 encoded=(amount//hp+1)&65535
 return 0 if encoded<=1 else count if encoded>=count else encoded-1
def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','page','toolbar','audit']);p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--openkb',type=pathlib.Path);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();r=a.project;q=a.out;assert os.getuid()==1000
 if a.action=='prepare':
  assert a.openkb and not q.exists() and q.parent.is_dir() and q.parent.stat().st_uid==1000;q.mkdir();(q/'inputs').mkdir();(q/'src').mkdir()
  sources={}
  for n in ['data/free/troops.ini','src/bounty.h','src/play.c','src/game.c']:
   f=a.openkb/n;target=q/'inputs/openkb'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target);sources[n]=sha(f)
  config=configparser.ConfigParser();config.read(a.openkb/'data/free/troops.ini');assert len(config.sections())==25
  troops=[dict(id=i,**dict(config[f'troop{i}']))for i in range(25)]
  pam=r/'workplace/intake-20261023/sources/game/8sword/PAM.AY';raw=pam.read_bytes();assert sha(pam)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
  native=[]
  for kind in range(1,26):
   off=0x21472+kind*10;b=raw[off:off+10];native.append(dict(kind=kind,name=b.split(b'\0')[0].decode('big5'),file_offset=hex(off),bytes=b.hex(),level='static-string-table; runtime linkage not newly proved'))
  assert native[0]['name']=='民兵' and native[2]['name']=='弓箭手' and native[14]['name']=='骷髏' and native[20]['name']=='矮人'
  catalog=dict(openkb_commit='f67208e1aeedaefd737a860f66c9635305ad9376',openkb_sources=sources,openkb_troops=troops,original_pam_sha256=sha(pam),native_names=native,consumers=[dict(file='src/play.c',lines=[1215,1237],fact='reset_turn clears injury for REGEN; count is not restored here',level='source-proven'),dict(file='src/play.c',lines=[1470,1614],fact='deal_damage consumes MAGIC/IMMUNE, ABSORB and LEECH; leech has max_count cap',level='source-proven'),dict(file='src/game.c',lines=[4083,4097],fact='damage_army filters undead and magic immunity before external damage',level='source-proven')],limits=['New IDs and archive/save capacity remain unknown.','Matching names do not prove matching rules.','Formation is an original proposal, not an openKB ability.'])
  write(q/'catalog.json',catalog)
  batch=r/'workplace/probe-20261023/graphics-first/battle-r1/ai-policy-r1';inputs=[];reference=[]
  for name in ['normal-locked','normal-choice','normal-rear-only','front-ranged-mixed','rear-ranged-mixed']:
   path=batch/name/'baseline/trace.json';d=read(path);v=d['View'];target=v['OriginalSlot'];u=v['Friendly'][v['FriendlySlots'][target]];source=v['Enemy'][v['EnemySlots'][v['SourceSlot']]];amount=((v['Factors'][source['Kind']*2]*source['Count'])&65535)//((v['Divisor']+5)&65535);hp=v['Factors'][u['Kind']*2+1]
   unit=v['FriendlySlots'][target];actual=u['Count']-d['AfterUnits'][unit*2+1];assert loss(amount,hp,u['Count'])==actual
   item=dict(Name=name,Label='既有原版：'+name,Route=v['Route'],Side='player',Provenance='accepted original trace; no new game execution',Target=target,Slots=[v['Friendly'][i]for i in v['FriendlySlots']],Amount=amount,HP=hp)
   inputs.append(item);shutil.copyfile(path,q/'inputs'/(name+'.json'));reference.append(dict(case=name,trace_sha256=sha(path),observed_loss=actual))
  template=inputs[0]
  labels={'alone':'無前排同袍','front-ally':'前排有同袍','dead-ally':'同袍已全滅','rear-ally':'只有後排同袍','two-allies':'兩位同袍，不疊加','other-kind':'受擊者不是民兵','rear-target':'民兵在後排','ranged':'承受遠程攻擊','special':'特殊效果固定減5人','enemy':'敵方民兵也結陣','empty':'受擊隊已全滅','threshold':'整數門檻：25傷害','small':'原本未達減員門檻','two-person':'兩人民兵的全滅門檻'}
  for name,label in labels.items():
   v=json.loads(json.dumps(template));v.update(Name='proposal-'+name,Label='合成：'+label,Provenance='synthetic typed input; no guest mutation');v['Slots']=[dict(Kind=1,Count=31),dict(Kind=0,Count=0),dict(Kind=0,Count=0),dict(Kind=21,Count=69),dict(Kind=0,Count=0),dict(Kind=0,Count=0)]
   if name not in ['alone','dead-ally','rear-ally']:v['Slots'][1]=dict(Kind=21,Count=69)
   if name=='dead-ally':v['Slots'][1]=dict(Kind=21,Count=0)
   if name=='two-allies':v['Slots'][2]=dict(Kind=2,Count=10)
   if name=='other-kind':v['Slots'][0]['Kind']=2
   if name=='rear-target':v['Target']=3;v['Slots'][3]=dict(Kind=1,Count=31)
   if name=='ranged':v['Route']='ranged'
   if name=='special':v['Route']='special';v['Amount']=5
   if name=='enemy':v['Side']='enemy'
   if name=='empty':v['Slots'][0]['Count']=0
   if name in ['threshold','two-person']:v['Amount']=25
   if name=='two-person':v['Slots'][0]['Count']=2
   if name=='small':v['Amount']=24
   inputs.append(v)
  write(q/'formation-inputs.json',inputs);write(q/'references.json',reference)
  for n in ['research-formation.go','research-formation_test.go']:
   s=(r/'tools'/n).read_text().replace('//go:build ignore\n','',1);(q/'src'/n).write_text(s)
  (q/'src/go.mod').write_text('module formation-prototype\n\ngo 1.24.0\n');print('prepared 25+25 names, 5 original controls and 14 synthetic cases')
 elif a.action in ['page','toolbar']:
  results=read(q/'formation-results.json');catalog=read(q/'catalog.json');data=json.dumps(results,ensure_ascii=False).replace('<','\\u003c');names=json.dumps({v['kind']:v['name']for v in catalog['native_names']},ensure_ascii=False)
  html='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>神州八劍・民兵結陣原型</title><style>
body{background:#10291e;color:#eee2ba;font:18px/1.65 "Noto Sans CJK TC",sans-serif;max-width:1000px;margin:32px auto;padding:20px}h1,h2{color:#ebc572}h1{font-size:30px}button,select{background:#193c2a;color:#fff0ba;border:1px solid #bd9450;border-radius:5px;padding:12px;font:inherit;margin:6px}button[aria-pressed=true]{background:#73402c}select{max-width:100%;width:100%}.box{border:1px solid #79643b;padding:22px;margin:20px 0;border-radius:6px}.cells{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.cell{padding:14px;border:1px solid #817c50}.target{outline:3px solid #e5bd59}.dead{opacity:.5}.big{font-size:42px;color:#f4cb74}small{color:#c6c7a6}.values{display:grid;grid-template-columns:1fr 1fr;gap:20px}table{width:100%;border-collapse:collapse}td,th{padding:10px;border-bottom:1px solid #506048;text-align:left}@media(max-width:650px){.cells,.values{grid-template-columns:1fr}body{margin:0}}
</style><h1>民兵「結陣」計算原型</h1><p>待決設計，尚未接入遊戲。這是陣位與兵損試算，不是遊戲截圖，也未證明玩家可用此頁移位。</p><div class="box"><strong>候選規則</strong><p>民兵在前排，且同前排另有一隊活躍同袍時，自身普通／遠程傷害降低。效果不疊加，敵我相同；後排、其他兵種與特殊效果保持原有結算。</p><label for="scenario">比較局面</label><select id="scenario"></select><p>減少傷害量：</p><div id="rates"></div></div><div class="box"><p id="source"></p><p>前排陣位0至2</p><div id="front" class="cells"></div><p>後排陣位3至5</p><div id="rear" class="cells"></div><small>陣位示意，不代表畫面座標或自由走格。</small></div><div class="box values"><div>原版算式減員<div class="big" id="before"></div></div><div>候選結陣減員<div class="big" id="after"></div></div><p id="detail"></p></div><p>傷害先縮減、向下取整，再經原版減員編碼。減傷20%不等於兵損一定少20%，低兵數時差異可能很大。</p><details><summary>已核對的參考差異</summary><p>openKB的再生只清除injury，不補回陣亡人數。本作已有骷髏、飛龍與矮人，名稱相近不等於同一規則；新兵種ID、招募、存讀與玩家攻擊掛點仍待驗證。</p><p>原版五份固定trace只作算式控制；其餘局面全為合成資料。原版與策略AI、正式素材及存檔皆未修改。</p></details><script>
const results=DATA,names=NAMES,scenarios=[...new Map(results.map(r=>[r.Input.Name,r.Input])).values()];let rate=20;
const sel=document.querySelector('#scenario');scenarios.forEach(v=>{const o=document.createElement('option');o.value=v.Name;o.textContent=v.Label;sel.append(o)});sel.value='proposal-front-ally';
for(const n of [0,10,20,30]){const b=document.createElement('button');b.textContent=n+'%'+(n===20?'（建議試作）':'');b.onclick=()=>{rate=n;render()};b.dataset.rate=n;document.querySelector('#rates').append(b)}
function render(){const row=results.find(r=>r.Input.Name===sel.value&&r.Rate===rate),base=results.find(r=>r.Input.Name===sel.value&&r.Rate===0),v=row.Input;document.querySelector('#source').textContent=v.Label+'；'+(v.Side==='player'?'玩家受擊':'敵軍受擊');for(const [id,start]of [['front',0],['rear',3]]){const el=document.querySelector('#'+id);el.replaceChildren();for(let i=start;i<start+3;i++){const u=v.Slots[i],box=document.createElement('div');box.className='cell'+(i===v.Target?' target':'')+(u.Count===0?' dead':'');box.textContent='陣位'+i+'｜'+(u.Count?(names[u.Kind]||'類型'+u.Kind)+' '+u.Count+'人':'空隊');el.append(box)}}document.querySelector('#before').textContent=base.Loss+'人';document.querySelector('#after').textContent=row.Loss+'人';document.querySelector('#detail').textContent=(row.Eligible?'符合結陣條件':'不符合結陣條件')+'。傷害量 '+base.Amount+' → '+row.Amount+'；餘兵 '+base.Remaining+' → '+row.Remaining+'。';document.querySelectorAll('[data-rate]').forEach(b=>b.setAttribute('aria-pressed',Number(b.dataset.rate)===rate))}sel.onchange=render;render();
</script></html>'''.replace('DATA',data).replace('NAMES',names)
  filename='formation-prototype-r1.html'
  if a.action=='toolbar':
   filename='formation-toolbar-prototype-r1.html'
   html=html.replace('待決設計，尚未接入遊戲。','20%結陣已批准試作，規則工具列仍為操作原型，尚未接入遊戲。',1)
   html=html.replace('<h1>','<div class="box"><div style="display:flex;gap:18px;flex-wrap:wrap"><label>AI<select id="ai"><option value="native">原版 AI</option><option value="target">策略 AI</option></select></label><label>規則<select id="rules"><option value="native">原版規則</option><option value="formation">結陣試作</option></select></label><button id="battle">開始本場試算</button></div><small id="rule-state">戰鬥外可切規則；AI與規則獨立。</small></div><h1>',1)
   html=html.replace('<p>減少傷害量：</p><div id="rates"></div>','<p>結陣試作固定20%減傷；原版規則維持原算式。</p><div id="rates" hidden></div>')
   html=html.replace('r.Input.Name===sel.value&&r.Rate===rate','r.Input.Name===sel.value&&r.Rate===(document.querySelector("#rules").value==="formation"?20:0)',1)
   html=html.replace('sel.onchange=render;render();','''sel.onchange=render;
const rule=document.querySelector('#rules'),ai=document.querySelector('#ai'),battle=document.querySelector('#battle');let inBattle=false;
rule.onchange=render;ai.onchange=()=>{document.querySelector('#rule-state').textContent=(inBattle?'本場規則已固定；':'戰鬥外可切規則；')+(ai.value==='target'?'策略 AI':'原版 AI')+'，AI與規則獨立。'};
battle.onclick=()=>{inBattle=!inBattle;rule.disabled=inBattle;battle.textContent=inBattle?'結束本場試算':'開始本場試算';ai.onchange()};render();''')
   html=html.replace('</details>','</details><p><small>「本場試算」只示意規則鎖定，不會啟動遊戲。存檔規則標記及正式切換仍須接入契約。</small></p>',1)
  target=q/filename;assert not target.exists();target.write_text(html);print('standalone interactive review page written:',filename)
 else:
  inputs=read(q/'formation-inputs.json');results=read(q/'formation-results.json');assert len(inputs)==19 and len(results)==76
  assert len({(x['Input']['Name'],x['Rate'])for x in results})==76
  for row in results:
   v=row['Input'];assert v in inputs;u=v['Slots'][v['Target']];eligible=u['Count']>0 and u['Kind']==1 and v['Target']<3 and v['Route']in ['normal','ranged'] and any(i!=v['Target'] and v['Slots'][i]['Count']>0 for i in range(3));amount=v['Amount']*(100-row['Rate'])//100 if eligible else v['Amount'];expected=0 if not u['Count']else min(amount,u['Count'])if v['Route']=='special'else loss(amount,v['HP'],u['Count'])
   assert row['Eligible']==eligible and row['Amount']==amount and row['Loss']==expected and row['Remaining']==u['Count']-expected
  for ref in read(q/'references.json'):
   f=q/'inputs'/(ref['case']+'.json');assert sha(f)==ref['trace_sha256'];row=next(v for v in results if v['Input']['Name']==ref['case']and v['Rate']==0);assert row['Loss']==ref['observed_loss']
  assert 'PASS' in (q/'tests.log').read_text() and 'FAIL'not in(q/'tests.log').read_text() and not(q/'vet.log').read_text()
  prod=read(r/'preserved/ai-toolbar-audit-r1.json')
  for n,h in prod['programs'].items():assert sha(r/'workplace/player'/n)==h
  for n,h in prod['source_inputs'].items():assert sha(r/n)==h
  for n,h in prod['asset_hashes'].items():assert sha(r/'workplace/player/assets-painted-r66'/n)==h
  core=read(r/'workplace/player/runtime.json');assert core['total_inputs']==923
  for n,h in core['files'].items():assert sha(r/'workplace/player/runtime-render-r1/src'/n)==h
  result=dict(status='passed-offline-DRAFT',cases=19,results=76,original_trace_controls=5,synthetic_cases=14,production_programs_unchanged=7,source_inputs_unchanged=181,assets_unchanged=525,core_unchanged=923,inputs_sha256=sha(q/'formation-inputs.json'),results_sha256=sha(q/'formation-results.json'),catalog_sha256=sha(q/'catalog.json'),html_sha256=sha(q/'formation-prototype-r1.html'),limits=['Not connected to game; 20 percent is a proposed value.','No new IDA, normal player path, save schema or rule-mode validation.'])
  write(q/'audit-r1.json',result);print(json.dumps(result))
if __name__=='__main__':main()
