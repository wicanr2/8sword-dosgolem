#!/usr/bin/env python3
"""047 DRAFT：核對r33逐列接管、正常兩路徑及選用的實際視窗。Docker only。"""
import argparse
import bisect
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import runpy

from PIL import __version__ as PILLOW_VERSION


def read(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda: f.read(1024*1024), b''):
            h.update(data)
    return h.hexdigest()


def frame_digest(path):
    h = hashlib.sha256()
    with gzip.open(path, 'rb') as f:
        for data in iter(lambda: f.read(1024*1024), b''):
            h.update(data)
    return h.hexdigest()


def verify_manifest(path, root):
    count = 0
    for line in path.read_text().splitlines():
        sha, name = line.split('  ', 1)
        assert digest(root/name) == sha, name
        count += 1
    return count


def direct_calls(root):
    receipt = read(root/'direct-runtime-receipt.json')
    assert receipt['bound'] and not receipt['control'] and not receipt['production']
    assert receipt['pam_legacy_rgb_frames'] == 0 and receipt['pam_source_frames'] > 0
    source = [e for e in rows(root/'owned-commands.jsonl') if e['command'] == 'bitmap']
    bitmaps = {(e['entry_step'],e['entry']):e for e in source}
    families = {}
    for entry in (0x4f2,0x626):
        ordered = sorted((e for e in source if e['entry']==entry),key=lambda e:e['entry_step'])
        families[entry] = ([e['entry_step'] for e in ordered],ordered)
    accepted, coverage, totals = {}, {}, {'steps':0,'cycles':0,'compatibility':0,'row_batches':0,'row_bytes':0,'row_steps':0}
    commands = rows(root/'direct-runtime-commands.jsonl')
    for event in commands:
        p = event['plan']
        at,end,site = event['entry_step'],event['return_boundary_step'],p['Entry']
        assert event['original_pixel_instructions_executed'] == 0
        if p.get('Primitive') == 'masked-row':
            assert site in (0x56f,0x6a3)
            parent_entry = {0x56f:0x4f2,0x6a3:0x626}[site]
            assert p['SourceEntry'] == parent_entry
            starts,events = families[parent_entry]
            index = bisect.bisect_right(starts,at)-1
            assert index >= 0
            original = events[index]
            assert original['entry_step'] <= at < end <= original['step']
            plane,row,col = p.get('Plane',0),p.get('Row',0),p.get('Column',0)
            w,h = original['width_bytes'],original['height']
            assert 0<=plane<4 and 0<=row<h and 0<=col<w
            assert p['SourceSHA256'] == original['source_sha256']
            assert (p['XByte'],p['Y'],p['WidthBytes'],p['Height'],p['Destination']) == (
                original['x_byte']+col,original['y']+row,w-col,1,original['dest'])
            byte_steps = 9 if site==0x56f else 12
            assert p['ReturnBoundary'] == {0x56f:0x580,0x6a3:0x6bb}[site]
            assert p['WriteSite'] == {0x56f:0x57d,0x6a3:0x6b8}[site]
            assert p['Steps'] == end-at == byte_steps*(w-col)
            assert p['Cycles'] == (byte_steps+1)*(w-col)
            compatibility = p['CompatibilityBytes']
            assert compatibility == w-col
            key = (original['entry_step'],parent_entry,plane,row)
            assert key not in coverage, 'overlapping row batch'
            coverage[key] = compatibility
            totals['row_batches'] += 1;totals['row_bytes'] += compatibility;totals['row_steps'] += p['Steps']
        else:
            original = bitmaps[at,site]
            assert original['step'] == end and original['source_sha256'] == p['SourceSHA256']
            assert tuple(original[k] for k in ('x_byte','y','width_bytes','height','dest')) == tuple(
                p[k] for k in ('XByte','Y','WidthBytes','Height','Destination'))
            w,h = p['WidthBytes'],p['Height']
            if site in (0x99c,0x76f):
                assert p['ReturnBoundary'] == {0x99c:0xa6f,0x76f:0x854}[site]
                expected_steps = 32*h+81
            else:
                assert site in (0x4f2,0x626)
                assert p['ReturnBoundary'] == {0x4f2:0x625,0x626:0x76e}[site]
                expected_steps = 4*h*((9 if site==0x4f2 else 12)*w+7)+111
                for plane in range(4):
                    for row in range(h):
                        key=(at,site,plane,row)
                        assert key not in coverage
                        coverage[key]=w
            assert p['Steps'] == end-at == expected_steps and p['Cycles'] == expected_steps+4*w*h
            compatibility=4*w*h
        accepted[format(site,'04x')] = accepted.get(format(site,'04x'),0)+1
        totals['steps'] += p['Steps'];totals['cycles'] += p['Cycles'];totals['compatibility'] += compatibility
    counts=receipt['counts']
    assert counts['accepted'] == len(commands)
    assert counts['virtual-instructions'] == totals['steps'] and counts['virtual-cycles'] == totals['cycles']
    assert counts['compatibility-plane-bytes'] == totals['compatibility']
    assert counts['masked-row-batches'] == totals['row_batches'] and counts['masked-row-bytes'] == totals['row_bytes']
    assert counts['masked-row-virtual-instructions'] == totals['row_steps']
    for site,n in accepted.items():assert counts['accepted-'+site] == n
    assert totals['row_batches'] > 0
    masked = [e for e in source if e['entry'] in (0x4f2,0x626)]
    source_bytes = sum(4*e['width_bytes']*e['height'] for e in masked)
    skipped_bytes = sum(coverage.values())
    assert 0 < skipped_bytes <= source_bytes
    return dict(accepted=accepted,**totals,masked_source_calls=len(masked),masked_source_bytes=source_bytes,
                masked_skipped_bytes=skipped_bytes,masked_native_bytes=source_bytes-skipped_bytes,
                masked_calls_with_skips=len({key[:2] for key in coverage}),
                pam_source_frames=receipt['pam_source_frames'],pam_legacy_rgb_frames=0,
                fallback={k:v for k,v in counts.items() if k.startswith('fallback-')})


