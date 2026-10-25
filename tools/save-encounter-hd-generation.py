#!/usr/bin/env python3
"""049：保存單張內建image_gen遭遇圖、實際提示及來源，不登錄正式素材。"""
import argparse
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, __version__


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('project', 'out', 'image', 'request'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert a.out.is_dir() and a.out.stat().st_uid == 1000
    request = json.loads(a.request.read_text())
    number = request['record']
    assert number in (4, 5, 8, 9) and request['tool'] == 'built-in image_gen'
    assert request['transparent_background'] is True
    source = a.project / 'workplace/intake-20261023/sources/game/8sword/ENEMY.AY'
    raw = source.read_bytes()
    assert sha(raw) == '0d18b068e177b54f7b8a2b30072e9ae3ebc984fbed9fd6a8706f71d3140a5ffd'
    refs = [a.project / s for s in request['references']]
    assert len(refs) == 2 and all(f.is_file() for f in refs)
    im = Image.open(a.image).convert('RGBA')
    alpha = im.getchannel('A')
    assert alpha.getextrema() == (0, 255) and min(im.size) >= 512
    box = alpha.point(lambda v: 255 if v > 3 else 0).getbbox()
    assert box and box[0] > 0 and box[1] > 0 and box[2] < im.width and box[3] < im.height
    stem = f'encounter-{number:02d}-hd-r1'
    files = [a.out / (stem + s) for s in ('.png', '.prompt.txt', '.json')]
    assert not any(f.exists() for f in files)
    image, prompt, receipt = files
    with image.open('xb') as f:
        f.write(a.image.read_bytes())
    with prompt.open('x') as f:
        f.write(request['prompt'])
    report = dict(schema=1, status='generated-not-registered', production=False,
                  record=number, source='ENEMY.AY', source_sha256=sha(raw),
                  record_sha256=sha(raw[number * 1204:(number + 1) * 1204]),
                  tool=request['tool'], mode=request.get('mode', 'generate-from-references'),
                  references=[dict(file=str(f.relative_to(a.project)), sha256=sha(f.read_bytes())) for f in refs],
                  prompt=prompt.name, prompt_sha256=sha(prompt.read_bytes()),
                  image=image.name, image_sha256=sha(image.read_bytes()), width=im.width, height=im.height,
                  alpha_extrema=alpha.getextrema(), alpha_bbox_gt3=box,
                  transparent_background=True, pillow=__version__, tool_sha256=sha(Path(__file__).read_bytes()),
                  validation='art and alpha only; representative controlled presentation authorized; no natural encounter claim',
                  rights='local-only original-derived; no public distribution grant')
    with receipt.open('x') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write('\n')
    assert all(f.stat().st_uid == 1000 for f in files)
    print(json.dumps({k: report[k] for k in ('record', 'status', 'image', 'image_sha256', 'width', 'height')}))


if __name__ == '__main__':
    main()
