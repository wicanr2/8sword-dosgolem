#!/usr/bin/env python3
"""030 DRAFT: prepare actual Go army UI inputs/fonts, audit and preserve them."""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
from PIL import Image, ImageDraw, ImageFont, __version__

REL = "workplace/probe-20261023/graphics-first/battle-r1/owned-army-ui-r1"
TOOLS = ["owned-army-ui.go", "owned-army-ui_draw.go", "owned-army-ui_main.go",
         "owned-army-ui_test.go", "owned-army-ui-xcheck.go", "check-owned-army-ui.py", "prepare-owned-army-ui.py", "owned-army-ui.sh"]
FONT_SHA = {
    "noto": "3cffb10242b4b7e6edd439ebf3bd7e392345525e093ea08149e0a0158a1b5151",
    "lishu": "f0ba5eda31727ad89cc0b1f6b9a7dfda02f061fa101c18548b6f8ea0145c108b",
    "caoshu": "cab396b91a5b7c0b4005a35891180d06e6751f5ac261fe680aec65c1ae209033",
    "serif": "93069d8e9e45d515cc421c971a79e6a5777704b348e36a9ef86578bf58adef77",
}


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def write(p, v):
    with p.open("x") as f:
        json.dump(v, f, ensure_ascii=False, indent=2); f.write("\n")


def dependencies(r):
    d = read(r / "preserved/owned-combat-audit-r1.json")
    roots = {"source_inputs": r, "programs": r / "workplace/player", "core_files": r / "workplace/player/runtime-render-r1/src", "asset_hashes": r / "workplace/player/assets-painted-r69"}
    for key, root in roots.items():
        for name, h in d[key].items(): assert sha(root / name) == h, (key, name)
    return {k:d[k] for k in roots}


def stored(r, batch, suffix):
    d = read(r / "preserved" / (batch + ".json"))
    f = next(f for f in d["files"] if f["path"].endswith(suffix))
    obj = d["objects"][f["sha256"]]; blob = (r / "preserved" / batch / obj["file"]).read_bytes()
    assert hashlib.sha256(blob).hexdigest() == obj["stored_sha256"]
    raw = gzip.decompress(blob); assert len(raw) == f["bytes"] and hashlib.sha256(raw).hexdigest() == f["sha256"]
    return raw