def paired_run(run, control):
    hashes={}
    for name in ('final.state','audio.pcm','commands.jsonl','frames.jsonl','owned-commands.jsonl',
                 'owned-intro-commands.jsonl','vga-reads.json'):
        assert digest(run/name) == digest(control/name),name
        hashes[name]=digest(run/name)
    hashes['decompressed_frames']=frame_digest(run/'presentation.frames.gz')
    assert hashes['decompressed_frames'] == frame_digest(control/'presentation.frames.gz')
    files=lambda root:{str(f.relative_to(root)):digest(f) for f in root.rglob('*') if f.is_file()}
    scratch=files(run/'scratch');assert scratch==files(control/'scratch')
    final=read(run/'final.json')
    assert final['frame_pure_count']==final['recorded_frames']>0
    assert not final['unimplemented'] and not final['text']['Errors'] and final['text']['MissingGlyphs']==0
    old=read(control/'direct-runtime-receipt.json');assert old['control'] and not old['counts']
    assert {e['font_id'] for e in rows(run/'frames.jsonl')} == {'noto','lishu','caoshu'}
    return dict(frames=final['recorded_frames'],scratch_files=len(scratch),paired=hashes,
                direct=direct_calls(run),exited=final['exited'],exit_code=final['exit_code'])


def audit_gui(project,build,root):
    decode=runpy.run_path(str(project/'tools/audit-owned-modal.py'))['frames']
    audit=runpy.run_path(str(project/'tools/audit-owned-main-menu.py'))['audit_run']
    phases={}
    saved=root/'scratch/gamedata.ay'
    assert saved.stat().st_size==2987 and digest(saved)==read(root/'save/saved.json')['sha256']
    settings=root/'settings.json'
    if settings.exists():
        assert read(settings)['font']=='noto'
        preference='explicit-noto'
    else:
        # No toolbar/font change and no -font override means no file is written.
        # Missing preferences intentionally select Noto in the frozen program.
        loader=(build/'src/internal/eightsword/font_preferences.go').read_text()
        assert 'if os.IsNotExist(err) {\n\t\treturn "noto", nil' in loader
        preference='absent-default-noto'
    for phase in ('save','reload'):
        q=root/phase
        for name in ('build-inputs.sha256','build-outputs.sha256','build-go-version.txt'):
            assert digest(q/name)==digest(build/name)
        required={'main-menu','first-map','character','army','return-map'}
        if phase=='save':required|={'new-game-confirm','music-menu','confirm','system'}
        result=audit(q,required,decode,gui=True)
        status=read(q/'gui-final.json')
        assert status['closed'] and status['hd'] and status['font_id']=='noto'
        assert not status['unimplemented'] and not status['text']['Errors'] and status['text']['MissingGlyphs']==0
        if phase=='save':assert status['exited'] and status['exit_code']==0
        else:assert not status['exited'] and status['presented_scene']=='map'
        inputs=read(q/'gui-input-receipt.json')
        assert inputs['status']=='passed-input-path' and inputs['flow']==phase
        assert any(e.get('status',{}).get('presented_scene')=='character' and
                   e.get('status',{}).get('presented_font_id')=='noto' for e in inputs['events'])
        assert saved.read_bytes()==(q/'snapshot-readonly/save-buffer-9e000.bin').read_bytes()
        stream=read(q/'continuous-audit.json')
        assert stream['status']=='lossless-stream-valid' and stream['frames']==status['recorded_frames']
        assert stream['recording_sha256']==digest(q/'presentation.frames.gz')
        result['changed_frames']=stream['changed_frames'];result['contact_sheets']=stream['contact_sheets']
        result['direct']=direct_calls(q)
        assert result['direct']['accepted'].get('056f',0)>0
        phases[phase]=result
    cold=read(root/'reload/gui-final.json')
    reads=[e for e in cold['file_ops'] if e['Op']=='read' and e['Name']=='gamedata.ay']
    assert len(reads)==1 and reads[0]['Pos']==0 and reads[0]['Len']==2987 and not reads[0]['Failed']
    return dict(phases=phases,saved_bytes=2987,saved_sha256=digest(saved),read_step=reads[0]['Step'],preference=preference)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--gui',action='store_true',help='追加固定direct-rows-save-r1實際Draw、Noto與真正存退讀')
    args=parser.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid()==1000
    assert not args.out.exists() and args.out.parent.stat().st_uid==1000
    p=args.project;b=p/'workplace/probe-20261023/graphics-first/battle-r1'
    build=b/'owned-live-build-r33';core=b/'core-direct-r6'
    inputs=verify_manifest(build/'build-inputs.sha256',build/'src')
    programs=verify_manifest(build/'build-outputs.sha256',build)
    cm=read(core/'runtime-manifest.json');assert digest(core/'runtime.patch')==cm['patch_sha256']
    for name,sha in cm['base_inputs'].items():
        assert digest(p/'workplace/dosgolem'/name)==sha
        if name not in cm['changed']:assert digest(core/'src'/name)==sha
    for name,sha in cm['changed'].items():assert digest(core/'src'/name)==sha
    log=(b/'masked-rows-prefix-r2.log').read_text()
    for name,count in [('DirectMaskedRowsNativeState',60),('DirectMaskedRowsRejectWithoutWrites',14),
                       ('DirectMaskedNativePrefix',24),('DirectRuntimeNativePrefixAndPoisonedStack',16)]:
        assert log.count('    --- PASS: TestResearch'+name+'/')==count,name
    assert log.count('--- PASS: TestResearchOwnedBatch')==2 and '\nPASS\n' in log and '\nFAIL' not in log
    cases=read(b/'masked-rows-prefix-r2.json')['cases']
    assert len(cases)==60 and all(c['same_cpu_ram_planes_each_batch'] and c['same_final_serialized_state'] for c in cases)
    assert any(c['tail_batches']>0 for c in cases)
    normal={kind:paired_run(b/('masked-rows-'+kind+'-r1'),b/('masked-rows-'+kind+'-control-r1')) for kind in ('hire','palace')}
    assert normal['hire']['frames']==542 and normal['hire']['direct']['accepted'].get('056f',0)>0
    assert normal['palace']['direct']['accepted'].get('06a3',0)>0
    assert normal['palace']['exited'] and normal['palace']['exit_code']==0
    saved=b/'masked-rows-palace-r1/scratch/gamedata.ay'
    assert saved.stat().st_size==2987
    original=p/'workplace/intake-20261023/sources/game/8sword/PAM.AY'
    assert digest(original)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
    raw=original.read_bytes()
    report=dict(schema=1,status='PASS-scoped-047-normal-masked-rows',production=False,
                build_inputs=inputs,programs=programs,core_patch_sha256=cm['patch_sha256'],
                prefix_cases=60,row_rejections=16,tests_sha256=digest(b/'masked-rows-prefix-r2.log'),
                native_row_bytes=[dict(file_start=a,file_end_exclusive=z,sha256=hashlib.sha256(raw[a:z]).hexdigest())
                                  for a,z in ((0x155ff,0x15610),(0x15733,0x1574b))],
                normal=normal,saved_bytes=2987,saved_sha256=digest(saved),
                limits=['Only admitted PAM mode1 paths; event-boundary bytes retain native execution.',
                        'Normal runs preserve seed/state; no new RNG/gameplay parity claim.',
                        'Production r49 unchanged; whole 047, intro primitives and other failures remain open.'])
    if args.gui:
        report['gui']=audit_gui(p,build,p/'workplace/player/gui/direct-rows-save-r1')
    ida=read(p/'workplace/probe-20261023/graphics-first/ida-graphics-inventory-r4.json')
    database=p/'workplace/probe-20261023/text-first/PAM.i64'
    assert ida['source_sha256']==digest(original) and ida['database_sha256']==digest(database)
    report['source']=dict(file='PAM.AY',sha256=digest(original),ida_tool=ida['tool'],
            ida_database_sha256=digest(database),
            ida_export_sha256=digest(p/'workplace/probe-20261023/graphics-first/ida-graphics-inventory-r4.json'),
            address_spaces='PAM file offsets in native_row_bytes; runtime CS:IP and IDA linear addresses separately in spec047.')
    report['tools']=dict(go=(build/'build-go-version.txt').read_text().strip(),pillow=PILLOW_VERSION,
                         python=platform.python_version(),audit_sha256=digest(Path(__file__)))
    with args.out.open('x') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],build_inputs=inputs,normal={k:dict(frames=v['frames'],direct=v['direct']) for k,v in normal.items()}),ensure_ascii=False))


if __name__=='__main__':main()
