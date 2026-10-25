#!/usr/bin/env python3
"""042：核對正常攻城來源與唯讀觀測隔離。Docker only。"""
import argparse
import collections
import hashlib
import json
import struct
import tarfile
from pathlib import Path

PAM_SHA = "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"
DB_SHA = "a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac"
MAN21_SHA = "47cc484319abeba53551c20b7cf4b9b2c6061f2da3b6cda14155b3598f10982c"


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def files(path):
    return {str(p.relative_to(path)): sha(p) for p in path.rglob("*") if p.is_file()}


def mirror(raw):
    reverse = bytes(int(f"{v:08b}"[::-1], 2) for v in range(256))
    return raw[:4] + b"".join(raw[i:i + 11][::-1].translate(reverse) for i in range(4, 3304, 11))


def verify_ida(report, source):
    assert report["tool"] == "IDA 9.4" and report["uid"] == 1000 and report["function_count"] == 521
    assert report["input_sha256"] == PAM_SHA and report["database_sha256"] == DB_SHA
    data = bytearray(source)
    header = struct.unpack_from("<H", source, 8)[0] * 16
    count = struct.unpack_from("<H", source, 6)[0]
    table = struct.unpack_from("<H", source, 24)[0]
    for index in range(count):
        off, seg = struct.unpack_from("<HH", source, table + index * 4)
        at = header + seg * 16 + off
        struct.pack_into("<H", data, at, (struct.unpack_from("<H", data, at)[0] + 0x1000) & 65535)
    for function in report["functions"]:
        for row in function["lines"]:
            code = bytes.fromhex(row["bytes"])
            assert data[row["file_offset"]:row["file_offset"] + len(code)] == code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("original", "database", "ida", "bitmap-ida", "build", "observed", "control", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    a = parser.parse_args()
    assert not a.out.exists()
    assert sha(a.original / "PAM.AY") == PAM_SHA and sha(a.database) == DB_SHA
    assert sha(a.original / "MAN21.EGG") == MAN21_SHA
    source = (a.original / "PAM.AY").read_bytes()
    ida, bitmap_ida = read(a.ida), read(a.bitmap_ida)
    for report in (ida, bitmap_ida):
        verify_ida(report, source)
    castle = next(f for f in ida["functions"] if f["start"] == 0x12dde)
    assert castle["name"] == "sub_12DDE" and castle["end"] == 0x132b3
    question = next(row for row in castle["lines"] if row["ea"] == 0x12fa0)
    assert question["file_offset"] == 0x4410 and question["bytes"] == "b83045"
    bitmap = bitmap_ida["functions"]
    assert len(bitmap) == 1 and bitmap[0]["start"] == 0x24246 and bitmap[0]["end"] == 0x2438f
    assert bitmap[0]["lines"][0]["file_offset"] == 0x156b6
    assert [(r["ea"], r["file_offset"]) for r in bitmap[0]["lines"] if r["instruction"].strip() == "retf"] == [(0x2438e, 0x157fe)]
    inputs = {}
    for line in (a.build / "build-inputs.sha256").read_text().splitlines():
        digest, name = line.split("  ", 1)
        assert sha(a.build / "src" / name) == digest
        inputs[name] = digest
    assert len(inputs) == 52
    with tarfile.open(a.build / "source.tar.gz", "r:gz") as archive:
        archived = {member.name.removeprefix("src/"): hashlib.sha256(archive.extractfile(member).read()).hexdigest() for member in archive.getmembers() if member.isfile()}
    assert archived == inputs
    production = [name for name in inputs if name.startswith("internal/eightsword/")]
    assert len(production) == 49
    for name in production:
        assert sha(Path(__file__).resolve().parent.parent / name) == inputs[name], name
    digest, name = (a.build / "build-outputs.sha256").read_text().split()
    assert name == "probe" and sha(a.build / name) == digest
    finals = [read(root / "final.json") for root in (a.observed, a.control)]
    for final in finals:
        assert final["normal_input_replay"] and not final["snapshot_loaded"] and not final["guest_injection"]
        assert final["exited"] and final["exit_code"] == 0 and not final["unimplemented"]
        assert final["frame_pure_count"] == final["recorded_frames"] > 0
        assert not final["text"]["MissingGlyphs"] and not final["text"]["Errors"]
        assert not any(value for key, value in final.items() if key.endswith("_error"))
    for key in ("steps", "strings", "input_events", "file_ops", "exec_log", "music", "elapsed_ms", "irq1_delivered", "bios_consumed", "clock_baseline", "rng_seed", "recorded_frames", "frame_pure_count"):
        assert finals[0][key] == finals[1][key], key
    equal = {}
    for name in ("final.state", "frame-check.state", "audio.pcm", "commands.jsonl", "frames.jsonl", "presentation.frames.gz", "continued-game.json", "continued-companions.json"):
        assert sha(a.observed / name) == sha(a.control / name), name
        equal[name] = sha(a.observed / name)
    scratch = files(a.observed / "scratch")
    assert scratch == files(a.control / "scratch")
    assert (a.observed / "scratch/gamedata.ay").stat().st_size == 2987
    for name in ("map01.ay", "map02.ay"):
        assert (a.observed / "scratch" / name).stat().st_size == 5761
    checkpoints = sorted(a.observed.glob("*-native.png"))
    assert checkpoints
    questions = {}
    for path in checkpoints:
        for name in (path.name, path.name.replace("-native.png", "-hd.png")):
            assert sha(a.observed / name) == sha(a.control / name), name
        name = path.name.replace("-native.png", ".json")
        left, right = read(a.observed / name), read(a.control / name)
        for string in left["strings"]:
            if string["Source"] == 17712:
                questions[string["Step"]] = string
        for key in ("steps", "strings", "input_events", "file_ops", "exec_log", "music", "elapsed_ms"):
            assert left[key] == right[key], (name, key)
    known = {}
    targets = {}
    originals = sorted(a.original.glob("MAN*.EGG"))
    assert len(originals) == 26
    for path in originals:
        raw = path.read_bytes()
        assert len(raw) == 13216
        for index in range(4):
            record = raw[index * 3304:(index + 1) * 3304]
            assert struct.unpack_from("<HH", record) == (11, 50)
            for direction, data in (("identity", record), ("mirror-six-planes", mirror(record))):
                key = hashlib.sha256(data).hexdigest()
                known.setdefault(key, []).append(f"{path.name}/{index}/{direction}")
                if path.name == "MAN21.EGG" and direction == "mirror-six-planes":
                    targets[key] = (index, data)
    calls, repeated = [], []
    for call in rows(a.observed / "battle-source-calls.jsonl"):
        if call.get("observation") == "repeated-entry-before-instruction":
            assert call["repeated_step"] > call["entry_step"]
            repeated.append(call)
            continue
        assert call["serial"] == len(calls) + 1
        assert call["segment"] == 0x14d2 and call["entry"] == 0x626 and call["return"] == 0x76e
        assert call["abi_bytes_matched"] == 329 and call["return_step"] > call["entry_step"]
        assert sorted(call["catalog"] or []) == sorted(known.get(call["source_sha256"], []))
        calls.append(call)
    records = []
    for key, (index, raw) in sorted(targets.items(), key=lambda item: item[1][0]):
        selected = [c for c in calls if c["source_sha256"] == key]
        if not selected:
            assert not (a.observed / f"ally21-first-{index}-call.json").exists()
            continue
        prefix = a.observed / f"ally21-first-{index}"
        call = read(Path(str(prefix) + "-call.json"))
        assert call == selected[0] and call["target_record"] == index
        assert call["destination_segment"] == 0xa000 and call["mode"] == 1
        assert call["first_physical_byte"] == call["y"] * 80 + call["x_byte"]
        assert (Path(str(prefix) + "-source.bin")).read_bytes() == raw
        before, background, after = [Path(str(prefix) + suffix).read_bytes() for suffix in ("-before.idx", "-background.idx", "-after.idx")]
        assert len(before) == len(background) == len(after) == 4400
        expected = bytearray(background)
        for pixel in range(4400):
            offset, bit = pixel // 8, 7 - pixel % 8
            if raw[4 + 5 * 550 + offset] >> bit & 1:
                expected[pixel] = sum(((raw[4 + plane * 550 + offset] >> bit) & 1) << plane for plane in range(4))
        assert after == expected, index
        records.append(dict(record=index, source_sha256=key, calls=len(selected), pixels_verified=4400, first=call))
    if calls:
        assert len(questions) == 1
        assert any(op["Op"] == "open" and op["Name"].lower() == "gro01.eg" and not op["Failed"] for op in finals[0]["file_ops"])
    result = dict(status="normal-castle-observation-isolation-verified", frames_each=finals[0]["recorded_frames"], total_frame_purity=sum(f["frame_pure_count"] for f in finals), equal=equal, scratch_files=len(scratch), checkpoints=len(checkpoints), build_inputs=len(inputs), production_inputs=len(production), probe_sha256=digest, castle_questions=len(questions), battle_calls=len(calls), repeated_entries=repeated, catalog_counts=dict(collections.Counter(item for call in calls for item in call["catalog"] or [])), friendly_records=records, coverage="four-normal-sources-verified" if len(records) == 4 else "incomplete-source-coverage", production_ready=False, scope="正常原版來源與觀測隔離；不證明 HD 接入、實際 Draw 或存檔冷讀", verifier_sha256=sha(Path(__file__)))
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("status", "frames_each", "battle_calls", "coverage", "production_ready")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
