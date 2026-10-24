#!/usr/bin/env python3
"""核對全部 MAN*.EGG 的固定記錄及已登錄 HD 戰場圖；不宣稱正常路徑覆蓋。"""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ["original", "assets", "out"]:
        ap.add_argument("--"+name, type=Path, required=True)
    a = ap.parse_args()
    assert not a.out.exists() and a.out.parent.is_dir()
    assert a.out.parent.stat().st_uid == 1000
    registered = {}
    manifests = []
    # These are the runtime loaders' six current battle-unit entrypoints.
    for name in ["battle-actors.json", "battle-man06.json", "battle-man11.json",
                 "battle-man21.json", "battle-man01.json", "battle-militia.json"]:
        f = a.assets/name
        m = json.loads(f.read_text())
        source = m["source_file"]
        assert re.fullmatch(r"MAN\d{2}\.EGG", source)
        assert sha((a.original/source).read_bytes()) == m["source_sha256"]
        manifests.append(dict(file=name, sha256=sha(f.read_bytes())))
        entries = m.get("frames", [m] if "record" in m else [])
        for e in entries:
            record = e["record"]
            assert isinstance(record, int) and 0 <= record < 4
            image = e.get("image", dict(file=e.get("image_file"), sha256=e.get("image_sha256")))
            assert sha((a.assets/image["file"]).read_bytes()) == image["sha256"]
            assert (source, record) not in registered
            registered[source, record] = dict(manifest=name, image=image["file"], image_sha256=image["sha256"],
                                             transform=m.get("transform", "identity"))
    files = sorted(f for f in a.original.iterdir() if re.fullmatch(r"MAN\d{2}\.EGG", f.name))
    assert files
    records = []
    for f in files:
        raw = f.read_bytes()
        assert len(raw) == 4*3304, (f.name, len(raw))
        for record in range(4):
            at = record*3304
            value = raw[at:at+3304]
            assert struct.unpack_from("<HH", value) == (11, 50), (f.name, record)
            records.append(dict(source_file=f.name, source_sha256=sha(raw), record=record,
                                address_space="original file offset", file_offset=at, bytes=3304,
                                native_size=[88, 50], planes=6, record_sha256=sha(value),
                                first_four_planes_with_header_sha256=sha(value[:2204]),
                                hd_registration=registered.get((f.name, record)),
                                normal_path_coverage="not determined by this catalog",
                                formal_name_mapping="not evaluated by this catalog"))
    keys = {(r["source_file"], r["record"]) for r in records}
    assert set(registered) <= keys
    result = dict(schema=1, status="verified-fixed-record-inventory-and-HD-registration", source_files=len(files),
                  source_records=len(records), hd_registered_records=len(registered),
                  remaining_unregistered_records=len(records)-len(registered), input_manifests=manifests,
                  records=records, tool_sha256=sha(Path(__file__).read_bytes()),
                  evidence_level="proven file bytes, record geometry, manifest/image identity; not runtime path coverage",
                  limitation="excludes CHOI/PON effects, MAN.AY hero, ENEMY.AY encounters, army-page routing and other non-EGG art; counts are not whole-game HD completion percentages",
                  rights="local-only original-derived metadata; no public distribution grant")
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({k: result[k] for k in ["source_files", "source_records", "hd_registered_records", "remaining_unregistered_records"]}))


if __name__ == "__main__":
    main()
