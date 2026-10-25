#!/usr/bin/env python3
"""047 DRAFT：核對募兵整頁／編輯交易、正常輸入及真正GUI存讀。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import runpy

from PIL import Image, ImageChops, __version__ as PILLOW_VERSION


def read(path):return json.loads(path.read_text())
def rows(path):return [json.loads(line) for line in path.read_text().splitlines()]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def files(root):return {str(f.relative_to(root)):sha(f) for f in root.rglob('*') if f.is_file()}


def manifest(path,root):
    lines=path.read_text().splitlines()
    for line in lines:
        digest,name=line.split('  ',1)
        assert sha(root/name)==digest,name
    return len(lines)


def panels(root,decode,required):
    events=rows(root/'owned-commands.jsonl');pending=None;intervals=[]
    for event in events:
        if event['command']=='panel-begin':
            assert pending is None;pending=event
        elif event['command']=='panel-commit':
            assert pending and pending['kind']==event['kind'] and pending['step']==event['start_step']
            assert event['primitive_pending']==0 and event['step']>pending['step']
            intervals.append(dict(kind=event['kind'],begin=pending['step'],commit=event['step'],held=0));pending=None
    receipt=read(root/'owned-receipt.json')
    assert pending is None and receipt['panel_at_end'] is None and receipt['active_at_end']==0
    assert not receipt['commands'].get('writes-outside-command',0)
    assert not any('reject' in name for name in receipt['commands'])
    assert required<={v['kind'] for v in intervals}
    frames=list(decode(root/'presentation.frames.gz'));previous=None
    for ordinal,step,digest in frames:
        for v in intervals:
            if v['begin']<=step<v['commit']:
                assert digest==previous,(root,ordinal,v);v['held']+=1
        previous=digest
    captures=[]
    for event in events:
        if event['command']!='completed-capture' or not event['kind'].startswith('panel-'):continue
        name=event['kind'];own=Image.open(root/(name+'-owned.png')).convert('RGBA')
        old=Image.open(root/(name+'-legacy.png')).convert('RGBA')
        assert own.size==old.size==(1920,1200),name
        digest=hashlib.sha256(own.tobytes()).hexdigest()
        assert digest==event['rgba_sha256'] and hashlib.sha256(old.tobytes()).hexdigest()==event['legacy_rgba_sha256']
        if name=='panel-minimap-complete':
            # Existing 047 single-pixel repair, also checked by audit-owned-modal.
            channels=ImageChops.difference(own.convert('RGB'),old.convert('RGB')).split()
            mask=ImageChops.lighter(ImageChops.lighter(channels[0],channels[1]),channels[2]).point(lambda v:255 if v else 0)
            assert mask.histogram()[255]==event['different_pixels']==23040
            for lo,hi in [(96,100),(380,384)]:mask.paste(0,(lo*3,13*6,hi*3,173*6))
            assert mask.getbbox() is None
        else:assert own.tobytes()==old.tobytes() and event['different_pixels']==0,name
        end=min((v['begin'] for v in intervals if v['begin']>event['step']),default=2**64)
        actual=[n for n,s,h in frames if event['step']<=s<end and h==digest]
        captures.append(dict(kind=name,pixels=2304000,actual_frames=actual))
    return dict(frames=len(frames),intervals=intervals,held_frames=sum(v['held'] for v in intervals),captures=captures),frames


def party_draws(root,numeric,profiles):
    targets={};meta=rows(root/'intro-draw.jsonl')
    for path in root.glob('*-army-*.json'):
        st=read(path);targets[int(st['presented_frames'])]='army'
    accepted=root/'recruitment-accepted.json';after=read(accepted)['steps'] if accepted.exists() else 0
    for event in read(root/'gui-input-receipt.json')['events']:
        st=event['status']
        if event['x11_keycode']==9 and event['down'] and st.get('presented_scene')=='character' and st['steps']>after:
            targets[int(st['presented_frames'])]='character'
    checked=[]
    for ordinal,step,im in numeric.building.helper.stream(root):
        if ordinal not in targets:continue
        font=meta[ordinal-1]['font_id'];kind=targets[ordinal]
        points=(numeric.digits(im,profiles,font,'31',152,29)+numeric.digits(im,profiles,font,'31',152,45)) if kind=='army' else numeric.digits(im,profiles,font,'499',112,117,advance=16)
        checked.append(dict(draw=ordinal,kind=kind,opaque_points=points))
    assert sum(v['kind']=='army' for v in checked)==2
    assert sum(v['kind']=='character' for v in checked)>=2
    return checked


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--gui',action='store_true');a=ap.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid()==1000
    assert not a.out.exists() and a.out.parent.stat().st_uid==1000
    p=a.project;b=p/'workplace/probe-20261023/graphics-first/battle-r1';build=b/'owned-live-build-r43'
    inputs=manifest(build/'build-inputs.sha256',build/'src');programs=manifest(build/'build-outputs.sha256',build)
    decode=runpy.run_path(str(p/'tools/audit-owned-modal.py'))['frames']
    direct=runpy.run_path(str(p/'tools/audit-direct-masked-rows.py'))['direct_calls']
    c=b/'owned-recruit-control-r1';n=b/'owned-recruit-candidate-r1'
    candidate,rendered=panels(n,decode,{'recruitment','recruitment-edit','recruitment-result'})
    control,old_frames=panels(c,decode,set())
    assert candidate['frames']==control['frames']==611
    paired={}
    for name in ['final.state','audio.pcm','commands.jsonl','owned-intro-commands.jsonl','vga-reads.json']:
        assert sha(c/name)==sha(n/name),name;paired[name]=sha(n/name)
    assert files(c/'scratch')==files(n/'scratch')
    excluded={'panel-begin','panel-commit','completed-capture','recruitment-policy','recruitment-key'}
    assert [e for e in rows(c/'owned-commands.jsonl') if e['command'] not in excluded]==[e for e in rows(n/'owned-commands.jsonl') if e['command'] not in excluded]
    assert [{k:v for k,v in e.items() if k!='scene'} for e in rows(c/'direct-runtime-commands.jsonl')]==[{k:v for k,v in e.items() if k!='scene'} for e in rows(n/'direct-runtime-commands.jsonl')]
    keys=[e['key_ax'] for e in rows(n/'owned-commands.jsonl') if e['command']=='recruitment-key']
    assert keys==[0x0231,0x0b30,0x0e08,0x1c0d]
    changed=[]
    for lhs,rhs in zip(old_frames,rendered):
        assert lhs[:2]==rhs[:2]
        if lhs[2]!=rhs[2]:
            assert any(v['kind'].startswith('recruitment') and v['begin']<=rhs[1]<v['commit'] for v in candidate['intervals'])
            changed.append(rhs[0])
    assert changed and candidate['held_frames']>control['held_frames']
    for root in (c,n):
        st=read(root/'final.json')
        assert st['frame_pure_count']==st['recorded_frames']==611 and st['owned_render_fault'] is None
        assert not st['unimplemented'] and not st['text']['MissingGlyphs'] and not st['text']['Errors']
    old_status,new_status=read(c/'final.json'),read(n/'final.json')
    for field in ('steps','mode','input_events','exec_log','file_ops','strings','unimplemented'):
        assert old_status[field]==new_status[field],field
    spec=importlib.util.spec_from_file_location('recruit_input',p/'tools/audit-recruitment-input.py')
    numeric=importlib.util.module_from_spec(spec);spec.loader.exec_module(numeric)
    artmod=numeric.building;assets=p/'workplace/player/assets-painted-r49';profiles=artmod.helper.fonts(assets)
    normal_fields=numeric.normal(argparse.Namespace(receipt=n),profiles)
    for name in ['13-enter-one','13b-enter-ten','13b-ten-lishu','13b-ten-caoshu','13c-backspace-one','15-army-after-hire','16-character-after-hire','17-final-map']:
        assert Image.open(n/(name+'-hd.png')).tobytes()==Image.open(c/(name+'-hd.png')).tobytes(),name
    result=dict(schema=1,status='PASS-scoped-047-recruitment-transactions',production=False,build_inputs=inputs,programs=programs,
                normal=candidate,changed_frames=changed,paired=paired,scratch_files=len(files(n/'scratch')),
                direct=direct(n),numeric=normal_fields,
                tools=dict(go=(build/'build-go-version.txt').read_text().strip(),python=platform.python_version(),pillow=PILLOW_VERSION,audit_sha256=sha(Path(__file__))),
                source=dict(file='PAM.AY',sha256=sha(p/'workplace/intake-20261023/sources/game/8sword/PAM.AY'),
                            ida_export_sha256=sha(p/'workplace/probe-20261023/graphics-first/ida-graphics-inventory-r10.json'),
                            address_space='runtime 0110:IP; IDA MZ linear 10000+IP; file 1470+IP'),
                limits=['Numeric cursor waits remain live; a first pre-cursor capture need not appear in Draw.',
                        'No injection, rule/RNG claim, additional recruitment type or production promotion.'])
    if a.gui:
        gui=p/'workplace/player/gui/owned-recruit-save-r1';saved=gui/'scratch/gamedata.ay';assert saved.stat().st_size==2987
        assert sha(saved)==read(gui/'save/saved.json')['sha256']
        phases={}
        for phase in ('save','reload'):
            q=gui/phase
            for name in ('build-inputs.sha256','build-outputs.sha256','build-go-version.txt'):assert sha(q/name)==sha(build/name)
            required={'main-menu','first-map','character','army','return-map'}
            if phase=='save':required|={'recruitment','recruitment-edit','recruitment-result'}
            item,_=panels(q,decode,required)
            st=read(q/'gui-final.json');guard=read(q/'owned-guard-receipt.json');stream=read(q/'continuous-audit.json')
            assert st['closed'] and st['hd'] and st['font_id']=='noto' and st['owned_render_fault'] is None
            assert guard['enabled'] and guard['fault'] is None and guard['held_frames']==0
            assert not st['asset_error'] and not st['graphics_error'] and not st['unimplemented']
            assert not st['text']['MissingGlyphs'] and not st['text']['Errors']
            assert saved.read_bytes()==(q/'snapshot-readonly/save-buffer-9e000.bin').read_bytes()
            assert stream['status']=='lossless-stream-valid' and stream['recording_sha256']==sha(q/'presentation.frames.gz')
            assert stream['frames']==st['recorded_frames']==item['frames']
            inputs_receipt=read(q/'gui-input-receipt.json');assert inputs_receipt['status']=='passed-input-path' and inputs_receipt['flow']==phase
            if phase=='save':assert st['exited'] and st['exit_code']==0
            else:assert not st['exited'] and st['presented_scene']=='map'
            item.update(changed_frames=stream['changed_frames'],direct=direct(q));phases[phase]=item
        q=gui/'save';meta=rows(q/'intro-draw.jsonl');targets={}
        for digit in range(4,10):
            for name,text in [(f'recruitment-input-digit-{digit}',str(digit)),(f'recruitment-cleared-digit-{digit}','')]:
                st=read(q/(name+'.json'));targets[int(st['presented_frames'])]=(name,text,st['font_id'])
        for name,text in [('recruitment-input-ten','10'),('recruitment-edited-one','1')]:
            st=read(q/(name+'.json'));targets[int(st['presented_frames'])]=(name,text,st['font_id'])
        assert len(targets)==14
        building_targets={}
        for font in ['noto','lishu','caoshu']:
            st=read(q/('recruitment-'+font+'.json'));building_targets[int(st['presented_frames'])]=font
        art_path=assets/'recruitment-building-r1.png'
        assert sha(art_path)=='7aa67f8975843e91e0a393863ba08bb77582fd4ab62ee10fad059bebcd5b61ab'
        art=artmod.sample(art_path);fields=[];buildings=[]
        reference=Image.open(q/'panel-recruitment-complete-legacy.png').convert('RGBA')
        for ordinal,step,im in artmod.helper.stream(q):
            if ordinal in targets:
                name,text,font=targets[ordinal];numeric.check_input(im,profiles,font,text);fields.append(dict(draw=ordinal,name=name,text=text))
            if ordinal in building_targets:
                font=building_targets[ordinal];assert meta[ordinal-1]['font_id']==font
                assert im.crop(artmod.RECT).tobytes()==art
                points=artmod.font_points(im,font,profiles)
                if font=='noto':
                    numeric.check_input(im,profiles,font,'')
                    expected=reference.copy();expected.paste(im.crop(numeric.FIELD),numeric.FIELD)
                    assert expected.tobytes()==im.convert('RGBA').tobytes(),'full Noto page outside explicitly modelled cursor field'
                buildings.append(dict(draw=ordinal,font=font,exact_building_pixels=806400,opaque_font_points=points))
        assert len(fields)==14 and len(buildings)==3
        events=read(q/'gui-final.json')['input_events']
        for scan in list(range(5,12))+[14]:
            assert all(any(e['Scan']==scan and e['Down']==down for e in events) for down in [False,True])
        cold=read(gui/'reload/gui-final.json');reads=[e for e in cold['file_ops'] if e['Op']=='read' and e['Name']=='gamedata.ay']
        assert len(reads)==1 and reads[0]['Pos']==0 and reads[0]['Len']==2987 and not reads[0]['Failed']
        party={phase:party_draws(gui/phase,numeric,profiles) for phase in ('save','reload')}
        result['gui']=dict(phases=phases,fields=fields,buildings=buildings,party_draws=party,saved_bytes=2987,saved_sha256=sha(saved),read_step=reads[0]['Step'])
    with a.out.open('x') as f:f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],frames=611,changed=len(changed),gui=a.gui)))


if __name__=='__main__':main()
