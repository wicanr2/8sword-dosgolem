#!/usr/bin/env python3
"""Independently audit source bytes, raw states, save words and displayed frames."""
import argparse,base64,gzip,hashlib,importlib.util,json,os,struct,tempfile
from pathlib import Path
from PIL import Image
REL='workplace/probe-20261023/graphics-first/battle-r1/monthly-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def word(b,at):return struct.unpack_from('<H',b,at)[0]
def saved(b,at):return(word(b,at)-at-3)&65535
def camp(b,g,row):return[saved(b,36+row*50+f*10+g*2)for f in range(5)]
def state(q,name,file):
    d=q/'decoded-r1'/name;v=read(d/'index.json')[file];b=gzip.decompress((d/v['memory_file']).read_bytes());assert hashlib.sha256(b).hexdigest()==v['memory_sha256'];return b
def resources(w):return[w['progress']['rank'],w['progress']['merit'],w['progress']['legacy_04f6'],w['army']['gold'],w['army']['leadership'],w['progress']['legacy_04fc']]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
    r=a.project;q=r/REL;sp=importlib.util.spec_from_file_location('prep',r/'tools/prepare-monthly.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);h=m.helper(r);deps=h.dependencies(r);assert deps==read(q/'baseline.json');assert all(sha(q/'go-src'/n)==v for n,v in deps['source_inputs'].items())
    with tempfile.TemporaryDirectory()as td:
        t=Path(td);(t/'tools').mkdir()
        for n in ['research-paired-progress.go','world-army-review_main.go']:(t/'tools'/n).write_bytes(h.stored(r,'openkb-hd-r1','/openkb-hd-r1/go-src/tools/'+n))
        m.patch(t)
        for n in ['research-paired-progress.go','world-army-review_main.go']:assert(t/'tools'/n).read_bytes()==(q/'go-src/tools'/n).read_bytes()
    for n in m.NEW:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n),n
    pam=(q/'inputs/PAM.AY').read_bytes();ida=read(q/'ida/ida-monthly-r1.json');assert sha(q/'inputs/PAM.AY')==ida['source_sha256'];assert sha(r/'tools/export-monthly-ida.py')==ida['exporter_sha256'];header=word(pam,8)*16;relocs=[word(pam,word(pam,24)+i*4+2)*16+word(pam,word(pam,24)+i*4)for i in range(word(pam,6))];lines=0
    for f in ida['functions']:
        for l in f['lines']:
            pos=l['file_offset'];want=bytes.fromhex(l['bytes']);b=bytearray(pam[pos:pos+len(want)]);assert pos==l['ida_linear']-0x10000+header
            for off in relocs:
                if pos<=header+off and header+off+2<=pos+len(want):struct.pack_into('<H',b,header+off-pos,(word(b,header+off-pos)+0x1000)&65535)
            assert bytes(b)==want,(f['name'],pos);lines+=1
    code=pam[header:];caps=[word(code,0x1d780+0x3a56+g*240+row*10)for g in range(5)for row in range(24)];catalog=read(q/'inputs/army-catalog.json')['profiles'];fees={v['id']:v['gold']for v in catalog};assert all(v['gold']==word(code,0x1d780+0x2986+v['native_kind']*2)for v in catalog if v.get('native_kind',0))
    original=read(q/'original-r1/receipt.json');assert original['seed']==0x12345678 and original['caps']==caps and len(original['cases'])==7;checked=0
    expectations={'paid':(570,False),'exact':(0,False),'disband':(1,True),'cap':(30000,False),'no-month':(500,False),'word-expense-wrap':(16136,False),'word-income-wrap':(0,True)}
    for case in original['cases']:
        name=case['name'];before=state(q,'original-'+name,'before.state');after=state(q,'original-'+name,'after.state');gold,disband=expectations[name];assert word(after,0x1e880+0x4f8)==case['gold']==gold;assert after[0x1e880+0x54a:0x1e880+0x562].hex()==case['army_hex'];assert case['model_rejected']==name.startswith('word-');assert word(after,0x1e880+0x56da)==case['counter']==(1 if name=='no-month'else 324)
        for g in range(5):
            for row in range(24):
                at=0x1e880+0x3efe+g*240+row*10;kind,stock=word(before,at+6),word(before,at+8);expected=stock if name=='no-month'or not kind else min(stock+max(stock//10,10),caps[g*24+row]);assert word(after,at+8)==expected;assert before[at:at+8]==after[at:at+8];checked+=1
        if name!='no-month':
            native=(q/'original-r1'/name/'serialized.ay').read_bytes();assert len(native)==2987
            assert saved(native,6)==gold
            for g in range(5):
                for row in range(24):assert camp(native,g,row)==[word(after,0x1e880+0x3efe+g*240+row*10+f*2)for f in range(5)]
    candidate=read(q/'candidate-r1/receipt.json');assert candidate['seed']==original['seed']and candidate['wide_budget_rejected'];assert [(v['gold'],v['stock'])for v in candidate['faults']]==[(500,2900),(370,3000),(370,3000),(370,3000)]
    candidates=[]
    for case in candidate['cases']:
        name=case['name'];folder=q/'candidate-r1'/name;b=case['before']['world'];w=case['after']['world'];budget=case['budget'];due=sum(fees[s['unit']]*s['count']for s in b['army']['slots']if s['count']);total=b['army']['gold']+b['progress']['legacy_04f6'];disband=due>total;assert budget['Due']==due and budget['Disbanded']==disband;assert w['army']['gold']==min(30000,total-(0 if disband else due));assert w['revision']==b['revision']+1;assert w['army']['slots']==([{'unit':'','count':0}]*6 if disband else b['army']['slots']);assert w['army']['offers']['native-camp:00:01']['stock']==3000
        native=(folder/'after-native.ay').read_bytes();held=state(q,'candidate-'+name,'held.state');before=state(q,'candidate-'+name,'before.state');assert native[12:36]==(q/'inputs/original-save.ay').read_bytes()[12:36];assert len(native)==2987
        for i,v in enumerate(resources(w)):assert saved(native,i*2)==v==word(held,0x1e880+0x4f2+i*2)
        for g in range(5):
            for row in range(24):
                at=0x1e880+0x3efe+g*240+row*10;old=word(before,at+8);expected=min(old+max(old//10,10),caps[g*24+row])if word(before,at+6)else old;assert camp(native,g,row)==[word(held,at+f*2)for f in range(5)];assert word(held,at+8)==expected;assert before[at:at+8]==held[at:at+8];checked+=1
        assert held[0x1e880+0x54a:0x1e880+0x562]==before[0x1e880+0x54a:0x1e880+0x562];envelope=read(folder/'session/gamedata.ay.army.json');assert envelope['schema']=='eightsword-owned-world-save/4'and not envelope.get('resume');assert envelope['world']==w and envelope['original_sha256']==sha(folder/'after-native.ay');assert len(envelope['native_files'])==9
        for n,raw in envelope['native_files'].items():assert base64.b64decode(raw)==(folder/'evidence/month-001'/n).read_bytes()
        assert case['saves']==1 and case['seed']==original['cases'][0]['seed'];candidates.append(dict(name=name,due=due,gold=w['army']['gold'],native_sha256=sha(folder/'after-native.ay')))
    # Same controlled origin and RNG, original-only units: all opaque serializer
    # fields and all NPC garrisons agree; only deliberately set resources differ.
    native=(q/'candidate-r1/native/after-native.ay').read_bytes();source=(q/'original-r1/paid/serialized.ay').read_bytes();assert native[12:]==source[12:]
    gui=read(q/'gui-r1/receipt.json');assert gui['status']=='passed-monthly-ui-cold'and gui['controlled_countdown']and gui['ordinary_continue_and_movement']and not gui['f7_used'];assert gui['cold']['world']==gui['returned']['world']==gui['report']['world'];assert gui['cold']['pair_token']==gui['returned']['pair_token'];assert gui['cold']['monthly']['saves']==0 and gui['report']['monthly']['saves']==1;assert gui['initial']['native_rows_hex']==gui['returned']['native_rows_hex']==gui['cold']['native_rows_hex'];frames=[]
    for frame in gui['screens']:
        folder=q/'gui-r1'/frame['phase'];meta=read(folder/frame['metadata']);im=Image.open(folder/frame['screen']).convert('RGBA');digest=hashlib.sha256(im.tobytes()).hexdigest();assert digest==meta['canvas_sha256']==meta['presented_sha256'];assert im.tobytes()==Image.open(folder/frame['canvas']).convert('RGBA').tobytes();frames.append(dict(phase=frame['phase'],screen=frame['screen'],rgba_sha256=digest))
    result=dict(status='passed-monthly-bounded-candidate',dependencies=deps,source_tools={n:sha(r/'tools'/n)for n in m.NEW},binaries={n:sha(q/n)for n in ['monthly-original','monthly-candidate','monthly-ui','monthly-ui-fixture']},ida_lines=lines,independently_checked_camp_records=checked,original_cases=original['cases'],candidate_cases=candidates,faults=candidate['faults'],verified_x11_frames=frames,formal_changed=False,production_promoted=False,limits=['Controlled source dispatcher states and one controlled countdown; ordinary GUI Continue and movement.','Fees for eight openKB units are a prototype using their existing recruitment Gold values.','Signed-word UI domain only; excessive budgets reject before projection.','NPC garrisons, calendar and detached save serialization retain native code. Formal sidecar guard remains.'])
    with a.out.open('x')as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
if __name__=='__main__':main()
