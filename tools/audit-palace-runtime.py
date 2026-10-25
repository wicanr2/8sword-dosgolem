#!/usr/bin/env python3
"""046：獨立重建正式攻城 Frame／Draw，核對三組客體與回退。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
import struct
from pathlib import Path

from PIL import Image


def module(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), Path(__file__).with_name(name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def read(path):
    return json.loads(path.read_text())


def sha(data):
    return hashlib.sha256(data).hexdigest()


class PalaceModel:
    def __init__(self, assets, original, battle):
        self.common = module('audit-encounter-gui')
        self.model = self.common.Model(assets, original, battle)
        self.battle, self.assets = battle, assets
        data = self.common.sample(assets / 'battle-palace-background-r1.png', 1920, 1200)
        assert sha(data) == 'ee95cca6642a98ed4bdcb14415e19553d6efbb558b4fbf375ca2ba119abd9955'
        self.model.materials[151] = data, 640, 200
        self.raw = {}
        for group, name in enumerate(('man16', 'man06', 'man11', 'man21')):
            manifest = read(assets / ('battle-actors.json' if name == 'man16' else 'battle-' + name + '.json'))
            for i, entry in enumerate(manifest['frames']):
                image = entry['image']
                assert sha((assets / image['file']).read_bytes()) == image['sha256']
                x, y, w, h = entry['target_rect']
                sampled = self.common.sample(assets / image['file'], w, h, actor=True, rect=image['source_rect'])
                full = bytearray(264 * 300 * 4)
                for row in range(h):
                    start = ((row + y) * 264 + x) * 4
                    full[start:start + w * 4] = sampled[row * w * 4:(row + 1) * w * 4]
                data = bytes(full)
                assert data == (battle / (name + '-art-r1') / f'cache-frame-{i}.rgba').read_bytes()
                self.model.actors[87 + group * 4 + i] = data, 88, 50
                self.raw[87 + group * 4 + i] = (original / (name.upper() + '.EGG')).read_bytes()[i * 3304:(i + 1) * 3304]
        data = self.common.sample(assets / 'militia-painted-r1.png', 264, 300, actor=True)
        assert sha(data) == '1c795ec9e8d67feca9a014d3b3511bc9ed9d9d115102e8042e4a16b3b4982fe5'
        self.model.actors[107] = data, 88, 50
        raw = (original / 'MAN01.EGG').read_bytes()[:3304]
        reverse = bytes(int(f'{v:08b}'[::-1], 2) for v in range(256))
        self.raw[107] = raw[:4] + b''.join(raw[i:i + 11][::-1].translate(reverse) for i in range(4, 3304, 11))
        self.native_bg = (battle / 'gro01-art-r1/gro01-decoded.idx').read_bytes()

    def frame(self, stem):
        path = lambda suffix: Path(str(stem) + suffix)
        meta = read(path('.json'))
        assert not meta['pending']
        assert path('-before.state').read_bytes() == path('-after.state').read_bytes()
        native = bytearray(path('-native.idx').read_bytes())
        owners = list(struct.iter_unpack('<HI', path('-background.bin').read_bytes()))
        actors = list(struct.iter_unpack('<HI', path('-actors.bin').read_bytes()))
        effects = list(struct.iter_unpack('<HI', path('-effects.bin').read_bytes()))
        text = list(struct.iter_unpack('<IHB', path('-text.bin').read_bytes()))
        glyphs = {int(k): v for k, v in read(path('-glyphs.json')).items()}
        assert len(native) == len(owners) == len(actors) == len(effects) == len(text) == 128000
        assert {ident for ident, local in owners if ident} == {151}
        assert not any(152 <= ident <= 155 for ident, local in actors)
        fx_info = read(path('-layers.json'))['effects']
        fx_cache = {}
        base = path('-effect-base.idx').read_bytes()
        for key, source in fx_info.items():
            key = int(key)
            assert 108 <= source <= 111
            data = (self.battle / 'choi-art-r1' / f'cache-frame-{source - 108}.rgba').read_bytes()
            assert sha(data) == read(self.assets / 'battle-choi.json')['frames'][source - 108]['cache_sha256']
            assert path(f'-effect-cache-{key}.rgba').read_bytes() == data
            fx_cache[key] = data
        for i, (ident, local) in enumerate(effects):
            if not ident:
                continue
            assert ident in fx_cache and local < 4400
            actor, actor_local = actors[i]
            assert actor in self.raw
            raw = self.raw[actor]
            offset, bit = actor_local // 8, 7 - actor_local % 8
            expected = sum(((raw[4 + p * 550 + offset] >> bit) & 1) << p for p in range(4)) if raw[2754 + offset] >> bit & 1 else self.native_bg[i]
            assert base[i] == expected, ('effect base', i, actor)
            native[i] = base[i]
        palette = meta['display']['Palette']
        assert [tuple(c) for c in palette] == self.common.EGA
        rgba, groups = bytearray(128000 * 4), set()
        for i, color in enumerate(native):
            ident, local, ink = text[i]
            g = glyphs.get(ident)
            if g:
                groups.add((ident, i // 640 - local // g['Width'], i % 640 - local % g['Width']))
                if ink and color == g['FG']:
                    color = g['Before'][local] if g['BG'] == 255 else g['BG']
            rgba[i * 4:i * 4 + 4] = bytes(palette[color & 15]) + b'\xff'
        out = bytearray(Image.frombytes('RGBA', (640, 200), bytes(rgba)).resize((1920, 1200), Image.Resampling.NEAREST).tobytes())
        for i, (ident, local) in enumerate(owners):
            if not ident:
                continue
            data, w, h = self.model.material(ident)
            assert local < w * h
            for dy in range(6):
                dst = ((i // 640 * 6 + dy) * 1920 + i % 640 * 3) * 4
                src = ((local // w * 6 + dy) * w * 3 + local % w * 3) * 4
                out[dst:dst + 12] = data[src:src + 12]
        for cells, effect in ((actors, False), (effects, True)):
            for i, (ident, local) in enumerate(cells):
                if not ident:
                    continue
                data, w, h = (fx_cache[ident], 88, 50) if effect else self.model.actor(ident)
                assert local < w * h
                for dy in range(6):
                    for dx in range(3):
                        dst = ((i // 640 * 6 + dy) * 1920 + i % 640 * 3 + dx) * 4
                        src = ((local // w * 6 + dy) * w * 3 + local % w * 3 + dx) * 4
                        alpha = data[src + 3]
                        for c in range(3):
                            out[dst + c] = min(255, data[src + c] + (out[dst + c] * (255 - alpha) + 127) // 255)
        atlas, font = self.model.font(meta['font_id'])
        for ident, y, x in sorted(groups):
            g = glyphs[ident]
            if g['Rune'] == 32:
                continue
            ix, iy, iw, ih = font[g['Rune']]
            if iw <= 0 or ih <= 0:
                continue
            dw, dh = min(iw, g['Width'] * 3), min(ih, 90)
            left, top = x * 3 + (g['Width'] * 3 - dw) // 2, y * 6 + (90 - dh) // 2
            color = {10: [223, 195, 121], 12: [215, 112, 89], 14: [255, 241, 181]}.get(g['FG'], palette[g['FG']])
            for yy in range(dh):
                for xx in range(dw):
                    ox, oy = left + xx, top + yy
                    if not (0 <= ox < 1920 and 0 <= oy < 1200):
                        continue
                    nx, ny = ox // 3, oy // 6
                    owner, local, _ = text[ny * 640 + nx]
                    if owner != ident or local % g['Width'] != nx - x or local // g['Width'] != ny - y:
                        continue
                    a = atlas.getpixel((ix + xx * iw // dw, iy + yy * ih // dh))[3]
                    at = (oy * 1920 + ox) * 4
                    for c in range(3):
                        out[at + c] = (color[c] * a + out[at + c] * (255 - a) + 127) // 255
        actual = Image.open(path('.png')).convert('RGBA').tobytes()
        assert bytes(out) == actual, (stem.name, 'whole-frame mismatch', sum(a != b for a, b in zip(out, actual)))
        return dict(packet=str(stem), font_id=meta['font_id'], actual_draw=meta['actual_draw'], frame_ordinal=meta['frame_ordinal'], step=meta['step'], full_pixels=2304000, state_pure=True, rgba_sha256=sha(actual), effect_sources=list(fx_info.values()))


def link(root, rows):
    wanted = {(r['actual_draw'] or r['frame_ordinal']): r for r in rows}
    for ordinal, step, image in module('audit-army-dismiss').stream(root):
        if ordinal in wanted:
            r = wanted.pop(ordinal)
            assert step == r['step'] and sha(image.tobytes()) == r['rgba_sha256']
    assert not wanted


def gui_path(root, battle):
    initial = read(root / 'genuine-input.json')
    original_save = battle / 'ally21-castle-source-r1/scratch'
    assert initial == {name: sha((original_save / name).read_bytes()) for name in initial}
    statuses = {n: read(root / n / 'gui-final.json') for n in ('save', 'reload')}
    for phase, status in statuses.items():
        assert status['closed'] and status['session']['cycles_per_ms'] == 3000
        assert not status['unimplemented'] and not status['text']['Errors'] and status['text']['MissingGlyphs'] == 0
        assert not any(v for k, v in status.items() if k.endswith('_error'))
        assert read(root / phase / 'gui-input-receipt.json')['flow'] == phase
        assert read(root / phase / 'continuous-audit.json')['frames'] == status['recorded_frames']
    assert statuses['save']['exited'] and statuses['save']['exit_code'] == 0
    assert not statuses['reload']['exited'] and statuses['reload']['presented_scene'] == 'map'
    saved = (root / 'scratch/gamedata.ay').read_bytes()
    assert len(saved) == 2987 and sha(saved) != initial['gamedata.ay']
    assert read(root / 'save/saved.json')['sha256'] == sha(saved)
    for phase in statuses:
        assert saved == (root / phase / 'snapshot-readonly/save-buffer-9e000.bin').read_bytes()
        reads = [op for op in statuses[phase]['file_ops'] if op['Name'] == 'gamedata.ay' and op['Op'] == 'read']
        assert len(reads) == 1 and reads[0]['Pos'] == 0 and reads[0]['Len'] == 2987 and not reads[0]['Failed']
    for font in ('noto', 'lishu', 'caoshu'):
        status = read(root / 'save' / ('palace-character-' + font + '.json'))
        assert status['font_id'] == status['presented_font_id'] == font
        assert status['presented_scene'] == 'character' and not status['text']['Errors']
    source = root / 'save/research-palace-draws'
    assert (source / 'gro01-first-a000-source.bin').read_bytes() == (battle / 'gro01-art-r1/gro01-decoded.bin').read_bytes()
    for name in ('gro01-first-a000-after.idx', 'gro01-before-first-actor-a000.idx', 'gro01-before-first-actor-a400.idx'):
        assert (source / name).read_bytes() == (battle / 'gro01-art-r1/gro01-decoded.idx').read_bytes()
    return dict(normal_start='Continue with genuine three-file save; no snapshot entry', saved_bytes=len(saved), saved_and_two_RAM_sha256=sha(saved), cold_read_step=reads[0]['Step'], source_return=read(source / 'gro01-first-a000-call.json'), recorded_frames={n: s['recorded_frames'] for n, s in statuses.items()}, character_fonts=['noto', 'lishu', 'caoshu'], saved_companions={name: sha((root / 'scratch' / name).read_bytes()) for name in ('map01.ay', 'map02.ay')})


def main():
    parser = argparse.ArgumentParser()
    for name in ('original', 'assets', 'battle', 'out'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--gui', type=Path)
    args = parser.parse_args()
    assert not args.out.exists()
    model = PalaceModel(args.assets, args.original, args.battle)
    roots = {n: args.battle / ('palace-normal-' + n + '-r1') for n in ('hd', 'old', 'broken')}
    audit = module('audit-castle-background')
    frames = read(roots['hd'] / 'final.json')['recorded_frames']
    # The broken group has its expected load error; compare guest evidence separately.
    finals = {n: read(p / 'final.json') for n, p in roots.items()}
    for n, final in finals.items():
        assert final['normal_input_replay'] and not final['snapshot_loaded'] and not final['guest_injection']
        assert final['exited'] and final['exit_code'] == 0 and not final['unimplemented']
        assert final['recorded_frames'] == final['frame_pure_count'] == frames
        assert bool(final['battle_background_error']) == (n == 'broken')
        assert not any(v for k, v in final.items() if k.endswith('_error') and k != 'battle_background_error')
        for key in ('steps', 'strings', 'input_events', 'file_ops', 'exec_log', 'music', 'elapsed_ms', 'clock_baseline', 'rng_seed', 'irq1_delivered', 'bios_consumed'):
            assert final[key] == finals['old'][key], (n, key)
        for name in ('final.state', 'frame-check.state', 'audio.pcm', 'commands.jsonl', 'continued-game.json', 'continued-companions.json'):
            assert audit.sha(roots[n] / name) == audit.sha(roots['old'] / name), (n, name)
        assert audit.inventory(roots[n] / 'scratch') == audit.inventory(roots['old'] / 'scratch')
        for p in roots['old'].glob('*-native.png'):
            assert audit.sha(p) == audit.sha(roots[n] / p.name)
    for name in ('frames.jsonl', 'presentation.frames.gz'):
        assert audit.sha(roots['old'] / name) == audit.sha(roots['broken'] / name)
    native = (args.battle / 'gro01-art-r1/gro01-decoded.idx').read_bytes()
    assert len(native) == 128000 and sha(native) == '1fe7cd51da104b5274b20fc276956e6f8b66abfb0a8ffde9d40d0f0307acf6fc'
    source = (args.battle / 'gro01-art-r1/gro01-decoded.bin').read_bytes()
    assert sha(source) == '79e2c0119edf4ca9f87fb14dbee47de49afca4eee8f8cc2711c4c58c275e7be9'
    for root in roots.values():
        assert (root / 'gro01-first-a000-source.bin').read_bytes() == source
        for name in ('gro01-first-a000-after.idx', 'gro01-before-first-actor-a000.idx', 'gro01-before-first-actor-a400.idx'):
            assert (root / name).read_bytes() == native
    changed = []
    start = read(roots['hd'] / 'gro01-first-a000-call.json')['return_step']
    end = read(roots['hd'] / '23-retreat-result.json')['steps']
    streams = module('audit-army-dismiss')
    for left, right in zip(streams.stream(roots['hd']), streams.stream(roots['old']), strict=True):
        ordinal, step, image = left
        assert (ordinal, step) == right[:2]
        if image.tobytes() != right[2].tobytes():
            assert start <= step <= end, ('change outside battle', ordinal, step)
            changed.append(ordinal)
    assert changed
    rows = [model.frame(roots['hd'] / ('full-battle-font-' + font)) for font in ('noto', 'lishu', 'caoshu')]
    link(roots['hd'], rows)
    gui_rows, gui_receipt = [], None
    if args.gui:
        root = args.gui / 'save'
        gui_rows = [model.frame(root / 'research-palace-draws' / ('font-' + font + '-first-draw')) for font in ('noto', 'lishu', 'caoshu')]
        assert all(r['actual_draw'] > 0 for r in gui_rows)
        link(root, gui_rows)
        gui_receipt = gui_path(args.gui, args.battle)
    report = dict(status='PASS-scoped-palace-background-runtime', frames_each=frames, frame_purity_checks=frames * 3, state_sha256=audit.sha(roots['hd'] / 'final.state'), pcm_sha256=audit.sha(roots['hd'] / 'audio.pcm'), scratch_files=len(audit.inventory(roots['hd'] / 'scratch')), broken_stream_equals_old=True, changed_frames=len(changed), changed_range=[min(changed), max(changed)], changes_within_battle=True, frames=rows, gui_draws=gui_rows, gui_path=gui_receipt, limits=['Only GRO01 background; friendly 152–155 absent.', 'Battle count glyphs are numerals; actual Chinese in all three fonts is sampled on F1.', 'Pending full-07-battle-ready is retained and excluded from current-layer reconstruction.'])
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
