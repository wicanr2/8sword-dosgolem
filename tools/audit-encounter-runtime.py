#!/usr/bin/env python3
"""037：正常三組逐幀邊界、來源與客體隔離。不能代替 GUI 驗收。"""
import argparse
import hashlib
import importlib.util
import json
from itertools import zip_longest
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

spec = importlib.util.spec_from_file_location("frame_decoder", Path(__file__).with_name("audit-army-dismiss.py"))
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def files(root):
    return {str(p.relative_to(root)): sha(p) for p in root.rglob("*") if p.is_file()}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ["hd", "control", "broken", "out"]:
        ap.add_argument("--" + name, type=Path, required=True)
    a = ap.parse_args()
    assert not a.out.exists()
    roots = [a.hd, a.control, a.broken]
    states = [json.loads((p / "final.json").read_text()) for p in roots]
    for name in ["final.state", "audio.pcm", "commands.jsonl", "encounter-calls.jsonl"]:
        assert len({sha(p / name) for p in roots}) == 1, name
    assert all(files(p / "scratch") == files(a.hd / "scratch") for p in roots)
    for key in ["steps", "input_events", "file_ops", "exec_log", "strings", "exited", "exit_code", "elapsed_ms", "recorded_frames"]:
        assert all(s[key] == states[0][key] for s in states), key
    for s in states:
        assert s["exited"] and s["exit_code"] == 0 and s["elapsed_ms"] == 89900
        assert s["normal_input_replay"] and not s["snapshot_loaded"] and not s["guest_injection"]
        assert not s["text"]["MissingGlyphs"] and not s["text"]["Errors"]
        for key in ["asset_error", "graphics_error", "font_error", "battle_actor_error", "battle_background_error", "battle_effect_error", "battle_marker_error"]:
            assert not s[key], key
    assert not states[0]["map_encounter_error"] and not states[1]["map_encounter_error"]
    assert "SHA-256" in states[2]["map_encounter_error"]
    assert states[0]["graphics_actor_materials"] == states[1]["graphics_actor_materials"] + 10
    assert states[2]["graphics_actor_materials"] == states[1]["graphics_actor_materials"]
    assert states[0]["graphics"]["ActorCalls"] == states[1]["graphics"]["ActorCalls"] + 11
    assert states[0]["graphics"]["ActorFallbackCalls"] == states[1]["graphics"]["ActorFallbackCalls"]
    calls = [json.loads(l) for l in (a.hd / "encounter-calls.jsonl").read_text().splitlines()]
    assert len(calls) == 14
    assert [c["height"] for c in calls] == list(range(1, 26, 2)) + [25]
    mask = Image.new("L", (1920, 1200))
    draw = ImageDraw.Draw(mask)
    for c in calls:
        x, y = c["x_byte"] * 24, c["y"] * 6
        draw.rectangle((x, y, x + 191, y + c["height"] * 6 - 1), fill=255)
    inverse = ImageChops.invert(mask)
    changed = []
    for row in zip_longest(*(helper.stream(p) for p in roots)):
        assert all(v is not None for v in row)
        (n, step, hd), (cn, cs, control), (bn, bs, broken) = row
        assert (n, step) == (cn, cs) == (bn, bs)
        assert control.tobytes() == broken.tobytes(), ("fault differs from original fallback", n)
        diff = ImageChops.difference(hd.convert("RGB"), control.convert("RGB"))
        channel = ImageChops.lighter(ImageChops.lighter(diff.getchannel("R"), diff.getchannel("G")), diff.getchannel("B"))
        assert not ImageChops.multiply(channel, inverse).getbbox(), ("outside original source rectangle", n)
        if diff.getbbox():
            changed.append(dict(frame=n, step=step, bbox=diff.getbbox()))
    assert changed and n == states[0]["recorded_frames"]
    # These checkpoints include ordinary encounter confirmation, battle, F1/F2 and F7 save/quit.
    for f in a.control.glob("*-hd.png"):
        if f.name != "06-west-frontier-hd.png":
            assert sha(f) == sha(a.hd / f.name), ("stale encounter art after leaving", f.name)
        assert sha(f) == sha(a.broken / f.name)
    result = dict(schema=1, status="passed-normal-three-groups", frames_per_run=n,
                  source_calls=len(calls), new_actor_calls=11, changed_frames=changed,
                  state_sha256=sha(a.hd / "final.state"), pcm_sha256=sha(a.hd / "audio.pcm"),
                  scratch_files=len(files(a.hd / "scratch")), all_fault_frames_equal_control=True,
                  original_source_rectangles_preserved=True, other_checkpoints_equal=True,
                  frame_purity_checked=False, gui_verified=False,
                  limitation="normal cold start, first encounter, battle, F1/F2, real F7 save and DOS quit; no reload or GUI claim; image differences bounded, not independent whole-frame HD reconstruction",
                  tool_sha256=sha(Path(__file__)))
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ["status", "frames_per_run", "source_calls", "new_actor_calls", "state_sha256"]}))


if __name__ == "__main__":
    main()
