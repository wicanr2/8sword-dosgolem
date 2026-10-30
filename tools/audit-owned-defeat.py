#!/usr/bin/env python3
"""030 DRAFT: Go defeat controls, independent evidence and permanent archive.

Run only in the pinned Pillow 11.3.0 Docker image, UID 1000.
prepare --project /project; audit --project /project --out NEW.json;
archive --project /project --archive /preserved --out NEW.json;
verify --archive /preserved --out NEW.json needs no workplace mount.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct

REL = "workplace/probe-20261023/graphics-first/battle-r1/owned-defeat-r1"
TOOLS = ["export-owned-defeat-ida.py", "probe-owned-defeat.go",
         "research-owned-defeat.go", "research-owned-defeat_test.go",
         "owned-defeat-check.go", "inspect-owned-defeat-states.go", "audit-owned-defeat.py"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    with path.open("x") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write("\n")


def unchanged(root):
    base = read(root / "preserved/owned-combat-audit-r1.json")
    folders = {"source_inputs": root, "programs": root / "workplace/player",
               "core_files": root / "workplace/player/runtime-render-r1/src",
               "asset_hashes": root / "workplace/player/assets-painted-r69"}
    for key, folder in folders.items():
        for name, digest in base[key].items():
            assert sha(folder / name) == digest, (key, name)
    return {key: base[key] for key in folders}


def verify(archive, out):
    index = archive / "owned-defeat-r1.json"
    manifest = read(index)
    checked = set()
    for f in manifest["files"]:
        path = Path(f["path"])
        assert not path.is_absolute() and ".." not in path.parts
        obj = manifest["objects"][f["sha256"]]
        blob = archive / "owned-defeat-r1" / obj["file"]
        assert sha(blob) == obj["stored_sha256"]
        raw = gzip.decompress(blob.read_bytes())
        assert len(raw) == f["bytes"] and hashlib.sha256(raw).hexdigest() == f["sha256"]
        checked.add(f["sha256"])
    write(out, dict(status="passed-detached-owned-defeat", files=len(manifest["files"]),
                    objects=len(checked), index_sha256=sha(index), workplace_required=False))


def audit(root, q):
    dependencies = unchanged(root)
    ida = read(q / "ida/ida-defeat-r2.json")
    pam = root / "workplace/intake-20261023/sources/game/8sword/PAM.AY"
    raw = pam.read_bytes()
    assert sha(pam) == ida["input_sha256"] == "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"
    assert sha(root / "workplace/probe-20261023/text-first/PAM.i64") == ida["database_sha256"]
    assert sha(root / "tools/export-owned-defeat-ida.py") == ida["exporter_sha256"]
    word = lambda at: struct.unpack_from("<H", raw, at)[0]
    header = word(8) * 16
    relocated = bytearray(raw[header:])
    for i in range(word(6)):
        at = word(24) + i * 4
        off = word(at + 2) * 16 + word(at)
        struct.pack_into("<H", relocated, off, (struct.unpack_from("<H", relocated, off)[0] + 0x1000) & 65535)
    lines = 0
    for f in ida["functions"]:
        for line in f["lines"]:
            off = line["ida_linear"] - 0x10000
            data = bytes.fromhex(line["bytes"])
            assert line["file_offset"] == header + off
            assert relocated[off:off + len(data)] == data
            lines += 1
    assert len(ida["functions"]) == 8
    rand = next(f for f in ida["functions"] if f["name"] == "_rand")
    assert any(bytes.fromhex(v["bytes"]) == bytes.fromhex("80e47f") for v in rand["lines"])
    # Text and numeric rules are read directly from the fixed original image.
    string_at = lambda off: raw[header + 0x2d780 - 0x10000 + off:].split(b"\0", 1)[0].decode("big5")
    choices = [string_at(off) for off in (0x47e6, 0x480e, 0x4836)]
    assert "殲" in choices[0] and "起" in choices[1] and "江" in choices[2]
    thresholds = list(struct.unpack_from("<6H", raw, header + 0x2d780 - 0x10000 + 0x5b2))
    assert thresholds == [0, 2000, 5000, 8000, 12000, 30000]
    native = read(q / "original-r2/receipt.json")
    decoded = read(q / "decoded-r1.json")
    assert len(native["rows"]) == 12 and len(decoded) == 24 and native["player_path"] is False
    assert native["state_sha256"] == sha(q / "inputs/oracle-state.state")
    for v in native["rows"]:
        case = v["case"]
        assert v == read(q / "original-r2" / case["Name"] / "receipt.json")
        # sub_11796 does not define a uniform AX status: promotion's display
        # helper leaves AX=7181 here. Use saved strategic state, not that value.
        assert v["error"] == "<nil>"
        for phase in ("before", "after"):
            key = case["Name"] + "/" + phase + ".state"
            d = decoded[key]
            assert d["state_sha256"] == sha(q / "original-r2" / key)
            for field in ("progress", "army", "origin", "position_x", "position_y", "travel_56c4"):
                assert d[field] == v[phase][field], (key, field)
        expected = list(v["before"]["progress"])
        if case["Count"]:
            assert v["random_calls"] == 1 and v["raw_random"] == 13654
            random = v["effective_random"]
            assert random == (13654 if case["Random"] < 0 else case["Random"])
            expected[3] -= expected[3] // (random // 2730 + 3)
            if expected[0] < 5 and expected[1] > thresholds[expected[0]]:
                expected[0] += 1
                expected[2] = min(30000, expected[2] + 100)
                expected[4] = min(30000, expected[4] + 100)
                expected[5] = min(30000, expected[5] + expected[0] * 3)
        else:
            assert v["random_calls"] == 0 and v["choice_confirm_sent"]
            assert v["choice_down_sent"] == (case["Choice"] == 2)
            if case["Choice"] == 1:
                assert [v["after"]["position_x"], v["after"]["position_y"]] == v["before"]["origin"]
                assert v["after"]["travel_56c4"][0] == 3
            else:
                assert v["after"]["position_x"] == v["before"]["position_x"]
                assert v["after"]["position_y"] == v["before"]["position_y"]
        assert v["after"]["progress"] == expected
    flow = read(q / "flow-r1/receipt.json")
    assert flow["guest_instructions"] == 0 and flow["player_path"] is False
    for v in flow["rows"]:
        s = v["session"]
        before, after, result = s["before"], s["after"], s["resolution"]
        assert after["revision"] == before["revision"] + 1 and after["battle"] is None
        assert not after["encounters"]["enemy"]["cleared"]
        assert result["world_handoff"] == "pending" and v["engine_guard"]
        assert after["army"]["offers"] == before["army"]["offers"]
        assert after["progress"] == before["progress"]
        assert before["battle"]["state"]["rows"][0][0]["count"] == after["army"]["slots"][0]["count"]
        hit = v["hit"]
        assert hit["action"]["side"] == 1 and hit["action"]["source"] == 0 and hit["action"]["target"] == 0
        assert hit["before"] == before["battle"]["state"]["initial"][0][0]["count"]
        assert hit["after"] == after["army"]["slots"][0]["count"] and hit["before"] - hit["after"] == hit["loss"]
        if v["name"] == "retreat":
            assert before["army"]["gold"] == 3800 and after["army"]["gold"] == 2850
            assert result["gold_lost"] == 950 and after["army"]["slots"][0]["count"] == 29
        else:
            assert after["army"]["gold"] == 4920 and result["gold_lost"] == 0
            assert all(v["count"] == 0 for v in after["army"]["slots"])
        for side in range(2):
            compact = [v for v in before["battle"]["state"]["rows"][side] if v["count"] > 0]
            actual = after["army"]["slots"] if side == 0 else result["enemy_survivors"]
            assert [{"unit":v["unit"],"count":v["count"]} for v in compact] == [v for v in actual if v["count"] > 0]
        save_dir = q / "flow-r1" / v["name"]
        assert sha(save_dir / "gamedata.ay") == v["original_sha256"] == sha(q / "inputs/original-save.ay")
        saved = read(save_dir / "gamedata.ay.army.json")
        assert saved["session"] == s and saved["original_sha256"] == v["original_sha256"]
        cold = read(q / ("cold-" + v["name"] + "-r1") / "receipt.json")
        assert cold["status"] == "passed-defeat-cold-load" and cold["session"] == s
    test = (q / "go-test-r1.log").read_text()
    assert "FAIL" not in test and "SKIP" not in test and "PASS" in test
    assert "TestDefeatOriginalResourceControls" in test and "TestDefeatSaveAtomicBindings" in test
    return dict(status="passed-draft-owned-defeat", original_controls=12, independently_decoded_states=24,
                ida_functions=8, ida_lines=lines, original_choices=choices, go_branches=3,
                cold_processes=3, guest_instructions=0, player_path=False,
                test_log_sha256=sha(q / "go-test-r1.log"), dependencies=dependencies,
                checker_sha256=sha(q / "defeat-check"), reader_sha256=sha(q / "state-reader"),
                source_tools={name:sha(root / "tools" / name) for name in TOOLS},
                limits=["DRAFT standalone transitions; formal UI and map handoff pending.",
                        "Native controls use fixed snapshot and explicit returned random inputs; not natural annihilation.",
                        "World counter and enemy persistence are not inferred."])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["prepare", "audit", "archive", "verify", "integrity"])
    p.add_argument("--project", type=Path)
    p.add_argument("--archive", type=Path)
    p.add_argument("--out", type=Path)
    a = p.parse_args()
    assert Path("/.dockerenv").exists() and os.getuid() == 1000
    if a.action == "verify":
        verify(a.archive, a.out)
        return
    root = a.project
    q = root / REL
    dependencies = unchanged(root)
    if a.action == "prepare":
        source = q / "go-src"
        assert not source.exists() and q.stat().st_uid == 1000
        for name in dependencies["source_inputs"]:
            dest = source / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / name, dest)
        (source / "tools").mkdir(exist_ok=True)
        for name in ["research-owned-world.go", "research-owned-world_test.go"] + TOOLS:
            shutil.copyfile(root / "tools" / name, source / "tools" / name)
        common = (root / "tools/research-owned-army.go").read_text().removeprefix("//go:build ignore\n")
        common = common[:common.index("func main()")].replace('\n\t"flag"\n', '\n')
        (source / "tools/owned-army-model.go").write_text(common)
        shutil.copyfile(source / "go.mod", q / "probe.mod")
        shutil.copyfile(source / "go.sum", q / "probe.sum")
        write(q / "baseline-r1.json", dependencies)
        print("Prepared isolated defeat prototype; production unchanged")
    elif a.action == "audit":
        write(a.out, audit(root,q))
    elif a.action == "archive":
        verified = read(q / "audit-r1.json")
        assert verified["status"] == "passed-draft-owned-defeat"
        assert verified["source_tools"] == {n:sha(root / "tools" / n) for n in TOOLS}
        directory = a.archive / "owned-defeat-r1"
        directory.mkdir()
        selected = {f for f in q.rglob("*") if f.is_file()}
        selected.update(root / "tools" / n for n in TOOLS + ["research-owned-army.go", "research-owned-world.go"])
        selected.add(root / "docs/spec/030-battle-expansion-proposal.md")
        files, objects = [], {}
        for f in sorted(selected):
            assert not f.is_symlink() and f.stat().st_uid == 1000
            raw = f.read_bytes(); digest = hashlib.sha256(raw).hexdigest()
            if digest not in objects:
                blob = gzip.compress(raw,compresslevel=6,mtime=0)
                name = digest + ".gzip"; (directory / name).write_bytes(blob)
                objects[digest] = dict(file=name,stored_sha256=hashlib.sha256(blob).hexdigest(),stored_bytes=len(blob))
            files.append(dict(path=str(f.relative_to(root)),sha256=digest,bytes=len(raw),mode=f.stat().st_mode & 0o777))
        write(a.archive / "owned-defeat-r1.json", dict(schema=1,files=files,objects=objects,
              audit_sha256=sha(q / "audit-r1.json"),dependencies=dependencies))
        write(a.out,dict(status="preserved-draft-owned-defeat",files=len(files),objects=len(objects),
                         stored_bytes=sum(v["stored_bytes"] for v in objects.values())))
    else:
        assert read(a.archive / "owned-defeat-verification-r1.json")["workplace_required"] is False
        art = read(root / "artwork/manifest.json")
        assert len(art["files"]) == 1040
        for f in art["files"]:
            assert sha(root / "artwork" / f["path"]) == f["sha256"]
        for folder in (q,a.archive / "owned-defeat-r1"):
            assert all(f.stat().st_uid == 1000 for f in folder.rglob("*"))
            assert not any(f.is_dir() and f.name.endswith(".md") for f in folder.rglob("*"))
        write(a.out,dict(status="passed-owned-defeat-integrity",production_changed=False,source_inputs=197,
                         programs=7,core=923,assets=535,artwork=1040,root_owned_outputs=0,player_handoff="pending"))


if __name__ == "__main__":
    main()
