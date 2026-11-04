#!/usr/bin/env python3
"""Rust地圖預覽的正常按鍵、受阻、F7與獨立程序讀檔抽驗。"""
import ctypes as C
import hashlib,json,os,subprocess,time
from pathlib import Path
def main():
 assert Path('/.dockerenv').exists()and os.getuid()==1000
 root=Path('/out');base=root/'gui';base.mkdir();store=base/'store';store.mkdir();runs=[];app=None;log=None
 os.environ.update(DISPLAY=':97',SDL_AUDIODRIVER='dummy',SDL_RENDER_DRIVER='software')
 xvfb=subprocess.Popen(['Xvfb',':97','-screen','0','2000x1400x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  time.sleep(.4);x=C.CDLL('libX11.so.6');xt=C.CDLL('libXtst.so.6')
  x.XOpenDisplay.argtypes=[C.c_char_p];x.XOpenDisplay.restype=C.c_void_p;display=x.XOpenDisplay(None);assert display
  x.XDefaultRootWindow.argtypes=[C.c_void_p];x.XDefaultRootWindow.restype=C.c_ulong;window_root=x.XDefaultRootWindow(display)
  x.XQueryTree.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_ulong),C.POINTER(C.c_ulong),C.POINTER(C.POINTER(C.c_ulong)),C.POINTER(C.c_uint)]
  x.XFetchName.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_char_p)];x.XFree.argtypes=[C.c_void_p]
  x.XSetInputFocus.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_ulong];x.XFlush.argtypes=[C.c_void_p]
  x.XKeysymToKeycode.argtypes=[C.c_void_p,C.c_ulong];x.XKeysymToKeycode.restype=C.c_uint
  x.XTranslateCoordinates.argtypes=[C.c_void_p,C.c_ulong,C.c_ulong,C.c_int,C.c_int,C.POINTER(C.c_int),C.POINTER(C.c_int),C.POINTER(C.c_ulong)]
  xt.XTestFakeKeyEvent.argtypes=[C.c_void_p,C.c_uint,C.c_int,C.c_ulong]
  xt.XTestFakeMotionEvent.argtypes=[C.c_void_p,C.c_int,C.c_int,C.c_int,C.c_ulong];xt.XTestFakeButtonEvent.argtypes=[C.c_void_p,C.c_uint,C.c_int,C.c_ulong]
  for name in ['control','continue']:
   d=base/name;d.mkdir();log=(d/'player.log').open('w');cmd=['/out/8sword-remake','--world-preview','--assets','/out/pack','--capture-dir',str(d),'--scale','1','--save-dir',str(store)]+(['--continue']if name=='continue'else['--seed','1'])
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
     time.sleep(.025)
    raise AssertionError((name,'timeout',state()))
   wait(lambda s:'state_hash'in s)
   rr=C.c_ulong();parent=C.c_ulong();children=C.POINTER(C.c_ulong)();count=C.c_uint();found=[]
   assert x.XQueryTree(display,window_root,C.byref(rr),C.byref(parent),C.byref(children),C.byref(count))
   for i in range(count.value):
    title=C.c_char_p()
    if x.XFetchName(display,children[i],C.byref(title))and title.value:
     if b'Rust'in title.value:found.append(children[i])
     x.XFree(title)
   x.XFree(children);assert len(found)==1;window=found[0];x.XSetInputFocus(display,window,1,0);x.XFlush(display)
   def key(symbol):
    code=x.XKeysymToKeycode(display,symbol);assert code;inputs.append(dict(key=symbol,before=state()));xt.XTestFakeKeyEvent(display,code,1,0);x.XFlush(display);time.sleep(.04);xt.XTestFakeKeyEvent(display,code,0,0);x.XFlush(display);time.sleep(.08)
   def click(px,py):
    dx=C.c_int();dy=C.c_int();child=C.c_ulong();assert x.XTranslateCoordinates(display,window,window_root,px,py,C.byref(dx),C.byref(dy),C.byref(child));inputs.append(dict(click=[px,py],before=state()));xt.XTestFakeMotionEvent(display,0,dx.value,dy.value,0);xt.XTestFakeButtonEvent(display,1,1,0);x.XFlush(display);time.sleep(.04);xt.XTestFakeButtonEvent(display,1,0,0);x.XFlush(display);time.sleep(.08)
   def move(symbol):
    n=int(state()['actions']);key(symbol);return wait(lambda s:int(s['actions'])>n or s['pending']!='None')
   def capture(label):
    n=int(state()['captures']);key(0xffc9);s=wait(lambda s:int(s['captures'])>n);n=int(s['captures']);cap=dict(line.split('\t',1)for line in(d/f'capture-{n:03}.tsv').read_text().splitlines());assert cap['readback_equal']=='true';captures.append(dict(label=label,number=n,captured=cap));return cap
   if name=='control':
    capture('start-noto');move(0xff54);move(0xff54);s=move(0xff53);assert(s['x'],s['y'],s['remaining'],s['actions'])==('40','42','322','3'),s
    capture('blocked-mountain');click(450,20);wait(lambda s:s['font']=='1');click(1000,20);wait(lambda s:s['music']=='false');capture('save-lishu');click(1530,20);saved=wait(lambda s:s['saves']=='1');assert(store/'world-preview.chk').stat().st_size==5648
    checkpoint_hash=saved['state_hash'];checkpoint_frame=captures[-1]['captured']['frame_hash'];saved_bytes=(store/'world-preview.chk').read_bytes()
   else:
    s=state();assert s['loaded']=='true'and s['state_hash']==checkpoint_hash,s;c=capture('cold-lishu');assert c['frame_hash']==checkpoint_frame
   # Same normal inputs from saved state, including an event boundary.
   move(0xff51);move(0xff52);move(0xff52);move(0xff51);s=move(0xff51);assert s['pending']=='Some(Terrain(51))',s
   end=capture('camp-boundary');frozen=end['state_hash'];key(0xff54);time.sleep(.2);assert state()['state_hash']==frozen
   key(0xffc4);time.sleep(.1);assert(store/'world-preview.chk').read_bytes()==saved_bytes
   if name=='control':final_hash=frozen;final_frame=end['frame_hash']
   else:assert frozen==final_hash and end['frame_hash']==final_frame
   # The third font remains a toolbar choice even at a boundary.
   click(700,20);wait(lambda s:s['font']=='2');capture('caoshu');s=state();assert int(s['queued_bytes'])>0 or name=='continue'
   key(0xff1b);code=app.wait(timeout=10);assert code==0;log.close();log=None
   runs.append(dict(name=name,exit=code,inputs=inputs,captures=captures,final=s));app=None
  (base/'receipt.json').write_text(json.dumps(dict(status='passed-rust-world-gui',binary_sha256=hashlib.sha256((root/'8sword-remake').read_bytes()).hexdigest(),fixed_seed=1,checkpoint_hash=checkpoint_hash,final_hash=final_hash,runs=runs),ensure_ascii=False,indent=2)+'\n')
 finally:
  if app and app.poll()is None:app.terminate();app.wait(timeout=5)
  if log:log.close()
  xvfb.terminate();xvfb.wait(timeout=5)
if __name__=='__main__':main()
