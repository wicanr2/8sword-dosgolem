#!/usr/bin/env python3
"""045：核對第52／56筆正常來源、觀測隔離、真正存讀與位置原型。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from PIL import Image
import PIL

PMAP_SHA = "9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02"
PAM_SHA = "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"
ART = {
    52: ("bfa21fb69c92918d2a27380077153377dbba5d5d84f1a3d1dac6c7ab85fc7e83", "8147efffe2e0f26f26295391bdd1b2a3e5db621539ee55cc65ed2b48c9e2a6c8"),
    56: ("7188d67ebf710df40d2adfcaa520d21c1f9781008748a214a497629c2b0a542d", "412af4cb89b40adc1b0b56b2b5605fd016918b51712a081a4cea01938d0e9fd4"),
}
EGA = [(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),(170,85,0),(170,170,170),(85,85,85),(85,85,255),(85,255,85),(85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text())


def files(path):
    return {p.name:sha(p) for p in path.iterdir() if p.is_file()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("original", "assets", "source", "control", "reload", "build", "art", "saved-inspection", "loaded-inspection", "out"):
        p.add_argument("--"+name, type=Path, required=True)
    p.add_argument("--record", type=int, choices=[52,56], required=True)
    p.add_argument("--scene", required=True, help="正常目標畫面檔名前綴，不含 -hd.png")
    a = p.parse_args()
    assert not a.out.exists() and Path(a.scene).name == a.scene
    pm = (a.original/"PMAP.AY").read_bytes()
    assert hashlib.sha256(pm).hexdigest() == PMAP_SHA and sha(a.original/"PAM.AY") == PAM_SHA
    source, control = [read(root/"final.json") for root in (a.source,a.control)]
    frames = source["elapsed_ms"]//50
    for d in (source,control):
        assert frames > 0 and d["recorded_frames"] == d["frame_pure_count"] == frames
        assert d["normal_input_replay"] and not d["snapshot_loaded"] and not d["guest_injection"]
        assert d["exited"] and d["exit_code"] == 0
    keys = ("steps", "strings", "input_events", "file_ops", "exec_log", "music", "elapsed_ms", "irq1_delivered", "bios_consumed", "clock_baseline", "rng_seed")
    for key in keys:
        assert source[key] == control[key], key
    equal = {}
    for name in ("final.state", "frame-check.state", "audio.pcm", "commands.jsonl", "frames.jsonl", "presentation.frames.gz"):
        assert sha(a.source/name) == sha(a.control/name), name
        equal[name] = sha(a.source/name)
    scratch = files(a.source/"scratch")
    assert len(scratch) == 22 and scratch == files(a.control/"scratch")
    checkpoints = sorted(a.source.glob("*-native.png"))
    assert checkpoints
    for path in checkpoints:
        for name in (path.name, path.name.replace("-native.png", "-hd.png")):
            assert sha(a.source/name) == sha(a.control/name), name
        name = path.name.replace("-native.png", ".json")
        left, right = read(a.source/name), read(a.control/name)
        for key in keys[:-2]:
            assert left[key] == right[key], (name,key)
    calls = [json.loads(line) for line in (a.source/"map-object-calls.jsonl").read_text().splitlines()]
    selected = [c for c in calls if c["record"] == a.record]
    assert selected
    for call in calls:
        index = call["record"]
        assert index in [48,49,51,52,54,55,56]
        assert call["raw_sha256"] == hashlib.sha256(pm[index*1004:(index+1)*1004]).hexdigest()
        assert call["segment"] == 0x14D2 and call["entry"] == 0x76F and call["return"] == 0x854
        assert call["abi_bytes_matched"] == 230 and call["return_step"] > call["entry_step"] and call["mode"] == 1
    inputs = {}
    for line in (a.build/"build-inputs.sha256").read_text().splitlines():
        digest, name = line.split("  ",1)
        assert sha(a.build/"src"/name) == digest
        inputs[name] = digest
    assert len(inputs) == 49
    digest, name = (a.build/"build-outputs.sha256").read_text().split()
    assert name == "probe" and sha(a.build/name) == digest
    saved = a.source/"scratch/gamedata.ay"
    assert saved.stat().st_size == 2987
    for inspection in (a.saved_inspection,a.loaded_inspection):
        assert sha(inspection/"save-buffer-9e000.bin") == sha(saved)
    loaded = read(a.reload/"final.json")
    assert loaded["exited"] and loaded["exit_code"] == 0 and loaded["recorded_frames"] == 312
    reads = [op for op in loaded["file_ops"] if op["Op"] == "read" and op["Name"].lower() == "gamedata.ay" and op["Len"] == 2987 and not op["Failed"]]
    assert reads and sha(a.reload/"scratch/gamedata.ay") == sha(saved)
    assert sha(a.reload/"scratch/map01.ay") == sha(a.source/"scratch/map01.ay")
    record = pm[a.record*1004:(a.record+1)*1004]
    assert (a.source/f"map-object-first-{a.record}-source.bin").read_bytes() == record
    native = bytes(sum(((record[4+q*200+i//8]>>(7-i%8))&1)<<q for q in range(4)) for i in range(1600))
    assert (a.source/f"map-object-first-{a.record}-after.idx").read_bytes() == native
    status = read(a.source/(a.scene+".json"))
    call = max((c for c in selected if c["return_step"] <= status["steps"]), key=lambda c:c["return_step"])
    x, y = call["x_byte"]*24, call["y"]*6
    box = (x,y,x+192,y+150)
    scene = Image.open(a.source/(a.scene+"-hd.png")).convert("RGBA")
    rgb = bytes(v for c in native for v in EGA[c])
    expected = Image.frombytes("RGB",(64,25),rgb).resize((192,150),Image.Resampling.NEAREST)
    assert scene.crop(box).convert("RGB").tobytes() == expected.tobytes()
    image = a.art/f"pmap-{a.record}-painted-r1.png"
    assert sha(image) == ART[a.record][0]
    im = Image.open(image)
    assert im.size == (1419,1108) and im.mode == "RGBA" and im.getchannel("A").getextrema() == (0,255)
    spec = importlib.util.spec_from_file_location("pending_sampling",Path(__file__).with_name("audit-encounter-gui.py"))
    sampling = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sampling)
    model = sampling.Model(a.assets,a.original,a.art)
    tile = sampling.sample(image,192,150,actor=True,background=model.material(1)[0])
    assert hashlib.sha256(tile).hexdigest() == ART[a.record][1]
    assert tile == (a.art/f"pmap-{a.record}-prototype-cache-r1.rgba").read_bytes()
    scene.paste(Image.frombytes("RGBA",(192,150),tile),(x,y))
    prototype = a.art/f"normal-scene-prototype-{a.record}-r1.png"
    if prototype.exists():
        assert Image.open(prototype).convert("RGBA").tobytes() == scene.tobytes()
    else:
        scene.save(prototype)
    result = dict(status="normal-pending-source-art-verified", record=a.record, source_file="PMAP.AY", source_sha256=PMAP_SHA,
                  pam_sha256=PAM_SHA, frames_each=frames, total_frame_purity=frames*2, equal=equal, checkpoints=len(checkpoints), scratch_files=22,
                  total_source_calls=len(calls), selected_source_calls=len(selected), first_source_call=read(a.source/f"map-object-first-{a.record}-call.json"),
                  indexed_pixels=1600, native_sha256=hashlib.sha256(record[:804]).hexdigest(), record_sha256=hashlib.sha256(record).hexdigest(),
                  image_sha256=sha(image), prompt_sha256=sha(a.art/f"pmap-{a.record}-painted-r1.prompt.txt"), cache_sha256=ART[a.record][1], layout_box=box,
                  build_inputs=49, probe_sha256=digest, pillow_version=PIL.__version__, save_sha256=sha(saved), map_sha256=sha(a.source/"scratch/map01.ay"),
                  reload_frames=312, original_read_step=reads[0]["Step"], saved_loaded_ram_equal=True,
                  scope="normal source and disposable layout/art only; new formal materials and actual Draws remain unverified")
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:result[k] for k in ("status","record","frames_each","selected_source_calls","save_sha256")}))


if __name__ == "__main__":
    main()
