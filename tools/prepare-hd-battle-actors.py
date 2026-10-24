"""在 Pillow Docker 內匯入 023／024 的已審查圖像，不修改原始 PNG。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from PIL import Image


SOURCE_SHA = "d4acf7c58c199c1776ffde6c86afa3c9b0ae3b132e4cc59973e1e0d5c2011d6a"
STYLE_SHA = "2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6"
ART = [
    ("frame-0-painted-raw-r2.png", "53a599a6db8f10cf76d08de389fbf07b72b6f3c8f9fdf6647256c440809300ad", [123,311,1052,902], [30,84,231,192]),
    ("frame-1-painted-raw-r1.png", "276b05c40e6a728411d8fa4fd37cd2e7d01c1605435eb73e673dff6da9a22c97", [123,340,1041,869], [30,96,231,180]),
    ("frame-2-painted-raw-r1.png", "72674401cf1e6d9963cf06c0916950998b39fb99628f299ea752724135402c9f", [60,155,1116,953], [27,36,234,174]),
    ("frame-3-painted-raw-r1.png", "1721160832e226599e1799b396ad1be15f76f87304fc7eb5a1775fea80eb40e0", [69,189,1104,958], [33,60,228,174]),
]
MAN06_SHA = "97be211dd9289538aaa46f01b2340bcac9ce0a7c8e44ed9d3c4e9abdac873579"
MAN06_ART = [
    ("frame-0-painted-raw-r1.png", "ab571977babe4b7fdffd23ae3a88ac2ee1449ea0a74b5a0301692e03daa5d789", [229,133,923,1032], [75,54,177,210]),
    ("frame-1-painted-raw-r1.png", "d4e0f66020db4750594ee7d6aecbc0f15aba2d81b85eba17386496c749daa4f3", [232,88,919,1138], [78,42,177,222]),
    ("frame-2-painted-raw-r1.png", "86b4a07704069de292b0fa4f9eebc4d6f4462d79e51ff3b1d89e5959a377375f", [272,63,859,900], [78,0,183,210]),
    ("frame-3-painted-raw-r1.png", "b9ffc6df5c03db70480cfb894b7789c583e0390f0fec0368de337efea8e74e52", [83,95,1081,991], [18,0,243,210]),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("base", "source", "art-dir", "out"):
        p.add_argument("--"+name,required=True,type=Path)
    p.add_argument("--unit",choices=("MAN16","MAN06"),default="MAN16")
    a=p.parse_args()
    entries,source_sha,first_index,spec,prefix,manifest_name=ART,SOURCE_SHA,86,"023","battle-actors","battle-actors.json"
    stem="battle-man16"
    prompt_names=["frame-0-r1.prompt.txt","frame-0-r2.prompt.txt"]+[f"frame-{i}-r1.prompt.txt" for i in (1,2,3)]
    if a.unit=="MAN06":
        entries,source_sha,first_index,spec,prefix,manifest_name=MAN06_ART,MAN06_SHA,90,"024","battle-man06","battle-man06.json"
        stem="battle-man06"
        prompt_names=[f"frame-{i}-r1.prompt.txt" for i in range(4)]
    assert a.out.is_dir() and not any(a.out.iterdir()), "輸出須為已存在的空目錄"
    source=a.source.read_bytes();assert sha(source)==source_sha
    assert (a.base/"battle-background.json").is_file()
    assert not (a.base/manifest_name).exists()
    frames=[]
    for i,(name,expected,src,dst) in enumerate(entries):
        raw=(a.art_dir/name).read_bytes();assert sha(raw)==expected,name
        with Image.open(a.art_dir/name) as im:
            assert im.format=="PNG" and im.mode=="RGBA" and im.size==(1176,1337)
            alpha=im.getchannel("A");assert alpha.getextrema()==(0,255)
            box=alpha.point(lambda v:255 if v>3 else 0).getbbox()
            assert list(box)==[src[0],src[1],src[0]+src[2],src[1]+src[3]]
        frames.append(dict(record=i,image=dict(source_index=first_index+i,file=f"{stem}-{i}-r1.png",
                      sha256=expected,width=1176,height=1337,sampling="bitmap",source_rect=src),target_rect=dst))
    prompts={name:(a.art_dir/name).read_bytes() for name in prompt_names}
    preserved={}
    for path in sorted(a.base.iterdir()):
        assert path.is_file() and not path.is_symlink(), "基底只接受普通檔案"
        shutil.copyfile(path,a.out/path.name);preserved[path.name]=sha(path.read_bytes())
    for i,(name,_,_,_) in enumerate(entries):shutil.copyfile(a.art_dir/name,a.out/frames[i]["image"]["file"])
    manifest=dict(schema=1,source_file=a.unit+".EGG",source_sha256=source_sha,
                  style="B-bright-painted-r1",style_reference_sha256=STYLE_SHA,frames=frames)
    (a.out/manifest_name).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    provenance=dict(spec=spec,source_sha256=source_sha,record_bytes=3304,record_offsets=[0,3304,6608,9912],
                    tool="built-in image_gen",original_png_bytes_preserved=True,
                    input_art_sha256={q.name:sha(q.read_bytes()) for q in sorted(a.art_dir.glob("frame-*-painted-raw-*.png"))},
                    prompt_sha256={n:sha(b) for n,b in prompts.items()},preserved_files=preserved,
                    registration="native-position display approximation; original oval shadow omitted",
                    rights="local-only original-game derivatives; no public redistribution grant")
    (a.out/(prefix+"-source.json")).write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+"\n")
    (a.out/(prefix+"-prompts.txt")).write_bytes(b"\n\n".join(n.encode()+b"\n"+b for n,b in prompts.items()))
    print(json.dumps(dict(files=len(list(a.out.iterdir())),preserved=len(preserved),frames=len(frames))))


if __name__=="__main__":main()
