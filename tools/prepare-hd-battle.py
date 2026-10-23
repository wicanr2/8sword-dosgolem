"""在 Docker 匯入 021 已核對的戰場背景，保留完整基底與原圖 bytes。"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

from PIL import Image


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("base", "source", "art", "prompt", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    assert args.out.is_dir() and not any(args.out.iterdir()), "輸出目錄須存在且為空"
    raw = args.source.read_bytes()
    assert digest(raw) == "9e0182e0a576d62564ffcdccc6b9484bd0ff94e4f545ca43045f9aa1c1c45e4a", "GRO02.EG 來源不符"
    spec = importlib.util.spec_from_file_location("intro", Path(__file__).with_name("prepare-hd-intro.py"))
    intro = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(intro)
    decoded = intro.decode(raw)
    assert digest(decoded) == "b2262e970d5525826db47e9507787f9f3daddb2e00394934c728dc5d0ee8f763"
    art, prompt = args.art.read_bytes(), args.prompt.read_bytes()
    assert digest(art) == "4ec05b750acd05b1d86af6706fa9cec8f60ddf9123c30f6cd4b5a2c5dd3c59f2", "背景原圖不符"
    assert digest(prompt) == "dd2d46bc4a2e1df56152fbee27074e45aaf390844387f0793f407c2aa2aae195", "完整提示不符"
    with Image.open(args.art) as image:
        assert image.format == "PNG" and image.mode == "RGB" and image.size == (1586, 992)
        width, height = image.size
    assert not (args.base / "battle-background.json").exists(), "基底不可已有戰場背景"
    preserved = {}
    for path in sorted(args.base.iterdir()):
        assert path.is_file() and not path.is_symlink(), "基底僅接受普通檔案"
        shutil.copyfile(path, args.out / path.name)
        preserved[path.name] = digest(path.read_bytes())
    (args.out / "battle-background-r1.png").write_bytes(art)
    (args.out / "battle-background-prompt.txt").write_bytes(prompt)
    manifest = dict(schema=1, source_sha256=digest(raw), native_sha256=digest(decoded),
                    style="B-bright-painted-r1",
                    style_reference_sha256="2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6",
                    image=dict(source_index=85, file="battle-background-r1.png", sha256=digest(art),
                               width=width, height=height, sampling="bitmap"))
    (args.out / "battle-background.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    (args.out / "battle-background-source.json").write_text(json.dumps(dict(
        spec="021", source_file="GRO02.EG", source_sha256=digest(raw), decoded_sha256=digest(decoded),
        decoded_bytes=len(decoded), native_size=[640, 200], art_sha256=digest(art), prompt_sha256=digest(prompt),
        tool="built-in image_gen", original_png_bytes_preserved=True, preserved_files=preserved,
        rights="local-only derivative; no public redistribution grant"), ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(dict(files=len(list(args.out.iterdir())), preserved_files=len(preserved), art_sha256=digest(art))))


if __name__ == "__main__":
    main()
