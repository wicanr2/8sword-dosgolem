#!/usr/bin/env python3
"""盤點 ENEMY.AY，核對 019 正常遭遇的鏡射記錄與逐平面前綴。

在固定 Pillow Docker 中執行；用法與範圍見 037 規格。
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from PIL import Image, ImageDraw, __version__

SOURCE_SHA = "0d18b068e177b54f7b8a2b30072e9ae3ebc984fbed9fd6a8706f71d3140a5ffd"
PALETTE = [(0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170),
           (170, 0, 0), (170, 0, 170), (170, 85, 0), (170, 170, 170),
           (85, 85, 85), (85, 85, 255), (85, 255, 85), (85, 255, 255),
           (255, 85, 85), (255, 85, 255), (255, 255, 85), (255, 255, 255)]
REVERSE = bytes(int(f"{v:08b}"[::-1], 2) for v in range(256))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def mirror(raw):
    assert len(raw) == 1204 and struct.unpack_from("<HH", raw) == (8, 25)
    return raw[:4] + b"".join(bytes(REVERSE[v] for v in raw[a:a + 8][::-1])
                              for a in range(4, 1204, 8))


def prefix(raw, height):
    assert 1 <= height <= 25
    return struct.pack("<HH", 8, height) + b"".join(
        raw[4 + p * 200:4 + p * 200 + height * 8] for p in range(6))


def decode(raw):
    width, height = struct.unpack_from("<HH", raw)
    assert width == 8 and len(raw) == 4 + 6 * width * height
    area = width * height
    out = Image.new("RGBA", (width * 8, height))
    for y in range(height):
        for x in range(width * 8):
            a, bit = y * width + x // 8, 7 - x % 8
            opaque = (raw[4 + 5 * area + a] >> bit) & 1
            if opaque:
                color = sum(((raw[4 + p * area + a] >> bit) & 1) << p for p in range(4))
                out.putpixel((x, y), PALETTE[color] + (255,))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--normal", type=Path, required=True, help="019 source-r5")
    ap.add_argument("--out", type=Path, required=True, help="必須尚不存在")
    a = ap.parse_args()
    if a.out.exists():
        ap.error("輸出已存在")
    source = a.source.read_bytes()
    assert sha(source) == SOURCE_SHA and len(source) == 14 * 1204
    receipt = json.loads((a.normal / "receipt.json").read_text())
    calls = [r for r in receipt["sources"] if r["planes"] == 6 and r["width_bytes"] == 8]
    assert [r["height"] for r in calls] == list(range(1, 26, 2))
    full = mirror(source[12040:13244])
    matches = []
    for c in calls:
        raw = (a.normal / c["file"]).read_bytes()
        expected = prefix(full, c["height"])
        assert raw == expected and sha(raw) == c["record_sha256"]
        assert sha(raw[:4 + 4 * 8 * c["height"]]) == c["native_sha256"]
        assert c["y"] + c["height"] == 112
        matches.append(dict(height=c["height"], y=c["y"], x_byte=c["x_byte"],
                            record_sha256=sha(raw), native_sha256=c["native_sha256"],
                            calls=c["calls"], step=c["step"], source_file=c["file"]))
    a.out.mkdir()
    records = []
    sheet = Image.new("RGB", (4 * 240, 4 * 205), "#293b39")
    for record in range(14):
        raw = source[record * 1204:(record + 1) * 1204]
        im = decode(raw)
        mirrored = mirror(raw)
        assert mirror(mirrored) == raw
        assert decode(mirrored).tobytes() == im.transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()
        corrected = im.resize((192, 150), Image.Resampling.NEAREST)
        corrected.save(a.out / f"enemy-{record:02d}-native.png")
        decode(mirrored).resize((192, 150), Image.Resampling.NEAREST).save(a.out / f"enemy-{record:02d}-mirror-native.png")
        if record == 13:
            decode(mirrored).resize((768, 600), Image.Resampling.NEAREST).save(a.out / "enemy-13-mirror-reference.png")
            (a.out / "enemy-13-mirror.bin").write_bytes(mirrored)
        sheet.paste(corrected, ((record % 4) * 240 + 24, (record // 4) * 205 + 35), corrected)
        ImageDraw.Draw(sheet).text(((record % 4) * 240 + 12, (record // 4) * 205 + 10),
                                  f"ENEMY.AY record {record}", fill="white")
        records.append(dict(record=record, file_offset=record * 1204, bytes=1204,
                            raw_sha256=sha(raw), mirrored_sha256=sha(mirrored),
                            opaque_bbox=im.getbbox(), opaque_pixels=im.getchannel("A").histogram()[255],
                            mirrored_opaque_bbox=decode(mirrored).getbbox(),
                            normal_coverage="mirrored full and 12 prefixes" if record == 10 else "not established here",
                            role="unknown"))
    decode(full).resize((192, 150), Image.Resampling.NEAREST).save(a.out / "enemy-10-mirror-native.png")
    (a.out / "enemy-10-mirror.bin").write_bytes(full)
    sheet.save(a.out / "native-catalog.png")
    result = dict(schema=1, evidence_level="proven bytes, shape, decoding and existing normal source correspondence; roles unknown",
                  source=dict(file=a.source.name, bytes=len(source), sha256=sha(source)),
                  address_space="original file offsets; normal call addresses are DOS runtime segment offsets",
                  tool=dict(pillow=__version__, script_sha256=sha(Path(__file__).read_bytes())),
                  normal_receipt_sha256=sha((a.normal / "receipt.json").read_bytes()),
                  records=records, normal_record_10_prefixes=matches,
                  rights="local-only original-derived; no public distribution grant")
    (a.out / "catalog.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(dict(records=len(records), matched_prefixes=len(matches),
                          mirrored_bbox=decode(full).getbbox(), out=str(a.out))))


if __name__ == "__main__":
    main()
