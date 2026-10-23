#!/usr/bin/env python3
"""在 Pillow Docker 內核對正常視窗存退讀，快照僅供結束後只讀檢視。"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(root, original):
    saved = root / "scratch/gamedata.ay"
    record = read(root / "save/saved.json")
    first = read(root / "save/gui-final.json")
    second = read(root / "reload/gui-final.json")
    assert first["closed"] and first["exited"] and first["exit_code"] == 0
    assert second["closed"] and not second["exited"] and second["presented_scene"] == "map"
    for name, status in [("save", first), ("reload", second)]:
        assert status["hd"] and not status["asset_error"] and not status["unimplemented"]
        assert status["text"]["MissingGlyphs"] == 0 and not status["text"]["Errors"]
        assert read(root / name / "gui-input-receipt.json")["flow"] == name
        assert read(root / name / "continuous-audit.json")["frames"] == status["recorded_frames"]
    assert saved.stat().st_size == 2987
    assert record["sha256"] == digest(saved)
    assert digest(saved) != digest(original / "GAMEDATA.AY")
    actual_buffer = root / "reload/snapshot-readonly/save-buffer-9e000.bin"
    assert saved.read_bytes() == actual_buffer.read_bytes()
    reads = [entry for entry in second["file_ops"]
             if entry["Op"] == "read" and entry["Name"] == "gamedata.ay"]
    assert len(reads) == 1 and reads[0]["Pos"] == 0 and reads[0]["Len"] == 2987 and not reads[0]["Failed"]
    a = Image.open(root / "save/13-saved-map.png").convert("RGB")
    b = Image.open(root / "reload/04-loaded-map.png").convert("RGB")
    assert a.size == b.size == (1280, 800)
    difference = ImageChops.difference(a, b)
    result = {
        "status": "passed-scoped-normal-gui-save-exit-reload",
        "saved_bytes": 2987, "saved_sha256": digest(saved),
        "loaded_buffer_sha256": digest(actual_buffer),
        "buffer_address_space": "dosgolem runtime linear 0x9E000; final state inspected without executing instructions",
        "normal_exit_code": first["exit_code"], "dos_read": reads[0],
        "visual_comparison": {"changed_pixels": sum(x != y for x, y in zip(a.getdata(), b.getdata())),
                              "difference_bbox": difference.getbbox(),
                              "limit": "鏡頭與主角位置另目視核對；動畫相位未同步，不宣稱整幀 parity。"},
        "encounter_dialog_observed": (root / "save/encounter-selected-no.png").exists(),
        "scope": "XTEST 冷啟動、新遊戲、人物頁、F7 儲存與回 DOS、重新啟動繼續；未驗亂數規則、戰鬥、HD 美術或 HD 音樂。",
    }
    (root / "save-cycle-audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("original", type=Path)
    args = parser.parse_args()
    audit(args.root, args.original)
