#!/usr/bin/env python3
"""038：獨立核對正常三組串流、角色矩形、客體及原版存檔。Docker only。"""
import argparse
import importlib.util
import json
from itertools import zip_longest
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

spec = importlib.util.spec_from_file_location("common", Path(__file__).with_name("audit-encounter-runtime.py"))
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)


def read(path):
    return json.loads(path.read_text())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ["hd", "control", "broken", "out"]:
        ap.add_argument("--"+name, type=Path, required=True)
    a = ap.parse_args()
    assert not a.out.exists()
    roots = [a.hd, a.control, a.broken]
    states = [read(p/"final.json") for p in roots]
    for name in ["final.state", "audio.pcm", "commands.jsonl", "encounter-calls.jsonl"]:
        assert len({common.sha(p/name) for p in roots}) == 1, name
    assert all(common.files(p/"scratch") == common.files(a.hd/"scratch") for p in roots)
    for key in ["steps", "input_events", "file_ops", "exec_log", "strings", "exited", "exit_code", "elapsed_ms", "recorded_frames"]:
        assert all(s[key] == states[0][key] for s in states), key
    for state in states:
        assert state["exited"] and state["exit_code"] == 0
        assert state["normal_input_replay"] and not state["snapshot_loaded"] and not state["guest_injection"]
        assert not state["text"]["MissingGlyphs"] and not state["text"]["Errors"]
        for key in ["asset_error", "graphics_error", "font_error", "battle_actor_error", "battle_background_error", "battle_effect_error", "battle_marker_error", "map_encounter_error"]:
            assert not state[key], key
    assert not states[0]["map_encounter_10_error"] and not states[1]["map_encounter_10_error"]
    assert "尾隨" in states[2]["map_encounter_10_error"]
    assert states[0]["graphics_actor_materials"] == states[1]["graphics_actor_materials"]+13
    assert states[2]["graphics_actor_materials"] == states[1]["graphics_actor_materials"]
    calls = [json.loads(x) for x in (a.hd/"encounter-calls.jsonl").read_text().splitlines()]
    assert [c["height"] for c in calls] == list(range(1, 26, 2))+[25]
    assert all(c["catalog"] == [f'ENEMY.AY/10/mirror/height-{c["height"]:02d}'] for c in calls)
    assert states[0]["graphics"]["ActorCalls"] == states[1]["graphics"]["ActorCalls"]+len(calls)
    mask = Image.new("L", (1920, 1200))
    d = ImageDraw.Draw(mask)
    for c in calls:
        x, y = c["x_byte"]*24, c["y"]*6
        d.rectangle((x, y, x+191, y+c["height"]*6-1), fill=255)
    inverse = ImageChops.invert(mask)
    changed = []
    for records in zip_longest(*(common.helper.stream(p) for p in roots)):
        assert all(v is not None for v in records)
        (n, step, hd), (cn, cs, control), (bn, bs, broken) = records
        assert (n, step) == (cn, cs) == (bn, bs)
        assert control.tobytes() == broken.tobytes(), ("fault fallback", n)
        diff = ImageChops.difference(hd.convert("RGB"), control.convert("RGB"))
        channel = ImageChops.lighter(ImageChops.lighter(diff.getchannel("R"), diff.getchannel("G")), diff.getchannel("B"))
        assert not ImageChops.multiply(channel, inverse).getbbox(), ("outside source rectangle", n)
        if diff.getbbox():
            changed.append(dict(frame=n, step=step, bbox=diff.getbbox()))
    assert changed and n == states[0]["recorded_frames"]
    for f in a.control.glob("*-hd.png"):
        if not f.name.startswith(("02-", "03-", "04-", "05-")):
            assert common.sha(f) == common.sha(a.hd/f.name), ("stale actor after leaving", f.name)
        assert common.sha(f) == common.sha(a.broken/f.name)
    for root in roots:
        character, army = read(root/"09-character.json"), read(root/"10-army.json")
        assert character["visible_scene"] == "character"
        assert any(e["Source"] == 10380 and e["Step"] > character["steps"] for e in army["strings"])
        assert (root/"scratch/gamedata.ay").stat().st_size == 2987
    result = dict(schema=1, status="passed-normal-yes-retreat-F1-F2-save-exit", frames_per_run=n,
                  source_calls=len(calls), changed_frames=changed, state_sha256=common.sha(a.hd/"final.state"),
                  pcm_sha256=common.sha(a.hd/"audio.pcm"), scratch_files=len(common.files(a.hd/"scratch")),
                  save_sha256=common.sha(a.hd/"scratch/gamedata.ay"), fault_stream_equal_control=True,
                  frame_purity_checked=False, gui_verified=False,
                  limitation="same ordinary input and controlled clock; RNG internals unknown; no GUI or reload claim",
                  tool_sha256=common.sha(Path(__file__)))
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({k: result[k] for k in ["status", "frames_per_run", "source_calls", "state_sha256"]}))


if __name__ == "__main__":
    main()
