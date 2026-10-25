#!/usr/bin/env python3
"""051：保存三張無文字建築HD，建立獨立候選與六份來源總覽。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil

from PIL import Image, ImageDraw, ImageFont, __version__

GROUPS = {1: 847, 3: 848, 5: 850}


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
    p.add_argument('--number', type=int, choices=tuple(GROUPS))
    for key in ('image', 'base', 'out', 'review'):
        p.add_argument('--' + key, type=Path)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    request = json.loads((a.batch / 'manifest.json').read_text())
    if a.action == 'save':
        assert a.batch.stat().st_uid == 1000 and a.image.is_file()
        job = next(j for j in request['jobs'] if j['number'] == a.number)
        assert not job['inscription_review_required']
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
        report = dict(schema=1, status='generated-not-registered', production=False, spec='051',
                      tool='built-in image_gen', mode='generate-from-references', transparent_background=False,
                      source=job['source'], source_sha256=job['source_sha256'], native_sha256=job['native_sha256'],
                      reference=job['reference'], reference_sha256=job['reference_sha256'],
                      style_reference=request['style_reference'], style_sha256=request['style_sha256'],
                      prompt=job['prompt'], prompt_sha256=job['prompt_sha256'], image=target.name,
                      image_sha256=sha(target.read_bytes()), width=im.width, height=im.height,
                      alpha_extrema=[255, 255], tool_sha256=sha(Path(__file__).read_bytes()), rights=request['rights'])
        write(receipt, report)
        print(json.dumps({k: report[k] for k in ['source', 'status', 'image_sha256', 'width', 'height']}))
        return
    assert a.base.is_dir() and not a.out.exists() and not a.review.exists()
    assert a.out.parent.stat().st_uid == a.review.parent.stat().st_uid == 1000
    base = {f.name: sha(f.read_bytes()) for f in sorted(a.base.iterdir()) if f.is_file()}
    assert len(base) == 377 and all(f.is_file() and not f.is_symlink() and f.stat().st_uid == 1000 for f in a.base.iterdir())
    a.out.mkdir()
    a.review.mkdir()
    for name in base:
        os.link(a.base / name, a.out / name)
    sampler = module(a.project / 'tools/audit-encounter-gui.py', 'sampler')
    groups = []
    for job in request['jobs']:
        i = job['number']
        if i not in GROUPS:
            continue
        receipt = json.loads((a.batch / Path(job['output']).with_suffix('.json')).read_text())
        assert receipt['source_sha256'] == job['source_sha256'] and receipt['native_sha256'] == job['native_sha256']
        for key, digest in [('image', 'image_sha256'), ('prompt', 'prompt_sha256')]:
            assert sha((a.batch / receipt[key]).read_bytes()) == receipt[digest]
            shutil.copyfile(a.batch / receipt[key], a.out / receipt[key])
        image = Image.open(a.out / receipt['image'])
        cache = sampler.sample(a.out / receipt['image'], 1344, 600)
        (a.review / f'live{i}-building.rgba').write_bytes(cache)
        raw = (a.batch / job['native']).read_bytes()
        assert sha(raw) == job['native_sha256']
        (a.review / job['native']).write_bytes(raw)
        m = dict(schema=1, source_file=job['source'], source_sha256=job['source_sha256'], native_sha256=job['native_sha256'],
                 pam_sha256='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0',
                 style='B-bright-painted-r1', style_reference_sha256='2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6',
                 image=dict(source_index=GROUPS[i] - 1, file=receipt['image'], sha256=receipt['image_sha256'],
                            width=image.width, height=image.height, sampling='bitmap'),
                 prompt_file=receipt['prompt'], prompt_sha256=receipt['prompt_sha256'], cache_sha256=sha(cache))
        name = f'building-live{i}.json'
        write(a.out / name, m)
        groups.append(dict(number=i, material_id=GROUPS[i], manifest=name, manifest_sha256=sha((a.out / name).read_bytes()), config=m,
                           generation_receipt_sha256=sha((a.batch / Path(job['output']).with_suffix('.json')).read_bytes())))
    decoder = module(a.project / 'tools/prepare-hd-intro.py', 'decoder')
    planar = module(a.project / 'tools/catalog-all-graphics.py', 'planar')
    font = ImageFont.truetype(str(a.project / 'workplace/probe-20261023/graphics-first/font-settings-r1/NotoSansCJK-Black.ttc'), 20, index=3)
    sheet = Image.new('RGB', (928, 1532), '#172b2d')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 10), '六份建築素材：原版／HD對照', font=font, fill='#f1d69b')
    draw.text((16, 40), '四份HD素材；碑文待核對、紅牆院門待選稿。非自然玩家截圖。', font=font, fill='#ded7bf')
    for i in range(1, 7):
        source = a.project / f'workplace/intake-20261023/sources/game/8sword/LIVE{i}.AY'
        raw = decoder.decode(source.read_bytes())
        im = planar.planar(raw, (0, 56, 100, 4)).resize((448, 200), Image.Resampling.NEAREST)
        y = 78 + (i - 1) * 242
        draw.text((12, y), f'LIVE{i}.AY   原版 / HD', font=font, fill='#f1d69b')
        sheet.paste(im, (12, y + 30))
        if i in GROUPS or i == 2:
            name = f'live{i}-hd-r1.png' if i != 2 else 'recruitment-building-r1.png'
            hd = Image.open(a.out / name)
            sheet.paste(hd.convert('RGB').resize((448, 200), Image.Resampling.LANCZOS), (472, y + 30))
        else:
            text = '原圖保留：碑文尚待核對' if i == 4 else '原圖保留：既有樣稿待選定'
            draw.text((488, y + 100), text, font=font, fill='#ded7bf')
    sheet.save(a.review / 'comparison.png')
    report = dict(schema=1, spec='051', status='candidate-registration-review', production=False,
                  base_files=base, groups=groups, files=387, preserved=377, deferred=[4, 6],
                  comparison_sha256=sha((a.review / 'comparison.png').read_bytes()),
                  tool_sha256=sha(Path(__file__).read_bytes()), pillow=__version__, rights=request['rights'])
    write(a.out / 'buildings-import.json', report)
    write(a.review / 'registration.json', report)
    assert len(list(a.out.iterdir())) == 387
    assert all(sha((a.out / n).read_bytes()) == d for n, d in base.items())
    print(json.dumps(dict(files=387, preserved=377, groups=3, deferred=[4, 6], registration_sha256=sha((a.review / 'registration.json').read_bytes()))))


if __name__ == '__main__':
    main()
