#!/usr/bin/env python3
"""039：匯入第 7 筆粉紅角色，保留原 PNG；正式基底 r38，組合研究可用 r10 候選。"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image, __version__

SOURCE = "0d18b068e177b54f7b8a2b30072e9ae3ebc984fbed9fd6a8706f71d3140a5ffd"
ART = "b5f71a301064ed1d2a050588d400b0fe9113289e9baa2e5bb39c4e66def4e1b0"
PROMPT = "cef47c1fcc11ebc15810b596f720df9b8db25b12ef1a01162c25412e7cb2eb4e"
STYLE = "2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ["base", "source", "refs", "out"]:
        ap.add_argument("--"+name, type=Path, required=True)
    a = ap.parse_args()
    assert __version__ == "11.3.0" and not a.out.exists()
    assert a.out.parent.is_dir() and a.out.parent.stat().st_uid == 1000
    assert len(a.source.read_bytes()) == 16856 and sha(a.source) == SOURCE
    assert all(p.is_file() and not p.is_symlink() for p in a.base.iterdir())
    preserved = {p.name: sha(p) for p in a.base.iterdir()}
    assert len(preserved) in [177, 179] and "map-encounter-7.json" not in preserved
    assert ("map-encounter-10.json" in preserved) == (len(preserved) == 179)
    terrain = json.loads((a.base/"terrain.json").read_text())
    assert terrain["style"] == "B-bright-painted-r1" and terrain["style_reference_sha256"] == STYLE
    art, prompt = a.refs/"encounter-7-art-r2.png", a.refs/"encounter-7-art-r2.prompt.txt"
    assert sha(art) == ART and sha(prompt) == PROMPT
    with Image.open(art) as im:
        assert im.format == "PNG" and im.mode == "RGBA" and im.size == (1419, 1108)
        assert im.getchannel("A").getextrema() == (0, 255)
        assert im.getchannel("A").point(lambda a: 255 if a > 3 else 0).getbbox() == (62, 54, 1360, 1045)
    manifest = dict(schema=1, source="ENEMY.AY", source_sha256=SOURCE, record=7,
                    transform="mirror-six-planes", style=terrain["style"], style_reference_sha256=STYLE,
                    image=dict(source_index=138, file="map-encounter-7-r1.png", sha256=ART,
                               width=1419, height=1108, sampling="bitmap", source_rect=[62, 54, 1360, 1045]),
                    target_rect=[21, 18, 162, 150], prompt_file="map-encounter-7-r1.prompt.txt", prompt_sha256=PROMPT,
                    rights="local-only original-derived; no public distribution grant")
    a.out.mkdir()
    for name in preserved:
        shutil.copyfile(a.base/name, a.out/name)
    shutil.copyfile(art, a.out/manifest["image"]["file"])
    shutil.copyfile(prompt, a.out/manifest["prompt_file"])
    (a.out/"map-encounter-7.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n")
    history = []
    for version in [1, 2]:
        f = a.refs/f"encounter-7-art-r{version}.prompt.txt"
        history.append(dict(file=f.name, sha256=sha(f), prompt=f.read_text()))
    provenance = dict(spec="039", source=manifest, file_offset=8428, preserved_files=preserved,
                      original_png_bytes_preserved=True, generation_prompts=history,
                      generated_by="built-in image_gen", prefix_heights=list(range(5, 26, 2)),
                      approval_basis="existing approved B style; not individual PNG selection",
                      tool="Pillow "+__version__, rights=manifest["rights"])
    (a.out/"map-encounter-7-source.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2)+"\n")
    assert len(list(a.out.iterdir())) == len(preserved)+4
    assert all(sha(a.out/name) == digest for name, digest in preserved.items())
    assert all(p.stat().st_uid == 1000 for p in a.out.iterdir())
    print(f"{len(preserved)+4} files; all {len(preserved)} base files preserved; record 7 group")


if __name__ == "__main__":
    main()
