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
  for name in ['shop','shop-cold','spell-cold','world-cold','guard','guard-cold']:
   d=base/name;d.mkdir();store=base/(name+'-store');store.mkdir();log=(d/'player.log').open('w')
   sources={'shop':r/'shop-fixture','shop-cold':base/'shop-store','spell-cold':base/'shop-cold-store','world-cold':base/'spell-cold-store','guard':r/'guard-fixture','guard-cold':base/'guard-store'}
   for p in sources[name].iterdir():
    if p.is_file():shutil.copy2(p,store/p.name)
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
   def is_menu(s):return s['spell_phase']=='menu'and s['actor']=='player'
   def reach_caster():
    for _ in range(30):
     s=wait(lambda s:s['actor']=='player'or s['outcome']!='None');assert s['outcome']=='None'
     if is_menu(s):return s
     key(32,.25)
    raise AssertionError('no caster')
   def retreat_world():
    if state()['outcome']=='None':key(0xff1b,.55)
    wait(lambda s:s['outcome']!='None');capture('finished');key(0xff0d,.4)
    if state()['phase'].startswith('guard'):key(0xff0d,.4)
    wait(lambda s:s['phase']=='world');save()
   if name=='shop':
    wait(lambda s:s['phase']=='world');capture('before-shop');gold=int(state()['gold']);key(0xff54)
    wait(lambda s:s['phase']=='magic-shop');capture('fireball-shop');center(200,1295);center(200,1295)
    wait(lambda s:s['battle_charges']=='[2, 0, 0, 0, 0, 0, 0, 0]');assert int(state()['gold'])==gold-40;save();capture('purchased-two');anchors['shop']=state()['state_hash']
   elif name=='shop-cold':
    wait(lambda s:s['phase']=='magic-shop');assert state()['state_hash']==anchors['shop'];capture('shop-cold');key(0xff1b,.4)
    if state()['phase']=='world':
     key(0xffc1);wait(lambda s:s['phase']=='magic-menu');capture('inventory-two');key(0xff1b)
    if state()['phase']=='world':key(0xff51,.15)
    for i in range(180):
     if state()['phase']=='prompt':break
     assert state()['phase']=='world',state();key(0xff51 if i%2==0 else 0xff53,.12)
    wait(lambda s:s['phase']=='prompt');capture('natural-encounter');key(0xff0d);reach_caster();capture('spell-menu')
    center(300,200);center(200,1295);wait(lambda s:s['spell_phase']=='target');save();capture('target-saved');anchors['target']=state()['state_hash']
   elif name=='spell-cold':
    wait(lambda s:s['spell_phase']=='target');assert state()['state_hash']==anchors['target'];assert state()['battle_charges']=='[1, 0, 0, 0, 0, 0, 0, 0]';capture('target-cold')
    center(940,450);center(200,1295);time.sleep(.6);capture('cast-result');retreat_world();capture('world-one');anchors['world']=state()['state_hash']
   elif name=='world-cold':
    wait(lambda s:s['phase']=='world');assert state()['state_hash']==anchors['world'];assert state()['battle_charges']=='[1, 0, 0, 0, 0, 0, 0, 0]';key(0xffc1);wait(lambda s:s['phase']=='magic-menu');capture('inventory-one-cold')
   elif name=='guard':
    wait(lambda s:s['phase']=='world');key(0xff52);wait(lambda s:s['phase'].startswith('guard'));capture('guard-prompt');key(0xff0d);reach_caster();capture('guard-spell-menu')
    center(300,910);center(200,1295);wait(lambda s:s['spell_phase']=='target');save();capture('clone-target-saved');anchors['clone']=state()['state_hash']
   elif name=='guard-cold':
    wait(lambda s:s['phase']=='battle');assert state()['state_hash']==anchors['clone'];assert state()['battle_charges']=='[1, 0, 0, 0, 0, 0, 0, 0]';capture('clone-target-cold');center(680,450);center(200,1295)
    for _ in range(20):
     if state()['outcome']!='None':break
     key(0xff1b,.03)
    capture('clone-result');retreat_world();capture('guard-world');assert state()['army'].split(',')[0]=='60';key(0xffc1);capture('clone-inventory-cold')
   final=state();event=Event();event.client.type=33;event.client.display=display;event.client.window=window;event.client.message=x.XInternAtom(display,b'WM_PROTOCOLS',0);event.client.format=32;event.client.data.l[0]=x.XInternAtom(display,b'WM_DELETE_WINDOW',0);x.XSendEvent(display,window,0,0,C.byref(event));x.XFlush(display);code=app.wait(timeout=10);assert code==0;log.close();log=None;runs.append(dict(name=name,exit=code,command=cmd,inputs=inputs,captures=captures,final=final));app=None
   (base/'completed-runs.json').write_text(json.dumps(runs,ensure_ascii=False,indent=2)+'\n')
  (base/'receipt.json').write_text(json.dumps(dict(status='passed-rust-combat-inventory-gui',binary_sha256=hashlib.sha256((r/'8sword-remake').read_bytes()).hexdigest(),runs=runs,no_runtime_memory_or_ip_injection=True,scope='True v16 read; explicitly searched book at original coordinate, positioned shop and 30 militia plus 2 native sorcerers, seed1; guard additionally grants two test charges. All subsequent interaction uses normal mouse/key input, no runtime memory injection.'),ensure_ascii=False,indent=2)+'\n')
 finally:
  if app and app.poll()is None:app.terminate();app.wait(timeout=5)
  if log:log.close()
  xvfb.terminate();xvfb.wait(timeout=5)
if __name__=='__main__':main()
