"""在固定 Pillow Docker 內匯入 029；原圖與既有素材保持。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from PIL import Image

SOURCE_SHA = '5504591888f306aee2fce04015a81fca30e4e6c8bd48897c5103abcece780bcb'
STYLE_SHA = '2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6'
RAW_SHA = '71eed2ab870b03ccc366cd023c6a596c865220bed62b89cd8d9c045bea64dba6'
CACHES = [
    '440932408dcd85a70d4700731682bc235ad89574e541f1a36050c3815fc382c9',
    '2ab4c35017923bc12322986dd966fa042caef3a10dc16ab839c217a277f663ac',
    '83db999fc0339a8160fa2c6e7077409ff0343b6654f7d95e7acbc20051b9671d',
    'ad76295593ef0c421d9793658f5e4bc95cd66f2712b29aac971692e64d686fdf',
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--base', type=Path, required=True)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--refs', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    assert args.base.is_dir() and args.out.is_dir() and not any(args.out.iterdir())
    assert args.out.stat().st_uid == 1000
    assert sha(args.source) == SOURCE_SHA
    terrain = json.loads((args.base/'terrain.json').read_text())
    assert terrain['style'] == 'B-bright-painted-r1' and terrain['style_reference_sha256'] == STYLE_SHA
    assert (args.base/'battle-background.json').is_file()
    files = list(args.base.iterdir())
    assert all(f.is_file() and not f.is_symlink() for f in files)
    before = {f.name: sha(f) for f in files}
    additions = ['battle-choi.json', 'battle-choi-r1.png', 'battle-choi-provenance-r1.json', 'battle-choi.prompt.txt']
    assert not set(additions) & set(before)
    raw = args.refs/'frame-0-painted-raw-r1.png'
    assert sha(raw) == RAW_SHA
    art = json.loads((args.refs/'art-provenance-r1.json').read_text())
    source = json.loads((args.refs/'choi-source-r1.json').read_text())
    assert art['raw']['sha256'] == RAW_SHA and source['input']['sha256'] == SOURCE_SHA
    prompt = args.refs/art['actual_prompt']['file']
    assert sha(prompt) == art['actual_prompt']['sha256']
    assert len(art['frames']) == len(source['records']) == 4
    frames = []
    for i, (f, original) in enumerate(zip(art['frames'], source['records'])):
        assert f['record'] == original['record'] == i and f['clockwise_quarters'] == i
        assert f['cache_sha256'] == CACHES[i] and sha(args.refs/f['cache_file']) == CACHES[i]
        assert f['target_rect'] == [24, 36, 219, 222]
        frames.append(dict(record=i, file_offset=i*3304, clockwise_quarters=i,
                           native_sha256=original['native_sha256'], record_sha256=original['record_sha256'],
                           cache_sha256=CACHES[i]))
    image = Image.open(raw).convert('RGBA')
    assert image.size == (1254, 1254) and image.getchannel('A').getextrema() == (0, 255)
    assert image.getchannel('A').point(lambda a: 255 if a > 3 else 0).getbbox() == (103, 112, 1155, 1150)
    manifest = dict(schema=1, source_file='CHOI.EGG', source_sha256=SOURCE_SHA,
                    style='B-bright-painted-r1', style_reference_sha256=STYLE_SHA,
                    image=dict(source_index=107, file='battle-choi-r1.png', sha256=RAW_SHA,
                               width=1254, height=1254, sampling='bitmap', source_rect=[101, 110, 1056, 1042]),
                    frames=frames)
    for f in files:
        shutil.copy2(f, args.out/f.name)
    shutil.copyfile(raw, args.out/'battle-choi-r1.png')
    shutil.copyfile(prompt, args.out/'battle-choi.prompt.txt')
    (args.out/'battle-choi.json').write_text(json.dumps(manifest, indent=2)+'\n')
    provenance = dict(schema=1, source_sha256=SOURCE_SHA, preserved_base_files=len(before),
                      base_terrain_sha256=before['terrain.json'], art=art,
                      runtime_image='battle-choi-r1.png', rights='local-only-original-derived-art')
    (args.out/'battle-choi-provenance-r1.json').write_text(json.dumps(provenance, indent=2)+'\n')
    assert all(sha(args.out/name) == digest for name, digest in before.items())
    assert len(list(args.out.iterdir())) == len(before)+4
    print(f'保留 {len(before)} 檔，新增一張原圖、四方向清單、來源與提示；共 {len(before)+4} 檔。')


if __name__ == '__main__':
    main()
