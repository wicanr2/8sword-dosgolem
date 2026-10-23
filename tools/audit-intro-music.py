#!/usr/bin/env python3
"""Independently audit spec 009 normal-input state and rendered PCM receipts."""
import argparse
import array
import hashlib
import json
import math
from pathlib import Path
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def files(path):
    return {str(p.relative_to(path)): sha(p) for p in path.rglob("*") if p.is_file()}


def main():
    parser = argparse.ArgumentParser()
    for name in ("native", "hd", "ogg", "out"):
        parser.add_argument("--"+name, type=Path, required=True)
    parser.add_argument("--bad", type=Path)
    args = parser.parse_args()
    assert not args.out.exists(), "拒絕覆寫既有核對收據"
    a, b = load(args.native/"final-receipt.json"), load(args.hd/"final-receipt.json")
    catalogs = [load(d/"catalog.json") for d in (args.native, args.hd)]
    assert all(c["normal_input_replay"] and not c["snapshot_loaded"] and c["cycles_per_ms"] == 3000 for c in catalogs)
    for key in ("intro_ms", "first_ms", "entries"):
        assert catalogs[0][key] == catalogs[1][key]
    state = sha(args.native/"final.state")
    assert state == sha(args.hd/"final.state")
    assert files(args.native/"scratch") == files(args.hd/"scratch")
    for key in ("input_events", "file_ops", "exec_log"):
        assert a[key] == b[key]
    pictures = sorted(p.name for p in args.native.glob("[0-9]*.png"))
    assert len(pictures) == 13
    pictures += ["intro-before-skip.png"]
    assert all(sha(args.native/name) == sha(args.hd/name) for name in pictures)
    for receipt in (a, b):
        # A historical Scene survives DOS exit; it cannot prove interactivity.
        assert not receipt["exited"] and receipt["mode"] != 3
        assert receipt["hd"] and not receipt["asset_error"] and not receipt["graphics_error"]
        assert not receipt["unimplemented"] and receipt["text"]["MissingGlyphs"] == 0 and not receipt["text"]["Errors"]
        music = receipt["music"]
        assert music["intro_bound"] and music["intro_retired"] and music["bound"]
        assert music["fallbacks"] == music["clipped_samples"] == 0
    events = b["music"]["events"]
    assert events == a["music"]["events"]
    intro = [e for e in events if e.get("reason") == "PREDELLA.EXE"]
    assert [e["kind"] for e in intro] == ["request", "start", "stop", "handoff"]
    assert all(e["valid"] for e in intro)
    request, start, stop, handoff = intro
    assert request["cycles"] < start["cycles"] < stop["cycles"] <= handoff["cycles"]
    assert stop["step"] < b["music"]["intro_end_step"] <= handoff["step"]
    assert not any(e.get("reason", "").startswith("PREDELLA") for e in events if e["step"] > handoff["step"])
    expected = array.array("h", subprocess.check_output(["ffmpeg", "-v", "error", "-nostdin", "-i", str(args.ogg), "-f", "s16le", "-ac", "2", "-ar", "48000", "-"]))
    assert len(expected) == 4108980*2
    native = array.array("h", (args.native/"output-s16le-stereo.pcm").read_bytes())
    hd = array.array("h", (args.hd/"output-s16le-stereo.pcm").read_bytes())
    assert len(native) == len(hd) and len(hd) % 2 == 0
    frames = min(96000, math.floor((stop["cycles"]-start["cycles"])*48000/3000000)-8)
    assert frames >= 48000, "片頭實際播放不足一秒"
    nominal = math.ceil(start["cycles"]*48000/3000000)
    error, shift = min((math.sqrt(sum((hd[(nominal+s)*2+i]-expected[i])**2 for i in range(frames*2))/(frames*2)), s) for s in range(-3, 4))
    assert error < 32, (error, shift)
    actual_frame = nominal+shift
    difference = math.sqrt(sum((hd[actual_frame*2+i]-native[actual_frame*2+i])**2 for i in range(frames*2))/(frames*2))
    assert difference > 32
    loop_check = None
    loop_frame = actual_frame + len(expected)//2
    remaining = math.floor(stop["cycles"]*48000/3000000)-4-loop_frame
    if remaining >= 1024:
        loop_frames = min(96000, remaining)
        loop_error = math.sqrt(sum((hd[loop_frame*2+i]-expected[i])**2 for i in range(loop_frames*2))/(loop_frames*2))
        assert loop_error < 32 and b["music"]["loops"] >= 1
        loop_check = dict(output_frame=loop_frame, compared_frames=loop_frames, rms_error_int16=loop_error)
    before = max(0, math.ceil(request["cycles"]*48000/3000000)-4)
    assert hd[:before*2] == native[:before*2]
    restored = math.ceil(stop["cycles"]*48000/3000000)+4
    # PAM begins suppressing FM during its next initialization, before Start.
    # The native-restoration interval therefore ends at that Request boundary.
    next_request = next(e for e in events if e["kind"] == "request" and e["cycles"] > handoff["cycles"])
    until = max(restored, math.floor(next_request["cycles"]*48000/3000000)-4)
    assert until > restored and hd[restored*2:until*2] == native[restored*2:until*2]
    second = next(e for e in events if e["kind"] == "start" and e["cue"] == 2 and e["valid"])
    tail = math.ceil(second["cycles"]*48000/3000000)+4
    assert hd[tail*2:] == native[tail*2:]
    if args.bad:
        fault = load(args.bad/"final-receipt.json")
        assert sha(args.bad/"final.state") == state
        assert files(args.bad/"scratch") == files(args.native/"scratch")
        assert all(sha(args.bad/name) == sha(args.native/name) for name in pictures)
        assert (args.bad/"output-s16le-stereo.pcm").read_bytes() == (args.native/"output-s16le-stereo.pcm").read_bytes()
        assert "SHA-256" in fault["music"]["load_error"] and fault["music"]["hd_frames"] == 0
        assert fault["hd"] and not fault["asset_error"] and not fault["graphics_error"]
        for key in ("input_events", "file_ops", "exec_log"):
            assert fault[key] == a[key]
    report = dict(status="passed", scope="normal cold Engine path and frontend mixer; no GUI/device or full-game claim",
                  state_sha256=state, equal_pictures=len(pictures), scratch_files=len(files(args.native/"scratch")),
                  intro_ms=catalogs[0]["intro_ms"], intro_events=intro, compared_frames=frames,
                  rms_error_int16=error, calibration_shift_frames=shift, difference_from_native_int16=difference,
                  intro_loop_waveform=loop_check,
                  native_prefix_exact=True, native_after_intro_stop_exact=True, native_cue2_tail_exact=True,
                  native_restoration_ends_at_request_cycles=next_request["cycles"],
                  corrupt_music_exact_native=bool(args.bad), output_frames=len(hd)//2,
                  hd_frames=b["music"]["hd_frames"], hd_loops=b["music"]["loops"],
                  ogg_sha256=sha(args.ogg), pcm_sha256=sha(args.hd/"output-s16le-stereo.pcm"),
                  tool_sha256=sha(Path(__file__)))
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
