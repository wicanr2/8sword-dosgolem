#!/usr/bin/env python3
"""045：核對目前地圖材質缺口，輸出原生參考及研究步行規劃。Docker only。"""
import argparse
from collections import deque
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

from PIL import Image, ImageDraw

PMAP_SHA = "9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02"
MAP_SHA = "7835299e69ca627034132cb6dffa6f40df640f46dfce430642ad9780093a346a"
EGA = [(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),(170,85,0),(170,170,170),(85,85,85),(85,85,255),(85,255,85),(85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("assets","original","out"):
        parser.add_argument("--"+name,type=Path,required=True)
    a = parser.parse_args()
    assert not a.out.exists() and a.out.parent.is_dir()
    raw = (a.original/"PMAP.AY").read_bytes()
    mapraw = (a.original/"MAP1.AY").read_bytes()
    assert sha(raw) == PMAP_SHA and sha(mapraw) == MAP_SHA
    terrain = read(a.assets/"terrain.json")
    assert terrain["source_sha256"] == PMAP_SHA
    covered = {e["source_index"] for k in ("materials","composites","overlays") for e in terrain.get(k,[])}
    castle = read(a.assets/"map-castle.json")
    chest = read(a.assets/"map-chest.json")
    assert castle["source_sha256"] == chest["source_sha256"] == PMAP_SHA
    covered |= {e["source_index"] for e in castle["records"]}
    covered.add(chest["source_index"])
    # Optional later groups use the same source/index/image contract as 045.
    for path in sorted(a.assets.glob("map-landmark-*.json")):
        entry = read(path)
        index = entry["source_index"]
        assert 0 <= index < 65 and path.name == f"map-landmark-{index}.json"
        assert entry["source_file"] == "PMAP.AY" and entry["source_sha256"] == PMAP_SHA
        record = raw[index*1004:(index+1)*1004]
        assert sha(record) == entry["record_sha256"] and sha(record[:804]) == entry["native_sha256"]
        image = entry["image"]
        assert Path(image["file"]).name == image["file"] and sha((a.assets/image["file"]).read_bytes()) == image["sha256"]
        covered.add(index)
    missing = sorted(set(range(65))-covered)
    assert set(missing) <= {48,49,51,52,54,55,56}
    spec = importlib.util.spec_from_file_location("map_pending_decode",Path(__file__).with_name("prepare-hd-intro.py"))
    decoder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(decoder)
    data = decoder.decode(mapraw)
    assert len(data) == 5761 and data[-1] == 26
    assert all(data[y*72+70:y*72+72] == b"\r\n" for y in range(80))
    world = [[v-49 for v in data[y*72:y*72+70]] for y in range(80)]
    origin = (20,8)
    allowed = {0,50,53,57,62,63,64} | set(range(30,45))
    assert world[origin[1]][origin[0]] in allowed
    queue,paths = deque([origin]),{origin:""}
    while queue:
        x,y = queue.popleft()
        for dx,dy,letter in [(0,-1,"N"),(-1,0,"W"),(1,0,"E"),(0,1,"S")]:
            point = (x+dx,y+dy)
            if 0<=point[0]<70 and 0<=point[1]<80 and point not in paths and world[point[1]][point[0]] in allowed:
                paths[point] = paths[x,y]+letter
                queue.append(point)
    a.out.mkdir()
    sheet = Image.new("RGB",(1536,668),(18,25,20))
    draw = ImageDraw.Draw(sheet)
    records = []
    for n,index in enumerate(missing):
        record = raw[index*1004:(index+1)*1004]
        assert len(record) == 1004 and struct.unpack_from("<HH",record) == (8,25)
        native = bytes(sum(((record[4+q*200+p//8] >> (7-p%8)) & 1) << q for q in range(4)) for p in range(1600))
        rgb = bytes(v for c in native for v in EGA[c])
        image = Image.frombytes("RGB",(64,25),rgb)
        name = f"pmap-{index}-native-reference-r1.png"
        image.resize((768,600),Image.Resampling.NEAREST).save(a.out/name)
        x,y = n%4*384,n//4*334
        draw.text((x+8,y+8),f"PMAP {index} | native 64 x 25",fill=(240,230,190))
        sheet.paste(image.resize((384,300),Image.Resampling.NEAREST),(x,y+34))
        positions = [(x,y) for y,row in enumerate(world) for x,value in enumerate(row) if value == index]
        routes = []
        for target in positions:
            visible = [(len(path),point,path) for point,path in paths.items() if abs(point[0]-target[0])<=3 and abs(point[1]-target[1])<=3 and point!=target]
            if visible:
                _,end,path = min(visible)
                routes.append(dict(target=target,planned_end=end,directions=path,steps=len(path)))
        routes.sort(key=lambda entry:entry["steps"])
        records.append(dict(index=index,native_sha256=sha(record[:804]),record_sha256=sha(record),reference_file=name,
                            reference_sha256=sha((a.out/name).read_bytes()),map1_positions=positions,planned_visible_routes=routes))
    sheet.save(a.out/"pending-overview-r1.png")
    result = dict(schema=1,source_file="PMAP.AY",source_sha256=PMAP_SHA,map_file="MAP1.AY",map_sha256=MAP_SHA,
                  asset_set=a.assets.name,asset_files=len(list(a.assets.iterdir())),main_records=65,registered_main_records=65-len(missing),
                  scope="manifest coverage and raw geometry only; no normal source, gameplay identity or reachability claim",
                  origin=origin,walkable_source_indices=sorted(allowed),records=records)
    (a.out/"catalog.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(dict(registered=65-len(missing),missing=missing,nearest={str(e["index"]):e["planned_visible_routes"][:1] for e in records})))


if __name__ == "__main__":
    main()
