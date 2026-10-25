#!/usr/bin/env python3
"""046：核對GRO01正常來源、兩頁及可丟棄戰場原型。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
import platform
import struct
import tarfile
from pathlib import Path

from PIL import Image, __version__ as PILLOW_VERSION

SOURCE_SHA = "4e5c5c6569cc6fc9f1e585b7048c099228f787da041d46ded685e034b7594103"
DECODED_SHA = "79e2c0119edf4ca9f87fb14dbee47de49afca4eee8f8cc2711c4c58c275e7be9"
PIXELS_SHA = "1fe7cd51da104b5274b20fc276956e6f8b66abfb0a8ffde9d40d0f0307acf6fc"
IMAGE_SHA = "521a7a99e37cd437b6cf54835002df42dde1ef29c9bc551af0a1bfaec10230f6"
PROMPT_SHA = "f73b3fa8f3a9349f7e6a3809fc40d15fedea77ed5f5478f8d10978e98e8175f8"
CACHE_SHA = "ee95cca6642a98ed4bdcb14415e19553d6efbb558b4fbf375ca2ba119abd9955"
EGA = [(0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170), (170, 0, 0), (170, 0, 170), (170, 85, 0), (170, 170, 170), (85, 85, 85), (85, 85, 255), (85, 255, 85), (85, 255, 255), (255, 85, 85), (255, 85, 255), (255, 255, 85), (255, 255, 255)]


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text())


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def module(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), Path(__file__).with_name(name + ".py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def inventory(path):
    return {str(p.relative_to(path)): sha(p) for p in path.rglob("*") if p.is_file()}


def build(path, count, project, prototype=False):
    inputs = {}
    differences = []
    for line in (path / "build-inputs.sha256").read_text().splitlines():
        digest, name = line.split("  ", 1)
        assert sha(path / "src" / name) == digest
        inputs[name] = digest
        if name.startswith("internal/eightsword/") and (project / name).exists():
            if sha(project / name) != digest:
                differences.append(Path(name).name)
    assert len(inputs) == count
    assert sorted(differences) == (["battle_actors.go", "battle_transactions.go", "graphics.go"] if prototype else [])
    with tarfile.open(path / "source.tar.gz", "r:gz") as archive:
        members = {m.name.removeprefix("src/"): hashlib.sha256(archive.extractfile(m).read()).hexdigest() for m in archive.getmembers() if m.isfile()}
    assert members == inputs
    digest, name = (path / "build-outputs.sha256").read_text().split()
    assert name == "probe" and sha(path / name) == digest
    version = (path / "build-go-version.txt").read_text().strip()
    assert version == "go version go1.24.13 linux/amd64"
    return dict(inputs=count, probe_sha256=digest, go_version=version, disposable_production_differences=differences)


def isolation(source, control, frames, identical_images):
    finals = [read(root / "final.json") for root in (source, control)]
    for final in finals:
        assert final["normal_input_replay"] and not final["snapshot_loaded"] and not final["guest_injection"]
        assert final["exited"] and final["exit_code"] == 0 and not final["unimplemented"]
        assert final["recorded_frames"] == final["frame_pure_count"] == frames
        assert not any(value for key, value in final.items() if key.endswith("_error"))
    for key in ("steps", "strings", "input_events", "file_ops", "exec_log", "music", "elapsed_ms", "clock_baseline", "rng_seed", "irq1_delivered", "bios_consumed"):
        assert finals[0][key] == finals[1][key], key
    names = ["final.state", "frame-check.state", "audio.pcm", "commands.jsonl", "continued-game.json", "continued-companions.json"]
    if identical_images:
        names.extend(("frames.jsonl", "presentation.frames.gz"))
    equal = {}
    for name in names:
        assert sha(source / name) == sha(control / name), name
        equal[name] = sha(source / name)
    assert inventory(source / "scratch") == inventory(control / "scratch")
    frame_rows = [lines(root / "frames.jsonl") for root in (source, control)]
    assert len(frame_rows[0]) == len(frame_rows[1]) == frames
    for left, right in zip(*frame_rows):
        # Scene and visible text describe the presented frame during a hold.
        assert {k: v for k, v in left.items() if k not in ("scene", "visible_sources")} == {k: v for k, v in right.items() if k not in ("scene", "visible_sources")}
    checkpoints = sorted(source.glob("*-native.png"))
    for path in checkpoints:
        assert sha(path) == sha(control / path.name)
        if identical_images:
            name = path.name.replace("-native.png", "-hd.png")
            assert sha(source / name) == sha(control / name)
    return dict(frames_each=frames, equal=equal, scratch_files=len(inventory(source / "scratch")), checkpoints=len(checkpoints))


def blend(target, at, cache, src):
    alpha = cache[src + 3]
    for c in range(3):
        target[at + c] = min(255, cache[src + c] + (target[at + c] * (255 - alpha) + 127) // 255)


def prototype_frames(battle, prototype, bg, native_bg, original, assets):
    caches = {87 + group * 4 + i: (battle / (name + "-art-r1") / f"cache-frame-{i}.rgba").read_bytes()
              for group, name in enumerate(("man16", "man06", "man11", "man21")) for i in range(4)}
    caches[107] = module("audit-encounter-gui").sample(assets / "militia-painted-r1.png", 264, 300, actor=True)
    assert hashlib.sha256(caches[107]).hexdigest() == "1c795ec9e8d67feca9a014d3b3511bc9ed9d9d115102e8042e4a16b3b4982fe5"
    registration = read(battle / "ally21-mirror-prototype-r1/registration.json")["entries"]
    for entry in registration:
        data = (battle / "ally21-mirror-prototype-r1" / entry["cache_file"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry["cache_sha256"]
        caches[152 + entry["record"]] = data
    catalog = {}
    reverse = bytes(int(f"{v:08b}"[::-1], 2) for v in range(256))
    for path in original.glob("MAN*.EGG"):
        raw = path.read_bytes()
        for i in range(4):
            record = raw[i * 3304:(i + 1) * 3304]
            mirrored = record[:4] + b"".join(record[k:k + 11][::-1].translate(reverse) for k in range(4, 3304, 11))
            for data in (record, mirrored):
                catalog[hashlib.sha256(data).hexdigest()] = data
    calls = [c for c in lines(prototype / "battle-source-calls.jsonl") if "serial" in c]
    results = []
    for record in range(4):
        stem = prototype / "palace-frames" / f"record-{record}-first-frame"
        path = lambda suffix: Path(str(stem) + suffix)
        meta = read(path(".json"))
        assert meta["record"] == record and meta["actual_draw"] == 0 and not meta["pending"]
        assert sha(path("-before.state")) == sha(path("-after.state"))
        assert any(c.get("target_record") == record and c["return_step"] == meta["source_return_step"] <= meta["step"] for c in calls)
        assert [tuple(c) for c in meta["display"]["Palette"]] == EGA and meta["display"]["Start"] == 0
        assert not any(path("-text.bin").read_bytes()), "這份原型核對限於沒有文字的完整戰場幀"
        native = bytearray(path("-native.idx").read_bytes())
        owners = list(struct.iter_unpack("<HI", path("-background.bin").read_bytes()))
        actors = list(struct.iter_unpack("<HI", path("-actors.bin").read_bytes()))
        effects = list(struct.iter_unpack("<HI", path("-effects.bin").read_bytes()))
        assert len(native) == len(owners) == len(actors) == len(effects) == 128000
        assert sum(ident == 152 + record for ident, local in actors) == 4400
        fx_info = read(path("-layers.json"))["effects"]
        fx_cache = {}
        base = path("-effect-base.idx").read_bytes()
        for key, source in fx_info.items():
            assert 108 <= source <= 111, "其他效果累積需獨立驗證，不能沿用單層陰陽快取"
            key = int(key)
            data = (battle / "choi-art-r1" / f"cache-frame-{source - 108}.rgba").read_bytes()
            assert path(f"-effect-cache-{key}.rgba").read_bytes() == data
            fx_cache[key] = data
            cells = [(i, local) for i, (ident, local) in enumerate(effects) if ident == key]
            assert len(cells) == 4400
            first = next(i for i, local in cells if local == 0)
            x0, y0 = first % 640, first // 640
            reset = max((c for c in calls if c["x_byte"] * 8 == x0 and c["y"] == y0 and c["return_step"] <= meta["step"]), key=lambda c: c["return_step"])
            raw = catalog[reset["source_sha256"]]
            for i, local in cells:
                assert i == (y0 + local // 88) * 640 + x0 + local % 88
                offset, bit = local // 8, 7 - local % 8
                expected = sum(((raw[4 + plane * 550 + offset] >> bit) & 1) << plane for plane in range(4)) if raw[2754 + offset] >> bit & 1 else native_bg[i]
                assert base[i] == expected, (record, "effect native base", i)
        for i, (ident, local) in enumerate(effects):
            if ident:
                assert ident in fx_cache
                native[i] = base[i]
        im = Image.frombytes("P", (640, 200), bytes(native))
        im.putpalette([v for rgb in EGA for v in rgb] + [0] * (768 - 48))
        expected = bytearray(im.convert("RGBA").resize((1920, 1200), Image.Resampling.NEAREST).tobytes())
        for i, (ident, local) in enumerate(owners):
            if not ident:
                continue
            assert ident == 151 and local < 128000
            for dy in range(6):
                at = ((i // 640 * 6 + dy) * 1920 + i % 640 * 3) * 4
                src = ((local // 640 * 6 + dy) * 1920 + local % 640 * 3) * 4
                expected[at:at + 12] = bg[src:src + 12]
        for cells, cache_map in ((actors, caches), (effects, fx_cache)):
            for i, (ident, local) in enumerate(cells):
                if not ident:
                    continue
                assert ident in cache_map and local < 4400
                cache = cache_map[ident]
                for dy in range(6):
                    for dx in range(3):
                        at = ((i // 640 * 6 + dy) * 1920 + i % 640 * 3 + dx) * 4
                        src = ((local // 88 * 6 + dy) * 264 + local % 88 * 3 + dx) * 4
                        blend(expected, at, cache, src)
        actual = Image.open(path(".png")).convert("RGBA").tobytes()
        assert actual == expected, (record, "complete prototype frame")
        results.append(dict(record=record, step=meta["step"], frame_ordinal=meta["frame_ordinal"], source_return_step=meta["source_return_step"], full_pixels=2304000, rgba_sha256=hashlib.sha256(actual).hexdigest(), actor_ids=sorted({i for i, local in actors if i}), effect_sources=list(fx_info.values())))
    wanted = {row["frame_ordinal"]: row for row in results}
    for ordinal, step, frame in module("audit-army-dismiss").stream(prototype):
        if ordinal in wanted:
            row = wanted.pop(ordinal)
            assert frame.size == (1920, 1200) and step == row["step"]
            assert hashlib.sha256(frame.tobytes()).hexdigest() == row["rgba_sha256"]
    assert not wanted
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("original", "assets", "battle", "art", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--prototype", type=Path)
    a = parser.parse_args()
    assert not a.out.exists()
    project = Path(__file__).resolve().parent.parent
    raw = (a.original / "GRO01.EG").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA
    pam_sha = sha(a.original / "PAM.AY")
    assert pam_sha == "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"
    decoded = module("prepare-hd-intro").decode(raw)
    assert len(decoded) == 64004 and hashlib.sha256(decoded).hexdigest() == DECODED_SHA
    assert struct.unpack_from("<HH", decoded) == (80, 200)
    pixels = bytes(sum(((decoded[4 + plane * 16000 + i // 8] >> (7 - i % 8)) & 1) << plane for plane in range(4)) for i in range(128000))
    assert hashlib.sha256(pixels).hexdigest() == PIXELS_SHA
    builds = {name: build(a.battle / name, 52, project) for name in ("gro01-source-build-r1", "gro01-source-build-r2", "ally21-castle-build-r2")}
    full = a.battle / "gro01-source-r1"
    pages = a.battle / "gro01-source-r2"
    runs = dict(full=isolation(full, a.battle / "ally21-castle-control-r3", 1324, True), pages=isolation(pages, a.battle / "gro01-control-r2", 580, True))
    first_calls = []
    for root in (full, pages):
        call = read(root / "gro01-first-a000-call.json")
        assert call["segment"] == 0x14d2 and call["entry"] == 0x99c and call["return"] == 0xa6f and call["abi_bytes_matched"] == 212
        assert call["source"] == {"Seg": 0x5000, "Off": 0} and call["destination_segment"] == 0xa000 and call["mode"] == 1
        assert call["entry_step"] == 46534411 and call["return_step"] == 46541061
        assert (root / "gro01-first-a000-source.bin").read_bytes() == decoded
        assert (root / "gro01-first-a000-after.idx").read_bytes() == pixels
        first_calls.append(call)
    for suffix in ("a000", "a400"):
        assert (pages / f"gro01-before-first-actor-{suffix}.idx").read_bytes() == pixels
    pair = read(pages / "gro01-pages-before-first-actor.json")
    assert pair["step"] == 49839860 and pair["background_segment"] == 0xa400 and pair["destination_segment"] == 0xa000
    assert sha(a.art / "gro01-painted-r1.png") == IMAGE_SHA and sha(a.art / "gro01-painted-r1.prompt.txt") == PROMPT_SHA
    image = Image.open(a.art / "gro01-painted-r1.png")
    assert image.size == (1586, 992) and image.mode == "RGB"
    cache = module("audit-encounter-gui").sample(a.art / "gro01-painted-r1.png", 1920, 1200)
    assert hashlib.sha256(cache).hexdigest() == CACHE_SHA
    assert cache == (a.art / "gro01-cache-r1.rgba").read_bytes()
    packets = []
    if a.prototype:
        builds["prototype"] = build(a.battle / "gro01-prototype-build-r1", 54, project, True)
        runs["prototype"] = isolation(a.prototype, a.battle / "ally21-castle-control-r3", 1324, False)
        assert (a.prototype / "prototype-background-cache.rgba").read_bytes() == cache
        packets = prototype_frames(a.battle, a.prototype, cache, pixels, a.original, a.assets)
    result = dict(status="normal-GRO01-source-pages-and-art-verified", source_sha256=SOURCE_SHA, decoded_sha256=DECODED_SHA, native_pixels_each=128000, complete_page_samples=4, image_sha256=IMAGE_SHA, cache_sha256=CACHE_SHA, builds=builds, runs=runs, first_calls=first_calls, first_actor=pair, prototype_frames=packets, prototype_full_pixels=sum(p["full_pixels"] for p in packets), production_ready=False, scope="正常背景與可丟棄原型；不證明正式載入、實際GUI Draw或新存檔冷讀", verifier_sha256=sha(Path(__file__)))
    result.update(pam_sha256=pam_sha, tools=dict(python=platform.python_version(), pillow=PILLOW_VERSION, decoder_sha256=sha(Path(__file__).with_name("prepare-hd-intro.py"))))
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("status", "native_pixels_each", "prototype_full_pixels", "production_ready")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
