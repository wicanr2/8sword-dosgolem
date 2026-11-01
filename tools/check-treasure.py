#!/usr/bin/env python3
"""Read original/Go chest states and files independently of the executors."""
import argparse,base64,gzip,hashlib,importlib.util,json,os,struct,tempfile
from pathlib import Path
from PIL import Image
REL='workplace/probe-20261023/graphics-first/battle-r1/story-resources-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def word(b,at):return struct.unpack_from('<H',b,at)[0]
def saved(b,at):return(word(b,at)-at-3)&65535
def memory(folder,name):
    meta=read(folder/'index.json')[name];b=gzip.decompress((folder/meta['memory_file']).read_bytes());assert hashlib.sha256(b).hexdigest()==meta['memory_sha256'];return b
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--original-only',action='store_true');a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000;r=a.project;q=r/REL;sp=importlib.util.spec_from_file_location('prep',r/'tools/prepare-treasure.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);h=m.helper(r);deps=h.dependencies(r);assert deps==read(q/'baseline.json');pam=(q/'inputs/PAM.AY').read_bytes();header=word(pam,8)*16;relocs=[header+word(pam,word(pam,24)+i*4+2)*16+word(pam,word(pam,24)+i*4)for i in range(word(pam,6))];ida=read(q/'ida2/ida-story-resources-r1.json');assert sha(q/'inputs/PAM.AY')==ida['source_sha256'];assert sha(r/'tools/export-story-resources-ida.py')==ida['exporter_sha256'];lines=0
    for f in ida['functions']:
        for v in f['lines']:
            at=v['file_offset'];want=bytes.fromhex(v['bytes']);assert at==v['ida_linear']-0x10000+header;b=bytearray(pam[at:at+len(want)])
            for off in relocs:
                if at<=off and off+2<=at+len(want):struct.pack_into('<H',b,off-at,(word(b,off-at)+0x1000)&65535)
            assert bytes(b)==want,(f['name'],at);lines+=1
    input_ram=memory(q/'decoded-input-r1','before-commit.state');native=(q/'inputs/original-save.ay').read_bytes();assert all(saved(native,1348+i*2)==word(input_ram,0x1e880+0x4490+i*2)for i in range(80));orig=read(q/'original-r1/receipt.json');assert orig['seed']==0x12345678 and len(orig['cases'])==7;checked=0
    for v in orig['cases']:
        name=v['name'];before=memory(q/'decoded-original-r1'/name,'before.state');after=memory(q/'decoded-original-r1'/name,'after.state');n=(q/'original-r1'/name/'after-native.ay').read_bytes();assert len(n)==2987 and n[12:36]==native[12:36];assert v['native_sha256']==sha(q/'original-r1'/name/'after-native.ay');expected=dict(v['before']);awarded=v['choice']in[1,2]and v['amount']>0
        if awarded:
            field='gold'if v['choice']==1 else'leadership';total=expected[field]+(v['amount']if v['choice']==1 else v['amount']//10);value=total&65535;expected[field]=0 if value>=32768 else min(30000,value)
        assert v['after']==expected,(name,v['after'],expected)
        for i,key in enumerate(['rank','merit','monthly_pay','gold','leadership','spell_power']):assert saved(n,i*2)==expected[key]==word(after,0x1e880+0x4f2+i*2)
        for i in range(80):
            want=0 if i==0 and awarded else word(before,0x1e880+0x4490+i*2);assert saved(n,1348+i*2)==want==word(after,0x1e880+0x4490+i*2);checked+=1
    result=dict(status='passed-original-treasure-evidence',dependencies=deps,ida_lines=lines,original_treasure_words=checked,original_input_words=80,original_cases=orig['cases'],original_seed=0x12345678,formal_changed=False)
    if not a.original_only:
        assert all(sha(q/'go-src'/n)==v for n,v in deps['source_inputs'].items())
        with tempfile.TemporaryDirectory()as td:
            t=Path(td);(t/'tools').mkdir()
            for n in ['research-paired-progress.go','world-army-review_main.go']:(t/'tools'/n).write_bytes(h.stored(r,'monthly-wide-r1','/monthly-wide-r1/go-src/tools/'+n))
            m.patch(t)
            for n in ['research-paired-progress.go','world-army-review_main.go']:assert(t/'tools'/n).read_bytes()==(q/'go-src/tools'/n).read_bytes()
        for n in m.NEW:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n),n
        candidate=read(q/'candidate-r2/receipt.json');assert candidate['seed']==orig['seed']and len(candidate['cases'])==7;cases=[];old={v['name']:v for v in orig['cases']};candidate_words=0
        for v in candidate['cases']:
            name=v['name'];folder=q/'candidate-r2'/name;b=read(folder/'before-pair.json');after=read(folder/'after-pair.json');expected=json.loads(json.dumps(b['world']));awarded=v['choice']in[1,2]and v['amount']>0
            if awarded:
                field='gold'if v['choice']==1 else'leadership';expected['army'][field]=min(30000,expected['army'][field]+(v['amount']if v['choice']==1 else v['amount']//10));expected['revision']+=1
            assert v['world']==after['world']==expected;assert v['awards']==int(awarded);assert v['seed']==old[name]['seed']and v['keys']==old[name]['keys'];raw=(folder/'after-native.ay').read_bytes();source=(q/'original-r1'/name/'after-native.ay').read_bytes();assert raw[12:]==source[12:];assert raw[12:36]==native[12:36]and raw[36:1236]==native[36:1236]
            if name!='gold-wrap':assert raw==source
            else:assert saved(raw,6)==30000 and saved(source,6)==0 and raw[:6]+raw[8:]==source[:6]+source[8:]
            before_ram=memory(q/'decoded-candidate-r2'/name,'before.state');after_ram=memory(q/'decoded-candidate-r2'/name,'after.state')
            for i in range(80):
                want=0 if i==0 and awarded else word(before_ram,0x1e880+0x4490+i*2);assert saved(raw,1348+i*2)==want==word(after_ram,0x1e880+0x4490+i*2);candidate_words+=1
            if awarded:
                saved_world=read(folder/'session/gamedata.ay.army.json');assert saved_world['schema']=='eightsword-owned-world-save/4'and saved_world['world']==expected and not saved_world.get('resume');assert saved_world['original_sha256']==sha(folder/'after-native.ay');assert len(saved_world['native_files'])==9
                for value in saved_world['native_files'].values():assert len(base64.b64decode(value))==5761
            else:assert b['token']==after['token']
            cases.append(dict(name=name,resources=v['after'],award_count=v['awards'],native_sha256=sha(folder/'after-native.ay'),seed=v['seed']))
        faults=read(q/'faults-r1/receipt.json');assert faults['status']=='passed-treasure-faults'and faults['refusals']==8;assert[(v['gold'],v['amount'])for v in faults['faults']]==[(500,500),(1000,0),(1000,0),(1000,0)]
        gui=read(q/'gui-r1/receipt.json');assert gui['status']=='passed-treasure-ui-cold'and gui['controlled_initial_position']and gui['ordinary_movement_and_choice']and not gui['f7_used'];assert gui['returned']['world']==gui['army']['world']==gui['cold']['world']==gui['cold_army']['world'];assert gui['returned']['pair_token']==gui['cold']['pair_token'];assert gui['initial']['world']['army']['gold']==500 and gui['returned']['world']['army']['gold']==550;assert gui['initial']['treasure']['values'][0]==50 and gui['returned']['treasure']['values'][0]==gui['cold']['treasure']['values'][0]==0;assert gui['returned']['treasure']['values'][1:]==gui['initial']['treasure']['values'][1:];assert gui['returned']['world']['army']['slots']==gui['initial']['world']['army']['slots'];assert gui['cold']['treasure']['awards']==0;frames=[]
        for frame in gui['screens']:
            folder=q/'gui-r1'/frame['phase'];meta=read(folder/frame['metadata']);im=Image.open(folder/frame['screen']).convert('RGBA');digest=hashlib.sha256(im.tobytes()).hexdigest();assert digest==meta['canvas_sha256']==meta['presented_sha256'];assert im.tobytes()==Image.open(folder/frame['canvas']).convert('RGBA').tobytes();assert meta['native_rows_hex']==gui['initial']['native_rows_hex']
            for t in meta['text_fields']or[]:
                x,y,xx,yy=t['Rect'];a1,b1,a2,b2=t['Ink'];assert not t['Ellipsized']and(t['Ink']==[0,0,0,0]or(x<=a1<=a2<=xx and y<=b1<=b2<=yy))
            frames.append(dict(phase=frame['phase'],name=frame['name'],rgba_sha256=digest))
        result.update(status='passed-treasure-candidate',candidate_treasure_words=candidate_words,candidate_cases=cases,faults=faults,verified_x11_frames=frames,source_tools={n:sha(r/'tools'/n)for n in m.NEW},binaries={n:sha(q/n)for n in['treasure-original','treasure-candidate','treasure-faults','treasure-ui','treasure-ui-fixture']},production_promoted=False,limits=['Controlled dispatcher fixtures and GUI initial position/army; ordinary GUI movement and original choice.','Gold over signed-word native domain uses safe capped Go arithmetic and intentionally differs from native wrap.','Only chest gold/leadership and the one-time record are integrated; other story and spell resources remain outside this slice.','Formal engine guard, 197 source files, seven programs, 923 core and r69 assets remain unchanged.'])
    assert not a.out.exists();a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
