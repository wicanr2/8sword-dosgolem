"""041：共用已驗 MAN21 首筆，新增軍隊頁鏡射清單。Docker only。"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ['base', 'source', 'out']:
        ap.add_argument('--'+name, type=Path, required=True)
    a = ap.parse_args()
    assert not a.out.exists() and a.out.parent.is_dir()
    assert a.source.name == 'MAN21.EGG' and sha(a.source) == '47cc484319abeba53551c20b7cf4b9b2c6061f2da3b6cda14155b3598f10982c'
    base = {p.name: sha(p) for p in a.base.iterdir() if p.is_file()}
    assert len(base) == 181 and len(list(a.base.iterdir())) == 181
    assert not (a.base/'army-man21.json').exists()
    frame = json.loads((a.base/'battle-man21.json').read_text())['frames'][0]
    assert frame['record'] == 0 and frame['image']['source_index'] == 98
    assert sha(a.base/frame['image']['file']) == 'e710379542cf1c4279ce1703b17ed9d3a839a2e831add705d0f93a370cbf8122'
    style = json.loads((a.base/'battle-man21.json').read_text())['style_reference_sha256']
    manifest = dict(schema=1, source_file='MAN21.EGG', source_sha256=sha(a.source), record=0,
                    transform='mirror-six-planes', source_id=99, target_id=150,
                    style_reference_sha256=style,
                    cache_sha256='0d2155399bd208382cc623fd4087ebf274bdc497f82d807b5d56b551f22f58ee')
    shutil.copytree(a.base, a.out)
    (a.out/'army-man21.json').write_text(json.dumps(manifest, indent=2)+'\n')
    receipt = dict(schema=1, spec='041', source_file=a.source.name, source_sha256=sha(a.source),
                   preserved_files=base, shared_image=frame['image'], original_PNG_unchanged=True,
                   transform='mirror an immutable copy of source cache 99; no image regeneration',
                   cache_sha256=manifest['cache_sha256'],
                   rights='local-only original-derived; no public distribution grant')
    (a.out/'army-man21-source.json').write_text(json.dumps(receipt, indent=2)+'\n')
    assert all(sha(a.out/name) == digest for name, digest in base.items())
    print('183 files; all 181 base files preserved; no new PNG')


if __name__ == '__main__':
    main()
