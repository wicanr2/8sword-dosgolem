"""在 Pillow Docker 內匯入 023 的四筆已審查圖像，不修改原始 PNG。"""
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


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("base", "source", "art-dir", "out"):
        p.add_argument("--"+name,required=True,type=Path)
    a=p.parse_args()
    assert a.out.is_dir() and not any(a.out.iterdir()), "輸出須為已存在的空目錄"
    source=a.source.read_bytes();assert sha(source)==SOURCE_SHA
    assert (a.base/"battle-background.json").is_file()
    assert not (a.base/"battle-actors.json").exists()
    frames=[]
    for i,(name,expected,src,dst) in enumerate(ART):
        raw=(a.art_dir/name).read_bytes();assert sha(raw)==expected,name
        with Image.open(a.art_dir/name) as im:
            assert im.format=="PNG" and im.mode=="RGBA" and im.size==(1176,1337)
            alpha=im.getchannel("A");assert alpha.getextrema()==(0,255)
            box=alpha.point(lambda v:255 if v>3 else 0).getbbox()
            assert list(box)==[src[0],src[1],src[0]+src[2],src[1]+src[3]]
        frames.append(dict(record=i,image=dict(source_index=86+i,file=f"battle-man16-{i}-r1.png",
                      sha256=expected,width=1176,height=1337,sampling="bitmap",source_rect=src),target_rect=dst))
    prompts={name:(a.art_dir/name).read_bytes() for name in ["frame-0-r1.prompt.txt","frame-0-r2.prompt.txt"]+[f"frame-{i}-r1.prompt.txt" for i in (1,2,3)]}
    preserved={}
    for path in sorted(a.base.iterdir()):
        assert path.is_file() and not path.is_symlink(), "基底只接受普通檔案"
        shutil.copyfile(path,a.out/path.name);preserved[path.name]=sha(path.read_bytes())
    for i,(name,_,_,_) in enumerate(ART):shutil.copyfile(a.art_dir/name,a.out/frames[i]["image"]["file"])
    manifest=dict(schema=1,source_file="MAN16.EGG",source_sha256=SOURCE_SHA,
                  style="B-bright-painted-r1",style_reference_sha256=STYLE_SHA,frames=frames)
    (a.out/"battle-actors.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    provenance=dict(spec="023",source_sha256=SOURCE_SHA,record_bytes=3304,record_offsets=[0,3304,6608,9912],
                    tool="built-in image_gen",original_png_bytes_preserved=True,
                    input_art_sha256={q.name:sha(q.read_bytes()) for q in sorted(a.art_dir.glob("frame-*-painted-raw-*.png"))},
                    prompt_sha256={n:sha(b) for n,b in prompts.items()},preserved_files=preserved,
                    registration="native-position display approximation; original oval shadow omitted",
                    rights="local-only original-game derivatives; no public redistribution grant")
    (a.out/"battle-actors-source.json").write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+"\n")
    (a.out/"battle-actors-prompts.txt").write_bytes(b"\n\n".join(n.encode()+b"\n"+b for n,b in prompts.items()))
    print(json.dumps(dict(files=len(list(a.out.iterdir())),preserved=len(preserved),frames=len(frames))))


if __name__=="__main__":main()
