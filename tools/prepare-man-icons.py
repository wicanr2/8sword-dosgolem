#!/usr/bin/env python3
"""052：核對MAN16筆器物圖示並逐張準備原版參考與實際提示。Docker only。"""
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
    p.add_argument('--project', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    source = (a.project / 'workplace/intake-20261023/sources/game/8sword/MAN.AY').read_bytes()
    assert sha(source) == '9849714498718f6616644ad717906cc426c3f3f5f335cdb99dbcc8173c8dbe12'
    catalog = json.loads((a.project / 'docs/images/graphics-inventory-r1.json').read_text())
    records = [r for r in catalog['records'] if r['source_file'] == 'MAN.AY']
    assert len(records) == 29
    spec = importlib.util.spec_from_file_location('planar', a.project / 'tools/catalog-all-graphics.py')
    planar = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(planar)
    a.out.mkdir()
    jobs = []
    for row in records:
        i = row['record']
        if i not in list(range(12, 20)) + list(range(21, 29)):
            continue
        raw = source[row['decoded_offset']:row['decoded_offset']+row['bytes']]
        assert len(raw) == 388 and raw[:4] == bytes((4, 0, 16, 0)) and sha(raw) == row['record_sha256']
        original = planar.planar(raw, (0, 4, 16, 6))
        reference = f'man-{i:02d}-reference.png'
        original.resize((768, 768), Image.Resampling.NEAREST).save(a.out / reference)
        prompt = (
            'Use case: stylized-concept. Asset type: ONE transparent HD inventory icon for the Chinese fantasy DOS game 神州八劍.\n'
            'Input image 1 is the ORIGINAL low-resolution icon, the exact subject, silhouette, orientation, placement and color reference. '
            'Repaint that single object in a refined hand-painted Chinese classical fantasy game style. Preserve all visible parts and their arrangement, '
            'the original major colors and the original shape. Replace pixel dithering with smooth shaded surfaces and restrained painted detail. '
            'Do not reinterpret the object as a different item.\n'
            'Composition: square canvas, object occupying the SAME relative bounding box and orientation as the reference, including its empty margins. '
            'Do not enlarge, rotate or center-crop the object. All parts must stay fully visible. ONE icon only.\n'
            'True transparent background with alpha, not a checkerboard or solid color. No scene, floor, pedestal, cast shadow, frame, lettering, labels, '
            'comparison panels, extra objects or watermark. No added glow or effects that expand the silhouette.\n'
        )
        prompt_name = f'man-{i:02d}-r1.prompt.txt'
        (a.out / prompt_name).write_text(prompt)
        (a.out / f'man-{i:02d}-native.bin').write_bytes(raw)
        jobs.append(dict(index=i, offset=row['decoded_offset'], bytes=388, native_sha256=sha(raw[:260]), record_sha256=sha(raw),
                         reference=reference, reference_sha256=sha((a.out / reference).read_bytes()),
                         prompt=prompt_name, prompt_sha256=sha(prompt.encode()), status='prepared-not-generated'))
    assert len(jobs) == 16
    report = dict(schema=1, spec='052', status='prepared-not-generated', source_file='MAN.AY', source_sha256=sha(source),
                  jobs=jobs, tool_sha256=sha(Path(__file__).read_bytes()), decoder_sha256=sha((a.project/'tools/catalog-all-graphics.py').read_bytes()),
                  pillow=__version__, rights='local-only original-derived art; compact comparisons in existing private repository only')
    (a.out / 'request.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(jobs=len(jobs), request_sha256=sha((a.out/'request.json').read_bytes()))))


if __name__ == '__main__':
    main()
