#!/usr/bin/env python3
"""Rust玩家法術的有界X11輸入抽驗；不寫遊戲記憶體。"""
import ctypes as C
import hashlib,json,os,subprocess,time
from pathlib import Path
from collections import deque
NAV=[[0,0,0,0],[0,2,7,4],[1,3,8,4],[2,0,9,5],[0,5,2,6],[4,0,2,6],[0,0,5,0],[0,8,10,1],[7,9,10,2],[8,0,11,3],[0,11,12,8],[10,0,12,8],[0,0,0,11]]
KEYS=[0xff52,0xff54,0xff51,0xff53]
def main():
 assert Path('/.dockerenv').exists() and os.getuid()==1000
 q=Path('/out');folder=q/'gui-r3';folder.mkdir()
 os.environ.update(DISPLAY=':97',SDL_AUDIODRIVER='dummy',SDL_RENDER_DRIVER='software')
 xvfb=subprocess.Popen(['Xvfb',':97','-screen','0','2000x1400x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 app=None;logs=[];receipts=[]
 try:
  time.sleep(.5);x=C.CDLL('libX11.so.6');xt=C.CDLL('libXtst.so.6')
  x.XOpenDisplay.argtypes=[C.c_char_p];x.XOpenDisplay.restype=C.c_void_p;display=x.XOpenDisplay(None);assert display
  x.XDefaultRootWindow.argtypes=[C.c_void_p];x.XDefaultRootWindow.restype=C.c_ulong;root=x.XDefaultRootWindow(display)
  x.XQueryTree.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_ulong),C.POINTER(C.c_ulong),C.POINTER(C.POINTER(C.c_ulong)),C.POINTER(C.c_uint)]
  x.XFetchName.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_char_p)];x.XFree.argtypes=[C.c_void_p]
  x.XSetInputFocus.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_ulong];x.XFlush.argtypes=[C.c_void_p]
  x.XKeysymToKeycode.argtypes=[C.c_void_p,C.c_ulong];x.XKeysymToKeycode.restype=C.c_uint
  xt.XTestFakeKeyEvent.argtypes=[C.c_void_p,C.c_uint,C.c_int,C.c_ulong]
  for mode in ['fireball-win','support','target-esc']:
   d=folder/mode;d.mkdir();log=(d/'player.log').open('w');logs.append(log)
   cmd=['/out/8sword-remake','--battle','--assets','/out/pack','--spells','--capture-dir',str(d),'--scale','1','--seed','305419896']
   if mode=='support':cmd+=['--taoist']
   app=subprocess.Popen(cmd,stdout=log,stderr=log)
   def state():
    assert app.poll() is None,(app.returncode,(d/'player.log').read_text())
    try:return dict(line.split('\t',1)for line in(d/'status.tsv').read_text().splitlines())
    except FileNotFoundError:return {}
   def wait(pred,seconds=20):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
     s=state()
     if s and pred(s):return s
     time.sleep(.04)
    raise AssertionError((mode,'timeout',state()))
   wait(lambda s:s['actor']=='player')
   rr=C.c_ulong();parent=C.c_ulong();children=C.POINTER(C.c_ulong)();count=C.c_uint();found=[]
   assert x.XQueryTree(display,root,C.byref(rr),C.byref(parent),C.byref(children),C.byref(count))
   for i in range(count.value):
    name=C.c_char_p()
    if x.XFetchName(display,children[i],C.byref(name))and name.value:
     if b'Rust'in name.value:found.append(children[i])
     x.XFree(name)
   x.XFree(children);assert len(found)==1;window=found[0];x.XSetInputFocus(display,window,1,0);x.XFlush(display)
   inputs=[];captures=[]
   def key(symbol):
    code=x.XKeysymToKeycode(display,symbol);assert code
    inputs.append(dict(key=symbol,before=state()))
    xt.XTestFakeKeyEvent(display,code,1,0);x.XFlush(display);time.sleep(.06)
    xt.XTestFakeKeyEvent(display,code,0,0);x.XFlush(display);time.sleep(.11)
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
   def capture(label):
    n=int(state()['captures']);key(0xffc9);s=wait(lambda s:int(s['captures'])>n);assert s['readback_equal']=='true';captured=dict(line.split('\t',1)for line in(d/f"capture-{int(s['captures']):03}.tsv").read_text().splitlines());captures.append(dict(label=label,status=s,captured=captured))
   def next_player():return wait(lambda s:s['outcome']!='active' or s['actor']=='player')
   def skip_actor():
    marker=lambda s:(s['half_turn'],s['raw'],s['phase'],s['spell_returns'])
    old=marker(state());key(32);wait(lambda s:s['outcome']!='active' or marker(s)!=old)
   def to_menu(attack):
    for _ in range(150):
     s=next_player()
     assert s['outcome']=='active',s
     if s['phase']=='spell-menu':return s
     assert s['phase']=='ordinary',s
     if attack:
      goto(int(s['legal'].split(',')[0])+1);seq=s['sequence'];key(0xff0d);wait(lambda v:v['sequence']!=seq or v['outcome']!='active')
     else:skip_actor()
    raise AssertionError('menu budget')
   def select(selector):
    wait(lambda s:s['phase']=='spell-menu')
    while int(state()['spell_cursor'])!=selector:
     old=int(state()['spell_cursor']);key(0xff54);wait(lambda s:int(s['spell_cursor'])!=old)
    old=state()['spell_returns'];key(0xff0d)
    return wait(lambda s:s['phase']=='spell-target' or s['spell_returns']!=old)
   def cast(selector,target=None):
    before=state()['spell_returns'];s=select(selector)
    if s['phase']=='spell-target':
     goto(target if target is not None else int(s['legal'].split(',')[0])+(7 if selector==6 else 1));key(0xff0d)
    return wait(lambda s:s['spell_returns']!=before)
   if mode=='fireball-win':
    to_menu(True);capture('menu-noto');key(0xffc7);wait(lambda s:s['font']=='lishu');capture('menu-lishu');key(0xffc7);wait(lambda s:s['font']=='caoshu');capture('menu-caoshu');key(0xffc7)
    cast(0);capture('fireball-impact')
    for _ in range(150):
     s=next_player()
     if s['outcome']!='active':break
     if s['phase']=='spell-menu':skip_actor()
     else:
      goto(int(s['legal'].split(',')[0])+1);seq=s['sequence'];key(0xff0d);wait(lambda v:v['sequence']!=seq or v['outcome']!='active')
    else:raise AssertionError('victory budget')
    final=wait(lambda s:s['outcome']=='win');assert final['charges'].split(',')[0]=='2';capture('win')
   elif mode=='support':
    to_menu(False);cast(6,7);capture('clone');to_menu(False);cast(4);capture('freeze');to_menu(False);cast(1);capture('thunder')
    to_menu(False);select(0);wait(lambda s:s['phase']=='spell-target');old=state()['spell_returns'];key(32);wait(lambda s:s['spell_returns']!=old);to_menu(False);assert state()['charges']=='3,2,3,3,2,3,2,3',state();capture('target-space-refund');key(0xff1b);wait(lambda s:s['outcome']=='retreat');capture('menu-esc')
   else:
    to_menu(False);select(0);wait(lambda s:s['phase']=='spell-target');key(0xff1b);final=wait(lambda s:s['outcome']=='retreat');assert final['charges']=='2,3,3,3,3,3,3,3';capture('target-esc')
   final=state();key(0xff1b);assert app.wait(5)==0;app=None;log.close()
   receipts.append(dict(mode=mode,command=cmd,captures=captures,final=final,inputs=inputs,exit=0))
  (folder/'receipt.json').write_text(json.dumps(dict(status='passed-rust-player-spells-gui',binary_sha256=hashlib.sha256((q/'8sword-remake').read_bytes()).hexdigest(),rows=receipts,input='XTest keyboard only; no RAM, IP or state injection',scope='Explicit spell rosters; no world or native save acceptance'),ensure_ascii=False,indent=2)+'\n')
 finally:
  if app is not None and app.poll() is None:app.terminate();app.wait(5)
  xvfb.terminate();xvfb.wait(5)
  for log in logs:log.close()
if __name__=='__main__':main()
