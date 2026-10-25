#!/usr/bin/env python3
"""049：十四筆ENEMY圖候選、獨立快取及原版／HD總覽；不提升正式組。"""
import argparse
from collections import Counter
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil

from PIL import Image, ImageDraw, ImageFont, __version__

SOURCE_SHA = '0d18b068e177b54f7b8a2b30072e9ae3ebc984fbed9fd6a8706f71d3140a5ffd'
STYLE_SHA = '2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6'
REUSE = {0: (11, 2), 1: (6, 2), 2: (23, 0), 3: (18, 0), 4: (12, 0),
         6: (13, 0), 10: (16, 0), 11: (24, 0), 12: (22, 0)}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def write_json(path, obj):
    with path.open('x') as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def flip(data):
    return b''.join(data[(y * 192 + x) * 4:(y * 192 + x + 1) * 4]
                    for y in range(150) for x in range(191, -1, -1))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('project', 'base', 'batch', 'out', 'review'):
        p.add_argument('--' + key, type=Path, required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and not a.review.exists()
    assert a.out.parent.stat().st_uid == a.review.parent.stat().st_uid == 1000
    native = module(a.project / 'tools/catalog-encounter.py', 'native')
    sampler = module(a.project / 'tools/audit-encounter-gui.py', 'sampler')
    source = (a.project / 'workplace/intake-20261023/sources/game/8sword/ENEMY.AY').read_bytes()
    assert len(source) == 16856 and sha(source) == SOURCE_SHA
    records = [source[i * 1204:(i + 1) * 1204] for i in range(14)]
    variants = [[r, native.mirror(r)] for r in records]
    frequency = Counter(sha(native.prefix(r, h)[:4 + 32 * h])
                        for pair in variants for r in pair for h in range(1, 26, 2))
    base = {f.name: sha(f.read_bytes()) for f in sorted(a.base.iterdir()) if f.is_file()}
    assert len(base) == 344 and all(f.is_file() and not f.is_symlink() for f in a.base.iterdir())
    assert 'map-encounter-10.json' not in base
    a.out.mkdir()
    a.review.mkdir()
    for name in base:
        shutil.copyfile(a.base / name, a.out / name)
    font = ImageFont.truetype(str(a.project / 'workplace/probe-20261023/graphics-first/font-settings-r1/NotoSansCJK-Black.ttc'), 18, index=3)
    sheet = Image.new('RGB', (1104, 1064), '#172b2d')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 12), '地圖遭遇角色：十四筆原版／HD素材對照', font=font, fill='#f1d69b')
    draw.text((16, 40), '原版造型與配色；圖片定位原型，非自然遭遇截圖。', font=font, fill='#ded7bf')
    groups = []
    for i, raw in enumerate(records):
        mirrored_base = i in (7, 13)
        if i in (4, 5, 8, 9):
            stem = f'encounter-{i:02d}-hd-r1'
            receipt = json.loads((a.batch / (stem + '.json')).read_text())
            assert receipt['record'] == i and receipt['source_sha256'] == SOURCE_SHA
            assert receipt['record_sha256'] == sha(raw)
            for key, digest in [('image', 'image_sha256'), ('prompt', 'prompt_sha256')]:
                assert sha((a.batch / receipt[key]).read_bytes()) == receipt[digest]
                shutil.copyfile(a.batch / receipt[key], a.out / receipt[key])
            im = Image.open(a.out / receipt['image']).convert('RGBA')
            b = tuple(receipt['alpha_bbox_gt3'])
            entry = dict(file=receipt['image'], sha256=receipt['image_sha256'], width=im.width, height=im.height,
                         sampling='bitmap', source_rect=[b[0], b[1], b[2] - b[0], b[3] - b[1]])
            prompt = receipt['prompt']
            origin = dict(kind='new-map-pose', receipt_sha256=sha((a.batch / (stem + '.json')).read_bytes()))
        elif mirrored_base:
            old = json.loads((a.base / ('map-encounter-7.json' if i == 7 else 'map-encounter.json')).read_text())
            entry = copy.deepcopy(old['image'])
            b = entry['source_rect']
            entry['source_rect'] = [b[0], b[1], b[2] - b[0], b[3] - b[1]]
            prompt = old['prompt_file']
            origin = dict(kind='preserved-map-art', manifest_sha256=sha((a.base / ('map-encounter-7.json' if i == 7 else 'map-encounter.json')).read_bytes()))
        else:
            number, pose = REUSE[i]
            manifest = 'battle-actors.json' if number == 16 else f'battle-man{number:02d}.json' if number in (6, 11) else f'troop-man{number:02d}.json'
            old = json.loads((a.base / manifest).read_text())
            entry = copy.deepcopy(old['frames'][pose]['image'])
            prompt = 'battle-actors-prompts.txt' if number == 16 else f'battle-man{number:02d}-prompts.txt' if number in (6, 11) else f'troop-man{number:02d}-r1.prompt.txt'
            origin = dict(kind='reused-approved-art', appearance_correspondence='strong inference; no unit or rule identity claim',
                          resource=f'MAN{number:02d}.EGG', record=pose, manifest_sha256=sha((a.base / manifest).read_bytes()))
        entry['source_index'] = 480 + i * 26 - 1
        assert sha((a.out / entry['file']).read_bytes()) == entry['sha256']
        box = native.decode(raw).getbbox()
        target = [box[0] * 3, box[1] * 6, (box[2] - box[0]) * 3, (box[3] - box[1]) * 6]
        if mirrored_base:
            b = old['target_rect']
            target = [b[0], b[1], b[2] - b[0], b[3] - b[1]]
        if i == 10:
            target = [0, 0, 192, 150]
        sampled = sampler.sample(a.out / entry['file'], target[2], target[3], actor=True, rect=entry['source_rect'])
        full = bytearray(192 * 150 * 4)
        for y in range(target[3]):
            at = ((target[1] + y) * 192 + target[0]) * 4
            full[at:at + target[2] * 4] = sampled[y * target[2] * 4:(y + 1) * target[2] * 4]
        normal = flip(full) if mirrored_base else bytes(full)
        caches = [normal, flip(normal)]
        aliases, omitted = [], []
        for di, record in enumerate(variants[i]):
            (a.review / f'encounter-{i:02d}-{di}.rgba').write_bytes(caches[di])
            for height in range(1, 26, 2):
                prefix = native.prefix(record, height)
                key = sha(prefix[:4 + 32 * height])
                if frequency[key] != 1 or mirrored_base and di == 1:
                    omitted.append(dict(direction=di, height=height, reason='preserved-legacy' if mirrored_base and di == 1 else 'ambiguous-prefix'))
                    continue
                aliases.append(dict(direction=di, height=height, native_sha256=key,
                                    record_sha256=sha(prefix), cache_sha256=sha(caches[di][:height * 6 * 192 * 4])))
        manifest = dict(schema=1, source='ENEMY.AY', source_sha256=SOURCE_SHA, pam_sha256='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0',
                        record=i, style='B-bright-painted-r1', style_reference_sha256=STYLE_SHA,
                        geometry='native-alpha-bounds-r1', image=entry, target_rect=target, sampled_mirrored=mirrored_base,
                        prompt_file=prompt, prompt_sha256=sha((a.out / prompt).read_bytes()),
                        cache_sha256=[sha(data) for data in caches], aliases=aliases)
        name = f'encounter-batch-{i:02d}.json'
        write_json(a.out / name, manifest)
        groups.append(dict(record=i, manifest=name, manifest_sha256=sha((a.out / name).read_bytes()),
                           origin=origin, config=manifest, omitted=omitted))
        col, row = i % 3, i // 3
        x, y = col * 368 + 8, row * 196 + 78
        draw.text((x, y), f'ENEMY {i:02d}  原版 / HD', font=font, fill='#f1d69b')
        original = native.decode(raw).resize((154, 120), Image.Resampling.NEAREST)
        painted = Image.frombytes('RGBA', (192, 150), normal).resize((154, 120), Image.Resampling.LANCZOS)
        sheet.paste(original, (x + 2, y + 30), original)
        sheet.paste(painted, (x + 180, y + 30), painted)
    sheet.save(a.review / 'comparison.png')
    report = dict(schema=1, spec='049', status='candidate-registration-review', production=False,
                  source_sha256=SOURCE_SHA, source_records=14, groups=groups, base_files=base,
                  comparison_sha256=sha((a.review / 'comparison.png').read_bytes()),
                  tool_sha256=sha(Path(__file__).read_bytes()), pillow=__version__,
                  sampling='independent premultiplied Python sampler; 192x150 map cache',
                  rights='local-only original-derived; no public distribution grant')
    write_json(a.out / 'encounters-import.json', report)
    write_json(a.review / 'registration.json', report)
    assert len(list(a.out.iterdir())) == 367
    assert all(sha((a.out / n).read_bytes()) == d for n, d in base.items())
    assert all(f.stat().st_uid == 1000 for f in a.out.iterdir())
    print(json.dumps(dict(files=367, preserved=344, groups=14, new_images=4,
                          aliases=sum(len(g['config']['aliases']) for g in groups),
                          registration_sha256=sha((a.review / 'registration.json').read_bytes()))))


if __name__ == '__main__':
    main()
