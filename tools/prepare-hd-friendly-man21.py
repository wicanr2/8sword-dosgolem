#!/usr/bin/env python3
"""042：由已驗四份鏡射登錄資料匯入可選清單，不新增PNG。Docker only。"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base', 'original', 'prototype', 'out'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    assert not args.out.exists() and args.base.is_dir()
    registration = args.prototype / 'registration.json'
    assert sha(registration) == '70dd5894372d6a78587899e7791032f4411e4bda47d35f03c4126e1f00a237cb'
    reg = json.loads(registration.read_text())
    assert sha(args.original / 'MAN21.EGG') == reg['source_sha256']
    assert not (args.base / 'battle-friendly-man21.json').exists()
    frames = []
    for i, e in enumerate(reg['entries']):
        assert e['record'] == i and e['source_id'] == 99 + i
        assert sha(args.base / e['image_file']) == e['image_sha256']
        assert sha(args.prototype / e['cache_file']) == e['cache_sha256']
        frames.append(dict(record=i, source_id=99+i, target_id=152+i, native_sha256=e['native_sha256'], record_sha256=e['six_plane_sha256'], original_cache_sha256=e['original_cache_sha256'], cache_sha256=e['cache_sha256']))
    assert len(frames) == 4
    manifest = dict(schema=1, source_file='MAN21.EGG', source_sha256=reg['source_sha256'], pam_sha256='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0', transform='mirror-six-planes', style='B-bright-painted-r1', style_reference_sha256='2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6', frames=frames)
    files = sorted(args.base.iterdir())
    assert all(p.is_file() and not p.is_symlink() for p in files)
    preserved = {p.name: sha(p) for p in files}
    args.out.mkdir()
    for path in files:
        shutil.copyfile(path, args.out / path.name)
    (args.out / 'battle-friendly-man21.json').write_text(json.dumps(manifest, indent=2) + '\n')
    record = dict(spec='042', source_sha256=reg['source_sha256'], prototype_registration_sha256=sha(registration), frames=frames, preserved_files=preserved, PNG_bytes_unchanged=True, rights='local-only derived material; no public redistribution grant')
    (args.out / 'battle-friendly-man21-source.json').write_text(json.dumps(record, indent=2) + '\n')
    assert len(list(args.out.iterdir())) == len(files) + 2
    assert all(sha(args.out / name) == digest for name, digest in preserved.items())
    print(json.dumps(dict(files=len(files)+2, preserved=len(files))))


if __name__ == '__main__':
    main()
