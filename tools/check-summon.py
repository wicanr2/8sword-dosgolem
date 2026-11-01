#!/usr/bin/env python3
"""Independent summon arithmetic, six-row, charge, save and GUI audit."""
import argparse,base64,gzip,hashlib,importlib.util,json,os,struct,tempfile
from pathlib import Path
from PIL import Image
REL='workplace/probe-20261023/graphics-first/battle-r1/summon-r1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def word(b,at):return struct.unpack_from('<H',b,at)[0]
def saved(b,at):return(word(b,at)-at-3)&65535
def memory(folder,name):
    row=read(folder/'index.json')[name];b=gzip.decompress((folder/row['memory_file']).read_bytes());assert hashlib.sha256(b).hexdigest()==row['memory_sha256'];return b
def payload(roll,rank,bonus):return roll//6600*5+rank,(24-rank*4)*(3 if bonus else 2)//2
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--original-only',action='store_true');a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000;r=a.project;q=r/REL;sp=importlib.util.spec_from_file_location('prep',r/'tools/prepare-summon.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);deps=m.helper(r).dependencies(r);assert deps==read(q/'baseline.json');pam=(q/'inputs/PAM.AY').read_bytes();header=word(pam,8)*16;relocs=[header+word(pam,word(pam,24)+i*4+2)*16+word(pam,word(pam,24)+i*4)for i in range(word(pam,6))];lines=0
    for path,starts in [('ida-map-spells.json',[0x168ce,0x16bea]),('ida-monthly.json',[0x16226])]:
        d=read(q/'inputs'/path);assert sha(q/'inputs/PAM.AY')==d['source_sha256']
        for f in d['functions']:
            if f['start']not in starts:continue
            for v in f['lines']:
                at=v.get('original_file_offset',v.get('file_offset'));want=bytes.fromhex(v['bytes']);b=bytearray(pam[at:at+len(want)]);assert at==v['ida_linear']-0x10000+header
                for off in relocs:
                    if at<=off and off+2<=at+len(want):struct.pack_into('<H',b,off-at,(word(b,off-at)+0x1000)&65535)
                assert bytes(b)==want;lines+=1
    assert struct.unpack_from('<d',pam,header+0x1d780+0x8364)[0]==1.5
    assert pam[header+0x6249:header+0x624b]==bytes.fromhex('eb05')
    original=read(q/'original-r1/receipt.json');assert original['seed']==0x12345678 and len(original['cases'])==3;results=[];ds=0x1e880
    for v in original['cases']:
        name=v['name'];before=memory(q/'decoded-original-r1'/name,'before.state');after=memory(q/'decoded-original-r1'/name,'after.state');n=(q/'original-r1'/name/'after-native.ay').read_bytes();kind,count=payload(v['roll'],v['rank'],v['bonus']);assert kind==v['kind']and count==v['count'];rows=[[word(before,ds+0x54a+i*4),word(before,ds+0x54c+i*4)]for i in range(6)];matched=False
        for row in rows:
            if row[0]==kind:row[1]=(row[1]+count)&65535;matched=True
        if not matched:
            for row in rows:
                if row[0]==0:row[0]=kind;row[1]=(row[1]+count)&65535;matched=True;break
        assert [x for row in rows for x in row]==v['native_army_after'];assert all(saved(n,12+i*4)==rows[i][0]==word(after,ds+0x54a+i*4)and saved(n,14+i*4)==rows[i][1]==word(after,ds+0x54c+i*4)for i in range(6));assert len(n)==2987 and sha(q/'original-r1'/name/'after-native.ay')==v['native_sha256'];assert word(before,ds+0x2b2c)==2 and word(after,ds+0x2b2c)==saved(n,1256)==1;assert saved(n,1328)==int(v['bonus'])and saved(n,1316)==1;assert v['before']==v['after'];assert word(before,ds+0x56e6)==0 and word(after,ds+0x56e6)==1;assert struct.unpack_from('<I',before,ds+0x81bc)[0]==original['seed']
        for i,key in enumerate(['rank','merit','monthly_pay','gold','leadership','spell_power']):assert saved(n,i*2)==v['after'][key]==word(after,ds+0x4f2+i*2)
        results.append(dict(name=name,roll=v['roll'],kind=kind,count=count,joined=matched,rank=v['rank'],bonus=v['bonus'],uses=1,native_sha256=v['native_sha256'],seed_after=v['seed_after']))
    result=dict(status='passed-original-summon-evidence',dependencies=deps,ida_lines=lines,original_cases=results,seed=original['seed'],formal_changed=False)
    if not a.original_only:
        h=m.helper(r);assert all(sha(q/'go-src'/n)==v for n,v in deps['source_inputs'].items())
        with tempfile.TemporaryDirectory()as td:
            t=Path(td);(t/'tools').mkdir()
            for n in ['research-paired-progress.go','world-army-review_main.go']:(t/'tools'/n).write_bytes(h.stored(r,'alchemy-r1','/alchemy-r1/go-src/tools/'+n))
            m.patch(t)
            for n in ['research-paired-progress.go','world-army-review_main.go']:assert(t/'tools'/n).read_bytes()==(q/'go-src/tools'/n).read_bytes()
        base=read(r/'preserved/alchemy-r1.json');prefix='/alchemy-r1/go-src/tools/'
        for f in base['files']:
            if prefix not in f['path']:continue
            n=f['path'].split(prefix,1)[1]
            if n in ['research-paired-progress.go','world-army-review_main.go']:continue
            assert sha(q/'go-src/tools'/n)==f['sha256'],n
        for n in m.NEW:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n),n
        original_build=read(q/'original-execution-r1.json')
        for n,v in original_build['source_tools'].items():assert sha(q/'original-src'/n)==v
        candidate=read(q/'candidate-r2/receipt.json');assert candidate['status']=='passed-summon-candidate'and candidate['seed']==original['seed']and len(candidate['cases'])==4;old={v['name']:v for v in original['cases']};cases=[]
        for v in candidate['cases']:
            name=v['name'];folder=q/'candidate-r2'/name;before=memory(q/'decoded-candidate-r2'/name,'before.state');after=memory(q/'decoded-candidate-r2'/name,'after.state');assert struct.unpack_from('<I',before,ds+0x81bc)[0]==original['seed'];assert before[ds+0x54a:ds+0x562]==after[ds+0x54a:ds+0x562]
            if name=='unavailable':
                assert v['rejected']and'unavailable or mismatched'in v['error']and before==after;assert word(after,ds+0x2b2c)==saved((folder/'session/gamedata.ay').read_bytes(),1256)==0;cases.append(dict(name=name,rejected=True,ram_unchanged=True));continue
            b=read(folder/'before-pair.json');current=read(folder/'after-pair.json');expected=json.loads(json.dumps(b['world']));kind,count=payload(v['roll'],v['rank'],v['bonus']);assert kind==old[name]['kind']==v['kind']and count==old[name]['count']==v['count'];uid='native:%02d'%kind;slot=next((i for i,s in enumerate(expected['army']['slots'])if s['unit']==uid),-1)
            if slot<0:slot=next((i for i,s in enumerate(expected['army']['slots'])if s['unit']==''),-1)
            if slot>=0:expected['army']['slots'][slot]['unit']=uid;expected['army']['slots'][slot]['count']+=count
            expected['revision']+=1;assert current['world']==v['cold_world']==expected;assert v['go']['result']==dict(Kind=kind,Count=count,Slot=slot,Joined=slot>=0)and v['go']['casts']==1 and v['go']['repeat_rejected'];assert v['roll']==old[name]['roll']and v['seed_after']==old[name]['seed_after']==struct.unpack_from('<I',after,ds+0x81bc)[0]
            raw=(folder/'after-native.ay').read_bytes();source=(q/'original-r1'/name/'after-native.ay').read_bytes();assert len(raw)==2987 and raw[:12]+raw[36:]==source[:12]+source[36:];assert all(saved(raw,12+i*2)==word(before,ds+0x54a+i*2)==v['native_army_after'][i]for i in range(12));assert sha(folder/'after-native.ay')==v['native_sha256'];assert word(before,ds+0x2b2c)==2 and word(after,ds+0x2b2c)==saved(raw,1256)==1;assert saved(raw,1328)==int(v['bonus'])and saved(raw,1316)==1
            for i,key in enumerate(['rank','merit','monthly_pay','gold','leadership','spell_power']):assert saved(raw,i*2)==v['before'][key]==v['after'][key]==word(after,ds+0x4f2+i*2)
            envelope=read(folder/'session/gamedata.ay.army.json');assert envelope['schema']=='eightsword-owned-world-save/4'and envelope['world']==expected and not envelope.get('resume')and envelope['original_sha256']==sha(folder/'after-native.ay');assert len(envelope['native_files'])==9 and all(len(base64.b64decode(x))==5761 for x in envelope['native_files'].values())
            if name=='merge':
                assert v['go']['fault_intent_durable'];assert(folder/'session-fault/gamedata.ay').read_bytes()==raw;assert(folder/'session-fault/gamedata.ay.army.json').read_bytes()==(folder/'session/gamedata.ay.army.json').read_bytes()
            cases.append(dict(name=name,kind=kind,count=count,slot=slot,joined=slot>=0,uses=1,native_sha256=v['native_sha256'],outside_24_army_bytes_same_as_original=True,native_shadow_unchanged=True,repeat_rejected=True))
        gui=read(q/'gui-r2/receipt.json');assert gui['status']=='passed-summon-ui-cold'and gui['initial_army_access_and_uses_fixture']and gui['ordinary_f4_and_choice']and not gui['ram_or_ip_injected']and not gui['f7_used'];assert gui['returned']['world']==gui['army']['world']==gui['cold']['world']==gui['cold_army']['world'];assert gui['returned']['pair_token']==gui['cold']['pair_token'];assert gui['initial']['summon']['uses']==2 and gui['returned']['summon']['uses']==gui['cold']['summon']['uses']==1 and gui['cold']['summon']['casts']==0;assert gui['returned']['world']['army']['gold']==gui['initial']['world']['army']['gold']==500
        expected=json.loads(json.dumps(gui['initial']['world']));aw=gui['outcome']['summon']['award'];kind,count=payload(aw['Roll'],expected['progress']['rank'],aw['Bonus']);rr=gui['outcome']['summon']['result'];assert rr['Kind']==kind and rr['Count']==count and rr['Joined'];slot=rr['Slot'];expected['army']['slots'][slot]['unit']='native:%02d'%kind;expected['army']['slots'][slot]['count']+=count;expected['revision']+=1;assert gui['returned']['world']==expected;assert expected['army']['slots'][1]==gui['initial']['world']['army']['slots'][1]==dict(unit='openkb:wolf',count=5);frames=[]
        for f in gui['screens']:
            folder=q/'gui-r2'/f['phase'];meta=read(folder/f['metadata']);im=Image.open(folder/f['screen']).convert('RGBA');digest=hashlib.sha256(im.tobytes()).hexdigest();assert digest==meta['canvas_sha256']==meta['presented_sha256']and im.tobytes()==Image.open(folder/f['canvas']).convert('RGBA').tobytes();assert meta['native_rows_hex']==gui['initial']['native_rows_hex']
            for t in meta['text_fields']or[]:
                x,y,xx,yy=t['Rect'];a1,b1,a2,b2=t['Ink'];assert not t['Ellipsized']and(t['Ink']==[0,0,0,0]or(x<=a1<=a2<=xx and y<=b1<=b2<=yy))
            frames.append(dict(phase=f['phase'],name=f['name'],rgba_sha256=digest))
        assert len(frames)==3
        result.update(status='passed-summon-candidate',candidate_cases=cases,intent_durable_recovery=True,verified_x11_frames=frames,gui_result=rr,source_tools={n:sha(r/'tools'/n)for n in m.NEW},binaries={n:sha(q/n)for n in['summon-original','summon-candidate','summon-ui','xcheck']},previous_alchemy_sources_unchanged=True,production_promoted=False,limits=['Controlled F4 entries and native/owned army, rank, access flag, charges, bonus and source counter fixtures.','Normal GUI Continue/F4/original choice/acknowledgement/F2 and new-process cold read; no GUI RAM/IP/seed injection.','Owned army keeps unique string IDs, uint32 counts and existing leadership validation; native overflows and duplicate native kinds are outside parity.','Fixed source EB05 at runtime 6249 bypasses the unused validation branch; no invented counter restriction. Other story consumers and formal integration remain pending.','Formal 197 sources, seven programs, 923 core, r69 assets and the pre-DOS sidecar guard remain unchanged.'])
    assert not a.out.exists();a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
