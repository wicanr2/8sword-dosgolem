#!/usr/bin/env python3
"""原生戰鬥F7、獨立程序續接及同輸入結果抽驗；不寫RAM／IP。"""
import ctypes as C
import hashlib,json,os,shutil,subprocess,time
from pathlib import Path
from collections import deque
NAV=[[0,0,0,0],[0,2,7,4],[1,3,8,4],[2,0,9,5],[0,5,2,6],[4,0,2,6],[0,0,5,0],[0,8,10,1],[7,9,10,2],[8,0,11,3],[0,11,12,8],[10,0,12,8],[0,0,0,11]]
KEYS=[0xff52,0xff54,0xff51,0xff53]
def main():
 assert Path('/.dockerenv').exists()and os.getuid()==1000
 root=Path('/out');base=root/'gui';base.mkdir();runs=[];log=None;app=None
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
  xt.XTestFakeMotionEvent.argtypes=[C.c_void_p,C.c_int,C.c_int,C.c_int,C.c_ulong]
  xt.XTestFakeButtonEvent.argtypes=[C.c_void_p,C.c_uint,C.c_int,C.c_ulong]
  for name in ['ordinary-control','ordinary-continue','support-control','extra-continue','paid-continue']:
   d=base/name;d.mkdir();store=base/('ordinary-store'if name.startswith('ordinary')else'extra-store'if name=='extra-continue'else'paid-store'if name=='paid-continue'else'support-store');store.mkdir(exist_ok=True)
   log=(d/'player.log').open('w');cmd=['/out/8sword-remake','--battle','--assets','/out/pack','--capture-dir',str(d),'--scale','1','--save-dir',str(store)]
   if name.endswith('continue'):cmd+=['--continue']
   else:
    cmd+=['--seed','305419896']
    if name=='support-control':cmd+=['--taoist']
   app=subprocess.Popen(cmd,stdout=log,stderr=log);inputs=[];captures=[]
   def state():
    assert app.poll()is None,(name,app.returncode,(d/'player.log').read_text())
    try:return dict(line.split('\t',1)for line in(d/'status.tsv').read_text().splitlines())
    except FileNotFoundError:return {}
   def wait(pred,seconds=20):
    until=time.monotonic()+seconds
    while time.monotonic()<until:
     s=state()
     if s and pred(s):return s
     time.sleep(.015)
    raise AssertionError((name,'timeout',state()))
   wait(lambda s:s['actor']=='player' or s['outcome']!='active')
   rr=C.c_ulong();parent=C.c_ulong();children=C.POINTER(C.c_ulong)();count=C.c_uint();found=[]
   assert x.XQueryTree(display,window_root,C.byref(rr),C.byref(parent),C.byref(children),C.byref(count))
   for i in range(count.value):
    title=C.c_char_p()
    if x.XFetchName(display,children[i],C.byref(title))and title.value:
     if b'Rust'in title.value:found.append(children[i])
     x.XFree(title)
   x.XFree(children);assert len(found)==1;window=found[0];x.XSetInputFocus(display,window,1,0);x.XFlush(display)
   def key(symbol):
    code=x.XKeysymToKeycode(display,symbol);assert code;inputs.append(dict(key=symbol,before=state()));xt.XTestFakeKeyEvent(display,code,1,0);x.XFlush(display);time.sleep(.035);xt.XTestFakeKeyEvent(display,code,0,0);x.XFlush(display);time.sleep(.06)
   def capture(label):
    n=int(state()['captures']);key(0xffc9);s=wait(lambda s:int(s['captures'])>n);n=int(s['captures']);assert s['readback_equal']=='true';cap=dict(line.split('\t',1)for line in(d/f'capture-{n:03}.tsv').read_text().splitlines());captures.append(dict(label=label,number=n,captured=cap,status=s));return cap
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
   def skip():
    old=(state()['half_turn'],state()['raw'],state()['spell_returns']);key(32);wait(lambda s:s['outcome']!='active'or(s['half_turn'],s['raw'],s['spell_returns'])!=old)
   def menu():
    for _ in range(100):
     s=wait(lambda s:s['actor']=='player'or s['outcome']!='active');assert s['outcome']=='active',s
     if s['phase']=='spell-menu':return s
     skip()
    raise AssertionError('menu budget')
   def select(n):
    wait(lambda s:s['phase']=='spell-menu')
    while int(state()['spell_cursor'])!=n:
     before=state()['spell_cursor'];key(0xff54);wait(lambda s:s['spell_cursor']!=before)
    old=state()['spell_returns'];key(0xff0d);return wait(lambda s:s['phase']=='spell-target'or s['spell_returns']!=old)
   def save(toolbar=False):
    old=state()['saves']
    if toolbar:
     dx=C.c_int();dy=C.c_int();child=C.c_ulong();assert x.XTranslateCoordinates(display,window,window_root,1530,20,C.byref(dx),C.byref(dy),C.byref(child));inputs.append(dict(toolbar='F7',root_xy=[dx.value,dy.value],before=state()));xt.XTestFakeMotionEvent(display,0,dx.value,dy.value,0);xt.XTestFakeButtonEvent(display,1,1,0);x.XFlush(display);time.sleep(.04);xt.XTestFakeButtonEvent(display,1,0,0);x.XFlush(display)
    else:key(0xffc4)
    s=wait(lambda s:s['saves']!=old);assert(store/'battle.chk').is_file();time.sleep(1.3);return state()
   def to_win():
    for _ in range(180):
     s=wait(lambda s:s['actor']=='player'or s['outcome']!='active')
     if s['outcome']!='active':return s
     goto(int(s['legal'].split(',')[0])+1);old=s['sequence'];key(0xff0d);wait(lambda s:s['sequence']!=old or s['outcome']!='active')
    raise AssertionError('victory budget')
   if name=='ordinary-control':
    key(0xffc7);wait(lambda s:s['font']=='lishu');key(ord('m'));wait(lambda s:s['music']=='off');goto(1);anchor=save(True);capture('saved-wait');ordinary_anchor=anchor['checkpoint_hash'];ordinary_frame=captures[-1]['captured']['frame_hash'];final=to_win();assert final['outcome']=='win';capture('control-win');ordinary_final=final['checkpoint_hash']
   elif name=='ordinary-continue':
    time.sleep(1.3);assert state()['loaded']=='true'and state()['checkpoint_hash']==ordinary_anchor;capture('cold-wait');assert captures[-1]['captured']['frame_hash']==ordinary_frame;final=to_win();assert final['checkpoint_hash']==ordinary_final;capture('cold-win')
   else:
    if name=='support-control':
     menu();select(6);goto(7);old=state()['spell_returns'];key(0xff0d);wait(lambda s:s['spell_returns']!=old);menu();select(4);assert state()['fx']=='true';anchor=save();assert anchor['phase']=='ordinary';capture('freeze-saved');extra_anchor=anchor['checkpoint_hash'];extra_frame=captures[-1]['captured']['frame_hash'];extra_store=base/'extra-store';extra_store.mkdir();shutil.copy2(store/'battle.chk',extra_store/'battle.chk')
    elif name=='extra-continue':
     time.sleep(1.3);assert state()['checkpoint_hash']==extra_anchor;capture('freeze-cold');assert captures[-1]['captured']['frame_hash']==extra_frame
    if name!='paid-continue':
     menu();select(0);goto(1)
     if name=='support-control':
      anchor=save();assert anchor['phase']=='spell-target'and anchor['charges'].split(',')[0]=='2';capture('paid-saved');paid_anchor=anchor['checkpoint_hash'];paid_frame=captures[-1]['captured']['frame_hash'];paid_store=base/'paid-store';paid_store.mkdir();shutil.copy2(store/'battle.chk',paid_store/'battle.chk')
    else:
     time.sleep(1.3);assert state()['checkpoint_hash']==paid_anchor;capture('paid-cold');assert captures[-1]['captured']['frame_hash']==paid_frame
    old=state()['spell_returns'];key(32);wait(lambda s:s['spell_returns']!=old);assert state()['charges'].split(',')[0]=='3';menu();key(0xff1b);final=wait(lambda s:s['outcome']=='retreat');capture('refund-retreat')
    if name=='support-control':support_final=final['checkpoint_hash']
    else:assert final['checkpoint_hash']==support_final
   x.XInternAtom.argtypes=[C.c_void_p,C.c_char_p,C.c_int];x.XInternAtom.restype=C.c_ulong
   class Data(C.Union):_fields_=[('b',C.c_char*20),('s',C.c_short*10),('l',C.c_long*5)]
   class Client(C.Structure):_fields_=[('type',C.c_int),('serial',C.c_ulong),('send',C.c_int),('display',C.c_void_p),('window',C.c_ulong),('message',C.c_ulong),('format',C.c_int),('data',Data)]
   class Event(C.Union):_fields_=[('client',Client),('pad',C.c_long*24)]
   event=Event();event.client.type=33;event.client.display=display;event.client.window=window;event.client.message=x.XInternAtom(display,b'WM_PROTOCOLS',0);event.client.format=32;event.client.data.l[0]=x.XInternAtom(display,b'WM_DELETE_WINDOW',0)
   x.XSendEvent.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_long,C.c_void_p];x.XSendEvent(display,window,0,0,C.byref(event));x.XFlush(display);exit_code=app.wait(timeout=10);assert exit_code==0;log.close();log=None
   runs.append(dict(name=name,command=cmd,initial_seed=305419896 if name.endswith('control')else'saved seed',inputs=inputs,captures=captures,final=final,exit=exit_code))
  receipt=dict(status='passed-rust-checkpoint-gui',binary_sha256=hashlib.sha256((root/'8sword-remake').read_bytes()).hexdigest(),runs=runs,checkpoint_files={str(p.relative_to(base)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())for p in base.glob('*-store/battle.chk')},controlled_memory_or_ip=False)
  (base/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
 finally:
  if app and app.poll()is None:app.terminate();app.wait(timeout=5)
  if log:log.close()
  xvfb.terminate();xvfb.wait(timeout=5)
if __name__=='__main__':main()
