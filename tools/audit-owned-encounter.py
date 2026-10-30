#!/usr/bin/env python3
"""030 DRAFT: verify source-specific encounter ownership in bounded Docker.

prepare|audit --project PROJECT; archive --project PROJECT --archive PRESERVED;
verify --archive PRESERVED --out NEW.json runs without workplace.
All writes require UID1000, fixed toolchain and explicit writable mounts.
"""
import argparse
import ast
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct

REL = "workplace/probe-20261023/graphics-first/battle-r1/owned-encounter-r1"
TOOLS = ["export-owned-encounter-ida.py", "probe-owned-encounter.go", "research-owned-encounter.go",
         "research-owned-encounter_test.go", "owned-encounter-check.go",
         "inspect-owned-encounter-states.go", "audit-owned-encounter.py"]
COMMON = ["research-owned-army.go", "research-owned-world.go", "research-owned-world_test.go",
          "research-owned-defeat.go", "research-owned-defeat_test.go"]
BASES = [0x365e, 0x3706, 0x3766, 0x37c6, 0x3826, 0x3886, 0x38e6, 0x3946]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    return json.loads(p.read_text())


def write(p, value):
    with p.open("x") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write("\n")


def dependencies(root):
    baseline = read(root / "preserved/owned-combat-audit-r1.json")
    folders = {"source_inputs": root, "programs": root / "workplace/player",
               "core_files": root / "workplace/player/runtime-render-r1/src",
               "asset_hashes": root / "workplace/player/assets-painted-r69"}
    for key, folder in folders.items():
        for name, digest in baseline[key].items():
            assert sha(folder / name) == digest, (key, name)
    return {k: baseline[k] for k in folders}


def archived_file(root, batch, suffix):
    index = read(root / "preserved" / (batch + ".json"))
    f = next(f for f in index["files"] if f["path"].endswith(suffix))
    obj = index["objects"][f["sha256"]]
    blob = (root / "preserved" / batch / obj["file"]).read_bytes()
    assert hashlib.sha256(blob).hexdigest() == obj["stored_sha256"]
    raw = gzip.decompress(blob)
    assert len(raw) == f["bytes"] and hashlib.sha256(raw).hexdigest() == f["sha256"]
    return raw


def prepare(root, q, deps):
    assert not q.exists() and q.parent.stat().st_uid == 1000
    q.mkdir(); (q / "ida").mkdir(); (q / "inputs").mkdir()
    for name in ["oracle-state.state", "world-controls.json", "army-catalog.json", "combat-catalog.json", "original-save.ay"]:
        (q / "inputs" / name).write_bytes(archived_file(root, "owned-defeat-r1", "/inputs/" + name))
    (q / "inputs/defeat-controls.json").write_bytes(archived_file(root, "owned-defeat-r1", "/original-r2/receipt.json"))
    (q / "ida/ida-world-r3.json").write_bytes(archived_file(root, "owned-world-r1", "/ida-world-r3.json"))
    source = q / "go-src"
    for name in deps["source_inputs"]:
        target = source / name; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / name, target)
    (source / "tools").mkdir(exist_ok=True)
    for name in COMMON + TOOLS:
        shutil.copyfile(root / "tools" / name, source / "tools" / name)
    common = (root / "tools/research-owned-army.go").read_text().removeprefix("//go:build ignore\n")
    common = common[:common.index("func main()")].replace('\n\t"flag"\n', '\n')
    (source / "tools/owned-army-model.go").write_text(common)
    for suffix in ["mod", "sum"]:
        shutil.copyfile(source / ("go." + suffix), q / ("probe." + suffix))
    native = q / "native-src-r2"; native.mkdir()
    shutil.copyfile(root / "tools/probe-owned-encounter.go", native / "main.go")
    (native / "go.mod").write_text("module guard-control\n\ngo 1.24.13\n\nrequire github.com/wicanr2/dosgolem v0.0.0\nreplace github.com/wicanr2/dosgolem => /core\n")


