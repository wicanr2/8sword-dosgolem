#!/usr/bin/env python3
"""Independently audit spec 008 cold-input receipts and the actual PCM output."""
import argparse
import array
import hashlib
import json
import math
from pathlib import Path
import subprocess
import struct


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def files(root):
    return {str(p.relative_to(root)): sha(p) for p in root.rglob("*") if p.is_file()}


def audit_gui(args):
    final = load(args.gui/"gui-final.json")
    receipt = load(args.gui/"gui-input-receipt.json")
    music = final["music"]
    assert receipt["flow"] == "music" and receipt["status"] == "passed-input-path"
    assert final["closed"] and final["hd"] and not final["asset_error"] and not final["graphics_error"]
    assert music["bound"] and not music["binding_error"] and not music["load_error"]
    assert music["loaded_cues"] == 1 and music["hd_frames"] >= 96000 and music["clipped_samples"] == music["fallbacks"] == 0
    assert not final["unimplemented"] and final["text"]["MissingGlyphs"] == 0 and not final["text"]["Errors"]
    assert final["recorded_frames"] == final["presented_frames"]
    raw = args.gui/"audio-s16le-stereo.pcm"
    pcm = array.array("h", raw.read_bytes())
    assert len(pcm) == final["captured_audio_frames"]*2
    per_ms = final["session"]["cycles_per_ms"]
    assert abs(len(pcm)//2-final["session"]["guest_ms"]*48) < 2
    expected = array.array("h", subprocess.check_output(["ffmpeg", "-v", "error", "-nostdin", "-i", str(args.ogg), "-f", "s16le", "-ac", "2", "-ar", "48000", "-"]))
    checks = []
    events = music["events"]
    starts = [e for e in events if e["kind"] == "start" and e["cue"] == 1 and e["valid"]]
    assert len(starts) == 2
    for e in starts:
        stop = next(x for x in events if x["kind"] == "stop" and x["cycles"] > e["cycles"])
        frames = min(96000, int((stop["cycles"]-e["cycles"])*48000/(per_ms*1000))-8)
        assert frames > 12000
        nominal = math.ceil(e["cycles"]*48000/(per_ms*1000))
        error,shift = min((math.sqrt(sum((pcm[(nominal+s)*2+i]-expected[i])**2 for i in range(frames*2))/(frames*2)),s) for s in range(-3,4))
        assert error < 32, (error,shift)
        checks.append(dict(cycles=e["cycles"],compared_frames=frames,calibration_shift_frames=shift,rms_error_int16=error))
    captures = sorted(args.gui.glob("*.png"))
    captures = [p for p in captures if p.stem.startswith(("music-","01-","02-","03-","04-","05-","06-","07-","08-","09-","10-","11-"))]
    assert len(captures) == 17
    for p in captures:
        header = p.read_bytes()[:24]
        assert header[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II",header[16:24]) == (1280,800)
    result = dict(status="passed", scope="actual XTEST window and frontend rendered PCM; device muted, no physical audio continuity claim", input_events=len(receipt["events"]), captured_images=len(captures), frames=final["recorded_frames"], audio_frames=len(pcm)//2, hd_audio_frames=music["hd_frames"], waveform_checks=checks, pcm_sha256=sha(raw), ogg_sha256=sha(args.ogg), final_music_mode=music["mode"], final_cue=music["cue"])
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(result,ensure_ascii=False,indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--native", type=Path)
    parser.add_argument("--hd", type=Path)
    parser.add_argument("--gui", type=Path)
    parser.add_argument("--bad", type=Path)
    parser.add_argument("--bad-reference", type=Path)
    parser.add_argument("--ogg", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.gui:
        audit_gui(args)
        return
    if not args.native or not args.hd:
        parser.error("需要 --gui，或同時提供 --native 與 --hd")
    dirs = [args.native, args.hd]
    references = [load(d/"final-receipt.json") for d in dirs]
    catalogs = [load(d/"catalog.json") for d in dirs]
    assert all(c["normal_input_replay"] and not c["snapshot_loaded"] and c["cycles_per_ms"] == 3000 for c in catalogs)
    assert all(c["entries"] == catalogs[0]["entries"] for c in catalogs)
    state_hashes = [sha(d/"final.state") for d in dirs]
    assert len(set(state_hashes)) == 1, state_hashes
    assert all(files(d/"scratch") == files(dirs[0]/"scratch") for d in dirs)
    for key in ("input_events", "file_ops", "exec_log"):
        assert all(r[key] == references[0][key] for r in references)
    pictures = sorted(p.name for p in args.native.glob("[0-9]*.png"))
    assert len(pictures) == 13
    assert all(sha(d/name) == sha(args.native/name) for name in pictures for d in dirs)
    assert all(not r["unimplemented"] and r["text"]["MissingGlyphs"] == 0 and not r["text"]["Errors"] for r in references)
    for r in references:
        m = r["music"]
        assert m["bound"] and not m["binding_error"] and m["fallbacks"] == 0
    music = references[1]["music"]
    assert music["loops"] >= 1 and music["hd_frames"] >= 4108980 and music["clipped_samples"] == 0
    assert music["mode"] == "native" and music["cue"] == 2
    assert all(references[i]["music"]["events"] == music["events"] for i in range(len(dirs)))
    for name in ("02-first-play", "03-same-enter", "04-highlight-second"):
        assert load(args.hd/(name+".json"))["music"]["mode"] == "hd"
    native = array.array("h", (args.native/"output-s16le-stereo.pcm").read_bytes())
    hd = array.array("h", (args.hd/"output-s16le-stereo.pcm").read_bytes())
    assert len(native) == len(hd) and len(hd) % 2 == 0
    cue1 = [e for e in music["events"] if e["kind"] == "start" and e["cue"] == 1 and e["valid"]]
    cue2 = next(e for e in music["events"] if e["kind"] == "start" and e["cue"] == 2 and e["valid"])
    assert len(cue1) == 2
    expected = array.array("h", subprocess.check_output(["ffmpeg", "-v", "error", "-nostdin", "-i", str(args.ogg), "-f", "s16le", "-ac", "2", "-ar", "48000", "-"]))
    assert len(expected) == 4108980*2
    waveform = []
    width = 48000*2*2
    for e in cue1:
        nominal = math.ceil(e["cycles"]*48000/3000000)
        errors = []
        for shift in range(-3, 4):
            frame = nominal+shift
            err = math.sqrt(sum((hd[frame*2+i]-expected[i])**2 for i in range(width))/width)
            errors.append((err, shift, frame))
        error, shift, frame = min(errors)
        assert error < 32, (error, shift)
        native_difference = math.sqrt(sum((hd[frame*2+i]-native[frame*2+i])**2 for i in range(width))/width)
        assert native_difference > 32
        waveform.append(dict(cycles=e["cycles"], frame=frame, calibration_shift_frames=shift, rms_error_int16=error, difference_from_original_fm_int16=native_difference))
    loop_frame = waveform[0]["frame"]+4108980
    loop_error = math.sqrt(sum((hd[loop_frame*2+i]-expected[i])**2 for i in range(width))/width)
    assert loop_error < 32
    # After the unsupported HD cue starts, the original FM phase must be exact.
    restored = math.ceil(cue2["cycles"]*48000/3000000)+4
    assert hd[restored*2:] == native[restored*2:]
    if args.bad:
        fault_reference = args.bad_reference or args.native
        fault_native = load(fault_reference/"final-receipt.json")
        fault = load(args.bad/"final-receipt.json")
        assert load(args.bad/"catalog.json")["entries"] == load(fault_reference/"catalog.json")["entries"]
        assert sha(args.bad/"final.state") == sha(fault_reference/"final.state")
        assert files(args.bad/"scratch") == files(fault_reference/"scratch")
        for name in pictures:
            assert sha(args.bad/name) == sha(fault_reference/name)
        for key in ("input_events", "file_ops", "exec_log"):
            assert fault[key] == fault_native[key]
        bad = array.array("h", (args.bad/"output-s16le-stereo.pcm").read_bytes())
        assert bad == array.array("h", (fault_reference/"output-s16le-stereo.pcm").read_bytes())
        assert fault["hd"] and not fault["asset_error"] and not fault["graphics_error"]
        assert "SHA-256" in fault["music"]["load_error"] and fault["music"]["hd_frames"] == 0
    report = dict(status="passed", scope="normal cold Engine path; no actual GUI/device claim; F7 canceled", inputs=dict(native=str(args.native),hd=str(args.hd),bad=str(args.bad) if args.bad else None,bad_reference=str(args.bad_reference) if args.bad_reference else None), state_sha256=state_hashes[0], scratch_files=len(files(args.native/"scratch")), pictures_equal=len(pictures), guest_inputs_and_io_equal=True, source_events_equal=True, waveform_checks=waveform, loop_waveform_frame=loop_frame, loop_waveform_rms_error_int16=loop_error, decoded_output_frames=len(hd)//2, hd_frames=music["hd_frames"], hd_loops=music["loops"], native_fm_restored_exactly=True, corrupt_music_returns_exact_native=bool(args.bad), fault_first_ms=load(args.bad/"catalog.json").get("first_ms",90000) if args.bad else None, fault_state_sha256=sha(args.bad/"final.state") if args.bad else None, ogg_sha256=sha(args.ogg), rights="all input scores/captures/audio remain local")
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
