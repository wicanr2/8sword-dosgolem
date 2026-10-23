#!/usr/bin/env python3
"""規格 012：從已核對的正常執行期來源建立 Noto 故事字集。只在 Docker 執行。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from PIL import Image, ImageDraw, ImageFont, __version__

RUNTIME_SHA = "a764a110b9f8b1d32a6ee9cc0dd650350f917959d647fe4b45cd7f1013eaae68"
EXE_SHA = "b9c7abdac7849711b68b6b6fd5861052e6f3d025b25af5f96d4605bf673cadaa"
CODE_SHA = "2cf9a571e729cf77de2dd739207b015c2ec14c940182edb087d41784bdcc9fc8"
INK_SHA = "a87a063a736aaf847e4014cb3ecb22a3d8782ee6d67fb2bec474c7d9ff84de63"
TABLE_SHA = "bf10ab412d18dc7d4f77ba2918e55aeefd3ab02b53aa40c34cd3fae6119ed7aa"
FONT_SHA = "3cffb10242b4b7e6edd439ebf3bd7e392345525e093ea08149e0a0158a1b5151"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ("base", "runtime", "exe", "font", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    a = parser.parse_args()
    assert a.out.is_dir() and a.out.stat().st_uid == 1000 and not any(a.out.iterdir())
    b = a.runtime.read_bytes()
    assert sha(b) == RUNTIME_SHA and sha(a.exe.read_bytes()) == EXE_SHA
    codes = b[0xbd0c-0x1100:0xbd0c-0x1100+706]
    ink = b[0x2316-0x1100:0x2316-0x1100+10590]
    table = b[0xb3f2-0x1100:0xb3f2-0x1100+1924]
    assert sha(codes) == CODE_SHA and sha(ink) == INK_SHA and sha(table) == TABLE_SHA
    characters = codes.decode("big5")
    assert len(characters) == len(set(characters)) == 353
    for row in range(74):
        assert table[row*26+24:row*26+26] == b"\0\0"
        for col in range(12):
            pair = table[row*26+col*2:row*26+col*2+2]
            assert pair in (b"  ", b"\0\0") or pair.decode("big5") in characters
    assert sha(a.font.read_bytes()) == FONT_SHA and __version__ == "11.3.0"
    font = ImageFont.truetype(str(a.font), 48, index=3)
    assert font.getname() == ("Noto Sans CJK TC", "Black")
    before = {str(p.relative_to(a.base)): sha(p.read_bytes())
              for p in a.base.rglob("*") if p.is_file()}
    assert "intro.json" in before and "story.json" not in before
    im = Image.new("RGBA", (1024, 1792))
    draw = ImageDraw.Draw(im)
    missing = font.getmask("\U0010ffff")
    missing_key = missing.size, bytes(missing)
    glyphs = []
    for i, c in enumerate(characters + "".join(chr(n) for n in range(32, 127))):
        mask = font.getmask(c)
        assert c == " " or (mask.getbbox() and (mask.size, bytes(mask)) != missing_key)
        box = draw.textbbox((0, 0), c, font=font)
        w, h = box[2]-box[0], box[3]-box[1]
        assert 0 <= w <= 56 and 0 <= h <= 56
        x, y = i % 16 * 64, i // 16 * 64
        ox, oy = x+(64-w)//2-box[0], y+(64-h)//2-box[1]
        draw.text((ox, oy), c, font=font, fill=(255, 255, 255, 255))
        glyphs.append(dict(character=c, big5=codes[i*2:i*2+2].hex() if i < 353 else "",
                           source_index=i if i < 353 else -1, cell=[x, y, 64, 64],
                           ink=[ox+box[0], oy+box[1], w, h]))
    shutil.copytree(a.base, a.out, dirs_exist_ok=True)
    im.save(a.out/"story-font.png")
    m = dict(schema=1, source_sha256=EXE_SHA, runtime_sha256=RUNTIME_SHA,
             codes_sha256=CODE_SHA, native_ink_sha256=INK_SHA, table_sha256=TABLE_SHA,
             codes=codes.hex(), font_sha256=FONT_SHA, family="Noto Sans CJK TC", weight=900,
             atlas="story-font.png", atlas_sha256=sha((a.out/"story-font.png").read_bytes()),
             width=1024, height=1792, glyphs=glyphs,
             rights="local-only original mapping; Noto SIL OFL 1.1; notice: intro-Noto-NOTICE.txt")
    (a.out/"story.json").write_text(json.dumps(m, ensure_ascii=False, indent=2)+"\n")
    provenance = dict(source_runtime=a.runtime.name, runtime_sha256=RUNTIME_SHA,
                      source_exe_sha256=EXE_SHA, font_sha256=FONT_SHA, font_index=3,
                      font_px=48, pillow=__version__, missing=0, base_files=before,
                      manifest_sha256=sha((a.out/"story.json").read_bytes()), rights=m["rights"])
    (a.out/"story-import.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2)+"\n")
    assert all(sha((a.out/n).read_bytes()) == h for n, h in before.items())
    assert all(p.stat().st_uid == 1000 for p in a.out.rglob("*"))
    print(json.dumps(dict(preserved=len(before), glyphs=len(glyphs), missing=0,
                         atlas_sha256=m["atlas_sha256"], manifest_sha256=provenance["manifest_sha256"])))


if __name__ == "__main__":
    main()
