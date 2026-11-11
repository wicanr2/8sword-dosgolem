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

  anchor=None
  for name in ["native","target","cold-native","cold-target","journey","journey-cold","legacy"]:
   d=base/name;d.mkdir();store=base/(name+"-store");store.mkdir();log=(d/"player.log").open("w")
   mode="--play"if name=="journey"else "--journey"if name=="journey-cold"else "--battle"
   pack=r/"legacy-pack"if name=="legacy"else r/"pack"
   cmd=[str(r/"8sword-remake"),mode,"--assets",str(pack),"--capture-dir",str(d),"--scale","1","--save-dir",str(store)]
   if name=="journey":shutil.copy2(r/"legacy-v16.chk",store/"journey.chk");cmd += ["--skip-intro"]
   elif name=="journey-cold":shutil.copy2(base/"journey-ai.chk",store/"journey.chk");cmd += ["--continue"]
   else:
    src=base/"ai-battle.chk"if name.startswith("cold-")else r/"fixture/battle.chk";shutil.copy2(src,store/"battle.chk");cmd += ["--continue"]
   if name in ["cold-target","legacy"]:cmd += ["--battle-ai","target"]
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
   if name=="journey":
    wait(lambda s:s['phase']=='start');capture('start-native');mode(1);capture('start-target');key(0xff0d);wait(lambda s:s['phase']=='world');assert state()['battle_ai']=='target';capture('world-target')
    before=state();key(0xff53);wait(lambda s:s['actions']!=before['actions']or s['phase']=='prompt')
    for _ in range(324):
     if state()['phase']=='prompt':break
     assert state()['phase']=='world';old=state()['actions'];key(32,pause=.08);wait(lambda s:s['actions']!=old or s['phase']=='prompt')
    assert state()['phase']=='prompt';capture('natural-encounter');key(0xff0d);wait(lambda s:s['phase']=='battle');capture('natural-battle')
    for _ in range(32):
     if int(state()['ai_decisions'])>0:break
     wait(lambda s:s['actor']=='player'or s['outcome']!='None'or int(s['ai_decisions'])>0)
     if int(state()['ai_decisions'])>0:break
     assert state()['outcome']=='None';key(32,pause=.30)
    wait(lambda s:int(s['ai_decisions'])>0);wait(lambda s:s['actor']=='player'or s['outcome']!='None');time.sleep(1.3);capture('natural-ai-hit');old=state()['saves'];key(0xffc4);wait(lambda s:s['saves']!=old);time.sleep(1.3);world_anchor=capture('journey-saved');shutil.copy2(store/'journey.chk',base/'journey-ai.chk')
   elif name=="journey-cold":
    wait(lambda s:s['phase']=='battle');time.sleep(1.4);assert state()['battle_ai']=='native';cap=capture('journey-cold-native');assert cap['state_hash']==world_anchor['state_hash']and cap['frame_hash']==world_anchor['frame_hash']
   else:
    wait(lambda s:s['actor']=='player');time.sleep(1.4);initial=capture('before')
    if name=="target":
     before=state();click(2800,20);key(0xff54);key(0xff1b);assert state()['battle_ai']=='native'and state()['checkpoint_hash']==before['checkpoint_hash'];mode(1);capture('enabled');click(2800,20);key(0xff54);key(0xff0d);wait(lambda s:s['battle_ai']=='native');mode(1)
     key(0xffc7);wait(lambda s:s['font']=='lishu');assert state()['battle_ai']=='target';old=state()['saves'];key(0xffc4);wait(lambda s:s['saves']!=old);time.sleep(1.3);battle_anchor=capture('saved-target');shutil.copy2(store/'battle.chk',base/'ai-battle.chk')
    elif name.startswith('cold-'):
     assert initial['checkpoint_hash']==battle_anchor['checkpoint_hash']and initial['frame_hash']==battle_anchor['frame_hash'];assert state()['battle_ai']==('target'if name=='cold-target'else'native')
    after=first_enemy_hit();is_target=name in ['target','cold-target','legacy'];assert after['army']==('100,0,0,0,0,0'if is_target else'97,2,0,0,0,0'),after
    if is_target:assert after['ai_original_slot']=='0'and after['ai_selected_slot']=='1'and after['ai_changed']=='1'
    else:assert after['ai_decisions']=='0'
    capture('target-hit'if is_target else'native-hit')
    if name=='native':native_seed=after['seed']
    else:assert after['seed']==native_seed
    if name=='legacy':assert captures[-1]['shell']['ai_chinese']=='false'
   final=state();event=Event();event.client.type=33;event.client.display=display;event.client.window=window;event.client.message=x.XInternAtom(display,b'WM_PROTOCOLS',0);event.client.format=32;event.client.data.l[0]=x.XInternAtom(display,b'WM_DELETE_WINDOW',0);x.XSendEvent(display,window,0,0,C.byref(event));x.XFlush(display);code=app.wait(timeout=10);assert code==0;log.close();log=None;runs.append(dict(name=name,exit=code,command=cmd,inputs=inputs,captures=captures,final=final));app=None
  (base/"receipt.json").write_text(json.dumps(dict(status="passed-rust-ai-gui",binary_sha256=hashlib.sha256((r/"8sword-remake").read_bytes()).hexdigest(),runs=runs,no_runtime_memory_or_ip_injection=True,scope="True v16 Continue and normal movement/wait/encounter/battle/F7/cold; explicit battle fixture100 native06/2 native11 vs250 openkb arcr/seed1 is not natural acquisition. AI mode session-only; legacy font uses ASCII."),ensure_ascii=False,indent=2)+"\n")
 finally:
  if app and app.poll()is None:app.terminate();app.wait(timeout=5)
  if log:log.close()
  xvfb.terminate();xvfb.wait(timeout=5)
if __name__=='__main__':main()
