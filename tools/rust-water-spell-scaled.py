#!/usr/bin/env python3
"""涉水待上岸與拒絕的預設縮放滑鼠抽驗。"""
import ctypes as C
import hashlib,json,os,shutil,subprocess,time
from pathlib import Path

def main():
 assert Path('/.dockerenv').exists() and os.getuid()==1000
 r=Path('/out/native');base=r/'gui';runs=[];app=None;log=None
 os.environ.update(DISPLAY=':98',SDL_AUDIODRIVER='dummy',SDL_RENDER_DRIVER='software')
 xvfb=subprocess.Popen(['Xvfb',':98','-screen','0','2000x1400x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  time.sleep(.4);x=C.CDLL('libX11.so.6');xt=C.CDLL('libXtst.so.6');x.XOpenDisplay.argtypes=[C.c_char_p];x.XOpenDisplay.restype=C.c_void_p;display=x.XOpenDisplay(None);assert display
  x.XDefaultRootWindow.argtypes=[C.c_void_p];x.XDefaultRootWindow.restype=C.c_ulong;root=x.XDefaultRootWindow(display)
  x.XQueryTree.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_ulong),C.POINTER(C.c_ulong),C.POINTER(C.POINTER(C.c_ulong)),C.POINTER(C.c_uint)];x.XFetchName.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_char_p)];x.XFree.argtypes=[C.c_void_p];x.XSetInputFocus.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_ulong];x.XFlush.argtypes=[C.c_void_p];x.XKeysymToKeycode.argtypes=[C.c_void_p,C.c_ulong];x.XKeysymToKeycode.restype=C.c_uint;xt.XTestFakeKeyEvent.argtypes=[C.c_void_p,C.c_uint,C.c_int,C.c_ulong]
  x.XTranslateCoordinates.argtypes=[C.c_void_p,C.c_ulong,C.c_ulong,C.c_int,C.c_int,C.POINTER(C.c_int),C.POINTER(C.c_int),C.POINTER(C.c_ulong)];xt.XTestFakeMotionEvent.argtypes=[C.c_void_p,C.c_int,C.c_int,C.c_int,C.c_ulong];xt.XTestFakeButtonEvent.argtypes=[C.c_void_p,C.c_uint,C.c_int,C.c_ulong]
  x.XInternAtom.argtypes=[C.c_void_p,C.c_char_p,C.c_int];x.XInternAtom.restype=C.c_ulong;x.XSendEvent.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_long,C.c_void_p]
  class Data(C.Union):_fields_=[('b',C.c_char*20),('s',C.c_short*10),('l',C.c_long*5)]
  class Client(C.Structure):_fields_=[('type',C.c_int),('serial',C.c_ulong),('send',C.c_int),('display',C.c_void_p),('window',C.c_ulong),('message',C.c_ulong),('format',C.c_int),('data',Data)]
  class Event(C.Union):_fields_=[('client',Client),('pad',C.c_long*24)]
  d=r/'scaled';d.mkdir();store=d/'saves';store.mkdir();shutil.copy2(base/'pending-store/journey.chk',store/'journey.chk');log=(d/'player.log').open('w');cmd=[str(r/'8sword-remake'),'--journey','--assets',str(r/'pack'),'--save-dir',str(store),'--continue','--scale','0.6666666666666666'];app=subprocess.Popen(cmd,stdout=log,stderr=log);time.sleep(1)
  deadline=time.monotonic()+15;found=[];stable=0;last=[]
  while stable<8 and time.monotonic()<deadline:
   rr=C.c_ulong();parent=C.c_ulong();children=C.POINTER(C.c_ulong)();n=C.c_uint();assert x.XQueryTree(display,root,C.byref(rr),C.byref(parent),C.byref(children),C.byref(n));found=[]
   for i in range(n.value):
    title=C.c_char_p()
    if x.XFetchName(display,children[i],C.byref(title))and title.value:
     if b'Rust'in title.value:found.append(children[i])
     x.XFree(title)
   x.XFree(children)
   assert app.poll()is None
   stable=stable+1 if len(found)==1 and found==last else 0
   last=found[:]
   time.sleep(.1)
  assert len(found)==1;window=found[0];x.XSetInputFocus(display,window,1,0);x.XFlush(display);ox=C.c_int();oy=C.c_int();child=C.c_ulong();assert x.XTranslateCoordinates(display,window,root,0,0,C.byref(ox),C.byref(oy),C.byref(child))
  def grab(label):
   subprocess.run(['ffmpeg','-v','error','-f','x11grab','-video_size','1280x880','-i',f':98+{ox.value},{oy.value}','-frames:v','1',str(d/(label+'.png'))],check=True,timeout=15)
  def click(px,py):
   xt.XTestFakeMotionEvent(display,-1,ox.value+px,oy.value+py,0);xt.XTestFakeButtonEvent(display,1,1,0);x.XFlush(display);time.sleep(.05);xt.XTestFakeButtonEvent(display,1,0,0);x.XFlush(display);time.sleep(.3)
  grab('pending');click(461,864);grab('returned');click(1096,864)
  expected=(base/'refused.chk').read_bytes();time.sleep(.3);assert(store/'journey.chk').read_bytes()==expected;
  event=Event();event.client.type=33;event.client.display=display;event.client.window=window;event.client.message=x.XInternAtom(display,b'WM_PROTOCOLS',0);event.client.format=32;event.client.data.l[0]=x.XInternAtom(display,b'WM_DELETE_WINDOW',0);x.XSendEvent(display,window,0,0,C.byref(event));x.XFlush(display);assert app.wait(timeout=10)==0;app=None;log.close();log=None;(d/'receipt.json').write_text(json.dumps(dict(status='passed-scaled-water-spell-mouse',scale='2/3',pixels=[1280,880],same_returned_checkpoint=True,screens={n:hashlib.sha256((d/(n+'.png')).read_bytes()).hexdigest()for n in ['pending','returned']},binary_sha256=hashlib.sha256((r/'8sword-remake').read_bytes()).hexdigest(),capture='External X11; not native SDL readback'),indent=2)+'\n')
 finally:
  if app and app.poll()is None:app.terminate();app.wait(timeout=5)
  if log:log.close()
  xvfb.terminate();xvfb.wait(timeout=5)
if __name__=='__main__':main()
