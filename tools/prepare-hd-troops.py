#!/usr/bin/env python3
"""048：將已完成的四姿勢圖集匯入候選組，保留原版及原始圖集。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil

from PIL import Image, ImageDraw, ImageFont, __version__

CATALOG_SHA = 'c07d1b196eb8e8292d2f3db143775790a802ec91f092da0899eb8763c791d32f'
STYLE_SHA = '2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6'
GROUPS = (2, 3, 4, 5, 7, 8, 9, 10, 12, 13, 14, 15, 17, 18, 19, 20, 22, 23, 24, 25)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def native_image(raw):
    ega = [(0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170),
           (170, 0, 0), (170, 0, 170), (170, 85, 0), (170, 170, 170),
           (85, 85, 85), (85, 85, 255), (85, 255, 85), (85, 255, 255),
           (255, 85, 85), (255, 85, 255), (255, 255, 85), (255, 255, 255)]
    assert len(raw) == 3304 and raw[:4] == bytes((11, 0, 50, 0))
    im = Image.new('RGBA', (88, 50))
    pixels = []
    for y in range(50):
        for x in range(88):
            at, bit = y * 11 + x // 8, 7 - x % 8
            index = sum(((raw[4 + p * 550 + at] >> bit) & 1) << p for p in range(4))
            pixels.append(ega[index] + (255 if raw[2754 + at] >> bit & 1 else 0,))
    im.putdata(pixels)
    return im


def native_target(im):
    pixels = im.load()
    remaining = {(x, y) for y in range(50) for x in range(88) if pixels[x, y][3]}
    kept = []
    while remaining:
        queue = [remaining.pop()]
        component, colored = [], False
        while queue:
            x, y = queue.pop()
            component.append((x, y))
            colored |= pixels[x, y][:3] not in ((0, 0, 0), (85, 85, 85))
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    q = (x + dx, y + dy)
                    if q in remaining:
                        remaining.remove(q)
                        queue.append(q)
        x0, y0 = min(x for x, y in component), min(y for x, y in component)
        x1, y1 = max(x for x, y in component) + 1, max(y for x, y in component) + 1
        if not colored and y0 >= 38 and x1 - x0 >= 3 * (y1 - y0):
            continue
        kept.extend(component)
    assert kept
    x0, y0 = min(x for x, y in kept), min(y for x, y in kept)
    x1, y1 = max(x for x, y in kept) + 1, max(y for x, y in kept) + 1
    return [x0 * 3, y0 * 6, (x1 - x0) * 3, (y1 - y0) * 6]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('project', 'base', 'batch', 'out', 'review'):
        parser.add_argument('--' + name, type=Path, required=True)
    a = parser.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and not a.review.exists()
    assert a.out.parent.stat().st_uid == a.review.parent.stat().st_uid == 1000
    catalog_file = a.project / 'workplace/probe-20261023/graphics-first/all-graphics-catalog-r4/catalog.json'
    assert sha(catalog_file.read_bytes()) == CATALOG_SHA
    catalog = json.loads(catalog_file.read_text())
    original = a.project / 'workplace/intake-20261023/sources/game/8sword'
    art_report = json.loads((a.project / 'docs/images/troops-hd-batch-r1.json').read_text())
    selected = {r['resource']: r for r in art_report['resources'] if r['status'] == 'generated-not-registered'}
    preserved = {f.name: sha(f.read_bytes()) for f in sorted(a.base.iterdir()) if f.is_file()}
    assert len(preserved) == 223 and not (a.base / 'troop-man02.json').exists()
    assert all(f.is_file() and not f.is_symlink() for f in a.base.iterdir())
    a.out.mkdir()
    a.review.mkdir()
    for name in preserved:
        shutil.copyfile(a.base / name, a.out / name)
    font = ImageFont.truetype(str(a.project / 'workplace/probe-20261023/graphics-first/font-settings-r1/NotoSansCJK-Black.ttc'), 22, index=3)
    sheet = Image.new('RGB', (2112, 116 + len(GROUPS) * 340), '#112026')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 12), '批次定位原型：每組四姿勢，原版／HD；非遊玩截圖', font=font, fill='#f2d28b')
    draw.text((16, 50), '原圖與遊戲邏輯保持。鏡射共用快取，灰黑獨立地影省略屬視覺近似。', font=font, fill='#ded7bf')
    spec = importlib.util.spec_from_file_location('sampler', a.project / 'tools/audit-encounter-gui.py')
    sampler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sampler)
    reverse = bytes(int(f'{v:08b}'[::-1], 2) for v in range(256))
    groups = []
    for gi, number in enumerate(GROUPS):
        name, stem = f'MAN{number:02}.EGG', f'troop-man{number:02}'
        expected = selected[name]
        raw = (original / name).read_bytes()
        assert len(raw) == 13216 and sha(raw) == expected['source_sha256']
        receipt_file = a.batch / (Path(expected['image']).stem + '.json')
        receipt = json.loads(receipt_file.read_text())
        assert sha(receipt_file.read_bytes()) == expected['receipt_sha256']
        assert sha((a.batch / expected['image']).read_bytes()) == expected['image_sha256']
        assert sha((a.batch / expected['prompt']).read_bytes()) == expected['prompt_sha256']
        atlas = Image.open(a.batch / expected['image']).convert('RGBA')
        prompt_name = stem + '-r1.prompt.txt'
        shutil.copyfile(a.batch / expected['prompt'], a.out / prompt_name)
        frames = []
        draw.text((12, 116 + gi * 340), name, font=font, fill='#f2d28b')
        for ri, pose in enumerate(receipt['poses']):
            assert pose['record'] == ri
            record = raw[ri * 3304:(ri + 1) * 3304]
            assert sha(record) == expected['records'][ri]['record_sha256']
            im = atlas.crop(pose['quadrant'])
            assert im.getchannel('A').getextrema() == (0, 255)
            image_file = f'{stem}-{ri}-r1.png'
            im.save(a.out / image_file)
            bounds = im.getchannel('A').point(lambda v: 255 if v > 3 else 0).getbbox()
            assert bounds
            src = [bounds[0], bounds[1], bounds[2] - bounds[0], bounds[3] - bounds[1]]
            native = native_image(record)
            target = native_target(native)
            sampled = sampler.sample(a.out / image_file, target[2], target[3], actor=True, rect=src)
            cache = bytearray(264 * 300 * 4)
            for yy in range(target[3]):
                at = ((target[1] + yy) * 264 + target[0]) * 4
                cache[at:at + target[2] * 4] = sampled[yy * target[2] * 4:(yy + 1) * target[2] * 4]
            mirrored = b''.join(cache[(yy * 264 + xx) * 4:(yy * 264 + xx + 1) * 4]
                                for yy in range(300) for xx in range(263, -1, -1))
            flipped = record[:4] + bytes(reverse[v] for at in range(4, 3304, 11) for v in record[at:at + 11][::-1])
            ids = [160 + gi * 16 + ri * 4 + di * 2 for di in range(2)]
            frame = dict(record=ri, image=dict(source_index=ids[0] - 1, file=image_file,
                         sha256=sha((a.out / image_file).read_bytes()), width=im.width, height=im.height,
                         sampling='bitmap', source_rect=src), target_rect=target,
                         native_sha256=[sha(record[:2204]), sha(flipped[:2204])],
                         record_sha256=[sha(record), sha(flipped)], cache_sha256=[sha(cache), sha(mirrored)])
            frames.append(frame)
            for di, data in enumerate((cache, mirrored)):
                (a.review / f'{stem}-{ri}-{di}.rgba').write_bytes(data)
            xx, yy = ri * 528, 150 + gi * 340
            sheet.paste(native.resize((264, 300), Image.Resampling.NEAREST), (xx, yy), native.resize((264, 300), Image.Resampling.NEAREST))
            painted = Image.frombytes('RGBA', (264, 300), bytes(cache))
            sheet.paste(painted, (xx + 264, yy), painted)
        manifest = dict(schema=1, source_file=name, source_sha256=sha(raw), pam_sha256='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0',
                        style='B-bright-painted-r1', style_reference_sha256=STYLE_SHA,
                        geometry='native-mask-components-r1', frames=frames)
        (a.out / (stem + '.json')).write_text(json.dumps(manifest, indent=2) + '\n')
        groups.append(dict(resource=name, source_sha256=sha(raw), manifest=stem + '.json',
                           manifest_sha256=sha((a.out / (stem + '.json')).read_bytes()),
                           atlas=expected['image'], atlas_sha256=expected['image_sha256'],
                           receipt_sha256=expected['receipt_sha256'], prompt_file=prompt_name,
                           prompt_sha256=expected['prompt_sha256'], frames=frames))
    sheet.save(a.review / 'comparison.png')
    report = dict(schema=1, status='candidate-registration-review', spec='048', production=False,
                  groups=groups, base_files=preserved, original_atlases_unchanged=True,
                  catalog_sha256=CATALOG_SHA, tool_sha256=sha(Path(__file__).read_bytes()), pillow=__version__,
                  native_geometry='masked source bounds; isolated lower grayscale shadows omitted; presentation approximation',
                  comparison_sha256=sha((a.review / 'comparison.png').read_bytes()),
                  rights='local-only original-derived assets; no public distribution grant')
    (a.out / 'troops-import.json').write_text(json.dumps(report, indent=2) + '\n')
    (a.review / 'registration.json').write_text(json.dumps(report, indent=2) + '\n')
    assert len(list(a.out.iterdir())) == 344
    assert all(sha((a.out / name).read_bytes()) == digest for name, digest in preserved.items())
    print(json.dumps(dict(files=344, preserved=223, groups=len(groups), poses=80, directions=160, aliases=160,
                          registration_sha256=sha((a.review / 'registration.json').read_bytes()))))


if __name__ == '__main__':
    main()
