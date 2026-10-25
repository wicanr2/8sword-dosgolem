#!/usr/bin/env python3
"""050：核對三份GRO來源並準備原版參考與完整圖片生成提示。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

from PIL import Image, __version__


def sha(data):
    return hashlib.sha256(data).hexdigest()


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    catalog_path = a.project / 'docs/images/graphics-inventory-r1.json'
    catalog = json.loads(catalog_path.read_text())
    files = {f['file']: f for f in catalog['files']}
    records = {r['source_file']: r for r in catalog['records'] if r['source_file'] in ('GRO03.EG', 'GRO04.EG', 'GRO05.EG')}
    original = a.project / 'workplace/intake-20261023/sources/game/8sword'
    decoder = module(a.project / 'tools/prepare-hd-intro.py', 'decoder')
    planar = module(a.project / 'tools/catalog-all-graphics.py', 'planar')
    style = a.project / 'workplace/player/assets-painted-r50/battle-background-r1.png'
    assert sha(style.read_bytes()) == '4ec05b750acd05b1d86af6706fa9cec8f60ddf9123c30f6cd4b5a2c5dd3c59f2'
    a.out.mkdir()
    subjects = {
        3: 'A rugged RED-ORANGE rocky mountain rises on the left in the upper third, with smaller jagged red ridges receding to the right. Bright CYAN and pale blue sky with long soft white clouds. Thin vivid green shrubs trace the mountain foot. The lower two thirds is an open warm orange and ochre sandy plain, with only sparse small grass patches at the far edges. Preserve the original peak on the left, low ridge on the right, horizon height and very open foreground. No palace, no forest, no lava or fire.',
        4: 'A forest clearing framed by dense deep GREEN trees across the upper third, rising at both left and right edges and dipping at the distant center. A small GOLD-YELLOW opening in the sky at the top center. The lower two thirds is a broad empty warm ORANGE and ochre earth clearing, with a few green grass patches near the far tree line and edges. Preserve the original low tree-line silhouette and the wide clear battle area. No mountain, palace, road, river, autumn red trees or objects.',
        5: 'An open BLUE sea extends across the lower two thirds of the view, with layered cobalt and azure waves and small pale foam accents. A low distant dark-blue wave line at the horizon. The upper third is the original luminous sunset palette: CYAN at the very top, GOLD-YELLOW cloud bands, PEACH and PINK/MAGENTA light toward the horizon. Keep the spacious original horizon, broad open water and vivid blue foreground. No land, islands, mountains, shore, ships, architecture or people.',
    }
    jobs = []
    for i in (3, 4, 5):
        source = f'GRO{i:02d}.EG'
        packed = (original / source).read_bytes()
        assert sha(packed) == files[source]['sha256']
        raw = decoder.decode(packed)
        assert len(raw) == 64004 and sha(raw) == records[source]['record_sha256']
        assert raw[:4] == bytes((80, 0, 200, 0))
        im = planar.planar(raw, (0, 80, 200, 4))
        assert sha(im.tobytes()) == records[source]['decoded_rgba_sha256']
        native = f'gro{i:02d}-native.bin'
        reference = f'gro{i:02d}-reference.png'
        (a.out / native).write_bytes(raw)
        im.resize((640, 400), Image.Resampling.NEAREST).save(a.out / reference)
        prompt = ('Use case: game-art. Asset type: one full-frame opaque HD battle background for the Chinese fantasy DOS game 神州八劍.\n'
                  'Input 1 is the ORIGINAL scene, the PRIMARY composition, terrain, horizon and palette reference. Input 2 is an approved HD background and is ONLY the secondary hand-painted rendering-style reference. Do not copy its scene or sunset colors.\n'
                  + subjects[i] + '\n'
                  'Style: vivid detailed hand-painted 2D Chinese fantasy game scenery, painterly rock/foliage/water textures, clear atmospheric depth, natural smooth shading instead of pixel dithering. Match the approved game art polish.\n'
                  'Composition: landscape 16:10 complete edge-to-edge background. Preserve the original terrain and horizon placement; the lower two thirds must remain spacious for separately drawn tactical sprites. All pixels opaque.\n'
                  'Constraints: environment only, no characters, monsters, troops, weapons, interface, symbols, title, text, labels, watermark, borders, black bars or comparison panels. No dramatic new focal objects or redesigned color scheme.\n')
        prompt_name = f'gro{i:02d}-hd-r1.prompt.txt'
        (a.out / prompt_name).write_text(prompt)
        jobs.append(dict(number=i, source=source, source_sha256=sha(packed), native=native, native_sha256=sha(raw),
                         reference=reference, reference_sha256=sha((a.out / reference).read_bytes()), prompt=prompt_name,
                         prompt_sha256=sha((a.out / prompt_name).read_bytes()), output=f'gro{i:02d}-hd-r1.png'))
    report = dict(schema=1, spec='050', status='prepared-not-generated', jobs=jobs,
                  style_reference=str(style.relative_to(a.project)), style_sha256=sha(style.read_bytes()),
                  catalog_sha256=sha(catalog_path.read_bytes()), tool_sha256=sha(Path(__file__).read_bytes()),
                  decoder_sha256=sha((a.project / 'tools/prepare-hd-intro.py').read_bytes()), pillow=__version__,
                  rights='local-only original-derived; no public distribution grant')
    (a.out / 'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(sources=3, references=3, output=str(a.out))))


if __name__ == '__main__':
    main()
