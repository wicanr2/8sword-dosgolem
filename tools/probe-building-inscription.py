#!/usr/bin/env python3
"""051研究：以固定PAM字模比對LIVE4刻痕，僅輸出候選，不授權改碑文。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, __version__


def sha(data):
    return hashlib.sha256(data).hexdigest()


def packed_bits(im):
    return sum((1 << i) for i, v in enumerate(im.getdata()) if v)


def normalized(im, size, recipe):
    if recipe == 'nearest':
        return im.resize(size, Image.Resampling.NEAREST).point(lambda v: 255 if v >= 128 else 0)
    threshold = int(recipe.split('-')[1])
    return im.resize(size, Image.Resampling.BOX).point(lambda v: 255 if v >= threshold else 0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    a = parser.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    p = a.project
    catalog_file = p / 'workplace/probe-20261023/text-first/glyph-catalog.json'
    catalog = json.loads(catalog_file.read_text())
    assert catalog['count'] == 636 and sha(catalog_file.read_bytes()) == 'ac7363125cff4b2bb57ca73177a6aaeef3b18bdf00b220b98cf9da7b50190e15'
    pam = (p / 'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes()
    assert sha(pam) == catalog['input_sha256']
    spec = importlib.util.spec_from_file_location('planar', p / 'tools/catalog-all-graphics.py')
    planar = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(planar)
    native_file = p / 'workplace/probe-20261023/graphics-first/map-interaction-r1/buildings-hd-batch-r1/live4-native.bin'
    raw = native_file.read_bytes()
    assert sha(raw) == 'c249b6f8707a004789b20b8fac594a0cceaaad2ab601e0ba8aa9440d5b384590'
    source = planar.planar(raw, (0, 56, 100, 4))
    glyphs = []
    for g in catalog['glyphs']:
        data = pam[g['file_offset']:g['file_offset'] + 30]
        assert sha(data) == g['bitmap_sha256']
        im = Image.new('L', (16, 15))
        im.putdata([255 * ((data[y * 2 + x // 8] >> (7 - x % 8)) & 1) for y in range(15) for x in range(16)])
        glyphs.append((g, im))
    a.out.mkdir()
    recipes = ('nearest', 'box-96', 'box-128', 'box-160')
    boxes = [(116, 22, 140, 28), (116, 28, 140, 36), (116, 36, 140, 44),
             (116, 44, 140, 53), (116, 53, 140, 60), (120, 59, 141, 68)]
    font = ImageFont.truetype(str(p / 'workplace/probe-20261023/graphics-first/font-settings-r1/NotoSansCJK-Black.ttc'), 18, index=3)
    sheet = Image.new('RGB', (1320, 900), '#172b2d')
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 8), 'LIVE4刻痕／PAM字模候選：幾何相似度，未核定碑文', font=font, fill='#f1d69b')
    rows = []
    for i, box in enumerate(boxes):
        crop = source.crop(box)
        crop.resize((crop.width * 12, crop.height * 12), Image.Resampling.NEAREST).save(a.out / f'original-{i}.png')
        for mode in ('dark', 'dark-and-highlight'):
            mask = Image.new('L', crop.size)
            mask.putdata([255 if rgb[:3] == (85, 85, 85) or mode == 'dark-and-highlight' and rgb[:3] == (255, 255, 255) else 0 for rgb in crop.getdata()])
            bounds = mask.getbbox()
            assert bounds
            target = mask.crop(bounds)
            target_bits = packed_bits(target)
            by_character = {}
            for glyph, original in glyphs:
                for trim in (False, True):
                    img = original.crop(original.getbbox()) if trim and original.getbbox() else original
                    for recipe in recipes:
                        candidate = normalized(img, target.size, recipe)
                        value = packed_bits(candidate)
                        intersection = (value & target_bits).bit_count()
                        score = 2 * intersection / max(1, value.bit_count() + target_bits.bit_count())
                        item = dict(character=glyph['character'], index=glyph['index'], score=score,
                                    differing_pixels=(value ^ target_bits).bit_count(), exact=value == target_bits,
                                    recipe=recipe, trim=trim, source_offset=glyph['file_offset'], bitmap_sha256=glyph['bitmap_sha256'])
                        old = by_character.get(glyph['character'])
                        if old is None or score > old['score']:
                            by_character[glyph['character']] = item
            ranked = sorted(by_character.values(), key=lambda item: (-item['score'], item['index']))
            rows.append(dict(region=i, source_rect=box, mask=mode, mask_bbox=bounds,
                             exact_characters=[item['character'] for item in ranked if item['exact']], top10=ranked[:10]))
            if mode == 'dark':
                y = 48 + i * 140
                draw.text((12, y), f'刻痕 {i + 1}', font=font, fill='#f1d69b')
                sheet.paste(crop.convert('RGB').resize((240, 90), Image.Resampling.NEAREST), (12, y + 28))
                for j, item in enumerate(ranked[:8]):
                    x = 280 + j * 128
                    glyph, original = glyphs[item['index']]
                    assert glyph['character'] == item['character']
                    draw.text((x, y), f"{item['character']} {item['score']:.2f}", font=font, fill='#ded7bf')
                    img = original.crop(original.getbbox()) if item['trim'] and original.getbbox() else original
                    visual = normalized(img, target.size, item['recipe']).resize((100, 90), Image.Resampling.NEAREST)
                    sheet.paste(visual.convert('RGB'), (x, y + 28))
    sheet.save(a.out / 'candidate-comparison.png')
    report = dict(schema=1, spec='051', status='research-candidates-not-inscription-approval', production=False,
                  evidence_level='pixel candidates only; no textual meaning inferred from ranking',
                  source='LIVE4.AY', decoded_sha256=sha(raw), pam_sha256=sha(pam), glyphs=636,
                  catalog_sha256=sha(catalog_file.read_bytes()), recipes=recipes, rows=rows,
                  address_space='decoded LIVE4 bitmap coordinates; PAM original file offsets for glyphs',
                  tool_sha256=sha(Path(__file__).read_bytes()), pillow=__version__,
                  limits=['Only four fixed resampling recipes against PAM font; not a universal OCR or full font exclusion.',
                          'Manual geometric regions may contain carving and surface marks.',
                          'No production text changes; unique full round-trip or independent evidence required.'])
    (a.out / 'candidates.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(regions=6, modes=2, exact=[r['exact_characters'] for r in rows],
                          top_dark=[r['top10'][0] for r in rows if r['mask'] == 'dark']), ensure_ascii=False))


if __name__ == '__main__':
    main()
