"""在 Pillow Docker 內匯入 023 至 027 的已審查圖像，不修改原始 PNG。"""
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


MAN11_SHA = "860ab98a7165f25fe2007dd597ddf6fc698c9d2f048701eec955a1a0cd65f832"
MAN11_ART = [
    ("frame-0-painted-raw-r1.png", "1657bfc58772177d2b2819f30c01b198ed1702f0d64f3fa10662d6e5aa1452ef", [91,22,1071,1283], [96,30,165,246]),
    ("frame-1-painted-raw-r1.png", "e0cb5749c13db0ac91f526941bff6168eb94bbe2b4c034c5e47de3b58e3c86a0", [93,16,1076,1276], [96,18,165,258]),
    ("frame-2-painted-raw-r1.png", "49366f236e47db052009a52d4572fb4286dbc4767fff6e0d49067820aa2cca66", [102,25,1044,1299], [96,6,165,234]),
    ("frame-3-painted-raw-r1.png", "e0a50aa7717689827abae19de62335ae65ea8b760aa6169c368336f7bbc89eba", [25,79,1139,1131], [24,6,237,234]),
]


MAN21_SHA = "47cc484319abeba53551c20b7cf4b9b2c6061f2da3b6cda14155b3598f10982c"
MAN21_ART = [
    ("frame-0-painted-raw-r1.png", "e710379542cf1c4279ce1703b17ed9d3a839a2e831add705d0f93a370cbf8122", [119,161,1041,1074], [48,78,213,186]),
    ("frame-1-painted-raw-r1.png", "5e6b3a90ad34fef1914e42c6d9bee491df0596102f7dc134376d420d8c34c80a", [128,153,1031,1085], [60,78,201,186]),
    ("frame-2-painted-raw-r1.png", "483573cabb50b4ae6ecb2ac9b6a68c776398d37f847c2f36a45556862ade48c7", [180,163,972,1074], [84,78,177,186]),
    ("frame-3-painted-raw-r1.png", "1c079c414df24d03ae56e93990a17fa850782a10c796087dc403ec0b10be192d", [39,222,1130,985], [0,78,261,186]),
]

PON_SHA = "5fe52b534cccbcaab5265681c42f208751f69da1144161541f161d93b89b786e"
PON_ART = [
    ("frame-0-painted-raw-r1.png", "7f6d0bd35ac1a338f54bdf4ba64decba4b11f80ac0ba247983f2eab7404fe1c6", [45,52,1093,1233], [0,0,264,300]),
    ("frame-1-painted-raw-r1.png", "ca9b4e6aac263753d5135a28da3f04b9594dae7650c583fdef9d13d989b64b30", [48,67,1097,1223], [33,30,225,222]),
    ("frame-2-painted-raw-r1.png", "c60add2fde67e7e33463b3944c5d36cf78f8327562470d551e8f83e9060b8bcd", [64,75,1070,1205], [63,66,165,174]),
    ("frame-3-painted-raw-r2.png", "dbc2081a6b2bb66613825a0d4c807b765d2cddb30b5b7cd38650312b22622103", [235,229,797,840], [90,96,114,102]),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("base", "source", "art-dir", "out"):
        p.add_argument("--"+name,required=True,type=Path)
    p.add_argument("--unit",choices=("MAN16","MAN06","MAN11","MAN21","PON"),default="MAN16")
    a=p.parse_args()
    entries,source_sha,first_index,spec,prefix,manifest_name=ART,SOURCE_SHA,86,"023","battle-actors","battle-actors.json"
    stem="battle-man16"
    prompt_names=["frame-0-r1.prompt.txt","frame-0-r2.prompt.txt"]+[f"frame-{i}-r1.prompt.txt" for i in (1,2,3)]
    if a.unit=="MAN06":
        entries,source_sha,first_index,spec,prefix,manifest_name=MAN06_ART,MAN06_SHA,90,"024","battle-man06","battle-man06.json"
        stem="battle-man06"
        prompt_names=[f"frame-{i}-r1.prompt.txt" for i in range(4)]
    if a.unit=="MAN11":
        entries,source_sha,first_index,spec,prefix,manifest_name=MAN11_ART,MAN11_SHA,94,"025","battle-man11","battle-man11.json"
        stem="battle-man11"
        prompt_names=[f"frame-{i}-r1.prompt.txt" for i in range(4)]
    if a.unit=="MAN21":
        entries,source_sha,first_index,spec,prefix,manifest_name=MAN21_ART,MAN21_SHA,98,"026","battle-man21","battle-man21.json"
        stem="battle-man21"
        prompt_names=[f"frame-{i}-r1.prompt.txt" for i in range(4)]
    if a.unit=="PON":
        entries,source_sha,first_index,spec,prefix,manifest_name=PON_ART,PON_SHA,102,"027","battle-pon","battle-pon.json"
        stem="battle-pon"
        prompt_names=[f"frame-{i}-r1.prompt.txt" for i in range(4)]+["frame-3-r2.prompt.txt"]
    assert a.out.is_dir() and not any(a.out.iterdir()), "輸出須為已存在的空目錄"
    source=a.source.read_bytes();assert sha(source)==source_sha
    assert (a.base/"battle-background.json").is_file()
    assert not (a.base/manifest_name).exists()
    frames=[]
    for i,(name,expected,src,dst) in enumerate(entries):
        raw=(a.art_dir/name).read_bytes();assert sha(raw)==expected,name
        with Image.open(a.art_dir/name) as im:
            wide=(a.unit=="MAN11" and i in (1,3)) or (a.unit=="MAN21" and i in (2,3))
            expected_size=(1177 if wide else 1176,1337)
            if a.unit=="PON":expected_size=[(1178,1335),(1177,1337),(1177,1337),(1178,1335)][i]
            assert im.format=="PNG" and im.mode=="RGBA" and im.size==expected_size
            alpha=im.getchannel("A");assert alpha.getextrema()==(0,255)
            box=alpha.point(lambda v:255 if v>3 else 0).getbbox()
            assert list(box)==[src[0],src[1],src[0]+src[2],src[1]+src[3]]
        frames.append(dict(record=i,image=dict(source_index=first_index+i,file=f"{stem}-{i}-r1.png",
                      sha256=expected,width=expected_size[0],height=expected_size[1],sampling="bitmap",source_rect=src),target_rect=dst))
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
                    input_art_sha256={n:sha((a.art_dir/n).read_bytes()) for n,_,_,_ in entries},
                    prompt_sha256={n:sha(b) for n,b in prompts.items()},preserved_files=preserved,
                    registration=("original colored bounds; cumulative painted source-over is a presentation approximation" if a.unit=="PON" else "native-position display approximation; original oval shadow omitted"),
                    rights="local-only original-game derivatives; no public redistribution grant")
    (a.out/(prefix+"-source.json")).write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+"\n")
    (a.out/(prefix+"-prompts.txt")).write_bytes(b"\n\n".join(n.encode()+b"\n"+b for n,b in prompts.items()))
    print(json.dumps(dict(files=len(list(a.out.iterdir())),preserved=len(preserved),frames=len(frames))))


if __name__=="__main__":main()
