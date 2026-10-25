#!/usr/bin/env python3
"""047 DRAFT：核對基底圖像失效時的來源呈現、Noto及選用正常視窗。"""
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


def rows(path):return [json.loads(line) for line in path.read_text().splitlines()]


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
    p=a.project;b=p/'workplace/probe-20261023/graphics-first/battle-r1'
    build=b/'owned-live-build-r39';fixtures=b/'owned-fallback-assets-r1'
    inputs=verify_manifest(build/'build-inputs.sha256',build/'src')
    programs=verify_manifest(build/'build-outputs.sha256',build)
    regression=(b/'owned-fallback-regression-r1.log').read_text()
    for name,count in [('DirectMaskedRowsNativeState',60),('DirectMaskedRowsRejectWithoutWrites',14),
                       ('DirectMaskedNativePrefix',24),('DirectRuntimeNativePrefixAndPoisonedStack',16)]:
        assert regression.count('    --- PASS: TestResearch'+name+'/')==count,name
    assert regression.count('--- PASS: TestResearchOwnedBatch')==2
    assert '\nPASS\n' in regression and '\nFAIL' not in regression and '--- SKIP:' not in regression
    fixture=read(fixtures/'fixtures.json')
    base=p/'workplace/player/assets-painted-r49'
    for name,sha in fixture['base_hashes'].items():assert digest(base/name)==sha,name
    assert len(fixture['base_hashes'])==344
    for kind,data in fixture['cases'].items():
        actual={f.name:digest(f) for f in (fixtures/kind).iterdir()}
        assert actual==data['files']
        for name,sha in fixture['base_hashes'].items():
            if name!=data['changed']:assert actual[name]==sha,(kind,name)
    assert not (fixtures/'missing/terrain.json').exists()
    assert (fixtures/'corrupt/grass-painted-r1.png').read_bytes()==(base/'grass-painted-r1.png').read_bytes()+b'\0'
    for label in ('control','fixed'):
        log=(b/('owned-fallback-'+label+'-r2.log')).read_text()
        assert log.count('    --- PASS: TestResearchOwnedGraphicsGroupFailure/')==2 and '\nPASS\n' in log
        assert '--- SKIP:' not in log and '\nFAIL' not in log
    direct=runpy.run_path(str(p/'tools/audit-direct-masked-rows.py'))['direct_calls']
    cases={}
    for kind in ('missing','corrupt'):
        reference=b/'owned-fallback-control-r2'/kind
        current=b/'owned-fallback-fixed-r2'/kind
        old,new=read(reference/'receipt.json'),read(current/'receipt.json')
        assert old['control'] and not new['control']
        assert old['main_menu_ready_step']==new['main_menu_ready_step']>0
        assert new['font']=='noto' and new['pam_source_frames']>0 and new['pam_legacy_rgb_frames']==0
        if kind=='missing':assert new['graphics_error']==''
        else:assert new['graphics_error']=='HD 圖像 grass-painted-r1.png SHA-256 不符'
        paired={}
        for name in ('final.state','audio.pcm'):
            assert digest(reference/name)==digest(current/name),(kind,name)
            paired[name]=digest(current/name)
        files=lambda root:{str(f.relative_to(root)):digest(f) for f in root.rglob('*') if f.is_file()}
        assert files(reference/'scratch')==files(current/'scratch')
        assert len(new['captures'])==4
        for lhs,rhs in zip(old['captures'],new['captures']):
            assert (lhs['name'],lhs['step'])==(rhs['name'],rhs['step'])
            assert rhs['frame_pure']
            im=Image.open(current/(rhs['name']+'.png')).convert('RGBA')
            control=Image.open(reference/(lhs['name']+'.png')).convert('RGBA')
            assert im.size==control.size==(1920,1200) and im.tobytes()==control.tobytes()
            assert hashlib.sha256(im.tobytes()).hexdigest()==rhs['rgba_sha256']==lhs['rgba_sha256']
        source=rows(current/'owned/owned-commands.jsonl')
        bitmaps=[e for e in source if e['command']=='bitmap']
        assert len(bitmaps)>0 and all(e['material']==e['actor']==e['effect']==0 for e in bitmaps)
        assert {e['entry'] for e in bitmaps}>={0x4f2,0x76f,0x99c}
        owned=read(current/'owned/owned-receipt.json')
        assert owned['active_at_end']==0 and owned['panel_at_end'] is None
        assert owned['commands'].get('writes-outside-command',0)==0
        assert not any('reject' in key for key in owned['commands'])
        status=new['status']
        assert status['hd'] and not status['asset_error'] and not status['unimplemented']
        assert status['text']['MissingGlyphs']==0 and not status['text']['Errors']
        batches=rows(current/'owned/render-batch-audit.jsonl')
        assert batches and all(e['same_pixels'] and e['batch']['TextureCopyPixels']==0 for e in batches)
        cases[kind]=dict(ready_step=new['main_menu_ready_step'],paired=paired,
                captures=4,full_pixels=4*2304000,pam_source_frames=new['pam_source_frames'],pam_legacy_rgb_frames=0,
                unknown_resource_commands=len(bitmaps),direct=direct(current/'owned'),
                receipt_sha256=digest(current/'receipt.json'))
    # This earlier diagnostic stopped before the menu. It proves the old bind
    # guard selected legacy RGB, not the later full normal-input result.
    baseline={}
    before=b/'owned-live-build-r34'
    for name,sha in read(before/'baseline-inputs.json').items():assert digest(before/'src'/name)==sha,name
    for kind in ('missing','corrupt'):
        r=read(b/'owned-fallback-baseline-r1'/kind/'owned/direct-runtime-receipt.json')
        assert not r['bound'] and r['pam_source_frames']==0 and r['pam_legacy_rgb_frames']>0
        baseline[kind]=dict(source_frames=0,legacy_frames=r['pam_legacy_rgb_frames'],scope='pre-menu diagnostic only')
    result=dict(schema=1,status='PASS-scoped-047-source-graphics-failure',production=False,
                build_inputs=inputs,programs=programs,fixtures_sha256=digest(fixtures/'fixtures.json'),
                regression_sha256=digest(b/'owned-fallback-regression-r1.log'),
                baseline=baseline,cases=cases,full_pixels=18432000,
                tools=dict(go=(build/'build-go-version.txt').read_text().strip(),python=platform.python_version(),
                           pillow=PILLOW_VERSION,audit_sha256=digest(Path(__file__))),
                source=dict(file='PAM.AY',sha256=digest(p/'workplace/intake-20261023/sources/game/8sword/PAM.AY'),
                            address_space='fixed runtime 0110:055A for menu-ready observation; no guest state injection'),
                limits=['Only missing/corrupt graphics group with valid font data.',
                        'Unknown drawing opcodes, invalid modes and base-font failure remain separate contracts.',
                        'No normal source-art or production promotion claim.'])
    if a.gui:
        gui=p/'workplace/player/gui/owned-fallback-save-r1'
        decode=runpy.run_path(str(p/'tools/audit-owned-modal.py'))['frames']
        audit=runpy.run_path(str(p/'tools/audit-owned-main-menu.py'))['audit_run']
        saved=gui/'scratch/gamedata.ay'
        assert saved.stat().st_size==2987 and digest(saved)==read(gui/'save/saved.json')['sha256']
        phases={}
        for phase in ('save','reload'):
            q=gui/phase
            for name in ('build-inputs.sha256','build-outputs.sha256','build-go-version.txt'):
                assert digest(q/name)==digest(build/name)
            required={'main-menu','first-map','character','army','return-map'}
            if phase=='save':required|={'new-game-confirm','music-menu','confirm','system'}
            item=audit(q,required,decode,gui=True)
            st=read(q/'gui-final.json')
            assert st['closed'] and st['hd'] and st['font_id']=='noto' and not st['asset_error']
            assert st['graphics_error']=='HD 圖像 grass-painted-r1.png SHA-256 不符'
            assert not st['unimplemented'] and not st['text']['Errors'] and st['text']['MissingGlyphs']==0
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
            item['changed_frames']=stream['changed_frames'];item['contact_sheets']=stream['contact_sheets']
            item['direct']=direct(q);phases[phase]=item
        cold=read(gui/'reload/gui-final.json')
        reads=[e for e in cold['file_ops'] if e['Op']=='read' and e['Name']=='gamedata.ay']
        assert len(reads)==1 and reads[0]['Pos']==0 and reads[0]['Len']==2987 and not reads[0]['Failed']
        result['gui']=dict(phases=phases,saved_bytes=2987,saved_sha256=digest(saved),read_step=reads[0]['Step'])
    with a.out.open('x') as f:f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],cases={k:dict(source=v['pam_source_frames'],legacy=0) for k,v in cases.items()},gui=a.gui)))


if __name__=='__main__':main()
