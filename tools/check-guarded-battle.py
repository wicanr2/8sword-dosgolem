#!/usr/bin/env python3
"""Verify fixed-guard source layout and isolated Go player-path evidence."""
import argparse,base64,copy,gzip,hashlib,importlib.util,io,json,os,struct,tempfile
from pathlib import Path
from PIL import Image
REL='workplace/probe-20261023/graphics-first/battle-r1/guarded-battle-r1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def original(r,q):
    sp=importlib.util.spec_from_file_location('origin',r/'tools/check-annihilation-origin.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
    lines=sum(m.source_lines(pam,read(q/'inputs'/n))for n in['ida-guard-world.json','ida-guard-rewards.json','ida-save.json'])
    tagged=read(q/'mapping-r1/receipt.json');native=(q/'mapping-r1/scratch/gamedata.ay').read_bytes();assert tagged['status']=='passed-native-guard-save-mapping'and tagged['controlled_words']==504 and tagged['offsets']==list(range(1508,2516,2))
    for i,at in enumerate(tagged['offsets']):assert struct.unpack_from('<H',native,at)[0]-(at+3)&65535==0x5000+i
    layout=read(q/'guard-layout-evidence.json');coords=[]
    for g in range(8):
        b=m.unpack((r/'workplace/intake-20261023/sources/game/8sword'/f'MAP{g+1}.AY').read_bytes());coords.append([[i%72,i//72]for i,v in enumerate(b[:5760])if v==113])
    assert coords==layout['coordinates']and list(map(len,coords))==[7,4,4,4,4,4,4,11]and sum(map(len,coords))==42
    controls=read(q/'inputs/original-guard-controls.json');assert len(controls['rows'])==10
    for row in controls['rows']:
        c=row['case'];b,a=row['before'],row['after'];expected=list(b['progress'])
        if c['Result']==0:
            expected[2]+=20*(c['Region']+1)
            if c['Legacy26AA']==1:expected[5]+=c['Region']+1
        elif c['Result']==1:expected[3]-=expected[3]//(row['random_input']//2730+3)
        assert a['progress']==expected and row['battle_calls']==1
    return dict(status='passed-guarded-source-and-save-layout',ida_lines=lines,legacy_controls=10,guard_counts=list(map(len,coords)),npc_words=504,native_save_span=[1508,2516],original_player_path=False)
def compact(rows):return [copy.deepcopy(v)for v in rows if v['count']]+[dict(unit='',count=0)for _ in range(sum(not v['count']for v in rows))]
def settle(w,result,seed):
    w=copy.deepcopy(w);b=w['battle'];key=b['encounter'];record=w['encounters'][key];w['army']['slots']=compact(b['state']['rows'][0]);w['battle']=None;w['revision']+=1
    if result==0:
        assert b['state']['result']=='win';record['cleared']=True;w['progress']['legacy_04f6']=min(30000,w['progress']['legacy_04f6']+20)
    else:
        assert result==1;record['enemy']=compact(b['state']['rows'][1]);n=(seed*214013+2531011)&0xffffffff;value=(n>>16)&32767;w['army']['gold']-=w['army']['gold']//(value//2730+3)
    return w
def runtime(r,q,proof):
    sp=importlib.util.spec_from_file_location('prep',r/'tools/prepare-guarded-battle.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);h=m.helper(r);deps=h.dependencies(r);assert deps==read(q/'baseline.json')
    for n,v in deps['source_inputs'].items():assert sha(q/'go-src'/n)==v
    with tempfile.TemporaryDirectory()as td:
        t=Path(td);(t/'tools').mkdir()
        for n in m.PATCHED:(t/'tools'/n).write_bytes(h.stored(r,m.PARENT,'/'+m.PARENT+'/go-src/tools/'+n))
        m.patch(t)
        for n in m.PATCHED:assert(t/'tools'/n).read_bytes()==(q/'go-src/tools'/n).read_bytes()
    assets=0
    for f in read(r/'preserved'/f'{m.PARENT}.json')['files']:
        rel=f['path'].split('/'+m.PARENT+'/',1)[1]
        if rel.startswith('go-src/')and rel[7:]not in['tools/'+n for n in m.PATCHED+m.NEW]:assert sha(q/rel)==f['sha256'],rel
        if rel.startswith('ui-assets/'):assert sha(q/rel)==f['sha256'];assets+=1
    for n in m.NEW:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n),n
    index=read(r/'docs/spec/world-army-consumers-r1.json');links=0
    for f in index['functions']:
        if f['original_name']not in['sub_12DDE','sub_132E0','sub_11ABE']:continue
        v=f['resolution'];identity=v['identity'];assert identity['ida_mz_linear']==f['ida_mz_linear']and identity['runtime']==f['runtime']and identity['module']=='PAM.AY'and identity['source_sha256']==index['source_sha256'];assert v['evidence_receipt']=='preserved/guarded-battle-audit-r1.json'
        for n in['older_spec','evidence_spec']:
            p=r/v[n].split('#',1)[0];assert p.is_file()and v['required_correction']in p.read_text()and f['original_name']in p.read_text()
        assert(r/v['unaffected_spec']).is_file();links+=1
    assert links==3
    model=read(q/'model-r1.json');assert model['status']=='passed-guarded-rules-and-projection'and all(model[k]for k in['extended_npc_refused','actual_capacity_refused','unwon_refused'])
    gui=read(q/'gui-r2/receipt.json');assert gui['status']=='passed-guarded-battle-ui'and gui['native_guard_unmodified']and not gui['test_seed'];opened,strike,retreated,cold,rematch,won,settled,replayed,checkpoint,final=[gui[k]for k in['opened','strike','retreated','cold','rematch','won','settled','replayed','checkpoint','final']]
    key='guarded:00:00';source=[dict(unit=f'native:{n:02d}',count=v)for n,v in[(6,30),(11,40),(16,30),(21,40),(7,20)]]+[dict(unit='',count=0)]
    assert opened['guarded_binding']['rows']==source==opened['world']['battle']['state']['initial'][1]and opened['guarded_binding']['presence_skips']==1 and opened['encounter_confirmed']
    event=strike['combat_events'][-1];profiles=read(q/'inputs/combat-catalog.json')['profiles'];s=opened['world']['battle']['state'];damage=s['rows'][0][0]['count']*profiles[s['rows'][0][0]['unit']]['attack']//s['config']['divisors'][0]*s['config']['multipliers'][0];assert event['damage']==damage==24000 and event['loss']==30 and event['action']==dict(side=0,source=0,target=0,kind='normal',selector=0)
    expected=copy.deepcopy(opened['world']);expected['battle']['state']['rows'][1][0]['count']=0;expected['battle']['state']['acted'][0][0]=True;assert expected==strike['world']
    held=read(q/'session-before-cold-r1/gamedata.ay.army.json');seed=held['native_resume']['return_seed'];assert held['native_resume']['phase']=='battle'and held['world']==strike['world']
    assert settle(strike['world'],1,seed)==retreated['world'];assert cold['world']==retreated['world']and cold['pair_token']==retreated['pair_token']
    assert rematch['world']['battle']['state']['initial'][1]==retreated['world']['encounters'][key]['enemy']==source[1:5]+[dict(unit='',count=0)]*2
    assert settle(won['world'],0,0)==settled['world'];assert settled['world']['progress']['legacy_04f6']==120 and settled['world']['progress']['merit']==10000 and settled['world']['progress']['rank']==1 and settled['world']['army']['gold']==retreated['world']['army']['gold']
    assert replayed['world']==settled['world']and replayed['pair_token']==settled['pair_token']and final['world']==checkpoint['world']and gui['army']['world']==final['world']
    native0=(q/'session-before-cold-r1/gamedata.ay').read_bytes()
    for folder,state,cleared in[('session-retreated-r1',retreated,False),('session-settled-r1',settled,True)]:
        raw=(q/folder/'gamedata.ay').read_bytes();saved=read(q/folder/'gamedata.ay.army.json');assert saved['world']==state['world']and saved['schema']=='eightsword-owned-world-save/3'and len(saved['native_files'])==9 and saved['native_resume']['phase']=='return'
        rows=[dict(unit='',count=0)]*6 if cleared else state['world']['encounters'][key]['enemy']
        for i,row in enumerate(rows):
            at=1508+i*4;kind=(struct.unpack_from('<H',raw,at)[0]-at-3)&65535;count=(struct.unpack_from('<H',raw,at+2)[0]-at-5)&65535;assert (kind,count)==(int(row['unit'].split(':')[1])if row['unit']else 0,row['count'])
        for i,(b,a)in enumerate(zip(native0,raw)):
            if not(i<12 or 1508<=i<1532):assert a==b,('unrelated native byte',i)
    cm=read(q/'cold-model-r2.json');assert cm['status']=='passed-guarded-interrupted-cold-return'and all(cm[k]for k in['duplicate_refused','source_refused','boss_refused','ending_refused','player_shadow_unchanged']);assert settle(cm['before']['world'],1,cm['seed'])==cm['after']['world']and cm['resume']['result']==1
    ram=(q/'guarded-held.ram').read_bytes();word=lambda at:struct.unpack_from('<H',ram,0x1e880+at)[0];assert word(0x8e12)==5 and word(0x8e44)==4
    for i,row in enumerate(source):assert(word(0x365e+i*4),word(0x3660+i*4))==(int(row['unit'].split(':')[1])if row['unit']else 0,row['count'])
    frames=[]
    for row in gui['screens']:
        folder=q/'gui-r2'/row['phase'];meta=read(folder/row['metadata']);im=Image.open(folder/row['screen']).convert('RGBA');digest=hashlib.sha256(im.tobytes()).hexdigest();assert digest==meta['canvas_sha256']==meta['presented_sha256']and im.tobytes()==Image.open(folder/row['canvas']).convert('RGBA').tobytes();assert meta['native_rows_hex']==opened['native_rows_hex']and meta['battle_native_calls']==0
        for t in meta['text_fields']or[]:
            x,y,xx,yy=t['Rect'];a,b,c,d=t['Ink'];assert not t['Ellipsized']and(t['Ink']==[0,0,0,0]or x<=a<=c<=xx and y<=b<=d<=yy)
        if row['name']in['guard-opened','guard-strike']:
            assert meta['battle_guest_steps']==opened['battle_guest_steps']and meta['battle_guest_cycles']==opened['battle_guest_cycles']
        if meta.get('battle_finished'):
            assert meta['native_location']['raw_words']['DS:8E12']==5 and meta['native_location']['raw_words']['DS:8E44']==4
        frames.append(dict(name=row['name'],rgba_sha256=digest))
    assert read(q/'session-gui-r1/gamedata.ay.army.json')['schema']=='eightsword-owned-world-save/2'
    return dict(status='passed-guarded-battle-limited',source=proof,source_dependencies=deps,ui_assets_unchanged=assets,images=frames,salary_before=100,salary_after=120,guard_key=key,retreat_gold=retreated['world']['army']['gold'],other_41_guards_and_native_player_unchanged=True,original_guard_unmodified=True,controlled_initial_army_and_position=True,gui_schema_path=[1,3,2],formal_promoted=False,boss_and_ending=False,guard_loss_gui=False,source_tool_sha256=sha(r/'tools/check-guarded-battle.py'))
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--original-only',action='store_true');a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000;r=a.project;q=r/REL;d=original(r,q)
    if not a.original_only:d=runtime(r,q,d)
    with a.out.open('x')as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
if __name__=='__main__':main()
