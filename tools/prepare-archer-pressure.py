#!/usr/bin/env python3
"""030 DRAFT: prepare typed candidate inputs, independent audit and offline page."""
import argparse,hashlib,json,os,pathlib,shutil
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,d):assert not p.exists();p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','page','audit']);p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();r=a.project;q=a.out;assert os.getuid()==1000 and q.is_dir()
 if a.action=='prepare':
  base=dict(ID='front-0',Label='前排正對活敵軍',Level='synthetic-candidate',Side='enemy',Route='ranged',SourceKind=3,SourceSlot=0,SourceCount=50,Front=[31,0,0],TargetKind=1,TargetSlot=0,TargetCount=31,HP=25,RawAmount=400)
  cases=[]
  def add(id,label,**kw):d=dict(base,ID=id,Label=label);d.update(kw);cases.append(d)
  add('front-0','前排正對活敵軍')
  add('front-1','第二前排正對活敵軍',SourceSlot=1,Front=[0,31,0],TargetSlot=1)
  add('front-2','第三前排正對活敵軍',SourceSlot=2,Front=[0,0,31],TargetSlot=2)
  add('other-lane','只有其他正對陣位有敵軍',Front=[0,31,0],TargetSlot=1)
  add('rear','弓箭手退居後排',SourceSlot=3)
  add('other-ranged','鳥人不套弓箭手候選',SourceKind=24)
  add('other-kind','步兵不套弓箭手候選',SourceKind=2,Route='normal')
  add('protected','目標另有結陣保護',Front=[31,50,0])
  add('two-opponents','多支前排敵軍不疊加壓制',Front=[31,50,50])
  add('player-side','玩家弓箭手的相同局面',Side='player')
  add('threshold','少量部隊的整數門檻',Front=[2,0,0],TargetCount=2,RawAmount=25)
  add('rounding','小傷害的兩次向下取整',Front=[31,50,0],RawAmount=7,HP=1)
  add('special','特殊效果不套壓制或結陣',Route='special',SourceKind=12,RawAmount=2,Front=[31,50,0])
  sources={}
  for name,ref in [('original-ratio','ranged-ratio-native/baseline'),('original-rear','ranged-rear-native/aware')]:
   path=r/'workplace/probe-20261023/graphics-first/battle-r1/ai-formation-r1/original-r2'/ref/'trace.json';t=read(path);v=t['View'];pred=t['Prediction'];source=v['Enemy'][v['EnemySlots'][v['SourceSlot']]];target=v['Friendly'][pred['Unit']];front=[v['Friendly'][v['FriendlySlots'][i]]['Count']for i in range(3)];amount=((v['Factors'][source['Kind']*2]*source['Count'])&65535)//((v['Divisor']+5)&65535);assert amount==pred['Amount']
   add(name,'原版基準：'+('前排目標'if name=='original-ratio'else'遠程可改選目標'),Level='original-trace-baseline-only',SourceKind=source['Kind'],SourceSlot=v['SourceSlot'],SourceCount=source['Count'],Front=front,TargetKind=target['Kind'],TargetSlot=pred['Slot'],TargetCount=target['Count'],HP=v['Factors'][target['Kind']*2+1],RawAmount=amount,BaselineLoss=pred['Loss']);sources[str(path.relative_to(r))]=sha(path)
  save(q/'cases-r1.json',cases);module=q/'module';assert not module.exists();module.mkdir();(module/'go.mod').write_text('module archer-pressure-prototype\n\ngo 1.24.13\n');shutil.copyfile(r/'tools/research-archer-pressure.go',module/'main.go');shutil.copyfile(r/'tools/research-archer-pressure_test.go',module/'main_test.go');save(q/'preparation-r1.json',dict(schema=1,status='DRAFT',sources=sources,tool_sha256=sha(pathlib.Path(__file__)),go_source_sha256=sha(module/'main.go'),go_test_sha256=sha(module/'main_test.go'),cases=len(cases)));print('prepared',len(cases),'typed cases')
 elif a.action=='audit':
  cases=read(q/'cases-r1.json');result=read(q/'results-r1.json');assert len(cases)==len(result['rows'])==15;checked=0
  for s,row in zip(cases,result['rows']):
   assert s==row['scenario'];before=dict(s)
   for m,v in zip(result['modes'],row['results']):
    pressure=s['Route']!='special'and s['SourceKind']==3 and s['SourceSlot']<3 and s['Front'][s['SourceSlot']]>0;applied=pressure and m['Pressure']>0;after=s['RawAmount']*(100-m['Pressure'])//100 if applied else s['RawAmount'];formation=m['Formation']and s['Route']!='special'and s['TargetKind']==1 and s['TargetSlot']<3 and any(i!=s['TargetSlot']and n>0 for i,n in enumerate(s['Front']));amount=after*80//100 if formation else after
    if s['Route']=='special':loss=min(amount,s['TargetCount'])
    else:encoded=(amount//s['HP']+1)&65535;loss=0 if encoded<=1 else s['TargetCount']if encoded>=s['TargetCount']else encoded-1
    expected=dict(Mode=m['ID'],PressureEligible=pressure,PressureApplied=applied,FormationApplied=bool(formation),Raw=s['RawAmount'],AfterPressure=after,Amount=amount,Loss=loss,Remaining=s['TargetCount']-loss);assert expected==v,(s['ID'],expected,v)
    if m['ID']=='native'and'BaselineLoss'in s:assert loss==s['BaselineLoss']
    checked+=1
   assert s==before
  assert checked==60
  prod=read(r/'preserved/ai-formation-audit-r1.json')
  for n,h in prod['programs'].items():assert sha(r/'workplace/player'/n)==h
  for n,h in prod['source_inputs'].items():assert sha(r/n)==h
  for n,h in prod['asset_hashes'].items():assert sha(r/'workplace/player/assets-painted-r67'/n)==h
  for source,h in read(q/'preparation-r1.json')['sources'].items():assert sha(r/source)==h
  tests=(q/'tests-r1.log').read_text();assert '\nPASS\n'in tests and'FAIL'not in tests and'SKIP'not in tests;assert not(q/'vet-r1.log').read_text()
  save(q/'audit-r1.json',dict(status='passed-offline-archer-pressure-candidate',cases=15,calculations=checked,original_trace_baselines=2,synthetic_cases=13,production_programs_unchanged=7,production_sources_unchanged=184,assets_unchanged=525,results_sha256=sha(q/'results-r1.json'),candidate='front kind3, opposing front alive; pressure before formation',limitations=['Candidate percentages, multiplication order and new mode are not approved.','No production rules, new troop IDs or original gameplay claims.']));print('independent candidate audit passed:',checked)
 else:
  assert read(q/'audit-r1.json')['status']=='passed-offline-archer-pressure-candidate';data=(q/'results-r1.json').read_text().replace('<','\\u003c');html=PAGE.replace('__DATA__',data);target=q/'prototype-r1.html';assert not target.exists();target.write_text(html);print('offline interactive prototype prepared')
PAGE='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>神州八劍：弓箭手壓制試算</title><style>
*{box-sizing:border-box}body{margin:0;background:#101c1c;color:#efe5c4;font-family:"Noto Sans CJK TC",sans-serif;line-height:1.65}main{max-width:1060px;margin:auto;padding:22px}h1{font-size:26px;margin:8px 0}h2{font-size:19px}p{margin:9px 0}.badge{color:#f3ce7c}label{display:block}select{width:100%;background:#203a38;color:#fff1c7;border:1px solid #947d4e;padding:12px;font:inherit}.controls,.stats,.modes{display:grid;gap:12px}.controls{grid-template-columns:1.4fr 1fr}.modes{grid-template-columns:repeat(4,1fr);margin:16px 0}button{font:inherit;color:inherit;background:#1e3430;border:1px solid #87764c;padding:12px;cursor:pointer;text-align:left}button[aria-pressed=true]{background:#4a4330;border:2px solid #f0c66f}.small{font-size:13px;color:#c4bda4}.board{background:#122b2b;border:1px solid #756442;padding:12px;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}.cell{min-height:82px;padding:8px;border:1px solid #3b5a54;border-radius:5px;color:#a6b8b1}.unit{background:#294842;color:#fff2ca}.target{border:2px solid #e0b968}.suppressed{box-shadow:inset 0 0 0 2px #e1a95a}.stats{grid-template-columns:repeat(3,1fr);margin:16px 0}.stat{background:#263832;padding:14px}.stat b{font-size:30px;display:block}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse;margin:16px 0}th,td{padding:9px;border-bottom:1px solid #526052;text-align:right;white-space:nowrap}th:first-child,td:first-child{text-align:left}.note{border-left:3px solid #ba9250;padding:8px 13px;background:#20302b}.rule{background:#253b35;padding:14px}@media(max-width:650px){main{padding:14px}.controls{grid-template-columns:1fr}.modes{grid-template-columns:1fr 1fr}.cell{font-size:12px;padding:5px;min-height:75px}.stats{gap:7px}.stat{padding:8px}.stat b{font-size:25px}}
</style><main><div class="badge">設計原型，尚未接入遊戲</div><h1>弓箭手「正對壓制」</h1><p>前排弓箭手正對活敵軍時，自身普通／遠程傷害減25%或50%。後排、正對空隊、其他兵種與特殊效果不套。</p><div class="note">新特性只放在候選戰術模式；現有「原版規則」與「結陣試作」保持原語意。先壓制，再結陣，各自向下取整，最後沿原版減員編碼。這個順序也尚待確認。</div><div class="controls"><label>比較局面<select id="case"></select></label><label>試算模式<select id="mode"></select></label></div><p id="scenario-level" class="small"></p><div class="modes" id="cards"></div><div class="board" id="board"></div><div class="stats"><div class="stat">實際傷害量<b id="amount"></b></div><div class="stat">減員<b id="loss"></b></div><div class="stat">剩餘兵數<b id="remaining"></b></div></div><div class="rule" id="explain"></div><div class="table-wrap"><table><thead><tr><th>規則</th><th>原傷害量</th><th>壓制後</th><th>結陣後</th><th>減員</th></tr></thead><tbody id="comparison"></tbody></table></div><p class="small">整數門檻可能讓少量部隊的兵損大幅改變，減25%傷害不代表少損失25%兵數。頁面使用Go預算結果，不在瀏覽器另算傷害。</p><h2>槍兵的接入限制</h2><p>原版25筆名稱沒有槍兵，不能改名覆蓋步兵。新兵種仍需查ID、招募、素材與存讀容量；本頁沒有新增兵種或修改正式程式。</p></main><script id="payload" type="application/json">__DATA__</script><script>
const DATA=JSON.parse(document.getElementById('payload').textContent),cases=document.getElementById('case'),mode=document.getElementById('mode');
for(const row of DATA.rows)cases.add(new Option(row.scenario.Label,row.scenario.ID));for(const m of DATA.modes)mode.add(new Option(m.Label,m.ID));mode.value='tactics25';
function render(){const row=DATA.rows.find(r=>r.scenario.ID===cases.value),s=row.scenario,v=row.results.find(v=>v.Mode===mode.value);document.getElementById('scenario-level').textContent=s.Level==='synthetic-candidate'?'合成候選局面。不是遊戲已執行的新規則。':'0%原版基準取自已驗trace；壓制候選仍是離線試算。';
document.getElementById('cards').innerHTML=DATA.modes.map((m,i)=>`<button class="mode-card" data-mode="${m.ID}" aria-pressed="${m.ID===mode.value}">${m.Label}<br>減員 ${row.results[i].Loss}</button>`).join('');document.querySelectorAll('.mode-card').forEach(b=>b.onclick=()=>{mode.value=b.dataset.mode;render()});
const cells=['攻方後排','攻方前排','守方前排','守方後排'].map(x=>`<div class="small">${x}</div>`);for(let i=0;i<3;i++){for(let c=0;c<4;c++){let text='空陣位',cl='cell';if((c===0&&s.SourceSlot===i+3)||(c===1&&s.SourceSlot===i)){text=(s.SourceKind===3?'弓箭手':s.SourceKind===24?'鳥人':s.SourceKind===12?'雙頭鬼':'步兵')+' '+s.SourceCount;cl+=' unit';if(v.PressureApplied)cl+=' suppressed'}if(c===2&&s.Front[i]>0){text=(s.TargetSlot===i?'目標部隊':'活隊')+' '+s.Front[i];cl+=' unit'}if(c===3&&s.TargetSlot===i+3){text='目標部隊 '+s.TargetCount;cl+=' unit'}if((c===2&&s.TargetSlot===i)||(c===3&&s.TargetSlot===i+3))cl+=' target';cells.push(`<div class="${cl}">${text}</div>`)}}document.getElementById('board').innerHTML=cells.join('');
for(const [id,n]of [['amount',v.Amount],['loss',v.Loss],['remaining',v.Remaining]])document.getElementById(id).textContent=n;
document.getElementById('explain').textContent=(v.PressureApplied?'本候選觸發壓制。':v.PressureEligible?'符合壓制條件，但此模式沒有新增壓制。':'此局不符合弓箭手正對壓制條件。')+(v.FormationApplied?'目標的既有結陣再減20%。':'目標未套結陣減傷。');document.getElementById('comparison').innerHTML=DATA.modes.map((m,i)=>{const r=row.results[i];return `<tr><td>${m.Label}</td><td>${r.Raw}</td><td>${r.AfterPressure}</td><td>${r.Amount}</td><td>${r.Loss}</td></tr>`}).join('')}
cases.onchange=render;mode.onchange=render;render();
</script></html>'''
if __name__=='__main__':main()
