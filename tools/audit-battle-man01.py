"""036：正常三組隔離、完整返回圖及實際 Draw 的獨立重建。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
import runpy
import struct
from itertools import zip_longest
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

spec = importlib.util.spec_from_file_location("army_audit", Path(__file__).with_name("audit-army-dismiss.py"))
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def read(p):
    return json.loads(p.read_text())


def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def files(p):
    return {str(f.relative_to(p)): sha(f) for f in p.rglob("*") if f.is_file()}


def blend(dst, at, cache, src):
    alpha = cache[src + 3]
    for c in range(3):
        dst[at + c] = min(255, cache[src + c] + (dst[at + c] * (255 - alpha) + 127) // 255)
    dst[at + 3] = 255


def references(a):
    assert sha(a.original / "MAN01.EGG") == "a7e02cf495800fac19c293688043f3af6eb6deaec1a61a581ed3f9d5b8b3e5f1"
    assert sha(a.assets / "battle-background-r1.png") == "4ec05b750acd05b1d86af6706fa9cec8f60ddf9123c30f6cd4b5a2c5dd3c59f2"
    bg = Image.open(a.battle / "production-background-r9/sampled-background-cache.png").convert("RGBA")
    assert bg.size == (1920, 1200)
    assert hashlib.sha256(bg.tobytes()).hexdigest() == "5e0bb6b8ed2f45054bf722ef0282227daef20c16719909ce0cdbe0d1cbb23cb7"
    cache_hashes = ["3787d0a7b5eead1f97bd925080b7ff8fe2e54c84d0627bab27fb389d57e3b092", "5b1a69b1b40db4bc021bb3c2dce8af2409f274df4fd4a0b18536dffa27ca03bc", "5c329d56db28db83bb74725b1155a0baa01be33ae51c8f986edb9540769dd875"]
    caches = {}
    for i, expected in enumerate(cache_hashes, 1):
        p = a.battle / f"man01-mirror-{i}-cache-r1.rgba"
        assert sha(p) == expected and p.stat().st_size == 264 * 300 * 4
        caches[112 + i] = p.read_bytes()
    return bg, caches


def normal(a, bg, caches):
    roots = [a.hd, a.control, a.broken]
    states = [read(p / "final.json") for p in roots]
    for name in ["final.state", "audio.pcm", "commands.jsonl"]:
        assert len({sha(p / name) for p in roots}) == 1, name
    assert sha(a.hd / "final.state") == "3ad73d0b573815c93f42ca23c6588f6c5239c7bb6b516918dd3cf7cdcefab399"
    assert all(files(p / "scratch") == files(roots[0] / "scratch") for p in roots)
    for key in ["steps", "input_events", "file_ops", "exec_log", "strings", "exited", "exit_code"]:
        assert all(s[key] == states[0][key] for s in states), key
    for s in states:
        assert s["recorded_frames"] == 647 and s["return_frame_pure_count"] == 3
        assert s["exited"] and s["exit_code"] == 0
        assert not s["text"]["MissingGlyphs"] and not s["text"]["Errors"]
        for key in ["asset_error", "graphics_error", "font_error", "battle_background_error", "battle_effect_error", "battle_marker_error"]:
            assert not s[key], key
    assert not states[0]["battle_actor_error"] and not states[1]["battle_actor_error"]
    assert "MAN01.EGG" in states[2]["battle_actor_error"] and "SHA-256" in states[2]["battle_actor_error"]
    assert states[0]["graphics_actor_materials"] == states[1]["graphics_actor_materials"] + 3
    assert states[2]["graphics_actor_materials"] == states[1]["graphics_actor_materials"]
    calls = [json.loads(x) for x in (a.hd / "unit-calls.jsonl").read_text().splitlines()]
    added = [c for c in calls if c["catalog"] != "MAN01.EGG/0/mirror"]
    assert {c["catalog"] for c in added} == {f"MAN01.EGG/{i}/mirror" for i in [1, 2, 3]}
    assert states[0]["graphics"]["BattleActorCalls"] == states[1]["graphics"]["BattleActorCalls"] + len(added)
    assert states[0]["graphics"]["BattleActorFallbackCalls"] == 0
    mask = Image.new("L", (1920, 1200))
    d = ImageDraw.Draw(mask)
    for c in added:
        x, y = c["args"][2] * 24, c["args"][3] * 6
        d.rectangle((x, y, x + 263, y + 299), fill=255)
    inverse = ImageChops.invert(mask)
    changed = []
    for frames in zip_longest(*(helper.stream(p) for p in roots)):
        assert all(v is not None for v in frames)
        (n, step, im), (cn, cs, ci), (bn, bs, bi) = frames
        assert (n, step) == (cn, cs) == (bn, bs)
        assert ci.tobytes() == bi.tobytes(), ("fault frame", n)
        diff = ImageChops.difference(im.convert("RGB"), ci.convert("RGB"))
        channel = ImageChops.lighter(ImageChops.lighter(diff.getchannel("R"), diff.getchannel("G")), diff.getchannel("B"))
        assert not ImageChops.multiply(channel, inverse).getbbox(), ("outside actual source rectangles", n)
        if diff.getbbox():
            changed.append(n)
    assert n == 647 and changed
    returned = []
    for i in [1, 2, 3]:
        name = f"pose-{i}-first-return"
        meta = read(a.hd / (name + ".json"))
        source = next(c for c in added if c["catalog"] == f"MAN01.EGG/{i}/mirror")
        assert meta["steps"] == source["return_step"]
        x, y = source["args"][2] * 24, source["args"][3] * 6
        expected = bytearray(Image.open(a.control / (name + "-hd.png")).convert("RGBA").tobytes())
        background = bg.tobytes()
        for yy in range(300):
            for xx in range(264):
                at = ((y + yy) * 1920 + x + xx) * 4
                expected[at:at + 4] = background[at:at + 4]
                blend(expected, at, caches[112 + i], (yy * 264 + xx) * 4)
        got = Image.open(a.hd / (name + "-hd.png")).convert("RGBA").tobytes()
        assert bytes(expected) == got, ("complete return reconstruction", i)
        for root in roots:
            assert sha(root / (name + "-before.state")) == sha(root / (name + "-after.state"))
            assert sha(root / (name + "-native.png")) == sha(a.control / (name + "-native.png"))
        returned.append(dict(record=i, step=meta["steps"], full_pixels=2304000))
    return dict(status="passed-normal-three-poses", frames_per_run=647, return_frame_pure_count=9,
                state_sha256=sha(a.hd / "final.state"), pcm_sha256=sha(a.hd / "audio.pcm"),
                scratch_files=len(files(a.hd / "scratch")), new_source_calls=len(added),
                changed_frames=changed, returned=returned, all_fault_frames_equal_control=True,
                limit="three full first-return reconstructions; every-frame differences bounded by actual new-source rectangles; no per-frame guest state claim")


def gui(a, bg, caches):
    root = a.receipt
    phase = root / "save"
    sources = read(phase / "research-sources.json")
    assert not sources["error"] and sources["source"] == "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"
    calls = sources["calls"]
    assert {c["record"] for c in calls} == set(range(4))
    for c in calls:
        assert c["entry"] == 0x626 and c["entry_step"] < c["return_step"]
        assert sha(phase / ("battle-source-" + c["source_sha256"] + ".bin")) == c["source_sha256"]
    for group, unit in enumerate(["man16", "man06", "man11", "man21"]):
        for i in range(4):
            caches[87 + group * 4 + i] = (a.battle / (unit + "-art-r1") / f"cache-frame-{i}.rgba").read_bytes()
    caches[107] = (a.battle.parent / "army-r1/militia-independent-cache.rgba").read_bytes()
    palette = runpy.run_path(str(Path(__file__).with_name("catalog-battle-actors.py")))["PALETTE"]
    decoder = runpy.run_path(str(Path(__file__).with_name("prepare-hd-intro.py")))["decode"]
    original_bg = decoder((a.original / "GRO02.EG").read_bytes())
    bgbytes = bg.tobytes()
    wanted = {}
    packets = []
    for i in [1, 2, 3]:
        stem = phase / "research-man01-draws" / f"record-{i}-first-draw"
        path = lambda suffix: Path(str(stem) + suffix)
        meta = read(path(".json"))
        assert meta["record"] == i and not meta["status"]["visible_sources"]
        assert sha(path("-before.state")) == sha(path("-after.state"))
        assert not read(path("-layers.json"))["effects"]
        assert not any(path("-effects.bin").read_bytes())
        native = path("-native.idx").read_bytes()
        selected = [c for c in calls if c["record"] == i and c["return_step"] <= meta["step"]][-1]
        assert selected["source_sha256"] == meta["source_sha256"]
        raw = (phase / ("battle-source-" + meta["source_sha256"] + ".bin")).read_bytes()
        x0, y0 = selected["args"][2] * 8, selected["args"][3]
        for y in range(50):
            for x in range(88):
                at, bit = y * 11 + x // 8, 7 - x % 8
                if (raw[2754 + at] >> bit) & 1:
                    color = sum(((raw[4 + q * 550 + at] >> bit) & 1) << q for q in range(4))
                else:
                    at = (y0 + y) * 80 + (x0 + x) // 8
                    color = sum(((original_bg[4 + q * 16000 + at] >> bit) & 1) << q for q in range(4))
                assert native[(y0 + y) * 640 + x0 + x] == color, ("actual original pixels", i, x, y)
        im = Image.frombytes("P", (640, 200), native)
        im.putpalette([v for rgb in palette for v in rgb] + [0] * (768 - 48))
        expected = bytearray(im.convert("RGBA").resize((1920, 1200), Image.Resampling.NEAREST).tobytes())
        owners = list(struct.iter_unpack("<HI", path("-background.bin").read_bytes()))
        actors = list(struct.iter_unpack("<HI", path("-actors.bin").read_bytes()))
        occupied = 0
        for cell, (owner, local) in enumerate(owners):
            if not owner:
                continue
            assert owner == 86 and local < 128000
            x, y, bx, by = cell % 640, cell // 640, local % 640, local // 640
            for dy in range(6):
                at = ((y * 6 + dy) * 1920 + x * 3) * 4
                src = ((by * 6 + dy) * 1920 + bx * 3) * 4
                expected[at:at + 12] = bgbytes[src:src + 12]
        for cell, (actor, local) in enumerate(actors):
            if not actor:
                continue
            assert actor in caches and local < 4400
            x, y, ax, ay = cell % 640, cell // 640, local % 88, local // 88
            if actor == 112 + i:
                assert (x - x0, y - y0) == (ax, ay)
                occupied += 1
            for dy in range(6):
                for dx in range(3):
                    blend(expected, ((y * 6 + dy) * 1920 + x * 3 + dx) * 4,
                          caches[actor], ((ay * 6 + dy) * 264 + ax * 3 + dx) * 4)
        assert occupied == 4400
        got = Image.open(path(".png")).convert("RGBA").tobytes()
        assert bytes(expected) == got, ("complete actual Draw", i)
        wanted[meta["actual_draw"]] = (meta["step"], got)
        packets.append(dict(record=i, actual_draw=meta["actual_draw"], step=meta["step"], full_pixels=2304000, original_pixels=4400))
    linked = []
    for n, step, im in helper.stream(phase):
        if n in wanted:
            assert (step, im.tobytes()) == wanted[n]
            linked.append(n)
    assert set(linked) == set(wanted)
    for name in ["save", "reload"]:
        final = read(root / name / "gui-final.json")
        assert final["closed"] and not final["text"]["MissingGlyphs"] and not final["text"]["Errors"]
        for k in ["font_error", "graphics_error", "battle_actor_error", "battle_background_error", "battle_marker_error", "battle_effect_error"]:
            assert not final[k], k
        assert read(root / name / "continuous-audit.json")["frames"] == final["recorded_frames"]
    return dict(status="passed-three-actual-Draw-full-reconstruction", packets=packets,
                chronological_records=[p["record"] for p in sorted(packets, key=lambda p: p["actual_draw"])],
                source_calls=len(calls), actual_stream_link=True, pure_sampled_Draws=3,
                limit="three real central Draws, raw original pixels and reused independently verified legacy caches; no rule/RNG or game-wide parity claim")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ["assets", "original", "battle", "out"]:
        p.add_argument("--" + name, type=Path, required=True)
    sub = p.add_subparsers(dest="mode", required=True)
    n = sub.add_parser("normal")
    for name in ["hd", "control", "broken"]:
        n.add_argument("--" + name, type=Path, required=True)
    g = sub.add_parser("gui")
    g.add_argument("--receipt", type=Path, required=True)
    a = p.parse_args()
    assert not a.out.exists()
    bg, caches = references(a)
    result = normal(a, bg, caches) if a.mode == "normal" else gui(a, bg, caches)
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
