#!/usr/bin/env python3
"""053：匯入END3第1筆紅金光環，保留原始生成圖。Docker only。"""
import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path
from PIL import Image, __version__


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ['project', 'out']: p.add_argument('--'+key, type=Path, required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    b = a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    art = b/'end3-ring-art-r1'
    generation = json.loads((art/'generation-r1.json').read_text())
    assert generation['tool'] == 'built-in image_gen' and generation['mode'] == 'edit'
    image = art/generation['image']
    assert sha(image) == generation['image_sha256'] == 'a630bfb7dcbdccaa6cf4f5e7944f502c8632e12e31265fc534c472fe5cb93adc'
    assert sha(art/generation['prompt']) == generation['prompt_sha256']
    assert sha(art/generation['reference']) == generation['reference_sha256']
    source = next(r for r in json.loads((b/'source.json').read_text())['records'] if r['source_file']=='END3.AY' and r['record']==1)
    assert (source['width'],source['height'],source['planes']) == (232,105,6)
    assert sha(b/source['native']) == source['record_sha256'] == 'f63c6b90c58db6f1bdc596c0c6dc565ecd47b6e8540fcb99cf2d76cbbe2c6f4a'
    original = a.project/'workplace/intake-20261023/sources/game/8sword/END3.AY'
    assert sha(original) == source['source_sha256'] == 'cb56acd3b5652223083b6c41036b4df821f2310a097224613ddaf56ca599f9ff'
    native = Image.open(b/source['image']).convert('RGBA')
    assert hashlib.sha256(native.tobytes()).hexdigest() == source['decoded_rgba_sha256']
    assert not any(c[3] and c[:3]==(0,0,0) for c in native.getdata())
    raw = Image.open(image).convert('RGBA')
    assert raw.size == (1318,1193) and raw.getchannel('A').getextrema() == (0,254)
    texture = raw.resize((696,630),Image.Resampling.LANCZOS)
    base = a.project/'workplace/player/assets-painted-r63'
    assert len(list(base.iterdir())) == 460
    a.out.mkdir()
    old = {}
    for f in sorted(base.iterdir()):
        assert f.is_file() and not f.is_symlink() and f.stat().st_uid == 1000
        old[f.name] = sha(f)
        shutil.copyfile(f,a.out/f.name)
    texture.save(a.out/'ending-ring.png')
    manifest = dict(schema=1,source_file='END3.AY',record=1,original_sha256=sha(original),source_sha256=source['record_sha256'],image='ending-ring.png',image_sha256=sha(a.out/'ending-ring.png'),width=696,height=630)
    (a.out/'ending-ring.json').write_text(json.dumps(manifest,indent=2)+'\n')
    assert len(list(a.out.iterdir())) == 462
    report = dict(schema=1,spec='053',status='ring-candidate-not-promoted',files=462,preserved_files=460,base_files=old,manifest=manifest,manifest_sha256=sha(a.out/'ending-ring.json'),generation_sha256=sha(art/'generation-r1.json'),normalization='Entire generated canvas resized to 696x630 with original generated alpha; no recoloring or background removal.',tool_sha256=sha(Path(__file__)))
    receipt = a.out.parent/'ring-registration-r1.json'
    assert not receipt.exists()
    receipt.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(files=462,preserved=460,manifest_sha256=report['manifest_sha256'])))


if __name__ == '__main__': main()
