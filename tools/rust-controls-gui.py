#!/usr/bin/env python3
"""Linux真實滑鼠抽驗：原起點、營地、原式管理、獨立冷讀及選敵。"""
import ctypes as C
import hashlib,json,os,shutil,subprocess,time
from pathlib import Path

def main():
 assert Path('/.dockerenv').exists() and os.getuid()==1000
 r=Path('/out/native');base=r/'gui';base.mkdir();runs=[];app=None;log=None
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
  for name in ['purchase','camp-cold','world-cold','legacy-cold']:
   d=base/name;d.mkdir();store=base/(name+'-store');store.mkdir();log=(d/'player.log').open('w');cmd=[str(r/'8sword-remake'),'--journey','--assets',str(r/'pack'),'--capture-dir',str(d),'--scale','1','--save-dir',str(store)]
   if name=='purchase':cmd+=['--seed','1']
   else:
    src=base/('purchase-store'if name=='camp-cold'else'camp-cold-store')/'journey.chk'
    if name=='legacy-cold':src=r.parent/'evidence/legacy-v1.chk'
    shutil.copy2(src,store/'journey.chk');cmd+=['--continue']
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
   def move(px,py):xt.XTestFakeMotionEvent(display,-1,ox.value+px,oy.value+py,0);x.XFlush(display)
   def click(px,py,end=None):
    inputs.append(dict(mouse=[px,py],release=list(end or (px,py)),before=state()));move(px,py);xt.XTestFakeButtonEvent(display,1,1,0);x.XFlush(display);time.sleep(.04)
    if end:move(*end)
    xt.XTestFakeButtonEvent(display,1,0,0);x.XFlush(display);time.sleep(.10)
   def key(symbol):
    code=x.XKeysymToKeycode(display,symbol);assert code;inputs.append(dict(diagnostic_key=symbol));xt.XTestFakeKeyEvent(display,code,1,0);x.XFlush(display);time.sleep(.04);xt.XTestFakeKeyEvent(display,code,0,0);x.XFlush(display);time.sleep(.07)
   def capture(label):
    old=int(state()['captures']);key(0xffc9);s=wait(lambda s:int(s['captures'])>old);n=int(s['captures']);cap=dict(line.split('\t',1)for line in(d/f'capture-{n:03}.tsv').read_text().splitlines());assert cap['readback_equal']=='true';captures.append(dict(label=label,number=n,captured=cap));return cap
   def save():
    old=state()['saves'];click(1644,1296);wait(lambda s:s['saves']!=old);assert(store/'journey.chk').read_bytes()[:8]==b'8SJRN002'
   if name=='purchase':
    assert state()['army']=='30,0,0,0,0,0'and state()['gold']=='500';click(450,20);wait(lambda s:s['font']=='1');click(1000,20);wait(lambda s:s['music']=='false')
    click(696,495);wait(lambda s:s['y']=='39');click(696,495);wait(lambda s:s['y']=='38');click(504,645);wait(lambda s:s['phase']=='camp'and s['camp']=='Some(1)');assert state()['actions']=='2';capture('original-camp')
    click(660,768);wait(lambda s:s['extra']=='true');click(236,1296);wait(lambda s:s['phase']=='quantity')
    for _ in range(4):click(1800,708)
    click(236,1296);s=wait(lambda s:s['digits']=='9999'and bool(s['message']));assert s['gold']=='500'and s['army']=='30,0,0,0,0,0';capture('refused-quantity')
    click(1800,852);click(1488,420);click(236,1296);wait(lambda s:s['gold']=='460');assert state()['army']=='30,1,0,0,0,0'and state()['used']=='33';capture('wolf-purchased')
    click(692,1296);click(240,768);click(236,1296);click(1488,420);click(236,1296);wait(lambda s:s['gold']=='459');assert state()['army']=='31,1,0,0,0,0';capture('native-purchased');save();camp_anchor=state()['state_hash']
   elif name=='camp-cold':
    s=state();assert s['phase']=='camp'and s['state_hash']==camp_anchor and s['army']=='31,1,0,0,0,0';capture('camp-cold');click(660,768);click(236,1296);capture('extra-stock-cold');click(692,1296);click(692,1296);wait(lambda s:s['phase']=='world');assert state()['actions']=='3'
    click(1600,330);wait(lambda s:s['phase']=='review');capture('original-six-stack-review');click(252,20);wait(lambda s:s['font']=='0');capture('review-noto');click(708,20);wait(lambda s:s['font']=='2');capture('review-caoshu');click(450,20);wait(lambda s:s['font']=='1');click(692,1296);click(1600,500);wait(lambda s:s['phase']=='dismiss')
    click(408,636,end=(1300,1220));assert state()['selected']=='0';click(408,636);wait(lambda s:s['selected']=='1');capture('original-six-stack-dismiss');click(236,1296);wait(lambda s:s['army']=='31,0,0,0,0,0');assert state()['gold']=='459';click(692,1296);save();world_anchor=state()['state_hash'];capture('dismissed-world')
   elif name=='world-cold':
    assert state()['state_hash']==world_anchor and state()['army']=='31,0,0,0,0,0';capture('world-cold');click(696,795)
    for _ in range(100):
     s=state()
     if s['phase']=='prompt':break
     assert s['phase']=='world'and s['pending']=='None',s;old=s['actions'];click(236,1296);wait(lambda s:s['phase']!='world'or s['actions']!=old)
    wait(lambda s:s['phase']=='prompt');capture('mouse-encounter');click(360,900);click(236,1296);wait(lambda s:s['phase']=='battle'and s['actor']=='player');s=state();target=int(s['targets'].split(',')[0]);positions=[(948,498),(948,798),(948,1098),(1212,648),(1212,948),(1476,798)];click(*positions[target]);wait(lambda s:int(s['cursor'])==target+1);assert state()['sequence']==s['sequence'];capture('mouse-selected-enemy');click(236,1296);wait(lambda v:int(v['sequence'])>int(s['sequence']));capture('mouse-ordinary-action');click(692,1296);wait(lambda s:s['outcome']=='Some(Retreat)');time.sleep(.2);click(236,1296);wait(lambda s:s['phase']=='world');capture('mouse-returned-map');save()
   else:
    assert state()['phase']=='battle'and state()['army']=='30,0,0,0,0,0';capture('legacy-v1-cold');click(692,1296);wait(lambda s:s['outcome']=='Some(Retreat)');time.sleep(.2);click(236,1296);wait(lambda s:s['phase']=='world');save();capture('legacy-v2-saved')
   final=state();event=Event();event.client.type=33;event.client.display=display;event.client.window=window;event.client.message=x.XInternAtom(display,b'WM_PROTOCOLS',0);event.client.format=32;event.client.data.l[0]=x.XInternAtom(display,b'WM_DELETE_WINDOW',0);x.XSendEvent(display,window,0,0,C.byref(event));x.XFlush(display);code=app.wait(timeout=10);assert code==0;log.close();log=None;runs.append(dict(name=name,exit=code,command=cmd,inputs=inputs,captures=captures,final=final));app=None
  (base/'receipt.json').write_text(json.dumps(dict(status='passed-rust-controls-gui',binary_sha256=hashlib.sha256((r/'8sword-remake').read_bytes()).hexdigest(),runs=runs,fixed_seed=1,gameplay_input='XTest mouse; keyboard only F12 diagnostic capture',no_memory_or_ip_injection=True),ensure_ascii=False,indent=2)+'\n')
 finally:
  if app and app.poll()is None:app.terminate();app.wait(timeout=5)
  if log:log.close()
  xvfb.terminate();xvfb.wait(timeout=5)
if __name__=='__main__':main()
