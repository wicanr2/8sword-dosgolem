#!/usr/bin/env python3
"""037：重生 README 的正常同狀態原版／HD 遭遇圖。Docker only。"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, __version__


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", type=Path, required=True)
    ap.add_argument("--font", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    assert not a.out.exists() and a.out.parent.is_dir()
    rel = Path("workplace/probe-20261023/graphics-first/battle-r1/encounter-normal-hd-r1")
    root = a.project / rel
    meta = json.loads((root / "06-west-frontier.json").read_text())
    assert meta["steps"] == 165382267 and meta["elapsed_ms"] == 57600
    assert meta["hd"] and not meta["map_encounter_error"] and not meta["graphics_error"]
    inputs = []
    images = []
    for mode in ["native", "hd"]:
        p = root / f"06-west-frontier-{mode}.png"
        image = Image.open(p).convert("RGB")
        assert image.size == (1920, 1200)
        images.append(image)
        inputs.append(dict(path=str(p.relative_to(a.project)), sha256=sha(p), mode=mode))
    font = ImageFont.truetype(str(a.font), 36, index=3)
    small = ImageFont.truetype(str(a.font), 24, index=3)
    out = Image.new("RGB", (1920, 720), "#11251f")
    draw = ImageDraw.Draw(out)
    for i, (label, image) in enumerate(zip(["原版", "HD"], images)):
        draw.text((i*960+24, 8), label, font=font, fill="#fff1b5")
        out.paste(image.resize((960, 600), Image.Resampling.NEAREST), (i*960, 64))
    draw.text((24, 675), "同一原版狀態，HD 僅改呈現。", font=small, fill="#fff1b5")
    a.out.mkdir()
    png = a.out / "map-encounter-original-hd-r1.png"
    out.save(png)
    record = dict(schema=1, spec="037", output=png.name, output_sha256=sha(png), inputs=inputs,
                  source_status=dict(path=str(rel / "06-west-frontier.json"), sha256=sha(root / "06-west-frontier.json")),
                  source_record=dict(file="ENEMY.AY", record=13, file_offset=15652,
                                     sha256="0d18b068e177b54f7b8a2b30072e9ae3ebc984fbed9fd6a8706f71d3140a5ffd",
                                     transform="mirror-six-planes"),
                  step=meta["steps"], clock="pre-run 12:00, live 3000 cycles/ms", internal_rng_seed="unknown",
                  capture="native and HD in one normal-input probe shot, no guest advance between images",
                  layout="same 1920x1200 viewport on both sides, both resized to 960x600 with nearest-neighbor",
                  tool=dict(pillow=__version__, script_sha256=sha(Path(__file__)), font_sha256=sha(a.font), font_index=3),
                  approval_basis="user requested original-versus-HD monster and battlefield overviews in README",
                  rights="requested comparison in existing private repository only; original-derived; no public distribution grant; full original and HD packs stay local")
    (a.out / "map-encounter-original-hd-r1.json").write_text(json.dumps(record, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(dict(output=str(png), sha256=record["output_sha256"])))


if __name__ == "__main__":
    main()
