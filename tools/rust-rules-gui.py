#!/usr/bin/env python3
"""Rust策略AI切換、選敵與冷讀抽驗。限Docker。"""
import ctypes as C
import hashlib,json,os,shutil,subprocess,time
from pathlib import Path
def main():
 assert Path('/.dockerenv').exists()and os.getuid()==1000
 r=Path('/native');base=r/'gui';base.mkdir();runs=[];app=None;log=None
 os.environ.update(DISPLAY=':97',SDL_AUDIODRIVER='dummy',SDL_RENDER_DRIVER='software')
 xvfb=subprocess.Popen(['Xvfb',':97','-screen','0','3100x1450x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  time.sleep(.4);x=C.CDLL('libX11.so.6');xt=C.CDLL('libXtst.so.6');x.XOpenDisplay.argtypes=[C.c_char_p];x.XOpenDisplay.restype=C.c_void_p;display=x.XOpenDisplay(None);assert display
  x.XDefaultRootWindow.argtypes=[C.c_void_p];x.XDefaultRootWindow.restype=C.c_ulong;root=x.XDefaultRootWindow(display)
  x.XQueryTree.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_ulong),C.POINTER(C.c_ulong),C.POINTER(C.POINTER(C.c_ulong)),C.POINTER(C.c_uint)];x.XFetchName.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_char_p)];x.XFree.argtypes=[C.c_void_p];x.XSetInputFocus.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_ulong];x.XFlush.argtypes=[C.c_void_p];x.XKeysymToKeycode.argtypes=[C.c_void_p,C.c_ulong];x.XKeysymToKeycode.restype=C.c_uint;xt.XTestFakeKeyEvent.argtypes=[C.c_void_p,C.c_uint,C.c_int,C.c_ulong]
  x.XTranslateCoordinates.argtypes=[C.c_void_p,C.c_ulong,C.c_ulong,C.c_int,C.c_int,C.POINTER(C.c_int),C.POINTER(C.c_int),C.POINTER(C.c_ulong)];xt.XTestFakeMotionEvent.argtypes=[C.c_void_p,C.c_int,C.c_int,C.c_int,C.c_ulong];xt.XTestFakeButtonEvent.argtypes=[C.c_void_p,C.c_uint,C.c_int,C.c_ulong]
  x.XInternAtom.argtypes=[C.c_void_p,C.c_char_p,C.c_int];x.XInternAtom.restype=C.c_ulong;x.XSendEvent.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_long,C.c_void_p]
  class Data(C.Union):_fields_=[('b',C.c_char*20),('s',C.c_short*10),('l',C.c_long*5)]
  class Client(C.Structure):_fields_=[('type',C.c_int),('serial',C.c_ulong),('send',C.c_int),('display',C.c_void_p),('window',C.c_ulong),('message',C.c_ulong),('format',C.c_int),('data',Data)]
  class Event(C.Union):_fields_=[('client',Client),('pad',C.c_long*24)]

  world_anchor=None
  for name in os.environ.get("RUST_RULES_CASES","native,formation,tactics,battle-cold,journey,journey-cold,legacy").split(","):
   d=base/name;d.mkdir();store=base/(name+"-store");store.mkdir();log=(d/"player.log").open("w")
   journey=name in ["journey","journey-cold"]
   mode="--play" if name=="journey" else "--journey" if journey else "--battle"
   pack=r/"legacy-pack" if name=="legacy" else r/"pack"
   cmd=[str(r/"8sword-remake"),mode,"--assets",str(pack),"--capture-dir",str(d),"--scale","1","--save-dir",str(store)]
   if name=="journey":shutil.copy2(r/"legacy-v16.chk",store/"journey.chk");cmd += ["--skip-intro"]
   elif name=="journey-cold":
    for p in(base/"journey-store").glob("journey.chk*"):shutil.copy2(p,store/p.name)
    cmd += ["--continue"]
   else:
    src=base/"tactics-store" if name=="battle-cold" else r/"fixture"/("tactics" if name=="legacy" else name)
    for p in src.glob("battle.chk*"):shutil.copy2(p,store/p.name)
    cmd += ["--continue"]
   app=subprocess.Popen(cmd,stdout=log,stderr=log);inputs=[];captures=[]
   def state():
    assert app.poll()is None,(name,app.returncode,(d/'player.log').read_text())
    try:return dict(line.split('\t',1)for line in(d/'status.tsv').read_text().splitlines())
    except(FileNotFoundError,ValueError):return{}
   def wait(pred,seconds=20):
    until=time.monotonic()+seconds
    while time.monotonic()<until:
     s=state()
     if s and pred(s):return s
     time.sleep(.02)
    raise AssertionError((name,'timeout',state()))
   wait(lambda s:'state_hash'in s or 'checkpoint_hash'in s);rr=C.c_ulong();parent=C.c_ulong();children=C.POINTER(C.c_ulong)();n=C.c_uint();assert x.XQueryTree(display,root,C.byref(rr),C.byref(parent),C.byref(children),C.byref(n));found=[]
   for i in range(n.value):
    title=C.c_char_p()
    if x.XFetchName(display,children[i],C.byref(title))and title.value:
     if b'Rust'in title.value:found.append(children[i])
     x.XFree(title)
   x.XFree(children);assert len(found)==1;window=found[0];x.XSetInputFocus(display,window,1,0);x.XFlush(display)
   ox=C.c_int();oy=C.c_int();child=C.c_ulong();assert x.XTranslateCoordinates(display,window,root,0,0,C.byref(ox),C.byref(oy),C.byref(child))
   def click(px,py):
    inputs.append(dict(mouse=[px,py],before=state()));xt.XTestFakeMotionEvent(display,-1,ox.value+px,oy.value+py,0);xt.XTestFakeButtonEvent(display,1,1,0);x.XFlush(display);time.sleep(.04);xt.XTestFakeButtonEvent(display,1,0,0);x.XFlush(display);time.sleep(.10)
   def key(symbol,pause=.16):
    code=x.XKeysymToKeycode(display,symbol);assert code;inputs.append(dict(key=symbol,before=state()));xt.XTestFakeKeyEvent(display,code,1,0);x.XFlush(display);time.sleep(.04);xt.XTestFakeKeyEvent(display,code,0,0);x.XFlush(display);time.sleep(pause)
   def capture(label):
    old=int(state()['captures']);key(0xffc9);s=wait(lambda s:int(s['captures'])>old);num=int(s['captures']);cap=dict(line.split('\t',1)for line in(d/f'capture-{num:03}.tsv').read_text().splitlines());assert state()['readback_equal']=='true';assert(d/f'frame-{num:03}.ppm').read_bytes()==(d/f'readback-{num:03}.ppm').read_bytes();shell=dict(line.split('\t',1)for line in(d/f'shell-{num:03}.tsv').read_text().splitlines());captures.append(dict(label=label,number=num,captured=cap,shell=shell));return cap
   def save():
    old=state()['saves'];click(1644,1296);wait(lambda s:s['saves']!=old);assert(store/'journey.chk').read_bytes()[:8]==b'8SJRN016'

   assert state()
   def mode(i):
    click(2800,20);click(2600,74+i*48)
    if 'battle_ai'in state():wait(lambda s:s['battle_ai']==['native','target'][i])
   def center(px,py):click(px+512,py)
   def first_enemy_hit():
    for _ in range(16):
     if int(state()['sequence'])>=1:break
     wait(lambda s:s.get('actor')=='player'or int(s['sequence'])>=1)
     if int(state()['sequence'])>=1:break
     key(32,pause=.30)
    return wait(lambda s:int(s['sequence'])>=1)
   def rules(i):
    click(100,20);click(100,74+i*48);wait(lambda s:s['battle_rules']==['native','formation','tactics'][i])
   def save_key():
    old=state()['saves'];key(0xffc4);wait(lambda s:s['saves']!=old);time.sleep(1.4)
   if name=="journey":
    wait(lambda s:s['phase']=='start');capture('start-native');rules(1);capture('start-formation');key(0xff0d);wait(lambda s:s['phase']=='world');assert state()['battle_rules']=='formation';capture('continued-formation')
    rules(2);capture('world-tactics');rules(0);save_key();assert not(store/'journey.chk.rules.json').exists();capture('world-native');rules(1);save_key();marker=json.loads((store/'journey.chk.rules.json').read_text());assert marker['rules']=='formation'
    before=state();click(100,20);key(0xff54);key(0xff1b);assert state()['battle_rules']=='formation'and state()['state_hash']==before['state_hash']
    key(0xff53)
    for _ in range(324):
     if state()['phase']=='prompt':break
     assert state()['phase']=='world';old=state()['actions'];key(32,pause=.08);wait(lambda s:s['actions']!=old or s['phase']=='prompt')
    assert state()['phase']=='prompt';capture('natural-encounter');key(0xff0d);wait(lambda s:s['phase']=='battle');assert state()['rules_locked']=='true'
    before=state();click(100,20);assert state()['battle_rules']=='formation';mode(1);key(0xffc7);wait(lambda s:s['font'] in ['1','lishu']);assert state()['battle_rules']=='formation';capture('battle-locked-ai-lishu')
    for _ in range(32):
     if int(state()['ai_decisions'])>0:break
     wait(lambda s:s['actor']=='player'or s['outcome']!='None'or int(s['ai_decisions'])>0)
     if int(state()['ai_decisions'])>0:break
     assert state()['outcome']=='None';key(32,pause=.30)
    wait(lambda s:int(s['ai_decisions'])>0);wait(lambda s:s['actor']=='player'or s['outcome']!='None');time.sleep(1.4);save_key();world_anchor=capture('journey-saved');assert state()['battle_rules']=='formation'
   elif name=="journey-cold":
    wait(lambda s:s['phase']=='battle');time.sleep(1.4);assert state()['battle_rules']=='formation'and state()['rules_locked']=='true';cap=capture('cold-formation');assert cap['state_hash']==world_anchor['state_hash']and cap['frame_hash']==world_anchor['frame_hash']
   else:
    wait(lambda s:s['actor']=='player');time.sleep(1.4);initial=capture('before')
    wanted='tactics'if name in ['battle-cold','legacy']else name;assert state()['battle_rules']==wanted and state()['rules_locked']=='true'
    click(100,20);assert state()['battle_rules']==wanted
    after=first_enemy_hit();wait(lambda s:s['actor']=='player');time.sleep(1.4)
    expected='84,100,0,0,0,0'if name=='native'else'88,100,0,0,0,0';assert state()['army']==expected,state()
    capture('first-hit')
    if name=='tactics':save_key();battle_anchor=capture('tactics-saved')
    elif name=='battle-cold':
     assert initial['checkpoint_hash']==battle_anchor['checkpoint_hash']and initial['frame_hash']==battle_anchor['frame_hash']
    if name=='legacy':assert captures[-1]['shell']['rules_chinese']=='false'
   final=state();event=Event();event.client.type=33;event.client.display=display;event.client.window=window;event.client.message=x.XInternAtom(display,b'WM_PROTOCOLS',0);event.client.format=32;event.client.data.l[0]=x.XInternAtom(display,b'WM_DELETE_WINDOW',0);x.XSendEvent(display,window,0,0,C.byref(event));x.XFlush(display);code=app.wait(timeout=10);assert code==0;log.close();log=None;runs.append(dict(name=name,exit=code,command=cmd,inputs=inputs,captures=captures,final=final));app=None
   (base/'completed-runs.json').write_text(json.dumps(runs,ensure_ascii=False,indent=2)+'\n')
  (base/"receipt.json").write_text(json.dumps(dict(status="passed-rust-rules-gui",binary_sha256=hashlib.sha256((r/"8sword-remake").read_bytes()).hexdigest(),runs=runs,no_runtime_memory_or_ip_injection=True,scope="True v16 Continue / normal movement / natural encounter / F7 / cold; explicit 100 militia+100 native21 vs50 original archers seed1 tests rear archer damage. Front archer pressure is covered separately by both-side core tests. Mode hash sidecars; battle fixed; AI independent."),ensure_ascii=False,indent=2)+"\n")
 finally:
  if app and app.poll()is None:app.terminate();app.wait(timeout=5)
  if log:log.close()
  xvfb.terminate();xvfb.wait(timeout=5)
if __name__=='__main__':main()
