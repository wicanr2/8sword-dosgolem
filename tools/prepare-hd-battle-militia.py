"""重用 018 民兵原圖；只增加 028 戰場別名與來源紀錄。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("base", "source", "out"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    assert args.out.is_dir() and not any(args.out.iterdir()), "輸出目錄須存在且為空"
    raw = args.source.read_bytes()
    source_sha = "a7e02cf495800fac19c293688043f3af6eb6deaec1a61a581ed3f9d5b8b3e5f1"
    image_sha = "5173125ab4f02b170561b797d6ae043fc3c1c854f3ad61da791c3ba1e8aea620"
    assert digest(raw) == source_sha, "MAN01.EGG 來源不符"
    assert raw[:4] == bytes([11, 0, 50, 0])
    reverse = bytes(int(f"{v:08b}"[::-1], 2) for v in range(256))
    record = raw[:4] + b"".join(bytes(reverse[v] for v in raw[i:i+11][::-1])
                               for i in range(4, 3304, 11))
    native_sha = "0b22eb3e544d9f7805cc4df1f0c99fc47b8818ef4bf6e78a7ac08d6993df62e8"
    record_sha = "78b8127ab7346e62e062dc514bad4a749be8d21f69e6dede53a246240d74b924"
    assert digest(record) == record_sha and digest(record[:2204]) == native_sha
    terrain = json.loads((args.base / "terrain.json").read_text())
    assert terrain["schema"] == 1 and terrain["style"] == "B-bright-painted-r1"
    actor, = [v for v in terrain["actors"] if v["source_index"] == 84]
    assert actor == dict(source_index=84, file="militia-painted-r1.png", sha256=image_sha,
                         width=1176, height=1337, sampling="bitmap")
    assert digest((args.base / actor["file"]).read_bytes()) == image_sha
    prompt_sha = "643dafcb1320c09dd8581501e74a65cfb94d00f68d7a1338f1dcb590cc4f8591"
    assert digest((args.base / "army-prompt.txt").read_bytes()) == prompt_sha
    assert not (args.base / "battle-militia.json").exists(), "基底已有戰場別名"
    preserved = {}
    for path in sorted(args.base.iterdir()):
        assert path.is_file() and not path.is_symlink(), "基底僅接受普通檔案"
        shutil.copyfile(path, args.out / path.name)
        preserved[path.name] = digest(path.read_bytes())
    manifest = dict(schema=1, source_file="MAN01.EGG", source_sha256=source_sha,
                    record=0, transform="mirror-six-planes", native_sha256=native_sha,
                    record_sha256=record_sha, source_index=84, base_actor_id=85,
                    battle_actor_id=107, image_file=actor["file"], image_sha256=image_sha,
                    cache_sha256="1c795ec9e8d67feca9a014d3b3511bc9ed9d9d115102e8042e4a16b3b4982fe5",
                    style=terrain["style"], style_reference_sha256=terrain["style_reference_sha256"])
    (args.out / "battle-militia.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    provenance = dict(spec="028", source=manifest, reused_art_spec="018",
                      prompt_file="army-prompt.txt", prompt_sha256=prompt_sha,
                      existing_provenance_file="army-source.json", new_generation=False,
                      sampling="reuse immutable actor 85 cache without resampling",
                      preserved_files=preserved, rights="local-only derivative; no public redistribution grant")
    (args.out / "battle-militia-source.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(dict(files=len(list(args.out.iterdir())), preserved_files=len(preserved), new_images=0)))


if __name__ == "__main__":
    main()
