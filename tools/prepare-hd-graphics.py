#!/usr/bin/env python3
"""在 Docker 匯入已確認風格的地表素材，不改動生成 PNG 或原版資料。"""
import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path
from PIL import Image

PMAP_SHA = "9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02"
STYLE_SHA = "2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6"
MATERIALS = [(0, "grass-painted-r1", "4e6baf80381f064a8da9d9fa6c09e7a3009498da0dfd11c8472f449d7ed14992",256,200),
             (1, "water-painted-r1", "6a0fc05d7911bbf2d318f697e9361f19a09ed4c3c1d172d46eb09c400af70e93",256,200),
             (15, "ochre-rock-r1", "39afceb0428407ff189d075328ccd64acbd3e49443a48f975e4c6ee499074aa7",512,400),
             (46, "jade-paper-r1", "2b837ec73368ce72f85be474e056bfef7fd8e7328c864e42407a02757c303527",512,400),
             (68, "hero-portrait-r1", "8150858af91388a8fb46587c55a3ff83df6e51d1bf7bb2b9eb8b9d03d99a1533",0,0),
             (30, "sand-painted-r1", "564482c3eb590fb7da7fb9dff68a5450921ab6f077ea5139f57676a68cd00242",512,400)]
OVERLAYS=[(50,"pmap-50-banner-r1","881de51a799d407752555e0e34a6fd5b295e5b0233ffd269b8e5be865ff6d648"),
          (53,"pmap-53-compound-r1","c080e88ac3cd9a8464fc55ec0c9c0b31f12878049d8f6c4ea903bf487beca239"),
          (57,"pmap-57-house-r1","6bc2e7841c51fa9d72d8bf3b634d8c6433dfd1da0a50f93cf9180fd54233ec2d")]
