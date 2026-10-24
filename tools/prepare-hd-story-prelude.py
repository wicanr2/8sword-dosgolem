"""匯入 014 已批准的彩色前導；僅在鎖定 Pillow 容器中執行。"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from PIL import Image

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--base',type=Path,required=True)
    ap.add_argument('--candidate',type=Path,required=True)
    ap.add_argument('--orig',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    assert a.base.is_dir() and a.candidate.is_dir() and a.orig.is_dir()
    assert a.out.is_dir() and not any(a.out.iterdir())
    files=sorted(a.base.iterdir())
    assert len(files)==149 and all(p.is_file() and not p.is_symlink() for p in files)
    raw=a.candidate/'color-raw.png'; canvas=a.candidate/'color-canvas.png'
    assert digest(raw)=='12aed4841ed37026e91547dce49a4696fc3c20b511de5983dd4ed43c5a3340e8'
    assert digest(canvas)=='93879b591e694968c7b777a0b89bdc60f2e3965718ddd520491ebdb2b198eb7c'
    original=a.orig/'TIT6V.AY'
    assert original.is_file() and not original.is_symlink()
    assert digest(original)=='2131ac054ffd0df4c0f6edff23a393be2cf0416b72b6bb43eedc5d4d844b4212'
    im=Image.open(canvas).convert('RGBA')
    assert im.size==(1920,1200) and im.getchannel('A').getextrema()==(255,255)
    assert canvas.stat().st_size<=8*1024*1024
    before={p.name:digest(p) for p in files}
    for p in files: shutil.copyfile(p,a.out/p.name)
    shutil.copyfile(canvas,a.out/'story-prelude.png')
    manifest={'schema':1,'source_sha256':'9aadec77cf59adb1f444d47891526af7da888bebecc648a3fa16a6f0adcd6dfe','approved_sha256':digest(raw),'image':'story-prelude.png','image_sha256':digest(canvas),'width':1920,'height':1200,'rights':'local-only original-derived HD artwork; no public distribution permission'}
    (a.out/'story-prelude.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    receipt={'schema':1,'approved_option':'A 彩色手繪前導','method':'copy selected existing PNG; preserve original reveal order in host presentation','original_TIT6V_sha256':digest(original),'source_raw_sha256':digest(raw),'source_canvas_sha256':digest(canvas),'base_files_sha256':before,'rights':manifest['rights']}
    (a.out/'story-prelude-import.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    assert len(list(a.out.iterdir()))==152
    assert all(digest(a.out/n)==sha for n,sha in before.items())
    print('152 files; 149 base files unchanged; selected PNG copied without resampling')

if __name__=='__main__':main()
