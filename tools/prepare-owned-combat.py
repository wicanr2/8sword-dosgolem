#!/usr/bin/env python3
"""030: prepare and audit the Go combat core and early extended-save isolation."""
import argparse
import ast
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import urllib.parse
from fractions import Fraction


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text())
def write(path,value):
    with path.open('x')as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['prepare','audit','page','archive','verify','promote','integrity'])
    p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--out',type=Path)
    a=p.parse_args();assert Path('/.dockerenv').is_file()and os.getuid()==1000
    if a.action=='verify':
        index=a.archive/'owned-combat-r1.json';data=read(index);checked=set()
        for v in data['files']:
            path=Path(v['path']);assert not path.is_absolute()and '..'not in path.parts
            obj=data['objects'][v['sha256']];f=a.archive/'owned-combat-r1'/obj['file'];assert sha(f)==obj['stored_sha256']
            raw=gzip.decompress(f.read_bytes());assert len(raw)==v['bytes']and hashlib.sha256(raw).hexdigest()==v['sha256'];checked.add(v['sha256'])
        write(a.out,dict(status='passed-detached-owned-combat',files=len(data['files']),objects=len(checked),workplace_required=False,index_sha256=sha(index)));return
    r=a.project;player=r/'workplace/player';battle=r/'workplace/probe-20261023/graphics-first/battle-r1';q=battle/'owned-combat-r1';candidate=player/'source-candidate-owned-combat-r1'
    previous=read(r/'preserved/hd-music-audit-r1.json')
    added={'internal/eightsword/'+n for n in ['owned_combat.go','owned_combat_test.go','owned_army_guard.go','owned_army_guard_test.go']}
    if a.action=='prepare':
        assert not q.exists()and not candidate.exists()and q.parent.stat().st_uid==1000
        q.mkdir();candidate.mkdir();src=candidate/'src';inputs={}
        for name,h in previous['source_inputs'].items():
            if name!='internal/eightsword/engine.go':assert sha(r/name)==h
            dest=src/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/name,dest);inputs[name]=sha(r/name)
        for name in sorted(added):
            dest=src/name;shutil.copyfile(r/name,dest);inputs[name]=sha(r/name)
        assert len(inputs)==197
        shutil.copyfile(player/'runtime.json',candidate/'runtime.json')
        write(q/'preparation.json',dict(source_inputs=inputs,changed=['internal/eightsword/engine.go']+sorted(added),previous_programs=previous['programs'],core_files=previous['core_files'],asset_hashes=previous['asset_hashes'],runtime_before_sha256=sha(player/'runtime.json')))
        (q/'inputs').mkdir();profiles={}
        legacy=read(battle/'troop-capacity-r1/owned/catalog.json');write(q/'army-catalog.json',legacy)
        source=read(r/'docs/images/troop-traits-reference-r1.json')
        pam=r/'workplace/intake-20261023/sources/game/8sword/PAM.AY';assert sha(pam)==source['original_pam_sha256']
        table=next(v for v in read(battle/'troop-capacity-r1/ida/ida-capacity-r2.json')['tables']if v['label']=='battle-attack-hp-candidate')
        raw=pam.read_bytes()[table['file_offset']:table['file_offset']+104];assert raw.hex()==table['bytes'];factors=struct.unpack('<52H',raw)
        for u in legacy['profiles']:
            kind=u.get('native_kind',0)
            if kind:
                assert 1<=kind<=25;power,hp=factors[kind*2:kind*2+2];ranged=kind in(3,24)
            else:
                reference=next(v for v in source['openkb_troops']if 'openkb:'+v.get('file','')==u['id'])
                power=int(reference['melee'].split('-')[0]);hp=int(reference['hp']);ranged=int(reference['ammo'])>0
            profiles[u['id']]=dict(id=u['id'],attack=power,hp=hp,ranged=ranged,**({'native_kind':kind}if kind else {}))
        catalog=dict(schema='eightsword-owned-combat-catalog/1',profiles=profiles);write(q/'combat-catalog.json',catalog)
        cases=[];references=[]
        names=['normal-locked','normal-choice','normal-rear-only','front-ranged-mixed','rear-ranged-mixed','special0-choice','special2-choice','special5-empty-original']
        for name in names:
            folder=battle/('ai-policy-extra-r2'if name=='special5-empty-original'else'ai-policy-r1')/name
            shadow=read(folder/'shadow/trace.json')
            for mode in ['baseline','override']:
                if name=='special5-empty-original'and mode=='baseline':continue
                f=folder/mode/'trace.json';t=read(f);v=t['View'];rows=[]
                for units,slots in [(v['Friendly'],v['FriendlySlots']),(v['Enemy'],v['EnemySlots'])]:
                    assert len(units)==len(slots)==6 and all(0<=i<6 for i in slots)
                    side=[]
                    for i in slots:
                        u=units[i];assert 0<=u['Kind']<=25 and(u['Kind']or not u['Count'])
                        side.append(dict(unit=f'native:{u["Kind"]:02d}'if u['Kind']else'',count=u['Count']))
                    rows.append(side)
                target=v['OriginalSlot']if mode=='baseline'else t['Decision']['SuggestedSlot'];assert 0<=target<6
                physical=v['FriendlySlots'][target];before=t['BeforeUnits'][physical*2+1];after=t['AfterUnits'][physical*2+1]
                assert before>0 and before>=after and 0<=v['ShiftedSlotZero']<6
                dest=q/'inputs'/(name+'-'+mode+'.json');shutil.copyfile(f,dest)
                # Raw RAM belongs to the accepted original control, not a Go model.
                mem=folder/mode/'before-decision-ram.bin';target_ram=q/'inputs'/(name+'-'+mode+'.ram');shutil.copyfile(mem,target_ram)
                assert sha(mem)==t['BeforeRAMSHA256']
                cases.append(dict(name=name+'-'+mode,rows=rows,config=dict(rules='native',divisors=[5,v['Divisor']+5],multipliers=[1,1],special5_zero_gate=[v['Friendly'][v['ShiftedSlotZero']]['Count']>0,True]),
                    action=dict(side=1,source=v['SourceSlot'],target=target,kind=v['Route'],selector=v['Selector']),expected_loss=before-after,preferred=v['OriginalSlot'],expected_choice=shadow['Decision']['SuggestedSlot']))
                references.append(dict(name=name+'-'+mode,source=str(f.relative_to(r)),sha256=sha(f),ram=target_ram.name,ram_sha256=sha(target_ram)))
        assert len(cases)==15;write(q/'controls.json',dict(catalog=catalog,cases=cases));write(q/'references.json',references)
        shutil.copyfile(battle/'troop-capacity-r1/native-r2/saved-gamedata.ay',q/'inputs/original-save.ay')
        (q/'integration/src').mkdir(parents=True)
        for name in inputs:
            dest=q/'integration/src'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src/name,dest)
        common=(r/'tools/research-owned-army.go').read_text().removeprefix('//go:build ignore\n');common=common[:common.index('func main()')].replace('\n\t"flag"\n','\n')
        (q/'integration/src/tools/owned-army-model.go').write_text(common)
        shutil.copyfile(r/'tools/owned-combat-check.go',q/'integration/src/tools/owned-combat-check.go')
        shutil.copyfile(r/'tools/probe-troop-capacity.go',src/'tools/probe-troop-capacity.go')
        print('Prepared 197-source candidate, 33 Go combat profiles and 15 original outcome controls');return
    prep=read(q/'preparation.json')
    if a.action=='audit':
        log=(q/'tests-r1.log').read_text();assert 'PASS'in log and 'FAIL'not in log and 'SKIP'not in log
        edge=(q/'edge-tests-r1.log').read_text();assert 'TestOwnedCombatExtraEdgeFiveAndNative25'in edge and 'PASS'in edge and 'FAIL'not in edge and 'SKIP'not in edge
        assert not(q/'vet-r1.log').read_text().strip();assert 'go1.24.13'in(candidate/'build-go-version.txt').read_text()
        old_source=player/'source-candidate-map-color-r2/src'
        marker='\tpam, err := os.ReadFile(filepath.Join(opt.Root, "PAM.AY"))'
        injected='\tif err := guardOwnedArmySave(opt.Saves); err != nil {\n\t\treturn nil, err\n\t}\n'
        before=(old_source/'internal/eightsword/engine.go').read_text();assert before.count(marker)==1
        assert (r/'internal/eightsword/engine.go').read_text()==before.replace(marker,injected+marker,1)
        for n,h in prep['source_inputs'].items():assert sha(r/n)==sha(candidate/'src'/n)==sha(q/'integration/src'/n)==h
        for n,h in prep['previous_programs'].items():assert sha(player/n)==h
        for n,h in prep['core_files'].items():assert sha(player/'runtime-render-r1/src'/n)==h
        for n,h in prep['asset_hashes'].items():assert sha(player/'assets-painted-r69'/n)==h
        assert sha(player/'runtime.json')==prep['runtime_before_sha256']
        core=(r/'internal/eightsword/owned_combat.go').read_text()
        for token in ['unsafe','uintptr','oracle.','WriteU16','machine.','FarCall','OnHostCall']:assert token not in core
        controls=read(q/'controls.json');references=read(q/'references.json');assert len(controls['cases'])==len(references)==15
        results=[]
        for item,ref in zip(controls['cases'],references):
            assert item['name']==ref['name']
            f=q/'inputs'/(item['name']+'.json');assert sha(f)==ref['sha256']==sha(r/ref['source'])
            t=read(f);v=t['View'];mem=(q/'inputs'/ref['ram']).read_bytes();assert len(mem)==1<<20
            assert hashlib.sha256(mem).hexdigest()==ref['ram_sha256']==t['BeforeRAMSHA256']
            ds=t['TargetSegment']
            def words(off,n):return list(struct.unpack_from('<'+'H'*n,mem,ds*16+off))
            assert v['Factors']==words(0x70ce,52)
            assert v['FriendlySlots']==words(0x6fb6,6)and v['EnemySlots']==words(0x6fc2,6)
            raw_units=words(0x56e8,24)
            for units,offset in [(v['Friendly'],0),(v['Enemy'],12)]:
                assert [x for u in units for x in [u['Kind'],u['Count']]]==raw_units[offset:offset+12]
            source=v['Enemy'][v['EnemySlots'][v['SourceSlot']]]
            legal=[]
            if v['Route']=='normal':
                front=[i for i in range(3)if v['Friendly'][v['FriendlySlots'][i]]['Count']]
                if not front:legal=[i for i in range(3,6)if v['Friendly'][v['FriendlySlots'][i]]['Count']]
                elif v['Friendly'][v['FriendlySlots'][v['SourceSlot']]]['Count']:legal=[v['SourceSlot']]
                else:legal=front
            else:legal=[i for i in range(6)if v['Friendly'][v['FriendlySlots'][i]]['Count']]
            predictions={}
            for slot in legal:
                unit=v['FriendlySlots'][slot];target=v['Friendly'][unit]
                if v['Route']=='special':
                    selector=v['Selector']
                    if selector==2 and not 6<=target['Kind']<=15:continue
                    if selector==5:
                        guard=v['ShiftedSlotZero']if slot==0 else v['FriendlySlots'][slot-1]
                        assert 0<=guard<6
                        if not v['Friendly'][guard]['Count']:continue
                    if selector==0:loss=2 if source['Kind']==12 else 5
                    elif selector==2:loss=6 if source['Kind']==12 else 15
                    else:assert selector==5;loss=target['Count']//(3 if source['Kind']==12 else 2)+1
                    loss=min(loss,target['Count'])
                else:
                    power=v['Factors'][source['Kind']*2]*source['Count'];assert power<=65535
                    amount=power//(v['Divisor']+5);hp=v['Factors'][target['Kind']*2+1];assert hp>0
                    quotient=amount//hp;loss=0 if quotient==0 else target['Count']if quotient+1>=target['Count']else quotient
                predictions[slot]=loss
            assert predictions
            def score(slot):
                n=v['Friendly'][v['FriendlySlots'][slot]]['Count'];loss=predictions[slot]
                return(loss==n,Fraction(loss,n))
            best=v['OriginalSlot']if v['OriginalSlot']in predictions else next(iter(predictions))
            for slot in predictions:
                if score(slot)>score(best):best=slot
            target=item['action']['target'];assert target in predictions and item['expected_choice']==best
            physical=v['FriendlySlots'][target]
            assert item['expected_loss']==predictions[target]==t['BeforeUnits'][physical*2+1]-t['AfterUnits'][physical*2+1]
            results.append(dict(name=item['name'],loss=predictions[target],choice=best,trace_sha256=ref['sha256']))
        flow=read(q/'flow-r1/receipt.json');cold=read(q/'cold-r1/receipt.json')
        assert flow['status']=='passed-go-owned-combat-data-chain'and cold['status']=='passed-owned-combat-cold-load'
        assert flow['guest_instructions']==cold['guest_instructions']==0 and not flow['player_path']and not cold['player_path']
        assert flow['army']==cold['army']and flow['battle']==cold['battle']
        catalog=read(q/'combat-catalog.json');profiles=catalog['profiles'];assert len(profiles)==33
        native_table=next(v for v in read(battle/'troop-capacity-r1/ida/ida-capacity-r2.json')['tables']if v['label']=='battle-attack-hp-candidate')
        pam=r/'workplace/intake-20261023/sources/game/8sword/PAM.AY';assert sha(pam)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
        raw=pam.read_bytes()[native_table['file_offset']:native_table['file_offset']+104];assert raw.hex()==native_table['bytes'];factors=struct.unpack('<52H',raw)
        for kind in range(1,26):
            p=profiles[f'native:{kind:02d}'];assert(p['attack'],p['hp'])==factors[kind*2:kind*2+2]
        canonical={'schema':catalog['schema'],'profiles':{}}
        for key in sorted(profiles):
            p=profiles[key];d={'id':p['id']}
            if p.get('native_kind'):d['native_kind']=p['native_kind']
            d.update(attack=p['attack'],hp=p['hp'],ranged=p['ranged']);canonical['profiles'][key]=d
        digest=hashlib.sha256(json.dumps(canonical,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
        assert digest==flow['initial']['catalog_sha256']==flow['battle']['catalog_sha256']
        counts=[[v['count']for v in row]for row in flow['initial']['rows']];ids=[[v['unit']for v in row]for row in flow['initial']['rows']]
        acted=[[False]*6 for _ in range(2)];round_number=1;casualties=[0,0]
        for event in flow['events']:
            act=event['action'];side,src,dst=act['side'],act['source'],act['target']
            assert side in(0,1)and 0<=src<6 and 0<=dst<6 and act['kind']=='normal'
            if acted[side][src]:
                assert all(acted[s][i]for s in range(2)for i in range(6)if counts[s][i]);acted=[[False]*6 for _ in range(2)];round_number+=1
            assert not acted[side][src]
            sp,tp=profiles[ids[side][src]],profiles[ids[1-side][dst]]
            damage=counts[side][src]*sp['attack']//5;before=counts[1-side][dst];quotient=damage//tp['hp'];loss=0 if quotient==0 else before if quotient+1>=before else quotient
            counts[1-side][dst]-=loss;casualties[1-side]+=loss;acted[side][src]=True
            assert(event['damage'],event['before'],event['loss'],event['after'])==(damage,before,loss,counts[1-side][dst])
        assert len(flow['events'])==28 and counts[0][0]==29 and sum(counts[1])==0 and casualties==[1,15]
        assert round_number==flow['battle']['round']==14 and flow['battle']['result']=='win'and flow['battle']['committed']
        assert flow['strength']==dict(units=29,base_power=29,base_hp=87)
        army=flow['army'];assert army['gold']==5000-flow['hire']['spent']==3800 and army['offers']['wolf-camp']['stock']==970
        assert army['slots'][0]==dict(unit='openkb:wolf',count=29)
        save=read(q/'flow-r1/gamedata.ay.army.json');assert save['army']==army
        assert save['original_sha256']==sha(q/'inputs/original-save.ay')==sha(q/'flow-r1/gamedata.ay')
        checkpoint=read(q/'flow-r1/battle-checkpoint.json');assert checkpoint['rows'][0][0]['count']==29 and checkpoint['acted'][1][0]and not checkpoint['acted'][0][0]
        old=battle/'troop-capacity-r1'
        assert read(q/'normal-decoded-r1/index.json')==read(old/'decoded-r2/index.json')
        native_states={}
        for name in ['before-commit.state','after-commit.state','reload.state']:
            native_states[name]=sha(q/'normal-r1'/name);assert native_states[name]==sha(old/'native-r2'/name)
        assert sha(q/'normal-r1/saved-gamedata.ay')==sha(old/'native-r2/saved-gamedata.ay')==save['original_sha256']
        assert sha(q/'normal-r1/normal-frame.png')==sha(old/'native-r2/normal-frame.png')
        native=read(q/'normal-r1/receipt.json');assert native['native_save_cycle']['fresh_engine']and not native['native_save_cycle']['snapshot_loaded']
        programs={n:sha(candidate/n)for n in prep['previous_programs']};assert len(programs)==7
        write(a.out,dict(status='passed-owned-combat-core-and-early-isolation',source_count=197,source_inputs=prep['source_inputs'],programs=programs,previous_programs=prep['previous_programs'],core_files=prep['core_files'],asset_hashes=prep['asset_hashes'],native_control_cases=results,
            controlled_actions=28,rounds=14,player_before=30,player_after=29,player_losses=1,enemy_losses=15,go_only_combat=True,owned_cold_process_equal=True,native_normal_states=native_states,native_save_sha256=save['original_sha256'],native_frame_unchanged=True,guard_modes=6,guard_case_variants=2,valid_slot5_and_native25=True,
            checker_sha256=sha(q/'integration/checker'),audit_tool_sha256=sha(Path(__file__)),limits=['Go combat data API and early save isolation only; owned normal player army/battle/UI handoff is pending.','Fifteen historical fixed-source casualty/target controls; not full original battle or timing parity. Special5 baseline with an unsupported original target is explicitly excluded.','OpenKB battle stats are disposable reference lower bounds, not final balance. Reference traits remain inactive.','No world rewards, complete spell coverage or original accumulated-injury display claim.']));print('Passed independent original controls, Go-only battle/save chain and unchanged normal DOS save/reload');return
    if a.action=='page':
        audit=read(q/'audit-final.json');assert audit['status']=='passed-owned-combat-core-and-early-isolation'
        flow=read(q/'flow-r1/receipt.json');army=read(q/'army-catalog.json')
        data=dict(initial=flow['initial']['rows'],events=flow['events'],names={v['id']:v['name']for v in army['profiles']},gold=flow['army']['gold'],stock=flow['army']['offers']['wolf-camp']['stock'])
        text='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>神州八劍：Go兵力資料鏈回放</title><style>
body{background:#102b24;color:#f0e6ca;font:18px/1.7 system-ui,sans-serif;max-width:1100px;margin:30px auto;padding:20px}h1,h2{color:#efd59c}section{border:1px solid #89704a;border-radius:8px;padding:22px;margin:22px 0}.teams{display:grid;grid-template-columns:1fr 1fr;gap:20px}.team{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.slot{border:1px solid #778271;padding:12px;min-height:75px}.empty{opacity:.5}button,input{font:inherit;background:#284437;color:#fff0c4;border:1px solid #b59a5d;padding:12px}button{cursor:pointer;margin:6px}input{width:95%;padding:0}#event{min-height:3em;color:#f2ce8d}small{color:#c6c9b4}strong{color:#f5d99c}@media(max-width:700px){.teams{grid-template-columns:1fr}.team{grid-template-columns:repeat(3,minmax(0,1fr))}body{margin:0;padding:12px}.slot{padding:8px;font-size:16px}}
</style><h1>Go 兵力資料鏈回放</h1><p>這是實際Go核心輸出的28次行動回放，尚未接入遊戲內戰鬥UI。控制局面為30隻野狼對15名骷髏兵，候選數值只供資料鏈驗證，特性標記尚未啟用。</p><section><h2>兵力與陣位分開管理</h2><p>兵種以Go字串ID查表；每方6隊陣位。這場新增兵種的傷害、減員、AI選敵、全滅與戰後存讀都由Go計算，沒有呼叫原版戰鬥執行器。</p><p>197來源候選另已抽驗正常原版購兵、F7存檔及全新Engine冷讀，三份完整客體快照及畫面與前版相同。</p></section><section><button id="previous">上一步</button><button id="next">下一步</button><button id="end">看戰果</button><p id="step-label"></p><input id="step" type="range" min="0" max="28" value="0"><p id="event" role="status"></p><div class="teams"><div><h2>我方 <strong id="player"></strong></h2><div class="team" id="player-team"></div></div><div><h2>敵方 <strong id="enemy"></strong></h2><div class="team" id="enemy-team"></div></div></div></section><section><h2>結算與存讀</h2><p>14輪／28次行動後，我方損失1隻、剩29隻野狼，敵方15名全滅。戰果只回寫一次；金錢3800、招募庫存970保持。完整Go軍隊、庫存及規則已由另一程序讀回。</p><p>目前正式程式偵測到擴充軍隊附檔時，會在DOS啟動前拒絕交給原版讀取並保留資料。新增兵種的正常遊戲UI、原版世界資源同步、完整法術及戰果交接仍待接入。</p></section><script>
const data=DATA,slider=document.querySelector('#step');
function render(){const n=Number(slider.value),rows=JSON.parse(JSON.stringify(data.initial));for(const e of data.events.slice(0,n))rows[1-e.action.side][e.action.target].count=e.after;for(const [side,id]of [[0,'player'],[1,'enemy']]){document.querySelector('#'+id).textContent=rows[side].reduce((s,u)=>s+u.count,0)+' 名';document.querySelector('#'+id+'-team').replaceChildren(...rows[side].map((u,i)=>{const el=document.createElement('div');el.className='slot'+(u.count?'':' empty');el.textContent='陣位 '+i+'：'+(u.unit?(data.names[u.unit]+' × '+u.count):'空隊');return el}))}document.querySelector('#step-label').textContent='行動 '+n+' / '+data.events.length;const e=data.events[n-1];document.querySelector('#event').textContent=e?((e.action.side?'敵方':'我方')+'攻擊：傷害 '+e.damage+'，對方減員 '+e.loss+'，該隊剩 '+e.after+'。'):'初始狀態：Go軍隊已完成招募，尚未開始攻擊。'}
slider.oninput=render;document.querySelector('#previous').onclick=()=>{slider.value=Math.max(0,Number(slider.value)-1);render()};document.querySelector('#next').onclick=()=>{slider.value=Math.min(data.events.length,Number(slider.value)+1);render()};document.querySelector('#end').onclick=()=>{slider.value=data.events.length;render()};render();
</script></html>'''
        target=r/'docs/images/owned-combat-data-chain-r1.html';assert not target.exists();target.write_text(text.replace('DATA',json.dumps(data,ensure_ascii=False).replace('<','\\u003c')));print('Created actual Go event/count replay, clearly labeled outside normal battle UI');return
    if a.action=='archive':
        assert read(q/'audit-final.json')['status']=='passed-owned-combat-core-and-early-isolation'
        folder=a.archive/'owned-combat-r1';index=a.archive/'owned-combat-r1.json';assert not folder.exists()and not index.exists();folder.mkdir()
        selected={f for root in[q,candidate]for f in root.rglob('*')if f.is_file()}
        selected.update(r/n for n in ['tools/prepare-owned-combat.py','tools/owned-combat-check.go','docs/spec/030-battle-expansion-proposal.md','docs/images/owned-combat-data-chain-r1.html'])
        files=[];objects={}
        for f in sorted(selected):
            assert not f.is_symlink()and f.stat().st_uid==1000;raw=f.read_bytes();h=hashlib.sha256(raw).hexdigest()
            if h not in objects:
                blob=gzip.compress(raw,compresslevel=6,mtime=0);name=h+'.gzip';(folder/name).write_bytes(blob);objects[h]=dict(file=name,stored_sha256=hashlib.sha256(blob).hexdigest(),stored_bytes=len(blob))
            files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(raw),mode=f.stat().st_mode&0o777))
        write(index,dict(schema=1,files=files,objects=objects,audit_sha256=sha(q/'audit-final.json'),dependencies={n:sha(r/n)for n in ['preserved/troop-capacity-r1.json','preserved/hd-music-r1.json','preserved/catalog.json.gz']},note='Current Git documents supersede historical READY snapshots.'))
        write(a.out,dict(status='preserved-owned-combat-core',files=len(files),objects=len(objects),stored_bytes=sum(v['stored_bytes']for v in objects.values())));return
    audit=read(a.archive/'owned-combat-audit-r1.json');verified=read(a.archive/'owned-combat-verification-r1.json')
    assert not verified['workplace_required']and verified['index_sha256']==sha(a.archive/'owned-combat-r1.json')
    assert read(a.archive/'owned-combat-r1.json')['audit_sha256']==sha(a.archive/'owned-combat-audit-r1.json')
    if a.action=='promote':
        assert sha(player/'runtime.json')==prep['runtime_before_sha256']
        for n,h in audit['previous_programs'].items():assert sha(player/n)==h
        for n,h in audit['source_inputs'].items():assert sha(r/n)==sha(candidate/'src'/n)==h
        staged={}
        for n,h in audit['programs'].items():
            assert sha(candidate/n)==h;dest=player/('.owned-combat-'+n+'.tmp');assert not dest.exists();os.link(candidate/n,dest);staged[n]=dest
        metadata=read(player/'runtime.json');metadata.update(application_source_inputs=197,application_source_candidate='source-candidate-owned-combat-r1',owned_combat_core='Go-data-v1',owned_army_player_handoff='guarded-pending')
        temp=player/'.owned-combat-runtime.tmp';write(temp,metadata)
        for n,f in staged.items():os.replace(f,player/n)
        os.replace(temp,player/'runtime.json')
        write(a.out,dict(status='promoted-owned-combat-core-and-save-isolation',source_count=197,programs=audit['programs'],assets_unchanged=535,core_unchanged=923,owned_player_handoff='pending',audit_sha256=sha(a.archive/'owned-combat-audit-r1.json')));return
    for n,h in audit['programs'].items():assert sha(player/n)==sha(candidate/n)==h
    for n,h in audit['source_inputs'].items():assert sha(r/n)==sha(candidate/'src'/n)==h
    for n,h in audit['core_files'].items():assert sha(player/'runtime-render-r1/src'/n)==h
    for n,h in audit['asset_hashes'].items():assert sha(player/'assets-painted-r69'/n)==h
    for n,h in audit['previous_programs'].items():assert sha(player/'source-candidate-map-color-r2'/n)==h
    art=read(r/'artwork/manifest.json');assert len(art['files'])==1040
    for item in art['files']:assert sha(r/'artwork'/item['path'])==item['sha256']
    for folder in[q,candidate,a.archive/'owned-combat-r1']:
        assert all(f.stat().st_uid==1000 for f in folder.rglob('*'));assert not any(f.is_dir()and f.name.endswith('.md')for f in folder.rglob('*'))
    assert not any(f.is_file()for f in(r/'workplace/gocache').rglob('*'));ast.parse(Path(__file__).read_text());links=0
    for doc in list(r.glob('*.md'))+[f for d in ['docs','artwork','preserved']for f in(r/d).rglob('*.md')]:
        for target in re.findall(r'\[[^\]]*\]\(([^\s)]+)(?:\s+"[^\"]*")?\)',doc.read_text()):
            path=urllib.parse.unquote(target.strip('<>').split('#',1)[0])
            if not path or path.startswith('/')or re.match('[a-zA-Z][a-zA-Z0-9+.-]*:',path):continue
            assert(doc.parent/path).exists()or(doc.parent/path).resolve()==a.out.resolve(),(doc,target);links+=1
    write(a.out,dict(status='passed-owned-combat-integrity',sources=197,programs=7,core_unchanged=923,assets_unchanged=535,artwork_unchanged=1040,markdown_links=links,root_owned_outputs=0,workspace_cache_files=0,owned_player_handoff='pending'));print('Passed promoted core/guard, unchanged assets/core/art and preservation integrity')


if __name__=='__main__':main()
