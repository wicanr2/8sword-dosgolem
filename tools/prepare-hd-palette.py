#!/usr/bin/env python3
"""於非 root Docker 中建立保留原概念圖色彩的可選 HD 修色清單。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    base, out = args.base.resolve(), args.out.resolve()
    if base == out or not base.is_dir() or not out.is_dir() or any(out.iterdir()):
        raise ValueError("必須提供既有基底及全新的空輸出目錄")
    if os.geteuid() == 0 or out.stat().st_uid != os.geteuid():
        raise ValueError("輸出目錄必須由目前非 root 使用者擁有")
    terrain = json.loads((base / "terrain.json").read_text())
    if terrain.get("ui") != {"style": "jade-gold-v1", "paper_source": 46}:
        raise ValueError("基底必須含已驗證的金玉介面")
    entries = sorted(base.iterdir())
    if any(not p.is_file() or p.is_symlink() for p in entries) or (base / "presentation-palette.json").exists():
        raise ValueError("基底只能包含一般素材檔，且不得已有修色清單")
    manifest = {
        "schema": 1,
        "source_sha256": "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0",
        "style": "jade-gold-refined-r2",
        "style_reference_sha256": "2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6",
        "approved_sample_sha256": "a817d0b60b919f79f185efac72440880f7c28a211308db8de3e953f6337ea5d8",
    }
    for p in entries:
        shutil.copyfile(p, out / p.name)
    (out / "presentation-palette.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    for p in entries:
        if hashlib.sha256(p.read_bytes()).digest() != hashlib.sha256((out / p.name).read_bytes()).digest():
            raise ValueError(f"基底複製後不符：{p.name}")
    if any(p.stat().st_uid != os.geteuid() for p in out.iterdir()):
        raise ValueError("輸出擁有權不符")
    print(json.dumps({"files": len(entries) + 1, "preserved": len(entries), "style": manifest["style"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
