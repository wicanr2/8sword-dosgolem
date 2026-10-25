#!/usr/bin/env python3
"""045：保留 r42，匯入透明地圖物件55及獨立草地合成快取。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

from PIL import Image

IMAGE_SHA = "55e20818bf365b1d892ecce5ec2bf7eadaffba952635f890cc94c0bf2a107cdc"
PMAP_SHA = "9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02"
STYLE_SHA = "2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6"
NATIVE_SHA = "6f7b459688d11fa5249790a6802f677bc7e38a228d4c380d4b472c40b37e3f87"
RECORD_SHA = "18f01693acca18d6f4254c7f3a14bf1d7e9bff0fa4bca45d5c288a1432d94069"
CACHE_SHA = "2a4f23af0710c6e95ed002000f79dc612d312d74346f00452d5c0e4c0b4f322a"
PROMPT_SHA = "1b29570c9866f783596586c94b7fe82faea266aa4dd38ca3c82df193d887be40"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("base", "original", "image", "prompt", "out", "cache-out"):
        parser.add_argument("--"+name, type=Path, required=True)
    a = parser.parse_args()
    assert not a.out.exists() and not a.cache_out.exists()
    assert a.base.is_dir() and a.original.is_dir()
    assert sha(a.image) == IMAGE_SHA and sha(a.prompt) == PROMPT_SHA
    raw = (a.original/"PMAP.AY").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PMAP_SHA
    record = raw[55*1004:56*1004]
    assert hashlib.sha256(record).hexdigest() == RECORD_SHA and hashlib.sha256(record[:804]).hexdigest() == NATIVE_SHA
    image = Image.open(a.image)
    assert image.format == "PNG" and image.size == (1419, 1108) and image.mode == "RGBA"
    assert image.getchannel("A").getextrema() == (0,255)
    base = {p.name:sha(p) for p in a.base.iterdir() if p.is_file()}
    assert len(base) == len(list(a.base.iterdir())) == 193
    spec = importlib.util.spec_from_file_location("landmark55_sampling", Path(__file__).with_name("audit-encounter-gui.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    model = module.Model(a.base,a.original,a.cache_out)
    tile = module.sample(a.image,192,150,actor=True,background=model.material(1)[0])
    assert hashlib.sha256(tile).hexdigest() == CACHE_SHA
    manifest = dict(schema=1,source_file="PMAP.AY",source_sha256=PMAP_SHA,style_reference_sha256=STYLE_SHA,
                    source_index=55,native_sha256=NATIVE_SHA,record_sha256=RECORD_SHA,cache_sha256=CACHE_SHA,
                    grass_source=0,sampling="bilinear-full-alpha-over-grass",
                    image=dict(file="map-landmark-55-r1.png",sha256=IMAGE_SHA,width=1419,height=1108))
    provenance = dict(schema=1,tool="built-in image_gen",image_sha256=IMAGE_SHA,
                      prompt_sha256=PROMPT_SHA,
                      generation_style_sha256="744a39bb04c869803c0583604ac3c5c0481e174ad3153c4a8489f1219ad50a97",
                      source_sha256=PMAP_SHA,style_reference_sha256=STYLE_SHA,cache_sha256=CACHE_SHA,
                      rights="local-only original-derived; no public distribution grant",
                      approval="existing B style; no individual image approval claimed",base_sha256=base)
    a.out.mkdir()
    a.cache_out.mkdir()
    for name in base:
        shutil.copyfile(a.base/name,a.out/name)
    for src,name in [(a.image,"map-landmark-55-r1.png"),(a.prompt,"map-landmark-55-r1.prompt.txt")]:
        shutil.copyfile(src,a.out/name)
    for name,value in [("map-landmark-55.json",manifest),("map-landmark-55-provenance.json",provenance)]:
        (a.out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n")
    (a.cache_out/"landmark-55.rgba").write_bytes(tile)
    assert len(list(a.out.iterdir())) == 197 and all(sha(a.out/name)==digest for name,digest in base.items())
    print(json.dumps(dict(files=197,base_files_preserved=193,independent_caches=1)))


if __name__ == "__main__":
    main()
