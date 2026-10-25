#!/usr/bin/env python3
"""045：核對批次美術、正常 PMAP 55 來源及控制前綴，不代替正式 GUI。Docker only。"""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

from PIL import Image


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream,"sha256").hexdigest()


def inventory(path):
    return {p.name:sha(p) for p in path.iterdir() if p.is_file()}


def stream_prefix(source,control):
    digest = hashlib.sha256()
    with gzip.open(source/"presentation.frames.gz","rb") as left, gzip.open(control/"presentation.frames.gz","rb") as right:
        header = left.read(16)
        assert header == right.read(16) and header[:8] == b"8SFRM001"
        width,height = struct.unpack_from("<II",header,8)
        assert (width,height) == (1920,1200)
        digest.update(header)
        count = 0
        while header := left.read(24):
            assert len(header) == 24 and header == right.read(24)
            ordinal,step,rows = struct.unpack("<QQQ",header)
            count += 1
            assert ordinal == count and rows <= height
            digest.update(header)
            for _ in range(rows):
                row = left.read(2)
                assert len(row) == 2 and row == right.read(2) and struct.unpack("<H",row)[0] < height
                data = left.read(width*4)
                assert len(data) == width*4 and data == right.read(width*4)
                digest.update(row+data)
    assert count == 1230
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("original","assets","art","source","control","prefix-control","build","reload","saved-inspection","loaded-inspection","out"):
        parser.add_argument("--"+name,type=Path,required=True)
    a = parser.parse_args()
    assert not a.out.exists()
    source,control,prefix = read(a.source/"final.json"),read(a.control/"final.json"),read(a.prefix_control/"comparison.json")
    assert source["recorded_frames"] == source["frame_pure_count"] == 1230
    assert source["steps"] == prefix["steps"] == 180975745
    assert source["elapsed_ms"] == 61500 and not source["exited"]
    assert control["recorded_frames"] == control["frame_pure_count"]
    assert control["exited"] and control["exit_code"] == 0
    for data in (source,control):
        assert data["normal_input_replay"] and not data["guest_injection"] and not data["snapshot_loaded"]
    assert sha(a.source/"final.state") == sha(a.prefix_control/"frame-check.state")
    for name in ("audio.pcm","commands.jsonl","frames.jsonl"):
        assert sha(a.source/name) == sha(a.prefix_control/name)
    assert len((a.source/"commands.jsonl").read_text().splitlines()) == 84
    assert (a.control/"commands.jsonl").read_bytes().startswith((a.source/"commands.jsonl").read_bytes())
    assert inventory(a.source/"scratch") == prefix["scratch_sha256"] and len(prefix["scratch_sha256"]) == 20
    assert len(inventory(a.control/"scratch")) == 22
    shots = list(a.source.glob("*-hd.png"))
    assert len(shots) == 12
    for path in shots:
        name = path.name.removesuffix("-hd.png")
        for suffix in ("-hd.png","-native.png",".json"):
            assert sha(a.source/(name+suffix)) == sha(a.control/(name+suffix))
    # Strings is a rolling 32-entry diagnostic list. Later F1/F2/F7 legitimately
    # evict the prefix; the 12 identical checkpoint statuses above retain it.
    for key in ("input_events","file_ops"):
        assert control[key][:len(source[key])] == source[key],key
        assert all(e["Step"] >= source["steps"] for e in control[key][len(source[key]):]),key
    paired_stream = stream_prefix(a.source,a.control)
    pmap = (a.original/"PMAP.AY").read_bytes()
    catalog = read(a.art/"catalog.json")
    assert hashlib.sha256(pmap).hexdigest() == catalog["source_sha256"] == "9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02"
    assert sha(a.original/"PAM.AY") == "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"
    raw = (a.source/"map-object-first-55-source.bin").read_bytes()
    assert raw == pmap[55*1004:56*1004] and struct.unpack_from("<HH",raw) == (8,25)
    expected = bytes(sum(((raw[4+q*200+p//8] >> (7-p%8)) & 1) << q for q in range(4)) for p in range(1600))
    assert (a.source/"map-object-first-55-after.idx").read_bytes() == expected
    calls = [json.loads(line) for line in (a.source/"map-object-calls.jsonl").read_text().splitlines()]
    assert len(calls) == 2 and {c["record"] for c in calls} == {55}
    for call in calls:
        assert call["raw_sha256"] == hashlib.sha256(raw).hexdigest() and call["abi_bytes_matched"] == 230
        assert (call["segment"],call["entry"],call["return"],call["mode"]) == (0x14D2,0x76F,0x854,1)
        assert call["return_step"] > call["entry_step"]
    first = read(a.source/"map-object-first-55-call.json")
    assert (first["x_byte"],first["y"],first["dest"],first["first"]) == (49,12,0xA400,17393)
    assert first["source"] == {"Seg":0x7000,"Off":55220}
    inputs = 0
    for line in (a.build/"build-inputs.sha256").read_text().splitlines():
        digest,name = line.split("  ",1)
        assert sha(a.build/"src"/name) == digest
        inputs += 1
    assert inputs == 46
    digest,name = (a.build/"build-outputs.sha256").read_text().split()
    assert name == "probe" and sha(a.build/name) == digest
    spec = importlib.util.spec_from_file_location("landmark_sampling",Path(__file__).with_name("audit-encounter-gui.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    model = module.Model(a.assets,a.original,a.art)
    art = read(a.art/"art-provenance-r1.json")
    assert {e["index"] for e in art["records"]} == {52,54,55,56}
    caches = {}
    for entry in art["records"]:
        path = a.art/entry["file"]
        assert sha(path) == entry["image_sha256"] and sha(a.art/entry["prompt_file"]) == entry["prompt_sha256"]
        image = Image.open(path)
        assert image.size == (1419,1108) and image.mode == "RGBA" and image.getchannel("A").getextrema() == (0,255)
        tile = module.sample(path,192,150,actor=True,background=model.material(1)[0])
        assert tile == (a.art/entry["cache_file"]).read_bytes() and hashlib.sha256(tile).hexdigest() == entry["cache_sha256"]
        caches[entry["index"]] = tile
    # Placement prototype on an observed ordinary frame; it is not a runtime Draw.
    area = (1176,72,1368,222)
    rgba = bytes(v for c in expected for v in module.EGA[c])
    native = Image.frombytes("RGB",(64,25),rgba).resize((192,150),Image.Resampling.NEAREST)
    before = Image.open(a.source/"03-target-visible-hd.png").convert("RGBA")
    assert before.crop(area).convert("RGB").tobytes() == native.tobytes()
    after = before.copy()
    after.paste(Image.frombytes("RGBA",(192,150),caches[55]),area[:2])
    saved = a.control/"scratch/gamedata.ay"
    mapfile = a.control/"scratch/map01.ay"
    assert saved.stat().st_size == 2987 and mapfile.stat().st_size == 5761
    assert sha(saved) != prefix["scratch_sha256"]["gamedata.ay"] and sha(mapfile) != prefix["scratch_sha256"]["map01.ay"]
    loaded = read(a.reload/"final.json")
    assert loaded["exited"] and loaded["exit_code"] == 0 and loaded["recorded_frames"] == loaded["frame_pure_count"]
    assert loaded["normal_input_replay"] and not loaded["guest_injection"] and not loaded["snapshot_loaded"]
    assert read(a.reload/"continued-game.json")["sha256"] == sha(saved)
    assert read(a.reload/"continued-map.json")["sha256"] == sha(mapfile)
    reads = [e for e in loaded["file_ops"] if e["Op"] == "read" and e["Name"].lower() == "gamedata.ay" and e["Len"] == 2987 and not e["Failed"]]
    assert reads
    assert any(e["Op"] == "read" and e["Name"].lower() == "map01.ay" and e["Len"] == 5761 and not e["Failed"] for e in loaded["file_ops"])
    for inspection in (a.saved_inspection,a.loaded_inspection):
        assert sha(inspection/"save-buffer-9e000.bin") == sha(saved)
    # This core revision logs writes in DOS.Wrote, not FileOps. Verify persisted
    # bytes and a genuine cold Continue instead of inventing FileOps write events.
    target = a.art/"normal-scene-prototype-55-r2.png"
    assert not target.exists()
    after.save(target)
    result = dict(status="normal-source-prefix-and-art-sampling-verified",observed_records=[55],unobserved_records=[48,49,51,52,54,56],source_calls=2,indexed_pixels=1600,paired_frames=1230,paired_checkpoint_statuses=12,paired_work_files=20,control_final_work_files=22,paired_stream_sha256=paired_stream,paired_state_sha256=sha(a.source/"final.state"),paired_pcm_sha256=sha(a.source/"audio.pcm"),build_inputs=46,probe_sha256=digest,art_records=4,cache_sha256={str(i):hashlib.sha256(b).hexdigest() for i,b in caches.items()},save_sha256=sha(saved),map_sha256=sha(mapfile),control_frames=control["recorded_frames"],reload_frames=loaded["recorded_frames"],saved_loaded_RAM_equal=True,original_read_step=reads[0]["Step"],layout_prototype_sha256=sha(target),string_history_limit="12 checkpoint statuses match; final rolling diagnostic lists belong to different phases and are not compared",scope="source/control are paired only through the 84-command prefix; control then completes original F7 and separate cold Continue; layout image is a disposable composite, not a runtime HD Draw; no gameplay identity claim")
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:result[k] for k in ("status","observed_records","source_calls","paired_frames","art_records","save_sha256")}))


if __name__ == "__main__":
    main()
