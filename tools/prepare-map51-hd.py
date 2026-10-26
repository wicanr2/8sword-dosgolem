#!/usr/bin/env python3
"""045：準備PMAP51紅金格紋參考與提示，只描述原圖，不命名用途。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

from PIL import Image, __version__


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    source = (a.project / 'workplace/intake-20261023/sources/game/8sword/PMAP.AY').read_bytes()
    assert sha(source) == '9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02'
    raw = source[51 * 1004:52 * 1004]
    assert len(raw) == 1004 and raw[:4] == bytes((8, 0, 25, 0))
    spec = importlib.util.spec_from_file_location('planar', a.project / 'tools/catalog-all-graphics.py')
    planar = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(planar)
    im = planar.planar(raw, (0, 8, 25, 5))
    a.out.mkdir()
    (a.out / 'pmap51-native.bin').write_bytes(raw)
    im.resize((768, 600), Image.Resampling.NEAREST).save(a.out / 'pmap51-reference.png')
    prompt = ('Use case: game-art. Asset type: ONE opaque HD pattern tile for the Chinese fantasy DOS game 神州八劍.\n'
              'The input is the ORIGINAL tile and is the exact layout and palette reference. Repaint this flat abstract RED and GOLD rectangular grid pattern in a crisp hand-painted 2D game style. Preserve the visible arrangement, spacing, alternating red blocks, narrow golden grid lines and GREY horizontal bands of the source. Replace low-resolution color dithering with smooth painted surfaces and subtle brush texture, keeping the major color areas and all pattern elements in the same places.\n'
              'Composition: flat front-facing pattern only, filling the entire canvas, 1.28:1 landscape aspect matching the reference. All pixels opaque; no margins or borders.\n'
              'Do not interpret this as a named object or terrain. No scenery, perspective, buildings, bricks with deep mortar, grass, icons, characters, words, labels, comparison panels or watermark. Keep the original design; only improve rendering detail.\n')
    (a.out / 'map-landmark-51-r1.prompt.txt').write_text(prompt)
    report = dict(schema=1, spec='045', status='prepared-not-generated', source_file='PMAP.AY',
                  source_sha256=sha(source), source_index=51, record_sha256=sha(raw), native_sha256=sha(raw[:804]),
                  reference='pmap51-reference.png', reference_sha256=sha((a.out / 'pmap51-reference.png').read_bytes()),
                  prompt='map-landmark-51-r1.prompt.txt', prompt_sha256=sha(prompt.encode()),
                  tool_sha256=sha(Path(__file__).read_bytes()), pillow=__version__,
                  evidence='decoded source pixels and geometry proven; gameplay use unknown',
                  rights='local-only original-derived; no public distribution grant')
    (a.out / 'request.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
