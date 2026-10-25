#!/usr/bin/env python3
"""050：保存內建生成結果，或產生三背景候選、獨立快取與五幅總覽。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil

from PIL import Image, ImageDraw, ImageFont, __version__


def sha(data):
    return hashlib.sha256(data).hexdigest()


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def write(path, obj):
    with path.open('x') as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('save', 'prepare'))
    for key in ('project', 'batch'):
        p.add_argument('--' + key, type=Path, required=True)
    p.add_argument('--number', type=int, choices=(3, 4, 5))
    for key in ('image', 'base', 'out', 'review'):
        p.add_argument('--' + key, type=Path)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    request = json.loads((a.batch / 'manifest.json').read_text())
    assert len(request['jobs']) == 3
    if a.action == 'save':
        assert a.batch.stat().st_uid == 1000 and a.image.is_file()
        job = next(j for j in request['jobs'] if j['number'] == a.number)
        im = Image.open(a.image)
        assert im.format == 'PNG' and min(im.size) >= 512 and max(im.size) <= 4096
        assert im.convert('RGBA').getchannel('A').getextrema() == (255, 255)
        assert sha((a.batch / job['prompt']).read_bytes()) == job['prompt_sha256']
        assert sha((a.batch / job['reference']).read_bytes()) == job['reference_sha256']
        assert sha((a.project / request['style_reference']).read_bytes()) == request['style_sha256']
        target = a.batch / job['output']
        receipt = target.with_suffix('.json')
        assert not target.exists() and not receipt.exists()
        with target.open('xb') as f:
            f.write(a.image.read_bytes())
        report = dict(schema=1, status='generated-not-registered', production=False, spec='050',
                      tool='built-in image_gen', mode='generate-from-references', transparent_background=False,
                      source=job['source'], source_sha256=job['source_sha256'], native_sha256=job['native_sha256'],
                      reference=job['reference'], reference_sha256=job['reference_sha256'],
                      style_reference=request['style_reference'], style_sha256=request['style_sha256'],
                      prompt=job['prompt'], prompt_sha256=job['prompt_sha256'], image=target.name,
                      image_sha256=sha(target.read_bytes()), width=im.width, height=im.height,
                      alpha_extrema=[255, 255], tool_sha256=sha(Path(__file__).read_bytes()), rights=request['rights'])
        write(receipt, report)
        assert target.stat().st_uid == receipt.stat().st_uid == 1000
        print(json.dumps({k: report[k] for k in ['source', 'status', 'image_sha256', 'width', 'height']}))
        return
    assert a.base.is_dir() and not a.out.exists() and not a.review.exists()
    assert a.out.parent.stat().st_uid == a.review.parent.stat().st_uid == 1000
    base = {f.name: sha(f.read_bytes()) for f in sorted(a.base.iterdir()) if f.is_file()}
    assert len(base) == 367 and all(f.is_file() and not f.is_symlink() for f in a.base.iterdir())
    a.out.mkdir()
    a.review.mkdir()
    for name in base:
        # Complete immutable base groups can share storage; replacements always use new files.
        os.link(a.base / name, a.out / name)
    sampler = module(a.project / 'tools/audit-encounter-gui.py', 'sampler')
    groups = []
    for job in request['jobs']:
        i = job['number']
        receipt = json.loads((a.batch / Path(job['output']).with_suffix('.json')).read_text())
        assert receipt['source_sha256'] == job['source_sha256'] and receipt['native_sha256'] == job['native_sha256']
        for key, digest in [('image', 'image_sha256'), ('prompt', 'prompt_sha256')]:
            assert sha((a.batch / receipt[key]).read_bytes()) == receipt[digest]
            shutil.copyfile(a.batch / receipt[key], a.out / receipt[key])
        image = Image.open(a.out / receipt['image'])
        assert image.convert('RGBA').getchannel('A').getextrema() == (255, 255)
        cache = sampler.sample(a.out / receipt['image'], 1920, 1200)
        (a.review / f'gro{i:02d}-background.rgba').write_bytes(cache)
        raw = (a.batch / job['native']).read_bytes()
        assert sha(raw) == job['native_sha256']
        (a.review / job['native']).write_bytes(raw)
        m = dict(schema=1, source_file=job['source'], source_sha256=job['source_sha256'], native_sha256=job['native_sha256'],
                 pam_sha256='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0',
                 style='B-bright-painted-r1', style_reference_sha256='2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6',
                 image=dict(source_index=840 + i, file=receipt['image'], sha256=receipt['image_sha256'],
                            width=image.width, height=image.height, sampling='bitmap'),
                 prompt_file=receipt['prompt'], prompt_sha256=receipt['prompt_sha256'], cache_sha256=sha(cache))
        name = f'battle-gro{i:02d}.json'
        write(a.out / name, m)
        groups.append(dict(number=i, manifest=name, manifest_sha256=sha((a.out / name).read_bytes()), config=m,
                           generation_receipt_sha256=sha((a.batch / Path(job['output']).with_suffix('.json')).read_bytes())))
    decoder = module(a.project / 'tools/prepare-hd-intro.py', 'decoder')
    planar = module(a.project / 'tools/catalog-all-graphics.py', 'planar')
    font = ImageFont.truetype(str(a.project / 'workplace/probe-20261023/graphics-first/font-settings-r1/NotoSansCJK-Black.ttc'), 20, index=3)
    sheet = Image.new('RGB', (816, 1472), '#172b2d')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 10), '五幅彩色戰場背景：原版／HD素材對照', font=font, fill='#f1d69b')
    draw.text((16, 40), '保留原版構圖與配色；素材定位，非自然戰鬥截圖。', font=font, fill='#ded7bf')
    for i in range(1, 6):
        source = a.project / f'workplace/intake-20261023/sources/game/8sword/GRO{i:02d}.EG'
        raw = decoder.decode(source.read_bytes())
        im = planar.planar(raw, (0, 80, 200, 4)).resize((384, 240), Image.Resampling.NEAREST)
        if i < 3:
            name = 'battle-palace-background-r1.png' if i == 1 else 'battle-background-r1.png'
            hd = Image.open(a.base / name)
        else:
            hd = Image.open(a.out / f'gro{i:02d}-hd-r1.png')
        y = 78 + (i - 1) * 278
        draw.text((12, y), f'GRO{i:02d}.EG   原版 / HD', font=font, fill='#f1d69b')
        sheet.paste(im, (12, y + 30))
        sheet.paste(hd.convert('RGB').resize((384, 240), Image.Resampling.LANCZOS), (420, y + 30))
    sheet.save(a.review / 'comparison.png')
    report = dict(schema=1, spec='050', status='candidate-registration-review', production=False,
                  base_files=base, groups=groups, files=377, preserved=367,
                  comparison_sha256=sha((a.review / 'comparison.png').read_bytes()),
                  tool_sha256=sha(Path(__file__).read_bytes()), pillow=__version__, rights=request['rights'])
    write(a.out / 'battle-backgrounds-import.json', report)
    write(a.review / 'registration.json', report)
    assert len(list(a.out.iterdir())) == 377
    assert all(sha((a.out / n).read_bytes()) == d for n, d in base.items())
    print(json.dumps(dict(files=377, preserved=367, groups=3, registration_sha256=sha((a.review / 'registration.json').read_bytes()))))


if __name__ == '__main__':
    main()
