#!/usr/bin/env python3
"""047 DRAFT：直接從來源命令繪製戰場；原版Frame僅供輸出比較。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
import struct
from pathlib import Path

from PIL import Image

EGA = [(0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170), (170, 0, 0), (170, 0, 170), (170, 85, 0), (170, 170, 170), (85, 85, 85), (85, 85, 255), (85, 255, 85), (85, 255, 255), (255, 85, 85), (255, 85, 255), (255, 255, 85), (255, 255, 255)]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def sampler():
    spec = importlib.util.spec_from_file_location('source_sampling', Path(__file__).with_name('audit-encounter-gui.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.sample


def source_catalog(original):
    reverse = bytes(int(f'{v:08b}'[::-1], 2) for v in range(256))
    catalog = {}
    for path in sorted(original.glob('MAN*.EGG')):
        raw = path.read_bytes()
        assert len(raw) == 13216
        for i in range(4):
            record = raw[i*3304:(i+1)*3304]
            assert struct.unpack_from('<HH', record) == (11, 50)
            mirrored = record[:4] + b''.join(record[j:j+11][::-1].translate(reverse) for j in range(4, 3304, 11))
            for data in (record, mirrored):
                catalog[sha(data)] = data
    return catalog


def assets_from_sources(assets, original):
    sample = sampler()
    background = sample(assets / 'battle-palace-background-r1.png', 1920, 1200)
    assert sha(background) == 'ee95cca6642a98ed4bdcb14415e19553d6efbb558b4fbf375ca2ba119abd9955'
    textures = {}
    for manifest, source in [('battle-actors.json', 'MAN16.EGG'), ('battle-man06.json', 'MAN06.EGG'), ('battle-man11.json', 'MAN11.EGG'), ('battle-man21.json', 'MAN21.EGG')]:
        m = read(assets / manifest)
        raw = (original / source).read_bytes()
        assert sha(raw) == m['source_sha256']
        for i, entry in enumerate(m['frames']):
            e = entry['image']
            assert sha((assets / e['file']).read_bytes()) == e['sha256']
            x, y, w, h = entry['target_rect']
            sampled = sample(assets / e['file'], w, h, actor=True, rect=e['source_rect'])
            full = bytearray(264*300*4)
            for row in range(h):
                start = ((row+y)*264+x)*4
                full[start:start+w*4] = sampled[row*w*4:(row+1)*w*4]
            textures[sha(raw[i*3304:(i+1)*3304])] = bytes(full)
    m = read(assets / 'battle-militia.json')
    data = sample(assets / m['image_file'], 264, 300, actor=True)
    assert sha(data) == m['cache_sha256']
    textures[m['record_sha256']] = data
    m = read(assets / 'battle-friendly-man21.json')
    raw = (original / 'MAN21.EGG').read_bytes()
    for i, entry in enumerate(m['frames']):
        original_texture = textures[sha(raw[i*3304:(i+1)*3304])]
        mirrored = b''.join(original_texture[(y*264+x)*4:(y*264+x+1)*4] for y in range(300) for x in range(263, -1, -1))
        assert sha(mirrored) == entry['cache_sha256']
        textures[entry['record_sha256']] = mirrored
    return background, textures


def scene_from_commands(commands, step, catalog):
    slots = {}
    for c in commands:
        if 'return_step' not in c or c['return_step'] > step:
            continue
        assert c['source_sha256'] in catalog
        assert c['destination_segment'] == 0xa000 and c['mode'] == 1
        assert c['width_bytes'] == 11 and c['height'] == 50
        x, y = c['x_byte']*8, c['y']
        assert 0 <= x <= 552 and 0 <= y <= 150
        slots[x, y] = dict(x=x, y=y, source_sha256=c['source_sha256'], source_return_step=c['return_step'])
    assert len(slots) == 8
    # This pilot samples the established non-overlapping eight-slot battlefield.
    values = list(slots.values())
    for i, a in enumerate(values):
        for b in values[i+1:]:
            assert a['x']+88 <= b['x'] or b['x']+88 <= a['x'] or a['y']+50 <= b['y'] or b['y']+50 <= a['y']
    return dict(width=1920, height=1200, background='GRO01.EG', actors=sorted(values, key=lambda a: a['source_return_step']))


def render(scene, background, textures, catalog):
    """The renderer receives only our scene and source assets; no oracle/frame input."""
    pixels = bytearray(background)
    for actor in scene['actors']:
        digest = actor['source_sha256']
        texture = textures.get(digest)
        if texture is None:
            raw = catalog[digest]
            texture = bytearray(264*300*4)
            for i in range(4400):
                if raw[2754+i//8] >> (7-i%8) & 1:
                    color = sum(((raw[4+p*550+i//8] >> (7-i%8)) & 1) << p for p in range(4))
                    for dy in range(6):
                        start = ((i//88*6+dy)*264+i%88*3)*4
                        texture[start:start+12] = (bytes(EGA[color])+b'\xff')*3
        for y in range(300):
            for x in range(264):
                src = (y*264+x)*4
                dest = ((actor['y']*6+y)*1920+actor['x']*3+x)*4
                alpha = texture[src+3]
                for c in range(3):
                    pixels[dest+c] = min(255, texture[src+c]+(pixels[dest+c]*(255-alpha)+127)//255)
    return Image.frombytes('RGBA', (1920, 1200), bytes(pixels))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('original', 'assets', 'source', 'target', 'out'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    assert not args.out.exists()
    meta = read(Path(str(args.target)+'.json'))
    assert not meta['pending'] and not meta['visible_sources']
    assert not read(Path(str(args.target)+'-layers.json'))['effects']
    assert sha((args.original / 'GRO01.EG').read_bytes()) == '4e5c5c6569cc6fc9f1e585b7048c099228f787da041d46ded685e034b7594103'
    backgrounds = [json.loads(line) for line in (args.source / 'gro01-background-calls.jsonl').read_text().splitlines()]
    backgrounds = [c for c in backgrounds if c.get('return_step', meta['step']+1) <= meta['step'] and c.get('destination_segment') == 0xa000]
    assert backgrounds
    bg = backgrounds[-1]
    assert bg['source_sha256'] == '79e2c0119edf4ca9f87fb14dbee47de49afca4eee8f8cc2711c4c58c275e7be9'
    assert (bg['width_bytes'], bg['height'], bg['x_byte'], bg['y'], bg['mode']) == (80, 200, 0, 0, 1)
    catalog = source_catalog(args.original)
    commands = [json.loads(line) for line in (args.source / 'battle-source-calls.jsonl').read_text().splitlines()]
    scene = scene_from_commands(commands, meta['step'], catalog)
    scene['background_source_return_step'] = bg['return_step']
    background, textures = assets_from_sources(args.assets, args.original)
    image = render(scene, background, textures, catalog)
    # The captured frame is used only here, after independent scene rendering.
    expected = Image.open(Path(str(args.target)+'.png')).convert('RGBA')
    assert image.tobytes() == expected.tobytes(), 'owned scene differs from reference'
    args.out.mkdir()
    image.save(args.out / 'owned-scene.png')
    (args.out / 'scene.json').write_text(json.dumps(scene, indent=2)+'\n')
    record = dict(status='PASS-DRAFT-owned-battle-scene-pilot', step=meta['step'], full_pixels=2304000, actors=len(scene['actors']), original_decoded_actors=sum(a['source_sha256'] not in textures for a in scene['actors']), RGBA_sha256=sha(image.tobytes()), source_commands_sha256=sha((args.source / 'battle-source-calls.jsonl').read_bytes()), renderer_inputs=['typed scene', 'original source bitmaps', 'HD source assets'], forbidden_renderer_inputs=['VGA framebuffer', 'native index dump', 'ownership dump', 'captured frame'], comparison_only=str(args.target)+'.png', limits=['offline prototype only; not live frontend or production', 'one eight-slot battle frame without text or effects', 'does not prove flicker fixed'])
    (args.out / 'receipt.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record))


if __name__ == '__main__':
    main()
