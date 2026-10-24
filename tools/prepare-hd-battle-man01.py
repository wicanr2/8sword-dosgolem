"""036：匯入民兵第 1–3 筆鏡射姿勢，原 PNG bytes 保持。Docker only。"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image, __version__

SOURCE = "a7e02cf495800fac19c293688043f3af6eb6deaec1a61a581ed3f9d5b8b3e5f1"
ART = [
    "13f78b58f9ffe7e2d931cc5f3244bfb31b0dd3135139d12de7a79dd0333a38dd",
    "b0605ced5cfd421a7392e7e16bcde1a6ebbfdda4e79b3e38bc94283d8f05b55d",
    "02b5e836909d71c9d20e67bea2aee9d2321d8b05e2a66e69bb2a2b5e929fcb52",
]
PROMPTS = [
    "d83fbd2c9aebbe0e06b4be9a1a85b10b808129083d3da07153a0fe1d13046236",
    "a486a76c30289d1fb0b00fa410bab3d25b950443301d699aae5d176058894d96",
    "f9ff741a37f5b97a8d3bca60d49d8937dd52445a1590f589f185596a6dbba3ba",
]
RECORDS = [
    "ea9735a587549708dcfb17d8c163065b5265e0ccfcd66fd9cb505f68f386f175",
    "f741358c8c7ffe767479f5be83236afca0fcc7087b6d1dd02506c76bfd0f2611",
    "343d7379493dffbfaf7f23e074bc5799aa74bc705d1a3cf4fa556ed3d91b2c21",
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ["base", "source", "refs", "out"]:
        ap.add_argument("--" + name, type=Path, required=True)
    a = ap.parse_args()
    assert __version__ == "11.3.0"
    assert a.out.is_dir() and not any(a.out.iterdir()) and a.out.stat().st_uid == 1000
    raw = a.source.read_bytes()
    assert sha(a.source) == SOURCE and len(raw) == 13216
    preserved = {p.name: sha(p) for p in a.base.iterdir() if p.is_file()}
    assert len(preserved) == 165 and not (a.base / "battle-man01.json").exists()
    assert all(p.is_file() and not p.is_symlink() for p in a.base.iterdir())
    terrain = json.loads((a.base / "terrain.json").read_text())
    assert terrain["schema"] == 1 and terrain["style"] == "B-bright-painted-r1"
    assert terrain["style_reference_sha256"] == "2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6"
    reverse = bytes(int(f"{v:08b}"[::-1], 2) for v in range(256))
    frames = []
    for i in range(1, 4):
        record = raw[i * 3304:(i + 1) * 3304]
        mirrored = record[:4] + b"".join(bytes(reverse[v] for v in record[j:j + 11][::-1])
                                        for j in range(4, 3304, 11))
        assert hashlib.sha256(mirrored).hexdigest() == RECORDS[i - 1]
        image = a.refs / f"man01-mirror-{i}-painted-r1.png"
        prompt = image.with_suffix(".prompt.txt")
        assert sha(image) == ART[i - 1] and sha(prompt) == PROMPTS[i - 1]
        with Image.open(image) as im:
            assert im.format == "PNG" and im.mode == "RGBA" and im.size == (1176, 1337)
            assert im.getchannel("A").getextrema() == (0, 255)
        frames.append(dict(record=i, target_rect=[0, 0, 264, 300], image=dict(
            source_index=111 + i, file=f"battle-man01-{i}-r1.png", sha256=ART[i - 1],
            width=1176, height=1337, sampling="bitmap", source_rect=[0, 0, 1176, 1337],
            prompt_file=f"battle-man01-{i}-r1.prompt.txt", prompt_sha256=PROMPTS[i - 1])))
    for name in preserved:
        shutil.copyfile(a.base / name, a.out / name)
    for i, frame in enumerate(frames, 1):
        shutil.copyfile(a.refs / f"man01-mirror-{i}-painted-r1.png", a.out / frame["image"]["file"])
        shutil.copyfile(a.refs / f"man01-mirror-{i}-painted-r1.prompt.txt", a.out / frame["image"]["prompt_file"])
    manifest = dict(schema=1, source_file="MAN01.EGG", source_sha256=SOURCE,
                    style=terrain["style"], style_reference_sha256=terrain["style_reference_sha256"],
                    transform="mirror-six-planes", frames=frames)
    (a.out / "battle-man01.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    provenance = dict(spec="036", source=manifest, mirrored_record_sha256=RECORDS,
                      preserved_files=preserved, tool="Pillow " + __version__,
                      original_png_bytes_preserved=True,
                      approval_basis="existing B style and militia identity; no separate user selection of these PNGs",
                      rights="local-only original-derived; no public distribution grant")
    (a.out / "battle-man01-source.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n")
    assert len(list(a.out.iterdir())) == 173
    assert all(sha(a.out / name) == h for name, h in preserved.items())
    assert all(p.stat().st_uid == 1000 for p in a.out.iterdir())
    print("173 files; all 165 base files preserved; three optional mirrored MAN01 poses")


if __name__ == "__main__":
    main()
