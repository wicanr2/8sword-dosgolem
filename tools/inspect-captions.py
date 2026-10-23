#!/usr/bin/env python3
"""在 Docker 獨立重建博物館字幕帶，核對每個 Draw 並偵測原字露出。"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct

from PIL import Image


def inspect(runtime, assets, receipt):
    raw = runtime.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == "a764a110b9f8b1d32a6ee9cc0dd650350f917959d647fe4b45cd7f1013eaae68"
    table = raw[0xb352-0x1100:0xb352-0x1100+160]
    manifest = json.loads((assets/"story.json").read_text())
    atlas_raw = (assets/"story-font.png").read_bytes()
    assert hashlib.sha256(atlas_raw).hexdigest() == manifest["atlas_sha256"]
    atlas = Image.open(assets/"story-font.png").getchannel("A")
    glyphs = {g["big5"]: g for g in manifest["glyphs"] if g["source_index"] >= 0}
    expected = {}
    for source in (0x42, 0x6a, 0x92, 0xba):
        b = table[source-0x42:source-0x42+40].split(b"\0")[0]
        im = Image.new("RGBA", (1920, 90), (0, 0, 0, 255))
        i = 0
        while i < len(b):
            if b[i] == 32:
                i += 1
                continue
            g = glyphs[b[i:i+2].hex()]
            x, y, iw, ih = g["ink"]
            dw, dh = min(iw, 48), min(ih, 90)
            alpha = atlas.crop((x, y, x+iw, y+ih)).tobytes()
            mask = Image.frombytes("L", (dw, dh), bytes(alpha[(y*ih//dh)*iw+x*iw//dw]
                                                       for y in range(dh) for x in range(dw)))
            color = Image.new("RGBA", mask.size, (0, 170, 170, 255))
            black = Image.new("RGBA", mask.size, (0, 0, 0, 255))
            im.paste(Image.composite(color, black, mask), (i*8*3+(48-dw)//2, (90-dh)//2))
            i += 2
        expected[source] = im.tobytes()
    metadata = [json.loads(l) for l in (receipt/"intro-draw.jsonl").read_text().splitlines()]
    matched, frames, seen, exposures = 0, 0, {}, []
    with gzip.open(receipt/"presentation.frames.gz", "rb") as stream:
        def read(n):
            b = stream.read(n)
            assert len(b) == n
            return b
        assert read(8) == b"8SFRM001" and struct.unpack("<II", read(8)) == (1920, 1200)
        rgba = bytearray(1920*1200*4)
        while header := stream.read(24):
            ordinal, step, rows = struct.unpack("<QQQ", header)
            frames += 1
            assert ordinal == frames and rows <= 1200
            rowset = set()
            for _ in range(rows):
                y, = struct.unpack("<H", read(2))
                assert y < 1200 and y not in rowset
                rowset.add(y)
                rgba[y*1920*4:(y+1)*1920*4] = read(1920*4)
            info = metadata[ordinal-1]
            assert info["draw"] == ordinal and info["step"] == step
            band = rgba[960*1920*4:1050*1920*4]
            if info["stage"] == "captions-noto":
                source = info["caption_source"]
                assert source in expected
                if band != expected[source]:
                    Image.frombytes("RGBA", (1920, 90), bytes(band)).save(receipt/"captions-failed-actual.png")
                    Image.frombytes("RGBA", (1920, 90), expected[source]).save(receipt/"captions-failed-expected.png")
                    raise ValueError(f"字幕帶逐像素不符：draw={ordinal}, source={source:04x}")
                matched += 1
                seen[source] = seen.get(source, 0)+1
            else:
                colors = Image.frombytes("RGBA", (1920, 90), bytes(band)).getcolors(3)
                if colors and {c for n, c in colors} <= {(0, 0, 0, 255), (0, 170, 170, 255)}:
                    cyan = sum(n for n, c in colors if c == (0, 170, 170, 255))
                    if cyan > 100:
                        exposures.append(ordinal)
    final = json.loads((receipt/"gui-final.json").read_text())
    assert frames == len(metadata) == final["recorded_frames"] and final["closed"]
    assert matched > 0 and not exposures, exposures
    result = dict(status="passed-independent-caption-band", frames=frames, caption_draws=matched,
                  sources={f"{s:04x}": n for s, n in seen.items()}, native_caption_exposure_frames=exposures,
                  method="original bytes and Noto alpha independently reconstruct full 1920x90 band; exact RGBA comparison",
                  limit="涵蓋錄製的 Draw；字幕以外的美術、實際視窗與客體隔離另驗。")
    (receipt/"captions-pixel-audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("receipts", type=Path, nargs="+")
    a = parser.parse_args()
    for root in a.receipts:
        inspect(a.runtime, a.assets, root)
