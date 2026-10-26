#!/usr/bin/env python3
"""053：核對結局37筆來源並保存原像素與顯示比例參考。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import runpy

from PIL import Image, __version__


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not args.out.exists() and args.out.parent.stat().st_uid == 1000
    project = args.project
    catalog_path = project/'docs/images/graphics-inventory-r1.json'
    catalog = json.loads(catalog_path.read_text())
    sources = [f for f in catalog['files'] if f['category'] == 'ending']
    records = [r for r in catalog['records'] if r['source_file'] in {f['file'] for f in sources}]
    assert len(sources) == 13 and len(records) == 37
    decoder_path = project/'tools/catalog-all-graphics.py'
    spec = importlib.util.spec_from_file_location('planar', decoder_path)
    planar = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(planar)
    unpacker_path = project/'tools/prepare-hd-intro.py'
    unpack = runpy.run_path(str(unpacker_path))['decode']
    args.out.mkdir()
    outputs = []
    for source in sources:
        path = project/'workplace/intake-20261023/sources/game/8sword'/source['file']
        packed = path.read_bytes()
        assert sha(packed) == source['sha256']
        data = unpack(packed)
        assert len(data) == source['decoded_bytes'] and sha(data) == source['decoded_sha256']
        entries = [r for r in records if r['source_file'] == source['file']]
        assert sum(r['bytes'] for r in entries) == len(data)
        end = 0
        for row in entries:
            assert row['decoded_offset'] == end
            raw = data[end:end+row['bytes']]
            end += row['bytes']
            assert sha(raw) == row['record_sha256']
            image = planar.planar(raw, (0, row['width']//8, row['height'], row['planes']))
            assert sha(image.tobytes()) == row['decoded_rgba_sha256']
            name = source['file'].replace('.', '-').lower()+f'-{row["record"]:02d}'
            (args.out/f'{name}.bin').write_bytes(raw)
            image.save(args.out/f'{name}-native.png')
            reference = image.resize((row['width']*2, row['height']*4), Image.Resampling.NEAREST)
            reference.save(args.out/f'{name}-reference.png')
            outputs.append(dict(**row, source_sha256=source['sha256'],
                                native=f'{name}.bin', image=f'{name}-native.png',
                                reference=f'{name}-reference.png',
                                reference_sha256=sha((args.out/f'{name}-reference.png').read_bytes()),
                                color_variant=row['planes'] != 1, status='source-prepared-not-HD'))
    report = dict(schema=1, spec='053', status='original-source-prepared-not-HD', records=outputs,
                  color_records=sum(x['color_variant'] for x in outputs), monochrome_records=4,
                  catalog_sha256=sha(catalog_path.read_bytes()), decoder_sha256=sha(decoder_path.read_bytes()),
                  unpacker_sha256=sha(unpacker_path.read_bytes()), tool_sha256=sha(Path(__file__).read_bytes()),
                  pillow=__version__, address_space='decoded file offsets',
                  limits=['Static decoded sources, not normal ending playback or confirmed runtime ordering.'],
                  rights='original and full decoded inputs local only; no public distribution permission')
    assert report['color_records'] == 33
    with (args.out/'source.json').open('x') as f:
        f.write(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(color_records=33, monochrome_records=4, source_sha256=sha((args.out/'source.json').read_bytes()))))


if __name__ == '__main__':
    main()
