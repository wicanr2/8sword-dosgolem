#!/usr/bin/env python3
"""042：獨立核對四鏡射姿勢、三組隔離、實際Draw及真正存退讀。Docker only。"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from PIL import ImageChops

from importlib.util import spec_from_file_location, module_from_spec


def module(name):
    spec = spec_from_file_location(name.replace('-', '_'), Path(__file__).with_name(name + '.py'))
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sources(root, original):
    calls = [json.loads(line) for line in (root / 'battle-source-calls.jsonl').read_text().splitlines()]
    calls = [c for c in calls if 'target_record' in c and 'return_step' in c]
    raw = (original / 'MAN21.EGG').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == '47cc484319abeba53551c20b7cf4b9b2c6061f2da3b6cda14155b3598f10982c'
    reverse = bytes(int(f'{v:08b}'[::-1], 2) for v in range(256))
    records = []
    for record in range(4):
        selected = [c for c in calls if c['target_record'] == record]
        assert selected
        call = read(root / f'ally21-first-{record}-call.json')
        assert call == selected[0]
        source = raw[record*3304:(record+1)*3304]
        mirrored = source[:4] + b''.join(source[j:j+11][::-1].translate(reverse) for j in range(4, 3304, 11))
        assert (root / f'ally21-first-{record}-source.bin').read_bytes() == mirrored
        assert call['source_sha256'] == hashlib.sha256(mirrored).hexdigest()
        assert call['abi_bytes_matched'] == 329 and call['mode'] == 1 and call['destination_segment'] == 0xa000
        background = (root / f'ally21-first-{record}-background.idx').read_bytes()
        returned = (root / f'ally21-first-{record}-after.idx').read_bytes()
        assert len(background) == len(returned) == 4400
        expected = bytes(sum(((mirrored[4+p*550+i//8] >> (7-i%8)) & 1) << p for p in range(4)) if mirrored[2754+i//8] >> (7-i%8) & 1 else background[i] for i in range(4400))
        assert expected == returned
        records.append(dict(record=record, calls=len(selected), pixels_verified=4400, first_return_step=call['return_step'], source_sha256=call['source_sha256']))
    return calls, records


def packets(model, root, folder, calls, actual):
    results = []
    for record in range(4):
        stem = root / folder / f'record-{record}-first-frame'
        meta = read(Path(str(stem) + '.json'))
        assert meta['record'] == record and bool(meta['actual_draw']) == actual
        assert any(c['target_record'] == record and c['return_step'] == meta['source_return_step'] <= meta['step'] for c in calls)
        cells = list(struct.iter_unpack('<HI', Path(str(stem) + '-actors.bin').read_bytes()))
        assert sum(ident == 152+record for ident, local in cells) == 4400
        row = model.frame(stem)
        row.update(record=record, source_return_step=meta['source_return_step'])
        results.append(row)
    module('audit-palace-runtime').link(root, results)
    return results


def gui_save(root, battle):
    initial = read(root / 'genuine-input.json')
    assert set(initial) == {'gamedata.ay', 'map01.ay', 'map02.ay'}
    assert initial == {name: sha(battle / 'ally21-castle-source-r1/scratch' / name) for name in initial}
    states = {phase: read(root / phase / 'gui-final.json') for phase in ('save', 'reload')}
    saved = root / 'scratch/gamedata.ay'
    assert saved.stat().st_size == 2987 and sha(saved) != initial['gamedata.ay']
    assert read(root / 'save/saved.json')['sha256'] == sha(saved)
    for phase, status in states.items():
        assert status['closed'] and status['session']['cycles_per_ms'] == 3000
        assert not status['unimplemented'] and not status['text']['Errors'] and status['text']['MissingGlyphs'] == 0
        assert not any(v for k, v in status.items() if k.endswith('_error'))
        assert read(root / phase / 'gui-input-receipt.json')['flow'] == phase
        assert read(root / phase / 'continuous-audit.json')['frames'] == status['recorded_frames']
        assert saved.read_bytes() == (root / phase / 'snapshot-readonly/save-buffer-9e000.bin').read_bytes()
        reads = [op for op in status['file_ops'] if op['Name'] == 'gamedata.ay' and op['Op'] == 'read']
        assert len(reads) == 1 and reads[0]['Len'] == 2987 and reads[0]['Pos'] == 0 and not reads[0]['Failed']
    assert states['save']['exited'] and states['save']['exit_code'] == 0
    assert not states['reload']['exited'] and states['reload']['presented_scene'] == 'map'
    for font in ('noto', 'lishu', 'caoshu'):
        status = read(root / 'save' / ('palace-character-' + font + '.json'))
        assert status['font_id'] == status['presented_font_id'] == font and status['presented_scene'] == 'character'
    for phase in states:
        assert (root / phase / ('new-army-first.json' if phase == 'save' else 'loaded-army-first.json')).exists()
        assert (root / phase / ('new-army-again.json' if phase == 'save' else 'loaded-army-again.json')).exists()
    return dict(saved_bytes=2987, saved_and_two_RAM_sha256=sha(saved), cold_read_step=reads[0]['Step'], recorded_frames={n: s['recorded_frames'] for n, s in states.items()}, companions={n: sha(root / 'scratch' / n) for n in ('map01.ay', 'map02.ay')})


def main():
    parser = argparse.ArgumentParser()
    for name in ('original', 'assets', 'battle', 'out'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--gui', type=Path)
    args = parser.parse_args()
    assert not args.out.exists()
    roots = {n: args.battle / ('friendly21-normal-' + n + ('-r2' if n == 'broken' else '-r3')) for n in ('hd', 'old', 'broken')}
    audit = module('audit-castle-background')
    finals = {n: read(p / 'final.json') for n, p in roots.items()}
    frames = finals['hd']['recorded_frames']
    for name, f in finals.items():
        assert f['normal_input_replay'] and not f['snapshot_loaded'] and not f['guest_injection']
        assert f['exited'] and f['exit_code'] == 0 and not f['unimplemented']
        assert f['recorded_frames'] == f['frame_pure_count'] == frames
        assert bool(f['battle_actor_error']) == (name == 'broken')
        assert not any(v for k, v in f.items() if k.endswith('_error') and k != 'battle_actor_error')
        for key in ('steps', 'strings', 'input_events', 'file_ops', 'exec_log', 'music', 'elapsed_ms', 'clock_baseline', 'rng_seed', 'irq1_delivered', 'bios_consumed'):
            assert f[key] == finals['old'][key], (name, key)
        for filename in ('final.state', 'frame-check.state', 'audio.pcm', 'commands.jsonl', 'continued-game.json', 'continued-companions.json', 'battle-source-calls.jsonl'):
            assert sha(roots[name] / filename) == sha(roots['old'] / filename)
        assert audit.inventory(roots[name] / 'scratch') == audit.inventory(roots['old'] / 'scratch')
        for path in roots['old'].glob('*-native.png'):
            assert sha(path) == sha(roots[name] / path.name)
    for filename in ('presentation.frames.gz', 'frames.jsonl'):
        assert sha(roots['broken'] / filename) == sha(roots['old'] / filename)
    calls, records = sources(roots['hd'], args.original)
    changed = []
    rects = {(c['x_byte']*24, c['y']*6, (c['x_byte']*8+88)*3, (c['y']+50)*6) for c in calls}
    streams = module('audit-army-dismiss')
    for left, right in zip(streams.stream(roots['hd']), streams.stream(roots['old']), strict=True):
        assert left[:2] == right[:2]
        difference = ImageChops.difference(left[2].convert('RGB'), right[2].convert('RGB'))
        if difference.getbbox():
            changed.append(left[0])
            for rect in rects:
                difference.paste((0, 0, 0), rect)
            assert not difference.getbbox(), ('change outside friendly rectangles', left[0])
    assert changed
    model = module('audit-palace-runtime').PalaceModel(args.assets, args.original, args.battle, friendly=True)
    rows = packets(model, roots['hd'], 'friendly-frames', calls, False)
    gui_rows, gui_records, save = [], [], None
    if args.gui:
        root = args.gui / 'save'
        gui_calls, gui_records = sources(root / 'research-friendly-draws', args.original)
        gui_rows = packets(model, root, 'research-friendly-draws', gui_calls, True)
        save = gui_save(args.gui, args.battle)
    result = dict(status='PASS-scoped-four-friendly-MAN21-runtime', frames_each=frames, frame_purity_checks=frames*3, state_sha256=sha(roots['hd'] / 'final.state'), pcm_sha256=sha(roots['hd'] / 'audio.pcm'), scratch_files=len(audit.inventory(roots['hd'] / 'scratch')), changed_frames=len(changed), changed_range=[min(changed), max(changed)], changes_within_friendly_rectangles=True, broken_stream_equals_old=True, sources=records, frames=rows, gui_sources=gui_records, gui_draws=gui_rows, gui_path=save, limits=['Four mirrored views of existing MAN21 poses; source catalog remains 104.', 'Unregistered other units remain native; no game-wide HD claim.', 'Headless clock 12:00/3000, original RNG seed unknown; ordinary GUI clock and RNG uncontrolled.'])
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
