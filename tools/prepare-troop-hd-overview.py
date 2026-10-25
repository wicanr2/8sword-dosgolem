#!/usr/bin/env python3
"""048：核對批次素材，整理完整部隊對照與四姿勢圖集。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy

from PIL import Image, ImageDraw, ImageFont, __version__


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def fit(sheet, image, box, native=False):
    if native:
        image = image.resize((image.width, image.height * 2), Image.Resampling.NEAREST)
    image = image.copy()
    image.thumbnail((box[2] - box[0], box[3] - box[1]),
                    Image.Resampling.NEAREST if native else Image.Resampling.LANCZOS)
    # Native sources are small, so permit enlargement while preserving their pixels.
    scale = min((box[2] - box[0]) / image.width, (box[3] - box[1]) / image.height)
    if scale > 1:
        image = image.resize((round(image.width * scale), round(image.height * scale)),
                             Image.Resampling.NEAREST if native else Image.Resampling.LANCZOS)
    sheet.paste(image, (box[0] + (box[2] - box[0] - image.width) // 2,
                        box[1] + (box[3] - box[1] - image.height) // 2), image)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--batch', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    p, batch, out = args.project, args.batch, args.out
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not out.exists() and out.parent.stat().st_uid == 1000
    catalog_path = p / 'workplace/probe-20261023/graphics-first/all-graphics-catalog-r4/catalog.json'
    catalog = json.loads(catalog_path.read_text())
    plan = json.loads((batch / 'manifest.json').read_text())
    original = p / 'workplace/intake-20261023/sources/game/8sword'
    assets = p / 'workplace/player/assets-painted-r48'
    registered = {(r['source_file'], r['record']): r for r in catalog['hd_registrations']}
    assert len(registered) == 20 and len(plan['jobs']) == 20
    decode = runpy.run_path(str(p / 'tools/prepare-hd-intro.py'))['decode']
    planar = runpy.run_path(str(p / 'tools/catalog-all-graphics.py'))['planar']
    font_path = p / 'workplace/probe-20261023/graphics-first/font-settings-r1/NotoSansCJK-Black.ttc'
    fonts = {size: ImageFont.truetype(str(font_path), size, index=3) for size in (17, 20, 24, 36)}
    background, gold, text_color = '#112026', '#f2d28b', '#ded7bf'
    sheet = Image.new('RGB', (2000, 1540), background)
    poses = Image.new('RGB', (2000, 1900), background)
    draw, pd = ImageDraw.Draw(sheet), ImageDraw.Draw(poses)
    draw.text((24, 14), '神州八劍：25 組原版／HD 部隊與怪物', font=fonts[36], fill=gold)
    draw.text((24, 66), '每組第 0 筆。5 組已接入，20 組新圖待匯入；素材對照，非同狀態戰場截圖。', font=fonts[24], fill=text_color)
    pd.text((24, 14), '新增 20 組 HD 圖集：共 80 個姿勢', font=fonts[36], fill=gold)
    pd.text((24, 66), '每格依左上、右上、左下、右下對應原版 0／1／2／3。已繪製，尚未正式匯入。', font=fonts[24], fill=text_color)
    report_rows, generated, drawn_poses = [], [], 0
    for number in range(1, 26):
        name = f'MAN{number:02}.EGG'
        source = next(f for f in catalog['files'] if f['file'] == name)
        raw = (original / name).read_bytes()
        assert sha(raw) == source['sha256']
        data = decode(raw) if source['packed'] else raw
        records = [r for r in catalog['records'] if r['source_file'] == name]
        assert [r['record'] for r in records] == [0, 1, 2, 3]
        native = None
        for r in records:
            at = r['decoded_offset']
            assert sha(data[at:at + r['bytes']]) == r['record_sha256']
            im = planar(data, (at, r['width'] // 8, r['height'], r['planes']))
            assert sha(im.tobytes()) == r['decoded_rgba_sha256']
            if r['record'] == 0:
                native = im
        x, y = ((number - 1) % 5) * 400, 110 + ((number - 1) // 5) * 286
        draw.text((x + 14, y), name, font=fonts[24], fill=gold)
        draw.text((x + 54, y + 34), '原版', font=fonts[20], fill=text_color)
        draw.text((x + 246, y + 34), 'HD', font=fonts[20], fill=text_color)
        row = dict(resource=name, source_sha256=source['sha256'],
                   records=[dict(record=r['record'], record_sha256=r['record_sha256'],
                                 decoded_rgba_sha256=r['decoded_rgba_sha256']) for r in records])
        if (name, 0) in registered:
            entries = [registered[(name, i)] for i in range(4)]
            for entry in entries:
                assert sha((assets / entry['image']).read_bytes()) == entry['image_sha256']
            entry = entries[0]
            hd = Image.open(assets / entry['image']).convert('RGBA')
            if entry['transform'] == 'mirror-six-planes':
                native = native.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            row.update(status='registered', hd_records=entries)
            status, color = '已接入', '#a8d5b1'
        else:
            job = next(j for j in plan['jobs'] if j['source_file'] == name)
            receipt_path = batch / (Path(job['output']).stem + '.json')
            receipt = json.loads(receipt_path.read_text())
            assert receipt['resource'] == name and receipt['source_sha256'] == source['sha256']
            assert receipt['status'] == 'generated-not-registered'
            for field, hash_field in [('image', 'image_sha256'), ('prompt', 'prompt_sha256'),
                                     ('native_reference', 'native_reference_sha256'),
                                     ('style_reference', 'style_sha256')]:
                assert sha((batch / receipt[field]).read_bytes()) == receipt[hash_field]
            assert receipt['original_records'] == job['records']
            atlas = Image.open(batch / receipt['image']).convert('RGBA')
            assert atlas.size == (receipt['width'], receipt['height'])
            assert atlas.getchannel('A').getextrema() == (0, 255)
            assert len(receipt['poses']) == 4
            for pose in receipt['poses']:
                assert atlas.crop(pose['quadrant']).getchannel('A').getbbox()
            hd = atlas.crop(receipt['poses'][0]['quadrant'])
            row.update(status=receipt['status'], image=receipt['image'],
                       image_sha256=receipt['image_sha256'], prompt=receipt['prompt'],
                       prompt_sha256=receipt['prompt_sha256'], receipt_sha256=sha(receipt_path.read_bytes()),
                       width=atlas.width, height=atlas.height, poses=receipt['poses'])
            index = len(generated)
            xx, yy = (index % 5) * 400, 110 + (index // 5) * 446
            pd.text((xx + 14, yy), name + '  0 / 1 / 2 / 3', font=fonts[20], fill=gold)
            fit(poses, atlas, (xx + 8, yy + 34, xx + 392, yy + 430))
            generated.append(row)
            drawn_poses += 4
            status, color = '已繪製，待匯入', '#d9b789'
        fit(sheet, native, (x + 12, y + 66, x + 182, y + 248), native=True)
        fit(sheet, hd, (x + 204, y + 66, x + 388, y + 248))
        draw.text((x + 170, y + 254), status, font=fonts[17], fill=color)
        report_rows.append(row)
    assert len(generated) == 20 and drawn_poses == 80
    out.mkdir()
    sheet.save(out / 'troops-all-original-hd-r2.png')
    poses.save(out / 'troops-new-hd-all-poses-r1.png')
    report = dict(schema=1, status='generated-art-inventory-not-gameplay-validation',
                  source_groups=25, source_records=100, registered_groups=5, registered_records=20,
                  newly_generated_groups=20, newly_generated_records=80, production_changed=False,
                  excluded='MAN27 contains four Taiji records; original usage remains unknown',
                  batch_path=str(batch.relative_to(p)), catalog_sha256=sha(catalog_path.read_bytes()),
                  plan_sha256=sha((batch / 'manifest.json').read_bytes()),
                  tool_sha256=sha(Path(__file__).read_bytes()), pillow=__version__,
                  font_sha256=sha(font_path.read_bytes()), resources=report_rows,
                  outputs={f.name: sha(f.read_bytes()) for f in out.glob('*.png')},
                  rights='User-requested comparison documentation in existing private repository; full assets remain local.',
                  limits=['Static art sheets, not same-state battle screenshots.',
                          'Generated art is not yet registered in the formal runtime.',
                          'Shared rendering uses representative sampling; per-creature gameplay checks waived by user.',
                          'Controlled memory states are authorized for presentation checks only.'])
    (out / 'troops-hd-batch-r1.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ['status', 'source_groups', 'source_records',
                                          'newly_generated_groups', 'newly_generated_records', 'outputs']}))


if __name__ == '__main__':
    main()
