#!/usr/bin/env python3
"""有界X11正常輸入：自然敵術、新兵減員、普通勝利及再戰撤退。"""
import ctypes as C
import hashlib,json,os,subprocess,time
from collections import deque
from pathlib import Path
NAV=[[0,0,0,0],[0,2,7,4],[1,3,8,4],[2,0,9,5],[0,5,2,6],[4,0,2,6],[0,0,5,0],[0,8,10,1],[7,9,10,2],[8,0,11,3],[0,11,12,8],[10,0,12,8],[0,0,0,11]]
KEYS=[0xff52,0xff54,0xff51,0xff53]
def main():
 assert Path('/.dockerenv').exists()and os.getuid()==1000
 q=Path('/out');d=q/'gui';d.mkdir();captures=[];inputs=[]
 os.environ.update(DISPLAY=':97',SDL_AUDIODRIVER='dummy',SDL_RENDER_DRIVER='software')
 xvfb=subprocess.Popen(['Xvfb',':97','-screen','0','2000x1400x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 app=None;log=None
 try:
  time.sleep(.4);x=C.CDLL('libX11.so.6');xt=C.CDLL('libXtst.so.6')
  x.XOpenDisplay.argtypes=[C.c_char_p];x.XOpenDisplay.restype=C.c_void_p;display=x.XOpenDisplay(None);assert display
  x.XDefaultRootWindow.argtypes=[C.c_void_p];x.XDefaultRootWindow.restype=C.c_ulong;root=x.XDefaultRootWindow(display)
  x.XQueryTree.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_ulong),C.POINTER(C.c_ulong),C.POINTER(C.POINTER(C.c_ulong)),C.POINTER(C.c_uint)]
  x.XFetchName.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_char_p)];x.XFree.argtypes=[C.c_void_p]
  x.XSetInputFocus.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_ulong];x.XFlush.argtypes=[C.c_void_p]
  x.XKeysymToKeycode.argtypes=[C.c_void_p,C.c_ulong];x.XKeysymToKeycode.restype=C.c_uint
  xt.XTestFakeKeyEvent.argtypes=[C.c_void_p,C.c_uint,C.c_int,C.c_ulong]
  log=(d/'player.log').open('w');cmd=['/out/8sword-remake','--battle','--assets','/out/pack','--enemy-spells','--capture-dir',str(d),'--scale','1','--seed','1']
  app=subprocess.Popen(cmd,stdout=log,stderr=log)
  def state():
   assert app.poll()is None,(app.returncode,(d/'player.log').read_text())
   try:return dict(line.split('\t',1)for line in(d/'status.tsv').read_text().splitlines())
   except FileNotFoundError:return {}
  def wait(pred,seconds=20):
   end=time.monotonic()+seconds
   while time.monotonic()<end:
    s=state()
    if s and pred(s):return s
    time.sleep(.015)
   raise AssertionError(('timeout',state()))
  wait(lambda s:int(s['frames'])>0)
  rr=C.c_ulong();parent=C.c_ulong();children=C.POINTER(C.c_ulong)();count=C.c_uint();found=[]
  assert x.XQueryTree(display,root,C.byref(rr),C.byref(parent),C.byref(children),C.byref(count))
  for i in range(count.value):
   name=C.c_char_p()
   if x.XFetchName(display,children[i],C.byref(name))and name.value:
    if b'Rust'in name.value:found.append(children[i])
    x.XFree(name)
  x.XFree(children);assert len(found)==1;window=found[0];x.XSetInputFocus(display,window,1,0);x.XFlush(display)
  def key(symbol):
   code=x.XKeysymToKeycode(display,symbol);assert code;inputs.append(dict(key=symbol,before=state()))
   xt.XTestFakeKeyEvent(display,code,1,0);x.XFlush(display);time.sleep(.035)
   xt.XTestFakeKeyEvent(display,code,0,0);x.XFlush(display);time.sleep(.04)
  def capture(label):
   n=int(state()['captures']);key(0xffc9);s=wait(lambda s:int(s['captures'])>n);n=int(s['captures']);assert s['readback_equal']=='true'
   captured=dict(line.split('\t',1)for line in(d/f'capture-{n:03}.tsv').read_text().splitlines());captures.append(dict(label=label,number=n,captured=captured,status=s))
  def goto(node):
   start=int(state()['cursor']);todo=deque([(start,[])]);seen=set();route=None
   while todo:
    n,path=todo.popleft()
    if n==node:route=path;break
    if n in seen:continue
    seen.add(n)
    for direction,nxt in enumerate(NAV[n]):
     if nxt:todo.append((nxt,path+[direction]))
   assert route is not None
   for direction in route:
    start=NAV[start][direction];key(KEYS[direction]);wait(lambda s:int(s['cursor'])==start)
  wait(lambda s:s['enemy_returns']=='1'and s['fx']=='true');capture('enemy-thunder')
  assert captures[-1]['captured']['spell']=='1'and captures[-1]['captured']['fx']=='true'
  assert captures[-1]['captured']['army']=='71,0,0,0,0,0'
  for _ in range(20):
   s=wait(lambda s:s['outcome']!='active'or s['actor']=='player')
   if s['outcome']!='active':break
   goto(int(s['legal'].split(',')[0])+1);seq=s['sequence'];key(0xff0d);wait(lambda s:s['sequence']!=seq or s['outcome']!='active')
  victory=wait(lambda s:s['outcome']=='win');assert victory['sequence']=='3'and victory['army']=='71,0,0,0,0,0'and victory['enemy_returns']=='2'
  capture('native-win');key(0xffc7);wait(lambda s:s['font']=='lishu');capture('win-lishu')
  key(ord('r'));wait(lambda s:s['outcome']=='active'and s['actor']=='player');key(0xff1b);retreat=wait(lambda s:s['outcome']=='retreat');capture('restart-retreat')
  # Quit through the window manager event, not a signal.
  x.XInternAtom.argtypes=[C.c_void_p,C.c_char_p,C.c_int];x.XInternAtom.restype=C.c_ulong
  protocols=x.XInternAtom(display,b'WM_PROTOCOLS',0);delete=x.XInternAtom(display,b'WM_DELETE_WINDOW',0)
  class Data(C.Union):_fields_=[('b',C.c_char*20),('s',C.c_short*10),('l',C.c_long*5)]
  class Client(C.Structure):_fields_=[('type',C.c_int),('serial',C.c_ulong),('send',C.c_int),('display',C.c_void_p),('window',C.c_ulong),('message',C.c_ulong),('format',C.c_int),('data',Data)]
  event=Client();event.type=33;event.display=display;event.window=window;event.message=protocols;event.format=32;event.data.l[0]=delete
  x.XSendEvent.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_long,C.c_void_p];x.XSendEvent(display,window,0,0,C.byref(event));x.XFlush(display)
  exit_code=app.wait(timeout=10);assert exit_code==0
  receipt=dict(status='passed-rust-enemy-gui',binary_sha256=hashlib.sha256((q/'8sword-remake').read_bytes()).hexdigest(),command=cmd,seed=1,seed_set_before_execution=True,controlled_memory_or_ip=False,inputs=inputs,captures=captures,victory=victory,retreat=retreat,exit=exit_code)
  (d/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
 finally:
  if app and app.poll()is None:app.terminate();app.wait(timeout=5)
  if log:log.close()
  xvfb.terminate();xvfb.wait(timeout=5)
if __name__=='__main__':main()
