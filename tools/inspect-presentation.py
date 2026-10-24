#!/usr/bin/env python3
"""在 Docker 內獨立解碼逐幀收據；不把格式正確當成視覺驗收。"""
import argparse
import gzip
import hashlib
import json
import struct
from pathlib import Path

from PIL import Image, ImageDraw


def inspect(root):
    final = json.loads((root / "gui-final.json").read_text())
    path = root / "presentation.frames.gz"
    frames, changed, hashes, thumbs = 0, 0, [], []
    sheets = []
    def sheet():
        if not thumbs:
            return
        out = Image.new("RGB", (1920, ((len(thumbs) + 5) // 6) * 224), "#171b20")
        draw = ImageDraw.Draw(out)
        for n, (im, label) in enumerate(thumbs):
            x, y = n % 6 * 320, n // 6 * 224
            out.paste(im, (x, y + 24))
            draw.text((x + 4, y + 4), label, fill="white")
        name = f"continuous-{len(sheets) + 1:02}.png"
        out.save(root / name)
        sheets.append(name)
        thumbs.clear()
    with gzip.open(path, "rb") as stream:
        def read(n):
            value = stream.read(n)
            if len(value) != n:
                raise ValueError("逐幀收據遭截斷")
            return value
        if read(8) != b"8SFRM001":
            raise ValueError("未知逐幀格式")
        width, height = struct.unpack("<II", read(8))
        if (width, height) not in ((1920, 1200), (2944, 1264)):
            raise ValueError("未知呈現尺寸")
        if (width, height) == (2944, 1264) and final.get('presentation_size') != [2944, 1264]:
            raise ValueError("工具列尺寸與前端收據不符")
        rgba = bytearray(width * height * 4)
        previous_step = 0
        while header := stream.read(24):
            if len(header) != 24:
                raise ValueError("幀標頭遭截斷")
            ordinal, step, rows = struct.unpack("<QQQ", header)
            if ordinal != frames + 1 or step < previous_step or rows > height:
                raise ValueError("幀序、步數或列數錯誤")
            if frames == 0 and rows != height:
                raise ValueError("首幀不完整")
            seen = set()
            for _ in range(rows):
                y, = struct.unpack("<H", read(2))
                if y >= height or y in seen:
                    raise ValueError("差分列越界或重複")
                seen.add(y)
                at = y * width * 4
                rgba[at:at + width * 4] = read(width * 4)
            frames += 1
            previous_step = step
            if frames > 20000:
                raise ValueError("收據超出有界抽樣範圍")
            if rows:
                changed += 1
                hashes.append({"frame": ordinal, "step": step, "changed_rows": rows,
                               "rgba_sha256": hashlib.sha256(rgba).hexdigest()})
                image = Image.frombytes("RGBA", (width, height), bytes(rgba)).convert("RGB")
                if (width, height) == (2944, 1264):
                    preview = Image.new('RGB', (320, 200), '#081817')
                    small = image.resize((320, round(320 * height / width)), Image.Resampling.LANCZOS)
                    preview.paste(small, (0, (200 - small.height) // 2))
                else:
                    preview = image.resize((320, 200), Image.Resampling.LANCZOS)
                thumbs.append((preview,
                               f"frame {ordinal} / step {step}"))
                if len(thumbs) == 60:
                    sheet()
        sheet()
    if frames != final["recorded_frames"] or not final["closed"]:
        raise ValueError("關閉收據與實際幀數不符")
    Image.frombytes("RGBA", (width, height), bytes(rgba)).save(root / "continuous-final.png")
    result = {"status": "lossless-stream-valid", "width": width, "height": height, "frames": frames, "changed_frames": changed,
              "recording_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "contact_sheets": sheets, "frame_hashes": hashes,
              "limit": "只證明逐幀完整性；字墨、轉場及殘字仍須檢視連續畫面。"}
    (root / "continuous-audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "frame_hashes"}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    inspect(parser.parse_args().root)
