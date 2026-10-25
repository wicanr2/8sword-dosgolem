#!/usr/bin/env python3
"""006／045：核對普通世界探索的只讀觀測隔離與 PMAP 返回，不宣稱 HD Draw 驗收。"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import struct
import tarfile

PMAP_SHA = "9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02"
PAM_SHA = "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text())


def files(path):
    return {p.name:sha(p) for p in path.iterdir() if p.is_file()}


def frame_count(path):
    count, last_step = 0, 0
    with gzip.open(path, "rb") as stream:
        def exact(n):
            value = stream.read(n)
            assert len(value) == n
            return value
        assert exact(8) == b"8SFRM001"
        width, height = struct.unpack("<II", exact(8))
        assert (width,height) == (1920,1200)
        while raw := stream.read(24):
            assert len(raw) == 24
            ordinal, step, rows = struct.unpack("<QQQ",raw)
            assert ordinal == count+1 and step >= last_step and rows <= height
            assert count or rows == height
            seen = set()
            for _ in range(rows):
                y, = struct.unpack("<H",exact(2))
                assert y < height and y not in seen
                seen.add(y)
                exact(width*4)
            count, last_step = ordinal, step
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("original", "source", "control", "build", "out"):
        parser.add_argument("--"+name, type=Path, required=True)
    parser.add_argument("--require-records", type=int, nargs="+", required=True)
    a = parser.parse_args()
    assert not a.out.exists()
    pm = (a.original/"PMAP.AY").read_bytes()
    assert hashlib.sha256(pm).hexdigest() == PMAP_SHA and sha(a.original/"PAM.AY") == PAM_SHA
    source, control = [read(root/"final.json") for root in (a.source,a.control)]
    commands = [json.loads(line)["command"] for line in (a.source/"commands.jsonl").read_text().splitlines()]
    assert commands[-1] == "quit"
    font_frames = sum(command.startswith("font ") for command in commands)
    # probe-world.go records an additional Frame for each explicit font command.
    count = source["elapsed_ms"]//50 + font_frames
    keys = ("steps", "strings", "input_events", "file_ops", "exec_log", "music", "elapsed_ms",
            "irq1_delivered", "bios_consumed", "clock_baseline", "rng_seed")
    for d in (source,control):
        assert d["exited"] and d["exit_code"] == 0
        assert d["normal_input_replay"] and not d["snapshot_loaded"] and not d["guest_injection"]
        assert d["recorded_frames"] == d["frame_pure_count"] == count > 0
    assert all(source[k] == control[k] for k in keys)
    equal = {}
    for name in ("final.state", "frame-check.state", "audio.pcm", "commands.jsonl", "frames.jsonl", "presentation.frames.gz"):
        assert sha(a.source/name) == sha(a.control/name), name
        equal[name] = sha(a.source/name)
    assert frame_count(a.source/"presentation.frames.gz") == frame_count(a.control/"presentation.frames.gz") == count
    scratch = files(a.source/"scratch")
    assert scratch == files(a.control/"scratch")
    assert (a.source/"scratch/gamedata.ay").stat().st_size == 2987
    checkpoints = sorted(a.source.glob("*-native.png"))
    assert checkpoints
    for path in checkpoints:
        for suffix in ("-native.png", "-hd.png"):
            name = path.name.removesuffix("-native.png")+suffix
            assert sha(a.source/name) == sha(a.control/name), name
        name = path.name.removesuffix("-native.png")+".json"
        left, right = read(a.source/name), read(a.control/name)
        assert all(left[k] == right[k] for k in keys[:-2]), name
    calls = [json.loads(line) for line in (a.source/"map-object-calls.jsonl").read_text().splitlines()]
    observed = sorted({c["record"] for c in calls})
    assert set(a.require_records) <= set(observed)
    for c in calls:
        index = c["record"]
        assert index in set(range(30,45)) | {48,49,51}
        assert c["raw_sha256"] == hashlib.sha256(pm[index*1004:(index+1)*1004]).hexdigest()
        assert c["segment"] == 0x14d2 and c["entry"] == 0x76f and c["return"] == 0x854
        assert c["abi_bytes_matched"] == 230 and c["return_step"] > c["entry_step"] and c["mode"] == 1
    for index in observed:
        raw = (a.source/f"map-object-first-{index}-source.bin").read_bytes()
        assert raw == pm[index*1004:(index+1)*1004]
        native = bytes(sum(((raw[4+q*200+i//8]>>(7-i%8))&1)<<q for q in range(4)) for i in range(1600))
        assert (a.source/f"map-object-first-{index}-after.idx").read_bytes() == native
    inputs = {}
    for line in (a.build/"build-inputs.sha256").read_text().splitlines():
        digest, name = line.split("  ",1)
        assert sha(a.build/"src"/name) == digest
        inputs[name] = digest
    assert len(inputs) == 51
    with tarfile.open(a.build/"source.tar.gz") as archive:
        assert all(hashlib.sha256(archive.extractfile("src/"+name).read()).hexdigest() == digest for name,digest in inputs.items())
    digest, name = (a.build/"build-outputs.sha256").read_text().split()
    assert name == "probe" and sha(a.build/name) == digest
    result = dict(status="verified-normal-world-source-isolation", frames_each=count, total_frame_purity=count*2,
                  font_command_extra_frames=font_frames, complete_lossless_streams=True,
                  equal=equal, checkpoints=len(checkpoints), scratch_sha256=scratch,
                  observed_records=observed, source_calls=len(calls), first_indexed_pixels=1600*len(observed),
                  build_inputs=51, probe_sha256=digest, save_sha256=scratch["gamedata.ay"],
                  tool_sha256=sha(Path(__file__)), python_version=sys.version.split()[0],
                  scope="normal original exploration and read-only observer only; no new HD actualDraw or cold-save claim")
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:result[k] for k in ("status","frames_each","observed_records","source_calls","save_sha256")}))


if __name__ == "__main__":
    main()
