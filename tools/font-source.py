#!/usr/bin/env python3
"""依規格 002 解析固定 PAM 字碼與字模，對原版收據核對並製作 Noto 字集。"""
import argparse
import hashlib
import json
import struct
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, __version__, features

PAM_SHA = "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"
NOTO_SHA = "3cffb10242b4b7e6edd439ebf3bd7e392345525e093ea08149e0a0158a1b5151"
MENU = ["檢視主角", "檢閱軍隊", "解雇軍隊", "使用法術", "查看地圖", "搜尋物品", "存取遊戲"]


def digest(data):
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class Glyph:
    index: int
    character: str
    big5: bytes
    file_offset: int
    bitmap: bytes


def parse(data):
    if digest(data) != PAM_SHA:
        raise ValueError("PAM.AY 雜湊不符，未知版本或截斷來源不能套用本規格")
    length = struct.unpack_from("<H", data, 0x2463C)[0]
    if length != 1272:
        raise ValueError("Big5 對照表長度不符")
    codes = data[0x2463E:0x2463E + length]
    text = codes.decode("big5", errors="strict")
    pairs = [codes[i:i + 2] for i in range(0, length, 2)]
    if len(text) != 636 or len(set(text)) != 636 or len(set(pairs)) != 636:
        raise ValueError("Big5 原始字碼數量或唯一性不符")
    result = []
    for index, char in enumerate(text):
        offset = 0xAE00 + index * 30
        bitmap = data[offset:offset + 30]
        code = codes[index * 2:index * 2 + 2]
        if len(bitmap) != 30 or len(code) != 2 or code.decode("big5") != char:
            raise ValueError(f"字模／字碼不完整：{index}")
        result.append(Glyph(index, char, code, offset, bitmap))
    if b"".join(g.big5 for g in result) != codes:
        raise ValueError("原始 Big5 字碼重組不符")
    return result


def original_menu_check(glyphs, reference):
    im = Image.open(reference).convert("RGB")
    if im.size != (640, 200):
        raise ValueError("原版收據必須為原生 640×200")
    by_character = {g.character: g for g in glyphs}
    checks = []
    for row, text in enumerate(MENU):
        for col, char in enumerate(text):
            x, y = 488 + col * 32, 12 + row * 27
            packed = bytearray()
            for yy in range(y, y + 15):
                bits = 0
                for xx in range(x, x + 16):
                    r, g, b = im.getpixel((xx, yy))
                    bits = (bits << 1) | int(r > 150 and g > 150 and b < 150)
                packed.extend(bits.to_bytes(2, "big"))
            glyph = by_character[char]
            if bytes(packed) != glyph.bitmap:
                raise ValueError(f"原版字模不符：第 {row + 1} 列 {char}")
            checks.append({"character": char, "index": glyph.index,
                           "file_offset": glyph.file_offset, "native_rect": [x, y, 16, 15],
                           "changed_bits": 0})
    return checks


