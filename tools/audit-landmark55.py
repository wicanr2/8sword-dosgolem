#!/usr/bin/env python3
"""045：核對第55筆正式呈現、原版來源、狀態隔離與獨立完整畫面。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

PAM_SHA = "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"
PMAP_SHA = "9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02"
RECORD_SHA = "18f01693acca18d6f4254c7f3a14bf1d7e9bff0fa4bca45d5c288a1432d94069"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text())


def files(path):
    return {p.name: sha(p) for p in path.iterdir() if p.is_file()}


def verify(args):
    from PIL import Image

    assert all((args.assets, args.image, args.control, args.broken, args.build))
    assert sha(args.image) == "55e20818bf365b1d892ecce5ec2bf7eadaffba952635f890cc94c0bf2a107cdc"
    image = Image.open(args.image)
    assert image.size == (1419, 1108) and image.mode == "RGBA"
    assert image.getchannel("A").getextrema() == (0, 255)
    spec = importlib.util.spec_from_file_location("landmark55_independent_frame", Path(__file__).with_name("audit-encounter-gui.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    model = module.Model(args.assets, args.original, args.hd)
    tile = module.sample(args.image, 192, 150, actor=True, background=model.material(1)[0])
    assert len(tile) == 192 * 150 * 4
    model.materials[56] = tile, 64, 25
    reference, candidate, broken = [read(p / "final.json") for p in (args.control, args.hd, args.broken)]
    assert reference["graphics_materials"] == broken["graphics_materials"] == 64
    assert candidate["graphics_materials"] == 65
    error_key = "map_landmark_error"
    assert not reference[error_key] and not candidate[error_key]
    assert broken[error_key] == "地圖物件55圖片 SHA-256 不符"
    for data in (reference, candidate, broken):
        assert data["recorded_frames"] == data["frame_pure_count"] == 395
        assert data["normal_input_replay"] and not data["snapshot_loaded"] and not data["guest_injection"]
        assert data["exited"] and data["exit_code"] == 0
        for key in ("steps", "exit_code", "exited", "input_events", "file_ops", "exec_log",
                    "music", "elapsed_ms", "strings", "irq1_delivered", "bios_consumed"):
            assert data[key] == reference[key], key
    equal = {}
    for name in ("final.state", "frame-check.state", "audio.pcm", "commands.jsonl", "frames.jsonl"):
        digest = sha(args.control / name)
        assert sha(args.hd / name) == sha(args.broken / name) == digest, name
        equal[name] = digest
    assert sha(args.control / "presentation.frames.gz") == sha(args.broken / "presentation.frames.gz")
    # Decode every actual output frame independently; differences must stay in the observed source rectangle.
    spec = importlib.util.spec_from_file_location("landmark55_stream", Path(__file__).with_name("audit-army-dismiss.py"))
    streaming = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(streaming)
    from PIL import ImageChops
    changed = 0
    for left, right in zip(streaming.stream(args.control), streaming.stream(args.hd), strict=True):
        assert left[:2] == right[:2]
        bbox = ImageChops.difference(left[2].convert("RGB"), right[2].convert("RGB")).getbbox()
        if bbox:
            assert bbox[0] >= 1176 and bbox[1] >= 72 and bbox[2] <= 1368 and bbox[3] <= 222, (left[0],bbox)
            changed += 1
    assert changed > 0
    scratch = files(args.control / "scratch")
    assert files(args.hd / "scratch") == files(args.broken / "scratch") == scratch
    assert len(scratch) == 22
    shots = sorted(args.control.glob("*-native.png"))
    assert len(shots) == 6
    for path in shots:
        assert sha(args.hd / path.name) == sha(args.broken / path.name) == sha(path)
    for name in ("05-west-hd.png", "07-F1-hd.png", "08-F2-hd.png"):
        assert sha(args.control / name) == sha(args.hd / name) == sha(args.broken / name), name
    for path in args.control.glob("*.png"):
        assert sha(path) == sha(args.broken / path.name), path.name
    packets = sorted(args.hd.glob("*-model.json"))
    assert len(packets) == 5
    results = [model.frame(p.with_suffix("")) for p in packets]
    assert {r["font_id"] for r in results} == {"noto", "lishu", "caoshu"}
    assert all(r["height"] == 25 for r in results)
    assert all(56 in r["material_ids"] for r in results)
    for data, root in ((reference, args.control), (candidate, args.hd), (broken, args.broken)):
        calls = [json.loads(line) for line in (root / "map-object-calls.jsonl").read_text().splitlines()]
        assert calls and all(c["raw_sha256"] == RECORD_SHA for c in calls)
        raw = (root / "map-object-first-55-source.bin").read_bytes()
        assert hashlib.sha256(raw).hexdigest() == RECORD_SHA
        expected = bytes(sum(((raw[4 + q * 200 + p // 8] >> (7-p%8)) & 1) << q
                             for q in range(4)) for p in range(1600))
        assert (root / "map-object-first-55-after.idx").read_bytes() == expected
    build_inputs = 0
    for line in (args.build / "build-inputs.sha256").read_text().splitlines():
        digest, name = line.split("  ", 1)
        assert sha(args.build / "src" / name) == digest
        build_inputs += 1
    assert build_inputs == 52
    outputs = {}
    for line in (args.build / "build-outputs.sha256").read_text().splitlines():
        digest, name = line.split()
        assert sha(args.build / name) == digest
        outputs[name] = digest
    assert len(outputs) == 3 and "probe" in outputs
    assert not any("ResearchInstall" in p.read_text() for p in (args.build / "src").rglob("*.go"))
    return dict(status="passed-production-loader", frames_each=395, total_frame_purity=1185,
                build_inputs=build_inputs, probe_sha256=outputs["probe"], cache_sha256=hashlib.sha256(tile).hexdigest(),
                full_frames=results, equal=equal, scratch_sha256=scratch,
                broken_stream_equal=True, unaffected_pages_equal=True, changed_frames=changed,
                changed_rectangle=[1176,72,1368,222],
                limitation="headless normal Continue, original source, independent PNG/font reconstruction and original F7 save; GUI and saved RAM/cold reload remain unverified")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("assets","original","image","control","hd","broken","build","out"):
        p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args()
    assert not a.out.exists()
    result=verify(a)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:result[k] for k in ("status","frames_each","total_frame_purity","cache_sha256")}))

if __name__=="__main__":main()
