#!/usr/bin/env python3
"""051：核對LIVE來源並準備四幅原版參考；碑文另行核對，不由生成模型猜寫。"""
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
    records = {r['source_file']: r for r in catalog['records'] if r['source_file'] in ['LIVE1.AY', 'LIVE3.AY', 'LIVE4.AY', 'LIVE5.AY']}
    original = a.project / 'workplace/intake-20261023/sources/game/8sword'
    decoder = module(a.project / 'tools/prepare-hd-intro.py', 'decoder')
    planar = module(a.project / 'tools/catalog-all-graphics.py', 'planar')
    style = a.project / 'docs/images/recruitment-gate-approved-r1.png'
    assert sha(style.read_bytes()) == '7aa67f8975843e91e0a393863ba08bb77582fd4ab62ee10fad059bebcd5b61ab'
    a.out.mkdir()
    subjects = {
        1: 'A small Chinese rural village half hidden among lush bright green trees and shrubs. A line of modest warm orange and ochre tiled roofs across the middle, a larger gabled house cropped at the right edge. Cyan-blue sky with pale white clouds along the upper quarter, deep green distant trees. Preserve the original low roofline, overlapping village buildings and foreground vegetation. No pagoda, palace, gate, city wall or new focal structure.',
        3: 'One small weathered wooden hut on the left, under a warm orange and golden pitched roof, its doorway a dark rectangle. Dense bright green bamboo and forest fill the background under a narrow deep blue-violet sky band. Open orange earth and scattered green grass fill the right side and foreground. Preserve the original small low hut, single doorway and left-weighted composition. No new courtyard, tower, bridge, stone gate or decorative objects.',
        4: 'A quiet ancient Chinese burial ground following the original slanted view: a large simple grey standing stone on the left above a low rectangular grave platform, another smaller upright stone near the middle right, vivid green grass and vegetation around the stonework. Grey-blue sky and the original curved dark-blue distant background. Keep stone faces BLANK for later verified inscription rendering. No invented characters, tomb names, religious symbols, new statues, people or weapons.',
        5: 'A huge black cave opening in the steep jagged orange-ochre rocky hill on the right half. Layered red and golden rocky hills recede to the left. Vivid green shrubs and a narrow wooden fence or railing trace the foothills. Orange earth in the lower foreground, rich blue sky with pale white clouds above the distant left ridges. Preserve the original dark cave shape, right-weighted rocky mass, small wooden railing and left distant mountains. No buildings, temple doorway, treasure, flames or figures.',
    }
    jobs = []
    for i in (1, 3, 4, 5):
        source = f'LIVE{i}.AY'
        packed = (original / source).read_bytes()
        assert sha(packed) == files[source]['sha256']
        raw = decoder.decode(packed)
        assert len(raw) == 22404 and sha(raw) == records[source]['record_sha256']
        assert raw[:4] == bytes((56, 0, 100, 0))
        im = planar.planar(raw, (0, 56, 100, 4))
        assert sha(im.tobytes()) == records[source]['decoded_rgba_sha256']
        native, reference = f'live{i}-native.bin', f'live{i}-reference.png'
        (a.out / native).write_bytes(raw)
        im.resize((896, 400), Image.Resampling.NEAREST).save(a.out / reference)
        if i == 4:
            im.resize((1792, 800), Image.Resampling.NEAREST).save(a.out / 'live4-inscription-reference.png')
        prompt = ('Use case: game-art. Asset type: one full-frame opaque HD building/environment illustration for the Chinese fantasy DOS game 神州八劍.\n'
                  'Input 1 is the ORIGINAL scene, the PRIMARY composition, objects, architecture and palette reference. Input 2 is the approved LIVE2 HD gate and is ONLY the secondary hand-painted rendering-style reference. Do not copy its gate or buildings.\n'
                  + subjects[i] + '\n'
                  'Style: crisp vivid hand-painted 2D Chinese fantasy game background, fine painted wood/stone/foliage detail and natural shading, no pixel dithering. Preserve the original scene identity and principal colors.\n'
                  'Composition: very wide landscape approximately 2.24:1, edge to edge, matching the reference framing. Entire image opaque; no padding, borders or comparison panels.\n'
                  'Constraints: environment only. No people, troops, monsters, interface, title, labels, text, invented glyphs, watermark or religious symbols. Keep the original number and placement of architectural elements.\n')
        prompt_name = f'live{i}-hd-r1.prompt.txt'
        (a.out / prompt_name).write_text(prompt)
        jobs.append(dict(number=i, source=source, source_sha256=sha(packed), native=native, native_sha256=sha(raw),
                         reference=reference, reference_sha256=sha((a.out / reference).read_bytes()), prompt=prompt_name,
                         prompt_sha256=sha((a.out / prompt_name).read_bytes()), output=f'live{i}-hd-r1.png',
                         inscription_review_required=i == 4))
    report = dict(schema=1, spec='051', status='prepared-not-generated', jobs=jobs,
                  style_reference=str(style.relative_to(a.project)), style_sha256=sha(style.read_bytes()),
                  catalog_sha256=sha(catalog_path.read_bytes()), tool_sha256=sha(Path(__file__).read_bytes()),
                  decoder_sha256=sha((a.project / 'tools/prepare-hd-intro.py').read_bytes()), pillow=__version__,
                  excluded='LIVE2 already registered; LIVE6 awaits existing user art decision under035',
                  rights='local-only original-derived; no public distribution grant')
    (a.out / 'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(sources=4, references=4, inscription_pending='LIVE4', output=str(a.out))))


if __name__ == '__main__':
    main()
