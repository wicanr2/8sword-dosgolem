"""固定來源的盤點與安全解包；僅在 Docker 研究容器中執行。"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import stat
import struct
import subprocess
import zipfile
from pathlib import Path, PurePosixPath

INPUTS = {
    "8sword.zip": "27eddf82f0e832a8aeae0f11e2b8268650beaf78461764a7d80388ae970c465b",
    "珍092-神州八劍.rar": "00df0b17805b9f08e7ae3b120cc67294a007e2d42b5b23f791175dbe1c1a11fa",
}
MAX_TOTAL = 256 * 1024 * 1024
MAX_FILE = 64 * 1024 * 1024
MAX_ENTRIES = 5000


def run(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=90).stdout


def safe_name(name: str) -> str:
    name = name.replace("\\", "/")
    path = PurePosixPath(name)
    if not name or path.is_absolute() or ".." in path.parts or ":" in name:
        raise ValueError(f"Unsafe archive path: {name!r}")
    if any(ord(c) < 32 for c in name):
        raise ValueError(f"Control character in path: {name!r}")
    return str(path)


def bounds(names: list[str], sizes: list[int]) -> None:
    if len(names) > MAX_ENTRIES or len(set(n.casefold() for n in names)) != len(names):
        raise ValueError("Too many or duplicate archive members")
    if sum(sizes) > MAX_TOTAL or any(s < 0 or s > MAX_FILE for s in sizes):
        raise ValueError("Archive expansion exceeds limits")


def record(path: Path, root: Path) -> dict:
    data = path.read_bytes()
    item = {"path": str(path.relative_to(root)), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}
    if data.startswith(b"MZ") and len(data) >= 28:
        fields = ("last_page_bytes", "pages", "relocations", "header_paragraphs",
                  "min_extra", "max_extra", "initial_ss", "initial_sp", "checksum",
                  "initial_ip", "initial_cs", "relocation_offset", "overlay")
        item["mz_header"] = dict(zip(fields, struct.unpack_from("<13H", data, 2)))
        item["address_space"] = "source file offsets; not IDA or runtime addresses"
        item["entry_file_offset_candidate"] = (
            item["mz_header"]["header_paragraphs"] * 16
            + item["mz_header"]["initial_cs"] * 16
            + item["mz_header"]["initial_ip"])
        item["entry_note"] = "Raw unsigned header expression only; segment wrap/loading not interpreted"
    return item


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("/input"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    inputs = [record(args.input / name, args.input) for name in INPUTS]
    for item in inputs:
        if item["sha256"] != INPUTS[item["path"]]:
            raise ValueError(f"Source identity mismatch: {item['path']}")

    archive = zipfile.ZipFile(args.input / "8sword.zip")
    members = archive.infolist()
    zip_names = [safe_name(i.filename) for i in members]
    bounds(zip_names, [i.file_size for i in members])
    for item in members:
        kind = stat.S_IFMT(item.external_attr >> 16)
        if kind not in (0, stat.S_IFREG, stat.S_IFDIR) or item.flag_bits & 1:
            raise ValueError("Unsupported ZIP entry type or encryption")

    manual = args.input / "珍092-神州八劍.rar"
    rar_names = [safe_name(n) for n in run("bsdtar", "-tf", str(manual)).splitlines()]
    verbose = run("bsdtar", "-tvf", str(manual))
    sizes = []
    for line in verbose.splitlines():
        if not line or line[0] not in "-d":
            raise ValueError("Unsupported RAR entry type")
        sizes.append(int(line.split()[4]))
    if len(sizes) != len(rar_names):
        raise ValueError("RAR listing mismatch")
    bounds(rar_names, sizes)

    args.out.mkdir(parents=True, exist_ok=False)
    game_root = args.out / "sources" / "game"
    manual_root = args.out / "sources" / "manual"
    game_root.mkdir(parents=True)
    manual_root.mkdir()
    for info, name in zip(members, zip_names):
        target = game_root / name
        if info.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            # ZipFile.read validates CRC; sources are identity-checked and size-bounded.
            data = archive.read(info)
            with target.open("xb") as stream:
                stream.write(data)
    run("bsdtar", "-xf", str(manual), "--no-same-owner", "--no-same-permissions",
        "-C", str(manual_root))

    files = []
    for root, expected in ((game_root, zip_names), (manual_root, rar_names)):
        actual = []
        for path in sorted(root.rglob("*")):
            if path.is_symlink() or not (path.is_file() or path.is_dir()):
                raise ValueError("Unexpected extracted file type")
            actual.append(str(path.relative_to(root)))
            if path.is_file():
                if path.stat().st_size > MAX_FILE:
                    raise ValueError("Extracted file exceeds size limit")
                files.append(record(path, args.out / "sources"))
        expected_files = {n for n in expected if not (root / n).is_dir()}
        actual_files = {n for n in actual if (root / n).is_file()}
        if actual_files != expected_files:
            raise ValueError("Extracted membership mismatch")

    tools = {"python": platform.python_version(),
             "bsdtar": run("bsdtar", "--version").strip()}
    manifest = {"date": "2026-10-23", "evidence_level": "confirmed file inventory only",
                "address_space": "source file offsets", "tools": tools,
                "inputs": inputs, "zip_entries": len(members),
                "rar_entries": len(rar_names), "files": files}
    (args.out / "source-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.out / "manual-list.txt").write_text(verbose, encoding="utf-8")
    exe = game_root / "8sword/PREDELLA.EXE"
    strings = [{"file_offset": m.start(), "text": m.group().decode("ascii")}
               for m in re.finditer(rb"[\x20-\x7e]{6,}", exe.read_bytes())]
    (args.out / "exe-ascii-strings.json").write_text(
        json.dumps(strings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"inputs": inputs, "files": len(files), "tools": tools,
                      "executables": [f for f in files if "mz_header" in f]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
