#!/usr/bin/env python3
"""046：從固定原圖匯入可選攻城背景；Docker only。"""
import argparse
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

from PIL import Image

SOURCE = "4e5c5c6569cc6fc9f1e585b7048c099228f787da041d46ded685e034b7594103"
NATIVE = "79e2c0119edf4ca9f87fb14dbee47de49afca4eee8f8cc2711c4c58c275e7be9"
IMAGE = "521a7a99e37cd437b6cf54835002df42dde1ef29c9bc551af0a1bfaec10230f6"
PROMPT = "f73b3fa8f3a9349f7e6a3809fc40d15fedea77ed5f5478f8d10978e98e8175f8"
CACHE = "ee95cca6642a98ed4bdcb14415e19553d6efbb558b4fbf375ca2ba119abd9955"


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("base", "original", "art", "out", "cache-out"):
        parser.add_argument("--" + name, type=Path, required=True)
    a = parser.parse_args()
    assert a.base.is_dir() and not a.out.exists() and not a.cache_out.exists()
    assert not (a.base / "battle-palace-background.json").exists()
    source = a.original / "GRO01.EG"
    image = a.art / "gro01-painted-r1.png"
    prompt = a.art / "gro01-painted-r1.prompt.txt"
    assert sha(source) == SOURCE and sha(image) == IMAGE and sha(prompt) == PROMPT
    spec = importlib.util.spec_from_file_location("palace_decode", Path(__file__).with_name("prepare-hd-intro.py"))
    decoder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(decoder)
    decoded = decoder.decode(source.read_bytes())
    assert len(decoded) == 64004 and hashlib.sha256(decoded).hexdigest() == NATIVE
    im = Image.open(image)
    assert im.format == "PNG" and im.mode == "RGB" and im.size == (1586, 992)
    spec = importlib.util.spec_from_file_location("palace_sample", Path(__file__).with_name("audit-encounter-gui.py"))
    sampling = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sampling)
    cache = sampling.sample(image, 1920, 1200)
    assert hashlib.sha256(cache).hexdigest() == CACHE
    preserved = {}
    for path in sorted(a.base.iterdir()):
        assert path.is_file() and not path.is_symlink()
        preserved[path.name] = sha(path)
    a.out.mkdir()
    a.cache_out.mkdir()
    for name in preserved:
        shutil.copyfile(a.base / name, a.out / name)
    shutil.copyfile(image, a.out / "battle-palace-background-r1.png")
    shutil.copyfile(prompt, a.out / "battle-palace-background-prompt.txt")
    manifest = dict(schema=1, source_file="GRO01.EG", source_sha256=SOURCE, native_sha256=NATIVE,
                    pam_sha256="83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0",
                    style="B-bright-painted-r1", style_reference_sha256="2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6", cache_sha256=CACHE,
                    image=dict(source_index=150, file="battle-palace-background-r1.png", sha256=IMAGE, width=1586, height=992, sampling="bitmap"))
    (a.out / "battle-palace-background.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    provenance = dict(spec="046", source_file="GRO01.EG", source_sha256=SOURCE, native_sha256=NATIVE,
                      image_sha256=IMAGE, prompt_sha256=PROMPT, cache_sha256=CACHE,
                      tool="built-in image_gen; independent Python sampling", original_png_bytes_preserved=True,
                      rights="local-only derivative; no public redistribution grant", preserved_files=preserved)
    (a.out / "battle-palace-background-source.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n")
    (a.cache_out / "palace-background.rgba").write_bytes(cache)
    assert len(list(a.out.iterdir())) == len(preserved) + 4
    assert all(sha(a.out / name) == digest for name, digest in preserved.items())
    print(json.dumps(dict(files=len(preserved) + 4, preserved=len(preserved), cache_sha256=CACHE)))


if __name__ == "__main__":
    main()
