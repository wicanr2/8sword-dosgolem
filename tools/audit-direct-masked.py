#!/usr/bin/env python3
"""047 DRAFT：獨立核對固定r31六平面攔截研究，不代表正式切換或全遊戲驗收。"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path

from PIL import Image


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda: f.read(1024*1024), b''):
            h.update(data)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def verify_manifest(path, root):
    entries = {}
    for line in path.read_text().splitlines():
        sha, name = line.split('  ', 1)
        assert name not in entries and digest(root/name) == sha, name
        entries[name] = sha
    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--controlled', action='store_true', help='追加r49三組兩向／兩入口的受控自有呈現核對')
    args = parser.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000
    assert not args.out.exists() and args.out.parent.stat().st_uid == 1000
    p = args.project
    battle = p/'workplace/probe-20261023/graphics-first/battle-r1'
    build, core = battle/'owned-live-build-r31', battle/'core-direct-r6'
    control, run = battle/'masked-hire-control-r1', battle/'masked-hire-r1'
    inputs = verify_manifest(build/'build-inputs.sha256', build/'src')
    outputs = verify_manifest(build/'build-outputs.sha256', build)
    manifest = read(core/'runtime-manifest.json')
    assert digest(core/'runtime.patch') == manifest['patch_sha256']
    for name, sha in manifest['base_inputs'].items():
        assert digest(p/'workplace/dosgolem'/name) == sha
        if name not in manifest['changed']:
            assert digest(core/'src'/name) == sha
    for name, sha in manifest['changed'].items():
        assert digest(core/'src'/name) == sha
    # Bind the actual tested sources to the frozen build, not today's tools.
    tests = (battle/'masked-prefix-r2.log').read_text()
    expected = {'DirectMaskedNativePrefix': 24, 'DirectMaskedRejectsWithoutWrites': 10,
                'DirectRuntimeNativePrefixAndPoisonedStack': 16}
    for name, count in expected.items():
        assert tests.count('    --- PASS: TestResearch'+name+'/') == count, name
    for name in ('DirectMaskedNativeTrace', 'HostPlanarReadPreparation',
                 'DirectRuntimeRejectsWithoutWrites'):
        assert '--- PASS: TestResearch'+name+' ' in tests
    assert '\nPASS\n' in tests and '\nFAIL' not in tests
    assert tests.count('--- PASS: TestResearchOwnedBatch') == 2
    core_tests = (core/'host-call-tests-r1.log').read_text()
    assert core_tests.count('--- PASS: TestResearchHostCall') == 3 and '\nPASS\n' in core_tests
    export = p/'workplace/probe-20261023/graphics-first/ida-graphics-inventory-r4.json'
    ida = read(export)
    original = p/'workplace/intake-20261023/sources/game/8sword/PAM.AY'
    assert digest(original) == ida['source_sha256']
    assert ida['tool'] == 'IDA 9.4'
    assert digest(p/'workplace/probe-20261023/text-first/PAM.i64') == ida['database_sha256']
    raw = original.read_bytes()
    functions = []
    for name, start, stop, entry, ret in (
            ('sub_24112', 0x15582, 0x156b6, 0x4f2, 0x625),
            ('sub_24246', 0x156b6, 0x157ff, 0x626, 0x76e)):
        f = next(f for f in ida['functions'] if f['name'] == name)
        at = start
        padding = []
        for instruction in f['lines']:
            data = bytes.fromhex(instruction['bytes'])
            # IDA omitted one-byte NOP alignment at three branch boundaries.
            # Retain exact offsets/bytes; never silently skip arbitrary gaps.
            gap = instruction['file_offset']-at
            assert gap in (0, 1)
            if gap:
                assert raw[at:at+gap] == b'\x90'
                padding.append(dict(file_offset=at,bytes='90'))
                at += gap
            assert raw[at:at+len(data)] == data
            at += len(data)
        assert at == stop and raw[stop-1] == 0xcb
        functions.append(dict(original_name=name, ida_linear_start=f['start'], ida_linear_end_exclusive=f['end'],
                              file_start=start, file_end_exclusive=stop, runtime_cs=0x14d2,
                              runtime_entry=entry, runtime_retf=ret,
                              sha256=hashlib.sha256(raw[start:stop]).hexdigest(),
                              ida_unlisted_padding=padding,inference='confirmed'))
    paired = {}
    for name in ('final.state', 'audio.pcm', 'commands.jsonl', 'frames.jsonl',
                 'owned-commands.jsonl', 'owned-intro-commands.jsonl', 'vga-reads.json'):
        assert digest(run/name) == digest(control/name), name
        paired[name] = digest(run/name)
    def stream_sha(path):
        h = hashlib.sha256()
        with gzip.open(path, 'rb') as f:
            for data in iter(lambda: f.read(1024*1024), b''):
                h.update(data)
        return h.hexdigest()
    assert stream_sha(run/'presentation.frames.gz') == stream_sha(control/'presentation.frames.gz')
    paired['decompressed_frames'] = stream_sha(run/'presentation.frames.gz')
    files = lambda root: {str(f.relative_to(root)): digest(f) for f in root.rglob('*') if f.is_file()}
    scratch = files(run/'scratch')
    assert scratch == files(control/'scratch')
    final = read(run/'final.json')
    assert final['frame_pure_count'] == final['recorded_frames'] == 542
    assert not final['unimplemented'] and not final['text']['Errors'] and final['text']['MissingGlyphs'] == 0
    assert {e['font_id'] for e in rows(run/'frames.jsonl')} == {'noto', 'lishu', 'caoshu'}
    receipt, old = read(run/'direct-runtime-receipt.json'), read(control/'direct-runtime-receipt.json')
    assert receipt['bound'] and not receipt['control'] and not receipt['production']
    assert old['control'] and not old['counts']
    assert receipt['pam_source_frames'] > 0 and receipt['pam_legacy_rgb_frames'] == 0
    source = {(e['entry_step'], e['entry']): e for e in rows(run/'owned-commands.jsonl') if e['command'] == 'bitmap'}
    accepted, steps, cycles, compatibility = {}, 0, 0, 0
    commands = rows(run/'direct-runtime-commands.jsonl')
    for event in commands:
        plan = event['plan']
        entry, end = event['entry_step'], event['return_boundary_step']
        e = source[entry, plan['Entry']]
        assert e['step'] == end and e['source_sha256'] == plan['SourceSHA256']
        assert tuple(e[k] for k in ('x_byte','y','width_bytes','height','dest')) == tuple(
            plan[k] for k in ('XByte','Y','WidthBytes','Height','Destination'))
        w, h, site = plan['WidthBytes'], plan['Height'], plan['Entry']
        assert plan['ReturnBoundary'] == {0x99c:0xa6f,0x76f:0x854,0x4f2:0x625,0x626:0x76e}[site]
        expected_steps = 32*h+81 if site in (0x99c,0x76f) else 4*h*((12 if site==0x626 else 9)*w+7)+111
        assert plan['Steps'] == end-entry == expected_steps
        assert plan['Cycles'] == expected_steps+4*w*h
        assert event['original_pixel_instructions_executed'] == 0
        accepted[hex(site)] = accepted.get(hex(site), 0)+1
        steps += plan['Steps']; cycles += plan['Cycles']; compatibility += 4*w*h
    # This fixed route reaches twelve masked calls. The whole-prefix budget
    # conservatively rejects them; controlled tests carry the positive evidence.
    masked_calls = [e for e in source.values() if e['entry'] in (0x4f2,0x626)]
    assert len(masked_calls) == 12 and not accepted.get('0x4f2', 0) and not accepted.get('0x626', 0)
    counts = receipt['counts']
    assert counts['accepted'] == len(commands)
    assert counts['virtual-instructions'] == steps and counts['virtual-cycles'] == cycles
    assert counts['compatibility-plane-bytes'] == compatibility
    for site, count in accepted.items():
        assert counts['accepted-'+format(int(site,16),'04x')] == count
    report = dict(schema=1, status='passed-limited-research', production=False,
                  source=dict(file='PAM.AY',sha256=digest(original),ida_tool=ida['tool'],
                              database_sha256=ida['database_sha256'],export_sha256=digest(export),functions=functions),
                  build=dict(inputs=len(inputs),programs=outputs,core_changed=manifest['changed'],
                             core_patch_sha256=manifest['patch_sha256'],tests_sha256=digest(battle/'masked-prefix-r2.log')),
                  prefix_cases=24,rejection_cases=12,old_prefix_cases=16,host_call_tests=3,
                  normal=dict(frames=542,paired=paired,scratch_files=len(scratch),accepted=accepted,
                              virtual_instructions=steps,virtual_cycles=cycles,compatibility_bytes=compatibility,
                              masked_source_calls=len(masked_calls),masked_calls_skipped=0,
                              pam_source_frames=receipt['pam_source_frames'],pam_legacy_rgb_frames=0,
                              fallbacks={k:v for k,v in counts.items() if k.startswith('fallback-')}),
                  limits=['0626 background entry has native-prefix controlled tests, not natural battle in this run.',
                          'All twelve normal masked calls retain native execution; positive skip evidence is controlled only.',
                          'No new GUI/save-cycle claim; production r49 remains unchanged.',
                          'Original readback uses indexed compatibility planes; no original RGB underlay.',
                          'No gameplay/RND changes or hardware timing parity claim.'])
    if args.controlled:
        current = battle/'masked-controlled-troops-r1'
        previous = battle/'troops-controlled-r1'
        owned = battle/'masked-controlled-owned-r1'
        fixture = read(current/'receipt.json')
        prior = read(previous/'receipt.json')
        log = (battle/'masked-controlled-troops-r1.log').read_text()
        assert '--- PASS: TestTroopsControlledOriginalDraw' in log and '\nPASS\n' in log
        assert '--- SKIP:' not in log and '\nFAIL' not in log
        assert fixture['status'] == prior['status'] == 'PASS-controlled-original-draw-not-natural-encounter'
        assert not fixture['rules_changed'] and fixture['source_files_unchanged']
        assert fixture['controlled_memory']['source_buffer'] == '8000:0000'
        assert fixture['cases'] == prior['cases'] and len(fixture['cases']) == 12
        actors = [e for e in rows(owned/'owned-commands.jsonl') if e['command']=='bitmap' and e['actor']>=160]
        assert len(actors) == 12
        for row, source in zip(fixture['cases'], actors):
            assert row['frame_pure'] and row['pixels'] == 1920*1200
            assert source['actor'] == row['id'] and source['material'] == row['id']
            assert source['entry'] == (0x626 if row['battle'] else 0x4f2)
            assert (source['x_byte'],source['y'],source['width_bytes'],source['height']) == (20,60,11,50)
            # New source renderer must match the previously verified independent
            # full background/actor model, beyond agreement with its own code.
            im = Image.open(current/row['png']).convert('RGBA')
            old_im = Image.open(previous/row['png']).convert('RGBA')
            assert im.size == old_im.size == (1920,1200)
            assert im.tobytes() == old_im.tobytes()
            assert hashlib.sha256(im.tobytes()).hexdigest() == row['frame_sha256']
        direct = read(owned/'direct-runtime-receipt.json')
        assert direct['pam_source_frames'] > 0 and direct['pam_legacy_rgb_frames'] == 0
        report['controlled_owned_renderer'] = dict(cases=12,pixels=27648000,
                fixture_sha256=digest(current/'receipt.json'),prior_fixture_sha256=digest(previous/'receipt.json'),
                test_sha256=digest(battle/'masked-controlled-troops-r1.log'),
                owned_commands_sha256=digest(owned/'owned-commands.jsonl'),
                pam_source_frames=direct['pam_source_frames'],pam_legacy_rgb_frames=0,
                limitation='CallBudget uses arbitrary stop condition and retains native pixel instructions; no controlled CPU-skip claim.')
    with args.out.open('x') as f:
        f.write(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],frames=542,accepted=accepted,virtual_instructions=steps),ensure_ascii=False))


if __name__ == '__main__':
    main()
