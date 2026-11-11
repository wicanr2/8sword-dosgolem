#!/usr/bin/env python3
"""原行程條跨格、停時、月結與冷讀抽驗。限Docker。"""
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
  for name in ["play","world","cold","battle","ending","bad-panel"]:
   d=base/name;d.mkdir();store=base/(name+"-store");store.mkdir();log=(d/"player.log").open("w")
   mode="--play"if name=="play"else "--battle"if name=="battle"else "--journey"
   pack=r/"pack"
   if name=="bad-panel":pack=r/"bad-pack"
   cmd=[str(r/"8sword-remake"),mode,"--assets",str(pack),"--capture-dir",str(d),"--scale","1","--save-dir",str(store)]
   if name=="battle":cmd += ["--seed","1"]
   else:
    src=r/"ending-v15.chk"if name=="ending"else base/"world-store/journey.chk"if name=="cold"else r/"legacy-v16.chk"
    shutil.copy2(src,store/"journey.chk")
    if name=="cold":shutil.copy2(base/"world-store/poster.json",store/"poster.json")
    if name!="play":cmd += ["--continue"]
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
    old=int(state()['captures']);key(0xffc9);s=wait(lambda s:int(s['captures'])>old);num=int(s['captures']);cap=dict(line.split('\t',1)for line in(d/f'capture-{num:03}.tsv').read_text().splitlines());assert state()['readback_equal']=='true';assert(d/f'frame-{num:03}.ppm').read_bytes()==(d/f'readback-{num:03}.ppm').read_bytes();captures.append(dict(label=label,number=num,captured=cap));return cap
   def save():
    old=state()['saves'];click(1644,1296);wait(lambda s:s['saves']!=old);assert(store/'journey.chk').read_bytes()[:8]==b'8SJRN016'

   assert state()
   def poster(i):
    click(2600,20);click(2600,74+i*48);time.sleep(.55)
   def center(px,py):click(px+512,py)
   if name=="play":
    wait(lambda s:s['phase']=='intro');capture('intro');key(0xff1b);wait(lambda s:s['phase']=='start');poster(1);capture('menu-cover');key(0xff0d);wait(lambda s:s['phase']=='world');capture('world-cover')
    for symbol,phase,label in [(0xffbe,'character','character'),(0xffbf,'review','army'),(0xffc2,'minimap','minimap')]:
     key(symbol);wait(lambda s:s['phase']==phase);capture(label);key(0xff1b);wait(lambda s:s['phase']=='world')
   elif name=="world":
    wait(lambda s:s['phase']=='world');time.sleep(1.4);before=capture('wings')
    click(2600,20);key(0xff54);key(0xff54);key(0xff1b);assert all(state()[k]==before[k]for k in ['seed','steps','x','y']);capture('cancel')
    # Arrow/Enter changes only the poster preference, never world position.
    click(2600,20);key(0xff54);key(0xff0d);time.sleep(.55);capture('cover');assert all(state()[k]==before[k]for k in ['seed','steps','x','y'])
    center(480,20);wait(lambda s:s['font']=='1');capture('lishu');poster(2);capture('off');poster(1)
    old=state()['saves'];center(1644,1296);wait(lambda s:s['saves']!=old);capture('saved-cover')
   elif name=="cold":
    wait(lambda s:s['phase']=='world');assert state()['font']=='1';capture('cold-cover');assert json.loads((store/'poster.json').read_text())['poster']=='cover'
    old=int(state()['steps']);key(0xff53);wait(lambda s:int(s['steps'])==old-1);capture('moved')
   elif name=="battle":
    wait(lambda s:s.get('actor','') not in ['', '-1']);capture('battle-wings');poster(2);capture('battle-off')
   elif name=="ending":
    wait(lambda s:s['phase']=='ending');poster(1);capture('ending-cover');center(708,20);wait(lambda s:s['font']=='2');capture('ending-caoshu')
   else:
    wait(lambda s:s['phase']=='world');capture('bad-panel');old=int(state()['steps']);key(0xff53);wait(lambda s:int(s['steps'])==old-1);capture('fallback-moved')
   final=state();event=Event();event.client.type=33;event.client.display=display;event.client.window=window;event.client.message=x.XInternAtom(display,b'WM_PROTOCOLS',0);event.client.format=32;event.client.data.l[0]=x.XInternAtom(display,b'WM_DELETE_WINDOW',0);x.XSendEvent(display,window,0,0,C.byref(event));x.XFlush(display);code=app.wait(timeout=10);assert code==0;log.close();log=None;runs.append(dict(name=name,exit=code,command=cmd,inputs=inputs,captures=captures,final=final));app=None
  (base/"receipt.json").write_text(json.dumps(dict(status="passed-rust-poster-gui",binary_sha256=hashlib.sha256((r/"8sword-remake").read_bytes()).hexdigest(),runs=runs,no_runtime_memory_or_ip_injection=True,scope="Genuine v16 world/Continue; normal UI operations, three posters, fonts, keyboard cancellation and persistence. Battle uses the established explicit sample/seed1. Ending reads genuine saved v15; no natural completion claim."),ensure_ascii=False,indent=2)+"\n")
 finally:
  if app and app.poll()is None:app.terminate();app.wait(timeout=5)
  if log:log.close()
  xvfb.terminate();xvfb.wait(timeout=5)
if __name__=='__main__':main()
