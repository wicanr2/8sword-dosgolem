#!/usr/bin/env python3
"""Independent wide-budget arithmetic, state/save, glyph and X11 checks."""
import argparse,base64,gzip,hashlib,importlib.util,json,os,struct,tempfile
from pathlib import Path
from PIL import Image
REL='workplace/probe-20261023/graphics-first/battle-r1/monthly-wide-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def word(b,at):return struct.unpack_from('<H',b,at)[0]
def saved(b,at):return(word(b,at)-at-3)&65535
def camp(b,g,row):return[saved(b,36+row*50+f*10+g*2)for f in range(5)]
def ram(q,name,file):
    p=q/'decoded-r1'/name;v=read(p/'index.json')[file];raw=gzip.decompress((p/v['memory_file']).read_bytes());assert hashlib.sha256(raw).hexdigest()==v['memory_sha256'];return raw
def inside(a,b):return b[0]<=a[0]<=a[2]<=b[2]and b[1]<=a[1]<=a[3]<=b[3]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
    r=a.project;q=r/REL;sp=importlib.util.spec_from_file_location('prep',r/'tools/prepare-monthly-wide.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);h=m.helper(r);deps=h.dependencies(r);assert deps==read(q/'baseline.json');assert all(sha(q/'go-src'/n)==v for n,v in deps['source_inputs'].items())
    with tempfile.TemporaryDirectory()as td:
        t=Path(td);(t/'tools').mkdir()
        for n in m.PATCHED:(t/'tools'/n).write_bytes(h.stored(r,'monthly-r1','/monthly-r1/go-src/tools/'+n))
        m.patch(t)
        for n in m.PATCHED:assert(t/'tools'/n).read_bytes()==(q/'go-src/tools'/n).read_bytes(),n
    for n in m.NEW:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n),n
    original=read(r/'preserved/monthly-audit-r1.json');assert original['status']=='passed-monthly-bounded-candidate';source_control=json.loads(h.stored(r,'monthly-r1','/monthly-r1/original-r1/receipt.json'));caps=source_control['caps'];fees={p['id']:p['gold']for p in read(q/'inputs/army-catalog.json')['profiles']};native_rows=(q/'inputs/original-save.ay').read_bytes()[12:36]
    proof=read(q/'candidate-r1/receipt.json');assert proof['wide_budget_supported']and proof['seed']==0x12345678;assert len(proof['cases'])==6 and len(proof['rule_cases'])==6;assert [(v['gold'],v['stock'])for v in proof['faults']]==[(500,2900),(370,3000),(370,3000),(370,3000)];cases=[];checked=0
    expected={'native':(30,570,False),'mixed':(230,370,False),'bankrupt':(230,100,True),'large':(100030,600,True),'wide-paid':(39990,10,False),'wide-income':(230,30000,False)}
    for case in proof['cases']:
        name=case['name'];d=q/'candidate-r1'/name;b=case['before']['world'];w=case['after']['world'];budget=case['budget'];due=sum(fees[s['unit']]*s['count']for s in b['army']['slots']if s['count']);total=b['army']['gold']+b['progress']['legacy_04f6'];disband=due>total;after=min(30000,total-(0 if disband else due));assert(due,after,disband)==expected[name];assert budget==dict(Before=b['army']['gold'],Income=b['progress']['legacy_04f6'],Due=due,Charged=0 if disband else due,After=after,Disbanded=disband);assert w['army']['gold']==after and w['revision']==b['revision']+1;assert w['army']['slots']==([{'unit':'','count':0}]*6 if disband else b['army']['slots'])
        native=(d/'after-native.ay').read_bytes();before=ram(q,name,'before.state');held=ram(q,name,'held.state');assert native[12:36]==native_rows and len(native)==2987;assert before[0x1e880+0x54a:0x1e880+0x562]==held[0x1e880+0x54a:0x1e880+0x562];assert saved(native,6)==after;assert word(held,0x1e880+0x4f8)==after and word(held,0x1e880+0x56da)==324
        for g in range(5):
            for row in range(24):
                at=0x1e880+0x3efe+g*240+row*10;kind,stock=word(before,at+6),word(before,at+8);expected_stock=min(stock+max(stock//10,10),caps[g*24+row])if kind else stock;assert camp(native,g,row)==[word(held,at+f*2)for f in range(5)];assert word(held,at+8)==expected_stock and before[at:at+8]==held[at:at+8];checked+=1
        e=read(d/'session/gamedata.ay.army.json');assert e['schema']=='eightsword-owned-world-save/4'and e['world']==w and e['original_sha256']==sha(d/'after-native.ay')and not e.get('resume');assert len(e['native_files'])==9
        for n,blob in e['native_files'].items():assert base64.b64decode(blob)==(d/'evidence/month-001'/n).read_bytes()
        assert case['seed']==1530878130 and case['saves']==1;cases.append(dict(name=name,budget=budget,native_sha256=sha(d/'after-native.ay')))
    assert(q/'candidate-r1/native/after-native.ay').read_bytes()[12:]==h.stored(r,'monthly-r1','/monthly-r1/original-r1/paid/serialized.ay')[12:]
    fonts=read(q/'ui-assets/army-ui-fonts.json');old=json.loads(h.stored(r,'monthly-r1','/monthly-r1/ui-assets/army-ui-fonts.json'));assert fonts['glyphs'][:len(old['glyphs'])]==old['glyphs'];assert len(fonts['glyphs'])==434;atlas={};old_cells=0
    for profile in fonts['profiles']:
        assert profile['source_sha256']==h.FONT_SHA[profile['id']];file=q/'ui-assets'/profile['file'];assert sha(file)==profile['sha'];im=Image.open(file).convert('RGBA');prior=Image.open(__import__('io').BytesIO(h.stored(r,'monthly-r1','/monthly-r1/ui-assets/'+profile['file']))).convert('RGBA')
        for glyph in old['glyphs']:
            x,y,w,hh=glyph['cell'];assert im.crop((x,y,x+w,y+hh)).tobytes()==prior.crop((x,y,x+w,y+hh)).tobytes();old_cells+=1
        atlas[profile['id']]=im
    glyphs={g['character']:g['cell']for g in fonts['glyphs']};tests=read(q/'ui-test-r1/wide-ui-test.json');assert{v['font']for v in tests}=={'noto','lishu','caoshu'}
    for case in tests:
        for t in case['texts']:assert not t['Ellipsized']and(inside(t['Ink'],t['Rect'])or t['Ink']==[0,0,0,0])
        due=next(t for t in case['texts']if t['Role']=='monthly-due');assert due['Text']==str(2**64-1)and len(due['Text'])==20
    gui=read(q/'gui-r1/receipt.json');assert gui['status']=='passed-monthly-wide-ui-cold'and gui['controlled_countdown']and gui['ordinary_continue_and_movement']and not gui['f7_used'];assert gui['cold']['world']==gui['returned']['world']==gui['report']['world'];assert gui['cold']['pair_token']==gui['returned']['pair_token']==gui['lishu']['pair_token'];assert gui['cold']['monthly']['saves']==0 and gui['cold']['font_id']=='lishu';assert gui['report']['monthly']['budget']==dict(Before=500,Income=100,Due=100030,Charged=0,After=600,Disbanded=True);frames=[];numbers=0
    for frame in gui['screens']:
        folder=q/'gui-r1'/frame['phase'];meta=read(folder/frame['metadata']);im=Image.open(folder/frame['screen']).convert('RGBA');digest=hashlib.sha256(im.tobytes()).hexdigest();assert digest==meta['canvas_sha256']==meta['presented_sha256'];assert im.tobytes()==Image.open(folder/frame['canvas']).convert('RGBA').tobytes();assert meta['native_rows_hex']==gui['initial']['native_rows_hex']
        for t in meta['text_fields']or[]:assert not t['Ellipsized']and(inside(t['Ink'],t['Rect'])or t['Ink']==[0,0,0,0])
        if meta['view']=='monthly':
            assert meta['monthly']['committed'];assert any(t['Role']=='monthly-disband'for t in meta['text_fields']);values=meta['monthly']['budget']
            for t in meta['text_fields']:
                field={'monthly-before':'Before','monthly-income':'Income','monthly-due':'Due','monthly-charged':'Charged','monthly-after':'After'}.get(t['Role'])
                if not field:continue
                assert t['Text']==str(values[field]);rect=t['Rect'];w,hh=rect[2]-rect[0],rect[3]-rect[1];expected_im=Image.new('RGBA',(w,hh),(20,56,41,255));pixels=expected_im.load();size=t['Size'];x=0;y=(hh-size)//2;src=atlas[meta['font_id']]
                for c in t['Text']:
                    gx,gy,_,_=glyphs[c];adv=size*2//3
                    for py in range(size):
                        for px in range(adv):
                            alpha=src.getpixel((gx+px*64//adv,gy+py*64//size))[3];pixels[x+px,y+py]=tuple((fg*alpha+bg*(255-alpha)+127)//255 for fg,bg in zip((246,234,202),(20,56,41)))+(255,)
                    x+=adv
                assert im.crop(rect).tobytes()==expected_im.tobytes();numbers+=1
        frames.append(dict(phase=frame['phase'],screen=frame['screen'],rgba_sha256=digest))
    result=dict(status='passed-monthly-wide-candidate',dependencies=deps,source_tools={n:sha(r/'tools'/n)for n in m.NEW},binaries={n:sha(q/n)for n in['monthly-wide-candidate','monthly-wide-ui','monthly-wide-ui-fixture']},candidate_cases=cases,rule_cases=proof['rule_cases'],camp_records=checked,faults=proof['faults'],old_glyph_cells_preserved=old_cells,added_glyphs=12,fonts_tested=['noto','lishu','caoshu'],independently_rebuilt_numeric_fields=numbers,verified_x11_frames=frames,formal_changed=False,production_promoted=False,limits=['Controlled starting armies and source countdown; ordinary Continue, movement, font key and cold F2.','Wide arithmetic intentionally differs from native 16-bit wrap outside admitted parity domain.','Native resources remain capped at 30000; only displayed and calculated fees are wide.','Story resources, natural openKB camp recruitment and formal world integration remain outside this slice.'])
    write=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');assert not a.out.exists();write(a.out,result)
if __name__=='__main__':main()