ACTORS=[(0,"14c5f9b0b47abb05f61e2582bdad95630fc98d8428b04376289bbc1fd6b6a20d"),
        (1,"dba3abcf90bc113d51361f47203eb46ea4a9096b01ffb07887cf458fc63c0a24"),
        (2,"e06c9e61ebd2e7b34bfd706d8ecc87081da0122aff8948d1d55da293f046b304"),
        (3,"469c2809f1e4a94b9f7dd9ef05acf8e105de6e19ffa607d5a9a37585184630f1"),
        (4,"0669cbd886c338ce5c6d3d8216dfa9f0b3ac1c4c6c7a63808f4aecee3403462b"),
        (5,"9809cb98906713250edcd61031447df14eeb55e6db1000f3b05a04c6d9821f67"),
        (6,"20eb7426b2d16a256156d26c588361642d531db16b16cdf865ac239142964835"),
        (7,"9ba0656f5fb9000b63fb008b9f95461d64ac8aff1dce76484688bdb53c88c509"),
        (8,"c169beef7922cec01afc73e0a4f2a6a42e20b2ed993ae5bff166c3e082754c2a"),
        (9,"fa0913166dacc8f7b2792b1a9071a95bef99e42c71e99cacd7c12807a732e62e"),
        (10,"76197d437bf9d049f45ecaec1757ecf5d71767dc15b789a33110517b586d9dfb"),
        (11,"f46c4d3f27f0795fc0fd417d47a856edf52ba9406f2bb9f67e0a8f59d99d05c0")]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def prepare(args):
    if sha(args.source) != PMAP_SHA or sha(args.style_reference) != STYLE_SHA:
        raise ValueError("原版來源或定稿參考不符")
    if list(args.out.iterdir()):
        raise ValueError("輸出目錄須為空，不覆寫現有素材")
    if (args.out.stat().st_uid,args.out.stat().st_gid)!=(os.getuid(),os.getgid()):
        raise ValueError("輸出目錄 UID/GID 不符")
    fonts = json.loads((args.font_assets / "font.json").read_text())
    if fonts["schema"]!=1 or len(fonts["glyphs"])!=731 or fonts["weight"]!=900 or fonts["atlas_sha256"]!=sha(args.font_assets / "font.png"):
        raise ValueError("Noto 資產不符")
    manifest = {"schema":1,"source_sha256":PMAP_SHA,"style":"B-bright-painted-r1",
                "style_reference_sha256":STYLE_SHA,"generator":"built-in image_gen",
                "rights":"local-only-derived","materials":[]}
    selected=MATERIALS if args.set in ("current","objects") else MATERIALS[:5] if args.set in ("interface","portrait") else MATERIALS[:4] if args.set=="landscape" else MATERIALS[:2]
    for index,name,expected,crop_width,crop_height in selected:
        image_path=args.refs / (name+".png")
        if sha(image_path)!=expected:
            raise ValueError("已選取生成圖的 SHA 不符")
        with Image.open(image_path) as image:
            width,height=image.size
            if image.format!="PNG" or not (1<=width<=4096 and 1<=height<=4096) or width*height>8388608:
                raise ValueError("生成圖格式或尺寸不符")
            if image.convert("RGBA").getchannel("A").getextrema()!=(255,255):
                raise ValueError("地表素材須完全不透明")
        prompt=args.refs / (name+".prompt.txt")
        if not prompt.is_file() or not prompt.read_text().strip():
            raise ValueError("生成提示缺失")
        for source in [image_path,prompt]:
            shutil.copyfile(source,args.out / source.name)
        if index==68:
            crop_width,crop_height=width,height
        manifest["materials"].append({"source_index":index,"file":image_path.name,"sha256":expected,
                                     "width":width,"height":height,"prompt_file":prompt.name,"prompt_sha256":sha(prompt),
                                     "sampling":"bitmap" if index==68 else "periodic","source_rect":[(width-crop_width)//2,(height-crop_height)//2,crop_width,crop_height]})
    manifest["composites"]=[{"source_index":i,"land_source":0,"water_source":1,"mask_rule":"pmap-green-blue-v1"} for i in range(2,14)]
    if args.set!="ground":
        manifest["composites"] += [{"source_index":i,"land_source":0,"rock_source":15,"mask_rule":"pmap-grass-rock-v1"} for i in range(14,30) if i!=15]
    if args.set in ("current","objects"):
        manifest["composites"] += [{"source_index":i,"land_source":0,"sand_source":30,"mask_rule":"pmap-grass-sand-v1"} for i in range(31,45)]
        manifest["overlays"]=[]
        for index,name,expected in OVERLAYS:
            image_path=args.refs/(name+".png");prompt=args.refs/(name+".prompt.txt")
            if sha(image_path)!=expected or not prompt.is_file() or not prompt.read_text().strip():
                raise ValueError("透明靜物來源或提示不符")
            with Image.open(image_path) as image:
                width,height=image.size
                if image.format!="PNG" or not (1<=width<=4096 and 1<=height<=4096) or width*height>8388608 or image.convert("RGBA").getchannel("A").getextrema()!=(0,255):
                    raise ValueError("透明靜物格式或 alpha 不符")
            for source in [image_path,prompt]:shutil.copyfile(source,args.out/source.name)
            manifest["overlays"].append({"source_index":index,"file":image_path.name,"sha256":expected,"width":width,"height":height,
                                         "sampling":"bitmap","background_source":0,"prompt_file":prompt.name,"prompt_sha256":sha(prompt)})
    if args.set=="current":
        if sha(args.source.parent/"MAN.AY")!="9849714498718f6616644ad717906cc426c3f3f5f335cdb99dbcc8173c8dbe12":
            raise ValueError("主角來源不符")
        manifest["actors"]=[]
        for frame,expected in ACTORS:
            name=f"actor-painted-{frame:02d}-r1"
            image_path=args.refs/(name+".png");prompt=args.refs/(name+".prompt.txt")
            if sha(image_path)!=expected or not prompt.is_file() or not prompt.read_text().strip():
                raise ValueError("主角 PNG 或提示不符")
            with Image.open(image_path) as image:
                width,height=image.size
                if image.format!="PNG" or not (1<=width<=4096 and 1<=height<=4096) or width*height>8388608 or image.convert("RGBA").getchannel("A").getextrema()!=(0,255):
                    raise ValueError("主角 PNG 格式或 alpha 不符")
            for source in [image_path,prompt]:shutil.copyfile(source,args.out/source.name)
            manifest["actors"].append({"source_index":72+frame,"file":image_path.name,"sha256":expected,"width":width,"height":height,
                                       "sampling":"bitmap","prompt_file":prompt.name,"prompt_sha256":sha(prompt)})
    if args.set in ("current","objects","interface"):
        manifest["ui"]={"style":"jade-gold-v1","paper_source":46}
    for name in ["font.json","font.png"]:
        shutil.copyfile(args.font_assets/name,args.out/name)
    (args.out / "terrain.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    for p in args.out.iterdir():
        if (p.stat().st_uid,p.stat().st_gid)!=(os.getuid(),os.getgid()):
            raise ValueError("輸出檔擁有權不符")
    print(json.dumps({"materials":len(manifest["materials"]),"composites":len(manifest["composites"]),"overlays":len(manifest.get("overlays",[])),"actors":len(manifest.get("actors",[])),"ui":3 if "ui" in manifest else 0,"manifest_sha256":sha(args.out/"terrain.json"),
                      "rights":manifest["rights"],"generated_png_bytes":"preserved"}))

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--refs",type=Path,required=True)
    parser.add_argument("--font-assets",type=Path,required=True)
    parser.add_argument("--style-reference",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--set",choices=["ground","landscape","portrait","interface","objects","current"],default="current")
    prepare(parser.parse_args())
