#!/usr/bin/env python3
"""044：保留 r41，匯入透明寶箱及獨立草地合成快取。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

from PIL import Image

IMAGE_SHA = "cbdafc80d3bc9b137d2ba10f6f1d76d0e4cdb8cf8e5cf24abe4768af6ebaae85"
PMAP_SHA = "9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02"
STYLE_SHA = "2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6"
NATIVE_SHA = "fbc25f989bb092e80bd2970605e5e27e1639dc907e857c8a03f3c9a06a04c2f6"
RECORD_SHA = "58a024b3400338bfc12ffba0f8bc5d49c53343ed73ada2a0c41e2a2b19bcb781"
CACHE_SHA = "549d61ae37b4cdf0c4e9f6b0fa70c29322a145621e408716fe91b10bfd422919"
FIRST_PROMPT_SHA = "d1e2fa1357f4ddd2d9061991505ac2c1cd060ccf6e364095e43080abb8659289"
PROMPT_SHA = "c2c248649962026acc18aa11dc0777f463d487ba6767118b4d8cdb2e55fcb1a5"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("base", "original", "image", "prompt", "first-prompt", "out", "cache-out"):
        parser.add_argument("--"+name, type=Path, required=True)
    a = parser.parse_args()
    assert not a.out.exists() and not a.cache_out.exists()
    assert a.base.is_dir() and a.original.is_dir()
    assert sha(a.image) == IMAGE_SHA and sha(a.prompt) == PROMPT_SHA and sha(a.first_prompt) == FIRST_PROMPT_SHA
    raw = (a.original/"PMAP.AY").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PMAP_SHA
    record = raw[58*1004:59*1004]
    assert hashlib.sha256(record).hexdigest() == RECORD_SHA and hashlib.sha256(record[:804]).hexdigest() == NATIVE_SHA
    image = Image.open(a.image)
    assert image.format == "PNG" and image.size == (1419, 1108) and image.mode == "RGBA"
    assert image.getchannel("A").getextrema() == (0,255)
    base = {p.name:sha(p) for p in a.base.iterdir() if p.is_file()}
    assert len(base) == len(list(a.base.iterdir())) == 188
    spec = importlib.util.spec_from_file_location("chest_sampling", Path(__file__).with_name("audit-encounter-gui.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    model = module.Model(a.base,a.original,a.cache_out)
    tile = module.sample(a.image,192,150,actor=True,background=model.material(1)[0])
    assert hashlib.sha256(tile).hexdigest() == CACHE_SHA
    manifest = dict(schema=1,source_file="PMAP.AY",source_sha256=PMAP_SHA,style_reference_sha256=STYLE_SHA,
                    source_index=58,native_sha256=NATIVE_SHA,record_sha256=RECORD_SHA,cache_sha256=CACHE_SHA,
                    grass_source=0,sampling="bilinear-full-alpha-over-grass",
                    image=dict(file="map-chest-r2.png",sha256=IMAGE_SHA,width=1419,height=1108))
    provenance = dict(schema=1,tool="built-in image_gen",image_sha256=IMAGE_SHA,
                      first_prompt_sha256=FIRST_PROMPT_SHA,edit_prompt_sha256=PROMPT_SHA,
                      source_sha256=PMAP_SHA,style_reference_sha256=STYLE_SHA,cache_sha256=CACHE_SHA,
                      rights="local-only original-derived; no public distribution grant",
                      approval="existing B style; no individual image approval claimed",base_sha256=base)
    a.out.mkdir()
    a.cache_out.mkdir()
    for name in base:
        shutil.copyfile(a.base/name,a.out/name)
    for src,name in [(a.image,"map-chest-r2.png"),(a.prompt,"map-chest-r2.prompt.txt"),(a.first_prompt,"map-chest-r1.prompt.txt")]:
        shutil.copyfile(src,a.out/name)
    for name,value in [("map-chest.json",manifest),("map-chest-provenance.json",provenance)]:
        (a.out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n")
    (a.cache_out/"chest-58.rgba").write_bytes(tile)
    assert len(list(a.out.iterdir())) == 193 and all(sha(a.out/name)==digest for name,digest in base.items())
    print(json.dumps(dict(files=193,base_files_preserved=188,independent_caches=1)))


if __name__ == "__main__":
    main()
