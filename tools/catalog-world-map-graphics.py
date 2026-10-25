#!/usr/bin/env python3
"""006／045：盤點八張原始地圖的初始圖像編號，不推論執行期可達性。Docker only。"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

PMAP_SHA = "9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02"
PAM_SHA = "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    a = parser.parse_args()
    assert a.original.is_dir() and a.out.parent.is_dir() and not a.out.exists()
    assert sha((a.original/"PAM.AY").read_bytes()) == PAM_SHA
    assert sha((a.original/"PMAP.AY").read_bytes()) == PMAP_SHA
    spec = importlib.util.spec_from_file_location("world_map_decode", Path(__file__).with_name("prepare-hd-intro.py"))
    decoder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(decoder)
    maps, union = [], set()
    for index in range(1, 9):
        path = a.original/f"MAP{index}.AY"
        raw = path.read_bytes()
        data = decoder.decode(raw)
        assert len(data) == 5761 and data[-1:] == b"\x1a"
        assert all(data[y*72+70:y*72+72] == b"\r\n" for y in range(80))
        cells = bytes(v for y in range(80) for v in data[y*72:y*72+70])
        assert len(cells) == 5600 and all(49 <= v <= 113 for v in cells)
        counts = Counter(v-49 for v in cells)
        union.update(counts)
        maps.append(dict(file=path.name, source_bytes=len(raw), source_sha256=sha(raw),
                         decoded_bytes=len(data), decoded_sha256=sha(data), width=70, height=80,
                         stored_native_counts={str(k):counts[k] for k in sorted(counts)},
                         sand_stored_count=sum(counts[k] for k in range(30,45)),
                         landmark48_positions=[[x,y] for y in range(80) for x in range(70) if data[y*72+x]-49 == 48],
                         landmark51_positions=[[x,y] for y in range(80) for x in range(70) if data[y*72+x]-49 == 51]))
    result = dict(schema=1, status="verified-eight-initial-world-maps", pam_sha256=PAM_SHA,
                  pmap_sha256=PMAP_SHA, decode_tool="tools/prepare-hd-intro.py:decode",
                  decoder_sha256=sha(Path(__file__).with_name("prepare-hd-intro.py").read_bytes()),
                  tool_sha256=sha(Path(__file__).read_bytes()), python_version=sys.version.split()[0],
                  stored_encoding="native index = decoded ASCII cell -49; original draw path separately verified in IDA",
                  maps=maps, present_native_indices=sorted(union), absent_native_indices=sorted(set(range(65))-union),
                  scope="initial MAP1..MAP8 data only; excludes MAP00..MAP08 files with a different on-disk format; no runtime reachability or unused-asset claim")
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(dict(status=result["status"], maps=8, initial_cells=44800,
                          absent_native_indices=result["absent_native_indices"])))


if __name__ == "__main__":
    main()
