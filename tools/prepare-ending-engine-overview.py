#!/usr/bin/env python3
"""053：整理已獨立核對的Engine結局候選Frame，完整原圖留本機。"""
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
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--audit', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    report = json.loads(a.audit.read_text())
    assert report['status'] == 'verified-Engine-ending-candidate' and report['production'] is False
    b = a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    run = b/report.get('runtime_directory', 'runtime-r2')/'hd'
    font_path = a.project/'workplace/probe-20261023/graphics-first/font-settings-r1/NotoSansCJK-Black.ttc'
    assert sha(font_path) == '3cffb10242b4b7e6edd439ebf3bd7e392345525e093ea08149e0a0158a1b5151'
    font = ImageFont.truetype(str(font_path), 21, index=3)
    canvas = Image.new('RGB', (1792, 1312), '#10131d')
    draw = ImageDraw.Draw(canvas)
    for i, label in enumerate(['原版來源重建', 'Noto Black 900', '教育部隸書', '草書']):
        draw.text((i*448+12, 12), label, font=font, fill='#e8d4a2')
    entries = []
    stages = ['END5.AY', 'END7.AY', 'END8.AY', 'END9.AY']
    labels = ['對話，人物圖仍用原版來源', '人物構圖修正 r2', '標題', '製作名單，捲動中畫格']
    for row, stage in enumerate(stages):
        sample = next(x['sample'] for x in report['frames'] if x['stage'] == stage)
        top = 48+row*316
        draw.text((12, top), labels[row], font=font, fill='#d7dce8')
        for col, profile in enumerate(['native', 'noto', 'lishu', 'caoshu']):
            path = run/f'sample-{sample:02d}-{profile}.png'
            if profile != 'native':
                expected = next(x['image_sha256'] for x in report['frames'] if x['sample'] == sample and x['font'] == profile)
                assert sha(path) == expected
            im = Image.open(path).convert('RGB')
            assert im.size == (1920, 1200)
            canvas.paste(im.resize((448, 280), Image.Resampling.LANCZOS), (col*448, top+30))
            entries.append(dict(stage=stage, profile=profile, source=str(path.relative_to(a.project)), sha256=sha(path)))
    canvas.save(a.out)
    with a.out.with_suffix('.json').open('x') as f:
        f.write(json.dumps(dict(schema=1, spec='053', production=False,
            tool_sha256=sha(Path(__file__)), audit_sha256=sha(a.audit), comparison_sha256=sha(a.out),
            entries=entries, scope='Engine candidate Frames. Native column is independently reconstructed source checked against original RGB; other columns are actual candidate Frames. No GUI Draw or release claim.'), ensure_ascii=False, indent=2)+'\n')
    print(sha(a.out))


if __name__ == '__main__':
    main()
