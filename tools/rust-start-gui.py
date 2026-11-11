#!/usr/bin/env python3
"""原式開始選單、新遊戲、音樂欣賞與獨立冷讀抽驗。限Docker。"""
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

  anchor=None
  for name in ['fresh','cold','legacy','corrupt','default']:
   d=base/name;d.mkdir();store=base/(name+'-store');store.mkdir();log=(d/'player.log').open('w');cmd=[str(r/'8sword-remake'),'--play','--assets',str(r/'pack'),'--capture-dir',str(d),'--scale','1','--save-dir',str(store)]
   if name=='fresh':cmd.extend(['--seed','1'])
   elif name=='cold':shutil.copy2(base/'fresh.chk',store/'journey.chk')
   elif name=='legacy':shutil.copy2(r/'legacy-v16.chk',store/'journey.chk')
   elif name=='corrupt':(store/'journey.chk').write_bytes(b'corrupt-checkpoint')
   else:
    os.environ['XDG_DATA_HOME']=str(base/'default-data');cmd=[str(r/'8sword-remake'),'--capture-dir',str(d),'--scale','1'];store=base/'default-data/8sword-remake'
   old=(store/'journey.chk').read_bytes()if(store/'journey.chk').exists()else None
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
   def click(px,py):
    inputs.append(dict(mouse=[px,py],before=state()));xt.XTestFakeMotionEvent(display,-1,ox.value+px,oy.value+py,0);xt.XTestFakeButtonEvent(display,1,1,0);x.XFlush(display);time.sleep(.04);xt.XTestFakeButtonEvent(display,1,0,0);x.XFlush(display);time.sleep(.10)
   def key(symbol,pause=.16):
    code=x.XKeysymToKeycode(display,symbol);assert code;inputs.append(dict(key=symbol,before=state()));xt.XTestFakeKeyEvent(display,code,1,0);x.XFlush(display);time.sleep(.04);xt.XTestFakeKeyEvent(display,code,0,0);x.XFlush(display);time.sleep(pause)
   def capture(label):
    old=int(state()['captures']);key(0xffc9);s=wait(lambda s:int(s['captures'])>old);num=int(s['captures']);cap=dict(line.split('\t',1)for line in(d/f'capture-{num:03}.tsv').read_text().splitlines());assert cap['readback_equal']=='true';captures.append(dict(label=label,number=num,captured=cap));return cap
   def save():
    old=state()['saves'];click(1644,1296);wait(lambda s:s['saves']!=old);assert(store/'journey.chk').read_bytes()[:8]==b'8SJRN016'

   assert state()['phase']=='start'and state()['selected']=='0'
   if name=='fresh':
    capture('main-noto');click(480,20);wait(lambda s:s['font']=='1');capture('main-lishu');click(708,20);wait(lambda s:s['font']=='2');capture('main-caoshu')
    key(0xff0d);wait(lambda s:s['phase']=='start-message');capture('no-progress');assert not(store/'journey.chk').exists();key(0xff0d);wait(lambda s:s['phase']=='start')
    key(0xff52);wait(lambda s:s['selected']=='2');key(0xff0d);wait(lambda s:s['phase']=='music');key(0xff0d);wait(lambda s:s['playing']=='Some(1)'and int(s['queued_bytes'])>0);capture('music-first')
    before=int(state()['queued_bytes']);key(0xff52);wait(lambda s:s['selected']=='9');key(0xff0d);wait(lambda s:s['playing']=='Some(10)'and int(s['queued_bytes'])>before);capture('music-last');key(0xff1b);wait(lambda s:s['phase']=='start'and s['selected']=='0')
    click(800,570);wait(lambda s:s['selected']=='1');click(220,1296);wait(lambda s:s['phase']=='new-confirm');capture('new-confirm');click(1344,1000);wait(lambda s:s['yes']=='false');click(220,1296);wait(lambda s:s['phase']=='start'and s['selected']=='1');assert not(store/'journey.chk').exists()
    click(220,1296);wait(lambda s:s['phase']=='new-confirm');click(220,1296);wait(lambda s:s['phase']=='world');assert state()['resources']=='1,0,100,500,100,0'and state()['army']=='30,0,0,0,0,0'and state()['x']=='40'and state()['y']=='40'and state()['steps']=='324';capture('new-world')
    key(0xff53);wait(lambda s:s['x']=='41');key(0xffbf);wait(lambda s:s['phase']=='review');capture('new-army');key(0xff1b);wait(lambda s:s['phase']=='world');save();anchor=capture('saved-world');shutil.copy2(store/'journey.chk',base/'fresh.chk')
   elif name=='cold':
    click(220,1296);wait(lambda s:s['phase']=='world'and s['loaded']=='true');cap=capture('continued-world');assert cap['state_hash']==anchor['state_hash']and cap['frame_hash']==anchor['frame_hash'];key(0xff53);wait(lambda s:s['x']=='42');save();capture('continued-move')
   elif name=='legacy':
    click(800,570);wait(lambda s:s['selected']=='1');click(220,1296);wait(lambda s:s['phase']=='new-confirm');key(0xff1b);wait(lambda s:s['phase']=='start');assert(store/'journey.chk').read_bytes()==old
    key(0xff52);key(0xff0d);wait(lambda s:s['phase']=='world'and s['loaded']=='true');assert state()['resources']=='1,0,120,107,1000,4'and state()['items']=='[true, true, true, true, true, true, true, true]';capture('legacy-continued');save()
   elif name=='corrupt':
    key(0xff0d);wait(lambda s:s['phase']=='start-message');assert(store/'journey.chk').read_bytes()==old;capture('corrupt-kept');key(0xff0d);wait(lambda s:s['phase']=='start');key(0xff54);key(0xff0d);wait(lambda s:s['phase']=='new-confirm');key(0xff0d);wait(lambda s:s['phase']=='world');assert state()['resources']=='1,0,100,500,100,0'and state()['items']=='[false, false, false, false, false, false, false, false]';assert(store/'journey.chk').read_bytes()[:8]==b'8SJRN016';capture('corrupt-new-world');save()
   else:
    capture('executable-default-menu');key(0xff54);key(0xff0d);wait(lambda s:s['phase']=='new-confirm');key(0xff0d);wait(lambda s:s['phase']=='world');assert state()['resources']=='1,0,100,500,100,0';save();assert(store/'journey.chk').is_file();capture('default-save-world')
   final=state();event=Event();event.client.type=33;event.client.display=display;event.client.window=window;event.client.message=x.XInternAtom(display,b'WM_PROTOCOLS',0);event.client.format=32;event.client.data.l[0]=x.XInternAtom(display,b'WM_DELETE_WINDOW',0);x.XSendEvent(display,window,0,0,C.byref(event));x.XFlush(display);code=app.wait(timeout=10);assert code==0;log.close();log=None;runs.append(dict(name=name,exit=code,command=cmd,inputs=inputs,captures=captures,final=final));app=None
  (base/'receipt.json').write_text(json.dumps(dict(status='passed-rust-start-gui',binary_sha256=hashlib.sha256((r/'8sword-remake').read_bytes()).hexdigest(),runs=runs,no_runtime_memory_or_ip_injection=True,source='fresh/corrupt new games use normal menu inputs; cold is a real saved new game; legacy is the real prior v16 item checkpoint, not natural acquisition'),ensure_ascii=False,indent=2)+'\n')
 finally:
  if app and app.poll()is None:app.terminate();app.wait(timeout=5)
  if log:log.close()
  xvfb.terminate();xvfb.wait(timeout=5)
if __name__=='__main__':main()
