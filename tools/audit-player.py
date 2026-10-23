#!/usr/bin/env python3
"""核對同一冷啟動輸入的原版／覆繪收據；在 Docker 執行。"""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(hd, native):
    left = json.loads((hd / "receipt.json").read_text())
    right = json.loads((native / "receipt.json").read_text())
    for result in (left, right):
        assert result["normal_input_replay"] and not result["snapshot_loaded"]
        assert result["steps"] == 250000000 and not result["unimplemented"]
        assert not result["asset_error"]
    assert left["hd"] and not right["hd"]
    text = left["text"]
    assert text["Full"] > 0 and text["Half"] > 0
    assert text["ErasedInk"] > 0 and text["RenderedGlyphs"] > 0
    assert text["MissingGlyphs"] == 0 and not text["Errors"]
    assert text["BoundLoadSegment"] == 0x110
    assert left["input_events"] == right["input_events"]
    assert left["exec_log"] == right["exec_log"]
    state = sha(hd / "final.state")
    assert state == sha(native / "final.state")
    def files(root):
        return {str(p.relative_to(root)): sha(p) for p in root.rglob("*") if p.is_file()}
    writes = files(hd / "scratch")
    assert writes == files(native / "scratch")
    assert sha(hd / "final.png") != sha(native / "final.png")
    return {"status": "passed-scoped-guest-isolation", "hd": str(hd), "native": str(native),
            "guest_state_sha256": state, "steps": left["steps"], "dos_files": writes,
            "hd_text": text, "input_events_sha256": hashlib.sha256(
                json.dumps(left["input_events"], sort_keys=True).encode()).hexdigest(),
            "limit": "限正常新遊戲、人物頁、返回、F7 開關與移動；不含真正存退讀、戰鬥、HD 美術與 HD 音樂。"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("hd", type=Path)
    parser.add_argument("native", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = audit(args.hd, args.native)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(result["status"], result["guest_state_sha256"], len(result["dos_files"]))
