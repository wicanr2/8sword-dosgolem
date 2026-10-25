#!/usr/bin/env python3
"""043：獨立重建正常城堡實際 Draw，連結原始來源、錄影與真正存讀。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("assets", "original", "cache", "gui", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--saved-inspection", type=Path)
    parser.add_argument("--loaded-inspection", type=Path)
    args = parser.parse_args()
    assert not args.out.exists()
    sampling = module("castle_sampling", "audit-encounter-gui.py")
    constants = module("castle_constants", "prepare-hd-castle.py")
    streaming = module("castle_recording", "audit-army-dismiss.py")
    model = sampling.Model(args.assets, args.original, args.cache)
    image = args.assets / "map-castle-r2.png"
    assert sha(image) == constants.IMAGE_SHA
    grass = model.material(1)[0]
    background = b"".join(grass[(row % 150) * 768:(row % 150 + 1) * 768] * 3
                          for row in range(300))
    whole = sampling.sample(image, 576, 300, actor=True, background=background)
    for i in range(6):
        x, y = i % 3 * 192, i // 3 * 150
        tile = b"".join(whole[((row + y) * 576 + x) * 4:
                              ((row + y) * 576 + x + 192) * 4] for row in range(150))
        assert hashlib.sha256(tile).hexdigest() == constants.CACHE_SHA[i]
        assert tile == (args.cache / f"castle-{59 + i}.rgba").read_bytes()
        model.materials[60 + i] = tile, 64, 25
    pmap = (args.original / "PMAP.AY").read_bytes()
    assert hashlib.sha256(pmap).hexdigest() == constants.PMAP_SHA
    phases = {}
    for phase in ("save", "reload"):
        root = args.gui / phase
        final = read(root / "gui-final.json")
        assert not final["map_castle_error"] and final["graphics_materials"] == 63
        assert final["closed"] and final["recorded_frames"] == final["presented_frames"]
        for key in ("asset_error", "graphics_error", "font_error", "palette_error",
                    "army_man21_error", "battle_actor_error", "battle_marker_error"):
            assert not final[key], (phase, key)
        calls = [json.loads(line) for line in (root / "castle-calls.jsonl").read_text().splitlines()]
        assert {call["record"] for call in calls} == set(range(59, 65))
        for index in range(59, 65):
            raw = (root / f"castle-first-{index}-source.bin").read_bytes()
            assert raw == pmap[index * 1004:(index + 1) * 1004]
            expected = bytes(sum(((raw[4 + plane * 200 + pixel // 8] >>
                                  (7 - pixel % 8)) & 1) << plane for plane in range(4))
                             for pixel in range(1600))
            assert (root / f"castle-first-{index}-after.idx").read_bytes() == expected
        paths = sorted((root / "research-castle-draws").glob("*-first-draw.json"))
        assert len(paths) == 3
        results = [model.frame(path.with_suffix("")) for path in paths]
        assert {result["font_id"] for result in results} == {"noto", "lishu", "caoshu"}
        for path, result in zip(paths, results):
            meta = read(path)
            assert set(range(60, 66)) <= set(result["material_ids"])
            for index in range(59, 65):
                prior = [call for call in calls if call["record"] == index and call["return_step"] <= meta["step"]]
                assert prior and max(c["return_step"] for c in prior) == meta["source_return_steps"][str(index)]
        wanted = {result["actual_draw"]: result for result in results}
        count = 0
        for ordinal, step, frame in streaming.stream(root):
            count = ordinal
            if ordinal in wanted:
                result = wanted.pop(ordinal)
                assert result["step"] == step
                assert result["rgba_sha256"] == hashlib.sha256(frame.tobytes()).hexdigest()
        assert not wanted and count == final["recorded_frames"]
        phases[phase] = dict(frames=count, source_calls=len(calls), source_indexed_pixels=9600,
                             actual_draws=results, full_model_pixels=len(results) * 2304000)
    saved = read(args.gui / "save/saved.json")
    assert saved["bytes"] == 2987 and saved["sha256"] == sha(args.gui / "scratch/gamedata.ay")
    assert read(args.gui / "save/gui-final.json")["exited"]
    assert read(args.gui / "save/gui-final.json")["exit_code"] == 0
    assert (args.gui / "scratch/map01.ay").stat().st_size == 5761
    loaded = read(args.gui / "reload/gui-final.json")
    reads = [op for op in loaded["file_ops"] if op["Op"] == "read" and
             op["Name"].lower() == "gamedata.ay" and op["Len"] == 2987 and not op["Failed"]]
    assert reads
    ram = False
    if args.saved_inspection or args.loaded_inspection:
        assert args.saved_inspection and args.loaded_inspection
        for inspection in (args.saved_inspection, args.loaded_inspection):
            assert sha(inspection / "save-buffer-9e000.bin") == saved["sha256"]
        ram = True
    result = dict(status="passed-independent-castle-actual-Draws", phases=phases,
                  actual_stream_link=True, three_fonts=True, save_bytes=2987,
                  save_sha256=saved["sha256"], map_sha256=sha(args.gui / "scratch/map01.ay"),
                  original_read_step=reads[0]["Step"], saved_loaded_ram_equal=ram,
                  scope="six PMAP castle parts, normal Continue, XTEST menus, F7 save/quit/cold Continue")
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in
                      ("status", "save_sha256", "original_read_step", "saved_loaded_ram_equal")}))


if __name__ == "__main__":
    main()
