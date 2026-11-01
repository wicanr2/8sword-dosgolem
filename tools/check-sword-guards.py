#!/usr/bin/env python3
"""Independent original bytes, sword serialization and Go GUI receipt audit."""
import argparse,copy,hashlib,importlib.util,json,os,struct,tempfile
from pathlib import Path
from PIL import Image
REL='workplace/probe-20261023/graphics-first/battle-r1/sword-guards-r1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def module(p,n):
    sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
def original(r,q):
    m=module(r/'tools/check-annihilation-origin.py','original');pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0';lines=sum(m.source_lines(pam,read(q/'inputs'/n))for n in['ida-guard-world.json','ida-guard-rewards.json','ida-save.json'])
    ending=read(q/'inputs/ida-ending-handoff.json');converted=copy.deepcopy(ending['bodies'])
    for f in converted:
        for x in f['lines']:x['file_offset']=x['original_file_offset']
    lines+=m.source_lines(pam,dict(functions=converted));layout=read(q/'mapping-r2/receipt.json');raw=(q/'mapping-r2/scratch/gamedata.ay').read_bytes();assert layout['offsets']==list(range(1318,1350,4))
    for i,at in enumerate(layout['offsets']):assert(struct.unpack_from('<H',raw,at)[0]-at-3)&65535==0x6000+i
    coords=[list(struct.unpack_from('<HH',pam,0x1470+0x1e880+0x26bc-0x1100+i*6))for i in range(8)];assert coords==layout['boss_coordinates']==[[48,5],[27,69],[29,77],[32,62],[53,54],[35,72],[18,58],[61,76]]
    guard=next(f for f in read(q/'inputs/ida-guard-world.json')['functions']if f['name']=='sub_12DDE');bytes_at={x['ida_linear']:x['bytes']for x in guard['lines']};assert bytes_at[0x13295]=='c706e2560100'and bytes_at[0x1329c]=='e86fcf'and bytes_at[0x1329b]=='0e'
    return dict(status='passed-sword-and-ending-original-evidence',ida_lines=lines,source_serializer_words=8,sword_offsets=layout['offsets'],boss_coordinates=coords,ending_call='0110:329B -> 0110:020E',full_original_battle=False)
