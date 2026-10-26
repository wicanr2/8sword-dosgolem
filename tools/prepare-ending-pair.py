#!/usr/bin/env python3
"""053：按END6原始位置及縮小比例匯入透明雙人材質。Docker only。"""
import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path
from PIL import Image, __version__


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    root = a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    art = root/'end6-pair-art-r1'
    generation = json.loads((art/'generation-r2.json').read_text())
    assert generation['tool'] == 'built-in image_gen' and generation['mode'] == 'edit'
    image = art/generation['image']
    assert sha(image) == generation['image_sha256'] == '510742d5838478747a8f3c0bb8c017fed6319071d7564c93718689b144e24a8b'
    assert sha(art/generation['prompt']) == generation['prompt_sha256']
    assert sha(art/generation['reference']) == generation['reference_sha256']
    original = a.project/'workplace/intake-20261023/sources/game/8sword/END6.AY'
    assert sha(original) == 'b8112bbcfe9cd045015da16a06ce98a53622c0fcf5cea436069cdcb0eccc96cc'
    source = json.loads((root/'source.json').read_text())
    records = [row for row in source['records'] if row['source_file'] == 'END6.AY' and row['record'] > 0]
    assert len(records) == 4
    bboxes = [(2,2,128,49), (14,4,121,45), (27,9,109,39), (39,13,96,34)]
    black_counts = [7,14,10,4]
    raw = Image.open(image).convert('RGBA')
    assert raw.size == (1536,1024) and raw.getchannel('A').getextrema() == (0,254)
    prepared = []
    for i, row in enumerate(records):
        assert row['record'] == i+1 and (row['width'], row['height'], row['planes']) == (136,50,6)
        data = (root/row['native']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == row['record_sha256']
        native = Image.open(root/row['image']).convert('RGBA')
        assert native.getchannel('A').getbbox() == bboxes[i]
        black = sum(c[3] != 0 and c[:3] == (0,0,0) for c in native.getdata())
        assert black == black_counts[i]
        x0,y0,x1,y1 = bboxes[i]
        target = (x0*3,y0*6,x1*3,y1*6)
        texture = Image.new('RGBA',(408,300))
        resized = raw.resize((target[2]-target[0],target[3]-target[1]), Image.Resampling.LANCZOS)
        texture.paste(resized, target[:2])
        prepared.append((row, target, black, texture))
    base = a.project/'workplace/player/assets-painted-r62'
    assert len(list(base.iterdir())) == 455
    a.out.mkdir()
    old = {}
    for path in sorted(base.iterdir()):
        assert path.is_file() and not path.is_symlink() and path.stat().st_uid == 1000
        old[path.name] = sha(path)
        shutil.copyfile(path, a.out/path.name)
    manifest = dict(schema=1, source_file='END6.AY', original_sha256=sha(original), records=[])
    for row, target, black, texture in prepared:
        name = f'ending-pair-{row["record"]:02d}.png'
        texture.save(a.out/name)
        manifest['records'].append(dict(record=row['record'], source_sha256=row['record_sha256'],
                                        image=name, image_sha256=sha(a.out/name), width=408, height=300,
                                        native_bbox=bboxes[row['record']-1], target_bbox=target, black_writes=black))
    (a.out/'ending-pair.json').write_text(json.dumps(manifest, indent=2)+'\n')
    assert len(list(a.out.iterdir())) == 460
    report = dict(schema=1, spec='053', status='pair-candidate-not-promoted', files=460, preserved_files=455,
                  base_files=old, manifest=manifest, manifest_sha256=sha(a.out/'ending-pair.json'),
                  generation_sha256=sha(art/'generation-r2.json'), normalization='Full generated canvas resized into each original alpha bbox; generated alpha preserved.',
                  tool_sha256=sha(Path(__file__)))
    target = a.out.parent/'pair-registration-r1.json'
    assert not target.exists()
    target.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(files=460, preserved=455, manifest_sha256=report['manifest_sha256'])))


if __name__ == '__main__':
    main()
