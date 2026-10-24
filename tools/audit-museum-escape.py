#!/usr/bin/env python3
"""017：核對真正到達博物館後的普通 Esc，以及離場後完整回退。"""
import argparse
import hashlib
import json
from pathlib import Path
import runpy


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files(root):
    return {str(path.relative_to(root)): sha(path) for path in root.rglob("*") if path.is_file()}


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("hd", type=Path)
parser.add_argument("control", type=Path)
args = parser.parse_args()
read = lambda path: json.loads(path.read_text())
status, control = [read(root / "gui-final.json") for root in [args.hd, args.control]]
checks = {}
for name in ["final.state", "audio.pcm"]:
    checks[name] = [sha(root / name) for root in [args.hd, args.control]]
    assert len(set(checks[name])) == 1, name
assert files(args.hd / "scratch") == files(args.control / "scratch")
for key in ["file_ops", "input_events", "exec_log", "music", "text"]:
    assert status[key] == control[key], key
assert status["pam_loaded"] and status["museum"]["retired"] and not status["museum"]["draining"]
assert not status["museum"]["errors"] and not status["museum"]["unknown_writes"]
metadata = [json.loads(line) for line in (args.hd / "intro-draw.jsonl").read_text().splitlines()]
assert any(row["elapsed_ms"] == 9100 and row["museum_stage"] == "portrait" for row in metadata)
stream = runpy.run_path(str(Path(__file__).with_name("audit-museum.py")))["stream"]
after = 0
for a, b in zip(stream(args.hd / "presentation.frames.gz"), stream(args.control / "presentation.frames.gz")):
    assert a[:2] == b[:2]
    row = metadata[a[0] - 1]
    if row["elapsed_ms"] > 9100:
        assert not row["museum_stage"] and a == b
        after += 1
assert after == 246
for root, final in [(args.hd, status), (args.control, control)]:
    assert final["frame_pure_count"] == final["recorded_frames"] == 428
    assert (root / "frame-before.state").read_bytes() == (root / "frame-after.state").read_bytes()
result = {"status": "PASS-normal-museum-Esc", "checks": checks,
          "ordinary_Esc_ms": 9100, "positive_HD_portrait_before_Esc": True,
          "same_frames_after_Esc": after, "Frame_purity_total": 856,
          "same_scratch_files": len(files(args.hd / "scratch")),
          "scope": "normal boot and ordinary Esc after real portrait; no entry injection or RNG parity claim"}
(args.hd / "museum-escape-audit.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result))
