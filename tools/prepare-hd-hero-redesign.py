"""依 004 使用者更正的方向匯入武將主角肖像；原圖 byte 保持。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from PIL import Image


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for key in ("base", "source", "refs", "out"):
        ap.add_argument("--" + key, type=Path, required=True)
    a = ap.parse_args()
    assert a.out.is_dir() and not any(a.out.iterdir())
    assert sha(a.source) == "9849714498718f6616644ad717906cc426c3f3f5f335cdb99dbcc8173c8dbe12"
    assert hashlib.sha256(a.source.read_bytes()[17552:19556]).hexdigest() == "61694748e9f443d37427a725c564cfad3ed4df77418c99081729e175e8a7c28a"
    art = a.refs / "hero-portrait-r3.png"
    assert sha(art) == "b97e3a9c908db0ce66b5579478fa40551e93d8ff9d91622cf89427eed4fa1e41"
    with Image.open(art) as im:
        assert im.format == "PNG" and im.size == (1254, 1254)
        assert im.convert("RGBA").getchannel("A").getextrema() == (255, 255)
    provenance = json.loads((a.refs / "hero-portrait-redesign-provenance-r1.json").read_text())
    assert len(provenance["runs"]) == 2 and provenance["runs"][1]["selected"]
    for run in provenance["runs"]:
        assert sha(a.refs / run["output"]) == run["output_sha256"]
    terrain = json.loads((a.base / "terrain.json").read_text())
    item, = [e for e in terrain["materials"] if e["source_index"] == 68]
    assert item["file"] == "hero-portrait-r1.png" and item["sampling"] == "bitmap"
    preserved = {}
    for f in sorted(a.base.iterdir()):
        assert f.is_file() and not f.is_symlink()
        shutil.copyfile(f, a.out / f.name)
        preserved[f.name] = sha(f)
    newfile = "hero-portrait-warrior-r1.png"
    prompts = "hero-portrait-warrior-r1.prompts.json"
    assert not (a.out / newfile).exists()
    shutil.copyfile(art, a.out / newfile)
    (a.out / prompts).write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n")
    item.update(file=newfile, sha256=sha(art), width=1254, height=1254,
                source_rect=[0, 0, 1254, 1254], prompt_file=prompts,
                prompt_sha256=sha(a.out / prompts))
    (a.out / "terrain.json").write_text(json.dumps(terrain, ensure_ascii=False, indent=2) + "\n")
    (a.out / "hero-portrait-warrior-source.json").write_text(json.dumps(dict(
        spec="004/HERO-PORTRAIT-DESIGN-REVISED", source_file="MAN.AY", source_sha256=sha(a.source),
        record_offset=17552, record_bytes=2004, source_index=68, native_rect=[24, 13, 80, 40],
        art_sha256=sha(art), prompt_sha256=sha(a.out / prompts), base_files=preserved,
        preserved_files={n: v for n, v in preserved.items() if n != "terrain.json"},
        changed_files=["terrain.json"], original_PNG_bytes_preserved=True,
        rights="local-only derivative; no public redistribution grant"), ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(dict(files=len(list(a.out.iterdir())), original_files=len(preserved), changed=["terrain.json"])))


if __name__ == "__main__":
    main()
