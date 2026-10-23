"""核對本輪已命名的原版啟動收據；在 Pillow Docker 映像中執行。"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pixels(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def changed(a: Image.Image, b: Image.Image) -> int:
    if a.size != b.size:
        raise ValueError("Screenshot dimensions differ")
    return sum(x != y for x, y in zip(a.getdata(), b.getdata()))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("/project"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.root
    intake = root / "workplace/intake-20261023"
    receipts = root / "workplace/probe-20261023"
    manifest = json.loads((intake / "source-manifest.json").read_text())
    failures = [r["path"] for r in manifest["inputs"] if digest(root / r["path"]) != r["sha256"]]
    failures += [r["path"] for r in manifest["files"]
                 if digest(intake / "sources" / r["path"]) != r["sha256"]]
    if failures:
        raise ValueError(f"Original source changed: {failures}")

    diagnostic = pixels(receipts / "page-calls/plane-offset-4000.png")
    warm = pixels(receipts / "pages-fixed/screen.png")
    cold = pixels(receipts / "cold-fixed-r1/screen.png")
    if changed(diagnostic, warm) or changed(warm, cold):
        raise ValueError("Cold/warm/diagnostic page comparison failed")

    saved = receipts / "saved/scratch/gamedata.ay"
    reloaded = receipts / "cold-after-exit/loaded-save.bin"
    if saved.stat().st_size != 2987 or saved.read_bytes() != reloaded.read_bytes():
        raise ValueError("Normal save data did not reach the original load buffer intact")
    save_screen = pixels(receipts / "saved/screen.png")
    exit_log = (receipts / "exited/probe.log").read_text(errors="replace")
    if "程式呼叫 int 21h AH=4Ch，離開碼 0" not in exit_log:
        raise ValueError("Missing normal DOS exit receipt")
    if (receipts / "exited/scratch/gamedata.ay").read_bytes() != saved.read_bytes():
        raise ValueError("Exit changed the stored save data")
    load_screen = pixels(receipts / "cold-after-exit/screen.png")
    rect = (0, 0, 460, 200)
    a, b = save_screen.crop(rect), load_screen.crop(rect)
    diff = ImageChops.difference(a, b)
    tests = (receipts / "validation/tests.log").read_text()
    expected = ("internal/dos", "internal/machine", "internal/state", "oracle")
    for package in expected:
        if not any(l.startswith("ok") and f"github.com/wicanr2/dosgolem/{package}\t" in l
                   for l in tests.splitlines()):
            raise ValueError(f"Missing passing test result: {package}")
    report = {
        "scope": "original dosgolem bootstrap, BIOS display pages, normal save/load; no HD runtime claim",
        "source_archives_checked": len(manifest["inputs"]),
        "extracted_files_checked": len(manifest["files"]),
        "source_changes": failures,
        "warm_vs_diagnostic_changed_pixels": 0,
        "cold_vs_warm_changed_pixels": 0,
        "saved_bytes": 2987,
        "normal_exit_code": 0,
        "saved_sha256": digest(saved),
        "loaded_buffer_sha256": digest(reloaded),
        "saved_buffer_address_space": "dosgolem runtime linear 0x9E000 at step 126029773, after original DOS read",
        "load_visual_comparison": {
            "rectangle": rect,
            "changed_pixels": changed(a, b),
            "difference_bbox": diff.getbbox(),
            "note": "Camera/player position inspected; animation phase is not aligned; not full-frame parity",
        },
        "passing_packages": list(expected),
        "probe_sha256": digest(root / "workplace/probe-pages"),
        "dosgolem_base": "f79eab6db8c64a524a06535e53e5d32b0bbcf7c8",
        "patch_sha256": digest(root / "tools/dosgolem-planar-pages.patch"),
    }
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
