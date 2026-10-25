#!/usr/bin/env python3
"""045：獨立重建第48／49／52／54／56筆圖像實際 Draw，連回正常來源、錄影及真正存讀。Docker only。"""
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
    parser.add_argument("--record",type=int,choices=[48,49,52,54,56],required=True)
    a = parser.parse_args()
    assert not a.out.exists()
    sampling = module("landmarks_gui_sampling","audit-encounter-gui.py")
    constants = module("landmarks_gui_constants","prepare-hd-landmarks.py")
    streaming = module("landmarks_gui_stream","audit-army-dismiss.py")
    model = sampling.Model(a.assets,a.original,a.cache)
    entry=constants.RECORDS[a.record]
    image = a.assets/f"map-landmark-{a.record}-r{2 if a.record == 48 else 1}.png"
    assert sha(image) == entry["image"]
    tile = sampling.sample(image,192,150,actor=True,background=model.material(1)[0])
    assert hashlib.sha256(tile).hexdigest() == entry["cache"]
    assert tile == (a.cache/f"landmark-{a.record}.rgba").read_bytes()
    helper=module("landmarks_static","audit-map-landmark-route.py")
    helper.register_static_materials(model,a.assets,sampling)
    pmap = (a.original/"PMAP.AY").read_bytes()
    assert hashlib.sha256(pmap).hexdigest() == constants.PMAP_SHA
    phases = {}
    for phase in ("save","reload"):
        root = a.gui/phase
        final = read(root/"gui-final.json")
        assert final["closed"] and final["recorded_frames"] == final["presented_frames"]
        assert final["graphics_materials"] == (70 if a.record == 48 else 67 if a.record in (49,54) else 69)
        for key in ("asset_error","graphics_error","map_chest_error","map_landmark_error","map_castle_error","font_error","palette_error",
                    "army_man21_error","battle_actor_error","battle_marker_error"):
            assert not final[key],(phase,key)
        calls = [json.loads(line) for line in (root/"landmarks-calls.jsonl").read_text().splitlines()]
        assert calls and {c["record"] for c in calls} == {a.record}
        raw = (root/f"landmarks-first-{a.record}-source.bin").read_bytes()
        assert raw == pmap[a.record*1004:(a.record+1)*1004]
        expected = bytes(sum(((raw[4+q*200+p//8] >> (7-p%8)) & 1) << q for q in range(4)) for p in range(1600))
        assert (root/f"landmarks-first-{a.record}-after.idx").read_bytes() == expected
        for call in calls:
            assert call["raw_sha256"] == entry["record"] and call["abi_bytes_matched"] == 230
            assert call["segment"] == 0x14D2 and call["entry"] == 0x76F and call["return"] == 0x854
            assert call["return_step"] > call["entry_step"]
        paths = sorted((root/"research-landmarks-draws").glob("*-first-draw.json"))
        assert len(paths) == 3
        results = [model.frame(p.with_suffix("")) for p in paths]
        assert {r["font_id"] for r in results} == {"noto","lishu","caoshu"}
        for path,result in zip(paths,results):
            meta = read(path)
            assert a.record+1 in result["material_ids"] and result["height"] == 25
            prior = [c for c in calls if c["return_step"] <= meta["step"]]
            assert prior and max(c["return_step"] for c in prior) == meta["source_return_steps"][str(a.record)]
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
    companions={"map01.ay":sha(a.gui/"scratch/map01.ay")}
    save_open_steps={}
    if a.record == 48:
        assert (a.gui/"scratch/map02.ay").stat().st_size == 5761
        companions["map02.ay"]=sha(a.gui/"scratch/map02.ay")
        for name,length in (("map2.ay",2133),("map02.ay",5761)):
            assert any(op["Op"] == "read" and op["Name"].lower() == name and op["Len"] == length and not op["Failed"] for op in loaded["file_ops"])
        # The GUI starts with a genuine existing save. Verify a fresh ordinary F7
        # save-path open before its saved checkpoint, rather than file existence alone.
        initial_reads=[op["Step"] for op in final["file_ops"] if op["Op"] == "read" and op["Name"].lower() in ("gamedata.ay","map02.ay")]
        assert initial_reads
        for name in ("gamedata.ay","map02.ay"):
            operations=[op for op in final["file_ops"] if op["Op"] == "open" and op["Name"].lower() == name and not op["Failed"] and max(initial_reads) < op["Step"] <= saved["status"]["steps"]]
            assert len(operations) == 1
            save_open_steps[name]=operations[0]["Step"]
    for inspection in (a.saved_inspection,a.loaded_inspection):
        assert sha(inspection/"save-buffer-9e000.bin") == saved["sha256"]
    result = dict(status="passed-independent-landmarks-actual-Draws",record=a.record,phases=phases,actual_stream_link=True,
                  three_fonts=True,save_bytes=2987,save_sha256=saved["sha256"],map_sha256=sha(a.gui/"scratch/map01.ay"),
                  original_read_step=reads[0]["Step"],saved_loaded_ram_equal=True,map_companions_sha256=companions,save_path_open_steps=save_open_steps,
                  scope=f"PMAP {a.record} rendering, normal Continue, XTEST menus, F7 save/quit/cold Continue; no landmark identity or reward claim")
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:result[k] for k in ("status","save_sha256","original_read_step","saved_loaded_ram_equal")}))


if __name__ == "__main__":
    main()