def audit(root, q, deps):
    pam = root / "workplace/intake-20261023/sources/game/8sword/PAM.AY"
    raw = pam.read_bytes()
    assert sha(pam) == "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"
    word = lambda off: struct.unpack_from("<H", raw, off)[0]
    header = word(8) * 16
    relocated = bytearray(raw[header:])
    for i in range(word(6)):
        at = word(24) + i * 4; off = word(at + 2) * 16 + word(at)
        struct.pack_into("<H", relocated, off, (struct.unpack_from("<H", relocated, off)[0] + 0x1000) & 65535)
    line_counts = []
    for name in ["ida-world-r3.json", "ida-encounter-r1.json"]:
        d = read(q / "ida" / name)
        assert d["input_sha256"] == sha(pam)
        assert d["database_sha256"] == sha(root / "workplace/probe-20261023/text-first/PAM.i64")
        n = 0
        for f in d["functions"]:
            for line in f["lines"]:
                at = line["ida_linear"] - 0x10000; data = bytes.fromhex(line["bytes"])
                assert line["file_offset"] == at + header and relocated[at:at + len(data)] == data
                n += 1
        line_counts.append(n)
    assert read(q / "ida/ida-encounter-r1.json")["exporter_sha256"] == sha(root / "tools/export-owned-encounter-ida.py")
    text = lambda off: raw[header + 0x1d780 + off:].split(b"\0",1)[0].decode("big5").replace(" ", "")
    assert text(0x4746) == "提高月薪:" and text(0x476e) == "法術能力增加:"
    assert text(0x4796) == "找到:" and text(0x26ea) == "掩日劍" and text(0x26f8) == "斷水劍"
    native = read(q / "original-r2/receipt.json")
    assert native["status"] == "passed-original-guard-caller-controls" and native["player_path"] is False
    assert native["source_state_sha256"] == sha(q / "inputs/oracle-state.state")
    assert sha(q / "native-src-r2/main.go") == sha(root / "tools/probe-owned-encounter.go")
    index = read(q / "decoded-r1/index.json")
    assert len(index) == 20 and len(native["rows"]) == 10
    repeated = 0
    for v in native["rows"]:
        case = v["case"]; area = case["Region"]
        assert v["error"] == "<nil>" and v["battle_calls"] == 1
        assert read(q / "original-r2" / case["Name"] / "receipt.json") == v
        for phase in ["before", "after"]:
            name = case["Name"] + "/" + phase + ".state"; info = index[name]
            assert info["state_sha256"] == sha(q / "original-r2" / name)
            mem = gzip.decompress((q / "decoded-r1" / (info["memory_sha256"] + ".ram.gz")).read_bytes())
            assert len(mem) == info["memory_bytes"] and hashlib.sha256(mem).hexdigest() == info["memory_sha256"]
            words = lambda at, n: list(struct.unpack_from("<" + "H" * n, mem, 0x1e880 + at))
            fields = dict(progress=words(0x4f2, 6), army=words(0x54a, 12), battle=words(0x56e8, 24),
                          pool=words(0x365e, 516), coordinates=words(0x8c30, 24), position=[words(0x8e12, 1)[0], words(0x8e44, 1)[0]],
                          region=words(0x56d6, 1)[0], pieces=words(0x275a, 8), legacy_26aa=words(0x26aa, 1)[0])
            for key, value in fields.items():
                assert v[phase][key] == value, (case["Name"], phase, key)
            battle_bytes = mem[0xf678:0xf67c]
            assert battle_bytes == base64.b64decode(v["stub_bytes"] if phase == "before" else v["original_battle_bytes"])
            if (q / "original-r1" / name).exists():
                assert sha(q / "original-r1" / name) == info["state_sha256"]
                repeated += 1
        before, after = v["before"], v["after"]
        expected = list(before["pool"])
        at = (BASES[area] - BASES[0]) // 2
        expected[at:at + 12] = [0] * 12 if case["Result"] == 0 else [1, 8, 5, 2] + [0] * 8
        assert after["pool"] == expected  # entire bank neighborhood, not only the selected six cells
        actual = list(before["progress"])
        pieces = list(before["pieces"])
        if case["Result"] == 0:
            actual[2] = min(30000, actual[2] + (area + 1) * 20)
            if case["Legacy26AA"] == 1:
                actual[5] = min(30000, actual[5] + area + 1)
            if case["Boss"]:
                pieces[area] = 1
        elif case["Result"] == 1:
            assert v["random_input"] == 25927
            actual[3] -= actual[3] // (v["random_input"] // 2730 + 3)
        assert after["progress"] == actual and after["pieces"] == pieces
        assert after["army"] == ([0] * 12 if case["Result"] == 2 else [1, 11] + [0] * 10)
        assert v["roam_fixture_calls"] == (1 if case["Result"] == 2 else 0)
        events = {e["ip"]: e for e in v["events"]}
        assert events[0x3733]["battle"][12:] == before["pool"][at:at + 12]
        assert events[0x3745]["battle"][12:] == expected[at:at + 12]
    flow = read(q / "flow-r2/receipt.json")
    assert flow["guest_instructions"] == 0 and flow["player_path"] is False and len(flow["rows"]) == 6
    assert sha(root / "tools/owned-encounter-check.go") == sha(q / "go-src/tools/owned-encounter-check.go")
    first_flow = {v["name"]:v["session"] for v in read(q / "flow-r1/receipt.json")["rows"]} if (q / "flow-r1/receipt.json").exists() else {}
    profiles = {v["id"]: v for v in read(q / "inputs/army-catalog.json")["profiles"]}
    actions = 0
    for v in flow["rows"]:
        s = v["session"]; before, after, ctx, res = s["before"], s["after"], s["context"], s["result"]
        if first_flow:
            assert s == first_flow[v["name"]]  # r2 only corrects field-name evidence in the receipt's limits
        id = before["battle"]["encounter"]; state = before["battle"]["state"]
        guarded = ctx["kind"] == "guarded"; win = state["result"] == "win"
        assert after["revision"] == before["revision"] + 1 and after["battle"] is None
        assert res["persistent"] == guarded and res["world_handoff"] == "pending"
        assert after["encounters"]["guarded:07:03"] == before["encounters"]["guarded:07:03"]
        assert after["army"]["offers"] == before["army"]["offers"] and v["engine_guard"]
        expected_progress = dict(before["progress"])
        gold = before["army"]["gold"]
        if win:
            if guarded:
                expected_progress["legacy_04f6"] += 20 * (ctx["region"] + 1)
                if ctx["legacy_26aa"] == 1:
                    expected_progress["legacy_04fc"] += ctx["region"] + 1
            else:
                gold += sum(v["count"] * profiles[v["unit"]]["gold"] for v in state["initial"][1] if v["count"])
                expected_progress["merit"] += sum(v["count"] * profiles[v["unit"]]["command"] for v in state["initial"][1] if v["count"]) // 2
        elif s["input"]["reason"] == "retreat":
            gold -= gold // (s["input"]["random"] // 2730 + 3)
        if not guarded and expected_progress["rank"] < 5 and expected_progress["merit"] > expected_progress["thresholds"][expected_progress["rank"]]:
            expected_progress["rank"] += 1; expected_progress["legacy_04f6"] += 100; expected_progress["legacy_04fc"] += expected_progress["rank"] * 3
        assert after["army"]["gold"] == gold and after["progress"] == expected_progress
        assert after["army"]["recruit_rank"] == expected_progress["rank"]
        assert after["army"]["leadership"] == before["army"]["leadership"] + (100 if expected_progress["rank"] > before["progress"]["rank"] else 0)
        assert (id in after["encounters"]) == guarded
        if guarded:
            assert after["encounters"][id]["cleared"] == win and res["cleared"] == win
            if not win:
                assert after["encounters"][id]["enemy"] == res["enemy_rows"]
        for side in range(2):
            compact = [{"unit":v["unit"], "count":v["count"]} for v in state["rows"][side] if v["count"]]
            actual = after["army"]["slots"] if side == 0 else res["enemy_rows"]
            assert [v for v in actual if v["count"]] == compact
        expected_pieces = list(ctx["pieces"])
        if guarded and win and ctx["boss"]:
            expected_pieces[ctx["region"]] = True
        assert res["pieces"] == expected_pieces
        cold = read(q / ("cold-" + v["name"] + "-r2") / "receipt.json")
        assert cold["session"] == s and cold["status"] == "passed-encounter-cold-load"
        directory = q / "flow-r2" / v["name"]
        assert sha(directory / "gamedata.ay") == v["original_sha256"] == sha(q / "inputs/original-save.ay")
        assert read(directory / "gamedata.ay.army.json")["session"] == s
        actions += len(v["events"])
    log = (q / "go-test-r3.log").read_text()
    assert "PASS" in log and "FAIL" not in log and "SKIP" not in log
    return dict(status="passed-draft-owned-encounter", native_controls=10, decoded_states=20,
                observed_state_equal_to_first_run=repeated, ida_line_counts=line_counts, go_chains=6,
                go_actions=actions, cold_processes=6, guest_instructions=0, player_path=False,
                dependencies=deps, checker_sha256=sha(q / "encounter-check-r2"), reader_sha256=sha(q / "state-reader"),
                test_sha256=sha(q / "go-test-r3.log"), source_tools={n:sha(root / "tools" / n) for n in TOOLS},
                resolved_fields={"DS:04F6h":"月薪","DS:04FCh":"法術能力","DS:275Ah + 2*region":"八劍取得旗標"},
                limits=["Native battle entry and outcome are explicit stubs; caller control only.",
                        "Global ending gate, normal UI and original map handoff remain unconnected.",
                        "No expanded IDs or Go battle counts are written to native tables."])


