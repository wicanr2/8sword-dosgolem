#!/usr/bin/env python3
"""047 DRAFT：核對未知寫入／模式的有界錯誤，以及正常GUI未受影響。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import runpy

from PIL import Image, __version__ as PILLOW_VERSION


def read(path):return json.loads(path.read_text())


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_manifest(path,root):
    lines=path.read_text().splitlines()
    for line in lines:
        sha,name=line.split('  ',1)
        assert digest(root/name)==sha,name
    return len(lines)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--gui',action='store_true')
    a=ap.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid()==1000
    assert not a.out.exists() and a.out.parent.stat().st_uid==1000
    p=a.project;b=p/'workplace/probe-20261023/graphics-first/battle-r1';build=b/'owned-live-build-r42'
    inputs=verify_manifest(build/'build-inputs.sha256',build/'src')
    programs=verify_manifest(build/'build-outputs.sha256',build)
    log=(b/'owned-guard-tests-r1.log').read_text()
    for name,count in [('DirectMaskedRowsNativeState',60),('DirectMaskedRowsRejectWithoutWrites',14),
                       ('DirectMaskedNativePrefix',24),('DirectRuntimeNativePrefixAndPoisonedStack',16),
                       ('OwnedSourceGuard',4)]:
        assert log.count('    --- PASS: TestResearch'+name+'/')==count,name
    assert log.count('--- PASS: TestResearchOwnedBatch')==2
    assert '--- PASS: TestResearchOwnedGuardDoesNotSwallowRuntimePanic' in log
    assert '\nPASS\n' in log and '\nFAIL' not in log and '--- SKIP:' not in log
    cases={}
    for kind,reason,ip in [('unclassified-write','unclassified-video-write',31),
                           ('unhandled-mode','unhandled-display-mode',5)]:
        q=b/'owned-guard-faults-r1'/kind;old,new=read(q/'control/receipt.json'),read(q/'guarded/receipt.json')
        assert old['control'] and not new['control'] and old['fault'] is None
        for key in ['injection_step','final_step','slice_steps','controlled_code_hex','controlled_code_sha256',
                    'native_before_size','native_after_size','native_before_sha256','native_after_sha256','frame_sha256']:
            assert old[key]==new[key],(kind,key)
        assert old['requested_cycles']==50000 and new['requested_cycles']==100000
        assert old['first_slice_cycles']==new['first_slice_cycles']==50000
        assert new['slice_steps']==50000 and new['frame_pure'] and old['frame_pure']
        assert new['native_before_sha256']!=new['native_after_sha256']
        assert hashlib.sha256(bytes.fromhex(new['controlled_code_hex'])).hexdigest()==new['controlled_code_sha256']
        fault=new['fault']
        assert fault['phase']=='pam' and fault['reason']==reason and fault['cs']==0x8000 and fault['ip']==ip
        assert new['injection_step']<=fault['step']<=new['final_step']
        assert fault['mode']==(0x0e if kind=='unclassified-write' else 0x13)
        paired={}
        for name in ('final.state','audio.pcm'):
            assert digest(q/'control'/name)==digest(q/'guarded'/name),(kind,name)
            paired[name]=digest(q/'guarded'/name)
        files=lambda root:{str(f.relative_to(root)):digest(f) for f in root.rglob('*') if f.is_file()}
        assert files(q/'control/scratch')==files(q/'guarded/scratch')
        rgba=[]
        for label in ('control','guarded'):
            for name in ('before','after'):
                im=Image.open(q/label/(name+'.png')).convert('RGBA')
                assert im.size==(1920,1200)
                rgba.append(hashlib.sha256(im.tobytes()).hexdigest())
        assert set(rgba)=={new['frame_sha256']}
        for label in ('control','guarded'):
            guard=read(q/label/'owned/owned-guard-receipt.json')
            assert guard['enabled']==(label=='guarded') and guard['fault']==(fault if label=='guarded' else None)
            if label=='guarded':assert guard['held_frames']>0
            direct=read(q/label/'owned/direct-runtime-receipt.json')
            assert direct['pam_source_frames']>0 and direct['pam_legacy_rgb_frames']==0
        cases[kind]=dict(fault=fault,paired=paired,native_before_size=new['native_before_size'],
                        native_after_size=new['native_after_size'],first_slice_steps=50000,
                        requested_cycles=100000,full_pixels=9216000,controlled_code_sha256=new['controlled_code_sha256'])
    result=dict(schema=1,status='PASS-scoped-047-bounded-source-failure',production=False,
                build_inputs=inputs,programs=programs,cases=cases,full_pixels=18432000,
                tests_sha256=digest(b/'owned-guard-tests-r1.log'),
                tools=dict(go=(build/'build-go-version.txt').read_text().strip(),python=platform.python_version(),
                           pillow=PILLOW_VERSION,audit_sha256=digest(Path(__file__))),
                source=dict(file='PAM.AY',sha256=digest(p/'workplace/intake-20261023/sources/game/8sword/PAM.AY'),
                            address_space='PAM observation at runtime 0110:055A; fault program at 8000:0000'),
                limits=['Controlled RAM and CallNear fault injection, not a natural failure or player-path claim.',
                        'Video metadata IP is the store; mode-change IP is current callback registers after INT10.',
                        'No automatic recovery or production error-interface claim.'])
    if a.gui:
        root=p/'workplace/player/gui/owned-guard-save-r1'
        decode=runpy.run_path(str(p/'tools/audit-owned-modal.py'))['frames']
        audit=runpy.run_path(str(p/'tools/audit-owned-main-menu.py'))['audit_run']
        direct=runpy.run_path(str(p/'tools/audit-direct-masked-rows.py'))['direct_calls']
        saved=root/'scratch/gamedata.ay';assert saved.stat().st_size==2987
        assert digest(saved)==read(root/'save/saved.json')['sha256']
        phases={}
        for phase in ('save','reload'):
            q=root/phase
            for name in ('build-inputs.sha256','build-outputs.sha256','build-go-version.txt'):
                assert digest(q/name)==digest(build/name)
            required={'main-menu','first-map','character','army','return-map'}
            if phase=='save':required|={'new-game-confirm','music-menu','confirm','system'}
            item=audit(q,required,decode,gui=True)
            st=read(q/'gui-final.json');guard=read(q/'owned-guard-receipt.json')
            assert st['closed'] and st['hd'] and st['font_id']=='noto' and st['owned_render_fault'] is None
            assert guard['enabled'] and guard['fault'] is None and guard['held_frames']==0
            assert not st['asset_error'] and not st['graphics_error'] and not st['unimplemented']
            assert not st['text']['Errors'] and st['text']['MissingGlyphs']==0
            if phase=='save':assert st['exited'] and st['exit_code']==0
            else:assert not st['exited'] and st['presented_scene']=='map'
            assert saved.read_bytes()==(q/'snapshot-readonly/save-buffer-9e000.bin').read_bytes()
            inputs_receipt=read(q/'gui-input-receipt.json')
            assert inputs_receipt['status']=='passed-input-path' and inputs_receipt['flow']==phase
            assert any(e.get('status',{}).get('presented_scene')=='character' and
                       e.get('status',{}).get('presented_font_id')=='noto' for e in inputs_receipt['events'])
            stream=read(q/'continuous-audit.json')
            assert stream['status']=='lossless-stream-valid' and stream['frames']==st['recorded_frames']
            assert stream['recording_sha256']==digest(q/'presentation.frames.gz')
            item.update(changed_frames=stream['changed_frames'],contact_sheets=stream['contact_sheets'],direct=direct(q))
            phases[phase]=item
        cold=read(root/'reload/gui-final.json')
        reads=[e for e in cold['file_ops'] if e['Op']=='read' and e['Name']=='gamedata.ay']
        assert len(reads)==1 and reads[0]['Pos']==0 and reads[0]['Len']==2987 and not reads[0]['Failed']
        result['gui']=dict(phases=phases,saved_bytes=2987,saved_sha256=digest(saved),read_step=reads[0]['Step'])
    with a.out.open('x') as f:f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],cases=len(cases),gui=a.gui)))


if __name__=='__main__':main()