def flags(raw):return [(struct.unpack_from('<H',raw,1318+i*4)[0]-1321-i*4)&65535 for i in range(8)]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--original-only',action='store_true');a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000;r=a.project;q=r/REL;proof=original(r,q)
    if a.original_only:result=proof
    else:
        prep=module(r/'tools/prepare-sword-guards.py','prep');h=prep.helper(r);deps=h.dependencies(r);assert deps==read(q/'baseline.json')
        for n,v in deps['source_inputs'].items():assert sha(q/'go-src'/n)==v
        with tempfile.TemporaryDirectory()as td:
            t=Path(td);(t/'tools').mkdir()
            for n in prep.PATCHED:(t/'tools'/n).write_bytes(h.stored(r,prep.PARENT,'/'+prep.PARENT+'/go-src/tools/'+n))
            prep.patch(t)
            for n in prep.PATCHED:assert(t/'tools'/n).read_bytes()==(q/'go-src/tools'/n).read_bytes()
        assets=0
        for f in read(r/'preserved/guarded-battle-r1.json')['files']:
            rel=f['path'].split('/guarded-battle-r1/',1)[1]
            if rel.startswith('go-src/')and rel[7:]not in['tools/'+n for n in prep.PATCHED+prep.NEW]:assert sha(q/rel)==f['sha256']
            if rel.startswith('ui-assets/'):assert sha(q/rel)==f['sha256'];assets+=1
        for n in prep.NEW:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n),n
        index=read(r/'docs/spec/world-army-consumers-r1.json');links=0
        for f in index['functions']:
            if f['original_name']not in['sub_12DDE','sub_132E0','sub_11ABE']:continue
            v=next(v for v in f['resolution']['followups']if v['evidence_receipt']=='preserved/sword-guards-audit-r1.json');assert v['identity']==f['resolution']['identity']and v['identity']['source_sha256']==index['source_sha256'];assert v['required_correction']in(r/v['older_spec']).read_text()and f['original_name']in(r/v['evidence_spec'].split('#')[0]).read_text();links+=1
        v=index['sword_guard_handoff'];assert links==3 and v['identity']['runtime']=='0110:020E'and v['identity']['ida_mz_linear']=='0x1020E'and v['required_correction']in(r/v['older_spec']).read_text()
        model=read(q/'model-r1.json');assert model['status']=='passed-sword-projection-boundaries'and len(model['cases'])==16 and model['ending_no_sword']and model['invalid_flag_refused']
        g=read(q/'gui-r3/receipt.json');assert g['status']=='passed-sword-guards-ui'and g['native_enemies_unmodified']and not g['test_seed'];base=(q/'inputs/original-save.ay').read_bytes();assert flags(base)==[0]*8
        for name,index in[('boss_opened',1),('final_opened',4)]:
            s=g[name];assert s['guarded_binding']['context']['index']==index and s['guarded_binding']['context']['boss']==(index==1)
            for i,row in enumerate(s['world']['battle']['state']['initial'][1]):
                at=1508+index*24+i*4;k,n=[(struct.unpack_from('<H',base,at+j*2)[0]-at-j*2-3)&65535 for j in range(2)];assert row==dict(unit=f'native:{k:02d}'if k else'',count=n)
        for won,returned,key in[('boss_won','boss_return','guarded:00:01'),('final_won','committed','guarded:00:04')]:
            w=copy.deepcopy(g[won]['world']);assert w['battle']['state']['result']=='win';w['army']['slots']=[v for v in w['battle']['state']['rows'][0]if v['count']]+[dict(unit='',count=0)]*sum(not v['count']for v in w['battle']['state']['rows'][0]);w['battle']=None;w['encounters'][key]['cleared']=True;w['revision']+=1;w['progress']['legacy_04f6']+=20;assert w==g[returned]['world'];assert w['army']['gold']==500 and w['progress']['merit']==10000 and w['progress']['rank']==1
        assert g['boss_return']['swords']==g['boss_cold']['swords']==[True]+[False]*7 and g['checkpoint']['world']==g['boss_cold']['world']
        saved=read(q/'session-final-return-r1/gamedata.ay.army.json');assert saved['schema']=='eightsword-owned-world-save/3'and saved['native_resume']['phase']=='return'and saved['native_resume']['result']==0 and saved['world']==g['committed']['world'];raw=(q/'session-final-return-r1/gamedata.ay').read_bytes();assert flags(raw)==[1]*8 and g['final_opened']['swords']==[True]*8
        for i in range(12):at=1508+4*24+i*2;assert(struct.unpack_from('<H',raw,at)[0]-at-3)&65535==0
        assert g['complete']['engine_exited']and g['complete']['engine_exit_code']==0 and g['ending']['ending']['active']and g['ending']['ending']['stage']=='END7.AY';assert g['committed']['world']==g['ending']['world']==g['complete']['world']and g['committed']['pair_token']==g['complete']['pair_token'];assert g['complete']['ending']['direct']and not g['complete']['ending']['error']
        cm=read(q/'cold-model-r1.json');assert cm['status']=='passed-sword-interrupted-cold-return'and cm['duplicate_refused']and cm['unrelated_sword_refused']and cm['flags']==[True]+[False]*7
        assert cm['before']['world']['battle']['state']['result']=='win'and cm['after']['world']['battle']is None
        assert any(t['Role']=='swords'and t['Text']=='八劍: 1 / 8'for t in g['boss_cold']['text_fields'])
        before=(q/'session-before-cold-r1/gamedata.ay').read_bytes();after=(q/'session-won-r1/gamedata.ay').read_bytes();assert flags(before)==[0]*8 and flags(after)==[1]+[0]*7
        for i,(b,c)in enumerate(zip(before,after)):
            if not(i<12 or 1318<=i<1320 or 1532<=i<1556):assert b==c,('unrelated byte',i)
        frames=[]
        for row in g['screens']:
            f=q/row.get('batch','gui-r3')/row['phase'];meta=read(f/row['metadata']);im=Image.open(f/row['screen']).convert('RGBA');hsh=hashlib.sha256(im.tobytes()).hexdigest();assert hsh==meta['canvas_sha256']==meta['presented_sha256']and im.tobytes()==Image.open(f/row['canvas']).convert('RGBA').tobytes()
            for t in meta['text_fields']or[]:
                x,y,xx,yy=t['Rect'];aa,b,c,d=t['Ink'];assert not t['Ellipsized']and(t['Ink']==[0,0,0,0]or x<=aa<=c<=xx and y<=b<=d<=yy)
            if row['name']not in['ending-committed','hd-ending','ending-complete']:assert meta['battle_native_calls']==0 and meta['native_rows_hex']==g['boss_opened']['native_rows_hex']
            frames.append(dict(name=row['name'],rgba_sha256=hsh))
        result=dict(status='passed-sword-guards-limited',original=proof,dependencies=deps,ui_assets_unchanged=assets,images=frames,sword_flags=[1]+[0]*7,ending_completed=True,production_promoted=False,natural_completion=False,source_tool_sha256=sha(r/'tools/check-sword-guards.py'))
    with a.out.open('x')as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
if __name__=='__main__':main()
