#!/usr/bin/env python3
"""核對同一冷啟動輸入的原版／覆繪收據；在 Docker 執行。"""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(hd, native, graphics=False, actors=False):
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
    result = {"status": "passed-scoped-guest-isolation", "hd": str(hd), "native": str(native),
            "guest_state_sha256": state, "steps": left["steps"], "dos_files": writes,
            "hd_text": text, "input_events_sha256": hashlib.sha256(
                json.dumps(left["input_events"], sort_keys=True).encode()).hexdigest(),
            "limit": "限正常新遊戲、人物頁、返回、F7 開關與移動；不含真正存退讀、戰鬥、HD 美術與 HD 音樂。"}
    if graphics:
        art = left["graphics"]
        assert not left["graphics_error"] and left["graphics_materials"] > 0
        assert art["Bound"] and art["HDSourceCalls"] > 0 and art["PaintedNativePixels"] > 0
        assert art["CompositedFrames"] > 0 and art["MaskedCalls"] > 0 and art["CopiedBytes"] > 0
        assert not art["Errors"] and not art["GeometryRejected"]
        result["graphics"] = art
        result["graphics_materials"] = left["graphics_materials"]
        result["limit"] = "限此冷啟動、新遊戲、人物頁、返回、F7 開關與移動，確認圖像確實啟用且客體隔離；不含真正存退讀、戰鬥、完整美術或 HD 音樂。"
    if actors:
        assert graphics and left["graphics_actor_materials"] == 12
        art = left["graphics"]
        assert art["ActorCalls"] == art["MaskedCalls"] and art["ActorCalls"] > 0
        assert art["ActorPaintedPixels"] > 0 and not art["ActorFallbackCalls"]
        result["graphics_actor_materials"] = left["graphics_actor_materials"]
        result["limit"] = "十二張主角素材已載入；此路段限五張左右動作的正常冷啟動、人物頁往返與移動，圖像確實繪出且客體隔離。不含其餘朝向實景、真正存退讀、全遊戲或 HD 音樂。"
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("hd", type=Path)
    parser.add_argument("native", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--graphics", action="store_true", help="另要求 HD 圖像實際啟用、遮罩及頁搬移")
    parser.add_argument("--actors", action="store_true", help="另要求十二張主角素材與實際人物層合成，包含 --graphics")
    args = parser.parse_args()
    result = audit(args.hd, args.native, graphics=args.graphics or args.actors, actors=args.actors)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(result["status"], result["guest_state_sha256"], len(result["dos_files"]))
