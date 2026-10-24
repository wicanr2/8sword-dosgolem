#!/usr/bin/env python3
"""038：正常無頭完整 Frame 的獨立模型與客體純度。實際 GUI 另驗。"""
import argparse
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location("model", Path(__file__).with_name("audit-encounter-gui.py"))
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ["assets", "original", "cache", "run", "out"]:
        ap.add_argument("--"+name, type=Path, required=True)
    a = ap.parse_args()
    assert not a.out.exists()
    packets = sorted((a.run/"research-encounter-draws").glob("*-first-draw.json"))
    assert len(packets) == 15
    oracle = model.Model(a.assets, a.original, a.cache)
    results = []
    for p in packets:
        meta = model.read(p)
        assert meta["capture_kind"] == "normal-headless-frame" and meta["record"] == 10
        results.append(oracle.frame(p.with_suffix("")))
    assert {r["height"] for r in results} == set(range(1, 26, 2))
    assert {r["font_id"] for r in results if r["height"] == 25} == {"noto", "lishu", "caoshu"}
    result = dict(schema=1, status="passed-independent-normal-frames", packets=results,
                  pixels_per_frame=2304000, frame_purity_checks=len(results), actual_gui_verified=False,
                  model_sha256=model.sha(Path(__file__).with_name("audit-encounter-gui.py")),
                  tool_sha256=model.sha(Path(__file__)), limitation="normal headless frames; not actual GUI Draws or gameplay/RNG parity")
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    print("15 complete frames, all 13 heights, three fonts and Frame purity passed")


if __name__ == "__main__":
    main()
