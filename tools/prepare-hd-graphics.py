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
MATERIALS = [(0, "grass-painted-r1", "4e6baf80381f064a8da9d9fa6c09e7a3009498da0dfd11c8472f449d7ed14992"),
             (1, "water-painted-r1", "6a0fc05d7911bbf2d318f697e9361f19a09ed4c3c1d172d46eb09c400af70e93")]

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
    for index,name,expected in MATERIALS:
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
        manifest["materials"].append({"source_index":index,"file":image_path.name,"sha256":expected,
                                     "width":width,"height":height,"prompt_file":prompt.name,"prompt_sha256":sha(prompt),
                                     "sampling":"periodic","source_rect":[(width-256)//2,(height-200)//2,256,200]})
    manifest["composites"]=[{"source_index":i,"land_source":0,"water_source":1,"mask_rule":"pmap-green-blue-v1"} for i in range(2,14)]
    for name in ["font.json","font.png"]:
        shutil.copyfile(args.font_assets/name,args.out/name)
    (args.out / "terrain.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    for p in args.out.iterdir():
        if (p.stat().st_uid,p.stat().st_gid)!=(os.getuid(),os.getgid()):
            raise ValueError("輸出檔擁有權不符")
    print(json.dumps({"materials":len(manifest["materials"]),"composites":len(manifest["composites"]),"manifest_sha256":sha(args.out/"terrain.json"),
                      "rights":manifest["rights"],"generated_png_bytes":"preserved"}))

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--refs",type=Path,required=True)
    parser.add_argument("--font-assets",type=Path,required=True)
    parser.add_argument("--style-reference",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    prepare(parser.parse_args())
