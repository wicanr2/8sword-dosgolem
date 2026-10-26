#!/usr/bin/env python3
"""014：匯入使用者指定的海報姿態前導圖，保留r58與完整生成紀錄。Docker only。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
from PIL import Image, __version__


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    with path.open('x') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2)+'\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('project', 'batch', 'base', 'out', 'images'):
        p.add_argument('--'+key, type=Path, required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid == a.images.stat().st_uid == 1000
    generation = json.loads((a.batch/'generation-r4.json').read_text())
    assert generation['tool'] == 'built-in image_gen'
    raw, prompt = a.batch/generation['image'], a.batch/generation['prompt']
    assert sha(raw) == generation['image_sha256'] == '92c27b8030dfa335883483b06e8b81a1beeca846a150d92940da044baf35476e'
    assert sha(prompt) == generation['prompt_sha256'] and prompt.read_text() == generation['actual_prompt']
    for item in generation['references']:
        assert sha(a.project/item['path']) == item['sha256']
    source = a.project/'workplace/intake-20261023/sources/game/8sword/TIT6V.AY'
    assert sha(source) == '2131ac054ffd0df4c0f6edff23a393be2cf0416b72b6bb43eedc5d4d844b4212'
    assert all(f.is_file() and not f.is_symlink() and f.stat().st_uid == 1000 for f in a.base.iterdir())
    old = {f.name: sha(f) for f in sorted(a.base.iterdir())}
    assert len(old) == 439
    replaced = {'story-prelude.png', 'story-prelude.json', 'story-prelude-import.json'}
    assert replaced <= set(old)
    a.out.mkdir()
    for name in old:
        if name not in replaced:
            os.link(a.base/name, a.out/name)
    image = Image.open(raw).convert('RGBA')
    assert image.size == (1586, 992) and image.getchannel('A').getextrema() == (255, 255)
    canvas = image.resize((1920, 1200), Image.Resampling.LANCZOS)
    canvas.save(a.out/'story-prelude.png')
    assert sha(a.out/'story-prelude.png') == '8fda0573047dfbcc8373e921d09ff175befc7daada5bba01e9d4ec9a7c705541'
    manifest = dict(schema=1, source_sha256='9aadec77cf59adb1f444d47891526af7da888bebecc648a3fa16a6f0adcd6dfe',
                    approved_sha256=sha(raw), image='story-prelude.png', image_sha256=sha(a.out/'story-prelude.png'),
                    width=1920, height=1200, rights='local-only original-derived HD artwork; no public distribution permission')
    write(a.out/'story-prelude.json', manifest)
    report = dict(schema=1, spec='014', status='poster-pose-candidate-not-promoted', production=False,
                  config=manifest, base_files_sha256=old, preserved_files=436, replaced=sorted(replaced), files=439,
                  generation_sha256=sha(a.batch/'generation-r4.json'), source_sha256=sha(source),
                  canvas_rgba_sha256=hashlib.sha256(canvas.tobytes()).hexdigest(),
                  canvas_normalization='Pillow11.3.0 LANCZOS full-frame1920x1200, raw generation unchanged',
                  tool_sha256=sha(Path(__file__)), pillow=__version__)
    write(a.out/'story-prelude-import.json', report)
    write(a.batch/'registration-r4.json', report)
    name = 'story-prelude-color-poster-pose-r4'
    for src, suffix in ((raw, '.png'), (prompt, '.prompt.txt')):
        target = a.images/(name+suffix)
        assert not target.exists()
        shutil.copyfile(src, target)
    write(a.images/(name+'.json'), dict(generation, file=name+'.png', prompt=name+'.prompt.txt',
          supersedes='story-prelude-color-corrected-r3.png', registration_sha256=sha(a.batch/'registration-r4.json')))
    assert len(list(a.out.iterdir())) == 439
    assert all(sha(a.out/n) == value for n, value in old.items() if n not in replaced)
    print(json.dumps(dict(files=439, preserved=436, registration_sha256=sha(a.batch/'registration-r4.json'))))


if __name__ == '__main__':
    main()