def make_atlases(glyphs, font):
    native = Image.new("RGBA", (32 * 40, 20 * 40), (0, 0, 0, 0))
    hd = Image.new("RGBA", (32 * 64, 20 * 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(hd)
    missing = font.getmask("\U0010ffff")
    missing_key = (missing.size, bytes(missing))
    bounds = []
    for glyph in glyphs:
        column, row = glyph.index % 32, glyph.index // 32
        for y in range(15):
            bits = int.from_bytes(glyph.bitmap[y * 2:y * 2 + 2], "big")
            for x in range(16):
                if bits >> (15 - x) & 1:
                    # 2 倍原生點陣，透明背景，不套用顯示比例。
                    for dy in range(2):
                        for dx in range(2):
                            native.putpixel((column * 40 + 4 + x * 2 + dx,
                                             row * 40 + 5 + y * 2 + dy), (255, 241, 181, 255))
        mask = font.getmask(glyph.character)
        if not mask.getbbox() or (mask.size, bytes(mask)) == missing_key:
            raise ValueError(f"Noto 字模缺字或空白：{glyph.character}")
        box = draw.textbbox((0, 0), glyph.character, font=font)
        width, height = box[2] - box[0], box[3] - box[1]
        if width > 56 or height > 56:
            raise ValueError(f"Noto 字模超出製作格：{glyph.character}")
        x = column * 64 + (64 - width) // 2 - box[0]
        y = row * 64 + (64 - height) // 2 - box[1]
        draw.text((x, y), glyph.character, font=font, fill=(255, 241, 181, 255))
        ink = draw.textbbox((x, y), glyph.character, font=font)
        if not (column * 64 + 4 <= ink[0] <= ink[2] <= (column + 1) * 64 - 4
                and row * 64 + 4 <= ink[1] <= ink[3] <= (row + 1) * 64 - 4):
            raise ValueError(f"Noto 字模超出安全矩形：{glyph.character}")
        bounds.append({"index": glyph.index, "atlas_rect": [column * 64, row * 64, 64, 64],
                       "ink_rect": ink})
    return native, hd, bounds


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    outputs = [args.out / name for name in ["glyph-catalog.json", "native-font-atlas.png",
                                           "noto-black900-atlas.png", "font-source-checks.json"]]
    if not args.out.is_dir() or any(p.exists() for p in outputs):
        parser.error("輸出目錄必須存在，且四份目標檔案不能已存在")
    data = args.exe.read_bytes()
    glyphs = parse(data)
    checks = original_menu_check(glyphs, args.reference)
    if digest(args.font.read_bytes()) != NOTO_SHA:
        raise ValueError("Noto 字型來源雜湊不符")
    font = ImageFont.truetype(str(args.font), size=48, index=3)
    if font.getname() != ("Noto Sans CJK TC", "Black"):
        raise ValueError("Noto 字面不符")
    native, hd, bounds = make_atlases(glyphs, font)
    # 錯版及截斷檔必須被拒絕，不能以相同副檔名繼續。
    rejected = []
    for name, bad in [("truncated", data[:-1]), ("modified", bytes([data[0] ^ 1]) + data[1:])]:
        try:
            parse(bad)
        except ValueError:
            rejected.append(name)
        else:
            raise AssertionError(f"未拒絕錯誤來源：{name}")
    catalog = {"input": args.exe.name, "input_sha256": PAM_SHA,
               "glyph_geometry": [16, 15], "glyph_stride": 30, "count": len(glyphs),
               "address_space": "original PAM.AY file offsets, not IDA/runtime addresses",
               "glyphs": [{"index": g.index, "character": g.character, "big5": g.big5.hex(),
                           "file_offset": g.file_offset, "bitmap_sha256": digest(g.bitmap)} for g in glyphs]}
    outputs[0].write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")
    native.save(outputs[1])
    hd.save(outputs[2])
    receipt = {"status": "passed", "scope": "PAM font catalog and 28 native menu glyphs; no runtime HD overlay",
               "input_sha256": PAM_SHA, "reference_sha256": digest(args.reference.read_bytes()),
               "pillow": __version__, "freetype": features.version("freetype2"),
               "font_sha256": NOTO_SHA, "font_collection_index": 3, "font_family_style": font.getname(),
               "atlas_cell_px": [64, 64], "atlas_font_px": 48,
               "game_font_size_approved": False, "glyph_count": len(glyphs), "missing_glyphs": 0,
               "native_menu_checks": checks, "rejected_sources": rejected, "atlas_bounds": bounds,
               "unicode_reencoding_differences": [{"index": g.index, "character": g.character,
                    "source_big5": g.big5.hex(), "python_big5": g.character.encode("big5").hex()}
                    for g in glyphs if g.big5 != g.character.encode("big5")],
               "outputs_sha256": {p.name: digest(p.read_bytes()) for p in outputs[:3]}}
    outputs[3].write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": "passed", "glyph_count": len(glyphs), "native_glyph_matches": len(checks),
                      "missing_glyphs": 0, "outputs_sha256": receipt["outputs_sha256"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
