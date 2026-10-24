#!/usr/bin/env python3
"""037：核對正常遭遇來源、逐次返回像素及只讀觀測隔離。Docker only。"""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path


spec = importlib.util.spec_from_file_location("encounter_catalog", Path(__file__).with_name("catalog-encounter.py"))
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)


def digest(path, compressed=False):
    h = hashlib.sha256()
    opener = gzip.open if compressed else open
    with opener(path, "rb") as f:
        for b in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def files(root):
    return {str(p.relative_to(root)): digest(p) for p in root.rglob("*") if p.is_file()}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--observed", required=True, type=Path)
    ap.add_argument("--control", required=True, type=Path)
    ap.add_argument("--original", required=True, type=Path)
    ap.add_argument("--record", required=True, type=int, choices=range(14))
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    assert not a.out.exists()
    source = (a.original / "ENEMY.AY").read_bytes()
    assert catalog.sha(source) == catalog.SOURCE_SHA and len(source) == 16856
    full = catalog.mirror(source[a.record * 1204:(a.record + 1) * 1204])
    captures = []
    calls = [json.loads(l) for l in (a.observed / "encounter-calls.jsonl").read_text().splitlines()]
    assert len(calls) >= 13
    assert [c["height"] for c in calls[:13]] == list(range(1, 26, 2))
    for c in calls:
        raw = catalog.prefix(full, c["height"])
        assert catalog.sha(raw) == c["sha256"] and c["y"] + c["height"] == 112
        assert f"ENEMY.AY/{a.record}/mirror/height-{c['height']:02d}" in c["catalog"]
        assert c["entry_step"] < c["return_step"]
        assert c["entry"] == 0x4f2 and c["return"] == 0x625
    for meta in sorted(a.observed.glob("encounter-first-*-call.json")):
        c = json.loads(meta.read_text())
        stem = meta.name.removesuffix("-call.json")
        raw = (a.observed / (stem + "-source.bin")).read_bytes()
        assert raw == catalog.prefix(full, c["height"])
        before = (a.observed / (stem + "-before.idx")).read_bytes()
        after = (a.observed / (stem + "-after.idx")).read_bytes()
        assert len(before) == len(after) == 64 * c["height"]
        area = 8 * c["height"]
        expected = bytearray(before)
        for y in range(c["height"]):
            for x in range(64):
                at, bit = y * 8 + x // 8, 7 - x % 8
                if (raw[4 + 5 * area + at] >> bit) & 1:
                    expected[y * 64 + x] = sum(((raw[4 + p * area + at] >> bit) & 1) << p for p in range(4))
        assert bytes(expected) == after, (stem, c)
        captures.append(dict(height=c["height"], pixels=len(after), mode=c["mode"],
                             destination_segment=c["destination_segment"], entry_step=c["entry_step"],
                             return_step=c["return_step"], source_sha256=c["sha256"]))
    assert [c["height"] for c in captures] == list(range(1, 26, 2))
    roots = [a.observed, a.control]
    states = [json.loads((p / "final.json").read_text()) for p in roots]
    for name in ["final.state", "audio.pcm", "commands.jsonl"]:
        assert digest(roots[0] / name) == digest(roots[1] / name), name
    assert digest(roots[0] / "presentation.frames.gz", True) == digest(roots[1] / "presentation.frames.gz", True)
    assert files(roots[0] / "scratch") == files(roots[1] / "scratch")
    for key in ["steps", "input_events", "file_ops", "exec_log", "strings", "exited", "exit_code", "elapsed_ms", "recorded_frames"]:
        assert states[0][key] == states[1][key], key
    for s in states:
        assert not s["guest_injection"] and not s["snapshot_loaded"] and s["normal_input_replay"]
        assert not s["text"]["MissingGlyphs"] and not s["text"]["Errors"]
        assert not s["asset_error"] and not s["graphics_error"]
    result = dict(schema=1, status="passed-normal-source-and-observation-isolation", record=a.record,
                  source_file="ENEMY.AY", source_sha256=catalog.SOURCE_SHA, file_offset=a.record * 1204,
                  transform="mirror-six-planes and per-plane prefixes", captures=captures, source_calls=len(calls),
                  state_sha256=digest(a.observed / "final.state"), pcm_sha256=digest(a.observed / "audio.pcm"),
                  scratch_files=len(files(a.observed / "scratch")), frames_per_run=states[0]["recorded_frames"],
                  raw_frame_stream_equal=True, frame_purity_checked=False,
                  evidence="proven observed sources and mask output; no gameplay/RNG parity or HD/GUI completion claim",
                  tool_sha256=digest(Path(__file__)))
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ["status", "record", "source_calls", "frames_per_run", "state_sha256"]}))


if __name__ == "__main__":
    main()
