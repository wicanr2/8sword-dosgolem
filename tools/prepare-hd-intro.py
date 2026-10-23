#!/usr/bin/env python3
"""在 Docker 匯入 Noto 片頭標題；規格 011，保留基底素材 byte。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct

from PIL import Image, ImageDraw, ImageFont, __version__ as pillow_version

SOURCE_SHA = "ff31a0a4916ee1b27a56f2f7da32ec06df3716b42f831b547ed5518586f64060"
DECODED_SHA = "5f62f595ac003c069acace22770cd71b99e14d48bdd43db671598f5320c74f65"
FONT_SHA = "3cffb10242b4b7e6edd439ebf3bd7e392345525e093ea08149e0a0158a1b5151"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def decode(data):
    if len(data) < 8:
        raise ValueError("壓縮表頭遭截斷")
    size, root = struct.unpack_from("<HH", data)
    if not 256 <= root <= 511 or not 0 < size <= 65535:
        raise ValueError("壓縮表頭越界")
    count = root - 255
    stream_at = 4 + count * 4
    if stream_at >= len(data):
        raise ValueError("壓縮樹遭截斷")
    nodes = [struct.unpack_from("<HH", data, 4 + i * 4) for i in range(count)]
    for i, children in enumerate(nodes):
        if any(child >= 256 + i for child in children):
            raise ValueError("壓縮樹循環或前向引用")
    out = bytearray()
    node = root
    for value in data[stream_at:]:
        for bit in range(8):
            node = nodes[node - 256][0 if value & (1 << bit) else 1]
            if node < 256:
                out.append(node)
                node = root
                if len(out) == size:
                    return bytes(out)
    raise ValueError("壓縮位元流遭截斷")


def main():
    parser = argparse.ArgumentParser()
    for name in ("base", "source", "font", "notice", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    assert args.out.is_dir() and args.out.stat().st_uid == 1000
    assert not any(args.out.iterdir()), "拒絕覆寫素材組"
    assert args.base.is_dir() and (args.base / "font.json").is_file()
    source = args.source.read_bytes()
    assert sha(source) == SOURCE_SHA, "TIT2 來源不符"
    native = decode(source)
    assert len(native) == 28124 and sha(native) == DECODED_SHA
    assert struct.unpack_from("<HH", native) == (74, 95)
    assert sha(args.font.read_bytes()) == FONT_SHA
    assert pillow_version == "11.3.0", "字型工具版本不符"
    notice = args.notice.read_bytes()
    assert b"SIL OPEN FONT LICENSE" in notice
    before = {str(p.relative_to(args.base)): sha(p.read_bytes())
              for p in args.base.rglob("*") if p.is_file()}
    assert "intro.json" not in before, "基底已含片頭，需先審查"
    font = ImageFont.truetype(str(args.font), 420, index=3)
    im = Image.new("RGBA", (1776, 570))
    ImageDraw.Draw(im).text((888, 285), "神州八劍", font=font,
                           anchor="mm", fill=(245, 207, 113, 255))
    ink = im.getbbox()
    assert ink and 24 <= ink[0] < ink[2] <= 1752 and 24 <= ink[1] < ink[3] <= 546
    shutil.copytree(args.base, args.out, dirs_exist_ok=True)
    png = args.out / "intro-title-noto-r1.png"
    im.save(png)
    (args.out / "intro-Noto-NOTICE.txt").write_bytes(notice)
    manifest = dict(schema=1, source_sha256=SOURCE_SHA, decoded_sha256=DECODED_SHA,
                    font_sha256=FONT_SHA, family="Noto Sans CJK TC", weight=900,
                    text="神州八劍", file=png.name, sha256=sha(png.read_bytes()),
                    width=1776, height=570, ink_rect=list(ink),
                    rights="local-only original-title mapping; Noto SIL OFL 1.1")
    (args.out / "intro.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    provenance = dict(source_name=args.source.name, source_sha256=SOURCE_SHA,
                      decoded_sha256=DECODED_SHA, font_sha256=FONT_SHA, font_index=3,
                      font_size=420, anchor="mm", color=[245, 207, 113, 255],
                      pillow=pillow_version, base_files=before,
                      manifest_sha256=sha((args.out / "intro.json").read_bytes()),
                      font_notice_sha256=sha(notice),
                      rights=manifest["rights"])
    (args.out / "intro-import.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n")
    assert all(sha((args.out / name).read_bytes()) == digest for name, digest in before.items())
    assert all(p.stat().st_uid == 1000 for p in args.out.rglob("*"))
    print(json.dumps(dict(preserved_files=len(before), ink_rect=ink,
                         manifest_sha256=provenance["manifest_sha256"])))


if __name__ == "__main__":
    main()
