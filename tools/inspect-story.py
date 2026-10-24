#!/usr/bin/env python3
"""規格 012：獨立重建每個故事 Draw，逐像素核對無損收據。在 Docker 執行。"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct

from PIL import Image


def sha(b):
    return hashlib.sha256(b).hexdigest()


def inspect(runtime, assets, background, receipt):
    raw = runtime.read_bytes()
    assert sha(raw) == "a764a110b9f8b1d32a6ee9cc0dd650350f917959d647fe4b45cd7f1013eaae68"
    table = raw[0xb3f2-0x1100:0xb3f2-0x1100+1924]
    manifest = json.loads((assets/"story.json").read_text())
    atlas_raw = (assets/"story-font.png").read_bytes()
    assert sha(atlas_raw) == manifest["atlas_sha256"]
    atlas = Image.open(assets/"story-font.png").getchannel("A")
    glyphs = {g["big5"]: g for g in manifest["glyphs"] if g["source_index"] >= 0}
    bg = Image.open(background).convert("RGBA")
    assert bg.size == (640, 200) and set(bg.getdata()) == {(0, 0, 0, 255), (0, 0, 170, 255)}
    bg = bg.resize((1920, 1200), Image.Resampling.NEAREST)
    art_manifest = assets/"story-background.json"
    if art_manifest.exists():
        art = json.loads(art_manifest.read_text())
        assert art["approved_sha256"] == "bd21a34613dabef939afc9b94c9f45473cef2cd5f0e42aeee660d3d02b6d5c04"
        art_png = (assets/art["image"]).read_bytes()
        if sha(art_png) == art["image_sha256"]:
            bg = Image.open(assets/art["image"]).convert("RGBA")
            assert bg.size == (1920,1200) and bg.getchannel("A").getextrema() == (255,255)
    metadata = [json.loads(s) for s in (receipt/"intro-draw.jsonl").read_text().splitlines()]
    masks = {}
    choices = {}
    needed = {m.get("font_id", "noto") for m in metadata if m["stage"] in ("story-noto", "story-transition")}
    if (assets/"font-choices.json").exists():
        for profile in json.loads((assets/"font-choices.json").read_text())["profiles"]:
            if profile["id"] not in needed:
                continue
            assert sha((assets/profile["atlas"]).read_bytes()) == profile["atlas_sha256"]
            choices[profile["id"]] = (Image.open(assets/profile["atlas"]).getchannel("A"),
                                      {g["character"]: g for g in profile["glyphs"]})

    def expected(calls, page, font_id="noto"):
        assert 1 <= page <= 5 and (page-1)*192 <= calls <= min(page*192, 888)
        out = bg.copy()
        for i in range((page-1)*192, calls):
            c, r = divmod(i, 12)
            pair = table[c*26+r*2:c*26+r*2+2]
            if pair in (b"  ", b"\0\0"):
                continue
            code = pair.hex()
            key = font_id, code
            if key not in masks:
                g = glyphs[code]
                selected_atlas = atlas
                if font_id != "noto":
                    selected_atlas, selected_glyphs = choices[font_id]
                    g = selected_glyphs[g["character"]]
                x, y, iw, ih = g["ink"]
                dw, dh = min(iw, 48), min(ih, 90)
                assert dw > 0 and dh > 0
                source = selected_atlas.crop((x, y, x+iw, y+ih)).tobytes()
                mask = Image.frombytes("L", (dw, dh), bytes(
                    source[(y*ih//dh)*iw+x*iw//dw]
                    for y in range(dh) for x in range(dw)))
                masks[key] = mask
            mask = masks[key]
            x = (75-c%16*5)*8*3+(48-mask.width)//2
            y = (4+r*16)*6+(90-mask.height)//2
            rect = (x, y, x+mask.width, y+mask.height)
            out.paste(Image.composite(Image.new("RGBA", mask.size, (245, 207, 113, 255)),
                                      out.crop(rect), mask), (x, y))
        return out

    frames, matched, pages = 0, 0, {}
    with gzip.open(receipt/"presentation.frames.gz", "rb") as stream:
        def read(n):
            b = stream.read(n)
            assert len(b) == n, "收據遭截斷"
            return b
        assert read(8) == b"8SFRM001"
        width, height = struct.unpack("<II", read(8))
        assert (width, height) in ((1920, 1200), (2944,1264))
        ox,oy=(512,64) if width==2944 else (0,0)
        rgba = bytearray(width*height*4)
        while header := stream.read(24):
            ordinal, step, rows = struct.unpack("<QQQ", header)
            frames += 1
            assert ordinal == frames and rows <= height
            seen = set()
            for _ in range(rows):
                y, = struct.unpack("<H", read(2))
                assert y < height and y not in seen
                seen.add(y)
                rgba[y*width*4:(y+1)*width*4] = read(width*4)
            info = metadata[ordinal-1]
            assert info["draw"] == ordinal and info["step"] == step
            if info["stage"] not in ("story-noto", "story-transition"):
                continue
            calls, page = info["story_calls"], info["story_pages"]
            im = expected(calls, page, info.get("font_id", "noto"))
            central=b''.join(rgba[((y+oy)*width+ox)*4:((y+oy)*width+ox+1920)*4] for y in range(1200))
            if im.tobytes() != central:
                im.save(receipt/"story-expected-failed.png")
                Image.frombytes("RGBA", (1920, 1200), central).save(receipt/"story-actual-failed.png")
                raise ValueError(f"故事逐像素不符：draw={ordinal}, calls={calls}, page={page}")
            matched += 1
            pages.setdefault(str(page), []).append(calls)
    final = json.loads((receipt/"gui-final.json").read_text())
    assert frames == len(metadata) == final["recorded_frames"] and matched > 0 and final["closed"]
    result = dict(status="passed-independent-story-pixels", frames=frames, story_draws=matched,
                  pages={p: dict(draws=len(v), first_calls=min(v), last_calls=max(v)) for p, v in pages.items()},
                  method="independent Python/Pillow composition from original table, active font atlas and verified native or approved HD background; every recorded story Draw equals RGBA byte for byte",
                  recording_sha256=sha((receipt/"presentation.frames.gz").read_bytes()),
                  limit="只涵蓋實際錄製的故事 Draw；實際視窗、玩法、存檔與客體隔離另驗。")
    (receipt/"story-pixel-audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for key in ("runtime", "assets", "background"):
        parser.add_argument("--"+key, type=Path, required=True)
    parser.add_argument("receipts", type=Path, nargs="+")
    args = parser.parse_args()
    for receipt in args.receipts:
        inspect(args.runtime, args.assets, args.background, receipt)
