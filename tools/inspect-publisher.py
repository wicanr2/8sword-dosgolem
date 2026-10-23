#!/usr/bin/env python3
"""在 Docker 獨立核對發行商逐幀字墨、圖標與故障回退。"""
import argparse
import gzip
import hashlib
import json
import struct
from pathlib import Path

from PIL import Image


def expected_images(native_path, assets):
    native = Image.open(native_path).convert("RGBA").resize((1920, 1200), Image.Resampling.NEAREST)
    mask = Image.open(assets / "publisher-erase.png").convert("L")
    assert hashlib.sha256(mask.tobytes()).hexdigest() == "7c6f7c1719915f4ddee9ac2d03938e42654c45777a3236c58b1ee3ea89a90985"
    mask = mask.resize(native.size, Image.Resampling.NEAREST)
    clean = native.copy()
    clean.paste((0, 0, 0, 255), (0, 0), mask)
    result = {}
    manifest = json.loads((assets / "publisher.json").read_text())
    for profile in manifest["words"]:
        path = assets / profile["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == profile["sha"]
        words = Image.open(path).convert("RGBA")
        # Go image/draw 的 16-bit 預乘與截位；獨立於遊戲合成程式。
        output = bytearray(clean.tobytes())
        for i, (r, g, b, a) in enumerate(words.getdata()):
            if not a:
                continue
            sa = a * 257
            inverse = (65535 - sa) * 257
            for c, source in enumerate((r, g, b)):
                output[i*4+c] = (output[i*4+c] * inverse // 65535 + source * sa // 255) >> 8
            output[i*4+3] = 255
        result[profile["id"]] = bytes(output)
    return native.tobytes(), result


def inspect(receipt, native, expected, fallback):
    metadata = [json.loads(line) for line in (receipt / "intro-draw.jsonl").read_text().splitlines()]
    black = bytes((0, 0, 0, 255)) * (1920*1200)
    held = set(expected.values()) | {black}
    matched, transitions, native_frames, fonts = 0, 0, [], {}
    frames = 0
    with gzip.open(receipt / "presentation.frames.gz", "rb") as stream:
        def read(n):
            b = stream.read(n)
            assert len(b) == n, "逐幀收據截斷"
            return b
        assert read(8) == b"8SFRM001" and struct.unpack("<II", read(8)) == (1920, 1200)
        rgba = bytearray(1920*1200*4)
        while header := stream.read(24):
            ordinal, step, rows = struct.unpack("<QQQ", header)
            frames += 1
            assert ordinal == frames and rows <= 1200
            seen = set()
            for _ in range(rows):
                y, = struct.unpack("<H", read(2))
                assert y < 1200 and y not in seen
                seen.add(y)
                rgba[y*1920*4:(y+1)*1920*4] = read(1920*4)
            info = metadata[ordinal-1]
            assert info["draw"] == ordinal and info["step"] == step
            if rgba == native:
                native_frames.append(ordinal)
            stage = info["stage"]
            if stage == "publisher-noto":
                assert not fallback
                font = info.get("font_id", "noto")
                if rgba != expected[font]:
                    Image.frombytes("RGBA", (1920, 1200), bytes(rgba)).save(receipt / "publisher-failed-actual.png")
                    Image.frombytes("RGBA", (1920, 1200), expected[font]).save(receipt / "publisher-failed-expected.png")
                    raise ValueError(f"發行商逐像素不符：Draw {ordinal}, {font}")
                matched += 1
                fonts[font] = fonts.get(font, 0)+1
            elif stage == "publisher-transition":
                assert not fallback and bytes(rgba) in held, f"轉場不是完整保留幀：{ordinal}"
                transitions += 1
    final = json.loads((receipt / "gui-final.json").read_text())
    assert final["closed"] and frames == len(metadata) == final["recorded_frames"]
    if fallback:
        assert native_frames and not matched and not transitions
        assert final["intro_publisher"]["load_error"] == "發行商字圖 publisher-caoshu.png SHA-256 不符"
    else:
        assert matched and not native_frames
        assert not final["intro_publisher"]["stats"]["Errors"]
        assert final["intro_publisher"]["stats"]["Timeouts"] == 0
    result = dict(status="passed-independent-publisher-frames", frames=frames, publisher_draws=matched,
                  transition_draws=transitions, fonts=fonts, native_publisher_frames=native_frames,
                  fallback=fallback, method="原版完整像素、二值清墨及選定字圖重建；全幅 RGBA 相同，包含未改的圖標",
                  limit="只涵蓋錄製 Draw；真正視窗截圖、原始來源與客體隔離另外核對。")
    (receipt / "publisher-pixel-audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--fallback", action="store_true")
    parser.add_argument("receipts", type=Path, nargs="+")
    args = parser.parse_args()
    original, expected = expected_images(args.native, args.assets)
    for receipt in args.receipts:
        inspect(receipt, original, expected, args.fallback)
