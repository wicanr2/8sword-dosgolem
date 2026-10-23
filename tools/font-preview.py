#!/usr/bin/env python3
"""在 Docker 中製作真實 Noto 字型樣張；不改寫遊戲畫面或 DOS 狀態。"""
import argparse
import hashlib
import json
import platform
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, __version__, features


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fonts", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not args.out.is_dir():
        parser.error("輸出目錄必須預先建立")
    image_path = args.out / "noto-weight-comparison-r1.png"
    metadata_path = image_path.with_suffix(".json")
    if image_path.exists() or metadata_path.exists():
        parser.error("樣張已存在，先核對既有成果，不覆寫")

    variants = [("Bold", 700), ("Black", 900)]
    menu = ["檢視主角", "檢閱軍隊", "解雇軍隊", "使用法術", "查看地圖", "搜尋物品", "存取遊戲"]
    canvas = Image.new("RGB", (1440, 1130), "#101b21")
    draw = ImageDraw.Draw(canvas)
    bounds = []
    records = []

    def write(text, box, font, color="#fff1b5", center=False):
        left, top, right, bottom = box
        ink = draw.textbbox((0, 0), text, font=font)
        width, height = ink[2] - ink[0], ink[3] - ink[1]
        if width > right - left or height > bottom - top:
            raise ValueError(f"文字超出安全矩形：{text!r}")
        x = left + ((right - left - width) / 2 if center else 0) - ink[0]
        y = top + (bottom - top - height) / 2 - ink[1]
        draw.text((x, y), text, font=font, fill=color)
        actual = draw.textbbox((x, y), text, font=font)
        assert left <= actual[0] <= actual[2] <= right
        assert top <= actual[1] <= actual[3] <= bottom
        bounds.append({"text": text, "safe_rect": box, "ink_rect": actual})

    for column, (weight, number) in enumerate(variants):
        path = args.fonts / f"NotoSansCJK-{weight}.ttc"
        font = lambda size: ImageFont.truetype(str(path), size=size, index=3)
        assert font(32).getname() == ("Noto Sans CJK TC", weight)
        x = 40 + 710 * column
        write(f"Noto Sans CJK TC · {weight} {number}", (x, 25, x + 650, 72), font(28), "#e0d1a7")
        write("神州八劍", (x, 88, x + 650, 160), font(60))
        for row, label in enumerate(menu):
            y = 185 + row * 77
            draw.rounded_rectangle((x, y, x + 650, y + 67), radius=8, fill="#081014", outline="#87754a", width=2)
            write(label, (x + 20, y + 9, x + 630, y + 58), font(44), center=True)
        write("內文大小與標點測讀", (x, 752, x + 650, 790), font(28), "#a7c5ce")
        # 下列句子是排版測試文字，不冒充原版對白。
        write("此為排版測試，並非原版對白。", (x, 804, x + 650, 850), font(32))
        write("探索地圖、檢閱軍隊、使用法術。", (x, 860, x + 650, 906), font(32))
        write("等級 05　金錢 123456　確認？", (x, 916, x + 650, 962), font(32))
        records.append({"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "collection_index": 3, "family": "Noto Sans CJK TC", "style": weight,
                        "weight": number, "synthetic_bold": False})

    footer = ImageFont.truetype(str(args.fonts / "NotoSansCJK-Bold.ttc"), size=25, index=3)
    write("字重與排版樣張，尚未接入遊戲。色彩、字級與邊框僅供比較。", (40, 1000, 1400, 1050), footer, "#aec3c7")
    write("上方七項文字依原版地圖指令；下方為自製測試句。", (40, 1058, 1400, 1098), footer, "#aec3c7")
    canvas.save(image_path)
    receipt = {
        "status": "disposable-font-specimen-not-runtime", "python": platform.python_version(),
        "pillow": __version__, "freetype": features.version("freetype2"),
        "fonts": records, "sizes_px": {"heading": 60, "menu": 44, "body": 32},
        "image": image_path.name, "image_sha256": hashlib.sha256(image_path.read_bytes()).hexdigest(),
        "size": canvas.size, "all_text_within_safe_rectangles": True, "text_bounds": bounds,
    }
    metadata_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: receipt[k] for k in ["status", "image", "image_sha256", "all_text_within_safe_rectangles"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
