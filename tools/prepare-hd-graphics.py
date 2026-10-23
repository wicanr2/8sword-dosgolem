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
             (68, "hero-portrait-r1", "8150858af91388a8fb46587c55a3ff83df6e51d1bf7bb2b9eb8b9d03d99a1533",0,0)]

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
    selected=MATERIALS if args.set in ("current","portrait") else MATERIALS[:4] if args.set=="landscape" else MATERIALS[:2]
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
    if args.set=="current":
        manifest["ui"]={"style":"jade-gold-v1","paper_source":46}
    for name in ["font.json","font.png"]:
        shutil.copyfile(args.font_assets/name,args.out/name)
    (args.out / "terrain.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    for p in args.out.iterdir():
        if (p.stat().st_uid,p.stat().st_gid)!=(os.getuid(),os.getgid()):
            raise ValueError("輸出檔擁有權不符")
    print(json.dumps({"materials":len(manifest["materials"]),"composites":len(manifest["composites"]),"ui":3 if "ui" in manifest else 0,"manifest_sha256":sha(args.out/"terrain.json"),
                      "rights":manifest["rights"],"generated_png_bytes":"preserved"}))

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--refs",type=Path,required=True)
    parser.add_argument("--font-assets",type=Path,required=True)
    parser.add_argument("--style-reference",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--set",choices=["ground","landscape","portrait","current"],default="current")
    prepare(parser.parse_args())
