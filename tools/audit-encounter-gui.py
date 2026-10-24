#!/usr/bin/env python3
"""037–039：從原生像素、所有權、PNG 與字型重建實際中央 Draw。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
import struct
from pathlib import Path

from PIL import Image, ImageDraw

EGA = [(0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170),
       (170, 0, 0), (170, 0, 170), (170, 85, 0), (170, 170, 170),
       (85, 85, 85), (85, 85, 255), (85, 255, 85), (85, 255, 255),
       (255, 85, 85), (255, 85, 255), (255, 255, 85), (255, 255, 255)]


def read(path):
    return json.loads(path.read_text())


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sample(path, width, height, actor=False, periodic=False, rect=None, background=None):
    im = Image.open(path).convert("RGBA")
    if rect:
        x, y, w, h = rect
        im = im.crop((x, y, x + w, y + h))
    sw, sh = im.size
    pixels = im.load()
    out = bytearray(width * height * 4)
    for y in range(height):
        sy = max(0, (y + .5) * sh / height - .5)
        y0, fy = int(sy), sy - int(sy)
        y1 = min(y0 + 1, sh - 1)
        for x in range(width):
            sx = max(0, (x + .5) * sw / width - .5)
            x0, fx = int(sx), sx - int(sx)
            x1 = min(x0 + 1, sw - 1)
            sums = [0.] * 4
            for (xx, yy), weight in zip([(x0, y0), (x1, y0), (x0, y1), (x1, y1)],
                                        [(1-fx)*(1-fy), fx*(1-fy), (1-fx)*fy, fx*fy]):
                r, g, b, a = pixels[xx, yy]
                if actor and a <= 3:
                    continue
                if not actor:
                    assert a == 255
                values = [v * 257 * a // 255 for v in [r, g, b]] + [a * 257] if actor else [r, g, b, 255]
                for c, v in enumerate(values):
                    sums[c] += weight * v
            at = (y * width + x) * 4
            if background is None:
                out[at:at+4] = bytes(min(255, int((v / 257 if actor else v) + .5)) for v in sums)
            else:
                alpha = sums[3] / 65535
                out[at:at+4] = bytes([int(max(0, min(255, sums[c]/257+background[at+c]*(1-alpha)))+.5) for c in range(3)]+[255])
    if periodic:
        prior = bytes(out)
        for y in range(height):
            for x in range(width):
                ax, ay = .5 * max(0, 1 - min(x, width-1-x) / 16), .5 * max(0, 1 - min(y, height-1-y) / 16)
                points = [(x, y), (width-1-x, y), (x, height-1-y), (width-1-x, height-1-y)]
                weights = [(1-ax)*(1-ay), ax*(1-ay), (1-ax)*ay, ax*ay]
                for c in range(3):
                    out[(y*width+x)*4+c] = int(sum(prior[(yy*width+xx)*4+c]*w for (xx, yy), w in zip(points, weights))+.5)
    return bytes(out)


def ui(index, paper):
    w, h = {69: (1224, 120), 70: (1344, 450), 71: (1920, 1200)}[index]
    im = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    d = ImageDraw.Draw(im)
    gold, light, bronze = (216, 174, 78, 255), (255, 233, 159, 255), (105, 66, 25, 255)
    def fill(r, color):
        if r[2] > r[0] and r[3] > r[1]:
            d.rectangle((r[0], r[1], r[2]-1, r[3]-1), fill=color)
    def inset(r, n):
        return r[0]+n, r[1]+n, r[2]-n, r[3]-n
    def outline(r, n, color):
        x, y, xx, yy = r
        for q in [(x, y, xx, y+n), (x, yy-n, xx, yy), (x, y+n, x+n, yy-n), (xx-n, y+n, xx, yy-n)]:
            fill(q, color)
    def key(x, y):
        outline((x, y, x+16, y+16), 2, gold)
        for r in [(x+4, y+4, x+12, y+6), (x+10, y+4, x+12, y+12), (x+5, y+10, x+12, y+12)]:
            fill(r, light)
    def bar(r):
        fill(r, bronze)
        outline(inset(r, 1), 2, light)
        q = inset(r, 4)
        for y in range(max(0, q[1]), min(h, q[3])):
            for x in range(max(0, q[0]), min(w, q[2])):
                a = ((y % 150)*192+x % 192)*4
                rr, gg, bb = paper[a:a+3]
                im.putpixel((x, y), (rr//2+4, gg*3//4+26, bb*3//4+18, 255))
        outline(q, 1, gold)
        if r[2]-r[0] > 80 and r[3]-r[1] >= 24:
            key(r[0]+7, r[1]+(r[3]-r[1]-16)//2)
            key(r[2]-23, r[1]+(r[3]-r[1]-16)//2)
    if index in [69, 70]:
        bar((0, 0, w, h))
        if index == 70:
            fill((18, 18, w-18, h-18), (85, 85, 85, 255))
            outline((17, 17, w-17, h-17), 1, gold)
    else:
        rects = [(0, 2, 8, 199), (456, 2, 465, 199), (632, 2, 640, 199), (8, 2, 456, 12), (8, 187, 456, 192)]
        rects += [(465, 2+r*27, 632, 9+r*27) for r in range(8)]
        for x, y, xx, yy in rects:
            bar((x*3, y*6, xx*3, yy*6))
        outline((24, 1146, 1368, 1188), 3, gold)
    return im.tobytes(), w//3, h//6


class Model:
    def __init__(self, assets, original, cache):
        self.assets, self.cache = assets, cache
        self.manifest = read(assets / "terrain.json")
        self.materials, self.actors, self.fonts, self.native = {}, {}, {}, []
        raw = (original / "PMAP.AY").read_bytes()
        assert hashlib.sha256(raw).hexdigest() == self.manifest["source_sha256"]
        at = 0
        while at < len(raw):
            w, h = struct.unpack_from("<HH", raw, at)
            area = w*h
            pixels = bytes(sum(((raw[at+4+p*area+i//8] >> (7-i%8)) & 1) << p for p in range(4)) for i in range(area*8))
            self.native.append((w*8, h, pixels))
            at += 4+area*5
        assert len(self.native) == 68 and at == len(raw)
        self.native += [(80, 40, b""), (408, 20, b""), (448, 75, b""), (640, 200, b"")]
        self.entries = {e["source_index"]+1: e for e in self.manifest["materials"]}
        self.composites = {e["source_index"]+1: e for e in self.manifest.get("composites", [])}
        self.overlays = {e["source_index"]+1: e for e in self.manifest.get("overlays", [])}
        self.actor_entries = {e["source_index"]+1: e for e in self.manifest["actors"]}
        self.font_entries = {"noto": read(assets / "font.json")}
        self.font_entries.update({p["id"]: p for p in read(assets / "font-choices.json")["profiles"]})

    def material(self, ident):
        if ident in self.materials:
            return self.materials[ident]
        if 70 <= ident <= 72:
            result = ui(ident-1, self.material(47)[0])
        elif ident in self.entries:
            e = self.entries[ident]
            assert sha(self.assets / e["file"]) == e["sha256"]
            w, h, _ = self.native[ident-1]
            data = sample(self.assets/e["file"], w*3, h*6, periodic=e.get("sampling", "periodic") == "periodic", rect=e.get("source_rect"))
            result = data, w, h
        elif ident in self.overlays:
            e = self.overlays[ident]
            assert sha(self.assets/e["file"]) == e["sha256"]
            result = sample(self.assets/e["file"], 192, 150, actor=True, background=self.material(1)[0]), 64, 25
        elif ident in self.composites:
            e = self.composites[ident]
            rule = e["mask_rule"]
            detail = {"pmap-green-blue-v1": 2, "pmap-grass-rock-v1": 16, "pmap-grass-sand-v1": 31}[rule]
            land, other = self.material(1)[0], self.material(detail)[0]
            w, h, pixels = self.native[ident-1]
            assert (w, h) == (64, 25)
            pos, neg = {"pmap-green-blue-v1": ({2, 10, 14}, {1, 9, 11}),
                        "pmap-grass-rock-v1": ({2, 10}, {4, 12, 15}),
                        "pmap-grass-sand-v1": ({2, 10}, {7, 12, 13, 15})}[rule]
            labels = [1 if v in pos else -1 if v in neg else 0 for v in pixels]
            alpha = []
            for y in range(25):
                for x in range(64):
                    total = votes = 0
                    for iy, vy in enumerate([1, 2, 1]):
                        for ix, vx in enumerate([1, 2, 3, 4, 3, 2, 1]):
                            label = labels[max(0, min(24, y+iy-1))*64+max(0, min(63, x+ix-3))]
                            if label:
                                total += vx*vy
                                if label == 1:
                                    votes += vx*vy
                    ratio = votes/total if total else .5 if detail == 2 else 0
                    alpha.append(max(0, min(1, (ratio-.4)/.2)))
            data = bytearray(len(land))
            for y in range(150):
                for x in range(192):
                    sx, sy = max(0, (x+.5)/3-.5), max(0, (y+.5)/6-.5)
                    x0, y0 = int(sx), int(sy)
                    x1, y1 = min(x0+1, 63), min(y0+1, 24)
                    fx, fy = sx-x0, sy-y0
                    a = (alpha[y0*64+x0]*(1-fx)+alpha[y0*64+x1]*fx)*(1-fy)+(alpha[y1*64+x0]*(1-fx)+alpha[y1*64+x1]*fx)*fy
                    at = (y*192+x)*4
                    data[at:at+4] = bytes([int(land[at+c]*a+other[at+c]*(1-a)+.5) for c in range(3)]+[255])
            result = bytes(data), 64, 25
        else:
            raise AssertionError(("unmodeled material", ident))
        self.materials[ident] = result
        return result

    def actor(self, ident):
        if ident not in self.actors:
            if 139 <= ident <= 149:
                entry = read(self.assets / "map-encounter-7.json")["image"]
                assert sha(self.assets/entry["file"]) == "b5f71a301064ed1d2a050588d400b0fe9113289e9baa2e5bb39c4e66def4e1b0"
                sampled = sample(self.assets/entry["file"], 141, 132, actor=True, rect=[62, 54, 1298, 991])
                full = bytearray(192*150*4)
                for y in range(132):
                    at = ((y+18)*192+21)*4
                    full[at:at+141*4] = sampled[y*141*4:(y+1)*141*4]
                data = bytes(full)
                assert hashlib.sha256(data).hexdigest() == "9898de9adfd7db00aa65808077bce8774d45105e07454612b9ed6f89c093d126"
                result = data, 64, 5+(ident-139)*2
            elif 126 <= ident <= 138:
                entry = read(self.assets / "map-encounter-10.json")["image"]
                assert sha(self.assets/entry["file"]) == "53a599a6db8f10cf76d08de389fbf07b72b6f3c8f9fdf6647256c440809300ad"
                left = sample(self.assets/entry["file"], 192, 150, actor=True, rect=[123, 311, 1052, 902])
                data = b"".join(left[(y*192+x)*4:(y*192+x+1)*4]
                                for y in range(150) for x in range(191, -1, -1))
                assert hashlib.sha256(data).hexdigest() == "314e66eae62475a9076a3ea996885013dddb1f698d01c6466fd0a2bad27d4f74"
                result = data, 64, 1+(ident-126)*2
            elif 116 <= ident <= 125:
                entry = read(self.assets / "map-encounter.json")["image"]
                assert sha(self.assets/entry["file"]) == "81f72e1ad3e1363c38c49eed75fcd906302a74818f21845e073310026954e146"
                sampled = sample(self.assets/entry["file"], 186, 120, actor=True, rect=[11, 72, 1397, 1006])
                full = bytearray(192*150*4)
                for y in range(120):
                    at = ((y+30)*192+3)*4
                    full[at:at+186*4] = sampled[y*186*4:(y+1)*186*4]
                data = bytes(full)
                assert hashlib.sha256(data).hexdigest() == "da28fb22a5c5b6c6e40dbaf0e3e59d9d7b283d7f61064d0710b9d7f2c015ab97"
                reference = self.cache / "encounter-13-cache-r1.rgba"
                if reference.exists():
                    assert reference.read_bytes() == data
                result = data, 64, 7+(ident-116)*2
            else:
                e = self.actor_entries[ident]
                assert sha(self.assets/e["file"]) == e["sha256"]
                w, h = (88, 50) if ident == 85 else (64, 25)
                result = sample(self.assets/e["file"], w*3, h*6, actor=True), w, h
            self.actors[ident] = result
        return self.actors[ident]

    def font(self, ident):
        if ident not in self.fonts:
            e = self.font_entries[ident]
            assert sha(self.assets/e["atlas"]) == e["atlas_sha256"]
            self.fonts[ident] = Image.open(self.assets/e["atlas"]).convert("RGBA"), {ord(g["character"]): g["ink"] for g in e["glyphs"]}
        return self.fonts[ident]

    def frame(self, stem):
        path = lambda suffix: Path(str(stem)+suffix)
        meta = read(path(".json"))
        native = path("-native.idx").read_bytes()
        assert len(native) == 128000 and max(native) < 16
        assert sha(path("-before.state")) == sha(path("-after.state"))
        owners = list(struct.iter_unpack("<HI", path("-background.bin").read_bytes()))
        actors = list(struct.iter_unpack("<HI", path("-actors.bin").read_bytes()))
        text = list(struct.iter_unpack("<IHB", path("-text.bin").read_bytes()))
        glyphs = {int(k): v for k, v in read(path("-glyphs.json")).items()}
        assert len(owners) == len(actors) == len(text) == 128000
        assert not any(path("-effects.bin").read_bytes())
        # The supplied packets are map/encounter frames with the complete sidebar.
        sidebar_sources = {g["Source"] for g in glyphs.values() if g["Rune"] != 32}
        assert set(range(990, 1111, 20)) <= sidebar_sources
        palette = meta["display"]["Palette"]
        assert [tuple(c) for c in palette] == EGA
        base = bytearray(128000*4)
        groups = set()
        for i, color in enumerate(native):
            x, y = i % 640, i // 640
            ident, local, ink = text[i]
            g = glyphs.get(ident)
            if g:
                groups.add((ident, y-local//g["Width"], x-local % g["Width"]))
                if ink and color == g["FG"]:
                    color = g["Before"][local] if g["BG"] == 255 else g["BG"]
            rgb = palette[color & 15]
            if 8 <= x < 456 and 192 <= y < 198:
                rgb = {2: [36, 91, 56], 10: [110, 167, 92], 14: [223, 190, 102]}.get(color, rgb)
            if color == 12 and 472 <= x < 624 and 12 <= y < 189 and (y-12) % 27 < 15 and g and g["BG"] == 12:
                left, top = x-local % g["Width"], y-local//g["Width"]
                if g["Source"] == 990+(y-12)//27*20 and 472 <= left < 624 and top == 12+(y-12)//27*27:
                    rgb = [128, 45, 39]
            base[i*4:i*4+4] = bytes(rgb)+b"\xff"
        out = bytearray(Image.frombytes("RGBA", (640, 200), bytes(base)).resize((1920, 1200), Image.Resampling.NEAREST).tobytes())
        for i, (ident, local) in enumerate(owners):
            if not ident:
                continue
            data, w, h = self.material(ident)
            assert local < w*h
            x, y, sx, sy = i % 640, i//640, local % w, local//w
            for dy in range(6):
                dst, src = ((y*6+dy)*1920+x*3)*4, ((sy*6+dy)*w*3+sx*3)*4
                out[dst:dst+12] = data[src:src+12]
        for i, (ident, local) in enumerate(actors):
            if not ident:
                continue
            data, w, h = self.actor(ident)
            assert local < w*h
            x, y, sx, sy = i % 640, i//640, local % w, local//w
            for dy in range(6):
                for dx in range(3):
                    dst, src = ((y*6+dy)*1920+x*3+dx)*4, ((sy*6+dy)*w*3+sx*3+dx)*4
                    a = data[src+3]
                    for c in range(3):
                        out[dst+c] = min(255, data[src+c]+(out[dst+c]*(255-a)+127)//255)
        atlas, font = self.font(meta["font_id"])
        for ident, y, x in sorted(groups):
            g = glyphs[ident]
            if g["Rune"] == 32:
                continue
            ix, iy, iw, ih = font[g["Rune"]]
            if iw <= 0 or ih <= 0:
                continue
            dw, dh = min(iw, g["Width"]*3), min(ih, 90)
            left, top = x*3+(g["Width"]*3-dw)//2, y*6+(90-dh)//2
            color = {10: [223, 195, 121], 12: [215, 112, 89], 14: [255, 241, 181]}.get(g["FG"], palette[g["FG"]])
            for yy in range(dh):
                for xx in range(dw):
                    ox, oy = left+xx, top+yy
                    if not (0 <= ox < 1920 and 0 <= oy < 1200):
                        continue
                    nx, ny = ox//3, oy//6
                    owner, local, _ = text[ny*640+nx]
                    if owner != ident or local % g["Width"] != nx-x or local//g["Width"] != ny-y:
                        continue
                    a = atlas.getpixel((ix+xx*iw//dw, iy+yy*ih//dh))[3]
                    at = (oy*1920+ox)*4
                    for c in range(3):
                        out[at+c] = (color[c]*a+out[at+c]*(255-a)+127)//255
        actual = Image.open(path(".png")).convert("RGBA").tobytes()
        if bytes(out) != actual:
            mismatch = sum(a != b for a, b in zip(out, actual))
            Image.frombytes("RGBA", (1920, 1200), bytes(out)).save(path("-model-failed.png"))
            raise AssertionError((stem.name, "whole-frame mismatch bytes", mismatch))
        return dict(packet=stem.name, actual_draw=meta["actual_draw"], step=meta["step"], height=meta["height"],
                    font_id=meta["font_id"], full_pixels=2304000, state_pure=True,
                    rgba_sha256=hashlib.sha256(actual).hexdigest(),
                    material_ids=sorted({i for i, _ in owners if i}), actor_ids=sorted({i for i, _ in actors if i}))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ["assets", "original", "cache", "receipt", "out"]:
        ap.add_argument("--"+name, type=Path, required=True)
    ap.add_argument("--record", type=int, choices=[7, 10, 13], default=13)
    a = ap.parse_args()
    assert not a.out.exists()
    root = a.receipt / "save"
    packets = [p for p in sorted((root / "research-encounter-draws").glob("*-first-draw.json"))
               if read(p)["record"] == a.record]
    assert packets
    sources = read(root / "research-encounter-sources.json")
    assert not sources["error"] and sources[f"full{a.record}_count"] >= 2
    model = Model(a.assets, a.original, a.cache)
    results = [model.frame(p.with_suffix("")) for p in packets]
    for p, result in zip(packets, results):
        meta = read(p)
        assert meta["record"] == a.record
        raw_path = root / ("encounter-source-"+meta["source_sha256"]+".bin")
        assert sha(raw_path) == meta["source_sha256"]
        h = meta["height"]
        raw = raw_path.read_bytes()
        assert struct.unpack_from("<HH", raw) == (8, h) and len(raw) == 4+48*h
        candidates = [c for c in sources["calls"] if c["source_sha256"] == meta["source_sha256"]
                      and c["return_step"] <= meta["step"]
                      and c["first_physical_byte"] == meta["display"]["Start"]+c["args"][3]*80+c["args"][2]]
        assert candidates
        call = candidates[-1]
        assert call["records"] == [a.record] and call["args"][3]+h == 112
        native = p.with_name(p.name.removesuffix(".json")+"-native.idx").read_bytes()
        pixels = 0
        for y in range(h):
            for x in range(64):
                at, bit = y*8+x//8, 7-x%8
                if (raw[4+5*8*h+at] >> bit) & 1:
                    color = sum(((raw[4+q*8*h+at] >> bit) & 1) << q for q in range(4))
                    assert native[(call["args"][3]+y)*640+call["args"][2]*8+x] == color
                    pixels += 1
        result["original_masked_pixels"] = pixels
        result["original_return_step"] = call["return_step"]
    assert {r["font_id"] for r in results if r["height"] == 25} == {"noto", "lishu", "caoshu"}
    assert len({r["height"] for r in results}) >= 2
    # Link each exact central Draw to the original full-width recorder.
    spec = importlib.util.spec_from_file_location("frames", Path(__file__).with_name("audit-army-dismiss.py"))
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    wanted = {r["actual_draw"]: r for r in results}
    for ordinal, step, frame in helper.stream(root):
        if ordinal not in wanted:
            continue
        record = wanted.pop(ordinal)
        assert frame.size == (1920, 1200) and step == record["step"]
        assert hashlib.sha256(frame.tobytes()).hexdigest() == record["rgba_sha256"]
    assert not wanted
    result = dict(schema=1, status="passed-independent-actual-Draws", packets=results,
                  source_calls=len(sources["calls"]), **{f"source_full{a.record}_calls": sources[f"full{a.record}_count"]},
                  actual_stream_link=True, formal_source_roles="unknown", gui_receipt=str(a.receipt),
                  limitation="sampled actual central Draws, native layers and PNG/font reconstruction; gameplay/RNG and full game are outside scope",
                  tool_sha256=sha(Path(__file__)))
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(dict(status=result["status"], packets=len(results), heights=sorted({r["height"] for r in results}))))


if __name__ == "__main__":
    main()
