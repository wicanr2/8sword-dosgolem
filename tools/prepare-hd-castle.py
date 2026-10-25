#!/usr/bin/env python3
"""043：保留基底，匯入透明城堡全景，另存六份獨立驗證快取。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

from PIL import Image

IMAGE_SHA = "744a39bb04c869803c0583604ac3c5c0481e174ad3153c4a8489f1219ad50a97"
PMAP_SHA = "9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02"
STYLE_SHA = "2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6"
PROMPT_SHA = "c7f52f54dfe8c57bc8e805c4c0234d1a1c0a8878598dafc9bdf90afe0bff4adb"
FIRST_PROMPT_SHA = "e66a4c90116d5c56485c3b496e33a8218c6a7f38ff1ec7ddc690de3b978926ef"
CACHE_SHA = [
    "f559bcaa54ffb080ed1d049dd16fb652a41901394dddf63a5d53697ef9deabdf",
    "3912e71422f4e03357d145c657f614dafaab99064730349624abd258a8751822",
    "930f2493e01185914169e26c1ce12928cc70674f3aacc29e85832852031c9450",
    "bd490ec89fbe00c1856a5ddad1ad1ae76b359168d2383e9145ad6cc9a08141b5",
    "5f6236bce522acb5e0606e3fc1d06116bceb5cf24c2924038207e09dc06142a9",
    "610a7beecd74a656b566a45014a194dc321a93f63270dfb87f51d710d9ad1d10",
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("base", "original", "image", "prompt", "first-prompt", "out", "cache-out"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    assert not args.out.exists() and not args.cache_out.exists()
    assert args.base.is_dir() and args.original.is_dir()
    assert sha(args.image) == IMAGE_SHA
    assert sha(args.prompt) == PROMPT_SHA and sha(args.first_prompt) == FIRST_PROMPT_SHA
    raw = (args.original / "PMAP.AY").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PMAP_SHA
    image = Image.open(args.image)
    assert image.format == "PNG" and image.size == (1736, 906) and image.mode == "RGBA"
    assert image.getchannel("A").getextrema() == (0, 255)
    base = {p.name: sha(p) for p in args.base.iterdir() if p.is_file()}
    assert len(base) == 183 and len(list(args.base.iterdir())) == 183
    module_path = Path(__file__).with_name("audit-encounter-gui.py")
    spec = importlib.util.spec_from_file_location("castle_independent_sampling", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    model = module.Model(args.base, args.original, args.cache_out)
    grass = model.material(1)[0]
    background = b"".join(grass[(row % 150) * 768:(row % 150 + 1) * 768] * 3
                          for row in range(300))
    whole = module.sample(args.image, 576, 300, actor=True, background=background)
    records, caches = [], {}
    for i in range(6):
        index, x, y = 59 + i, i % 3 * 192, i // 3 * 150
        tile = b"".join(whole[((row + y) * 576 + x) * 4:
                              ((row + y) * 576 + x + 192) * 4]
                        for row in range(150))
        assert hashlib.sha256(tile).hexdigest() == CACHE_SHA[i]
        entry = raw[index * 1004:(index + 1) * 1004]
        records.append(dict(source_index=index, native_sha256=hashlib.sha256(entry[:804]).hexdigest(),
                            record_sha256=hashlib.sha256(entry).hexdigest(), cache_sha256=CACHE_SHA[i]))
        caches[f"castle-{index}.rgba"] = tile
    manifest = dict(schema=1, source_file="PMAP.AY", source_sha256=PMAP_SHA,
                    style_reference_sha256=STYLE_SHA, layout=[3, 2], grass_source=0,
                    sampling="bilinear-full-then-split", records=records,
                    image=dict(file="map-castle-r2.png", sha256=IMAGE_SHA, width=1736, height=906))
    provenance = dict(schema=1, tool="built-in image_gen", image_sha256=IMAGE_SHA,
                      first_prompt_sha256=FIRST_PROMPT_SHA, edit_prompt_sha256=PROMPT_SHA,
                      source_sha256=PMAP_SHA, style_reference_sha256=STYLE_SHA,
                      rights="local-only original-derived; no public distribution grant",
                      approval="existing B style; no individual image approval claimed",
                      cache_sha256=CACHE_SHA, base_sha256=base)
    args.out.mkdir()
    args.cache_out.mkdir()
    for name in base:
        shutil.copyfile(args.base / name, args.out / name)
    for source, name in ((args.image, "map-castle-r2.png"), (args.prompt, "map-castle-r2.prompt.txt"),
                         (args.first_prompt, "map-castle-r1.prompt.txt")):
        shutil.copyfile(source, args.out / name)
    for name, value in (("map-castle.json", manifest), ("map-castle-provenance.json", provenance)):
        (args.out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    for name, tile in caches.items():
        (args.cache_out / name).write_bytes(tile)
    assert len(list(args.out.iterdir())) == 188
    assert all(sha(args.out / name) == digest for name, digest in base.items())
    print(json.dumps(dict(files=188, base_files_preserved=183, independent_caches=6)))


if __name__ == "__main__":
    main()
