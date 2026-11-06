#!/usr/bin/env python3
"""特殊地點上岸、原式商店與冷讀抽樣。限Docker。"""
import ctypes as C
import hashlib,json,os,shutil,subprocess,time
from pathlib import Path
def main():
 assert Path('/.dockerenv').exists()and os.getuid()==1000
 r=Path('/native');base=r/'gui';base.mkdir();runs=[];app=None;log=None
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
  for name in ['treasure','cold-treasure','shop','cold-shop','exit','cold-exit','camp']:
   d=base/name;d.mkdir();store=base/(name+'-store');store.mkdir();log=(d/'player.log').open('w');cmd=[str(r/'8sword-remake'),'--journey','--assets',str(r/'pack'),'--capture-dir',str(d),'--scale','1','--save-dir',str(store),'--continue']
   src=base/'pending-treasure.chk'if name=='cold-treasure'else base/'pending-shop.chk'if name=='cold-shop'else base/'exit-store/journey.chk'if name=='cold-exit'else r/('fixture-'+name)/'journey.chk'
   shutil.copy2(src,store/'journey.chk');app=subprocess.Popen(cmd,stdout=log,stderr=log);inputs=[];captures=[]
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
   def click(px,py):
    inputs.append(dict(mouse=[px,py],before=state()));xt.XTestFakeMotionEvent(display,-1,ox.value+px,oy.value+py,0);xt.XTestFakeButtonEvent(display,1,1,0);x.XFlush(display);time.sleep(.04);xt.XTestFakeButtonEvent(display,1,0,0);x.XFlush(display);time.sleep(.10)
   def key(symbol,pause=.16):
    code=x.XKeysymToKeycode(display,symbol);assert code;inputs.append(dict(key=symbol,before=state()));xt.XTestFakeKeyEvent(display,code,1,0);x.XFlush(display);time.sleep(.04);xt.XTestFakeKeyEvent(display,code,0,0);x.XFlush(display);time.sleep(pause)
   def capture(label):
    old=int(state()['captures']);key(0xffc9);s=wait(lambda s:int(s['captures'])>old);num=int(s['captures']);cap=dict(line.split('\t',1)for line in(d/f'capture-{num:03}.tsv').read_text().splitlines());assert cap['readback_equal']=='true';captures.append(dict(label=label,number=num,captured=cap));return cap
   def save():
    old=state()['saves'];click(1644,1296);wait(lambda s:s['saves']!=old);assert(store/'journey.chk').read_bytes()[:8]==b'8SJRN011'
   mode=name.removeprefix('cold-');meta=dict(l.split('\t',1)for l in(r/('fixture-'+mode)/'fixture.tsv').read_text().splitlines())
   def approach():
    before=state();key(int(meta['key']));wait(lambda s:s['phase']=='shore');assert state()['x']==meta['x']and state()['y']==meta['y'];return before
   if name=='treasure':
    approach();anchor_treasure=capture('shore');save();shutil.copy2(store/'journey.chk',base/'pending-treasure.chk')
   elif name=='cold-treasure':
    cap=capture('cold-shore');assert cap['state_hash']==anchor_treasure['state_hash']and cap['frame_hash']==anchor_treasure['frame_hash'];before=state();key(0xff1b);wait(lambda s:s['phase']=='world');assert all(state()[k]==before[k]for k in ['x','y','gold','steps','army']);capture('refused');approach();click(230,1296);wait(lambda s:s['phase']=='treasure');capture('chest');before=state();key(0xff0d);wait(lambda s:s['phase']=='world');assert int(state()['gold'])==int(before['gold'])+int(meta['amount'])and int(state()['steps'])==int(before['steps'])-1 and state()['boat']=='0';capture('earned');save()
   elif name=='shop':
    before=approach();key(0xff1b);wait(lambda s:s['phase']=='magic-shop');assert state()['x']==meta['x']and state()['y']==meta['y']and state()['boat']=='2'and state()['gold']==before['gold'];anchor_shop=capture('default-bridge');save();shutil.copy2(store/'journey.chk',base/'pending-shop.chk')
   elif name=='cold-shop':
    cap=capture('cold-shop');assert cap['state_hash']==anchor_shop['state_hash']and cap['frame_hash']==anchor_shop['frame_hash'];before=state();charges=json.loads(before['magic_charges']);click(230,1296);wait(lambda s:int(s['gold'])==int(before['gold'])-10);assert json.loads(state()['magic_charges'])[0]==charges[0]+1;capture('bought');key(0xff1b);wait(lambda s:s['phase']=='world');assert state()['boat']=='2'and state()['x']==meta['x']and state()['y']==meta['y']and state()['steps']==before['steps'];capture('returned');save()
   elif name=='exit':
    before=approach();key(0xff1b);wait(lambda s:s['phase']=='world'and s['area']=='2');assert state()['x']=='16'and state()['y']=='5'and state()['boat']=='2'and state()['steps']==before['steps']and state()['gold']==before['gold'];anchor_exit=capture('crossed');save()
   elif name=='cold-exit':
    cap=capture('cold-exit');assert cap['state_hash']==anchor_exit['state_hash']and cap['frame_hash']==anchor_exit['frame_hash'];before=state();key(0xff53);wait(lambda s:s['phase']=='shore');click(230,1296);wait(lambda s:s['phase']=='world');assert state()['boat']=='0'and int(state()['steps'])==int(before['steps'])-1;capture('landed');key(0xffbf);wait(lambda s:s['phase']=='review');capture('army');key(0xff1b);wait(lambda s:s['phase']=='world');save()
   else:
    before=approach();click(230,1296);wait(lambda s:s['phase']=='camp');capture('camp');key(0xff1b);wait(lambda s:s['phase']=='world');assert state()['boat']=='0'and int(state()['steps'])==int(before['steps'])-1 and state()['gold']==before['gold'];capture('returned');save()
   final=state();event=Event();event.client.type=33;event.client.display=display;event.client.window=window;event.client.message=x.XInternAtom(display,b'WM_PROTOCOLS',0);event.client.format=32;event.client.data.l[0]=x.XInternAtom(display,b'WM_DELETE_WINDOW',0);x.XSendEvent(display,window,0,0,C.byref(event));x.XFlush(display);code=app.wait(timeout=10);assert code==0;log.close();log=None;runs.append(dict(name=name,exit=code,command=cmd,inputs=inputs,captures=captures,final=final));app=None
  (base/'receipt.json').write_text(json.dumps(dict(status='passed-rust-special-shore-gui',binary_sha256=hashlib.sha256((r/'8sword-remake').read_bytes()).hexdigest(),runs=runs,source='Previous real v10 army/resources/magic; controlled actual water positions,boat2,seed1. Subsequent keyboard/mouse only; no runtime memory or IP injection',controlled_initial_progress=True,no_runtime_memory_or_ip_injection=True),ensure_ascii=False,indent=2)+'\n')
 finally:
  if app and app.poll()is None:app.terminate();app.wait(timeout=5)
  if log:log.close()
  xvfb.terminate();xvfb.wait(timeout=5)
if __name__=='__main__':main()
