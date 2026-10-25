#!/usr/bin/env python3
"""043：以已驗實際 Draw 與同狀態原生色碼製作 README 比較圖。Docker only。"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("project", "gui", "font", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    assert not args.out.exists()
    assert args.project.is_dir()
    audit = json.loads((args.gui / "castle-draw-audit-r1.json").read_text())
    assert audit["actual_stream_link"] and audit["saved_loaded_ram_equal"]
    stem = args.gui / "save/research-castle-draws/font-noto-first-draw"
    path = lambda suffix: Path(str(stem) + suffix)
    meta = json.loads(path(".json").read_text())
    assert sha(path("-before.state")) == sha(path("-after.state"))
    native = path("-native.idx").read_bytes()
    assert len(native) == 128000 and max(native) < 16
    palette = meta["display"]["Palette"]
    original = Image.new("RGB", (640, 200))
    original.putdata([tuple(palette[pixel]) for pixel in native])
    original = original.resize((1920, 1200), Image.Resampling.NEAREST)
    hd = Image.open(path(".png")).convert("RGB")
    assert hd.size == (1920, 1200)
    actual = next(row for row in audit["phases"]["save"]["actual_draws"] if row["font_id"] == "noto")
    assert actual["rgba_sha256"] == hashlib.sha256(hd.convert("RGBA").tobytes()).hexdigest()
    initial_save = args.project / "workplace/probe-20261023/graphics-first/map-interaction-r1/castle-source-r1/scratch/gamedata.ay"
    initial_inspection = args.gui / "inspect-initial-r1"
    assert sha(initial_save) == sha(initial_inspection / "save-buffer-9e000.bin")
    assert json.loads((initial_inspection / "pages.json").read_text())["steps"] == meta["step"]
    font = ImageFont.truetype(str(args.font), 20, index=3)
    image = Image.new("RGB", (1920, 1216), (12, 33, 24))
    draw = ImageDraw.Draw(image)
    for col, source in enumerate((original, hd)):
        image.paste(source.resize((960, 600), Image.Resampling.LANCZOS), (col * 960, 28))
        draw.text((col * 960 + 12, 2), ("原版 DOS：dosgolem 原生色碼" if col == 0 else "HD：同一客體狀態的實際 Draw"), font=font, fill=(247, 228, 166))
        image.paste(source.crop((408, 348, 1008, 698)).resize((960, 560), Image.Resampling.NEAREST), (col * 960, 656))
        draw.text((col * 960 + 12, 630), ("原版城堡局部" if col == 0 else "HD 城堡局部：六圖塊完整銜接"), font=font, fill=(247, 228, 166))
    args.out.mkdir()
    output = args.out / "map-castle-original-hd-r1.png"
    image.save(output)
    record = dict(schema=1, scope="same-state native VGA and verified actual central Draw; castle six parts only",
                  image_sha256=sha(output), native_index_sha256=sha(path("-native.idx")),
                  actual_png_sha256=sha(path(".png")), actual_draw=meta["actual_draw"],
                  runtime_step=meta["step"], font_id=meta["font_id"],
                  state_sha256=sha(path("-before.state")), source_return_steps=meta["source_return_steps"],
                  production_build_inputs_sha256=sha(args.project / "workplace/player/build-castle-r1/build-inputs.sha256"),
                  gui_build_inputs_sha256=sha(args.gui / "save/build-inputs.sha256"),
                  display_palette=palette, clock="12:00:00.00 before execution; 3000 cycles/ms; normal PIT",
                  rng_seed="unknown; no seed changes or selection",
                  initial_save_sha256=sha(initial_save), resulting_save_sha256=audit["save_sha256"],
                  font_sha256=sha(args.font),
                  art_sha256="744a39bb04c869803c0583604ac3c5c0481e174ad3153c4a8489f1219ad50a97",
                  source="workplace/player/gui/castle-save-r1/save/research-castle-draws/font-noto-first-draw",
                  rights="requested comparison only in existing private repository; full art and original data remain local")
    output.with_suffix(".json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(output)


if __name__ == "__main__":
    main()
