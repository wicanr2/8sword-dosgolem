#!/usr/bin/env python3
"""Independent native origin-map evidence and isolated return audit."""
import argparse,base64,copy,gzip,hashlib,importlib.util,io,json,os,struct,tempfile
from pathlib import Path
from PIL import Image
REL='workplace/probe-20261023/graphics-first/battle-r1/annihilation-origin-r1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unpack(raw):
    size,root=struct.unpack_from('<HH',raw);assert size==5761 and root>=256;start=4+(root-255)*4;tree=[struct.unpack_from('<HH',raw,4+4*i)for i in range(root-255)];out=bytearray();node=root
    for byte in raw[start:]:
        for shift in range(8):
            node=tree[node-256][0 if byte&(1<<shift)else 1]
            if node<256:
                out.append(node);node=root
                if len(out)==size:return bytes(out)
    raise AssertionError('truncated decisions')
def source_lines(pam,ida):
    word=lambda at:struct.unpack_from('<H',pam,at)[0];header=word(8)*16;relocated=bytearray(pam[header:])
    for i in range(word(6)):
        at=word(24)+i*4;off=word(at+2)*16+word(at);struct.pack_into('<H',relocated,off,(struct.unpack_from('<H',relocated,off)[0]+0x1000)&65535)
    n=0
    for f in ida['functions']:
        for x in f['lines']:
            b=bytes.fromhex(x['bytes']);off=x['ida_linear']-0x10000;assert x['file_offset']==header+off and relocated[off:off+len(b)]==b;n+=1
    return n
