#!/usr/bin/env python3
"""053：匯入END3八劍透明材質，固定Pillow容器執行。"""
import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path
from PIL import Image, __version__


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('project', 'out'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    batch = a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1/swords-art-r1'
    gen = json.loads((batch/'generation-r2.json').read_text())
    assert gen['tool'] == 'built-in image_gen'
    assert sha(batch/gen['image']) == gen['image_sha256'] == 'd3d83dc3d23207934976a47145e06ea321321f62658a19071920a363311bc91f'
    assert sha(batch/gen['prompt']) == gen['prompt_sha256']
    base = a.project/'workplace/player/assets-painted-r59'
    assert len(list(base.iterdir())) == 439
    old = {}
    a.out.mkdir()
    for f in sorted(base.iterdir()):
        assert f.is_file() and not f.is_symlink() and f.stat().st_uid == 1000
        old[f.name] = sha(f)
        shutil.copyfile(f, a.out/f.name)
    im = Image.open(batch/gen['image']).convert('RGBA')
    assert im.size == (1407, 1118) and im.getchannel('A').getextrema() == (0, 255)
    im = im.resize((528, 420), Image.Resampling.LANCZOS)
    assert im.getpixel((264, 210))[3] == 0
    im.save(a.out/'ending-swords.png')
    source = a.project/'workplace/intake-20261023/sources/game/8sword/END3.AY'
    assert sha(source) == 'cb56acd3b5652223083b6c41036b4df821f2310a097224613ddaf56ca599f9ff'
    manifest = dict(schema=1, source_file='END3.AY', original_sha256=sha(source),
                    source_sha256='b13caa558e7e0d93aec2023eedd21fec0f3b6980178770444395c0913e9cc687',
                    image='ending-swords.png', image_sha256=sha(a.out/'ending-swords.png'), width=528, height=420)
    (a.out/'ending-swords.json').write_text(json.dumps(manifest, indent=2)+'\n')
    report = dict(schema=1, spec='053', status='swords-candidate-not-promoted', files=441,
                  preserved_files=439, base_files=old, manifest=manifest,
                  manifest_sha256=sha(a.out/'ending-swords.json'),
                  normalized_rgba_sha256=hashlib.sha256(im.tobytes()).hexdigest(),
                  generation_sha256=sha(batch/'generation-r2.json'), tool_sha256=sha(Path(__file__)))
    receipt = a.out.parent/'swords-registration-r2.json'
    assert not receipt.exists()
    receipt.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ['files', 'preserved_files', 'manifest_sha256', 'normalized_rgba_sha256']}))


if __name__ == '__main__':
    main()
