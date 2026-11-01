#!/usr/bin/env python3
"""Narrow independent alchemy bytes, arithmetic, charge and display audit."""
import argparse,base64,gzip,hashlib,importlib.util,json,os,struct,tempfile
from pathlib import Path
from PIL import Image
REL='workplace/probe-20261023/graphics-first/battle-r1/alchemy-r1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def word(b,at):return struct.unpack_from('<H',b,at)[0]
def saved(b,at):return(word(b,at)-at-3)&65535
def memory(folder,name):
    row=read(folder/'index.json')[name];b=gzip.decompress((folder/row['memory_file']).read_bytes());assert hashlib.sha256(b).hexdigest()==row['memory_sha256'];return b
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--original-only',action='store_true');a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000;r=a.project;q=r/REL;sp=importlib.util.spec_from_file_location('prep',r/'tools/prepare-alchemy.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);deps=m.helper(r).dependencies(r);assert deps==read(q/'baseline.json');d=read(q/'inputs/ida-map-spells.json');pam=(q/'inputs/PAM.AY').read_bytes();assert sha(q/'inputs/PAM.AY')==d['source_sha256'];header=word(pam,8)*16;relocs=[header+word(pam,word(pam,24)+i*4+2)*16+word(pam,word(pam,24)+i*4)for i in range(word(pam,6))];lines=0
    for f in d['functions']:
        if f['start']not in[0x168ce,0x16b20]:continue
        for v in f['lines']:
            at=v['original_file_offset'];want=bytes.fromhex(v['bytes']);b=bytearray(pam[at:at+len(want)]);assert at==v['ida_linear']-0x10000+header
            for off in relocs:
                if at<=off and off+2<=at+len(want):struct.pack_into('<H',b,off-at,(word(b,off-at)+0x1000)&65535)
            assert bytes(b)==want;lines+=1
    original=read(q/'original-r3/receipt.json');assert original['seed']==0x12345678 and len(original['cases'])==2;results=[]
    for v in original['cases']:
        name=v['name'];before=memory(q/'decoded-original-r3'/name,'before.state');after=memory(q/'decoded-original-r3'/name,'after.state');n=(q/'original-r3'/name/'after-native.ay').read_bytes();amount=v['roll']//260+(40 if v['bonus']else 0);expected=dict(v['before']);expected['gold']=min(30000,expected['gold']+amount);assert v['amount']==amount and v['after']==expected;assert word(before,0x1e880+0x2b2a)==2 and word(after,0x1e880+0x2b2a)==v['uses_after']==saved(n,1254)==1;assert before[0x1e880+0x54a:0x1e880+0x562]==after[0x1e880+0x54a:0x1e880+0x562];assert saved(n,1316)==1 and saved(n,1324)==int(v['bonus']);assert len(n)==2987
        for i,key in enumerate(['rank','merit','monthly_pay','gold','leadership','spell_power']):assert saved(n,i*2)==expected[key]==word(after,0x1e880+0x4f2+i*2)
        results.append(dict(name=name,roll=v['roll'],bonus=v['bonus'],amount=amount,gold=expected['gold'],uses=1,native_sha256=sha(q/'original-r3'/name/'after-native.ay')))
    result=dict(status='passed-original-alchemy-evidence',dependencies=deps,ida_lines=lines,original_cases=results,seed=0x12345678,formal_changed=False)
    if not a.original_only:
        assert all(sha(q/'go-src'/n)==v for n,v in deps['source_inputs'].items())
        h=m.helper(r)
        with tempfile.TemporaryDirectory()as td:
            t=Path(td);(t/'tools').mkdir()
            for n in ['research-paired-progress.go','world-army-review_main.go']:(t/'tools'/n).write_bytes(h.stored(r,'treasure-r1','/story-resources-r1/go-src/tools/'+n))
            m.patch(t)
            for n in ['research-paired-progress.go','world-army-review_main.go']:assert(t/'tools'/n).read_bytes()==(q/'go-src/tools'/n).read_bytes()
        xs=h.stored(r,'treasure-r1','/story-resources-r1/go-src/tools/owned-army-ui-xcheck.go').decode();assert(q/'go-src/tools/owned-army-ui-xcheck.go').read_text()==xs.replace('"F3": 0xffc0,','"F3": 0xffc0, "F4": 0xffc1,')
        for n in m.NEW:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n),n
        candidate=read(q/'candidate-r1/receipt.json');assert candidate['status']=='passed-alchemy-candidate'and candidate['seed']==original['seed']and len(candidate['cases'])==3;old={v['name']:v for v in original['cases']};cases=[];ds=0x1e880;native=(q/'inputs/original-save.ay').read_bytes()
        for v in candidate['cases']:
            name=v['name'];folder=q/'candidate-r1'/name;before=memory(q/'decoded-candidate-r1'/name,'before.state');after=memory(q/'decoded-candidate-r1'/name,'after.state');assert struct.unpack_from('<I',before,ds+0x81bc)[0]==original['seed'];assert before[ds+0x54a:ds+0x562]==after[ds+0x54a:ds+0x562]
            if name=='unavailable':
                assert v['rejected']and'unavailable or mismatched'in v['error']and before==after;assert word(after,ds+0x2b2a)==0;assert saved((folder/'session/gamedata.ay').read_bytes(),1254)==0;cases.append(dict(name=name,rejected=True,ram_unchanged=True));continue
            source=(q/'original-r3'/name/'after-native.ay').read_bytes();raw=(folder/'after-native.ay').read_bytes();assert raw==source and sha(folder/'after-native.ay')==v['native_sha256']==old[name]['native_sha256'];assert raw[12:1236]==native[12:1236]and raw[1348:1508]==native[1348:1508]
            b=read(folder/'before-pair.json');current=read(folder/'after-pair.json');expected=json.loads(json.dumps(b['world']));amount=v['roll']//260+(40 if v['bonus']else 0);expected['army']['gold']=min(30000,expected['army']['gold']+amount);expected['revision']+=1;assert current['world']==v['cold_world']==expected
            assert v['roll']==old[name]['roll']==23359 and v['seed_after']==old[name]['seed_after']==struct.unpack_from('<I',after,ds+0x81bc)[0];assert v['amount']==v['go']['amount']==amount and v['go']['casts']==1 and v['go']['repeat_rejected'];assert word(before,ds+0x2b2a)==2 and word(after,ds+0x2b2a)==saved(raw,1254)==1
            assert word(after,ds+0x26aa)==saved(raw,1316)==1 and word(after,ds+0x26ae)==saved(raw,1324)==int(v['bonus'])
            for i,key in enumerate(['rank','merit','monthly_pay','gold','leadership','spell_power']):assert saved(raw,i*2)==v['after'][key]==word(after,ds+0x4f2+i*2)
            envelope=read(folder/'session/gamedata.ay.army.json');assert envelope['schema']=='eightsword-owned-world-save/4'and envelope['world']==expected and not envelope.get('resume')and envelope['original_sha256']==sha(folder/'after-native.ay');assert len(envelope['native_files'])==9 and all(len(base64.b64decode(x))==5761 for x in envelope['native_files'].values())
            if name=='normal':
                assert v['go']['fault_intent_durable'];assert(folder/'session-fault/gamedata.ay').read_bytes()==raw;assert(folder/'session-fault/gamedata.ay.army.json').read_bytes()==(folder/'session/gamedata.ay.army.json').read_bytes()
            cases.append(dict(name=name,amount=amount,gold=expected['army']['gold'],uses=1,native_sha256=sha(folder/'after-native.ay'),full_native_same_as_original=True,repeat_rejected=True))
        gui=read(q/'gui-r1/receipt.json');assert gui['status']=='passed-alchemy-ui-cold'and gui['initial_army_learned_and_uses_fixture']and gui['ordinary_f4_and_choice']and not gui['ram_or_ip_injected']and not gui['f7_used'];assert gui['returned']['world']==gui['army']['world']==gui['cold']['world']==gui['cold_army']['world'];assert gui['returned']['pair_token']==gui['cold']['pair_token'];assert gui['initial']['world']['army']['gold']==500;amount=gui['outcome']['alchemy']['amount'];award=gui['outcome']['alchemy']['award'];assert amount==award['Roll']//260+(40 if award['Bonus']else 0);assert gui['returned']['world']['army']['gold']==500+amount;assert gui['initial']['alchemy']['uses']==2 and gui['returned']['alchemy']['uses']==gui['cold']['alchemy']['uses']==1 and gui['cold']['alchemy']['casts']==0;assert gui['returned']['world']['army']['slots']==gui['initial']['world']['army']['slots'];frames=[]
        for f in gui['screens']:
            folder=q/'gui-r1'/f['phase'];meta=read(folder/f['metadata']);im=Image.open(folder/f['screen']).convert('RGBA');digest=hashlib.sha256(im.tobytes()).hexdigest();assert digest==meta['canvas_sha256']==meta['presented_sha256']and im.tobytes()==Image.open(folder/f['canvas']).convert('RGBA').tobytes();assert meta['native_rows_hex']==gui['initial']['native_rows_hex']
            for t in meta['text_fields']or[]:
                x,y,xx,yy=t['Rect'];a1,b1,a2,b2=t['Ink'];assert not t['Ellipsized']and(t['Ink']==[0,0,0,0]or(x<=a1<=a2<=xx and y<=b1<=b2<=yy))
            frames.append(dict(phase=f['phase'],name=f['name'],rgba_sha256=digest))
        assert len(frames)==3
        result.update(status='passed-alchemy-candidate',candidate_cases=cases,intent_durable_recovery=True,verified_x11_frames=frames,gui_amount=amount,source_tools={n:sha(r/'tools'/n)for n in m.NEW},binaries={n:sha(q/n)for n in['alchemy-original','alchemy-candidate','alchemy-ui','xcheck']},production_promoted=False,limits=['Controlled F4 original/candidate entries and initial army/learned/uses fixture.','Normal GUI Continue, F4, original choice, acknowledgement, F2 and a new-process cold read; no RAM or IP injection in GUI.','Only alchemy resources and charge persistence; summon, other story consumers and formal integration remain pending.','Native RNG result is reused; seeds are fixed before headless runs, never rerolled.','Formal 197 sources, seven programs, 923 core, r69 assets and the pre-DOS sidecar guard remain unchanged.'])
    assert not a.out.exists();a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
