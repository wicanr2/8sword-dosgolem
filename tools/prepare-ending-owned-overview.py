#!/usr/bin/env python3
"""053：只以已獨立核對的實際研究輸出製作README縮小對照。Docker only。"""
import argparse
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, __version__


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('project', 'audit', 'out'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    audit = json.loads(a.audit.read_text())
    assert audit['status'] == 'research-owned-source-verified' and audit['production'] is False
    assert len(audit['native_frames']) == 41 and len(audit['hd_frames']) == 12
    batch = a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    run = batch/'owned-scene-r3'
    assert sha(run/'owned-result.json') == audit['run_sha256']
    assert sha(a.project/'tools/audit-ending-owned.py') == audit['tool_sha256']
    font_path = a.project/'workplace/probe-20261023/graphics-first/font-settings-r1/NotoSansCJK-Black.ttc'
    assert sha(font_path) == '3cffb10242b4b7e6edd439ebf3bd7e392345525e093ea08149e0a0158a1b5151'
    font = ImageFont.truetype(str(font_path), 25, index=3)
    small = ImageFont.truetype(str(font_path), 21, index=3)
    sheet = Image.new('RGB', (1960, 1520), '#101c25')
    draw = ImageDraw.Draw(sheet)
    draw.text((20, 12), '結局自有來源場景：原版／三種HD字型', font=font, fill='#f6d389')
    draw.text((20, 52), '獨立PAE研究演出；尚未正式接入，人物等其他素材仍保留原圖。', font=small, fill='#e0dccf')
    columns = [('source-native', '原版來源'), ('noto', 'Noto Black 900'), ('lishu', '教育部隸書'), ('caoshu', '草書，缺字回宋體')]
    for col, (_, label) in enumerate(columns):
        draw.text((20+col*485, 92), label, font=font, fill='#f6d389')
    rows = [('END5.AY', '對話與人物特寫'), ('END7.AY', '八劍插畫'), ('END8.AY', '標題'), ('END9.AY', '片尾名單捲動中')]
    entries = []
    for row, (stage, label) in enumerate(rows):
        y = 136+row*340
        native = next(n for n in audit['native_frames'] if n['stage'] == stage and
                      any(h['sample'] == n['sample'] and h['stage'] == stage for h in audit['hd_frames']))
        sample = native['sample']
        snap = json.loads((run/('sample-%03d.json' % sample)).read_text())
        draw.text((20, y), label+'  '+stage, font=small, fill='#e0dccf')
        for col, (profile, _) in enumerate(columns):
            path = run/('sample-%03d-%s.png' % (sample, profile))
            expected = native['image_sha256'] if profile == 'source-native' else next(
                h['image_sha256'] for h in audit['hd_frames'] if h['sample'] == sample and h['font'] == profile)
            assert sha(path) == expected
            im = Image.open(path).convert('RGB')
            assert im.size == (1920, 1200)
            sheet.paste(im.resize((480, 300), Image.Resampling.LANCZOS), (20+col*485, y+32))
            entries.append(dict(stage=stage, sample=sample, step=snap['step'], page=snap['page'],
                                profile=profile, image_sha256=expected))
    a.out.mkdir()
    png = a.out/'ending-owned-scenes-r1.png'
    sheet.save(png)
    result = dict(schema=1, spec='053', status='actual-research-render-comparison', production=False,
                  comparison=png.name, comparison_sha256=sha(png), audit_sha256=sha(a.audit),
                  tool_sha256=sha(Path(__file__)), original_source_sha256='8ae11b4c89f0361ed0a2d5b1859bbb4750047d37f0e26885e6903e4feb721a0c',
                  painter_provenance_sha256=audit['provenance_sha256'], clock='12:00:00.00', command_tail='v a y a n g',
                  build='ending-owned-r3 / Go1.24.13 / Linux Docker', entries=entries,
                  state_relation='same standalone diagnostic state and source commands; deliberate visual modernization',
                  pillow=__version__, rights='compact comparison in existing private repository; full art and originals local only',
                  limits=audit['limits'])
    with (a.out/'ending-owned-scenes-r1.json').open('x') as f:
        f.write(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(comparison=png.name, sha256=sha(png), entries=len(entries))))


if __name__ == '__main__':
    main()
