#!/usr/bin/env python3
"""053 READY：組合結局來源場景候選，保留正式r56與完整生成原圖。"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil

from PIL import Image, __version__


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not args.out.exists() and args.out.parent.stat().st_uid == 1000
    project = args.project
    base = project/'workplace/player/assets-painted-r56'
    batch = project/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    old = batch/'owned-inputs-r1'
    assert sha(old/'inputs.json') == '19497ef75d6a1eb26c8e5e07b806f4a4ccc1ceada43fb1710a7e850fdd7a6ef2'
    source = json.loads((old/'inputs.json').read_text())
    formal = json.loads((project/'workplace/probe-20261023/graphics-first/story-art-r1/blue-person-correction-r4/runtime-audit-r4.json').read_text())
    assert len(list(base.iterdir())) == 425
    for name, digest in formal['asset_hashes'].items():
        assert sha(base/name) == digest
    assert sha(batch/'end7-r2.png') == '50dc8cfd675457526810c709a0e5197bcb46eff7aef1fdc0d12a6b7774fdde27'
    args.out.mkdir()
    # Candidate view only. Relative links resolve through read-only /project;
    # a promoted standalone group must materialize these unchanged base files.
    for path in base.iterdir():
        target = args.out/path.name
        target.symlink_to(os.path.relpath(path, batch/args.out.name))
    files = {}
    for name in source['files']:
        if name == 'end7.png':
            continue
        assert sha(old/name) == source['files'][name]
        target_name = 'ending-'+name if name.startswith('title-') else name
        shutil.copyfile(old/name, args.out/target_name)
        files[target_name] = sha(args.out/target_name)
    image = Image.open(batch/'end7-r2.png').convert('RGBA')
    assert image.size == (1586, 992) and image.getchannel('A').getextrema() == (255, 255)
    image.resize((1920, 1200), Image.Resampling.LANCZOS).save(args.out/'ending-end7-r2.png')
    files['ending-end7-r2.png'] = sha(args.out/'ending-end7-r2.png')
    catalog = json.loads((batch/'source.json').read_text())
    manifest = dict(schema=1, pam_sha256='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0',
                    pae_sha256='8ae11b4c89f0361ed0a2d5b1859bbb4750047d37f0e26885e6903e4feb721a0c',
                    cjk=copy.deepcopy(source['cjk']), ascii=source['ascii'], profiles=source['profiles'],
                    files=files, sources={r['record_sha256']: r['source_file'] for r in catalog['records']},
                    art_source_sha256=sha(batch/'end7-r2.png'))
    (args.out/'ending.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    assert len(list(args.out.iterdir())) == 433
    receipt = dict(schema=1, spec='053', production=False, tool_sha256=sha(Path(__file__)),
                   manifest_sha256=sha(args.out/'ending.json'), files=files, unchanged_base_files=425,
                   candidate_entries=433, base_links=True,
                   inputs_sha256=sha(old/'inputs.json'), corrected_art_sha256=manifest['art_source_sha256'],
                   limits=['Candidate view uses relative links; read via project alias, not writable output alias.',
                           'Original files, full art and fonts remain local. Unconverted ending art uses source commands.'])
    with (args.out.parent/(args.out.name+'-preparation.json')).open('x') as handle:
        handle.write(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(manifest_sha256=receipt['manifest_sha256'], entries=433, files=files)))


if __name__ == '__main__':
    main()
