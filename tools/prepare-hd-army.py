"""在 Docker 內匯入 018 已核對的民兵圖；原始 PNG 不修改。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct

from PIL import Image


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("base", "source", "art", "prompt", "out"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    assert args.out.is_dir() and not any(args.out.iterdir()), "輸出目錄須存在且為空"
    raw = args.source.read_bytes()
    assert digest(raw) == "a7e02cf495800fac19c293688043f3af6eb6deaec1a61a581ed3f9d5b8b3e5f1", "MAN01.EGG 來源不符"
    w, h = struct.unpack_from("<HH", raw)
    assert (w, h) == (11, 50)
    reverse = bytes(int(f"{v:08b}"[::-1], 2) for v in range(256))
    runtime = bytearray(raw[:4])
    for plane in range(6):
        for y in range(h):
            start = 4 + plane * w * h + y * w
            runtime.extend(reverse[v] for v in raw[start:start + w][::-1])
    assert digest(runtime) == "78b8127ab7346e62e062dc514bad4a749be8d21f69e6dede53a246240d74b924"
    art = args.art.read_bytes()
    assert digest(art) == "5173125ab4f02b170561b797d6ae043fc3c1c854f3ad61da791c3ba1e8aea620", "民兵原圖不符"
    prompt = args.prompt.read_bytes()
    assert digest(prompt) == "643dafcb1320c09dd8581501e74a65cfb94d00f68d7a1338f1dcb590cc4f8591", "生成提示不符"
    with Image.open(args.art) as im:
        assert im.format == "PNG" and im.mode == "RGBA" and im.size == (1176, 1337)
        assert im.getchannel("A").getextrema() == (0, 255)
        width, height = im.size
    manifest = json.loads((args.base / "terrain.json").read_text())
    assert manifest["schema"] == 1 and manifest["style"] == "B-bright-painted-r1"
    assert [e["source_index"] for e in manifest["actors"]] == list(range(72, 84))
    preserved = {}
    for path in sorted(args.base.iterdir()):
        assert path.is_file() and not path.is_symlink(), "基底僅接受普通檔案"
        if path.name == "terrain.json":
            continue
        shutil.copyfile(path, args.out / path.name)
        preserved[path.name] = digest(path.read_bytes())
    name = "militia-painted-r1.png"
    assert not (args.out / name).exists()
    (args.out / name).write_bytes(art)
    manifest["actors"].append(dict(source_index=84, file=name, sha256=digest(art),
                                   width=width, height=height, sampling="bitmap"))
    (args.out / "terrain.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    (args.out / "army-source.json").write_text(json.dumps(dict(
        spec="018", source_file="MAN01.EGG", source_sha256=digest(raw),
        record_offset=0, record_bytes=3304, transform="horizontal mirror of all six planes",
        runtime_record_sha256=digest(runtime), art_sha256=digest(art),
        prompt_sha256=digest(prompt), tool="built-in image_gen", original_png_bytes_preserved=True,
        preserved_files=preserved, base_manifest_sha256=digest((args.base / "terrain.json").read_bytes()),
        rights="local-only derivative; no public redistribution grant"), ensure_ascii=False, indent=2) + "\n")
    (args.out / "army-prompt.txt").write_bytes(prompt)
    print(json.dumps({"files": len(list(args.out.iterdir())), "actors": len(manifest["actors"]),
                      "preserved_files": len(preserved), "art_sha256": digest(art)}))


if __name__ == "__main__":
    main()
