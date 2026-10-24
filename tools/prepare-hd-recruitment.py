"""034：匯入已批准募兵城門；僅在 Docker 執行，原圖與基底 bytes 保持。"""
import argparse
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path
from PIL import Image, __version__

SOURCE = 'b854b04f3b0d3620adc37e3adb498cbe3ae710f007766695f40f4065ebde32eb'
NATIVE = 'edf6a0cc7dc13fbd054049bcb9bec91e1386c0c8b141174da376499854cb5978'
APPROVED = '7aa67f8975843e91e0a393863ba08bb77582fd4ab62ee10fad059bebcd5b61ab'
PROMPT = 'a5a7397084a136035ef0824c9636d6658250b196752f765190e666e39c16f02e'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('base', 'orig', 'approved', 'out'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    assert __version__ == '11.3.0'
    assert a.out.is_dir() and a.out.stat().st_uid == 1000 and not any(a.out.iterdir())
    assert sha(a.orig / 'LIVE2.AY') == SOURCE
    module_spec = importlib.util.spec_from_file_location('intro', Path(__file__).with_name('prepare-hd-intro.py'))
    intro = importlib.util.module_from_spec(module_spec); module_spec.loader.exec_module(intro)
    raw = intro.decode((a.orig / 'LIVE2.AY').read_bytes())
    assert len(raw) == 22404 and hashlib.sha256(raw).hexdigest() == NATIVE
    image = a.approved / 'recruitment-gate-approved-r1.png'
    prompt = a.approved / 'recruitment-gate-approved-r1.prompt.txt'
    assert sha(image) == APPROVED and sha(prompt) == PROMPT
    with Image.open(image) as im:
        assert im.format == 'PNG' and im.mode == 'RGB' and im.size == (1877, 838)
    before = {f.name: sha(f) for f in a.base.iterdir() if f.is_file()}
    assert len(before) == 158 and 'recruitment-building.json' not in before
    assert all(f.is_file() and not f.is_symlink() for f in a.base.iterdir())
    for name in before: shutil.copyfile(a.base / name, a.out / name)
    shutil.copyfile(image, a.out / 'recruitment-building-r1.png')
    shutil.copyfile(prompt, a.out / 'recruitment-building-r1.prompt.txt')
    m = dict(schema=1, source='LIVE2.AY', source_sha256=SOURCE, native_sha256=NATIVE,
             style='B-bright-painted-r1', style_reference_sha256='2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6',
             image=dict(source_index=111, file='recruitment-building-r1.png', sha256=APPROVED, width=1877, height=838, sampling='bitmap'),
             rights='local-only original-derived; approved private reference, no public distribution grant')
    (a.out / 'recruitment-building.json').write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n')
    (a.out / 'recruitment-building-import.json').write_text(json.dumps(dict(schema=1, spec='034',
        source_sha256=SOURCE, native_sha256=NATIVE, approved_sha256=APPROVED, prompt_sha256=PROMPT,
        preserved_files=before, original_png_bytes_preserved=True, pillow=__version__, rights=m['rights']), indent=2) + '\n')
    assert len(list(a.out.iterdir())) == 162 and all(sha(a.out/n) == h for n,h in before.items())
    assert all(f.stat().st_uid == 1000 for f in a.out.iterdir())
    print('162 files; 158 base files unchanged; approved PNG bytes preserved')

if __name__ == '__main__': main()
