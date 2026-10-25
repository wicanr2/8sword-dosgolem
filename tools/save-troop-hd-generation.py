#!/usr/bin/env python3
"""048：保存內建image_gen結果與逐檔來源，不改正式資產清單。"""
import argparse
import hashlib
import json
import os
from pathlib import Path

from PIL import Image


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', type=Path, required=True)
    parser.add_argument('--resource', required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--prompt', required=True)
    parser.add_argument('--mode', choices=('generate', 'edit'), default='generate')
    args = parser.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000
    batch = args.batch
    assert batch.is_dir() and batch.stat().st_uid == 1000 and args.source.is_file()
    request = json.loads((batch/'manifest.json').read_text())
    job = next(j for j in request['jobs'] if j['source_file'] == args.resource)
    prompt = batch/args.prompt
    assert prompt.is_file() and prompt.parent == batch
    image = Image.open(args.source)
    image.load()
    alpha = image.convert('RGBA').getchannel('A')
    assert alpha.getextrema() == (0, 255), 'requested transparent output must actually contain alpha'
    w, h = image.size
    assert w >= 512 and h >= 512
    quadrants = [(0, 0, w//2, h//2), (w//2, 0, w, h//2),
                 (0, h//2, w//2, h), (w//2, h//2, w, h)]
    poses = []
    for i, rectangle in enumerate(quadrants):
        box = alpha.crop(rectangle).getbbox()
        assert box is not None, ('empty pose', i)
        poses.append(dict(record=i, quadrant=rectangle, alpha_bbox=box,
                          touches_quadrant_edge=box[0] == 0 or box[1] == 0 or
                          box[2] == rectangle[2]-rectangle[0] or box[3] == rectangle[3]-rectangle[1]))
    raw = args.source.read_bytes()
    output = batch/job['output']
    receipt = batch/(output.stem+'.json')
    assert not output.exists() and not receipt.exists()
    with output.open('xb') as f:
        f.write(raw)
    report = dict(schema=1, status='generated-not-registered', production=False,
                  resource=args.resource, source_sha256=job['source_sha256'],
                  original_records=job['records'], tool='built-in image_gen', mode=args.mode,
                  prompt=args.prompt, prompt_sha256=sha(prompt.read_bytes()),
                  native_reference=job['reference'], native_reference_sha256=job['reference_sha256'],
                  style_reference=request['style_reference'], style_sha256=request['style_sha256'],
                  image=output.name, image_sha256=sha(raw), bytes=len(raw), width=w, height=h,
                  alpha_extrema=alpha.getextrema(), poses=poses,
                  validation='file/alpha/grid inventory only; per-creature gameplay verification waived by user',
                  rights=request['rights'])
    with receipt.open('x') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write('\n')
    assert output.stat().st_uid == receipt.stat().st_uid == 1000
    print(json.dumps({k: report[k] for k in ('resource', 'status', 'image', 'image_sha256', 'width', 'height')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
