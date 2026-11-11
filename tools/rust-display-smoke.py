#!/usr/bin/env python3
"""Rust策略AI切換、選敵與冷讀抽驗。限Docker。"""
import ctypes as C
import hashlib,json,os,shutil,subprocess,time
from pathlib import Path
def main():
 assert Path('/.dockerenv').exists()and os.getuid()==1000
 r=Path('/native');base=r/'default-gui';base.mkdir();runs=[];app=None;log=None
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

  for name in ['current','legacy']:
   store=base/(name+'-store');store.mkdir()
   for p in(r/'fixture').iterdir():shutil.copy2(p,store/p.name)
   media=r/'pack' if name=='current' else r/'cli-check/old-pack'
   cmd=[str(r/'8sword-remake'),'--battle','--assets',str(media),'--save-dir',str(store),'--continue','--mute'];log=(base/(name+'.log')).open('w');app=subprocess.Popen(cmd,stdout=log,stderr=log)
   def wait(pred):
    end=time.monotonic()+15
    while time.monotonic()<end:
     assert app.poll()is None,(name,app.returncode,(base/(name+'.log')).read_text())
     if pred():return
     time.sleep(.03)
    raise AssertionError((name,'timeout'))
   def windows():
    rr=C.c_ulong();parent=C.c_ulong();children=C.POINTER(C.c_ulong)();n=C.c_uint();assert x.XQueryTree(display,root,C.byref(rr),C.byref(parent),C.byref(children),C.byref(n));found=[]
    for i in range(n.value):
     title=C.c_char_p()
     if x.XFetchName(display,children[i],C.byref(title))and title.value:
      if b'Rust'in title.value:found.append(children[i])
      x.XFree(title)
    x.XFree(children);return found
   wait(lambda:len(windows())==1);window=windows()[0];x.XSetInputFocus(display,window,1,0);x.XFlush(display);time.sleep(.7)
   x.XGetGeometry.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_ulong),C.POINTER(C.c_int),C.POINTER(C.c_int),C.POINTER(C.c_uint),C.POINTER(C.c_uint),C.POINTER(C.c_uint),C.POINTER(C.c_uint)]
   wr=C.c_ulong();gx=C.c_int();gy=C.c_int();ww=C.c_uint();hh=C.c_uint();bw=C.c_uint();depth=C.c_uint();assert x.XGetGeometry(display,window,C.byref(wr),C.byref(gx),C.byref(gy),C.byref(ww),C.byref(hh),C.byref(bw),C.byref(depth));assert(ww.value,hh.value)==(1962,880),(ww.value,hh.value)
   ox=C.c_int();oy=C.c_int();child=C.c_ulong();assert x.XTranslateCoordinates(display,window,root,0,0,C.byref(ox),C.byref(oy),C.byref(child))
   def key(symbol):
    code=x.XKeysymToKeycode(display,symbol);xt.XTestFakeKeyEvent(display,code,1,0);x.XFlush(display);time.sleep(.04);xt.XTestFakeKeyEvent(display,code,0,0);x.XFlush(display);time.sleep(.20)
   def click():
    xt.XTestFakeMotionEvent(display,-1,ox.value+round(2600*ww.value/2944),oy.value+round(1296*hh.value/1320),0);xt.XTestFakeButtonEvent(display,1,1,0);x.XFlush(display);time.sleep(.04);xt.XTestFakeButtonEvent(display,1,0,0);x.XFlush(display);time.sleep(.20)
   path=store/'battle.chk';old_time=path.stat().st_mtime_ns;key(0xffc4);wait(lambda:path.stat().st_mtime_ns!=old_time);before=path.read_bytes();click()
   if name=='current':
    wait(lambda:(store/'display.json').exists());assert json.loads((store/'display.json').read_text())['mode']=='original';assert path.read_bytes()==before;click();wait(lambda:json.loads((store/'display.json').read_text())['mode']=='hd');assert path.read_bytes()==before
   else:assert not(store/'display.json').exists()
   old_time=path.stat().st_mtime_ns;key(0xffc4);wait(lambda:path.stat().st_mtime_ns!=old_time);assert path.read_bytes()==before
   event=Event();event.client.type=33;event.client.display=display;event.client.window=window;event.client.message=x.XInternAtom(display,b'WM_PROTOCOLS',0);event.client.format=32;event.client.data.l[0]=x.XInternAtom(display,b'WM_DELETE_WINDOW',0);x.XSendEvent(display,window,0,0,C.byref(event));x.XFlush(display);code=app.wait(timeout=10);assert code==0;app=None;log.close();log=None;runs.append(dict(name=name,command=cmd,exit=code,window=[ww.value,hh.value],same_checkpoint_sha256=hashlib.sha256(before).hexdigest(),legacy_no_original_group=name=='legacy'))
  (base/'receipt.json').write_text(json.dumps(dict(status='passed-rust-display-default-scale',runs=runs,scope='Default 2/3 actual window; current group toggles original/HD and persists; legacy34-glyph HD-only pack stays HD; F7 bytes unchanged by presentation; no default-scale pixel readback claim.'),ensure_ascii=False,indent=2)+'\n')
 finally:
  if app and app.poll()is None:app.terminate();app.wait(timeout=5)
  if log:log.close()
  xvfb.terminate();xvfb.wait(timeout=5)
if __name__=='__main__':main()
