#!/usr/bin/env python3
"""在 Docker 獨立核對發行商逐幀字墨、圖標與故障回退。"""
import argparse
import gzip
import hashlib
import json
import struct
from pathlib import Path

from PIL import Image


def over_rgba(clean, overlay):
    output = bytearray(clean)
    for i, (r, g, b, a) in enumerate(overlay.getdata()):
        if not a:
            continue
        sa = a * 257
        inverse = (65535 - sa) * 257
        for c, source in enumerate((r, g, b)):
            output[i*4+c] = (output[i*4+c] * inverse // 65535 + source * sa // 255) >> 8
        output[i*4+3] = 255
    return bytes(output)


def expected_images(native_path, assets, icon_fallback=False):
    native = Image.open(native_path).convert("RGBA").resize((1920, 1200), Image.Resampling.NEAREST)
    mask = Image.open(assets / "publisher-erase.png").convert("L")
    assert hashlib.sha256(mask.tobytes()).hexdigest() == "7c6f7c1719915f4ddee9ac2d03938e42654c45777a3236c58b1ee3ea89a90985"
    mask = mask.resize(native.size, Image.Resampling.NEAREST)
    clean = native.copy()
    clean.paste((0, 0, 0, 255), (0, 0), mask)
    icon_manifest = assets / "publisher-icon.json"
    canvas = clean.tobytes()
    if icon_manifest.exists() and not icon_fallback:
        icon = json.loads(icon_manifest.read_text())
        image_file, mask_file = assets / icon["image"], assets / icon["mask"]
        assert hashlib.sha256(image_file.read_bytes()).hexdigest() == icon["image_sha256"] == "21b9bb5de42c011434160cb208ff9a28354959a2d751e286c078a6b68699f2a0"
        assert hashlib.sha256(mask_file.read_bytes()).hexdigest() == icon["mask_sha256"]
        erase = Image.open(mask_file).convert("L")
        assert hashlib.sha256(erase.tobytes()).hexdigest() == "124dd022ac27ef2070195bf53baeb59915600317531766f5ae197ce6970c417d"
        clean.paste((0,0,0,255), (0,0), erase.resize(clean.size,Image.Resampling.NEAREST))
        canvas = over_rgba(clean.tobytes(),Image.open(image_file).convert("RGBA"))
    result = {}
    manifest = json.loads((assets / "publisher.json").read_text())
    for profile in manifest["words"]:
        path = assets / profile["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == profile["sha"]
        words = Image.open(path).convert("RGBA")
        # Go image/draw 的 16-bit 預乘與截位；獨立於遊戲合成程式。
        result[profile["id"]] = over_rgba(canvas,words)
    return native.tobytes(), result


def inspect(receipt, native, expected, fallback, icon_fallback=False, headless=False):
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
        assert read(8) == b"8SFRM001"
        width,height = struct.unpack("<II", read(8))
        assert (width,height) in [(1920,1200),(2944,1264)]
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
            actual = bytes(rgba) if width==1920 else Image.frombytes("RGBA",(width,height),bytes(rgba)).crop((512,64,2432,1264)).tobytes()
            if actual == native:
                native_frames.append(ordinal)
            stage = info["stage"]
            if stage == "publisher-noto":
                assert not fallback
                font = info.get("font_id", "noto")
                if actual != expected[font]:
                    Image.frombytes("RGBA", (1920, 1200), actual).save(receipt / "publisher-failed-actual.png")
                    Image.frombytes("RGBA", (1920, 1200), expected[font]).save(receipt / "publisher-failed-expected.png")
                    raise ValueError(f"發行商逐像素不符：Draw {ordinal}, {font}")
                matched += 1
                if font not in fonts:
                    Image.frombytes("RGBA", (1920,1200), actual).save(receipt / ("publisher-"+font+"-actual-draw.png"))
                    if width!=1920:
                        Image.frombytes("RGBA", (width,height), bytes(rgba)).save(receipt / ("publisher-"+font+"-wide-actual-draw.png"))
                fonts[font] = fonts.get(font, 0)+1
            elif stage == "publisher-transition":
                assert not fallback and actual in held, f"轉場不是完整保留幀：{ordinal}"
                transitions += 1
    final = json.loads((receipt / "gui-final.json").read_text())
    assert (final["frame_pure_count"] == frames if headless else final["closed"])
    assert frames == len(metadata) == final["recorded_frames"]
    if fallback:
        assert native_frames and not matched and not transitions
        assert final["intro_publisher"]["load_error"] == "發行商字圖 publisher-caoshu.png SHA-256 不符"
    else:
        assert matched and not native_frames
        assert not final["intro_publisher"]["stats"]["Errors"]
        assert final["intro_publisher"]["stats"]["Timeouts"] == 0
        if icon_fallback:
            assert final["intro_publisher"]["icon"] == {"loaded":False,"load_error":"發行商圖案 publisher-icon.png SHA-256 不符"}
        elif "icon" in final["intro_publisher"]:
            assert final["intro_publisher"]["icon"]["load_error"] == ""
    result = dict(status="passed-independent-publisher-frames", frames=frames, publisher_draws=matched,
                  transition_draws=transitions, fonts=fonts, native_publisher_frames=native_frames,
                  fallback=fallback, icon_fallback=icon_fallback, headless=headless,
                  method="原版完整像素、二值清墨及選定字圖、可選定稿圖案重建；獨立 16-bit 合成，全幅 RGBA 相同",
                  limit="只涵蓋錄製 Draw；真正視窗截圖、原始來源與客體隔離另外核對。")
    (receipt / "publisher-pixel-audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--fallback", action="store_true")
    parser.add_argument("--icon-fallback", action="store_true")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("receipts", type=Path, nargs="+")
    args = parser.parse_args()
    original, expected = expected_images(args.native, args.assets, args.icon_fallback)
    for receipt in args.receipts:
        inspect(receipt, original, expected, args.fallback, args.icon_fallback, args.headless)
