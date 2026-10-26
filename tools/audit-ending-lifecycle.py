#!/usr/bin/env python3
"""053 DRAFT：核對冷啟動、受控原版覆蓋交接、完整結局與BIOS Esc。"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000
    assert not args.out.exists() and args.out.parent.stat().st_uid == 1000
    project = args.project
    batch = project/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    for revision in (1, 2, 3):
        build = read(batch/f'handoff-r{revision}-build.json')
        assert build['source_sha256'] == sha(batch/build['source'])
        assert build['binary_sha256'] == sha(batch/build['binary'])
        assert build['go'] == '1.24.13' and build['production'] is False
        assert build['core_manifest_sha256'] == sha(project/'workplace/player/runtime-direct-r1/runtime-manifest.json')
    assert sha(batch/'handoff-r3-at-run.go') == sha(project/'tools/probe-ending-handoff.go')
    source = (batch/'handoff-r3-at-run.go').read_text()
    for forbidden in ['.SetRegs(', '.FarCall(', '.CallNear(', '.Stub(', '.WriteBytes(']:
        assert forbidden not in source
    assert source.count('.WriteU16(') == 1 and 'Off: 0x56e2' in source
    names = ['handoff-normal-r1', 'handoff-controlled-r1', 'handoff-complete-r2',
             'handoff-escape-end5-r2', 'handoff-bios-end5-r3']
    runs = {name: read(batch/name/'handoff.json') for name in names}
    normal, controlled, full, wrong, bios = [runs[name] for name in names]
    entry = normal['calls'][0]
    assert entry['stage'] == 'sub_1020E-entry' and entry['step'] == 25749241
    assert entry['registers']['CS'] == 0x110 and entry['registers']['IP'] == 0x20e
    assert entry['fields']['0x56e2'] == 0
    for name, run in runs.items():
        assert run['schema'] == 1 and run['production'] is False and run['unimplemented'] == []
        assert run['clock_cycles_per_ms'] == 3000 and run['pam_load_segment'] == 0x110
        assert run['calls'][0] == entry
        if name != names[0]:
            assert run['controlled_ending_branch'] is True
            assert run['mutations'] == [dict(address=dict(Seg=0x1e88, Off=0x56e2), old=0, new=1,
                reason='controlled branch at original caller; field meaning unproven', step=25749241)]
            caller = run['calls'][1]
            assert caller['stage'] == 'original-execl-call' and caller['step'] == 31822359
            pointers = caller['pointers']
            assert [x['text'] for x in pointers[:8]] == ['pae.ay', 'pae.ay', 'v', 'a', 'y', 'a', 'n', 'g']
            assert pointers[8]['segment'] == pointers[8]['offset'] == 0
            assert run['pae_exec_seen'] is True
            pae = run['overlays'][-1]
            assert pae['Name'] == 'pae.ay' and pae['Seg'] == pae['Reloc'] == 0x110
            assert pae['Steps'] == 31824856 and pae['CallCS'] == 0x9fe5 and pae['CallIP'] == 4
            assert run['exec_log'][-1]['Base'] == 'PAE.AY' and run['exec_log'][-1]['PSP'] == 0x110
        for stem in ['01-main-menu', '02-new-game-confirm', '03-map', '04-system-menu', '05-quit-confirm']:
            assert sha(batch/name/(stem+'.png')) == sha(batch/names[0]/(stem+'.png'))
    assert normal['controlled_ending_branch'] is False and not normal['mutations'] and normal['pae_exec_seen'] is False
    assert normal['exited'] is True and normal['exit_code'] == 0 and normal['steps'] == 25752629
    assert controlled['exited'] is False and controlled['steps'] == 31840956
    catalog = {row['record_sha256']: row for row in read(batch/'source.json')['records']}
    assert full['steps'] == wrong['steps'] == 128097768
    assert len(full['ending_calls']) == 3735
    assert {r['stage'] for r in full['ending_calls']} == {f'END{i}.AY' for i in range(1, 10)}
    assert len({r['source_sha256'] for r in full['ending_calls']}) == 30
    for row in full['ending_calls']:
        assert row['source_sha256'] in catalog and row['return_step'] >= row['entry_step']
        assert row['entry']['Seg'] == 0x393 and row['ds'] == 0x7e4
        assert row['destination'] in (0xa000, 0xa400)
    # The IRQ1 attempt remains a transport diagnostic, not proof Esc was ignored.
    assert full['ending_calls'] == wrong['ending_calls'] and full['file_ops'] == wrong['file_ops']
    assert sha(batch/names[2]/'final.state') == sha(batch/names[3]/'final.state')
    assert sha(batch/names[2]/'ram-00000-9ffff.bin') == sha(batch/names[3]/'ram-00000-9ffff.bin')
    for page in full['ending_pages']:
        assert base64.b64decode(page['irq1_vector']) == bytes.fromhex('24008000')
    assert bios['steps'] == 89860581 and bios['escaped'] is True and bios['escape_route'] == 'bios'
    assert len(bios['ending_calls']) == 1929
    assert bios['ending_calls'] == full['ending_calls'][:1929]
    assert sha(batch/names[4]/'escape-before-input.state') == sha(batch/names[3]/'escape-before-input.state')
    stats = bios['escape_transport_stats']
    assert [r['bios_pending'] for r in stats] == [0, 1, 0]
    assert [r['irq1_delivered'] for r in stats] == [13, 13, 13]
    assert stats[0]['step'] == stats[1]['step'] == 89817177
    assert bios['inputs'][-1] == dict(key='Esc', route='bios', ending_stage='END5.AY', step=89817177)
    for run in [full, wrong, bios]:
        assert run['exited'] is True and run['exit_code'] == 0
    outputs = {name: {str(f.relative_to(batch/name)): sha(f) for f in (batch/name).rglob('*') if f.is_file()}
               for name in names}
    result = dict(schema=1, spec='053', production=False, status='verified-controlled-original-ending-lifecycle',
                  tool_sha256=sha(Path(__file__)), current_probe_sha256=sha(project/'tools/probe-ending-handoff.go'),
                  inputs={n: sha(project/'workplace/intake-20261023/sources/game/8sword'/n)
                          for n in ['PREDELLA.EXE', 'PAM.AY', 'PAE.AY']},
                  builds={f'handoff-r{i}-build.json': sha(batch/f'handoff-r{i}-build.json') for i in (1, 2, 3)},
                  original_normal_quit_steps=normal['steps'], controlled_overlay_step=31824856,
                  load_segment=0x110, reloc_segment=0x110, complete_steps=full['steps'],
                  complete_source_calls=3735, unique_sources=30, complete_state_sha256=sha(batch/names[2]/'final.state'),
                  bios_escape_input_step=89817177, bios_escape_exit_step=89860581,
                  bios_escape_source_calls=1929, bios_escape_state_sha256=sha(batch/names[4]/'final.state'),
                  outputs=outputs,
                  limits=['The sole RAM mutation selects an original cleanup branch; this is not natural completion.',
                          'Original AH=4B03 overlay handoff, not a fabricated call or AH=4B00 child process.',
                          'IRQ1-only attempt does not validate Esc. BIOS Esc is consumed and exits in the sampled END5 path.',
                          'END7 appears in source calls without BIOS page flip; absence from page samples is not absence from rendering.',
                          'No HD, production, GUI, audio-listening or generalization to every ending input stage.'])
    with args.out.open('x') as handle:
        handle.write(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(status=result['status'], complete_calls=3735, bios_escape_calls=1929, sha256=sha(args.out))))


if __name__ == '__main__':
    main()
