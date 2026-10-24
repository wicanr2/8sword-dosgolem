#!/usr/bin/env python3
"""038：共用既有 MAN16 PNG，匯入第 10 筆地圖遭遇清單。Docker only。"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image, __version__

SOURCE = "0d18b068e177b54f7b8a2b30072e9ae3ebc984fbed9fd6a8706f71d3140a5ffd"
ART = "53a599a6db8f10cf76d08de389fbf07b72b6f3c8f9fdf6647256c440809300ad"
PROMPT = "c319d1165e849f1177a537a05fdf32a74418998f83cf2b6f6f9f45340b6ddf62"
STYLE = "2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ["base", "source", "out"]:
        ap.add_argument("--" + name, required=True, type=Path)
    a = ap.parse_args()
    assert __version__ == "11.3.0" and not a.out.exists()
    assert a.out.parent.is_dir() and a.out.parent.stat().st_uid == 1000
    assert len(a.source.read_bytes()) == 16856 and sha(a.source) == SOURCE
    assert all(p.is_file() and not p.is_symlink() for p in a.base.iterdir())
    preserved = {p.name: sha(p) for p in a.base.iterdir()}
    assert len(preserved) == 177 and "map-encounter-10.json" not in preserved
    assert preserved["battle-man16-0-r1.png"] == ART
    assert preserved["battle-actors-prompts.txt"] == PROMPT
    terrain = json.loads((a.base / "terrain.json").read_text())
    assert terrain["style"] == "B-bright-painted-r1" and terrain["style_reference_sha256"] == STYLE
    with Image.open(a.base / "battle-man16-0-r1.png") as im:
        assert im.format == "PNG" and im.mode == "RGBA" and im.size == (1176, 1337)
        assert im.getchannel("A").getextrema() == (0, 255)
        assert im.getchannel("A").point(lambda a: 255 if a > 3 else 0).getbbox() == (123, 311, 1175, 1213)
    manifest = dict(schema=1, source="ENEMY.AY", source_sha256=SOURCE, record=10,
                    transform="mirror-six-planes", style=terrain["style"], style_reference_sha256=STYLE,
                    image=dict(source_index=125, file="battle-man16-0-r1.png", sha256=ART,
                               width=1176, height=1337, sampling="bitmap", source_rect=[123, 311, 1052, 902]),
                    target_rect=[0, 0, 192, 150], prompt_file="battle-actors-prompts.txt", prompt_sha256=PROMPT,
                    rights="local-only original-derived; no public distribution grant")
    a.out.mkdir()
    for name in preserved:
        shutil.copyfile(a.base / name, a.out / name)
    (a.out / "map-encounter-10.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    provenance = dict(spec="038", source=manifest, file_offset=12040, preserved_files=preserved,
                      original_png_bytes_preserved=True, image_reused_from="023 MAN16 record 0",
                      cache_transform="mirror-x-after-premultiplied-bilinear", prefix_heights=list(range(1, 26, 2)),
                      tool="Pillow " + __version__, rights=manifest["rights"])
    (a.out / "map-encounter-10-source.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n")
    assert len(list(a.out.iterdir())) == 179
    assert all(sha(a.out / name) == digest for name, digest in preserved.items())
    assert all(p.stat().st_uid == 1000 for p in a.out.iterdir())
    print("179 files; all 177 base files preserved; shared PNG; record 10 encounter group")


if __name__ == "__main__":
    main()
