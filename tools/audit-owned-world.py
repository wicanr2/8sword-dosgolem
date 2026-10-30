#!/usr/bin/env python3
"""030: independently audit and preserve the DRAFT Go world ownership slice."""
import argparse
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    return json.loads(p.read_text())


def write(p, v):
    with p.open("x") as f:
        json.dump(v, f, ensure_ascii=False, indent=2)
        f.write("\n")


def verify(archive, out):
    manifest = read(archive / "owned-world-r1.json")
    checked = set()
    for item in manifest["files"]:
        path = Path(item["path"])
        assert not path.is_absolute() and ".." not in path.parts
        obj = manifest["objects"][item["sha256"]]
        blob = archive / "owned-world-r1" / obj["file"]
        assert sha(blob) == obj["stored_sha256"]
        raw = gzip.decompress(blob.read_bytes())
        assert len(raw) == item["bytes"] and hashlib.sha256(raw).hexdigest() == item["sha256"]
        checked.add(item["sha256"])
    write(out, dict(status="passed-detached-owned-world", files=len(manifest["files"]),
                    objects=len(checked), index_sha256=sha(archive / "owned-world-r1.json"),
                    workplace_required=False))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["prepare", "baseline", "audit", "page", "archive", "verify", "integrity"])
    p.add_argument("--project", type=Path)
    p.add_argument("--archive", type=Path)
    p.add_argument("--out", type=Path)
    a = p.parse_args()
    assert Path("/.dockerenv").is_file() and os.getuid() == 1000
    if a.action == "verify":
        verify(a.archive, a.out)
        return
    r = a.project
    q = r / "workplace/probe-20261023/graphics-first/battle-r1/owned-world-r1"
    player = r / "workplace/player"
    baseline = read(r / "preserved/owned-combat-audit-r1.json")
    tools = ["probe-owned-world.go", "research-owned-world.go", "research-owned-world_test.go",
             "owned-world-check.go", "export-owned-world-ida.py", "audit-owned-world.py"]
    roots = {"source_inputs": r, "programs": player, "core_files": player / "runtime-render-r1/src",
             "asset_hashes": player / "assets-painted-r69"}
    for key, folder in roots.items():
        for name, h in baseline[key].items():
            assert sha(folder / name) == h, (key, name)
    if a.action == "prepare":
        assert not q.exists() and q.parent.stat().st_uid == 1000
        q.mkdir()
        (q / "ida").mkdir()
        source = q / "probe-src"
        for name in baseline["source_inputs"]:
            dest = source / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(r / name, dest)
        (source / "tools").mkdir(exist_ok=True)
        for name in tools[:4]:
            shutil.copyfile(r / "tools" / name, source / "tools" / name)
        common = (r / "tools/research-owned-army.go").read_text().removeprefix("//go:build ignore\n")
        common = common[:common.index("func main()")].replace('\n\t"flag"\n', '\n')
        (source / "tools/owned-army-model.go").write_text(common)
        shutil.copyfile(source / "go.mod", q / "probe.mod")
        shutil.copyfile(source / "go.sum", q / "probe.sum")
    if a.action in {"prepare", "baseline"}:
        (q / "inputs").mkdir()
        old = q.parent / "owned-combat-r1"
        for src, dst in [("army-catalog.json", "army-catalog.json"),
                         ("combat-catalog.json", "combat-catalog.json"),
                         ("inputs/original-save.ay", "original-save.ay")]:
            shutil.copyfile(old / src, q / "inputs" / dst)
        write(q / "baseline.json", {k: baseline[k] for k in roots})
        print("Pinned unchanged 197 sources, 7 programs, 923 core and 535 assets")
        return
    if a.action == "audit":
        ida = read(q / "ida/ida-world-r3.json")
        pam = r / "workplace/intake-20261023/sources/game/8sword/PAM.AY"
        raw = pam.read_bytes()
        assert sha(pam) == ida["input_sha256"] == "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"
        assert sha(r / "workplace/probe-20261023/text-first/PAM.i64") == ida["database_sha256"]
        assert sha(r / "tools/export-owned-world-ida.py") == ida["exporter_sha256"]
        word = lambda at: struct.unpack_from("<H", raw, at)[0]
        header = word(8) * 16
        relocated = bytearray(raw[header:])
        for i in range(word(6)):
            at = word(24) + i * 4
            off = word(at + 2) * 16 + word(at)
            value = struct.unpack_from("<H", relocated, off)[0]
            struct.pack_into("<H", relocated, off, (value + 0x1000) & 65535)
        lines = 0
        for body in ida["functions"]:
            for line in body["lines"]:
                off = line["ida_linear"] - 0x10000
                data = bytes.fromhex(line["bytes"])
                assert off + header == line["file_offset"] and relocated[off:off + len(data)] == data
                lines += 1
        observed = read(q / "normal-r4/receipt.json")
        control = read(q / "control-r3/receipt.json")
        assert observed["normal_inputs"] and not observed["normal_ram_injection"] and not observed["normal_snapshot_loaded"]
        assert observed["keys"] == control["keys"] and observed["normal_world"] == control["normal_world"]
        assert sha(q / "normal-r4/normal-final.state") == sha(q / "control-r3/normal-final.state") == observed["state_sha256"] == control["state_sha256"]
        assert sha(q / "normal-r4/normal-result.png") == sha(q / "control-r3/normal-result.png")
        # The failed helper-input r2 did not contaminate its completed normal path.
        assert sha(q / "normal-r2/normal-final.state") == observed["state_sha256"]
        normal_events = observed["events"][:11]
        events = {v["name"]: v for v in normal_events}
        assert len(events) == 11
        assert events["army-copy-before"]["army_054a"] == events["army-copy-after"]["battle_56e8"][:12]
        assert events["army-copy-after"]["battle_56e8"][12:] == [0] * 12
        assert events["compact-after"]["battle_56e8"][:12] == events["army-writeback-after"]["army_054a"]
        assert int.from_bytes(base64.b64decode(events["world-reward-entry"]["stack"])[4:6], "little") == 1
        assert observed["normal_world"]["progress_04f2"][3] == 400
        threshold_offset = 0x2d780 + 0x5b2 - 0x10000 + header
        thresholds = list(struct.unpack_from("<6H", raw, threshold_offset))
        assert thresholds == observed["normal_world"]["rank_thresholds_05b2"][:6]
        controls = []
        for v in observed["fixtures"]:
            assert v["error"] == "<nil>"
            value = list(v["before"]["progress_04f2"])
            value[1] = min(30000, value[1] + v["reward_merit"])
            value[3] = min(30000, value[3] + v["reward_gold"])
            if value[0] < 5 and value[1] > 100:
                value[0] += 1
                value[2] = min(30000, value[2] + 100)
                value[4] = min(30000, value[4] + 100)
                value[5] = min(30000, value[5] + value[0] * 3)
            assert value == v["after"]["progress_04f2"], v["name"]
            controls.append(dict(name=v["name"], result=value))
        assert len(controls) == 7
        flow = read(q / "flow-r2/receipt.json")
        cold = read(q / "cold-final-r2/receipt.json")
        mid = read(q / "cold-mid-r2/receipt.json")
        assert flow["guest_instructions"] == 0 and not flow["player_path"] and flow["engine_guard"]
        assert flow["world"] == cold["world"] and mid["world"]["battle"]["state"]["acted"][1][0]
        counts = [30, 15]
        stats = read(q / "inputs/combat-catalog.json")["profiles"]
        ids = ["openkb:wolf", "openkb:skel"]
        for event in flow["events"]:
            side = event["action"]["side"]
            assert event["action"]["source"] == event["action"]["target"] == 0
            damage = counts[side] * stats[ids[side]]["attack"] // 5
            quotient = damage // stats[ids[1 - side]]["hp"]
            loss = 0 if quotient == 0 else counts[1 - side] if quotient + 1 >= counts[1 - side] else quotient
            assert event["damage"] == damage and event["loss"] == loss
            counts[1 - side] -= loss
            assert event["after"] == counts[1 - side]
        assert counts == [29, 0] and len(flow["events"]) == 28
        profiles = {v["id"]: v for v in read(q / "inputs/army-catalog.json")["profiles"]}
        gold = profiles[ids[1]]["gold"] * 15
        merit = profiles[ids[1]]["command"] * 15 // 2
        final = flow["world"]
        assert gold == flow["reward"]["gold"] == 600 and merit == flow["reward"]["merit"] == 22
        assert final["army"]["gold"] == 5000 - 30 * profiles[ids[0]]["gold"] + gold == 4400
        assert final["army"]["slots"][0]["count"] == 29 and final["army"]["offers"]["wolf-camp"]["stock"] == 970
        assert flow["initial"]["progress"]["thresholds"] == thresholds
        assert final["progress"]["merit"] == 2012 and final["progress"]["rank"] == final["army"]["recruit_rank"] == 2
        assert final["army"]["leadership"] == 1100 and final["encounters"]["skeleton-patrol"]["cleared"] and final["battle"] is None
        assert sha(q / "flow-r2/save/gamedata.ay") == sha(q / "inputs/original-save.ay") == flow["original_sha256"]
        log = (q / "world-tests-r2.log").read_text()
        assert "PASS" in log and "FAIL" not in log and "SKIP" not in log
        large_log = (q / "world-large-r1.log").read_text()
        assert "TestWorldLargeRewardsAndOverflow" in large_log and "PASS" in large_log and "FAIL" not in large_log and "SKIP" not in large_log
        assert not (q / "world-vet-r2.log").read_text().strip()
        assert "go1.24.13" in (q / "go-version.txt").read_text()
        browser = read(q / "browser-r1/browser-r1.json")
        assert browser["status"] == "passed-go-world-replay" and not browser["game_window"] and not browser["mobile_horizontal_overflow"]
        for name, h in baseline["source_inputs"].items():
            assert sha(q / "probe-src" / name) == h
        for name in tools[:4]:
            assert sha(r / "tools" / name) == sha(q / "probe-src/tools" / name)
        audit = dict(status="passed-draft-owned-world", production_changed=False, player_path=False,
                     ida_functions=len(ida["functions"]), ida_lines=lines, operand_candidates=len(ida["operand_candidates"]),
                     normal_boundary_events=11, normal_state_sha256=observed["state_sha256"],
                     original_controls=controls, actions=28, remaining_troops=29, gold=4400, merit=2012, rank=2,
                     mid_battle_cold_load=True, final_cold_load=True,
                     sources={"tools/" + n: sha(r / "tools" / n) for n in tools},
                     dependencies={n: sha(r / n) for n in ["preserved/owned-combat-r1.json", "preserved/troop-capacity-r1.json"]},
                     unchanged=dict(source_inputs=197, programs=7, core=923, assets=535, artwork=1040),
                     limits=["DRAFT; normal expanded-unit UI/world integration remains pending.",
                             "Normal player path is escape, not victory. Seven victory controls use explicit direct calls.",
                             "Go preserves original 30000 stat caps but does not emulate signed-16-bit overflow.",
                             "Defeat/retreat penalties, quests and unknown legacy field labels remain unsupported."])
        write(a.out, audit)
        print("Passed independent original/world/save audit; production unchanged")
        return
    if a.action == "page":
        f = read(q / "flow-r2/receipt.json")
        data = {k: f[k] for k in ["initial", "events", "world", "reward"]}
        template = '''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Go世界交接試作</title><style>body{margin:0;background:#102b28;color:#f7eccd;font:18px/1.7 system-ui}main{max-width:900px;margin:auto;padding:28px}section{border:1px solid #b99b5c;padding:20px;margin:20px 0;border-radius:10px}button{font:inherit;background:#e5ca89;border:0;border-radius:6px;padding:10px 16px;margin:5px;cursor:pointer}input{width:100%}strong{color:#ffdc83}.stats{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.stats div{background:#193d35;padding:12px}h1{font-size:28px}</style><main><h1>Go世界交接試作</h1><p>已串起招募、戰鬥、獎勵、晉級與存讀。這是資料流程回放，尚未接入遊戲內的軍隊與戰鬥介面。</p><section><button id="back">上一步</button><button id="next">下一步</button><button id="end">看結算</button><input id="step" type="range" min="0" max="29" value="0"><p id="message" role="status"></p><div class="stats" id="stats"></div></section><section><h2>這輪已驗證</h2><p>30隻野狼迎戰15名骷髏兵，完成28次Go行動後剩29隻。勝利獲得600金錢與22點戰績，等級1升至2。招募庫存維持970。</p><p>戰中與戰後各由另一個程序讀回。已行動部隊不能再動，已清除敵軍不能再次開戰，戰果不能重複領取，舊狀態不能覆寫新存檔。</p><p>原版正常路徑已抽驗遇敵、撤退、扣款與回地圖。七組勝利數值控制另以原版常式驗證。敗退、任務獎勵及新增兵種的正式玩家介面仍待接入。</p></section></main><script>const data=DATA,s=document.querySelector('#step');function render(){const n=+s.value;let counts=[30,15];for(const e of data.events.slice(0,Math.min(n,28)))counts[1-e.action.side]=e.after;const settled=n===29,w=data.world;const entries=[['我方兵力',counts[0]],['敵方兵力',counts[1]],['金錢',settled?w.army.gold:data.initial.army.gold],['戰績',settled?w.progress.merit:data.initial.progress.merit],['等級',settled?w.progress.rank:1],['領導力',settled?w.army.leadership:1000],['敵軍狀態',settled?'已清除':'尚未結算'],['招募庫存',970]];document.querySelector('#stats').replaceChildren(...entries.map(([label,value])=>{const el=document.createElement('div');el.textContent=label+'：'+value;return el}));document.querySelector('#message').textContent=settled?'戰果已一次提交，獎勵與部隊共同寫入存檔。':n===28?'敵軍全滅，等待結算。':n?'行動 '+n+' / 28，對方減員 '+data.events[n-1].loss+'。':'招募完成，準備開戰。'}s.oninput=render;document.querySelector('#back').onclick=()=>{s.value=Math.max(0,+s.value-1);render()};document.querySelector('#next').onclick=()=>{s.value=Math.min(29,+s.value+1);render()};document.querySelector('#end').onclick=()=>{s.value=29;render()};render();</script></html>'''
        page = r / "docs/images/owned-world-data-chain-r1.html"
        assert not page.exists()
        page.write_text(template.replace("DATA", json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")))
        print("Created Go world transaction replay")
        return
    if a.action == "archive":
        assert read(q / "audit-final.json")["status"] == "passed-draft-owned-world"
        directory = a.archive / "owned-world-r1"
        assert not directory.exists()
        directory.mkdir()
        selected = {f for f in q.rglob("*") if f.is_file()}
        selected.update(r / "tools" / n for n in tools)
        selected.update(r / n for n in ["docs/spec/030-battle-expansion-proposal.md", "docs/images/owned-world-data-chain-r1.html"])
        files, objects = [], {}
        for f in sorted(selected):
            assert not f.is_symlink() and f.stat().st_uid == 1000
            raw = f.read_bytes()
            h = hashlib.sha256(raw).hexdigest()
            if h not in objects:
                blob = gzip.compress(raw, compresslevel=6, mtime=0)
                name = h + ".gzip"
                (directory / name).write_bytes(blob)
                objects[h] = dict(file=name, stored_sha256=hashlib.sha256(blob).hexdigest(), stored_bytes=len(blob))
            files.append(dict(path=str(f.relative_to(r)), sha256=h, bytes=len(raw), mode=f.stat().st_mode & 0o777))
        write(a.archive / "owned-world-r1.json", dict(schema=1, files=files, objects=objects,
              audit_sha256=sha(q / "audit-final.json"), dependencies=read(q / "audit-final.json")["dependencies"]))
        write(a.out, dict(status="preserved-draft-owned-world", files=len(files), objects=len(objects),
                          stored_bytes=sum(v["stored_bytes"] for v in objects.values())))
        return
    # Final hygiene checks, without rebuilding unchanged programs or assets.
    assert read(a.archive / "owned-world-verification-r1.json")["workplace_required"] is False
    assert sha(a.archive / "owned-world-audit-r1.json") == read(a.archive / "owned-world-r1.json")["audit_sha256"]
    art = read(r / "artwork/manifest.json")
    assert len(art["files"]) == 1040
    for item in art["files"]:
        assert sha(r / "artwork" / item["path"]) == item["sha256"]
    for root in [q, a.archive / "owned-world-r1"]:
        assert all(f.stat().st_uid == 1000 for f in root.rglob("*"))
        assert not any(f.is_dir() and f.name.endswith(".md") for f in root.rglob("*"))
    links = 0
    for doc in list(r.glob("*.md")) + [f for d in ["docs", "artwork", "preserved"] for f in (r / d).rglob("*.md")]:
        for target in re.findall(r'\[[^\]]*\]\(([^\s)]+)(?:\s+"[^\"]*")?\)', doc.read_text()):
            path = target.strip("<>").split("#", 1)[0]
            if not path or path.startswith("/") or re.match('[a-zA-Z][a-zA-Z0-9+.-]*:', path):
                continue
            from urllib.parse import unquote
            assert (doc.parent / unquote(path)).exists() or (doc.parent / unquote(path)).resolve() == a.out.resolve(), (doc, target)
            links += 1
    write(a.out, dict(status="passed-owned-world-integrity", production_changed=False,
                      source_inputs=197, programs=7, core=923, assets=535, artwork=1040,
                      markdown_links=links, root_owned_outputs=0, player_handoff="pending"))


if __name__ == "__main__":
    main()
