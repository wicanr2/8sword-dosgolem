#!/usr/bin/env python3
"""037：匯入地圖遭遇第 13 筆手繪圖，保留原 PNG bytes。Docker only。"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image, __version__

SOURCE = "0d18b068e177b54f7b8a2b30072e9ae3ebc984fbed9fd6a8706f71d3140a5ffd"
ART = "81f72e1ad3e1363c38c49eed75fcd906302a74818f21845e073310026954e146"
PROMPT = "9b5cbabeeab94c5eb542b4a4e775aceb3148ecfef29265b681e022361d16360d"
STYLE = "2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ["base", "source", "refs", "out"]:
        ap.add_argument("--" + name, required=True, type=Path)
    a = ap.parse_args()
    assert __version__ == "11.3.0" and not a.out.exists()
    assert a.out.parent.is_dir() and a.out.parent.stat().st_uid == 1000
    assert len(a.source.read_bytes()) == 16856 and sha(a.source) == SOURCE
    preserved = {p.name: sha(p) for p in a.base.iterdir() if p.is_file()}
    assert len(preserved) == 173 and not (a.base / "map-encounter.json").exists()
    assert all(p.is_file() and not p.is_symlink() for p in a.base.iterdir())
    terrain = json.loads((a.base / "terrain.json").read_text())
    assert terrain["style"] == "B-bright-painted-r1" and terrain["style_reference_sha256"] == STYLE
    art, prompt = a.refs / "encounter-13-art-r1.png", a.refs / "encounter-13-art-r1.prompt.txt"
    assert sha(art) == ART and sha(prompt) == PROMPT
    with Image.open(art) as im:
        assert im.format == "PNG" and im.mode == "RGBA" and im.size == (1419, 1108)
        assert im.getchannel("A").getextrema() == (0, 255)
        assert im.getchannel("A").point(lambda a: 255 if a > 3 else 0).getbbox() == (11, 72, 1408, 1078)
    manifest = dict(schema=1, source="ENEMY.AY", source_sha256=SOURCE, record=13,
                    transform="mirror-six-planes", style=terrain["style"], style_reference_sha256=STYLE,
                    image=dict(source_index=115, file="map-encounter-13-r1.png", sha256=ART,
                               width=1419, height=1108, sampling="bitmap", source_rect=[11, 72, 1408, 1078]),
                    target_rect=[3, 30, 189, 150], prompt_file="map-encounter-13-r1.prompt.txt", prompt_sha256=PROMPT,
                    rights="local-only original-derived; no public distribution grant")
    a.out.mkdir()
    for name in preserved:
        shutil.copyfile(a.base / name, a.out / name)
    shutil.copyfile(art, a.out / manifest["image"]["file"])
    shutil.copyfile(prompt, a.out / manifest["prompt_file"])
    (a.out / "map-encounter.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    provenance = dict(spec="037", source=manifest, file_offset=15652, preserved_files=preserved,
                      original_png_bytes_preserved=True, tool="Pillow " + __version__,
                      approval_basis="existing B style and established costume; no individual PNG selection",
                      rights=manifest["rights"])
    (a.out / "map-encounter-source.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n")
    assert len(list(a.out.iterdir())) == 177
    assert all(sha(a.out / name) == digest for name, digest in preserved.items())
    assert all(p.stat().st_uid == 1000 for p in a.out.iterdir())
    print("177 files; all 173 base files preserved; record 13 encounter group")


if __name__ == "__main__":
    main()
