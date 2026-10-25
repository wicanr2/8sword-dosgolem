#!/usr/bin/env python3
"""044：獨立重建寶箱實際 Draw，連回正常來源、錄影及真正存讀。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name,Path(__file__).with_name(filename))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream,"sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("assets","original","cache","gui","out"):
        parser.add_argument("--"+name,type=Path,required=True)
    parser.add_argument("--saved-inspection",type=Path,required=True)
    parser.add_argument("--loaded-inspection",type=Path,required=True)
    a = parser.parse_args()
    assert not a.out.exists()
    sampling = module("chest_gui_sampling","audit-encounter-gui.py")
    constants = module("chest_gui_constants","prepare-hd-chest.py")
    streaming = module("chest_gui_stream","audit-army-dismiss.py")
    model = sampling.Model(a.assets,a.original,a.cache)
    image = a.assets/"map-chest-r2.png"
    assert sha(image) == constants.IMAGE_SHA
    tile = sampling.sample(image,192,150,actor=True,background=model.material(1)[0])
    assert hashlib.sha256(tile).hexdigest() == constants.CACHE_SHA
    assert tile == (a.cache/"chest-58.rgba").read_bytes()
    model.materials[59] = tile,64,25
    pmap = (a.original/"PMAP.AY").read_bytes()
    assert hashlib.sha256(pmap).hexdigest() == constants.PMAP_SHA
    phases = {}
    for phase in ("save","reload"):
        root = a.gui/phase
        final = read(root/"gui-final.json")
        assert final["closed"] and final["recorded_frames"] == final["presented_frames"]
        assert final["graphics_materials"] == 64
        for key in ("asset_error","graphics_error","map_chest_error","map_castle_error","font_error","palette_error",
                    "army_man21_error","battle_actor_error","battle_marker_error"):
            assert not final[key],(phase,key)
        calls = [json.loads(line) for line in (root/"chest-calls.jsonl").read_text().splitlines()]
        assert calls and {c["record"] for c in calls} == {58}
        raw = (root/"chest-first-58-source.bin").read_bytes()
        assert raw == pmap[58*1004:59*1004]
        expected = bytes(sum(((raw[4+q*200+p//8] >> (7-p%8)) & 1) << q for q in range(4)) for p in range(1600))
        assert (root/"chest-first-58-after.idx").read_bytes() == expected
        for call in calls:
            assert call["raw_sha256"] == constants.RECORD_SHA and call["abi_bytes_matched"] == 230
            assert call["segment"] == 0x14D2 and call["entry"] == 0x76F and call["return"] == 0x854
            assert call["return_step"] > call["entry_step"]
        paths = sorted((root/"research-chest-draws").glob("*-first-draw.json"))
        assert len(paths) == 3
        results = [model.frame(p.with_suffix("")) for p in paths]
        assert {r["font_id"] for r in results} == {"noto","lishu","caoshu"}
        for path,result in zip(paths,results):
            meta = read(path)
            assert 59 in result["material_ids"] and result["height"] == 25
            prior = [c for c in calls if c["return_step"] <= meta["step"]]
            assert prior and max(c["return_step"] for c in prior) == meta["source_return_steps"]["58"]
        wanted = {r["actual_draw"]:r for r in results}
        count = 0
        for ordinal,step,frame in streaming.stream(root):
            count = ordinal
            if ordinal in wanted:
                result = wanted.pop(ordinal)
                assert result["step"] == step
                assert result["rgba_sha256"] == hashlib.sha256(frame.tobytes()).hexdigest()
        assert not wanted and count == final["recorded_frames"]
        phases[phase] = dict(frames=count,source_calls=len(calls),source_indexed_pixels=1600,
                             actual_draws=results,full_model_pixels=len(results)*2304000)
    saved = read(a.gui/"save/saved.json")
    assert saved["bytes"] == 2987 and saved["sha256"] == sha(a.gui/"scratch/gamedata.ay")
    final = read(a.gui/"save/gui-final.json")
    assert final["exited"] and final["exit_code"] == 0
    assert (a.gui/"scratch/map01.ay").stat().st_size == 5761
    loaded = read(a.gui/"reload/gui-final.json")
    reads = [op for op in loaded["file_ops"] if op["Op"] == "read" and op["Name"].lower() == "gamedata.ay" and op["Len"] == 2987 and not op["Failed"]]
    assert reads
    for inspection in (a.saved_inspection,a.loaded_inspection):
        assert sha(inspection/"save-buffer-9e000.bin") == saved["sha256"]
    result = dict(status="passed-independent-chest-actual-Draws",phases=phases,actual_stream_link=True,
                  three_fonts=True,save_bytes=2987,save_sha256=saved["sha256"],map_sha256=sha(a.gui/"scratch/map01.ay"),
                  original_read_step=reads[0]["Step"],saved_loaded_ram_equal=True,
                  scope="PMAP 58 rendering, normal Continue, XTEST menus, F7 save/quit/cold Continue; no chest reward claim")
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:result[k] for k in ("status","save_sha256","original_read_step","saved_loaded_ram_equal")}))


if __name__ == "__main__":
    main()
