#!/usr/bin/env python3
"""Independent loss/roam transition, saved choice, glyph and X11 checks."""
import argparse,base64,copy,hashlib,importlib.util,io,json,os,tempfile,struct
from pathlib import Path
from PIL import Image
REL='workplace/probe-20261023/graphics-first/battle-r1/annihilation-roam-r1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def settled(w):
    n=copy.deepcopy(w);assert n['battle']['state']['result']=='loss'and not any(v['count']for v in n['battle']['state']['rows'][0]);del n['encounters'][n['battle']['encounter']];n['battle']=None;n['army']['slots']=[dict(unit='',count=0)for _ in range(6)];n['revision']+=1;return n
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000;r=a.project;q=r/REL;sp=importlib.util.spec_from_file_location('prep',r/'tools/prepare-annihilation-roam.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);h=m.helper(r);deps=h.dependencies(r);assert deps==read(q/'baseline.json')
    assert all(sha(q/'go-src'/n)==v for n,v in deps['source_inputs'].items())
    with tempfile.TemporaryDirectory()as td:
        t=Path(td);(t/'tools').mkdir()
        for n in m.PATCHED:(t/'tools'/n).write_bytes(h.stored(r,m.PARENT,'/'+m.PARENT+'/go-src/tools/'+n))
        m.patch(t)
        for n in m.PATCHED:assert(t/'tools'/n).read_bytes()==(q/'go-src/tools'/n).read_bytes()
    for f in read(r/'preserved/rear-actions-r1.json')['files']:
        if '/rear-actions-r1/go-src/'not in f['path']:continue
        rel=f['path'].split('/rear-actions-r1/go-src/',1)[1]
        if rel not in['tools/'+n for n in m.PATCHED+m.NEW]:assert sha(q/'go-src'/rel)==f['sha256'],rel
    for n in m.NEW:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n),n
    original=read(q/'inputs/original-defeat.json');assert(q/'inputs/original-defeat.json').read_bytes()==h.stored(r,'owned-defeat-r1','/original-r2/receipt.json');assert original['pam_sha256']=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
    controls=[]
    for row in original['rows']:
        if row['case']['Name']not in['roam','roam-promotion']:continue
        b,z=row['before'],row['after'];assert row['random_calls']==0 and z['progress']==b['progress']and z['army']==b['army']and z['position_x']==b['position_x']and z['position_y']==b['position_y'];controls.append(row['case']['Name'])
    assert len(controls)==2
    ida=read(q/'inputs/ida-defeat.json');assert(q/'inputs/ida-defeat.json').read_bytes()==h.stored(r,'owned-defeat-r1','/ida/ida-defeat-r2.json');pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();lines=0
    word=lambda at:struct.unpack_from('<H',pam,at)[0]
    header=word(8)*16;relocated=bytearray(pam[header:])
    for i in range(word(6)):
        at=word(24)+i*4;off=word(at+2)*16+word(at);struct.pack_into('<H',relocated,off,(struct.unpack_from('<H',relocated,off)[0]+0x1000)&65535)
    for f in ida['functions']:
        for x in f['lines']:
            raw=bytes.fromhex(x['bytes']);off=x['ida_linear']-0x10000;assert x['file_offset']==header+off and relocated[off:off+len(raw)]==raw;lines+=1
    model=read(q/'model-r1.json');assert model['status']=='passed-roam-core-and-resume'and settled(model['loss'])==model['after'];assert model['resume']['result']==2 and model['resume']['return_seed']==0x12345678
    gui=read(q/'gui-r1/receipt.json');assert gui['status']=='passed-annihilation-roam-ui'and gui['controlled_native_entry_and_enemy']and not gui['test_seed'];opened,loss,cold,returned,replayed,checkpoint,final=[gui[k]for k in['opened','loss','cold','returned','replayed','checkpoint','final']]
    ev=loss['combat_events'][-1];a1=ev['action'];assert a1==dict(side=1,source=0,target=0,kind='normal',selector=0);profiles=read(q/'inputs/combat-catalog.json')['profiles'];s=opened['world']['battle']['state'];attacker=s['rows'][1][0];target=s['rows'][0][0];amount=attacker['count']*profiles[attacker['unit']]['attack']//s['config']['divisors'][1]*s['config']['multipliers'][1];expected_loss=min(target['count'],amount//profiles[target['unit']]['hp']);assert expected_loss==5 and ev['damage']==amount and ev['loss']==expected_loss
    expected=copy.deepcopy(opened['world']);expected['battle']['state']['rows'][0][0]['count']=0;expected['battle']['state']['acted'][1][0]=True;expected['battle']['state']['result']='loss';assert expected==loss['world'];assert cold['world']==loss['world']and cold['pair_token']==loss['pair_token'];assert settled(loss['world'])==returned['world'];assert replayed['world']==returned['world']and replayed['pair_token']==returned['pair_token'];assert replayed['native_location']==returned['native_location'];assert final['world']==checkpoint['world']and final['native_location']==checkpoint['native_location']
    for state in[returned,replayed,checkpoint,final,gui['army']]:
        assert not any(v['count']for v in state['world']['army']['slots'])and state['world']['battle']is None;assert state['world']['army']['gold']==500 and state['world']['progress']==opened['world']['progress']
        for key in['map_name','map_sha256']:assert state['native_location'][key]==opened['native_location'][key]
        for key in['DS:8E12','DS:8E44']:assert state['native_location']['raw_words'][key]==opened['native_location']['raw_words'][key]
    coldmodel=read(q/'cold-model-r1.json');assert coldmodel['status']=='passed-roam-interrupted-cold-return'and coldmodel['duplicate_refused']and coldmodel['native_unchanged'];assert settled(coldmodel['before']['world'])==coldmodel['after']['world'];assert coldmodel['resume']['phase']=='return'and coldmodel['resume']['result']==2 and coldmodel['resume']['return_seed']==coldmodel['seed']
    old=read(q/'ui-assets/army-ui-fonts.json');prior=json.loads(h.stored(r,'rear-actions-r1','/rear-actions-r1/ui-assets/army-ui-fonts.json'));assert old['glyphs'][:len(prior['glyphs'])]==prior['glyphs'];cells=0
    for profile in old['profiles']:
        file=profile['file'];before=Image.open(io.BytesIO(h.stored(r,'rear-actions-r1','/rear-actions-r1/ui-assets/'+file))).convert('RGBA');after=Image.open(q/'ui-assets'/file).convert('RGBA');assert sha(q/'ui-assets'/file)==profile['sha']
        for g in prior['glyphs']:
            x,y,w,hh=g['cell'];assert before.crop((x,y,x+w,y+hh)).tobytes()==after.crop((x,y,x+w,y+hh)).tobytes();cells+=1
    frames=[]
    for f in gui['screens']:
        folder=q/'gui-r1'/f['phase'];meta=read(folder/f['metadata']);im=Image.open(folder/f['screen']).convert('RGBA');digest=hashlib.sha256(im.tobytes()).hexdigest();assert digest==meta['canvas_sha256']==meta['presented_sha256']and im.tobytes()==Image.open(folder/f['canvas']).convert('RGBA').tobytes();assert meta['native_rows_hex']==opened['native_rows_hex']and meta['battle_native_calls']==0
        for t in meta['text_fields']or[]:
            x,y,xx,yy=t['Rect'];a1,b1,a2,b2=t['Ink'];assert not t['Ellipsized']and(t['Ink']==[0,0,0,0]or(x<=a1<=a2<=xx and y<=b1<=b2<=yy))
        if f['name']in['loss','cold-loss']:assert meta['battle_guest_steps']==(opened if f['name']=='loss'else cold)['battle_guest_steps']and meta['battle_guest_cycles']==opened['battle_guest_cycles']
        frames.append(dict(name=f['name'],rgba_sha256=digest))
    assert len(frames)==7
    envelope=read(q/'session-gui-r1/gamedata.ay.army.json');assert envelope['schema']=='eightsword-owned-world-save/2'and not envelope.get('native_resume')and envelope['world']==final['world'];assert len(envelope['native_files'])==9 and all(len(base64.b64decode(x))==5761 for x in envelope['native_files'].values())
    native=(q/'session-gui-r1/gamedata.ay').read_bytes();base=(q/'inputs/original-save.ay').read_bytes();assert native[12:36]==base[12:36]
    assert not list(q.rglob('.owned-pair.intent.json'))
    report=dict(status='passed-annihilation-roam-limited',original_controls=controls,source_ida_lines=lines,formal_dependencies=deps,model=True,interrupted_cold_return=True,duplicate_refused=True,gui_core_loss=True,gui_cold_choice=True,gui_return_replay=True,gui_f7_then_cold_f2=True,frames=frames,old_glyph_cells_kept=cells,glyphs=len(old['glyphs']),original_army_unchanged=True,original_mode_unchanged=True,production_promoted=False,limits=['Controlled initial army, native entry and enemy.','Roam branch only; return-origin remains DRAFT.','Formal Engine owned-army guard remains enabled.'])
    with a.out.open('x')as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
if __name__=='__main__':main()