def original(r,q):
    pam=r/'workplace/intake-20261023/sources/game/8sword/PAM.AY';ida=read(q/'ida/ida-origin-r3.json');assert sha(pam)==ida['source_sha256']=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0';assert ida['database_sha256']=='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac';assert ida['exporter_sha256']==sha(r/'tools/export-annihilation-origin-ida.py')and ida['function_count']==521
    assert ida['index_sha256']==sha(q/'inputs/world-army-consumers-at-origin-export.json')and sum(len(f['indexed_operands'])for f in ida['functions'])==9
    lines=source_lines(pam.read_bytes(),ida);packed=(q/'inputs/origin-terrain-packed.ay').read_bytes();assert hashlib.sha256(packed).hexdigest()=='7835299e69ca627034132cb6dffa6f40df640f46dfce430642ad9780093a346a';terrain=unpack(packed);native=read(q/'original-r3/receipt.json');assert native['status']=='captured-original-origin-and-go-plans';rows=[]
    for row in native['rows']:
        folder=q/'original-r3'/f"region-{row['region']}";before=(folder/'before.ram').read_bytes();after=(folder/'after.ram').read_bytes();assert hashlib.sha256(before).hexdigest()==row['before_sha256']and hashlib.sha256(after).hexdigest()==row['after_sha256'];plan=read(folder/'go-plan.json');maps={k:base64.b64decode(v)for k,v in read(folder/'before-maps.json').items()};branch=(folder/'branch-before.ram').read_bytes();current=branch[0x276d2:0x276e2].split(b'\0')[0].decode().lower();assert current==f"map{row['region']+1:02d}.ay"==plan['current_name'];saved=branch[0x9c000:0x9c000+5761].replace(b'\x64',b'\x32');loaded=saved if current=='map01.ay'else maps['map01.ay'];assert before[0x9c000+5760]==100 and saved[-1]==50
        assert base64.b64decode(plan['terrain'])==terrain==after[0x9a000:0x9a000+5761];assert base64.b64decode(plan['saved_map'])==saved==(folder/'scratch'/current).read_bytes();assert base64.b64decode(plan['loaded_map'])==loaded==after[0x9c000:0x9c000+5761]
        bases={99:0x8cbc,101:0x8d6c,102:0x8dc8,103:0x8de0,104:0x8df8,105:0x8e14,106:0x8e2c,107:0x8c60,113:0x8c30};counts={k:0 for k in bases};words=[]
        for i,kind in enumerate(terrain[:5760]):
            if kind not in bases:continue
            at=bases[kind]+counts[kind]*4;words.extend([dict(Offset=at,Value=i%72),dict(Offset=at+2,Value=i//72)]);counts[kind]+=1
        words+= [dict(Offset=k,Value=v)for k,v in[(0x56d6,0),(0x8e12,40),(0x8e44,40),(0x56ce,0),(0x56c4,3)]];assert words==plan['words']and plan['X']==plan['Y']==40
        for v in words:assert struct.unpack_from('<H',after,0x1e880+v['Offset'])[0]==v['Value'],v
        assert after[0x275dc:0x275dc+8]==b'map1.ay\0'and after[0x276d2:0x276d2+9]==b'map01.ay\0';assert before[0x1ed72:0x1ed7e]==after[0x1ed72:0x1ed7e]and before[0x1edca:0x1ede2]==after[0x1edca:0x1ede2]and (folder/'branch-before.ram').read_bytes()[0x26a3c:0x26a40]==after[0x26a3c:0x26a40]and row['rand_calls_map']==0 and row['rand_calls_before_map']==3
        rows.append(dict(region=row['region'],current=current,go_words=len(words),terrain_sha256=hashlib.sha256(terrain).hexdigest(),saved_map_sha256=hashlib.sha256(saved).hexdigest(),loaded_map_sha256=hashlib.sha256(loaded).hexdigest(),landmark_counts=counts))
    assert len(rows)==2 and rows[1]['current']=='map02.ay';return dict(status='passed-original-origin-map-evidence',ida_lines=lines,original_cases=rows,map_transition_rng_unchanged=True,original_pre_map_rand_calls=3,original_pre_map_rand_callers=['0110:6494','0110:71B3'],full_wrapper_rng_parity=False,controlled_initial_state=True,player_path=False)
def settled(w):
    n=copy.deepcopy(w);assert n['battle']['state']['result']=='loss'and not any(v['count']for v in n['battle']['state']['rows'][0]);del n['encounters'][n['battle']['encounter']];n['battle']=None;n['army']['slots']=[dict(unit='',count=0)for _ in range(6)];n['revision']+=1;return n
def runtime(r,q,proof):
    sp=importlib.util.spec_from_file_location('prep',r/'tools/prepare-annihilation-origin.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);h=m.helper(r);deps=h.dependencies(r);assert deps==read(q/'baseline.json')
    for n,v in deps['source_inputs'].items():assert sha(q/'go-src'/n)==v
    with tempfile.TemporaryDirectory()as td:
        t=Path(td);(t/'tools').mkdir()
        for n in m.PATCHED:(t/'tools'/n).write_bytes(h.stored(r,m.PARENT,'/'+m.PARENT+'/go-src/tools/'+n))
        m.patch(t)
        for n in m.PATCHED:assert(t/'tools'/n).read_bytes()==(q/'go-src/tools'/n).read_bytes()
    parent=read(r/'preserved/annihilation-roam-r1.json');assets=0
    for f in parent['files']:
        rel=f['path'].split('/annihilation-roam-r1/',1)[1]
        if rel.startswith('go-src/')and rel[7:]not in['tools/'+n for n in m.PATCHED+m.NEW]:assert sha(q/rel)==f['sha256'],rel
        if rel.startswith('ui-assets/'):assert sha(q/rel)==f['sha256'];assets+=1
    for n in m.NEW:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n),n
    index=read(r/'docs/spec/world-army-consumers-r1.json');f=next(x for x in index['functions']if x['original_name']=='sub_11796');link=next(x for x in f['resolution']['followups']if x['evidence_receipt']=='preserved/annihilation-origin-audit-r1.json');identity=link['identity'];assert identity==f['resolution']['identity']and identity['module']=='PAM.AY'and identity['ida_mz_linear']=='0x11796'and identity['runtime']=='0110:1796'and identity['source_sha256']==index['source_sha256']
    older=r/link['older_spec'];evidence=r/link['evidence_spec'].split('#',1)[0];assert older.is_file()and evidence.is_file()and link['required_correction']in older.read_text()and 'sub_11796'in evidence.read_text()and '0110:1975'in evidence.read_text()
    model=read(q/'model-r1.json');assert model['status']=='passed-origin-input-guards'and model['bad_map_name_refused']and model['short_tree_refused']and model['truncated_tree_refused']
    gui=read(q/'gui-r1/receipt.json');assert gui['status']=='passed-annihilation-origin-ui'and gui['controlled_native_entry_and_enemy']and not gui['test_seed'];opened,loss,cold,returned,replayed,checkpoint,final=[gui[k]for k in['opened','loss','cold','returned','replayed','checkpoint','final']]
    profiles=read(q/'inputs/combat-catalog.json')['profiles'];ev=loss['combat_events'][-1];assert ev['action']==dict(side=1,source=0,target=0,kind='normal',selector=0);s=opened['world']['battle']['state'];attacker=s['rows'][1][0];target=s['rows'][0][0];damage=attacker['count']*profiles[attacker['unit']]['attack']//s['config']['divisors'][1]*s['config']['multipliers'][1];assert ev['damage']==damage==1600 and ev['loss']==target['count']==5
    w=copy.deepcopy(opened['world']);w['battle']['state']['rows'][0][0]['count']=0;w['battle']['state']['acted'][1][0]=True;w['battle']['state']['result']='loss';assert w==loss['world'];assert cold['world']==loss['world']and cold['pair_token']==loss['pair_token'];assert settled(loss['world'])==returned['world'];assert returned['world']==replayed['world']and returned['pair_token']==replayed['pair_token']and returned['native_location']==replayed['native_location'];assert final['world']==checkpoint['world']and final['native_location']==checkpoint['native_location']
    assert opened['native_location']['raw_words']['DS:8E12']==41
    for state in[returned,replayed,checkpoint,final,gui['army']]:
        assert state['world']['battle']is None and not any(v['count']for v in state['world']['army']['slots']);assert state['world']['army']['gold']==500 and state['world']['progress']==opened['world']['progress'];loc=state['native_location'];assert loc['map_name']=='map01.ay'and loc['raw_words']['DS:8E12']==40 and loc['raw_words']['DS:8E44']==40 and loc['raw_words']['DS:56D6']==0
    cm=read(q/'cold-model-r1.json');assert cm['status']=='passed-origin-interrupted-cold-return'and cm['duplicate_refused']and cm['modified_terrain_refused']and cm['native_unchanged'];assert cm['resume']['result']==3 and cm['resume']['phase']=='return'and cm['resume']['return_seed']==cm['seed'];assert settled(cm['before']['world'])==cm['after']['world']
    pending=read(q/'session-loss-r1/gamedata.ay.army.json');assert pending['schema']=='eightsword-owned-world-save/3'and pending['native_resume']['result']==3 and pending['native_resume']['phase']=='return'and pending['world']==cm['after']['world'];ref=pending['native_resume'];objects=[p for p in(q/'session-loss-r1/.native-resume').iterdir()if ref['sha256']in p.name];assert len(objects)==1 and sha(objects[0])==ref['sha256']and objects[0].stat().st_size==ref['bytes'];assert len(pending['native_files'])==9
    frames=[]
    for row in gui['screens']:
        folder=q/'gui-r1'/row['phase'];meta=read(folder/row['metadata']);im=Image.open(folder/row['screen']).convert('RGBA');digest=hashlib.sha256(im.tobytes()).hexdigest();assert digest==meta['canvas_sha256']==meta['presented_sha256']and im.tobytes()==Image.open(folder/row['canvas']).convert('RGBA').tobytes();assert meta['native_rows_hex']==opened['native_rows_hex']and meta['battle_native_calls']==0
        for t in meta['text_fields']or[]:
            x,y,xx,yy=t['Rect'];a,b,c,d=t['Ink'];assert not t['Ellipsized']and(t['Ink']==[0,0,0,0]or x<=a<=c<=xx and y<=b<=d<=yy)
        if row['name']in['loss','cold-loss']:
            start=opened if row['name']=='loss'else cold;assert meta['battle_guest_steps']==start['battle_guest_steps']and meta['battle_guest_cycles']==opened['battle_guest_cycles'];buttons={t['Role']:t['Text']for t in meta['text_fields']};assert buttons['origin']=='傳送回起點'and buttons['roam']=='冒險浪跡江湖'
        frames.append(dict(name=row['name'],rgba_sha256=digest))
    assert len(frames)==7
    finalsave=read(q/'session-gui-r1/gamedata.ay.army.json');assert finalsave['schema']=='eightsword-owned-world-save/2'and not finalsave.get('native_resume')and finalsave['world']==final['world'];assert len(finalsave['native_files'])==9 and all(len(base64.b64decode(v))==5761 for v in finalsave['native_files'].values());assert(q/'session-gui-r1/gamedata.ay').read_bytes()[12:36]==(q/'inputs/original-save.ay').read_bytes()[12:36];assert not list(q.rglob('.owned-pair.intent.json'))
    return dict(status='passed-annihilation-origin-limited',original_evidence=proof,formal_dependencies=deps,gui_loss_choice_return_cold_f7_f2=True,interrupted_cold_result=3,duplicate_refused=True,modified_source_refused=True,frames=frames,parent_ui_asset_files_kept=assets,glyphs=len(read(q/'ui-assets/army-ui-fonts.json')['glyphs']),formal_promoted=False,limits=['Controlled initial army, native entry and enemy.','Cross-map source/control audit; GUI representative stays on origin region.','No full original wrapper RNG parity.','Actual GUI v1 to v3 to v2; v4 source unchanged except the admitted resume result.'])
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--original-only',action='store_true');a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000;r=a.project;q=r/REL;d=original(r,q)
    if not a.original_only:d=runtime(r,q,d)
    with a.out.open('x')as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
if __name__=='__main__':main()
