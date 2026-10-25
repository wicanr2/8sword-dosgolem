#!/usr/bin/env python3
"""047 DRAFT：在固定 Pillow Docker 準備直接攔截的原版來源樣本。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import struct


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    p, out = args.project, args.out
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000
    assert not out.exists() and out.parent.stat().st_uid == 1000
    original = p/'workplace/intake-20261023/sources/game/8sword'
    catalog = json.loads((p/'workplace/probe-20261023/graphics-first/all-graphics-catalog-r4/catalog.json').read_text())
    decode = runpy.run_path(str(p/'tools/prepare-hd-intro.py'))['decode']
    out.mkdir()
    fixtures = []
    for name in ('PMAP.AY', 'LIVE2.AY', 'GRO02.EG'):
        record = next(r for r in catalog['records'] if r['source_file'] == name and r['record'] == 0)
        raw = (original/name).read_bytes()
        source = next(r for r in catalog['files'] if r['file'] == name)
        assert sha(raw) == source['sha256']
        data = decode(raw) if source['packed'] else raw
        offset = record['decoded_offset']
        item = data[offset:offset+record['bytes']]
        assert sha(item) == record['record_sha256'] and record['planes'] in (4, 5)
        w, h = struct.unpack_from('<HH', item)
        assert 0 < w <= 80 and 0 < h <= 200
        planar = item[:4+w*h*4]
        filename = name.lower().replace('.', '-')+'.bin'
        (out/filename).write_bytes(planar)
        fixtures.append(dict(name=name, file=filename, sha256=sha(planar), source_sha256=sha(raw),
                             record_sha256=sha(item), width_bytes=w, height=h,
                             note='first four planes; fifth PMAP block is not alpha'))
    manifest = dict(schema=1, production=False, normal_player_route=False, fixtures=fixtures,
                    pam_sha256=sha((original/'PAM.AY').read_bytes()),
                    huffman_script_sha256=sha((p/'tools/prepare-hd-intro.py').read_bytes()))
    (out/'fixtures.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == '__main__':
    main()