def verify(archive, out):
    index = archive / "owned-encounter-r1.json"; manifest = read(index); checked = set()
    for f in manifest["files"]:
        path = Path(f["path"]); assert not path.is_absolute() and ".." not in path.parts
        obj = manifest["objects"][f["sha256"]]; blob = archive / "owned-encounter-r1" / obj["file"]
        assert sha(blob) == obj["stored_sha256"]
        raw = gzip.decompress(blob.read_bytes())
        assert len(raw) == f["bytes"] and hashlib.sha256(raw).hexdigest() == f["sha256"]
        checked.add(f["sha256"])
    write(out, dict(status="passed-detached-owned-encounter",files=len(manifest["files"]),objects=len(checked),
                    index_sha256=sha(index),workplace_required=False))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=["prepare","audit","archive","verify","integrity"])
    p.add_argument("--project",type=Path);p.add_argument("--archive",type=Path);p.add_argument("--out",type=Path)
    p.add_argument("--audit",type=Path)
    a=p.parse_args();assert Path("/.dockerenv").exists() and os.getuid()==1000
    if a.action=="verify":verify(a.archive,a.out);return
    root=a.project;q=root/REL;deps=dependencies(root)
    if a.action=="prepare":prepare(root,q,deps);return
    if a.action=="audit":write(a.out,audit(root,q,deps));return
    if a.action=="archive":
        receipt=a.audit or q/"audit-final.json"
        verified=read(receipt);assert verified["status"]=="passed-draft-owned-encounter"
        assert verified["source_tools"]=={n:sha(root/"tools"/n) for n in TOOLS}
        directory=a.archive/"owned-encounter-r1";directory.mkdir()
        selected={f for f in q.rglob("*") if f.is_file()};selected.update(root/"tools"/n for n in TOOLS+COMMON);selected.add(root/"docs/spec/030-battle-expansion-proposal.md")
        selected.update(root/name for name in ["docs/spec/ai-resolution-backlinks-r1.json","tools/check-ai-resolution-backlinks.py","RESEARCH-LOG.md"])
        files,objects=[],{}
        for f in sorted(selected):
            assert not f.is_symlink() and f.stat().st_uid==1000
            raw=f.read_bytes();h=hashlib.sha256(raw).hexdigest()
            if h not in objects:
                blob=gzip.compress(raw,compresslevel=6,mtime=0);name=h+".gzip";(directory/name).write_bytes(blob)
                objects[h]=dict(file=name,stored_sha256=hashlib.sha256(blob).hexdigest(),stored_bytes=len(blob))
            files.append(dict(path=str(f.relative_to(root)),sha256=h,bytes=len(raw),mode=f.stat().st_mode&0o777))
        write(a.archive/"owned-encounter-r1.json",dict(schema=1,files=files,objects=objects,audit_sha256=sha(receipt),dependencies=deps))
        write(a.out,dict(status="preserved-draft-owned-encounter",files=len(files),objects=len(objects),stored_bytes=sum(v["stored_bytes"] for v in objects.values())))
        return
    assert read(a.archive/"owned-encounter-verification-r1.json")["workplace_required"] is False
    art=read(root/"artwork/manifest.json");assert len(art["files"])==1040
    for f in art["files"]:assert sha(root/"artwork"/f["path"])==f["sha256"]
    for folder in [q,a.archive/"owned-encounter-r1"]:
        assert all(f.stat().st_uid==1000 for f in folder.rglob("*"))
        assert not any(f.is_dir() and f.name.endswith(".md") for f in folder.rglob("*"))
    links=0
    for doc in list(root.glob("*.md"))+[p for d in ["docs","artwork","preserved"] for p in (root/d).rglob("*.md")]:
        for target in re.findall(r'\[[^\]]*\]\(([^\s)]+)(?:\s+"[^\"]*")?\)',doc.read_text()):
            from urllib.parse import unquote
            path=target.strip("<>").split("#",1)[0]
            if not path or path.startswith("/") or re.match('[a-zA-Z][a-zA-Z0-9+.-]*:',path):continue
            assert (doc.parent/unquote(path)).exists() or (doc.parent/unquote(path)).resolve()==a.out.resolve(),(doc,target)
            links+=1
    for name in ["audit-owned-encounter.py","export-owned-encounter-ida.py"]:ast.parse((root/"tools"/name).read_text())
    write(a.out,dict(status="passed-owned-encounter-integrity",production_changed=False,source_inputs=197,programs=7,
                     core=923,assets=535,artwork=1040,markdown_links=links,root_owned_outputs=0,player_handoff="pending"))


if __name__=="__main__":main()
