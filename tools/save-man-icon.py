#!/usr/bin/env python3
"""052：保存內建image_gen的單張PNG、實際提示與參考收據，不改alpha。Docker only。"""
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
    p.add_argument('--batch', type=Path, required=True)
    p.add_argument('--image', type=Path, required=True)
    p.add_argument('--index', type=int, required=True)
    p.add_argument('--variant', type=int, default=1)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert a.batch.stat().st_uid == 1000 and a.variant in (1, 2)
    request = json.loads((a.batch / 'request.json').read_text())
    job = next(j for j in request['jobs'] if j['index'] == a.index)
    prefix = f'man-{a.index:02d}-r{a.variant}'
    prompt = a.batch / (prefix + '.prompt.txt')
    assert prompt.is_file() and a.image.is_file()
    assert sha((a.batch / job['reference']).read_bytes()) == job['reference_sha256']
    if a.variant == 1:
        assert sha(prompt.read_bytes()) == job['prompt_sha256']
    image = Image.open(a.image)
    assert image.format == 'PNG' and min(image.size) >= 512 and max(image.size) <= 4096
    alpha = image.convert('RGBA').getchannel('A')
    assert alpha.getextrema() == (0, 255)
    raw_bbox = alpha.getbbox()
    # Match the existing renderer's alpha<=3 rejection; retain raw PNG bytes.
    bbox = alpha.point(lambda value: 255 if value > 3 else 0).getbbox()
    assert bbox and bbox[0] > 0 and bbox[1] > 0 and bbox[2] < image.width and bbox[3] < image.height
    target, receipt = a.batch / (prefix + '.png'), a.batch / (prefix + '.json')
    assert not target.exists() and not receipt.exists()
    with target.open('xb') as f:
        f.write(a.image.read_bytes())
    result = dict(schema=1, spec='052', status='generated-not-registered', production=False, index=a.index,
                  variant=a.variant, tool='built-in image_gen', transparent_background=True,
                  source_sha256=request['source_sha256'], native_sha256=job['native_sha256'], record_sha256=job['record_sha256'],
                  image=target.name, image_sha256=sha(target.read_bytes()), width=image.width, height=image.height,
                  alpha_extrema=[0, 255], alpha_bbox=list(bbox), raw_alpha_bbox=list(raw_bbox), prompt=prompt.name, prompt_sha256=sha(prompt.read_bytes()),
                  actual_prompt=prompt.read_text(), reference=job['reference'], reference_sha256=job['reference_sha256'],
                  original_request_sha256=sha((a.batch / 'request.json').read_bytes()), tool_sha256=sha(Path(__file__).read_bytes()),
                  pillow=__version__, rights=request['rights'])
    with receipt.open('x') as f:
        f.write(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(index=a.index, variant=a.variant, image_sha256=result['image_sha256'], alpha_bbox=result['alpha_bbox'])))


if __name__ == '__main__':
    main()
