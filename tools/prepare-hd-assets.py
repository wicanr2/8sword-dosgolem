#!/usr/bin/env python3
"""在容器製作執行期字型素材，來源固定，輸出只留本機。"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, __version__, features

PAM_SHA = "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"
FONT_SHA = "3cffb10242b4b7e6edd439ebf3bd7e392345525e093ea08149e0a0158a1b5151"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe", type=Path, required=True)
    p.add_argument("--font", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    assert a.out.is_dir()
    assert not (a.out / "font.json").exists() and not (a.out / "font.png").exists()
    data = a.exe.read_bytes()
    assert sha(data) == PAM_SHA and sha(a.font.read_bytes()) == FONT_SHA
    codes = data[0x2463e:0x24b36]
    chars = codes.decode("big5")
    assert len(chars) == len(set(chars)) == 636
    entries = [(c, codes[i*2:i*2+2].hex(), i) for i,c in enumerate(chars)]
    entries += [(chr(c), "", -1) for c in range(32,127)]
    columns,cell = 32,64
    rows = (len(entries)+columns-1)//columns
    image = Image.new("RGBA",(columns*cell,rows*cell),(255,255,255,0))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(a.font),48,index=3)
    assert font.getname() == ("Noto Sans CJK TC","Black")
    missing = font.getmask("\U0010ffff")
    missing_key = (missing.size,bytes(missing))
    glyphs=[]
    for ordinal,(c,code,index) in enumerate(entries):
        mask=font.getmask(c)
        assert c==" " or (mask.getbbox() and (mask.size,bytes(mask))!=missing_key),repr(c)
        box=draw.textbbox((0,0),c,font=font)
        width,height=box[2]-box[0],box[3]-box[1]
        assert width<=56 and height<=56,(c,box)
        x,y=(ordinal%columns)*cell,(ordinal//columns)*cell
        ox,oy=x+(cell-width)//2-box[0],y+(cell-height)//2-box[1]
        draw.text((ox,oy),c,font=font,fill=(255,255,255,255))
        glyphs.append({"character":c,"big5":code,"source_index":index,
                       "cell":[x,y,cell,cell],"ink":[int(ox+box[0]),int(oy+box[1]),width,height]})
    image.save(a.out/"font.png")
    manifest={"schema":1,"source_sha256":PAM_SHA,"font_sha256":FONT_SHA,
              "family":"Noto Sans CJK TC","weight":900,"collection_index":3,"font_px":48,
              "atlas":"font.png","atlas_sha256":sha((a.out/"font.png").read_bytes()),
              "width":image.width,"height":image.height,"glyphs":glyphs,
              "tools":{"pillow":__version__,"freetype":features.version("freetype2")},
              "rights":"local generated font assets; Noto remains under SIL OFL 1.1; original code mapping is not relicensed"}
    (a.out/"font.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({"glyphs":len(glyphs),"missing":0,"atlas_sha256":manifest['atlas_sha256'],
                      "manifest_sha256":sha((a.out/"font.json").read_bytes())},ensure_ascii=False))

if __name__=="__main__":
    main()
