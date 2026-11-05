#!/usr/bin/env python3
"""原起點正常遭遇、原式戰場、F7與獨立程序回場抽驗。"""
import ctypes as C
import hashlib,json,os,shutil,subprocess,time
from pathlib import Path
def main():
 assert Path('/.dockerenv').exists()and os.getuid()==1000
 r=Path('/out');base=r/'gui';base.mkdir();runs=[];app=None;log=None
 os.environ.update(DISPLAY=':97',SDL_AUDIODRIVER='dummy',SDL_RENDER_DRIVER='software')
 xvfb=subprocess.Popen(['Xvfb',':97','-screen','0','2000x1400x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  time.sleep(.4);x=C.CDLL('libX11.so.6');xt=C.CDLL('libXtst.so.6');x.XOpenDisplay.argtypes=[C.c_char_p];x.XOpenDisplay.restype=C.c_void_p;display=x.XOpenDisplay(None);assert display
  x.XDefaultRootWindow.argtypes=[C.c_void_p];x.XDefaultRootWindow.restype=C.c_ulong;root=x.XDefaultRootWindow(display)
  x.XQueryTree.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_ulong),C.POINTER(C.c_ulong),C.POINTER(C.POINTER(C.c_ulong)),C.POINTER(C.c_uint)];x.XFetchName.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_char_p)];x.XFree.argtypes=[C.c_void_p];x.XSetInputFocus.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_ulong];x.XFlush.argtypes=[C.c_void_p];x.XKeysymToKeycode.argtypes=[C.c_void_p,C.c_ulong];x.XKeysymToKeycode.restype=C.c_uint;xt.XTestFakeKeyEvent.argtypes=[C.c_void_p,C.c_uint,C.c_int,C.c_ulong]
  x.XInternAtom.argtypes=[C.c_void_p,C.c_char_p,C.c_int];x.XInternAtom.restype=C.c_ulong;x.XSendEvent.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_long,C.c_void_p]
  class Data(C.Union):_fields_=[('b',C.c_char*20),('s',C.c_short*10),('l',C.c_long*5)]
  class Client(C.Structure):_fields_=[('type',C.c_int),('serial',C.c_ulong),('send',C.c_int),('display',C.c_void_p),('window',C.c_ulong),('message',C.c_ulong),('format',C.c_int),('data',Data)]
  class Event(C.Union):_fields_=[('client',Client),('pad',C.c_long*24)]
  for name in['control','battle-continue','world-continue','annihilation']:
   d=base/name;d.mkdir();store=base/(name+'-store');store.mkdir();log=(d/'player.log').open('w');cmd=['/out/8sword-remake','--journey','--assets','/out/pack','--capture-dir',str(d),'--scale','1','--save-dir',str(store)]
   if name=='control':cmd+=['--seed','1']
   else:
    shutil.copy2(base/('battle-store'if name=='battle-continue'else'world-store')/'journey.chk',store/'journey.chk');cmd+=['--continue']
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
   def key(symbol):
    code=x.XKeysymToKeycode(display,symbol);assert code;inputs.append(dict(key=symbol,before=state()));xt.XTestFakeKeyEvent(display,code,1,0);x.XFlush(display);time.sleep(.04);xt.XTestFakeKeyEvent(display,code,0,0);x.XFlush(display);time.sleep(.07)
   def capture(label):
    n=int(state()['captures']);key(0xffc9);s=wait(lambda s:int(s['captures'])>n);n=int(s['captures']);cap=dict(line.split('\t',1)for line in(d/f'capture-{n:03}.tsv').read_text().splitlines());assert cap['readback_equal']=='true';captures.append(dict(label=label,number=n,captured=cap));return cap
   def encounter():
    for _ in range(324):
     s=state()
     if s['phase']=='prompt':return s
     assert s['phase']=='world'and s['pending']=='None',s;before=s['actions'];key(32);wait(lambda s:s['actions']!=before or s['phase']=='prompt')
    raise AssertionError('encounter budget')
   def save():
    before=state()['saves'];key(0xffc4);wait(lambda s:s['saves']!=before);assert(store/'journey.chk').is_file()
   if name=='control':
    assert state()['army']=='30,0,0,0,0,0'and state()['gold']=='500';capture('original-start');encounter();capture('encounter-prompt');key(0xff0d);wait(lambda s:s['phase']=='battle'and s['actor']=='player');key(0xffc7);wait(lambda s:s['font']=='1');key(ord('m'));wait(lambda s:s['music']=='false');anchor=capture('battle-save');save();(base/'battle-store').mkdir();shutil.copy2(store/'journey.chk',base/'battle-store/journey.chk')
   elif name=='battle-continue':
    s=wait(lambda s:s['actor']=='player');assert s['state_hash']==anchor['state_hash'],s;cap=capture('battle-cold');assert cap['frame_hash']==anchor['frame_hash']
   else:
    s=state();assert s['state_hash']==world_anchor['state_hash'];cap=capture('world-cold');assert cap['frame_hash']==world_anchor['frame_hash']
   if name in['control','battle-continue']:
    key(0xff1b);wait(lambda s:s['outcome']=='Some(Retreat)');capture('retreat');key(0xff0d);s=wait(lambda s:s['phase']=='world'and s['battles']=='1');assert s['army']=='30,0,0,0,0,0'and int(s['gold'])<500;s=capture('returned-map')
    if name=='control':world_anchor=s;save();(base/'world-store').mkdir();shutil.copy2(store/'journey.chk',base/'world-store/journey.chk')
    else:assert s['state_hash']==world_anchor['state_hash']and s['frame_hash']==world_anchor['frame_hash']
   if name=='annihilation':
    encounter();key(0xff0d);wait(lambda s:s['phase']=='battle');
    for _ in range(200):
     s=wait(lambda s:s['actor']=='player'or s['outcome']!='None')
     if s['outcome']!='None':break
     old=s['sequence'];key(32);time.sleep(.35)
    s=wait(lambda s:s['outcome']=='Some(Loss)');capture('annihilation-choice');key(0xff53);key(0xff0d);s=wait(lambda s:s['phase']=='world'and s['battles']=='2');assert s['army']=='0,0,0,0,0,0'and s['gold']==world_anchor['gold'];capture('empty-army-roam');save()
   final=state();event=Event();event.client.type=33;event.client.display=display;event.client.window=window;event.client.message=x.XInternAtom(display,b'WM_PROTOCOLS',0);event.client.format=32;event.client.data.l[0]=x.XInternAtom(display,b'WM_DELETE_WINDOW',0);x.XSendEvent(display,window,0,0,C.byref(event));x.XFlush(display);code=app.wait(timeout=10);assert code==0;log.close();log=None;runs.append(dict(name=name,exit=code,command=cmd,inputs=inputs,captures=captures,final=final));app=None
  (base/'receipt.json').write_text(json.dumps(dict(status='passed-rust-journey-gui',binary_sha256=hashlib.sha256((r/'8sword-remake').read_bytes()).hexdigest(),runs=runs,fixed_seed=1,no_memory_or_ip_injection=True),ensure_ascii=False,indent=2)+'\n')
 finally:
  if app and app.poll()is None:app.terminate();app.wait(timeout=5)
  if log:log.close()
  xvfb.terminate();xvfb.wait(timeout=5)
if __name__=='__main__':main()
