#!/usr/bin/env python3
"""045：核對第49／54筆普通步行來源、觀測隔離與手繪位置原型。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from PIL import Image

PMAP_SHA="9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02"
PAM_SHA="83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"
ART_SHA={49:"347e485c9450754b28bb5f1db743a8d6aea83d51836ae8a1298e7f45919cd303",54:"328c5a99cf1758062778c7381742129f4a755af5bb0d35693084a78c7c35d7b5"}
EGA=[(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),(170,85,0),(170,170,170),(85,85,85),(85,85,255),(85,255,85),(85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]

def sha(p):
    with p.open("rb") as f:return hashlib.file_digest(f,"sha256").hexdigest()

def read(p):return json.loads(p.read_text())

def files(p):return {f.name:sha(f) for f in p.iterdir() if f.is_file()}

def register_static_materials(model, assets, sampling):
    """Independent PNG sampling for optional map groups used in normal full-frame audits."""
    def module(name):
        spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+".py"))
        value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
    entries=module("prepare-hd-landmarks").RECORDS.copy()
    for index, name in [(55,"prepare-hd-landmark55"),(58,"prepare-hd-chest")]:
        value=module(name)
        entries[index]=dict(image=value.IMAGE_SHA,cache=value.CACHE_SHA)
    for index, expected in entries.items():
        path=assets/("map-chest.json" if index==58 else f"map-landmark-{index}.json")
        if not path.exists():continue
        manifest=read(path)
        filename="map-chest-r2.png" if index==58 else f"map-landmark-{index}-r{2 if index == 48 else 1}.png"
        assert manifest["source_index"]==index and manifest["source_sha256"]==PMAP_SHA
        assert manifest["image"]["file"]==filename and manifest["image"]["sha256"]==expected["image"]
        image=assets/filename;assert sha(image)==expected["image"]
        tile=sampling.sample(image,192,150,actor=True,background=model.material(1)[0])
        assert hashlib.sha256(tile).hexdigest()==expected["cache"]==manifest["cache_sha256"]
        model.materials[index+1]=tile,64,25


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("original","assets","source","control","reload","build","art","saved-inspection","loaded-inspection","out"):
        p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args();assert not a.out.exists()
    pm=(a.original/"PMAP.AY").read_bytes();assert hashlib.sha256(pm).hexdigest()==PMAP_SHA
    assert sha(a.original/"PAM.AY")==PAM_SHA
    finals=[read(root/"final.json") for root in (a.source,a.control)]
    for d in finals:
        assert d["normal_input_replay"] and not d["snapshot_loaded"] and not d["guest_injection"]
        assert d["recorded_frames"]==d["frame_pure_count"]==2156
        assert d["exited"] and d["exit_code"]==0
    for key in ("steps","strings","input_events","file_ops","exec_log","music","elapsed_ms","irq1_delivered","bios_consumed"):
        assert finals[0][key]==finals[1][key],key
    equal={}
    for name in ("final.state","frame-check.state","audio.pcm","commands.jsonl","frames.jsonl","presentation.frames.gz"):
        assert sha(a.source/name)==sha(a.control/name),name
        equal[name]=sha(a.source/name)
    scratch=files(a.source/"scratch");assert scratch==files(a.control/"scratch") and len(scratch)==22
    checkpoints=sorted(a.source.glob("*-native.png"));assert len(checkpoints)==16
    for path in checkpoints:
        for name in (path.name,path.name.replace("-native.png","-hd.png"),path.name.replace("-native.png",".json")):
            left,right=a.source/name,a.control/name
            if name.endswith(".json"):
                dl,dr=read(left),read(right)
                for key in ("steps","strings","input_events","file_ops","exec_log","music","elapsed_ms","irq1_delivered","bios_consumed"):
                    assert dl[key]==dr[key],(name,key)
            else:assert sha(left)==sha(right),name
    calls=[json.loads(l) for l in (a.source/"map-object-calls.jsonl").read_text().splitlines()]
    assert len(calls)==10 and {c["record"] for c in calls}=={49,54}
    for c in calls:
        assert c["segment"]==0x14d2 and c["entry"]==0x76f and c["return"]==0x854 and c["abi_bytes_matched"]==230
        assert c["return_step"]>c["entry_step"] and c["mode"]==1
        assert c["raw_sha256"]==hashlib.sha256(pm[c["record"]*1004:(c["record"]+1)*1004]).hexdigest()
    inputs={}
    for line in (a.build/"build-inputs.sha256").read_text().splitlines():
        digest,name=line.split("  ",1);assert sha(a.build/"src"/name)==digest;inputs[name]=digest
    assert len(inputs)==47
    digest,name=(a.build/"build-outputs.sha256").read_text().split();assert name=="probe" and sha(a.build/name)==digest
    saved=a.source/"scratch/gamedata.ay";assert saved.stat().st_size==2987
    for inspection in (a.saved_inspection,a.loaded_inspection):assert sha(inspection/"save-buffer-9e000.bin")==sha(saved)
    loaded=read(a.reload/"final.json");assert loaded["exited"] and loaded["exit_code"]==0 and loaded["recorded_frames"]==312
    reads=[op for op in loaded["file_ops"] if op["Op"]=="read" and op["Name"].lower()=="gamedata.ay" and op["Len"]==2987 and not op["Failed"]]
    assert reads and sha(a.reload/"scratch/gamedata.ay")==sha(saved)
    assert sha(a.reload/"scratch/map01.ay")==sha(a.source/"scratch/map01.ay")
    spec=importlib.util.spec_from_file_location("landmark_route_sampling",Path(__file__).with_name("audit-encounter-gui.py"));mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    model=mod.Model(a.assets,a.original,a.art)
    images=[];records=[]
    for index in (49,54):
        record=pm[index*1004:(index+1)*1004]
        raw=(a.source/f"map-object-first-{index}-source.bin").read_bytes();assert raw==record
        native=bytes(sum(((record[4+q*200+i//8]>>(7-i%8))&1)<<q for q in range(4)) for i in range(1600))
        assert (a.source/f"map-object-first-{index}-after.idx").read_bytes()==native
        status=read(a.source/f"target-{index}-map.json")
        call=max((c for c in calls if c["record"]==index and c["return_step"]<=status["steps"]),key=lambda c:c["return_step"])
        x,y=call["x_byte"]*8*3,call["y"]*6;box=(x,y,x+192,y+150)
        rgb=bytes(v for c in native for v in EGA[c]);expected=Image.frombytes("RGB",(64,25),rgb).resize((192,150),Image.Resampling.NEAREST)
        scene=Image.open(a.source/f"target-{index}-map-hd.png").convert("RGBA")
        assert scene.crop(box).convert("RGB").tobytes()==expected.tobytes(),(index,box)
        path=a.art/f"pmap-{index}-painted-r1.png";assert sha(path)==ART_SHA[index]
        im=Image.open(path);assert im.size==(1419,1108) and im.mode=="RGBA" and im.getchannel("A").getextrema()==(0,255)
        tile=mod.sample(path,192,150,actor=True,background=model.material(1)[0]);cache=hashlib.sha256(tile).hexdigest()
        if index==54:assert cache=="79b142d453644177050a596082bcbc2607e9e48b3dfebb07e9f7981e686e7706" and tile==(a.art/"pmap-54-prototype-cache-r1.rgba").read_bytes()
        source=scene.copy();scene.paste(Image.frombytes("RGBA",(192,150),tile),(x,y))
        # Only a disposable rectangle composite: no new formal loader or actual Draw claim.
        source.paste(scene.crop(box),(x,y));assert source.tobytes()==scene.tobytes()
        records.append(dict(index=index,native_sha256=hashlib.sha256(record[:804]).hexdigest(),record_sha256=hashlib.sha256(record).hexdigest(),image_sha256=sha(path),prompt_sha256=sha(a.art/f"pmap-{index}-painted-r1.prompt.txt"),cache_sha256=cache,source_call=read(a.source/f"map-object-first-{index}-call.json"),layout_box=box,normal_native_pixels=1600,source_calls=sum(c["record"]==index for c in calls)))
        images.append((index,scene,tile))
    result=dict(status="normal-route-source-and-independent-art-verified",frames_each=2156,total_frame_purity=4312,equal=equal,source_calls=10,records=records,checkpoint_pairs=len(checkpoints),scratch_files=22,build_inputs=47,probe_sha256=digest,save_sha256=sha(saved),map_sha256=sha(a.source/"scratch/map01.ay"),reload_frames=312,original_read_step=reads[0]["Step"],saved_loaded_ram_equal=True,scope="PMAP49/54 source and disposable art/layout only; formal materials and new actual Draws remain unverified")
    for index,scene,tile in images:
        out=a.art/f"normal-scene-prototype-{index}-r1.png"
        if out.exists():
            assert Image.open(out).convert("RGBA").tobytes()==scene.tobytes()
        else:scene.save(out)
        if index==49:
            cache=a.art/"pmap-49-prototype-cache-r1.rgba"
            if cache.exists():assert cache.read_bytes()==tile
            else:cache.write_bytes(tile)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:result[k] for k in ("status","frames_each","source_calls","save_sha256")}))

if __name__=="__main__":main()
