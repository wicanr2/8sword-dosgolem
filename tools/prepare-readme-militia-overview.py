"""README 原版／HD 民兵動作總覽；只輸出比較圖與來源，不複製原素材。"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, __version__


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--battle", type=Path, required=True)
    p.add_argument("--fonts", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    assert __version__ == "11.3.0" and a.out.is_dir() and a.out.stat().st_uid == 1000
    name = "battle-militia-poses-original-hd-r1"
    image_path, record_path = a.out / (name + ".png"), a.out / (name + ".json")
    assert not image_path.exists() and not record_path.exists()
    font_path = a.fonts / "NotoSansCJK-Black.ttc"
    font = ImageFont.truetype(str(font_path), 28, index=3)
    large = ImageFont.truetype(str(font_path), 34, index=3)
    im = Image.new("RGB", (1600, 830), "#142720")
    d = ImageDraw.Draw(im)
    d.text((20, 10), "民兵動作：原版／HD", font=large, fill="#fff0b9")
    rows = []
    for i in [1, 2, 3]:
        stem = f"pose-{i}-first-return"
        hd = a.battle / "man01-runtime-hd-r1"
        old = a.battle / "man01-runtime-old-r1"
        broken = a.battle / "man01-runtime-broken-r1"
        states = [r / (stem + "-before.state") for r in [hd, old, broken]]
        assert len({sha(f) for f in states}) == 1
        meta = json.loads((hd / (stem + ".json")).read_text())
        assert all(json.loads((r / (stem + ".json")).read_text())["steps"] == meta["steps"] for r in [old, broken])
        native_path, hd_path = hd / (stem + "-native.png"), hd / (stem + "-hd.png")
        native, painted = Image.open(native_path), Image.open(hd_path)
        assert native.size == painted.size == (1920, 1200)
        assert sha(native_path) == sha(old / native_path.name) == sha(broken / native_path.name)
        x = 16 + (i - 1) * 528
        d.text((x, 58), f"原版・姿勢 {i}", font=font, fill="#dce5df")
        d.text((x, 426), f"HD・姿勢 {i}", font=font, fill="#fff0b9")
        im.paste(native.convert("RGB").resize((512, 320), Image.Resampling.LANCZOS), (x, 96))
        im.paste(painted.convert("RGB").resize((512, 320), Image.Resampling.LANCZOS), (x, 464))
        rows.append(dict(record=i, step=meta["steps"], full_guest_state_sha256=sha(states[0]),
                         native_file=str(native_path.relative_to(a.battle)), native_sha256=sha(native_path),
                         hd_file=str(hd_path.relative_to(a.battle)), hd_sha256=sha(hd_path),
                         scope="same complete guest state at the first completed original draw; appearance differs"))
    d.text((20, 791), "正常選中敵方後的三個姿勢。相同客體狀態，完整中央戰場；未驗範圍見 036。", font=font, fill="#c0d1c7")
    im.save(image_path)
    provenance = dict(schema=1, spec="036", tool="Pillow " + __version__, output=image_path.name,
                      sha256=sha(image_path), size=im.size, font="Noto Sans CJK TC Black 900",
                      font_sha256=sha(font_path), font_index=3, sources=rows,
                      rights="original/HD comparison montage requested by user for existing private README; no raw asset or public distribution grant")
    record_path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(dict(output=image_path.name, sha256=provenance["sha256"], states=[r["full_guest_state_sha256"] for r in rows])))


if __name__ == "__main__":
    main()
