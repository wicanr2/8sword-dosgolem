"""042：鏡射原型、正常來源與觀測隔離核對。沒有動作來源時保持 incomplete。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
import struct
from pathlib import Path
from PIL import Image, ImageChops


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text())


def files(root):
    return {str(p.relative_to(root)): sha(p) for p in root.rglob("*") if p.is_file()}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ["source", "build", "reload-build", "observed", "control", "reload", "partial-reload", "prototype", "rebuild", "out"]:
        ap.add_argument("--" + name, type=Path, required=True)
    a = ap.parse_args()
    assert not a.out.exists() and a.out.parent.is_dir()
    source = a.source.read_bytes()
    assert len(source) == 13216
    assert sha(a.source) == "47cc484319abeba53551c20b7cf4b9b2c6061f2da3b6cda14155b3598f10982c"
    proto = read(a.prototype / "registration.json")
    assert proto["source_sha256"] == sha(a.source)
    assert not proto["production_registered"] and not proto["normal_source_verified"]
    assert files(a.prototype) == files(a.rebuild)
    assert [e["record"] for e in proto["entries"]] == list(range(4))
    for e in proto["entries"]:
        p = a.prototype / e["cache_file"]
        assert p.stat().st_size == 264 * 300 * 4 and sha(p) == e["cache_sha256"]
    observed, control, reload = [read(p / "final.json") for p in [a.observed, a.control, a.reload]]
    for s in [observed, control, reload]:
        assert s["exited"] and s["exit_code"] == 0
        assert s["normal_input_replay"] and not s["snapshot_loaded"] and not s["guest_injection"]
        assert s["recorded_frames"] == s["frame_pure_count"] > 0
        assert not s["text"]["MissingGlyphs"] and not s["text"]["Errors"]
        assert not any(v for k, v in s.items() if k.endswith("_error"))
    identical = ["final.state", "audio.pcm", "commands.jsonl", "presentation.frames.gz"]
    for name in identical:
        assert sha(a.observed / name) == sha(a.control / name), name
    scratch = files(a.observed / "scratch")
    assert scratch == files(a.control / "scratch")
    for key in ["steps", "input_events", "file_ops", "exec_log", "strings", "clock_baseline", "rng_seed"]:
        assert observed[key] == control[key], key
    for p in a.observed.glob("*.png"):
        assert sha(p) == sha(a.control / p.name), p.name
    saved = a.observed / "scratch/gamedata.ay"
    ram = a.reload / "snapshot-readonly/save-buffer-9e000.bin"
    assert saved.stat().st_size == ram.stat().st_size == 2987
    assert sha(saved) == sha(ram) == read(a.reload / "continued-game.json")["sha256"]
    saved_map = a.observed / "scratch/map01.ay"
    assert saved_map.stat().st_size == 5761
    assert sha(saved_map) == read(a.reload / "continued-map.json")["sha256"]
    assert sha(saved_map) == sha(a.reload / "scratch/map01.ay")
    assert not (a.partial_reload / "continued-map.json").exists()
    assert sha(saved_map) != sha(a.partial_reload / "scratch/map01.ay")
    pages = read(a.reload / "snapshot-readonly/pages.json")
    assert pages["steps"] == reload["steps"] and pages["save_buffer_sha256"] == sha(saved)
    assert sha(a.observed / "24-F2-hd.png") == sha(a.reload / "03-reloaded-army-hd.png")
    old_map = Image.open(a.observed / "25-end-location-hd.png").convert("RGB")
    reloaded_map = Image.open(a.reload / "02-reloaded-location-hd.png").convert("RGB")
    final_map_diff = ImageChops.difference(old_map, reloaded_map)
    partial_map = Image.open(a.partial_reload / "02-reloaded-location-hd.png").convert("RGB")
    partial_diff = ImageChops.difference(old_map, partial_map)
    assert partial_diff.getbbox(), "negative fixture did not expose the missing map companion"
    module = importlib.util.spec_from_file_location("stream_helper", Path(__file__).with_name("audit-army-dismiss.py"))
    helper = importlib.util.module_from_spec(module)
    module.loader.exec_module(helper)
    decoded = {}
    phase_match = None
    expected_map = old_map.tobytes()
    for root, status in [(a.observed, observed), (a.reload, reload)]:
        count = 0
        phases = [json.loads(line) for line in (root / "frames.jsonl").read_text().splitlines()]
        assert len(phases) == status["recorded_frames"]
        for count, step, im in helper.stream(root):
            assert im.size == (1920, 1200) and step <= status["steps"]
            if root == a.reload and phase_match is None and phases[count - 1]["phase"] == "key-0x3f":
                if im.convert("RGB").tobytes() == expected_map:
                    phase_match = dict(draw=count, step=step, full_pixels=2304000)
        assert count == status["recorded_frames"]
        decoded[root.name] = count
    assert phase_match is not None, "full F5 image absent throughout the recorded reload blink cycle"
    calls = [json.loads(line) for line in (a.observed / "battle-source-calls.jsonl").read_text().splitlines()]
    captured = []
    for e in proto["entries"]:
        i = e["record"]
        matching = [c for c in calls if c.get("target_record") == i]
        if not matching:
            assert not (a.observed / f"ally21-first-{i}-call.json").exists()
            continue
        call = read(a.observed / f"ally21-first-{i}-call.json")
        assert call == matching[0]
        assert call["entry"] == 0x626 and call["return"] == 0x76e and call["segment"] == 0x14d2
        assert call["abi_bytes_matched"] == 329 and call["entry_step"] < call["return_step"]
        assert call["destination_segment"] == 0xa000 and call["mode"] == 1
        assert call["width_bytes"] == 11 and call["height"] == 50
        assert 0 <= call["x_byte"] <= 69 and 0 <= call["y"] <= 150
        assert f"MAN21.EGG/{i}/mirror-six-planes" in call["catalog"]
        raw = source[i * 3304:(i + 1) * 3304]
        assert struct.unpack_from("<HH", raw) == (11, 50)
        mirrored = raw[:4] + bytes(int(f"{v:08b}"[::-1], 2)
                                  for row in range(4, 3304, 11) for v in raw[row:row + 11][::-1])
        prefix = a.observed / f"ally21-first-{i}"
        assert Path(str(prefix) + "-source.bin").read_bytes() == mirrored
        assert hashlib.sha256(mirrored).hexdigest() == e["six_plane_sha256"] == call["source_sha256"]
        assert hashlib.sha256(mirrored[:2204]).hexdigest() == e["native_sha256"]
        background = Path(str(prefix) + "-background.idx").read_bytes()
        after = Path(str(prefix) + "-after.idx").read_bytes()
        assert len(background) == len(after) == 4400
        for y in range(50):
            for x in range(88):
                at, bit = y * 11 + x // 8, 7 - x % 8
                color = sum(((mirrored[4 + plane * 550 + at] >> bit) & 1) << plane for plane in range(4))
                expected = color if (mirrored[4 + 5 * 550 + at] >> bit) & 1 else background[y * 88 + x]
                assert after[y * 88 + x] == expected, (i, x, y)
        captured.append(i)
    build_inputs = a.build / "build-inputs.sha256"
    for build in [a.build, a.reload_build]:
        for line in (build / "build-inputs.sha256").read_text().splitlines():
            digest, name = line.split(None, 1)
            assert sha(build / "src" / name.strip()) == digest
    result = dict(schema=1, status="source-coverage-complete" if len(captured) == 4 else "incomplete-source-coverage",
                  production_ready=False, production_registered=False,
                  source_file=a.source.name, source_sha256=sha(a.source),
                  prototype_files=len(files(a.prototype)), prototype_rebuild_equal=True,
                  source_calls=len(calls), captured_records=captured,
                  missing_records=[i for i in range(4) if i not in captured],
                  source_observation_isolation="passed", frames_per_run=observed["recorded_frames"],
                  total_frame_purity=sum(s["frame_pure_count"] for s in [observed, control, reload]),
                  decoded_streams=decoded, scratch_files=len(scratch),
                  state_sha256=sha(a.observed / "final.state"), pcm_sha256=sha(a.observed / "audio.pcm"),
                  commands_sha256=sha(a.observed / "commands.jsonl"),
                  clock_baseline=observed["clock_baseline"], rng_seed=observed["rng_seed"],
                  save_bytes=2987, save_sha256=sha(saved), reload_steps=reload["steps"],
                  map_bytes=5761, map_sha256=sha(saved_map), reload_F2_exact=True,
                  reload_F5_phase_aligned=phase_match, GUI_verified=False,
                  reload_F5_final_difference=dict(difference_bbox=final_map_diff.getbbox(),
                      different_pixels=sum(v != (0, 0, 0) for v in final_map_diff.getdata())),
                  partial_reload_negative_control=dict(difference_bbox=partial_diff.getbbox(),
                      different_pixels=sum(v != (0, 0, 0) for v in partial_diff.getdata())),
                  probe_sha256=sha(a.build / "probe"), probe_source_sha256=sha(a.build / "src/tools/probe-ally21.go"),
                  reload_probe_sha256=sha(a.reload_build / "probe"),
                  reload_probe_source_sha256=sha(a.reload_build / "src/tools/probe-ally21.go"),
                  build_input_count=len(build_inputs.read_text().splitlines()),
                  build_input_manifest_sha256=sha(build_inputs), verifier_sha256=sha(Path(__file__)))
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
