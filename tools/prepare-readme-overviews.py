"""在固定 Pillow 容器內重生 README 原版／HD 比較圖，不生成或猜補遊戲畫面。"""
import argparse
import hashlib
import json
from pathlib import Path
import runpy

from PIL import Image, ImageDraw, ImageFont, __version__


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    p, out = a.project, a.out
    names = ["monsters-original-hd-r1.png", "battle-original-hd-r1.png", "overviews-r1.json"]
    assert out.is_dir() and not any((out / n).exists() for n in names)
    g = p / "workplace/probe-20261023/graphics-first"
    r = g / "battle-r1"
    original = p / "workplace/intake-20261023/sources/game/8sword"
    catalog = runpy.run_path(str(p / "tools/catalog-battle-actors.py"))
    font_path = g / "font-settings-r1/NotoSansCJK-Black.ttc"
    font = lambda size: ImageFont.truetype(str(font_path), size, index=3)
    inputs = {}

    def track(path):
        inputs[path.relative_to(p).as_posix()] = sha(path)
        return path

    track(font_path)
    background = (35, 46, 48)

    def hd_tile(raw):
        assert len(raw) == 264 * 300 * 4
        rgb = bytearray(264 * 300 * 3)
        for i in range(264 * 300):
            alpha = raw[i * 4 + 3]
            for c in range(3):
                rgb[i * 3 + c] = min(255, raw[i * 4 + c] + (background[c] * (255-alpha)+127)//255)
        return Image.frombytes("RGB", (264, 300), bytes(rgb))

    sheet = Image.new("RGB", (2400, 1620), "#101b22")
    d = ImageDraw.Draw(sheet)
    d.text((36, 20), "原版／HD 怪物與敵方部隊總覽", font=font(44), fill="#f5d99a")
    d.text((36, 82), "四組已接入來源，共十六筆。每格左：原版；右：HD。記錄編號不代表動作名稱。", font=font(25), fill="#d3dde1")
    monsters = []
    for row, unit in enumerate(["MAN16", "MAN06", "MAN11", "MAN21"]):
        source = track(original / (unit + ".EGG"))
        raw = source.read_bytes()
        assert sha(source) == catalog["SOURCES"][unit + ".EGG"] and len(raw) == 13216
        y = 150 + row * 360
        d.text((22, y + 140), unit, font=font(25), fill="#f5d99a")
        for i in range(4):
            x = 148 + i * 558
            d.rectangle((x-4, y-4, x+544, y+340), outline="#596c6b", width=2)
            d.text((x+20, y+4), f"記錄 {i}    原版                    HD", font=font(22), fill="#d3dde1")
            tile = Image.new("RGBA", (264, 300), background + (255,))
            native = catalog["decode"](raw[i*3304:(i+1)*3304]).resize((264, 300), Image.Resampling.NEAREST)
            tile = Image.alpha_composite(tile, native).convert("RGB")
            cache = track(r / (unit.lower() + "-art-r1") / f"cache-frame-{i}.rgba")
            sheet.paste(tile, (x, y+36))
            sheet.paste(hd_tile(cache.read_bytes()), (x+276, y+36))
            monsters.append(dict(source=unit+".EGG", record=i, offset=i*3304,
                                 original_rgba_sha256=hashlib.sha256(native.tobytes()).hexdigest(),
                                 HD_cache_sha256=sha(cache), action_semantics="unknown"))
    sheet.save(out / names[0])

    sheet = Image.new("RGB", (2400, 1700), "#101b22")
    d = ImageDraw.Draw(sheet)
    d.text((36, 20), "原版／HD 戰場總覽", font=font(44), fill="#f5d99a")
    d.text((36, 82), "每列為相同原版狀態。原版由實際 VGA 索引與當時色盤重建；右側為已接入的 HD。", font=font(25), fill="#d3dde1")
    battles = []
    for row, (point, label) in enumerate([("01-counts", "戰場與兵力"), ("07-pon-3-return", "交戰火花")]):
        root = r / "militia-hd-r1"
        layers = json.loads(track(root / (point+"-layers.json")).read_text())
        assert not layers["pending"]
        indices = track(root / (point+"-native.idx")).read_bytes()
        assert len(indices) == 128000 and max(indices) < 16
        palette = layers["display"]["Palette"]
        im = Image.frombytes("P", (640, 200), indices)
        im.putpalette([v for rgb in palette for v in rgb] + [0]*(768-48))
        native = im.convert("RGB").resize((1920, 1200), Image.Resampling.NEAREST)
        hd = Image.open(track(root / (point+".png"))).convert("RGB")
        assert hd.size == (1920, 1200)
        before, after = track(root/(point+"-before.state")), track(root/(point+"-after.state"))
        assert before.read_bytes() == after.read_bytes()
        y = 140 + row * 770
        d.text((30, y), label+"　原版", font=font(28), fill="#f5d99a")
        d.text((1220, y), label+"　HD", font=font(28), fill="#f5d99a")
        sheet.paste(native.resize((1152, 720), Image.Resampling.NEAREST), (30, y+42))
        sheet.paste(hd.resize((1152, 720), Image.Resampling.LANCZOS), (1220, y+42))
        status = json.loads(track(root/(point+".json")).read_text())
        battles.append(dict(point=point, step=status["steps"], state_sha256=sha(before),
                            original_RGBA_source="actual VGA indices plus captured palette; no DOSBox or generated replacement",
                            native_index_sha256=sha(root/(point+"-native.idx")), HD_frame_sha256=sha(root/(point+".png"))))
    sheet.save(out / names[1])
    meta = dict(schema=1, tool="Pillow "+__version__, script_sha256=sha(Path(__file__)),
                sources=inputs, monsters=monsters, battles=battles,
                outputs={n:sha(out/n) for n in names[:2]},
                user_authorization="使用者要求將原版／HD 怪物總覽及戰場總覽放入 README；限既有私人倉庫的比較圖。",
                scope="四組十六筆敵方來源；兩個相同狀態戰場抽樣。不是全遊戲／全怪物完成聲明。",
                rights="Comparison documentation only; no original game files, full-resolution asset packs or public redistribution grant.")
    (out/names[2]).write_text(json.dumps(meta, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(dict(outputs=meta["outputs"], monsters=len(monsters), battles=len(battles))))


if __name__ == "__main__":
    main()
