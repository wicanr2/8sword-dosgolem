#!/usr/bin/env python3
"""Independently check the saved native words, Go results and X11 samples."""
import argparse,gzip,hashlib,importlib.util,json,os,struct,tempfile
from pathlib import Path
from PIL import Image
REL='workplace/probe-20261023/graphics-first/battle-r1/camp-stock-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
    r=a.project;q=r/REL;sp=importlib.util.spec_from_file_location('prep',r/'tools/prepare-camp-stock.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);h=m.helper(r);deps=h.dependencies(r);assert deps==read(q/'baseline.json')
    assert all(sha(q/'go-src'/n)==v for n,v in deps['source_inputs'].items())
    patched=['research-native-checkpoint.go','research-paired-progress.go','research-battle-resume.go','research-world-army-port.go']
    with tempfile.TemporaryDirectory()as td:
        t=Path(td);(t/'tools').mkdir()
        for n in patched:(t/'tools'/n).write_bytes(h.stored(r,'recruit-icons-r1','/recruit-icons-r1/go-src/tools/'+n))
        m.patch(t)
        for n in patched:assert(t/'tools'/n).read_bytes()==(q/'go-src/tools'/n).read_bytes(),n
    for n in m.NEW:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n),n
    ida=read(q/'inputs/ida-checkpoint-r1.json');pam=(q/'inputs/PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()==ida['source_sha256'];header=struct.unpack_from('<H',pam,8)[0]*16;relocs=[];lines=0
    for i in range(struct.unpack_from('<H',pam,6)[0]):off,seg=struct.unpack_from('<HH',pam,struct.unpack_from('<H',pam,24)[0]+i*4);relocs.append(header+seg*16+off)
    for f in ida['functions']:
        if f['start']not in [0x184c0,0x18d38]:continue
        for l in f['lines']:
            pos=l['file_offset'];want=bytes.fromhex(l['bytes']);b=bytearray(pam[pos:pos+len(want)]);assert pos==l['ida_linear']-0x10000+header
            for off in relocs:
                if pos<=off and off+2<=pos+len(want):struct.pack_into('<H',b,off-pos,(struct.unpack_from('<H',b,off-pos)[0]+0x1000)&65535)
            assert bytes(b)==want;lines+=1
    index=read(q/'state-read-r1/index.json')['before-commit.state'];ram=gzip.decompress((q/'state-read-r1'/index['memory_file']).read_bytes());native=(q/'inputs/original-save.ay').read_bytes();words=0
    for row in range(24):
        for field in range(5):
            for group in range(5):
                at=36+row*50+field*10+group*2;value=(struct.unpack_from('<H',native,at)[0]-at-3)&65535
                assert value==struct.unpack_from('<H',ram,0x1e880+0x3efe+group*240+row*10+field*2)[0];words+=1
    result=read(q/'probe-r2/receipt.json');assert result['status']=='passed-camp-stock-probe'and result['native_changed_offsets']==[6,126]
    assert len(result['refusals'])==5 and len(result['faults'])==4 and len(result['wrappers'])==4
    assert [(v['stock'],v['gold'])for v in result['faults']]==[(1200,5000),(1199,4999),(1199,4999),(1199,4999)]
    states=read(q/'wrapper-state-read-r1/index.json');wrapper_rows=[]
    for i,case in enumerate(result['wrappers']):
        world=read(q/f'probe-r2/wrapper-{i}-pair.json')['world'];meta=states[case['state']];ram=gzip.decompress((q/'wrapper-state-read-r1'/meta['memory_file']).read_bytes());n=(q/f'probe-r2/wrapper-{i}-native.ay').read_bytes()
        assert len(n)==2987 and n[12:36]==native[12:36]
        resources=[world['progress']['rank'],world['progress']['merit'],world['progress']['legacy_04f6'],world['army']['gold'],world['army']['leadership'],world['progress']['legacy_04fc']]
        for j,v in enumerate(resources):assert (struct.unpack_from('<H',n,j*2)[0]-j*2-3)&65535==v==struct.unpack_from('<H',ram,0x1ed72+j*2)[0]
        for j in range(12):assert (struct.unpack_from('<H',native,12+j*2)[0]-15-j*2)&65535==struct.unpack_from('<H',ram,0x1edca+j*2)[0]
        for key,offer in world['army']['offers'].items():
            if not key.startswith('native-camp:'):continue
            _,g,row=key.split(':');g,row=int(g),int(row);at=76+row*50+g*2;assert (struct.unpack_from('<H',n,at)[0]-at-3)&65535==offer['stock']==struct.unpack_from('<H',ram,0x1e880+0x3f06+g*240+row*10)[0]
        assert case['stock_before']-case['qty']==case['stock_after']and case['purchases']==int(case['qty']>0)
        wrapper_rows.append(dict(group=case['group'],row=case['row'],stock=case['stock_after'],gold=world['army']['gold'],memory_sha256=meta['memory_sha256'],native_sha256=sha(q/f'probe-r2/wrapper-{i}-native.ay')))
    assert result['wrappers'][-1]['token']==result['wrappers'][-2]['token']
    resume=result['resume'];assert resume['f7_kept_v4']and resume['identity_failure_preserved_stock']
    before,after=resume['before_purchase']['world'],resume['after_purchase']['world'];assert before['army']['gold']-1==after['army']['gold']
    k='native-camp:00:01';assert before['army']['offers'][k]['stock']-1==after['army']['offers'][k]['stock']==resume['stock_after_restore']
    gui=read(q/'gui-r1/receipt.json');assert gui['status']=='passed-actual-go-camp-stock'and not gui['f7_used']and not gui['memory_injected']
    assert gui['returned']['world']==gui['cold']['world']==gui['revisited']['world']==gui['cancelled']['world']
    assert gui['returned']['pair_token']==gui['cold']['pair_token']==gui['cancelled']['pair_token'];assert gui['stock_before']-1==gui['stock_after']==gui['revisited']['recruit_icons']['stock']
    assert gui['initial']['native_rows_hex']==gui['returned']['native_rows_hex']==gui['cold']['native_rows_hex'];assert gui['army']['review_opens']==1
    x11=[]
    for s in gui['screens']:
        folder=q/'gui-r1'/s['phase'];meta=read(folder/s['metadata']);im=Image.open(folder/s['screen']).convert('RGBA');digest=hashlib.sha256(im.tobytes()).hexdigest();assert digest==meta['canvas_sha256']==meta['presented_sha256'],s
        x11.append(dict(phase=s['phase'],screen=s['screen'],rgba_sha256=digest))
    saved=read(q/'gui-session-r1/gamedata.ay.army.json');n=(q/'gui-session-r1/gamedata.ay').read_bytes();assert saved['schema']=='eightsword-owned-world-save/4'and saved['original_sha256']==hashlib.sha256(n).hexdigest()==gui['native_sha256']
    v=dict(status='passed-go-camp-stock-candidate',dependencies=deps,source_tools={n:sha(r/'tools'/n)for n in m.NEW},binaries={n:sha(q/n)for n in ['camp-probe','camp-ui']},ida_lines=lines,original_camp_words=words,wrapper_rows=wrapper_rows,faults=result['faults'],refusals=result['refusals'],resume=resume,gui=gui,x11=x11,formal_changed=False,production_promoted=False,limits=['Controlled initial Go wolf army; GUI uses ordinary Continue/movement/shop/cold reopen and no RAM injection.','Only native source stock and six resources are autosaved by purchase. Current map position still follows F7.','Monthly/scripted refresh, all remaining army consumers and the eight openKB shop portraits remain outside this slice.','Formal Engine still refuses the owned-army sidecar before DOS. No production schema promotion.'])
    with a.out.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
if __name__=='__main__':main()
