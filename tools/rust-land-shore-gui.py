#!/usr/bin/env python3
"""旅程戰鬥法術庫存與冷讀抽驗。限Docker。"""
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

  anchors={}
  for name in ['notice','notice-cold','shop','shop-cold','guard','guard-cold']:
   d=base/name;d.mkdir();store=base/(name+'-store');store.mkdir();log=(d/'player.log').open('w')
   source=base/(name.removesuffix('-cold')+'-store') if name.endswith('-cold') else r/(name+'-fixture')
   for p in source.iterdir():
    if p.is_file():shutil.copy2(p,store/p.name)
   fixture=dict(l.split('\t',1)for l in(store/'fixture.tsv').read_text().splitlines());move=int(fixture['key'])
   cmd=[str(r/'8sword-remake'),'--journey','--assets',str(r/'pack'),'--capture-dir',str(d),'--scale','1','--save-dir',str(store),'--continue']
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
   def center(px,py):click(px+512,py)
   def save():
    old=state()['saves'];key(0xffc4);wait(lambda s:s['saves']!=old);assert(store/'journey.chk').read_bytes()[:8]==b'8SJRN017'
   def arrive_notice():
    key(move);wait(lambda s:s['phase']=='map-notice');key(0xff0d);wait(lambda s:s['phase']=='shore')
   if name=='notice':
    wait(lambda s:s['phase']=='world');assert state()['boat']=='2' and state()['steps']=='1';capture('land-before-notice');key(move);wait(lambda s:s['phase']=='map-notice');capture('notice-before-shore');key(0xff0d);wait(lambda s:s['phase']=='shore');key(0xff51);wait(lambda s:s['shore_yes']=='Some(false)');save();capture('refusal-saved');anchors['notice']=state()['state_hash']
   elif name=='notice-cold':
    wait(lambda s:s['phase']=='shore');assert state()['state_hash']==anchors['notice'];capture('refusal-cold');center(200,1295);wait(lambda s:s['phase']=='world');assert state()['boat']=='2' and state()['steps']=='1';capture('refused-on-land');arrive_notice();center(200,1295);wait(lambda s:s['phase']=='monthly');assert state()['boat']=='0';save();capture('accepted-monthly');key(0xff0d);wait(lambda s:s['phase']=='world');assert state()['steps']=='324';capture('month-return')
   elif name=='shop':
    wait(lambda s:s['phase']=='world');anchors['shop-gold']=int(state()['gold']);key(move);wait(lambda s:s['phase']=='shore');key(0xff51);center(200,1295);wait(lambda s:s['phase']=='magic-shop');capture('refused-shop-bridge');center(200,1295);wait(lambda s:s['magic_charges']=='[1, 0, 0, 0, 0, 0, 0, 0]');assert int(state()['gold'])==anchors['shop-gold']-10;save();capture('bridge-purchased-saved');anchors['shop']=state()['state_hash']
   elif name=='shop-cold':
    wait(lambda s:s['phase']=='magic-shop');assert state()['state_hash']==anchors['shop'];capture('bridge-cold');key(0xff1b);wait(lambda s:s['phase']=='world');assert state()['boat']=='2'and state()['steps']=='2';assert int(state()['gold'])==anchors['shop-gold']-10;save();capture('shop-return-no-second-shore')
   elif name=='guard':
    wait(lambda s:s['phase']=='world');key(move);wait(lambda s:s['phase']=='shore');key(0xff51);center(200,1295);wait(lambda s:s['phase']=='guard');assert state()['guard_stage']=='Some(Refused)';save();capture('guard-refused-saved');anchors['guard']=state()['state_hash']
   elif name=='guard-cold':
    wait(lambda s:s['phase']=='guard');assert state()['state_hash']==anchors['guard'];capture('guard-refused-cold');key(0xff0d);wait(lambda s:s['phase']=='world');assert state()['steps']=='2'and state()['boat']=='2';key(move);wait(lambda s:s['phase']=='shore');center(200,1295);wait(lambda s:s['guard_stage']=='Some(Prompt)');capture('guard-after-landing');key(0xff1b);wait(lambda s:s['phase']=='world');assert state()['boat']=='0'and state()['steps']=='1';save();capture('guard-cancel-return')
   final=state();event=Event();event.client.type=33;event.client.display=display;event.client.window=window;event.client.message=x.XInternAtom(display,b'WM_PROTOCOLS',0);event.client.format=32;event.client.data.l[0]=x.XInternAtom(display,b'WM_DELETE_WINDOW',0);x.XSendEvent(display,window,0,0,C.byref(event));x.XFlush(display);code=app.wait(timeout=10);assert code==0;log.close();log=None;runs.append(dict(name=name,exit=code,command=cmd,inputs=inputs,captures=captures,final=final));app=None
   (base/'completed-runs.json').write_text(json.dumps(runs,ensure_ascii=False,indent=2)+'\n')
  (base/'receipt.json').write_text(json.dumps(dict(status='passed-rust-land-shore-gui',binary_sha256=hashlib.sha256((r/'8sword-remake').read_bytes()).hexdigest(),runs=runs,no_runtime_memory_or_ip_injection=True,scope='True v17; explicit original land coordinates, boat2, seed1 and remaining1 or2. Subsequent mouse/key input uses normal notice, shore, shop, guard, monthly and F7/cold paths; no live memory/IP injection. Space special-site branch excluded.'),ensure_ascii=False,indent=2)+'\n')
 finally:
  if app and app.poll()is None:app.terminate();app.wait(timeout=5)
  if log:log.close()
  xvfb.terminate();xvfb.wait(timeout=5)
if __name__=='__main__':main()
