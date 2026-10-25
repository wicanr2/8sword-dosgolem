#!/usr/bin/env python3
"""核對 043 的正常來源、只讀觀測隔離與固定六筆 PMAP 返回。

在 Docker 內執行。這份收據不代表 HD 接入或實際視窗驗收。
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

PMAP_SHA = "9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02"
PAM_SHA = "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text())


def inventory(directory):
    return {str(p.relative_to(directory)): sha(p)
            for p in sorted(directory.rglob("*")) if p.is_file()}


def world_mapping(args, module):
    from PIL import Image

    path = Path(__file__).with_name("prepare-hd-intro.py")
    spec = importlib.util.spec_from_file_location("castle_map_decode", path)
    decoder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(decoder)
    data = decoder.decode((args.original / "MAP1.AY").read_bytes())
    assert len(data) == 5761 and data[-1] == 0x1A
    rows = data[:-1].split(b"\r\n")
    assert len(rows) == 81 and not rows[-1]
    assert all(len(row) == 70 for row in rows[:-1])
    terrain = [[value - 49 for value in row] for row in rows[:-1]]
    assert 0 <= min(map(min, terrain)) and max(map(max, terrain)) <= 64
    screen = Image.open(args.source / "02-south-three-native.png").convert("RGB")
    pmap = (args.original / "PMAP.AY").read_bytes()
    matches = []
    for row in range(7):
        for col in range(7):
            if (row, col) == (3, 3):
                continue
            x, y = 38 + col - 3, 40 + row - 3
            index = terrain[y][x]
            raw = pmap[index * 1004:(index + 1) * 1004]
            for py in range(25):
                for px in range(64):
                    bit, at = 7 - px % 8, py * 8 + px // 8
                    color = sum(((raw[4 + plane * 200 + at] >> bit) & 1) << plane
                                for plane in range(4))
                    assert screen.getpixel(((8 + col * 64 + px) * 3,
                                            (12 + row * 25 + py) * 6)) == module.EGA[color]
            matches.append(dict(x=x, y=y, record=index, indexed_pixels=1600))
    assert [terrain[28][x] for x in range(17, 20)] == [59, 60, 61]
    assert [terrain[29][x] for x in range(17, 20)] == [62, 63, 64]
    return dict(compressed_sha256=sha(args.original / "MAP1.AY"),
                decoded_sha256=hashlib.sha256(data).hexdigest(),
                map_format="70x80 terrain, ASCII minus 49; MAP01 is separate fog state",
                matching_tiles=matches, matching_pixels=48 * 1600)


def prototype(args, source, scratch):
    """沿既有完整 Frame 模型，獨立建立全景取樣與六塊切分。"""
    from PIL import Image

    module_path = Path(__file__).with_name("audit-encounter-gui.py")
    spec = importlib.util.spec_from_file_location("castle_frame_model", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert args.image and args.assets
    image_sha = sha(args.image)
    alpha_variant = image_sha == "744a39bb04c869803c0583604ac3c5c0481e174ad3153c4a8489f1219ad50a97"
    assert alpha_variant or image_sha == "ea90a41fe5747555e8389cd4be1f276fe9aed62323b3e2189a78313200fb8072"
    assert Image.open(args.image).size == ((1736, 906) if alpha_variant else (1737, 906))
    model = module.Model(args.assets, args.original, args.prototype)
    if alpha_variant:
        grass = model.material(1)[0]
        background = b"".join(grass[(row % 150) * 192 * 4:(row % 150 + 1) * 192 * 4] * 3
                              for row in range(300))
        whole = module.sample(args.image, 576, 300, actor=True, background=background)
    else:
        whole = module.sample(args.image, 576, 300)
    tiles = []
    for index in range(6):
        x, y = index % 3 * 192, index // 3 * 150
        tile = b"".join(whole[((row + y) * 576 + x) * 4:
                              ((row + y) * 576 + x + 192) * 4]
                        for row in range(150))
        assert len(tile) == 192 * 150 * 4
        model.materials[60 + index] = tile, 64, 25
        tiles.append(dict(record=59 + index, rgba_sha256=hashlib.sha256(tile).hexdigest()))
    reference = args.continuation_control or args.source
    if args.continuation_control:
        source = read(reference / "final.json")
        scratch = inventory(reference / "scratch")
        assert source["exited"] and source["exit_code"] == 0
        assert not source["guest_injection"] and not source["snapshot_loaded"]
        assert source["normal_input_replay"]
    final = read(args.prototype / "final.json")
    assert not final["prototype_castle_error"]
    if args.production:
        assert not final["map_castle_error"] and not source["map_castle_error"]
    assert final["recorded_frames"] == final["frame_pure_count"] == source["recorded_frames"]
    assert final["graphics_materials"] == source["graphics_materials"] + 6
    assert not final["guest_injection"] and not final["snapshot_loaded"]
    for name in ("final.state", "audio.pcm", "commands.jsonl", "frames.jsonl"):
        assert sha(args.prototype / name) == sha(reference / name), name
    for key in ("steps", "exit_code", "exited", "input_events", "file_ops", "exec_log",
                "music", "elapsed_ms", "strings", "irq1_delivered", "bios_consumed"):
        assert final[key] == source[key], key
    assert inventory(args.prototype / "scratch") == scratch
    packets = sorted(args.prototype.glob("*-model.json"))
    assert len(packets) == 5
    results = [model.frame(p.with_suffix("")) for p in packets]
    assert {row["font_id"] for row in results} == {"noto", "lishu", "caoshu"}
    assert set(range(60, 66)) <= {i for row in results for i in row["material_ids"]}
    for name in ("15-F1", "16-F2"):
        for suffix in ("-hd.png", "-native.png"):
            assert sha(reference / (name + suffix)) == sha(args.prototype / (name + suffix))
    for path in reference.glob("*-native.png"):
        assert sha(path) == sha(args.prototype / path.name), path.name
    fault = None
    if args.broken:
        failed = read(args.broken / "final.json")
        reason = failed["map_castle_error"] if args.production else failed["prototype_castle_error"]
        assert reason == ("城堡圖片 SHA-256 不符" if args.production else "castle image hash")
        assert failed["graphics_materials"] == source["graphics_materials"]
        for name in ("final.state", "audio.pcm", "commands.jsonl", "frames.jsonl",
                     "presentation.frames.gz"):
            assert sha(args.broken / name) == sha(reference / name), name
        assert failed["recorded_frames"] == failed["frame_pure_count"] == source["recorded_frames"]
        assert inventory(args.broken / "scratch") == scratch
        for path in reference.glob("*.png"):
            assert sha(path) == sha(args.broken / path.name), path.name
        fault = dict(reason=reason,
                     frames=failed["recorded_frames"], all_frames_equal_to_control=True,
                     all_six_unregistered=True)
    return dict(scope=("production loader; headless full Frame only; GUI pending" if args.production
                       else "disposable prototype; headless full Frame only; GUI pending"),
                image_sha256=image_sha, alpha_variant=alpha_variant, tiles=tiles, frames=results,
                state_sha256=sha(args.prototype / "final.state"),
                pcm_sha256=sha(args.prototype / "audio.pcm"),
                frame_purity=final["frame_pure_count"], normal_exit=final["exit_code"],
                old_F1_F2_unchanged=True, all_native_checkpoints_unchanged=True,
                fault=fault, world_mapping=world_mapping(args, module))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("original", "source", "control", "build", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("prototype", "image", "assets", "continuation-control", "broken",
                 "saved-inspection", "cold-inspection"):
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--production", action="store_true", help="核對正式載入器及其獨立回退錯誤")
    args = parser.parse_args()
    assert not args.out.exists(), "不能覆寫舊收據"
    assert sha(args.original / "PMAP.AY") == PMAP_SHA
    assert sha(args.original / "PAM.AY") == PAM_SHA
    pmap = (args.original / "PMAP.AY").read_bytes()
    left, right = read(args.source / "final.json"), read(args.control / "final.json")
    assert left == right, "唯讀觀測改變最終狀態或事件"
    assert left["exited"] and left["exit_code"] == 0
    assert not left["guest_injection"] and not left["snapshot_loaded"]
    assert left["normal_input_replay"] and left["recorded_frames"] == 1421
    assert left["frame_pure_count"] == left["recorded_frames"]
    equal = {}
    for name in ("commands.jsonl", "frames.jsonl", "presentation.frames.gz",
                 "audio.pcm", "final.state", "frame-check.state"):
        a, b = sha(args.source / name), sha(args.control / name)
        assert a == b, (name, a, b)
        equal[name] = a
    snapshots = sorted(args.source.glob("*-hd.png"))
    assert len(snapshots) == 17
    for image in snapshots:
        for suffix in ("-hd.png", "-native.png", ".json"):
            name = image.name.removesuffix("-hd.png") + suffix
            assert sha(args.source / name) == sha(args.control / name), name
    scratch = inventory(args.source / "scratch")
    assert scratch == inventory(args.control / "scratch") and len(scratch) == 22
    assert {"gamedata.ay", "map01.ay"} <= scratch.keys()
    assert (args.source / "scratch/gamedata.ay").stat().st_size == 2987
    assert (args.source / "scratch/map01.ay").stat().st_size == 5761
    calls = [json.loads(line) for line in
             (args.source / "castle-calls.jsonl").read_text().splitlines()]
    assert {row["record"] for row in calls} == set(range(59, 65))
    records = []
    for index in range(59, 65):
        stem = args.source / f"castle-first-{index}"
        call = read(Path(str(stem) + "-call.json"))
        raw = Path(str(stem) + "-source.bin").read_bytes()
        assert raw == pmap[index * 1004:(index + 1) * 1004]
        assert raw[:4] == b"\x08\0\x19\0" and len(raw) == 1004
        assert call in calls and call["raw_sha256"] == hashlib.sha256(raw).hexdigest()
        assert (call["segment"], call["entry"], call["return"], call["abi_bytes_matched"]) == (0x14D2, 0x76F, 0x854, 230)
        assert call["mode"] == 1 and call["dest"] in (0xA000, 0xA400)
        assert (call["width_bytes"], call["height"]) == (8, 25)
        assert call["return_step"] > call["entry_step"]
        assert call["source"] == {"Seg": 0x7000, "Off": index * 1004}
        assert call["first"] == (call["dest"] - 0xA000) * 16 + call["y"] * 80 + call["x_byte"]
        expected = bytes(sum(((raw[4 + plane * 200 + pixel // 8] >>
                              (7 - pixel % 8)) & 1) << plane
                             for plane in range(4)) for pixel in range(1600))
        assert Path(str(stem) + "-after.idx").read_bytes() == expected
        assert len(Path(str(stem) + "-before.idx").read_bytes()) == 1600
        records.append(dict(record=index, native_sha256=hashlib.sha256(raw[:804]).hexdigest(),
                            full_sha256=hashlib.sha256(raw).hexdigest(),
                            destination=call["dest"], return_step=call["return_step"],
                            indexed_pixels=1600,
                            calls=sum(row["record"] == index for row in calls)))
    inputs = 0
    for line in (args.build / "build-inputs.sha256").read_text().splitlines():
        digest, name = line.split("  ", 1)
        assert sha(args.build / "src" / name) == digest, name
        inputs += 1
    assert inputs == 44
    output_sha, output_name = (args.build / "build-outputs.sha256").read_text().split()
    assert output_name == "../probe" and sha(args.build / "probe") == output_sha
    result = dict(schema=1, scope="normal original source and observer isolation only",
                  status="source-verified; HD integration and GUI pending",
                  original=dict(pmap_sha256=PMAP_SHA, pam_sha256=PAM_SHA),
                  executable_sha256=output_sha, build_inputs=inputs,
                  frames_each=left["recorded_frames"],
                  total_frame_purity=left["frame_pure_count"] + right["frame_pure_count"],
                  elapsed_ms=left["elapsed_ms"], normal_exit=0, equal=equal,
                  checkpoints=len(snapshots), scratch_files=len(scratch),
                  scratch_sha256=scratch, records=records,
                  indexed_pixels=sum(row["indexed_pixels"] for row in records))
    if args.prototype:
        result["prototype"] = prototype(args, left, scratch)
    if args.saved_inspection or args.cold_inspection:
        assert args.saved_inspection and args.cold_inspection and args.prototype
        saved = args.source / "scratch/gamedata.ay"
        saved_map = args.source / "scratch/map01.ay"
        for inspection in (args.saved_inspection, args.cold_inspection):
            assert sha(inspection / "save-buffer-9e000.bin") == sha(saved)
            assert read(inspection / "pages.json")["save_buffer_sha256"] == sha(saved)
        assert read(args.prototype / "continued-game.json")["sha256"] == sha(saved)
        assert read(args.prototype / "continued-map.json")["sha256"] == sha(saved_map)
        cold = read(args.prototype / "08-castle-approach.json")
        assert read(args.cold_inspection / "pages.json")["steps"] == cold["steps"]
        reads = []
        for name, size in (("gamedata.ay", 2987), ("map01.ay", 5761)):
            found = [op for op in cold["file_ops"] if op["Op"] == "read" and
                     op["Name"].lower() == name and op["Len"] == size and not op["Failed"]]
            assert found, name
            reads.extend(found)
        result["normal_save_and_cold_continue"] = dict(
            save_sha256=sha(saved), map_sha256=sha(saved_map),
            saved_and_loaded_ram_equal=True, runtime_ram_address="dosgolem linear 0x9E000, 2987 bytes",
            reads=reads, scope="normal F7, DOS exit, cold Continue; no state injection; GUI pending")
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in
                      ("status", "frames_each", "total_frame_purity", "checkpoints",
                       "scratch_files", "indexed_pixels")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
