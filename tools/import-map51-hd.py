#!/usr/bin/env python3
"""045：保存PMAP51生成圖，或建立不透明材質候選與獨立快取。Docker only。"""
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


def write(path, data):
    with path.open('x') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('save', 'prepare'))
    for name in ('project', 'art'):
        p.add_argument('--' + name, type=Path, required=True)
    for name in ('image', 'base', 'out', 'review'):
        p.add_argument('--' + name, type=Path)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    request = json.loads((a.art / 'request.json').read_text())
    assert request['source_index'] == 51
    if a.action == 'save':
        assert a.art.stat().st_uid == 1000 and a.image.is_file()
        im = Image.open(a.image)
        assert im.format == 'PNG' and min(im.size) >= 512 and max(im.size) <= 4096
        assert im.convert('RGBA').getchannel('A').getextrema() == (255, 255)
        assert sha((a.art / request['prompt']).read_bytes()) == request['prompt_sha256']
        assert sha((a.art / request['reference']).read_bytes()) == request['reference_sha256']
        target = a.art / 'map-landmark-51-r1.png'
        assert not target.exists() and not (a.art / 'generation.json').exists()
        with target.open('xb') as f:
            f.write(a.image.read_bytes())
        report = dict(schema=1, status='generated-not-registered', production=False,
                      tool='built-in image_gen', mode='generate-from-reference', transparent_background=False,
                      image=target.name, image_sha256=sha(target.read_bytes()), width=im.width, height=im.height,
                      prompt=request['prompt'], prompt_sha256=request['prompt_sha256'],
                      reference=request['reference'], reference_sha256=request['reference_sha256'],
                      record_sha256=request['record_sha256'], native_sha256=request['native_sha256'],
                      alpha_extrema=[255, 255], tool_sha256=sha(Path(__file__).read_bytes()), rights=request['rights'])
        write(a.art / 'generation.json', report)
        print(json.dumps(report))
        return
    assert a.base.is_dir() and not a.out.exists() and not a.review.exists()
    assert a.out.parent.stat().st_uid == a.review.parent.stat().st_uid == 1000
    base = {f.name: sha(f.read_bytes()) for f in a.base.iterdir()}
    assert len(base) == 387 and all(f.is_file() and not f.is_symlink() and f.stat().st_uid == 1000 for f in a.base.iterdir())
    generation = json.loads((a.art / 'generation.json').read_text())
    source = (a.project / 'workplace/intake-20261023/sources/game/8sword/PMAP.AY').read_bytes()
    assert sha(source) == request['source_sha256'] == '9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02'
    raw = source[51 * 1004:52 * 1004]
    assert sha(raw) == generation['record_sha256'] and sha(raw[:804]) == generation['native_sha256']
    for key, digest in [('image', 'image_sha256'), ('prompt', 'prompt_sha256')]:
        assert sha((a.art / generation[key]).read_bytes()) == generation[digest]
    spec = importlib.util.spec_from_file_location('sampler', a.project / 'tools/audit-encounter-gui.py')
    sampler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sampler)
    cache = sampler.sample(a.art / generation['image'], 192, 150)
    a.out.mkdir()
    a.review.mkdir()
    for name in base:
        os.link(a.base / name, a.out / name)
    for key in ('image', 'prompt'):
        shutil.copyfile(a.art / generation[key], a.out / generation[key])
    manifest = dict(schema=1, source_file='PMAP.AY', source_sha256=request['source_sha256'], source_index=51,
                    style_reference_sha256='2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6',
                    native_sha256=generation['native_sha256'], record_sha256=generation['record_sha256'], cache_sha256=sha(cache),
                    sampling='bilinear-full-opaque', prompt_file=generation['prompt'], prompt_sha256=generation['prompt_sha256'],
                    image=dict(file=generation['image'], sha256=generation['image_sha256'], width=generation['width'], height=generation['height']))
    write(a.out / 'map-landmark-51.json', manifest)
    report = dict(schema=1, spec='045', status='candidate-registration-review', production=False,
                  manifest_sha256=sha((a.out / 'map-landmark-51.json').read_bytes()), config=manifest,
                  generation_sha256=sha((a.art / 'generation.json').read_bytes()), base_files=base,
                  candidate_files=391, preserved_files=387, tool_sha256=sha(Path(__file__).read_bytes()), pillow=__version__,
                  evidence='fixed original record and shared render mechanism; natural use unknown', rights=request['rights'])
    write(a.out / 'map-landmark-51-provenance.json', report)
    write(a.review / 'registration.json', report)
    (a.review / 'map51.rgba').write_bytes(cache)
    (a.review / 'pmap51-native.bin').write_bytes(raw)
    font = ImageFont.truetype(str(a.project / 'workplace/probe-20261023/graphics-first/font-settings-r1/NotoSansCJK-Black.ttc'), 18, index=3)
    sheet = Image.new('RGB', (800, 390), '#172b2d')
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 8), 'PMAP 51：原版／HD格紋；用途未知，非自然實景', font=font, fill='#f1d69b')
    sheet.paste(Image.open(a.art / request['reference']).convert('RGB').resize((384, 300), Image.Resampling.NEAREST), (8, 66))
    sheet.paste(Image.open(a.art / generation['image']).convert('RGB').resize((384, 300), Image.Resampling.LANCZOS), (408, 66))
    sheet.save(a.review / 'comparison.png')
    assert len(list(a.out.iterdir())) == 391
    assert all(sha((a.out / n).read_bytes()) == d for n, d in base.items())
    print(json.dumps(dict(files=391, preserved=387, manifest_sha256=report['manifest_sha256'], cache_sha256=sha(cache), registration_sha256=sha((a.review / 'registration.json').read_bytes()))))


if __name__ == '__main__':
    main()
