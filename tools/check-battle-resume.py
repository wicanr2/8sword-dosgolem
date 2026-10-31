#!/usr/bin/env python3
"""Independently check frozen source, raw VM evidence and actual X11 frames."""
import argparse,base64,gzip,hashlib,importlib.util,json,os,struct,tempfile
from pathlib import Path
from PIL import Image
REL='workplace/probe-20261023/graphics-first/battle-r1/battle-resume-r1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
    r=a.project;q=r/REL;spec=importlib.util.spec_from_file_location('candidate',r/'tools/prepare-battle-resume.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);h=m.helper(r);deps=h.dependencies(r);assert deps==read(q/'baseline.json')
    # Rebuild every inherited tool from the prior permanent batch and apply
    # only this candidate's declared patches. Formal sources stay byte-identical.
    assert all(sha(q/'go-src'/n)==v for n,v in deps['source_inputs'].items())
    d=read(r/'preserved/native-checkpoint-r1.json');inherited=[]
    with tempfile.TemporaryDirectory()as td:
        root=Path(td);(root/'tools').mkdir()
        for f in d['files']:
            marker='/go-src/tools/'
            if marker not in f['path']:continue
            n=f['path'].split(marker,1)[1];(root/'tools'/n).write_bytes(h.stored(r,'native-checkpoint-r1',marker+n));inherited.append(n)
        m.patch(root)
        for n in inherited:
            if n not in m.NEW:assert(root/'tools'/n).read_bytes()==(q/'go-src/tools'/n).read_bytes(),n
    for n in m.NEW:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n),n
    core=hashlib.sha256(json.dumps(deps['core_files'],sort_keys=True,separators=(',',':')).encode()).hexdigest();execution=read(q/'resume-execution-r1.json');assert execution['core_sha256']==core
    probe=read(q/'probe-r3/receipt.json');assert probe['status']=='passed-battle-resume-cold-engine'
    assert probe['saved_world']==probe['cold_world']and probe['return_world']['battle']is None
    assert probe['native_calls']==0 and probe['warm_return_seed']==probe['cold_return_seed']
    before=probe['seed_before_retreat'];after=(before*214013+2531011)&0xffffffff;value=(after>>16)&32767
    assert after==probe['seed_after_retreat']
    gold=probe['saved_world']['army']['gold'];assert probe['return_world']['army']['gold']==gold-gold//(value//2730+3)
    survivors=[v for v in probe['saved_world']['battle']['state']['rows'][0]if v['count']>0]
    survivors += [dict(unit='',count=0)]*(6-len(survivors));assert probe['return_world']['army']['slots']==survivors
    assert len(probe['faults'])==4 and all(v['recovered']for v in probe['faults'])
    assert probe['faults'][0]['active_battle']is False and probe['missing_object_rejected']and probe['corrupt_codec_rejected']and probe['double_settlement_rejected']
    # Standalone gob reader exposes raw memory without executing the guest.
    decoded=read(q/'decoded-r3/index.json');ram={}
    for name,v in decoded.items():
        raw=gzip.decompress((q/'decoded-r3'/v['memory_file']).read_bytes());assert len(raw)==1<<20 and hashlib.sha256(raw).hexdigest()==v['memory_sha256'];ram[name]=raw
    held=ram['held.state'];cold=ram['cold-held.state'];assert held==cold
    pam=(q/'inputs/PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
    word=lambda at:struct.unpack_from('<H',pam,at)[0];code=bytearray(pam[word(8)*16:])
    for i in range(word(6)):
        at=word(24)+i*4;off=word(at+2)*16+word(at);struct.pack_into('<H',code,off,(struct.unpack_from('<H',code,off)[0]+0x110)&65535)
    for lo,hi in [(0x151c,0x1796),(0x32e0,0x3774),(0x1953e,0x19566)]:assert code[lo:hi]==held[0x1100+lo:0x1100+hi]
    assert decoded['held.state']['registers']==decoded['cold-held.state']['registers']and decoded['held.state']['segments']==decoded['cold-held.state']['segments']
    assert decoded['held.state']['ip']==decoded['cold-held.state']['ip']==0x32e0
    assert struct.unpack_from('<I',held,0x26a3c)[0]==before
    locations=[0x56c4,0x56ca,0x56cc,0x56ce,0x56d0,0x56d2,0x56d6,0x56dc,0x8e12,0x8e44]
    raw_return={name:[struct.unpack_from('<H',ram[name],0x1e880+o)[0]for o in locations]for name in ['first-return.state','cold-return.state']}
    assert raw_return['first-return.state']==raw_return['cold-return.state']==probe['native_location']
    for name in ['first-return.state','cold-return.state']:
        assert ram[name][0x1edca:0x1ede2]==held[0x1edca:0x1ede2]
        assert struct.unpack_from('<I',ram[name],0x26a3c)[0]==probe['warm_return_seed']
    opening=read(q/'opening-test-r1/receipt.json');assert opening['status']=='passed-atomic-pursuit-opening'and opening['cold_equal']and opening['ordinary_unchanged']and len(opening['actions'])>0
    gui=read(q/'gui-r2/receipt.json');assert gui['status']=='passed-battle-resume-ui-cold'
    assert gui['saved']['world']==gui['cold']['world']and gui['saved']['pair_token']==gui['cold']['pair_token']
    assert gui['returned']['world']==gui['replayed']['world']and gui['returned']['pair_token']==gui['replayed']['pair_token']
    assert gui['checkpoint']['world']==gui['final']['world']
    pixels=[]
    for s in gui['screens']:
        folder=q/'gui-r2'/s['phase'];im=Image.open(folder/s['canvas']).convert('RGBA');screen=Image.open(folder/s['screen']).convert('RGB');meta=read(folder/s['metadata']);assert im.size==(1920,1200)and im.convert('RGB').tobytes()==screen.tobytes();assert hashlib.sha256(im.tobytes()).hexdigest()==meta['canvas_sha256']==meta['presented_sha256'];pixels.append(s)
    # UI selection/message are transient, so compare world state and verify
    # each drawn frame; do not demand identical pre/post transient text.
    pair=read(q/'session-gui-r2/gamedata.ay.army.json');assert pair['schema']=='eightsword-owned-world-save/2'and'native_resume'not in pair
    for n,v in pair['native_files'].items():assert len(base64.b64decode(v,validate=True))==5761
    write(a.out,dict(status='passed-battle-resume-candidate',probe=probe,gui=gui,opening=opening,independent_ram_equal=True,raw_return_location=raw_return,verified_x11_frames=len(pixels),dependencies=deps,source_tools={n:sha(r/'tools'/n)for n in m.NEW},formal_changed=False,format_promoted=False,scope='Controlled warm start; actual UI cold Continue, retreat, return replay, F7 and F2. No natural encounter or complete-game claim.'))
if __name__=='__main__':main()
