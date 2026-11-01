#!/usr/bin/env python3
"""Independently check UI-only rear actions, old glyph cells, and cold resume."""
import argparse,base64,copy,hashlib,importlib.util,io,json,os,tempfile
from pathlib import Path
from PIL import Image
REL='workplace/probe-20261023/graphics-first/battle-r1/rear-actions-r1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def apply_special(before,ev,profiles):
    w=copy.deepcopy(before);s=w['battle']['state'];a=ev['action'];side,source,target=a['side'],a['source'],a['target'];sp=profiles[s['rows'][side][source]['unit']];tp=profiles[s['rows'][1-side][target]['unit']];n=s['rows'][1-side][target]['count'];assert source>=3 and sp['native_kind']in[10,12]and not s['acted'][side][source];v=a['selector']
    if v==0:loss=5 if sp['native_kind']==10 else 2
    elif v==2:assert 6<=tp.get('native_kind',0)<=15;loss=15 if sp['native_kind']==10 else 6
    else:
        assert v==5 and(target>0 and s['rows'][1-side][target-1]['count']>0 or target==0 and s['config']['special5_zero_gate'][1-side]);loss=n//(2 if sp['native_kind']==10 else 3)+1
    loss=min(loss,n);assert ev['loss']==loss and ev['before']==n and ev['after']==n-loss and ev['damage']==loss*tp['hp'];s['rows'][1-side][target]['count']-=loss;s['acted'][side][source]=True;assert ev['result']==s['result']=='';return w
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000;r=a.project;q=r/REL;sp=importlib.util.spec_from_file_location('prep',r/'tools/prepare-rear-actions.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);h=m.helper(r);deps=h.dependencies(r);assert deps==read(q/'baseline.json')
    assert all(sha(q/'go-src'/n)==v for n,v in deps['source_inputs'].items())
    with tempfile.TemporaryDirectory()as td:
        t=Path(td);(t/'tools').mkdir()
        for n in m.PATCHED:(t/'tools'/n).write_bytes(h.stored(r,'summon-r1','/summon-r1/go-src/tools/'+n))
        m.patch(t)
        for n in m.PATCHED:assert(t/'tools'/n).read_bytes()==(q/'go-src/tools'/n).read_bytes()
    base=read(r/'preserved/summon-r1.json')
    for f in base['files']:
        if '/summon-r1/go-src/'not in f['path']:continue
        rel=f['path'].split('/summon-r1/go-src/',1)[1]
        if rel in['tools/'+n for n in m.PATCHED]:continue
        assert sha(q/'go-src'/rel)==f['sha256'],rel
    for n in m.NEW:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n),n
    oracle=read(q/'inputs/owned-combat-audit.json');assert sha(q/'inputs/owned-combat-audit.json')==sha(r/'preserved/owned-combat-audit-r1.json');assert oracle['status']=='passed-owned-combat-core-and-early-isolation';sample={v['name']:v for v in oracle['native_control_cases']};assert[sample[n]['loss']for n in['special0-choice-override','special2-choice-override','special5-empty-original-override']]==[2,6,11]
    model=read(q/'model-r1/receipt.json');assert model['status']=='passed-rear-actions-ui-helpers'and model['persist_collector_only'];profiles=read(q/'inputs/combat-catalog.json')['profiles'];cases=[]
    for v in model['cases']:
        n=v['name']
        if v.get('rejected'):assert v['before']==v['after']and v['persist_calls']==0
        elif n=='rear-pass-round':
            w=copy.deepcopy(v['before']);w['battle']['state']['acted'][1][5]=True;assert w==v['passed'];s=w['battle']['state'];assert all(row['count']==0 or s['acted'][side][i]for side,rows in enumerate(s['rows'])for i,row in enumerate(rows));s['round']+=1;s['acted']=[[False]*6 for _ in range(2)];assert w==v['after']and v['persist_calls']==2
        else:
            assert apply_special(v['before'],v['event'],profiles)==v['after']and v['persist_calls']==1
            if n=='enemy-rear':assert v['event']['action']==dict(side=1,source=3,target=1,kind='special',selector=0)
        cases.append(dict(name=n,rejected=v.get('rejected',False),persist_calls=v['persist_calls']))
    assert len(cases)==9
    old=read(q/'ui-assets/army-ui-fonts.json');prior=json.loads(h.stored(r,'summon-r1','/summon-r1/ui-assets/army-ui-fonts.json'));assert old['glyphs'][:len(prior['glyphs'])]==prior['glyphs'];cells=0
    for profile in old['profiles']:
        file=profile['file'];raw=h.stored(r,'summon-r1','/summon-r1/ui-assets/'+file);before=Image.open(io.BytesIO(raw)).convert('RGBA');after=Image.open(q/'ui-assets'/file).convert('RGBA');assert sha(q/'ui-assets'/file)==profile['sha']
        for g in prior['glyphs']:
            x,y,w,hh=g['cell'];assert before.crop((x,y,x+w,y+hh)).tobytes()==after.crop((x,y,x+w,y+hh)).tobytes();cells+=1
        for g in old['glyphs'][len(prior['glyphs']):]:
            x,y,w,hh=g['cell'];box=after.crop((x,y,x+w,y+hh)).getchannel('A').getbbox();assert box and box[2]-box[0]<=48 and box[3]-box[1]<=52
    gui=read(q/'gui-r1/receipt.json');assert gui['status']=='passed-rear-actions-ui-cold'and gui['controlled_native_entry_and_enemy']and gui['normal_ui_clicks'];assert apply_special(gui['opened']['world'],gui['player']['combat_events'][-1],profiles)==gui['player']['world'];assert gui['cold']['world']==gui['player']['world']and gui['cold']['pair_token']==gui['player']['pair_token']
    ee=[v for v in gui['enemy']['battle_events']if v.get('command')=='enemy'];assert len(ee)==2;assert apply_special(ee[0]['world'],gui['enemy']['combat_events'][-1],profiles)==gui['enemy']['world'];assert gui['enemy']['combat_events'][-1]['action']['source']==3
    events=gui['round2']['battle_events'];previous=events[-2]['world'];w=copy.deepcopy(previous);s=w['battle']['state'];assert all(row['count']==0 or s['acted'][side][i]for side,rows in enumerate(s['rows'])for i,row in enumerate(rows));s['round']+=1;s['acted']=[[False]*6 for _ in range(2)];assert w==gui['round2']['world']and s['round']==2
    frames=[]
    for f in gui['screens']:
        folder=q/'gui-r1'/f['phase'];meta=read(folder/f['metadata']);im=Image.open(folder/f['screen']).convert('RGBA');digest=hashlib.sha256(im.tobytes()).hexdigest();assert digest==meta['canvas_sha256']==meta['presented_sha256']and im.tobytes()==Image.open(folder/f['canvas']).convert('RGBA').tobytes();assert meta['native_rows_hex']==gui['opened']['native_rows_hex']and meta['battle_native_calls']==0;phase_start=gui['opened']if f['phase']=='warm'else gui['cold'];assert meta['battle_guest_steps']==phase_start['battle_guest_steps']and meta['battle_guest_cycles']==gui['opened']['battle_guest_cycles'];assert meta['unit_art']['loaded']==33 and not meta['unit_art']['failures']
        for t in meta['text_fields']or[]:
            x,y,xx,yy=t['Rect'];a1,b1,a2,b2=t['Ink'];assert not t['Ellipsized']and(t['Ink']==[0,0,0,0]or(x<=a1<=a2<=xx and y<=b1<=b2<=yy))
        frames.append(dict(phase=f['phase'],name=f['name'],rgba_sha256=digest))
    assert len(frames)==4
    envelope=read(q/'session-gui-r1/gamedata.ay.army.json');assert envelope['schema']=='eightsword-owned-world-save/3'and envelope['world']==gui['round2']['world']and envelope.get('native_resume')
    ref=envelope['native_resume'];assert ref['phase']=='battle'and ref['pam_sha256']=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0';objects=[f for f in(q/'session-gui-r1').rglob('*')if f.is_file()and ref['sha256']in f.name];assert len(objects)==1 and sha(objects[0])==ref['sha256']and objects[0].stat().st_size==ref['bytes'];assert len(envelope['native_files'])==9 and all(len(base64.b64decode(v))==5761 for v in envelope['native_files'].values())
    index=read(r/'docs/spec/world-army-consumers-r1.json');resolved=next(v for v in index['functions']if v['original_name']=='sub_16BEA');assert resolved['level']=='proven'and resolved['resolution']['required_correction']in(r/'docs/spec/030-battle-expansion-proposal.md').read_text()
    result=dict(status='passed-rear-actions-ui-and-cold',dependencies=deps,model_cases=cases,old_original_controls_reused=oracle['native_control_cases'][10:],old_glyph_cells_unchanged=cells,new_glyphs=[v['character']for v in old['glyphs'][len(prior['glyphs']):]],verified_x11_frames=frames,saved_schema=envelope['schema'],native_cpu_paused=True,cold_host_step_delta=gui['cold']['battle_guest_steps']-gui['opened']['battle_guest_steps'],native_army_unchanged=True,summon_resolution_backlink=resolved,source_tools={n:sha(r/'tools'/n)for n in m.NEW},binaries={n:sha(q/n)for n in['rear-actions-ui','rear-actions-fixture','xcheck']},production_promoted=False,limits=['Pure helper persistence uses a collector; real paired save/cold resume is the separate GUI evidence.','GUI initial army, native entry and enemy rows are explicit fixtures; no natural encounter claim.','Only selectors 0/2/5 are wired; enemy strategy retains selector 0 and existing target ordering.','No new combat formulas, full magic menu, full native tactical parity or formal world integration.'])
    assert not a.out.exists();a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
