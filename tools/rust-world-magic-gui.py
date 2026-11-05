#!/usr/bin/env python3
"""世界法術正常走路、尋寶、購買、施法及冷讀。"""
import ctypes as C
import hashlib,json,os,shutil,subprocess,time
from pathlib import Path

def main():
 assert Path('/.dockerenv').exists() and os.getuid()==1000
 r=Path('/out/native');base=r/'gui';base.mkdir();runs=[];app=None;log=None
 os.environ.update(DISPLAY=':97',SDL_AUDIODRIVER='dummy',SDL_RENDER_DRIVER='software')
 xvfb=subprocess.Popen(['Xvfb',':97','-screen','0','2000x1400x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  time.sleep(.4);x=C.CDLL('libX11.so.6');xt=C.CDLL('libXtst.so.6');x.XOpenDisplay.argtypes=[C.c_char_p];x.XOpenDisplay.restype=C.c_void_p;display=x.XOpenDisplay(None);assert display
  x.XDefaultRootWindow.argtypes=[C.c_void_p];x.XDefaultRootWindow.restype=C.c_ulong;root=x.XDefaultRootWindow(display)
  x.XQueryTree.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_ulong),C.POINTER(C.c_ulong),C.POINTER(C.POINTER(C.c_ulong)),C.POINTER(C.c_uint)];x.XFetchName.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_char_p)];x.XFree.argtypes=[C.c_void_p];x.XSetInputFocus.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_ulong];x.XFlush.argtypes=[C.c_void_p];x.XKeysymToKeycode.argtypes=[C.c_void_p,C.c_ulong];x.XKeysymToKeycode.restype=C.c_uint;xt.XTestFakeKeyEvent.argtypes=[C.c_void_p,C.c_uint,C.c_int,C.c_ulong]
  x.XTranslateCoordinates.argtypes=[C.c_void_p,C.c_ulong,C.c_ulong,C.c_int,C.c_int,C.POINTER(C.c_int),C.POINTER(C.c_int),C.POINTER(C.c_ulong)];xt.XTestFakeMotionEvent.argtypes=[C.c_void_p,C.c_int,C.c_int,C.c_int,C.c_ulong];xt.XTestFakeButtonEvent.argtypes=[C.c_void_p,C.c_uint,C.c_int,C.c_ulong]
  x.XInternAtom.argtypes=[C.c_void_p,C.c_char_p,C.c_int];x.XInternAtom.restype=C.c_ulong;x.XSendEvent.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_long,C.c_void_p]
  class Data(C.Union):_fields_=[('b',C.c_char*20),('s',C.c_short*10),('l',C.c_long*5)]
  class Client(C.Structure):_fields_=[('type',C.c_int),('serial',C.c_ulong),('send',C.c_int),('display',C.c_void_p),('window',C.c_ulong),('message',C.c_ulong),('format',C.c_int),('data',Data)]
  class Event(C.Union):_fields_=[('client',Client),('pad',C.c_long*24)]
  for name in ['fresh','pending','cold','legacy']:
   d=base/name;d.mkdir();store=base/(name+'-store');store.mkdir();log=(d/'player.log').open('w');cmd=[str(r/'8sword-remake'),'--journey','--assets',str(r/'pack'),'--capture-dir',str(d),'--scale','1','--save-dir',str(store)]
   if name=='fresh':cmd+=['--seed','1']
   else:
    src=r/'legacy-v4.chk' if name=='legacy' else base/('fresh-store/journey.chk' if name=='pending' else 'pending-store/journey.chk')
    shutil.copy2(src,store/'journey.chk');cmd+=['--continue']
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
   wait(lambda s:'state_hash'in s);rr=C.c_ulong();parent=C.c_ulong();children=C.POINTER(C.c_ulong)();n=C.c_uint();assert x.XQueryTree(display,root,C.byref(rr),C.byref(parent),C.byref(children),C.byref(n));found=[]
   for i in range(n.value):
    title=C.c_char_p()
    if x.XFetchName(display,children[i],C.byref(title))and title.value:
     if b'Rust'in title.value:found.append(children[i])
     x.XFree(title)
   x.XFree(children);assert len(found)==1;window=found[0];x.XSetInputFocus(display,window,1,0);x.XFlush(display)
   ox=C.c_int();oy=C.c_int();child=C.c_ulong();assert x.XTranslateCoordinates(display,window,root,0,0,C.byref(ox),C.byref(oy),C.byref(child))
   def move(px,py):xt.XTestFakeMotionEvent(display,-1,ox.value+px,oy.value+py,0);x.XFlush(display)
   def click(px,py,end=None):
    inputs.append(dict(mouse=[px,py],release=list(end or (px,py)),before=state()));move(px,py);xt.XTestFakeButtonEvent(display,1,1,0);x.XFlush(display);time.sleep(.04)
    if end:move(*end)
    xt.XTestFakeButtonEvent(display,1,0,0);x.XFlush(display);time.sleep(.10)
   def key(symbol):
    code=x.XKeysymToKeycode(display,symbol);assert code;inputs.append(dict(diagnostic_key=symbol));xt.XTestFakeKeyEvent(display,code,1,0);x.XFlush(display);time.sleep(.04);xt.XTestFakeKeyEvent(display,code,0,0);x.XFlush(display);time.sleep(.16)
   def capture(label):
    old=int(state()['captures']);key(0xffc9);s=wait(lambda s:int(s['captures'])>old);n=int(s['captures']);cap=dict(line.split('\t',1)for line in(d/f'capture-{n:03}.tsv').read_text().splitlines());assert cap['readback_equal']=='true';captures.append(dict(label=label,number=n,captured=cap));return cap
   def save():
    old=state()['saves'];click(1644,1296);wait(lambda s:s['saves']!=old);assert(store/'journey.chk').read_bytes()[:8]==b'8SJRN005'
   def phased(label,light):
    for attempt in range(8):
     wait(lambda s:s['minimap_light']==str(light).lower());cap=capture(label+'-phase-probe')
     if cap['minimap_light']==str(light).lower():
      captures[-1]['label']=label;return cap
    raise AssertionError(('capture phase unavailable',label,light))
   def resolve():
    for attempt in range(8):
     st=state()
     if st['phase'] in ['world','magic-shop']:return
     if st['phase']=='prompt':
      click(750,900);key(0xff0d);wait(lambda s:s['phase']!='prompt')
     elif st['phase']=='battle':
      if st['outcome']=='None':key(0xff1b);wait(lambda s:s['outcome']!='None')
      time.sleep(.2);key(0xff0d);wait(lambda s:s['phase']!='battle')
     else:raise AssertionError(('unexpected phase',st))
    raise AssertionError('encounter loop')
   def travel(route):
    for step in route:
     resolve();old=state()['actions'];key(step['key']);wait(lambda s:s['actions']!=old or s['phase']=='magic-shop');st=state();assert [int(st['x']),int(st['y'])]==step['to'],step
    resolve()
   route=json.loads((r/'route.json').read_text())
   if name=='fresh':
    assert state()['magic_book']=='false' and state()['resources']=='1,0,100,500,100,0'
    click(1640,680);wait(lambda s:s['phase']=='message');assert state()['message']=='你不會使用法術';key(0xff1b);wait(lambda s:s["phase"]=="world")
    travel(route['book']);before=state();click(1640,1010);wait(lambda s:s['phase']=='message');assert state()['magic_book']=='true' and state()['resources'].endswith(',3');assert state()['steps']==before['steps'] and state()['seed']==before['seed'];capture('book');key(0xff0d);wait(lambda s:s["phase"]=="world")
    key(0xffbe);wait(lambda s:s['phase']=='character');capture('character-book');click(450,20);wait(lambda s:s['font']=='1');key(0xff1b);wait(lambda s:s["phase"]=="world")
    before=state()['state_hash'];key(0xffc3);wait(lambda s:s['phase']=='message');assert state()['message']=='這裡沒有寶物' and state()['state_hash']==before;key(0xff1b);wait(lambda s:s["phase"]=="world")
    travel(route['shop']);assert state()['phase']=='magic-shop';before=int(state()['gold'])
    for i in range(3):
     click(230,1296);wait(lambda s:s['magic_charges'].startswith('['+str(i+1)+','));assert int(state()['gold'])==before-10*(i+1)
    click(230,1296);wait(lambda s:s['message']=='法術容量已滿');capture('shop');click(690,1296);wait(lambda s:s['phase']!='magic-shop');resolve()
    travel(route['shore']);assert [int(state()['x']),int(state()['y'])]==route['shore_position']
    click(1640,680);wait(lambda s:s['phase']=='magic-menu');capture('menu');before=state()['state_hash'];key(0xff52);wait(lambda s:s["selected"]=="7");assert state()['selected']=='7' and state()['state_hash']==before;key(0xff54);wait(lambda s:s["selected"]=="0")
    click(230,1296);wait(lambda s:s['phase']=='bridge-direction');assert state()['magic_charges']=='[2, 0, 0, 0, 0, 0, 0, 0]';before=state()['state_hash'];key(0xff1b);assert state()['phase']=='bridge-direction' and state()['state_hash']==before;capture('pending');save();pending_anchor=state()['state_hash']
   elif name=='pending':
    assert state()['phase']=='bridge-direction' and state()['state_hash']==pending_anchor
    key(route['cast_key']);wait(lambda s:s['phase']=='world');assert state()['magic_charges']=='[2, 0, 0, 0, 0, 0, 0, 0]' and state()['magic_bridges']!='[]';capture('cast-color');time.sleep(1.3)
    travel([dict(key=route['cast_key'],to=route['near'])]);capture('bridge');save();bridge_anchor=state()['magic_bridges'];world_anchor=state()['state_hash']
    key(0xffbe);wait(lambda s:s['phase']=='character');anchor=capture('anchor')
   elif name=='cold':
    assert state()['phase']=='world' and state()['state_hash']==world_anchor and state()['magic_bridges']==bridge_anchor
    key(0xffbe);wait(lambda s:s['phase']=='character');cap=capture('cold');assert cap['frame_hash']==anchor['frame_hash'];key(0xff1b);wait(lambda s:s["phase"]=="world")
    click(1640,680);wait(lambda s:s['phase']=='magic-menu');click(708,20);wait(lambda s:s['font']=='2');capture('caoshu');key(0xff1b);save()
   else:
    assert state()['phase']=='world' and state()['magic_book']=='false' and state()['magic_bridges']=='[]';key(0xffc1);wait(lambda s:s['phase']=='message');assert state()['message']=='你不會使用法術';capture('legacy');save();assert (store/'journey.chk').read_bytes()[:8]==b'8SJRN005'
   final=state();event=Event();event.client.type=33;event.client.display=display;event.client.window=window;event.client.message=x.XInternAtom(display,b'WM_PROTOCOLS',0);event.client.format=32;event.client.data.l[0]=x.XInternAtom(display,b'WM_DELETE_WINDOW',0);x.XSendEvent(display,window,0,0,C.byref(event));x.XFlush(display);code=app.wait(timeout=10);assert code==0;log.close();log=None;runs.append(dict(name=name,exit=code,command=cmd,inputs=inputs,captures=captures,final=final));app=None
  (base/'receipt.json').write_text(json.dumps(dict(status='passed-rust-world-magic-gui',binary_sha256=hashlib.sha256((r/'8sword-remake').read_bytes()).hexdigest(),runs=runs,fixed_seed=1,gameplay_input='XTest normal world path, F6/F4, mouse purchases and original movement; F12 diagnostic capture',no_memory_or_ip_injection=True),ensure_ascii=False,indent=2)+'\n')
 finally:
  if app and app.poll()is None:app.terminate();app.wait(timeout=5)
  if log:log.close()
  xvfb.terminate();xvfb.wait(timeout=5)
if __name__=='__main__':main()
