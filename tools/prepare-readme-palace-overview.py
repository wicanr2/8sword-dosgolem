#!/usr/bin/env python3
"""046：由已驗實際 Draw 製作原版／HD 攻城比較圖。Docker only。"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('gui', 'audit', 'font', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    assert not args.out.exists()
    audit = json.loads(args.audit.read_text())
    assert audit['status'] == 'PASS-scoped-palace-background-runtime' and audit['gui_path']
    stem = args.gui / 'save/research-palace-draws/font-noto-first-draw'
    path = lambda suffix: Path(str(stem) + suffix)
    meta = json.loads(path('.json').read_text())
    assert sha(path('-before.state')) == sha(path('-after.state'))
    actual = next(row for row in audit['gui_draws'] if row['font_id'] == 'noto')
    hd = Image.open(path('.png')).convert('RGBA')
    assert hd.size == (1920, 1200) and hashlib.sha256(hd.tobytes()).hexdigest() == actual['rgba_sha256']
    native = path('-native.idx').read_bytes()
    assert len(native) == 128000 and max(native) < 16
    original = Image.new('RGB', (640, 200))
    original.putdata([tuple(meta['display']['Palette'][c]) for c in native])
    original = original.resize((1920, 1200), Image.Resampling.NEAREST)
    out = Image.new('RGB', (1920, 640), (12, 33, 24))
    draw = ImageDraw.Draw(out)
    font = ImageFont.truetype(str(args.font), 24, index=3)
    for i, image in enumerate((original, hd)):
        out.paste(image.convert('RGB').resize((960, 600), Image.Resampling.LANCZOS), (i * 960, 40))
        draw.text((i * 960 + 12, 6), '原版：dosgolem 原生畫面' if i == 0 else 'HD：相同狀態的實際視窗畫面', font=font, fill=(247, 228, 166))
    args.out.mkdir()
    image = args.out / 'battle-palace-original-hd-r1.png'
    out.save(image)
    record = dict(schema=1, scope='046 GRO01 background; same-state native VGA and verified actual central Draw; remaining native units are visible', image_sha256=sha(image), actual_draw=meta['actual_draw'], runtime_step=meta['step'], native_index_sha256=sha(path('-native.idx')), actual_png_sha256=sha(path('.png')), state_sha256=sha(path('-before.state')), audit_sha256=sha(args.audit), audit_source=str(args.audit), font_sha256=sha(args.font), clock='ordinary GUI runtime; 3000 cycles/ms; original clock and RNG uncontrolled', source='workplace/player/gui/palace-save-r3/save/research-palace-draws/font-noto-first-draw', rights='user-requested comparison only in existing private repository; full artwork and original game remain local')
    image.with_suffix('.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print(image)


if __name__ == '__main__':
    main()