def fonts(r, q):
    assert __version__ == "11.3.0"
    index = json.loads(gzip.decompress((r / "preserved/catalog.json.gz").read_bytes()))
    faces = {}
    for id, h in FONT_SHA.items():
        obj = index["objects"][h]; raw = gzip.decompress((r / "preserved" / obj["path"]).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == h
        faces[id] = ImageFont.truetype(io.BytesIO(raw), 48, index=3 if id in ("noto", "serif") else 0)
    assert faces["noto"].getname() == ("Noto Sans CJK TC", "Black")
    assert faces["lishu"].getname() == ("TW-MOE-Li", "Regular")
    chars = {chr(n) for n in range(32,127)} | {"…", "　"}
    for name in ["owned-army-ui.go", "owned-army-ui_draw.go", "owned-army-ui_main.go"]:
        chars.update(c for c in (r / "tools" / name).read_text() if ord(c) >= 128 and c.isprintable())
    for p in read(q / "inputs/army-catalog.json")["profiles"]: chars.update(p["name"])
    chars = sorted(chars); height = ((len(chars)+15)//16)*64
    glyphs = [dict(character=c,cell=[i%16*64,i//16*64,64,64]) for i,c in enumerate(chars)]
    profiles = []
    for id in ["noto","lishu","caoshu"]:
        face = faces[id]; missing = face.getmask("\U0010ffff"); missing = (missing.size, bytes(missing))
        atlas = Image.new("RGBA",(1024,height)); fallbacks = []
        for i,c in enumerate(chars):
            if c in (" ","　"): continue
            mask = face.getmask(c); is_cjk = 0x3400 <= ord(c) <= 0x9fff
            primary = id=="noto" or (is_cjk and (mask.size,bytes(mask)) != missing and bool(mask.getbbox()))
            selected = face if primary else faces["serif"] if id=="lishu" and is_cjk else faces["noto"]
            if not primary: fallbacks.append(c)
            box=selected.getbbox(c); assert box[2]>box[0] and box[3]>box[1], (id,c)
            ink=Image.new("RGBA",(box[2]-box[0],box[3]-box[1]));ImageDraw.Draw(ink).text((-box[0],-box[1]),c,font=selected,fill="white")
            ink.thumbnail((48,52),Image.Resampling.LANCZOS)
            atlas.paste(ink,(i%16*64+(64-ink.width)//2,i//16*64+(64-ink.height)//2))
        filename="army-ui-"+id+".png";atlas.save(q/"ui-assets"/filename)
        profiles.append(dict(id=id,file=filename,sha=sha(q/"ui-assets"/filename),source_sha256=FONT_SHA[id],width=1024,height=height,fallbacks=len(fallbacks),fallback_characters="".join(fallbacks)))
    write(q/"ui-assets/army-ui-fonts.json",dict(schema=1,army_catalog_sha256=sha(q/"inputs/army-catalog.json"),glyphs=glyphs,profiles=profiles,font_sources=FONT_SHA,pillow=__version__,original_font_bytes_modified=False))
    (q/"ui-assets/font-NOTICE.txt").write_text("字型來源沿正式字型契約：Noto Sans CJK TC Black、教育部隸書3.00、劉建毛草。\n原始字型檔不修改；本目錄是一般文字排版快取。教育部隸書缺中文採Noto Serif CJK TC，英數／標點採Noto Black。\n")
    for name in ["font-choice-lishu-NOTICE.txt","font-choice-lishu-LICENSE.txt","font-choice-caoshu-LICENSE.txt"]:
        shutil.copyfile(r/"workplace/player/assets-painted-r69"/name,q/"ui-assets"/name)


def prepare(r,q,d):
    assert not q.exists() and q.parent.stat().st_uid==1000
    q.mkdir();(q/"inputs").mkdir();(q/"ui-assets").mkdir();(q/"session-r1").mkdir()
    for name in ["army-catalog.json","original-save.ay"]:
        (q/"inputs"/name).write_bytes(stored(r,"owned-encounter-r1","/inputs/"+name))
    shutil.copyfile(q/"inputs/original-save.ay",q/"session-r1/gamedata.ay")
    source=q/"go-src"
    for name in d["source_inputs"]:
        target=source/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/name,target)
    (source/"tools").mkdir(exist_ok=True)
    for name in TOOLS: shutil.copyfile(r/"tools"/name,source/"tools"/name)
    text=(r/"tools/research-owned-army.go").read_text().removeprefix("//go:build ignore\n")
    text=text[:text.index("func main()")].replace('\n\t"flag"\n','\n');(source/"tools/owned-army-model.go").write_text(text)
    for suffix in ["mod","sum"]:shutil.copyfile(source/("go."+suffix),q/("probe."+suffix))
    fonts(r,q);write(q/"baseline-r1.json",d)


def verify(archive,out):
    m=read(archive/"owned-army-ui-r1.json");checked=set()
    for f in m["files"]:
        path=Path(f["path"]);assert not path.is_absolute() and ".." not in path.parts
        obj=m["objects"][f["sha256"]];blob=archive/"owned-army-ui-r1"/obj["file"];assert sha(blob)==obj["stored_sha256"]
        raw=gzip.decompress(blob.read_bytes());assert len(raw)==f["bytes"] and hashlib.sha256(raw).hexdigest()==f["sha256"];checked.add(f["sha256"])
    write(out,dict(status="passed-detached-owned-army-ui",files=len(m["files"]),objects=len(checked),workplace_required=False,index_sha256=sha(archive/"owned-army-ui-r1.json")))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("action",choices=["prepare","preview","audit","archive","verify","integrity"])
    p.add_argument("--project",type=Path);p.add_argument("--archive",type=Path);p.add_argument("--out",type=Path);a=p.parse_args()
    assert Path("/.dockerenv").exists() and os.getuid()==1000
    if a.action=="verify":verify(a.archive,a.out);return
    r=a.project;q=r/REL;d=dependencies(r)
    if a.action=="prepare":prepare(r,q,d);print("Prepared actual Go UI and three source-checked font atlases");return
    if a.action=="preview":
        gui=read(q/"gui-r1/receipt.json");assert gui["status"]=="passed-real-x11-army-ui"
        session=q/"session-preview-r1";session.mkdir()
        shutil.copyfile(q/"inputs/original-save.ay",session/"gamedata.ay")
        source=q/"gui-r1/fresh/frame-004-lishu.png"
        target=r/"docs/images/owned-army-ui-preview-r1.png";assert not target.exists()
        Image.open(source).resize((1200,750),Image.Resampling.LANCZOS).save(target)
        write(target.with_suffix(".json"),dict(prototype=True,source_path=str(source.relative_to(r)),source_sha256=sha(source),preview_sha256=sha(target),source_size=[1920,1200],preview_size=[1200,750],
            capture="Actual Ebiten X11 window; full RGB checked against X11 GetImage by the audit.",font="lishu",fixture="5000 initial gold, leadership 1000, rank 1, all 33 offers stock 1000",production_path=False,
            glyph_emblems="First character of unit name; no new unit portraits."))
        return
    if a.action=="audit":
        gui=read(q/"gui-r1/receipt.json");assert gui["status"]=="passed-real-x11-army-ui" and gui["guest_instructions"]==0
        assert gui["cold_army_equal"] and gui["held_mouse_single_purchase"] and gui["seventh_stack_rejected"] and gui["over_quantity_rejected"]
        compared=[]
        pack=read(q/"ui-assets/army-ui-fonts.json")
        for item in gui["screens"]:
            meta=read(q/"gui-r1"/item["phase"]/item["metadata"]);png=q/"gui-r1"/item["phase"]/item["canvas"];screen=q/"gui-r1"/item["phase"]/item["screen"]
            image=Image.open(png).convert("RGB");actual=Image.open(screen).convert("RGB");assert image.size==actual.size==(1920,1200)
            assert image.tobytes()==actual.tobytes(),item
            assert meta["font_id"]==item["font"]==meta["presented_font"]
            assert meta["font_sources"][item["font"]]==FONT_SHA[item["font"]]
            assert hashlib.sha256(Image.open(png).convert("RGBA").tobytes()).hexdigest()==meta["canvas_sha256"]==meta["presented_sha256"]
            for f in meta["text_fields"]:
                rect,ink=f["Rect"],f["Ink"];assert 0<=rect[0]<rect[2]<=1920 and 0<=rect[1]<rect[3]<=1200
                if ink[2]>ink[0] and ink[3]>ink[1]:assert rect[0]<=ink[0]<ink[2]<=rect[2] and rect[1]<=ink[1]<ink[3]<=rect[3]
            compared.append(dict(font=item["font"],canvas_sha256=sha(png),x11_ppm_sha256=sha(screen)))
        assert set(v["font"] for v in compared)=={"noto","lishu","caoshu"}
        for p in pack["profiles"]:assert sha(q/"ui-assets"/p["file"])==p["sha"] and p["source_sha256"]==FONT_SHA[p["id"]]
        profiles={p["id"]:p for p in read(q/"inputs/army-catalog.json")["profiles"]}
        before,after=gui["initial_army"],gui["final_army"]
        assert before["gold"]==5000 and before["leadership"]==after["leadership"]==1000
        assert before["recruit_rank"]==after["recruit_rank"]==1 and before["rules"]==after["rules"]=="tactics"
        assert all(s["count"]==0 and s["unit"]=="" for s in before["slots"])
        expected={"openkb:wolf":30,"native:01":1,"native:02":1,"native:06":1,"native:07":1,"native:11":1}
        assert {s["unit"]:s["count"] for s in after["slots"]}==expected
        spent=sum(profiles[k]["gold"]*n for k,n in expected.items());command=sum(profiles[k]["command"]*n for k,n in expected.items())
        assert after["gold"]==5000-spent==3789 and command==97
        for key,offer in before["offers"].items():
            assert offer["stock"]==1000 and after["offers"][key]==dict(unit=offer["unit"],stock=1000-expected.get(offer["unit"],0))
        assert sha(q/"session-r1/gamedata.ay")==sha(q/"inputs/original-save.ay")
        assert sha(q/"session-r1/gamedata.ay.army.json")==gui["final_session_sha256"]
        assert not (q/"session-r1/.owned-army-ui.lock").exists()
        assert sorted(p.name for p in (q/"session-preview-r1").iterdir())==["gamedata.ay"]
        test=(q/"go-test-r2.log").read_text();assert "PASS" in test and "FAIL" not in test and "SKIP" not in test
        write(a.out,dict(status="passed-draft-owned-army-ui",dependencies=d,ui_screens=compared,real_x11=True,cold_army_equal=True,gui=gui,
            prototype=True,production_changed=False,source_tools={n:sha(r/"tools"/n) for n in TOOLS},fonts_source=FONT_SHA,
            independent_resource_check=dict(gold_spent=spent,final_gold=after["gold"],command_used=command,all_offer_stocks_match=True),
            limits=["Independent Go UI prototype with explicit resource/shop fixtures, not normal native world gameplay.","The formal Engine still rejects expanded army sidecars before DOS. No movement, combat or quest handoff is enabled."]))
        return
    if a.action=="archive":
        audit=read(q/"audit-r1.json");assert audit["status"]=="passed-draft-owned-army-ui" and audit["source_tools"]=={n:sha(r/"tools"/n) for n in TOOLS}
        folder=a.archive/"owned-army-ui-r1";folder.mkdir();selected={f for f in q.rglob("*") if f.is_file()};selected.update(r/"tools"/n for n in TOOLS+["research-owned-army.go"]);selected.add(r/"docs/spec/030-battle-expansion-proposal.md")
        selected.update(r/"docs/images"/n for n in ["owned-army-ui-preview-r1.png","owned-army-ui-preview-r1.json"])
        files,objects=[],{}
        for f in sorted(selected):
            assert not f.is_symlink() and f.stat().st_uid==1000
            raw=f.read_bytes();h=hashlib.sha256(raw).hexdigest()
            if h not in objects:
                blob=gzip.compress(raw,compresslevel=6,mtime=0);name=h+".gzip";(folder/name).write_bytes(blob);objects[h]=dict(file=name,stored_sha256=hashlib.sha256(blob).hexdigest(),stored_bytes=len(blob))
            files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(raw),mode=f.stat().st_mode&0o777))
        write(a.archive/"owned-army-ui-r1.json",dict(schema=1,files=files,objects=objects,dependencies=d,audit_sha256=sha(q/"audit-r1.json")))
        write(a.out,dict(status="preserved-draft-owned-army-ui",files=len(files),objects=len(objects),stored_bytes=sum(v["stored_bytes"] for v in objects.values())))
        return
    assert read(a.archive/"owned-army-ui-verification-r1.json")["workplace_required"] is False
    art=read(r/"artwork/manifest.json");assert len(art["files"])==1040
    for f in art["files"]:assert sha(r/"artwork"/f["path"])==f["sha256"]
    for folder in [q,a.archive/"owned-army-ui-r1"]:
        assert all(f.stat().st_uid==1000 for f in folder.rglob("*"));assert not any(f.is_dir() and f.name.endswith(".md") for f in folder.rglob("*"))
    write(a.out,dict(status="passed-owned-army-ui-integrity",production_changed=False,source_inputs=197,programs=7,core=923,assets=535,artwork=1040,root_owned_outputs=0))


if __name__=="__main__":main()
