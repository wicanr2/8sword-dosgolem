"""042：核對唯讀遭遇掛點與有界正常等待。此收據不證明戰場動作完成。Docker only。"""
import argparse
import collections
import hashlib
import json
import struct
from pathlib import Path


def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for part in iter(lambda: f.read(4194304), b""):
            h.update(part)
    return h.hexdigest()


def read(p):
    return json.loads(p.read_text())


def files(p):
    return {str(f.relative_to(p)): sha(f) for f in p.rglob("*") if f.is_file()}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ["pam", "database", "ida-report", "build", "observed", "control", "out"]:
        ap.add_argument("--" + name, type=Path, required=True)
    a = ap.parse_args()
    assert not a.out.exists()
    source = a.pam.read_bytes()
    assert sha(a.pam) == "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"
    assert sha(a.database) == "a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac"
    ida = read(a.ida_report)
    assert ida["tool"] == "IDA 9.4" and ida["uid"] == 1000 and ida["function_count"] == 521
    assert ida["input_sha256"] == sha(a.pam) and ida["database_sha256"] == sha(a.database)
    assert [v["ds_offset"] for v in ida["anchors"]] == [17749, 17786]
    assert {(v["ea"], v["function"]) for v in ida["operand_hits"]} == {(0x11644, 0x1151c), (0x116e8, 0x1151c)}
    f = next(v for v in ida["functions"] if v["start"] == 0x1151c)
    assert f["name"] == "sub_1151C" and f["end"] == 0x11796
    header = struct.unpack_from("<H", source, 8)[0] * 16
    count, table = struct.unpack_from("<H", source, 6)[0], struct.unpack_from("<H", source, 24)[0]
    analysis_load = (f["lines"][0]["ea"] - f["lines"][0]["file_offset"] + header) // 16
    assert analysis_load == 0x1000
    analysis_bytes = bytearray(source)
    for i in range(count):
        off, seg = struct.unpack_from("<HH", source, table + i * 4)
        at = header + seg * 16 + off
        struct.pack_into("<H", analysis_bytes, at, (struct.unpack_from("<H", analysis_bytes, at)[0] + analysis_load) & 65535)
    for function in ida["functions"]:
        for row in function["lines"]:
            code = bytes.fromhex(row["bytes"])
            assert analysis_bytes[row["file_offset"]:row["file_offset"] + len(code)] == code
    prefix = read(a.observed / "encounter-hook-prefixes.json")
    assert prefix["pam_sha256"] == sha(a.pam)
    assert prefix["ida_original_name"] == "sub_1151C" and prefix["ida_linear"] == 0x1151c
    assert prefix["runtime_segment"] == prefix["module_load_paragraph"] == 0x110
    assert prefix["runtime_offset"] == 0x151c and prefix["bytes_matched"] == 634
    relocated = bytearray(source)
    for i in range(count):
        off, seg = struct.unpack_from("<HH", source, table + i * 4)
        at = header + seg * 16 + off
        struct.pack_into("<H", relocated, at, (struct.unpack_from("<H", relocated, at)[0] + 0x110) & 65535)
    at = header + 0x151c
    assert prefix["file_offset"] == at == 0x298c
    assert bytes.fromhex(prefix["bytes"]) == relocated[at:at + 634]
    for name in ["final.state", "audio.pcm", "commands.jsonl", "presentation.frames.gz"]:
        assert sha(a.observed / name) == sha(a.control / name), name
    assert files(a.observed / "scratch") == files(a.control / "scratch")
    for p in a.observed.glob("*.png"):
        assert sha(p) == sha(a.control / p.name)
    statuses = [read(p / "final.json") for p in [a.observed, a.control]]
    for s in statuses:
        assert s["recorded_frames"] == s["frame_pure_count"] == 1310
        assert s["normal_input_replay"] and not s["snapshot_loaded"] and not s["guest_injection"]
        assert s["exited"] and s["exit_code"] == 0
        assert not s["text"]["MissingGlyphs"] and not s["text"]["Errors"]
        assert not any(v for k, v in s.items() if k.endswith("_error"))
    for name in ["steps", "input_events", "strings", "file_ops", "exec_log", "clock_baseline", "rng_seed"]:
        assert statuses[0][name] == statuses[1][name], name
    commands = [read_line["command"] for read_line in map(json.loads, (a.observed / "commands.jsonl").read_text().splitlines())]
    assert commands.count("key 0x39 100 300") == 128 and commands[0] == "key 0x50 100 600"
    rows = list(map(json.loads, (a.observed / "encounter-gate.jsonl").read_text().splitlines()))
    assert collections.Counter(v["role"] for v in rows) == {"entry": 129, "random-quotient": 129}
    for i in range(129):
        entry, result = rows[i * 2:i * 2 + 2]
        assert entry["entry_serial"] == result["entry_serial"] == i + 1
        assert entry["cs"] == result["cs"] == 0x110 and entry["ds"] == result["ds"] == 0x1e88
        assert entry["ip"] == 0x151c and result["ip"] == 0x1558 and entry["step"] < result["step"]
        assert entry["words_by_ds_offset"]["04f2"] == result["words_by_ds_offset"]["04f2"] == 1
        assert result["ax"] == result["words_by_ds_offset"]["56e0"] != 1
    assert not (a.observed / "battle-source-calls.jsonl").read_bytes()
    for line in (a.build / "build-inputs.sha256").read_text().splitlines():
        digest, name = line.split(None, 1)
        assert sha(a.build / "src" / name) == digest
    report = dict(schema=1, status="passed-readonly-gate-location-and-isolation", tool=ida["tool"],
                  input_sha256=sha(a.pam), database_sha256=sha(a.database),
                  ida_function="sub_1151C", ida_linear=0x1151c, ida_load_paragraph=analysis_load, file_offset=at,
                  ida_functions_verified=[v["name"] for v in ida["functions"]],
                  runtime_cs_ip="0110:151c", relocated_bytes_matched=634,
                  frames_per_run=1310, total_frame_purity=2620, gate_calls=129,
                  wait_keys=128, quotient_one_events=0, normal_encounter_acquired=False,
                  friendly_pose_records_verified=[], production_ready=False,
                  scratch_files=len(files(a.observed / "scratch")),
                  state_sha256=sha(a.observed / "final.state"), pcm_sha256=sha(a.observed / "audio.pcm"),
                  clock_baseline=statuses[0]["clock_baseline"], rng_seed=statuses[0]["rng_seed"],
                  quotient_distribution=dict(sorted(collections.Counter(v["ax"] for v in rows if v["role"] == "random-quotient").items())),
                  probe_sha256=sha(a.build / "probe"), ida_script_sha256=sha(a.ida_report.with_suffix(".py")),
                  verifier_sha256=sha(Path(__file__)))
    a.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
