#!/usr/bin/env python3
"""048：沿完整原版盤點建立缺圖清單與四姿勢生成參考，不改正式素材。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import runpy

from PIL import Image


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    p, out = args.project, args.out
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000
    assert not out.exists() and out.parent.stat().st_uid == 1000
    catalog = json.loads((p/'workplace/probe-20261023/graphics-first/all-graphics-catalog-r4/catalog.json').read_text())
    original = p/'workplace/intake-20261023/sources/game/8sword'
    helpers = runpy.run_path(str(p/'tools/catalog-all-graphics.py'))
    decode = runpy.run_path(str(p/'tools/prepare-hd-intro.py'))['decode']
    hd = {(r['source_file'], r['record']) for r in catalog['hd_registrations']}
    sources = sorted({r['source_file'] for r in catalog['records']
                      if re.fullmatch(r'MAN(?:0[1-9]|1[0-9]|2[0-5])\.EGG', r['source_file'])})
    assert len(sources) == 25
    out.mkdir()
    style = p/'workplace/player/assets-painted-r48/battle-man11-0-r1.png'
    (out/'style-reference.png').write_bytes(style.read_bytes())
    jobs = []
    for name in sources:
        records = [r for r in catalog['records'] if r['source_file'] == name]
        assert [r['record'] for r in records] == [0, 1, 2, 3]
        if all((name, r['record']) in hd for r in records):
            continue
        source = next(f for f in catalog['files'] if f['file'] == name)
        raw = (original/name).read_bytes()
        assert sha(raw) == source['sha256']
        data = decode(raw) if source['packed'] else raw
        stem = name.lower().removesuffix('.egg')
        sheet = Image.new('RGBA', (1056, 1200), (215, 212, 205, 255))
        frames = []
        for r in records:
            at, w, h, planes = r['decoded_offset'], r['width'], r['height'], r['planes']
            item = data[at:at+r['bytes']]
            assert sha(item) == r['record_sha256']
            im = helpers['planar'](data, (at, w//8, h, planes))
            assert sha(im.tobytes()) == r['decoded_rgba_sha256']
            filename = f'{stem}-native-{r["record"]}.png'
            im.save(out/filename)
            # The game's non-square pixels become the established 3x6 aspect.
            scaled = im.resize((w*6, h*12), Image.Resampling.NEAREST)
            x, y = (r['record'] % 2)*528, (r['record']//2)*600
            sheet.alpha_composite(scaled, (x+(528-scaled.width)//2, y+(600-scaled.height)//2))
            frames.append(dict(record=r['record'], file=filename, record_sha256=r['record_sha256'],
                               decoded_rgba_sha256=r['decoded_rgba_sha256'], width=w, height=h,
                               planes=planes, alpha_bbox=im.getbbox()))
        reference = f'{stem}-reference.png'
        sheet.save(out/reference)
        prompt = f'''Use case: stylized-concept
Asset type: one production-quality transparent 2-by-2 animation sprite atlas for the classic Chinese fantasy strategy RPG 神州八劍, source resource {name}.
Input images: Image 1 is the original four-pose pixel reference in reading order, records 0, 1, 2, 3. Image 2 is an approved HD sprite used ONLY as a painting-style reference; do not copy its costume, hat, anatomy or equipment into this different character.
Primary request: redraw this exact original creature or troop in all FOUR reference poses as detailed hand-painted HD art. Keep the same species, recognizable silhouette, facing direction in each pose, number of limbs, equipment, clothing color blocks, and action phase. Preserve distinctive original colors. For human clothing, use appropriate classical Chinese craftsmanship without changing the identity or adding weapons. For monsters, retain their actual beast anatomy rather than humanizing them. Resolve ambiguous tiny pixels conservatively.
Style: the approved bright hand-painted Chinese ancient-fantasy treatment, fine clean ink contours, luminous colored gouache shading, expressive forms, restrained material detail, legible at small game size. No pixel art, no photorealism, no generic Western fantasy replacement.
Layout: exactly four isolated full-body sprites in an equal 2x2 grid on a square canvas. Record 0 top-left, record 1 top-right, record 2 bottom-left, record 3 bottom-right. Keep each sprite entirely inside its quadrant, centered with generous empty transparent margins, consistent scale and character design across poses. Match pose and facing independently to the corresponding original quadrant.
Constraints: genuinely transparent RGBA background; no checkerboard, paper, scenery, floor, ground shadow, UI, grid lines, lettering, labels, watermark or extra characters. Do not crop a head, foot, wing or weapon. The gray background of Image 1 is reference display only and must not appear in the output.

Important finish: translate EGA color dithering into natural smooth painted shading, never literal checkerboard patterns on faces or fabrics. Humans have natural painted facial features unless the original clearly wears a mask. Do not invent face coverings from dithered skin pixels. Weapons remain solid defined weapons, without extra oversized magical trails.
Strict atlas spacing: each whole figure including weapon must fit inside the central 70 percent of its own quadrant. Keep a wide fully transparent separation across the middle and generous outer margins; no foot, blade or effect may touch the canvas edge or cross into another quadrant.
'''
        prompt_file = f'{stem}-r1.prompt.txt'
        (out/prompt_file).write_text(prompt)
        jobs.append(dict(source_file=name, source_sha256=sha(raw), records=frames,
                         reference=reference, reference_sha256=sha((out/reference).read_bytes()),
                         prompt=prompt_file, prompt_sha256=sha(prompt.encode()),
                         output=f'{stem}-hd-atlas-r1.png', status='awaiting-generation',
                         gameplay_verification='inherited shared-mechanism sampling; no per-creature normal-route gate'))
    assert len(jobs) == 20
    manifest = dict(schema=1, scope='original MAN01..MAN25; MAN27 unknown Taiji excluded',
                    source_groups=25, existing_hd_records=20, missing_groups=len(jobs), missing_records=80,
                    style_reference='style-reference.png', style_sha256=sha(style.read_bytes()),
                    jobs=jobs, generation='built-in image_gen; one four-pose atlas per source resource',
                    production=False, rights='local original-derived research assets; not a public distribution grant')
    (out/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k: v for k, v in manifest.items() if k != 'jobs'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
