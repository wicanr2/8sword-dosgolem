#!/usr/bin/env python3
"""033：從固定原圖建立女主角呈現圖，原版與原始生成 PNG 維持唯讀。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
from PIL import Image,__version__

ART='f060f488db011379ec80e82e48f2112309baf639fe1179f81cd822e95310a186'
SOURCES={'TIT3.AY':'31b943254292a75df2ad9d0c54eaeff7eacae83fb0f411bae4cfa4e66dd1bdec','TIT4.AY':'d12b77ead60f2a85033c89a99b8e444473f143413647735196f75685e24de14d','TIT5.AY':'b4114a8c64d949cba71321adc9979270ce001250845eb685badea9ad77c06d9e'}
DECODED='1ad430667a6d06969e1e71e1fa0b1f57453e65865488bbaa3416f86027e8924b'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser()
    for n in ['base','orig','art','prompt','out']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();assert __version__=='11.3.0' and a.out.is_dir() and a.out.stat().st_uid==os.getuid() and not list(a.out.iterdir())
    assert sha(a.art)==ART and sha(a.prompt)=='e685ce62fe116483a7daf6800881db95b2f86edcc726ec619c84e2090650be3c'
    for n,h in SOURCES.items():assert sha(a.orig/n)==h
    im=Image.open(a.art);assert im.size==(1825,862) and im.mode=='RGB';before={f.name:sha(f) for f in a.base.iterdir()};assert 'intro-heroine.json' not in before
    for f in a.base.iterdir():assert f.is_file() and not f.is_symlink();shutil.copyfile(f,a.out/f.name)
    im.resize((1272,600),Image.Resampling.LANCZOS).save(a.out/'intro-heroine.png')
    assert sha(a.out/'intro-heroine.png')=='9a9775fcf7c58ac5c60e8b8e1774858c6527d580801d5d04920b4c419f0b09f8'
    manifest=dict(schema=1,source_sha256=SOURCES['TIT5.AY'],decoded_sha256=DECODED,art_sha256=ART,file='intro-heroine.png',sha256=sha(a.out/'intro-heroine.png'),width=1272,height=600)
    (a.out/'intro-heroine.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (a.out/'intro-heroine-import.json').write_text(json.dumps(dict(base_files=before,packed_sources=SOURCES,art_sha256=ART,prompt_sha256=sha(a.prompt),pillow=__version__,resample='Lanczos, original physical aspect',native_rect=[112,20,536,120],hd_rect=[336,120,1608,720],rights='Local-only original-derived artwork; original generated PNG retained'),indent=2)+'\n')
    assert all(sha(a.out/n)==h for n,h in before.items());print(json.dumps(manifest))
if __name__=='__main__':main()
