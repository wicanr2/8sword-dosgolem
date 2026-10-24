#!/usr/bin/env python3
"""017：匯入選定的 A 博物館群組，保留既有素材與 033 女主角原圖。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

from PIL import Image, __version__

CANDIDATE_SHA = "88dbda67e6c1b4d3d0f1ce2a17b5695c97813e3ed6c7e2996cf33e716a3af09c"
PORTRAIT_SHA = "9a9775fcf7c58ac5c60e8b8e1774858c6527d580801d5d04920b4c419f0b09f8"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def regular(path, limit):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise ValueError(f"不是容量限制內的一般檔案：{path.name}")
    return path.read_bytes()


def clean_cache(path, item):
    with Image.open(path) as image:
        if image.format != "PNG" or image.size != (item["width"], item["height"]):
            raise ValueError("圖片形狀不符")
        if getattr(image, "n_frames", 1) != 1:
            raise ValueError("不接受動畫 PNG")
        pixels = image.convert("RGBA").tobytes()
    alpha = pixels[3::4]
    if item["cache_policy"] == "opaque":
        if min(alpha) != 255:
            raise ValueError("背景或近景不是完全不透明")
        return pixels
    if item["cache_policy"] != "floor8-largest8" or min(alpha) != 0 or max(alpha) != 255:
        raise ValueError("透明快取規則不符")
    width, height = item["width"], item["height"]
    visited = bytearray(width * height)
    components = []
    for start, value in enumerate(alpha):
        if value < 8 or visited[start]:
            continue
        visited[start] = 1
        queue = [start]
        for current in queue:
            x, y = current % width, current // width
            for yy in range(max(0, y - 1), min(height, y + 2)):
                for xx in range(max(0, x - 1), min(width, x + 2)):
                    neighbor = yy * width + xx
                    if not visited[neighbor] and alpha[neighbor] >= 8:
                        visited[neighbor] = 1
                        queue.append(neighbor)
        components.append(queue)
    components.sort(key=len, reverse=True)
    if not components or (len(components) > 1 and len(components[0]) == len(components[1])):
        raise ValueError("透明圖沒有唯一主體")
    result = bytearray(len(pixels))
    for index in components[0]:
        result[index * 4:index * 4 + 4] = pixels[index * 4:index * 4 + 4]
    if (sum(alpha) - sum(result[3::4])) * 500 > sum(alpha):
        raise ValueError("透明雜點移除超過 0.2%")
    return bytes(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["base", "candidate", "orig", "out"]:
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if __version__ != "11.3.0":
        raise ValueError("需要固定 Pillow 11.3.0")
    if not args.out.is_dir() or args.out.stat().st_uid != os.getuid() or list(args.out.iterdir()):
        raise ValueError("輸出須為目前使用者擁有的空目錄")
    raw = regular(args.candidate / "museum.json", 65536)
    if digest(raw) != CANDIDATE_SHA:
        raise ValueError("不是已審查的 A-r8 候選清單")
    manifest = json.loads(raw)
    if manifest["palette"] != "a-purple" or len(manifest["assets"]) != 14 or len(manifest["records"]) != 15:
        raise ValueError("群組不完整")
    for name, expected in manifest["packed_sources"].items():
        if Path(name).name != name or digest(regular(args.orig / name, 128 * 1024)) != expected:
            raise ValueError("原版來源不符")
    if digest(regular(args.base / "intro-heroine.png", 8 * 1024 * 1024)) != PORTRAIT_SHA:
        raise ValueError("基底沒有 033 的原女主角圖片")
    base = {}
    for file in args.base.iterdir():
        base[file.name] = digest(regular(file, 64 * 1024 * 1024))
    if "museum.json" in base:
        raise ValueError("基底已包含博物館群組")
    staged = []
    for item in manifest["assets"]:
        name = item["file"]
        if Path(name).name != name:
            raise ValueError("圖片檔名不符")
        source = args.candidate / name
        if digest(regular(source, 8 * 1024 * 1024)) != item["png_sha256"]:
            raise ValueError("圖片 SHA 不符")
        if digest(clean_cache(source, item)) != item["cache_sha256"]:
            raise ValueError("獨立透明快取不符")
        item["file"] = "intro-heroine.png" if item["id"] == "portrait" else "museum-" + item["id"] + ".png"
        if item["id"] != "portrait" and item["file"] in base:
            raise ValueError("圖片會覆寫基底")
        staged.append((source, item["file"]))
    if sum(item["width"] * item["height"] for item in manifest["assets"]) != 3902400:
        raise ValueError("群組解碼容量不符")
    # All source and image checks finish before the output receives any file.
    for name in base:
        shutil.copyfile(args.base / name, args.out / name)
    for source, name in staged:
        if name != "intro-heroine.png":
            shutil.copyfile(source, args.out / name)
    manifest["status"] = "spec-017-selected-A-runtime-group"
    (args.out / "museum.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    record = {"base_files": base, "candidate_sha256": CANDIDATE_SHA,
              "portrait_sha256": PORTRAIT_SHA, "group_images": 14, "source_records": 15,
              "cache_policy": "floor8-largest8", "pillow": __version__,
              "rights": "Local-only original-derived artwork; approved reference tracked separately"}
    (args.out / "museum-import.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    for name, expected in base.items():
        if digest((args.out / name).read_bytes()) != expected:
            raise ValueError("基底內容被更動")
    print(json.dumps({"base_files": len(base), "output_files": len(list(args.out.iterdir())),
                      "group_images": 14, "source_records": 15}))


if __name__ == "__main__":
    main()
