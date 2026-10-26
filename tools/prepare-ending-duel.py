#!/usr/bin/env python3
"""053：固定幾何匯入END1對峙人物，保留r60素材與原PNG。Docker only。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
from PIL import Image, __version__


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('project','out'):
        p.add_argument('--'+name,type=Path,required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    root = a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    batch = root/'end1-art-r1'
    generation = json.loads((batch/'generation-r1.json').read_text())
    assert generation['tool'] == 'built-in image_gen'
    assert sha(batch/generation['image']) == generation['image_sha256'] == '40851c0c267d190ea25242a24aad7177ef15c668ecf448a3688a8210156e6210'
    assert sha(batch/generation['prompt']) == generation['prompt_sha256']
    assert sha(root/generation['reference']) == generation['reference_sha256']
    base = a.project/'workplace/player/assets-painted-r60'
    assert len(list(base.iterdir())) == 441
    a.out.mkdir()
    old = {}
    for f in sorted(base.iterdir()):
        assert f.is_file() and not f.is_symlink() and f.stat().st_uid == 1000
        old[f.name] = sha(f)
        shutil.copyfile(f,a.out/f.name)
    raw = Image.open(batch/generation['image']).convert('RGBA')
    assert raw.size == (2169,725) and raw.getchannel('A').getextrema() == (255,255)
    crop = [0,35,2169,680]
    im = raw.crop(crop).resize((1536,450),Image.Resampling.LANCZOS)
    im.save(a.out/'ending-duel.png')
    source = a.project/'workplace/intake-20261023/sources/game/8sword/END1.AY'
    assert sha(source) == '7c1c6f91f4369d95c95b2d1e0ac09670ae459883add506bfe67dbe16da22e2b8'
    manifest = dict(schema=1,source_file='END1.AY',original_sha256=sha(source),
                    source_sha256='4a5df66d3efaef4610802b281a9a216116922c914ebe920ecec14af6e94936ae',
                    image='ending-duel.png',image_sha256=sha(a.out/'ending-duel.png'),width=1536,height=450)
    (a.out/'ending-duel.json').write_text(json.dumps(manifest,indent=2)+'\n')
    report = dict(schema=1,spec='053',status='duel-candidate-not-promoted',files=443,preserved_files=441,
                  base_files=old,crop=crop,manifest=manifest,manifest_sha256=sha(a.out/'ending-duel.json'),
                  normalized_rgba_sha256=hashlib.sha256(im.tobytes()).hexdigest(),
                  generation_sha256=sha(batch/'generation-r1.json'),tool_sha256=sha(Path(__file__)))
    target = a.out.parent/'duel-registration-r1.json'
    assert not target.exists();target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['files','preserved_files','manifest_sha256','normalized_rgba_sha256']}))


if __name__ == '__main__':
    main()
