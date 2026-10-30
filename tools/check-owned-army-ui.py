#!/usr/bin/env python3
"""030 DRAFT: real XTEST recruitment, font presentation and a second GUI process."""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def write(p,v):
    with p.open("x") as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write("\n")


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--work",type=Path,required=True);a=p.parse_args();q=a.work
    assert Path("/.dockerenv").exists() and os.getuid()==1000
    out=q/"gui-r1";assert not out.exists();out.mkdir()
    env=dict(os.environ,DISPLAY=":98",LIBGL_ALWAYS_SOFTWARE="1",GALLIUM_DRIVER="llvmpipe",LP_NUM_THREADS="1",MESA_GLTHREAD="false",GOMAXPROCS="2")
    children=[];streams=[];screens=[];process=None;phase=None
    signal.signal(signal.SIGTERM,lambda *_: (_ for _ in ()).throw(SystemExit(143)))
    signal.signal(signal.SIGINT,lambda *_: (_ for _ in ()).throw(SystemExit(130)))

    def call(*args):
        r=subprocess.run([str(q/"xcheck"),*map(str,args)],env=env,capture_output=True,text=True,timeout=12)
        assert r.returncode==0,(args,r.returncode,r.stdout,r.stderr)
        return r.stdout

    def state():
        try:return read(out/phase/"ui-state.json")
        except (OSError,ValueError):return None

    def wait(predicate,seconds=20):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            if process.poll() is not None:
                raise AssertionError(("UI exited",process.returncode,(out/phase/"player.log").read_text()[-2500:]))
            s=state()
            if s and predicate(s):return s
            time.sleep(.05)
        raise AssertionError(("UI condition timed out",state()))

    def key(name):call("key",name)
    def chord(modifier,keyname):call("key",modifier,"down");key(keyname);call("key",modifier,"up")
    def click(x,y):call("click",x,y)
    def quantity(text):
        click(1420,944);chord("Control_L","a")
        for c in text:key(c)
        return wait(lambda s:s["quantity"]==text)

    def snapshot(label):
        old=state()["last_capture"];key("F12")
        s=wait(lambda s:s["last_capture"]!=old and s["presented_sha256"]==s["canvas_sha256"] and s["presented_font"]==s["font_id"])
        filename=label+"-screen.ppm";call("screenshot",out/phase/filename)
        metadata=label+"-state.json";write(out/phase/metadata,s)
        screens.append(dict(phase=phase,font=s["font_id"],canvas=s["last_capture"],screen=filename,metadata=metadata))
        return s

    def start(name):
        nonlocal phase,process
        phase=name;(out/name).mkdir();log=(out/name/"player.log").open("w");streams.append(log)
        process=subprocess.Popen([str(q/"army-ui"),"-catalog",str(q/"inputs/army-catalog.json"),"-ui-assets",str(q/"ui-assets"),"-session",str(q/"session-r1"),"-capture-dir",str(out/name),"-scale","1","-max-updates","12000"],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        children.append(process)
        wait(lambda s:s["draws"]>0 and s["presented_sha256"]==s["canvas_sha256"])
        info=json.loads(call("info"));assert info==dict(width=1920,height=1200)

    def stop():
        chord("Control_L","q");assert process.wait(timeout=20)==0
        assert not (q/"session-r1/.owned-army-ui.lock").exists()

    def select(id):
        click(1340,270);s=wait(lambda s:not s["new_only"] and s["page"]==0)
        profiles=read(q/"inputs/army-catalog.json")["profiles"];position=next(i for i,p in enumerate(profiles) if p["id"]==id)
        for page in range(position//6):click(1780,760);wait(lambda s,page=page:s["page"]==page+1)
        s=state();row=next(r for r in s["rows"] if r["unit"]==id);x1,y1,x2,y2=row["rect"];click((x1+x2)//2,(y1+y2)//2)
        return wait(lambda s:s["selected"]==row["id"] and s["quantity"]=="1")

    try:
        log=(out/"xvfb.log").open("w");streams.append(log)
        xvfb=subprocess.Popen(["Xvfb",env["DISPLAY"],"-screen","0","2560x1440x24","-nolisten","tcp"],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(xvfb)
        time.sleep(.5);assert xvfb.poll() is None
        start("fresh");initial=snapshot("initial-noto");assert initial["army"]["gold"]==5000 and initial["army"]["slots"]==[{"unit":"","count":0}]*6
        select("openkb:wolf");quantity("30");call("hold",1500,1035,450)
        s=wait(lambda s:s["transactions"]==1);assert s["army"]["gold"]==3800 and s["army"]["slots"][0]==dict(unit="openkb:wolf",count=30)
        time.sleep(.25);assert state()["transactions"]==1
        saved=s["session_sha256"];army=s["army"];quantity("1000");click(1510,1035)
        s=wait(lambda s:"可招募" in s["message"]);assert s["army"]==army and s["session_sha256"]==saved and s["transactions"]==1
        click(1370,165);s=wait(lambda s:"新增兵種" in s["message"]);assert s["army"]["rules"]=="tactics" and s["session_sha256"]==saved
        key("F10");wait(lambda s:s["font_id"]=="lishu" and s["presented_font"]=="lishu");snapshot("purchased-lishu")
        key("F10");wait(lambda s:s["font_id"]=="caoshu" and s["presented_font"]=="caoshu");snapshot("purchased-caoshu")
        click(1500,72);wait(lambda s:s["font_id"]=="lishu" and s["presented_font"]=="lishu")
        profiles=read(q/"inputs/army-catalog.json")["profiles"]
        for p in profiles:
            s=state();used={v["unit"] for v in s["army"]["slots"] if v["count"]}
            if len(used)==6:break
            if p["id"] in used or p["rank"]>s["army"]["recruit_rank"]:continue
            s=select(p["id"])
            if s["quote"]["maximum"]<1:continue
            n=s["transactions"];click(1520,1035);wait(lambda s,n=n:s["transactions"]==n+1)
        s=state();used={v["unit"] for v in s["army"]["slots"] if v["count"]};assert len(used)==6
        extra=next(p for p in profiles if p["id"] not in used and p["rank"]<=s["army"]["recruit_rank"])
        s=select(extra["id"]);assert s["quote"]["maximum"]==0 and s["quote"]["reason"]=="slots"
        full=s["army"];saved=s["session_sha256"];click(1510,1035);s=wait(lambda s:"六隊已滿" in s["message"]);assert s["army"]==full and s["session_sha256"]==saved
        final=snapshot("six-stacks-lishu");stop()
        start("cold");cold=wait(lambda s:s["font_id"]=="lishu" and s["presented_font"]=="lishu");assert cold["army"]==full and cold["session_sha256"]==saved
        snapshot("restored-lishu");stop()
        assert sha(q/"session-r1/gamedata.ay")==sha(q/"inputs/original-save.ay")
        write(out/"receipt.json",dict(status="passed-real-x11-army-ui",guest_instructions=0,held_mouse_single_purchase=True,over_quantity_rejected=True,seventh_stack_rejected=True,cold_army_equal=True,font_preference_restored=True,
             initial_army=initial["army"],final_army=full,final_session_sha256=saved,screens=screens,transactions=final["transactions"],player_world_path=False))
        print("Actual Go UI: held click, over-limit, six slots, three fonts and cold GUI load passed")
    finally:
        for child in reversed(children):
            if child.poll() is None:
                with contextlib.suppress(ProcessLookupError):os.killpg(child.pid,signal.SIGTERM)
                try:child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    with contextlib.suppress(ProcessLookupError):os.killpg(child.pid,signal.SIGKILL)
                    child.wait()
        for stream in streams:stream.close()


if __name__=="__main__":main()
