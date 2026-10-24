#!/usr/bin/env python3
"""盤點 019 已遇 MAN 來源；只讀輸入，不賦予未驗證的動作名稱。

在 Pillow 11.3.0 專用 Docker 內執行，見 019 規格。
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

from PIL import Image, ImageDraw, __version__


SOURCES = {
    "MAN01.EGG": "a7e02cf495800fac19c293688043f3af6eb6deaec1a61a581ed3f9d5b8b3e5f1",
    "MAN06.EGG": "97be211dd9289538aaa46f01b2340bcac9ce0a7c8e44ed9d3c4e9abdac873579",
    "MAN11.EGG": "860ab98a7165f25fe2007dd597ddf6fc698c9d2f048701eec955a1a0cd65f832",
    "MAN16.EGG": "d4acf7c58c199c1776ffde6c86afa3c9b0ae3b132e4cc59973e1e0d5c2011d6a",
    "MAN21.EGG": "47cc484319abeba53551c20b7cf4b9b2c6061f2da3b6cda14155b3598f10982c",
}
PALETTE = [(0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170),
           (170, 0, 0), (170, 0, 170), (170, 85, 0), (170, 170, 170),
           (85, 85, 85), (85, 85, 255), (85, 255, 85), (85, 255, 255),
           (255, 85, 85), (255, 85, 255), (255, 255, 85), (255, 255, 255)]
REVERSE = bytes(int(f"{v:08b}"[::-1], 2) for v in range(256))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def mirror(raw):
    out = bytearray(raw[:4])
    for plane in range(6):
        for y in range(50):
            at = 4 + plane * 550 + y * 11
            out.extend(REVERSE[v] for v in raw[at:at + 11][::-1])
    return bytes(out)


def decode(raw):
    assert len(raw) == 3304 and struct.unpack_from("<HH", raw) == (11, 50)
    im = Image.new("RGBA", (88, 50))
    for y in range(50):
        for x in range(88):
            at, bit = y * 11 + x // 8, 7 - x % 8
            color = sum(((raw[4 + p * 550 + at] >> bit) & 1) << p for p in range(4))
            opaque = (raw[4 + 5 * 550 + at] >> bit) & 1
            im.putpixel((x, y), PALETTE[color] + (255 * opaque,))
    return im


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sources", type=Path, required=True)
    ap.add_argument("--calls", type=Path, help="既有正常視窗的 battle-observer/calls.json")
    ap.add_argument("--out", type=Path, required=True, help="必須尚不存在")
    a = ap.parse_args()
    if a.out.exists():
        ap.error("輸出已存在，請選新版本名稱")
    records, lookup, inputs = [], {}, []
    # 先驗完所有來源，避免留下看似完整的半份目錄。
    for name, expected in SOURCES.items():
        data = (a.sources / name).read_bytes()
        assert len(data) == 13216 and sha(data) == expected, name
        inputs.append(dict(file=name, sha256=expected, bytes=len(data)))
        for i in range(4):
            raw = data[i * 3304:(i + 1) * 3304]
            im = decode(raw)
            flipped = mirror(raw)
            assert mirror(flipped) == raw
            assert decode(flipped).tobytes() == im.transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()
            row = dict(file=name, record=i, file_offset=i * 3304, bytes=len(raw),
                       record_sha256=sha(raw), mirrored_sha256=sha(flipped),
                       native_width=88, native_height=50,
                       opaque_pixels=sum(px[3] == 255 for px in im.getdata()),
                       planes_sha256=[sha(raw[4 + p * 550:4 + (p + 1) * 550]) for p in range(6)],
                       action="unknown")
            records.append((row, im))
            for key, transform in [(sha(raw), "identity"), (sha(flipped), "mirror-six-planes")]:
                lookup.setdefault(key, []).append(dict(file=name, record=i, transform=transform))
    # CHOI 是獨立的圓形標記，不把同尺寸記錄誤列為部隊。
    marker = (a.sources / "CHOI.EGG").read_bytes()
    assert sha(marker) == "5504591888f306aee2fce04015a81fca30e4e6c8bd48897c5103abcece780bcb"
    marker_lookup = {sha(marker[i * 3304:(i + 1) * 3304]): i for i in range(4)}
    effect = (a.sources / "PON.EGG").read_bytes()
    assert sha(effect) == "5fe52b534cccbcaab5265681c42f208751f69da1144161541f161d93b89b786e"
    effect_lookup = {sha(effect[i * 3304:(i + 1) * 3304]): i for i in range(4)}
    calls, unmatched, excluded = [], Counter(), Counter()
    if a.calls:
        for c in json.loads(a.calls.read_text()):
            if (c["Width"], c["Height"]) != (11, 50) or not c.get("Raw"):
                continue
            raw = (a.calls.parent / c["Raw"]).read_bytes()
            if len(raw) == 4:
                excluded["header-only restoration"] += 1
                continue
            assert len(raw) == 3304, c["Raw"]
            if c.get("SHA256"):
                assert sha(raw) == c["SHA256"], c["Raw"]
            matches = lookup.get(sha(raw), [])
            marker_record = marker_lookup.get(sha(raw))
            effect_record = effect_lookup.get(sha(raw))
            calls.append(dict(serial=c["Serial"], entry=c["Entry"], step=c["Step"],
                              phase=c.get("Phase", "not supplied"),
                              record_sha256=sha(raw), matches=matches,
                              marker_record=marker_record, effect_record=effect_record))
            if not matches and marker_record is None and effect_record is None:
                unmatched[sha(raw)] += 1
    a.out.mkdir()
    sheet = Image.new("RGB", (1200, 1800), "#303b42")
    for n, (row, im) in enumerate(records):
        filename = f"{row['file']}-record-{row['record']}-native.png"
        corrected = im.resize((264, 300), Image.Resampling.NEAREST)
        corrected.save(a.out / filename)
        row["image"] = filename
        tile = Image.new("RGB", (300, 360), "#303b42")
        tile.paste(corrected, (18, 44), corrected)
        draw = ImageDraw.Draw(tile)
        draw.text((10, 8), f"{row['file']} record {row['record']}", fill="white")
        draw.text((10, 24), f"offset {row['file_offset']} / action unknown", fill="white")
        sheet.paste(tile, ((n % 4) * 300, (n // 4) * 360))
    sheet.save(a.out / "native-poses-contact.png")
    result = dict(schema=1, evidence_level="proven bytes and decoding; action semantics unknown",
                  address_space="original file offsets; calls use DOS runtime segment offsets",
                  tool=dict(pillow=__version__, script_sha256=sha(Path(__file__).read_bytes())),
                  inputs=inputs, records=[r for r, _ in records], calls=calls,
                  calls_source=dict(path=str(a.calls), sha256=sha(a.calls.read_bytes())) if a.calls else None,
                  marker_source=dict(file="CHOI.EGG", sha256=sha(marker)),
                  effect_source=dict(file="PON.EGG", sha256=sha(effect)),
                  unmatched=dict(unmatched), excluded=dict(excluded),
                  limitation="CHOI markers, PON effects and header-only restorations are separate; no action names or normal coverage inferred from archive order or input phase.")
    (a.out / "catalog.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(dict(records=len(records), matched_calls=sum(bool(c["matches"]) for c in calls),
                          unmatched_calls=sum(unmatched.values()), out=str(a.out))))


if __name__ == "__main__":
    main()
