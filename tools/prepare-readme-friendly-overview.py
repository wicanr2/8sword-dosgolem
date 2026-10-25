#!/usr/bin/env python3
"""042：由四個已驗實際Draw製作原版／HD姿勢總覽。Docker only。"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('gui', 'audit', 'font', 'out'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    assert not args.out.exists()
    audit = json.loads(args.audit.read_text())
    assert audit['status'] == 'PASS-scoped-four-friendly-MAN21-runtime' and audit['gui_path']
    assert len(audit['gui_draws']) == 4
    out = Image.new('RGB', (1056, 664), (12, 33, 24))
    draw = ImageDraw.Draw(out)
    font = ImageFont.truetype(str(args.font), 20, index=3)
    records = []
    for i, row in enumerate(audit['gui_draws']):
        stem = args.gui / 'save/research-friendly-draws' / f'record-{i}-first-frame'
        path = lambda suffix: Path(str(stem) + suffix)
        meta = json.loads(path('.json').read_text())
        assert row['record'] == i and meta['actual_draw'] == row['actual_draw'] > 0
        assert sha(path('-before.state')) == sha(path('-after.state'))
        hd = Image.open(path('.png')).convert('RGBA')
        assert hashlib.sha256(hd.tobytes()).hexdigest() == row['rgba_sha256']
        owners = list(struct.iter_unpack('<HI', path('-actors.bin').read_bytes()))
        assert sum(ident == 152+i for ident, local in owners) == 4400
        first = next(n for n, cell in enumerate(owners) if cell == (152+i, 0))
        x, y = first % 640, first // 640
        native = path('-native.idx').read_bytes()
        original = Image.new('RGB', (640, 200))
        original.putdata([tuple(meta['display']['Palette'][c]) for c in native])
        original = original.crop((x, y, x+88, y+50)).resize((264, 300), Image.Resampling.NEAREST)
        out.paste(original, (i*264, 32))
        out.paste(hd.crop((x*3, y*6, (x+88)*3, (y+50)*6)).convert('RGB'), (i*264, 364))
        for top, label in ((0, '原版'), (332, 'HD')):
            draw.text((i*264+10, top+4), f'{label}：姿勢 {i}', font=font, fill=(247, 228, 166))
        records.append(dict(record=i, actual_draw=meta['actual_draw'], runtime_step=meta['step'], native_rect=[x,y,88,50], native_sha256=sha(path('-native.idx')), actual_png_sha256=sha(path('.png')), state_sha256=sha(path('-before.state'))))
    args.out.mkdir()
    image = args.out / 'friendly-man21-poses-original-hd-r1.png'
    out.save(image)
    record = dict(schema=1, clock='ordinary GUI clock and RNG uncontrolled; 3000 cycles/ms', scenario='normal Continue from genuine MAP2 43,54 save, then castle battle', initial_save_sha256=json.loads((args.gui / 'genuine-input.json').read_text())['gamedata.ay'], scope='four paired same-state original/HD actual Draw crops; each column has its own guest state', image_sha256=sha(image), records=records, font_sha256=sha(args.font), audit_sha256=sha(args.audit), source='workplace/player/gui/' + args.gui.name + '/save/research-friendly-draws', rights='user-requested comparison only in existing private repository; full artwork and original data remain local')
    image.with_suffix('.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print(image)


if __name__ == '__main__':
    main()
