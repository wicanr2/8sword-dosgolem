#!/usr/bin/env python3
"""044：核對正常物件來源、觀測隔離，以及原版寶箱文字的靜態分派鏈。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
import struct
from pathlib import Path

PAM_SHA = "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"
PMAP_SHA = "9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02"
RECORD_SHA = "58a024b3400338bfc12ffba0f8bc5d49c53343ed73ada2a0c41e2a2b19bcb781"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text())


def files(path):
    return {p.name: sha(p) for p in path.iterdir() if p.is_file()}


def prototype(args):
    from PIL import Image

    assert all((args.assets, args.image, args.short_control, args.broken, args.prototype_build))
    assert sha(args.image) == "cbdafc80d3bc9b137d2ba10f6f1d76d0e4cdb8cf8e5cf24abe4768af6ebaae85"
    image = Image.open(args.image)
    assert image.size == (1419, 1108) and image.mode == "RGBA"
    assert image.getchannel("A").getextrema() == (0, 255)
    spec = importlib.util.spec_from_file_location("chest_independent_frame", Path(__file__).with_name("audit-encounter-gui.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    model = module.Model(args.assets, args.original, args.prototype)
    tile = module.sample(args.image, 192, 150, actor=True, background=model.material(1)[0])
    assert len(tile) == 192 * 150 * 4
    model.materials[59] = tile, 64, 25
    reference, candidate, broken = [read(p / "final.json") for p in (args.short_control, args.prototype, args.broken)]
    assert reference["graphics_materials"] == broken["graphics_materials"] == 63
    assert candidate["graphics_materials"] == 64
    error_key = "map_chest_error" if args.production else "prototype_chest_error"
    assert not reference[error_key] and not candidate[error_key]
    assert broken[error_key] == ("寶箱圖片 SHA-256 不符" if args.production else "chest image hash")
    for data in (reference, candidate, broken):
        assert data["recorded_frames"] == data["frame_pure_count"] == 395
        assert data["normal_input_replay"] and not data["snapshot_loaded"] and not data["guest_injection"]
        assert data["exited"] and data["exit_code"] == 0
        for key in ("steps", "exit_code", "exited", "input_events", "file_ops", "exec_log",
                    "music", "elapsed_ms", "strings", "irq1_delivered", "bios_consumed"):
            assert data[key] == reference[key], key
    equal = {}
    for name in ("final.state", "frame-check.state", "audio.pcm", "commands.jsonl", "frames.jsonl"):
        digest = sha(args.short_control / name)
        assert sha(args.prototype / name) == sha(args.broken / name) == digest, name
        equal[name] = digest
    assert sha(args.short_control / "presentation.frames.gz") == sha(args.broken / "presentation.frames.gz")
    scratch = files(args.short_control / "scratch")
    assert files(args.prototype / "scratch") == files(args.broken / "scratch") == scratch
    assert len(scratch) == 22
    shots = sorted(args.short_control.glob("*-native.png"))
    assert len(shots) == 6
    for path in shots:
        assert sha(args.prototype / path.name) == sha(args.broken / path.name) == sha(path)
    for name in ("05-west-hd.png", "07-F1-hd.png", "08-F2-hd.png"):
        assert sha(args.short_control / name) == sha(args.prototype / name) == sha(args.broken / name), name
    for path in args.short_control.glob("*.png"):
        assert sha(path) == sha(args.broken / path.name), path.name
    packets = sorted(args.prototype.glob("*-model.json"))
    assert len(packets) == 5
    results = [model.frame(p.with_suffix("")) for p in packets]
    assert {r["font_id"] for r in results} == {"noto", "lishu", "caoshu"}
    assert all(r["height"] == 25 for r in results)
    assert all(59 in r["material_ids"] for r in results)
    for data, root in ((reference, args.short_control), (candidate, args.prototype), (broken, args.broken)):
        calls = [json.loads(line) for line in (root / "map-object-calls.jsonl").read_text().splitlines()]
        assert calls and all(c["raw_sha256"] == RECORD_SHA for c in calls)
        raw = (root / "map-object-first-58-source.bin").read_bytes()
        assert hashlib.sha256(raw).hexdigest() == RECORD_SHA
        expected = bytes(sum(((raw[4 + q * 200 + p // 8] >> (7-p%8)) & 1) << q
                             for q in range(4)) for p in range(1600))
        assert (root / "map-object-first-58-after.idx").read_bytes() == expected
    build_inputs = 0
    for line in (args.prototype_build / "build-inputs.sha256").read_text().splitlines():
        digest, name = line.split("  ", 1)
        assert sha(args.prototype_build / "src" / name) == digest
        build_inputs += 1
    assert build_inputs == (51 if args.production else 47)
    outputs = {}
    for line in (args.prototype_build / "build-outputs.sha256").read_text().splitlines():
        digest, name = line.split()
        assert sha(args.prototype_build / name) == digest
        outputs[name] = digest
    assert len(outputs) == (3 if args.production else 1) and "probe" in outputs
    if args.production:
        assert not any("ResearchInstallChest" in p.read_text() for p in (args.prototype_build / "src").rglob("*.go"))
    return dict(status="passed-production-loader" if args.production else "passed-disposable-prototype", frames_each=395, total_frame_purity=1185,
                build_inputs=build_inputs, probe_sha256=outputs["probe"], cache_sha256=hashlib.sha256(tile).hexdigest(),
                full_frames=results, equal=equal, scratch_sha256=scratch,
                broken_stream_equal=True, unaffected_pages_equal=True,
                limitation="headless normal Continue, original source, independent PNG/font reconstruction and original F7 save; GUI and saved RAM/cold reload remain unverified")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("original", "source", "control", "build", "ida-query", "ida-map-query", "database", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("prototype", "short-control", "broken", "assets", "image", "prototype-build"):
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--production", action="store_true", help="verify the formal loader and absence of the research installer")
    args = parser.parse_args()
    assert not args.out.exists()
    pam = (args.original / "PAM.AY").read_bytes()
    pmap = (args.original / "PMAP.AY").read_bytes()
    assert hashlib.sha256(pam).hexdigest() == PAM_SHA
    assert hashlib.sha256(pmap).hexdigest() == PMAP_SHA
    source, control = read(args.source / "final.json"), read(args.control / "final.json")
    assert source == control
    assert source["exited"] and source["exit_code"] == 0
    assert source["normal_input_replay"] and not source["snapshot_loaded"] and not source["guest_injection"]
    assert source["recorded_frames"] == source["frame_pure_count"] == 1084
    equal = {}
    for name in ("commands.jsonl", "frames.jsonl", "presentation.frames.gz", "audio.pcm", "final.state", "frame-check.state"):
        assert sha(args.source / name) == sha(args.control / name), name
        equal[name] = sha(args.source / name)
    shots = sorted(args.source.glob("*-hd.png"))
    assert len(shots) == 14
    for image in shots:
        prefix = image.name.removesuffix("-hd.png")
        for suffix in ("-hd.png", "-native.png", ".json"):
            assert sha(args.source / (prefix + suffix)) == sha(args.control / (prefix + suffix))
    scratch = files(args.source / "scratch")
    assert scratch == files(args.control / "scratch")
    raw = (args.source / "map-object-first-58-source.bin").read_bytes()
    assert raw == pmap[58 * 1004:59 * 1004]
    assert hashlib.sha256(raw).hexdigest() == RECORD_SHA
    assert raw[:4] == b"\x08\0\x19\0"
    expected = bytes(sum(((raw[4 + plane * 200 + pixel // 8] >> (7 - pixel % 8)) & 1) << plane
                         for plane in range(4)) for pixel in range(1600))
    assert (args.source / "map-object-first-58-after.idx").read_bytes() == expected
    assert len((args.source / "map-object-first-58-before.idx").read_bytes()) == 1600
    calls = [json.loads(line) for line in (args.source / "map-object-calls.jsonl").read_text().splitlines()]
    assert calls
    for call in calls:
        assert call["record"] == 58 and call["raw_sha256"] == RECORD_SHA
        assert (call["segment"], call["entry"], call["return"], call["abi_bytes_matched"]) == (0x14D2, 0x76F, 0x854, 230)
        assert call["mode"] == 1 and call["return_step"] > call["entry_step"]
        assert call["source"] == {"Seg": 0x7000, "Off": 58 * 1004}
        assert call["dest"] in (0xA000, 0xA400)
        assert call["first"] == (call["dest"] - 0xA000) * 16 + call["y"] * 80 + call["x_byte"]
    primary, mapping = read(args.ida_query), read(args.ida_map_query)
    for query in (primary, mapping):
        assert query["input_sha256"] == PAM_SHA and query["database_sha256"] == sha(args.database)
        assert query["uid"] == 1000 and query["tool"] == "IDA 9.4" and query["function_count"] == 521
    # IDA MZ base 0x1000 is distinct from dosgolem's runtime load segment 0x0110.
    assert pam[:2] == b"MZ"
    loaded = bytearray(pam)
    header, count, table = struct.unpack_from("<H", pam, 8)[0] * 16, struct.unpack_from("<H", pam, 6)[0], struct.unpack_from("<H", pam, 0x18)[0]
    for index in range(count):
        offset, segment = struct.unpack_from("<HH", pam, table + index * 4)
        at = header + segment * 16 + offset
        struct.pack_into("<H", loaded, at, (struct.unpack_from("<H", pam, at)[0] + 0x1000) & 65535)
    checked = 0
    for function in primary["functions"] + [mapping["function"]]:
        for line in function["lines"]:
            binary = bytes.fromhex(line["bytes"])
            assert loaded[line["file_offset"]:line["file_offset"] + len(binary)] == binary, (function["name"], line["ea"])
            checked += len(binary)
    function = mapping["function"]
    assert function["name"] == "sub_13AEC" and function["start"] == 0x13AEC
    assert any(line["ea"] == 0x13B35 and line["bytes"] == "2d3000" for line in function["lines"])
    jump = mapping["jump_table"]
    assert jump["ea"] == 0x125F0 and jump["index_subtract"] == 53 and jump["entry_count"] == 13
    raw_table = bytes.fromhex(jump["bytes"])
    assert pam[jump["file_offset"]:jump["file_offset"] + 26] == raw_table
    assert struct.unpack_from("<H", raw_table, (59 - 53) * 2)[0] == 0x25E4
    dispatch = next(f for f in primary["functions"] if f["name"] == "sub_12446")
    dispatch_lines = {line["ea"]: line for line in dispatch["lines"]}
    for address, binary in {
        0x1245C: "b80400", 0x1245F: "50", 0x12460: "50",
        0x12462: "e88716", 0x12468: "8946f0", 0x1257B: "8b46f0",
        0x1257E: "2d3500", 0x12581: "3d0c00", 0x12589: "03c0",
        0x1258B: "93", 0x1258C: "2effa7f025", 0x125E4: "0e",
    }.items():
        assert dispatch_lines[address]["bytes"] == binary
    assert 0x12462 + 3 + struct.unpack_from("<h", bytes.fromhex(dispatch_lines[0x12462]["bytes"]), 1)[0] == 0x13AEC
    call = next(line for line in dispatch["lines"] if line["ea"] == 0x125E5)
    binary = bytes.fromhex(call["bytes"])
    assert binary[0] == 0xE8 and 0x125E5 + 3 + struct.unpack_from("<h", binary, 1)[0] == 0x120B0
    text = "你得到一個寶箱".encode("big5")
    at = pam.index(text)
    assert at == 0x22FDE and at - 0x1EBF0 == 0x43EE
    chest = next(f for f in primary["functions"] if f["name"] == "sub_120B0")
    assert sum(line["bytes"] == "b8ee43" for line in chest["lines"]) == 3
    chest_lines = {line["ea"]: line for line in chest["lines"]}
    assert chest_lines[0x1212F]["bytes"] == "b8ee43"
    assert chest_lines[0x12132]["bytes"] == "50"
    render_call = bytes.fromhex(chest_lines[0x12133]["bytes"])
    assert render_call[0] == 0x9A
    assert struct.unpack_from("<H", render_call, 3)[0] * 16 + struct.unpack_from("<H", render_call, 1)[0] == 0x24703
    assert 107 - 49 == 58 and 107 - 48 == 59
    inputs = 0
    for line in (args.build / "build-inputs.sha256").read_text().splitlines():
        digest, name = line.split("  ", 1)
        assert sha(args.build / "src" / name) == digest
        inputs += 1
    assert inputs == 45
    digest, name = (args.build / "build-outputs.sha256").read_text().split()
    assert name == "probe" and sha(args.build / name) == digest
    result = dict(schema=1, status="normal-source-and-static-chest-identity-verified",
                  scope="PMAP 58 rendering source only; reaching/opening chest and rewards not dynamically verified",
                  input_sha256=PAM_SHA, pmap_sha256=PMAP_SHA, probe_sha256=digest, build_inputs=inputs,
                  frames_each=1084, total_frame_purity=2168, checkpoints=len(shots),
                  scratch_files=len(scratch), scratch_sha256=scratch, source_calls=len(calls), indexed_pixels=1600,
                  equal=equal, identity=dict(level="confirmed static dataflow", native_record=58,
                                          terrain_ascii=107, interaction_value=59, query_bytes_checked=checked,
                                          tile_reader="IDA MZ linear sub_13AEC / 0x13B35 subtract 0x30",
                                          dispatch="IDA MZ linear 0x1258C; case59 table word 0x25E4 at 0x125FC",
                                          message_function="IDA MZ linear sub_120B0", text_file_offset=at,
                                          text_ds_offset=0x43EE, text="你得到一個寶箱",
                                          database_sha256=sha(args.database)))
    if args.prototype:
        result["prototype"] = prototype(args)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in
                      ("status", "frames_each", "total_frame_purity", "source_calls", "scratch_files", "indexed_pixels")}))


if __name__ == "__main__":
    main()
