#!/usr/bin/env python3
"""現行Rust正常新遊戲至月結的連續路徑抽驗。限Docker。"""
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
  for name in ['fresh','camp-cold','battle-cold','month-cold']:
   d=base/name;d.mkdir();store=base/(name+'-store');store.mkdir();log=(d/'player.log').open('w')
   if name!='fresh':
    source=base/({'camp-cold':'fresh','battle-cold':'camp-cold','month-cold':'battle-cold'}[name]+'-store')
    for p in source.iterdir():
     if p.is_file():shutil.copy2(p,store/p.name)
   cmd=[str(r/'8sword-remake'),'--play','--assets',str(r/'pack'),'--capture-dir',str(d),'--scale','1','--save-dir',str(store)]
   if name=='fresh':cmd.extend(['--seed','1'])
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
   wait(lambda s:'phase'in s);rr=C.c_ulong();parent=C.c_ulong();children=C.POINTER(C.c_ulong)();n=C.c_uint();assert x.XQueryTree(display,root,C.byref(rr),C.byref(parent),C.byref(children),C.byref(n));found=[]
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
    old=state()['saves'];key(0xffc4);wait(lambda s:s['saves']!=old);assert(store/'journey.chk').read_bytes()[:8]==b'8SJRN018'
   def enter_world():
    if name!='fresh':
     for _ in range(4):
      if state()['phase']!='intro':break
      key(0xff1b)
    wait(lambda s:s['phase']=='start',40)
    if name=='fresh':
     key(0xff54);key(0xff0d);wait(lambda s:s['phase']=='new-confirm');center(200,1295)
    else:center(200,1295)
   def clear_encounter():
    if state()['phase']=='theft':key(0xff0d)
    if state()['phase']=='prompt':
     key(0xff0d);wait(lambda s:s['phase']=='battle'and s['actor']=='player');key(0xff1b);wait(lambda s:s['outcome']=='Some(Retreat)');time.sleep(.25);key(0xff0d);wait(lambda s:s['phase']=='world')
   def walk(symbol):
    v=state();assert v['phase']=='world'and v['pending']=='None';key(symbol,.06);wait(lambda s:s['phase']!='world'or s['actions']!=v['actions'])
   def attack():
    s=wait(lambda s:s['outcome']!='None'or s['actor']=='player')
    if s['outcome']!='None':return
    assert s['spell_phase']=='ordinary';target=int(s['targets'].split(',')[0]);positions=[(948,498),(948,798),(948,1098),(1212,648),(1212,948),(1476,798)]
    time.sleep(.22);center(*positions[target]);key(0xff0d,.07);wait(lambda v:int(v['sequence'])>int(s['sequence'])or v['outcome']!='None')
   enter_world()
   if name=='fresh':
    wait(lambda s:s['phase']=='world');assert state()['resources']=='1,0,100,500,100,0'and state()['army']=='30,0,0,0,0,0'and state()['x']=='40'and state()['y']=='40';capture('new-game')
    walk(0xff52);walk(0xff52);walk(0xff51);wait(lambda s:s['phase']=='camp');center(200,1295);key(54);key(48);center(200,1295);wait(lambda s:s['army']=='90,0,0,0,0,0'and s['gold']=='440');key(0xff1b)
    center(660,768);wait(lambda s:s['extra']=='true');center(612,858);wait(lambda s:s['selected']=='0');center(200,1295);key(49);center(200,1295);wait(lambda s:s['army']=='90,1,0,0,0,0'and s['gold']=='190');key(0xff1b);save();capture('native-and-openkb-purchased');anchors['camp']=state()['state_hash']
   elif name=='camp-cold':
    wait(lambda s:s['phase']=='camp');assert state()['state_hash']==anchors['camp'];capture('camp-cold');key(0xff1b);wait(lambda s:s['phase']=='world')
    for symbol in [0xff53,0xff54,0xff54]:
     if state()['phase']!='world':break
     walk(symbol)
    for _ in range(150):
     if state()['phase']=='prompt':break
     walk(0xff54 if state()['y']=='40'else 0xff52)
    wait(lambda s:s['phase']=='prompt');capture('natural-encounter');center(360,900);center(200,1295);wait(lambda s:s['phase']=='battle'and s['actor']=='player');attack();wait(lambda s:s['outcome']!='None'or s['actor']=='player');save();capture('battle-saved');anchors['battle']=state()['state_hash']
   elif name=='battle-cold':
    wait(lambda s:s['phase']=='battle');assert state()['state_hash']==anchors['battle'];capture('battle-cold')
    for _ in range(150):
     if state()['outcome']!='None':break
     attack()
    assert state()['outcome'] in ['Some(Win)','Some(Loss)','Some(Retreat)'];anchors['outcome']=state()['outcome'];capture('natural-battle-result');time.sleep(.25);key(0xff0d);wait(lambda s:s['phase']=='world');capture('natural-return')
    rows=[int(v)for v in state()['army'].split(',')]
    if rows[1]>0:
     key(0xffc0);wait(lambda s:s['phase']=='dismiss');key(0xff54);key(0xff0d);key(0xff1b);wait(lambda s:s['phase']=='world')
    for _ in range(4):
     clear_encounter()
     if state()['y']=='40':break
     walk(0xff54 if int(state()['y'])<40 else 0xff52)
    for _ in range(400):
     clear_encounter();v=state()
     if v['phase']=='monthly':break
     walk(0xff54 if v['y']=='40'else 0xff52)
    wait(lambda s:s['phase']=='monthly');assert state()['months']=='1'and state()['steps']=='324';save();capture('normal-monthly-saved');anchors['month']=state()['state_hash']
   else:
    wait(lambda s:s['phase']=='monthly');assert state()['state_hash']==anchors['month'];capture('monthly-cold');key(0xff0d);wait(lambda s:s['phase']!='monthly');clear_encounter();assert state()['months']=='1'and state()['wait_event']=='None';key(0xffbe);wait(lambda s:s['phase']=='character');capture('character-after-month');key(0xff1b);key(0xffbf);wait(lambda s:s['phase']=='review');capture('army-after-month');key(0xff1b);key(0xffc2);wait(lambda s:s['phase']=='minimap');capture('explored-map');key(0xff1b);wait(lambda s:s['phase']=='world');save();capture('completed-normal-path')
   final=state();event=Event();event.client.type=33;event.client.display=display;event.client.window=window;event.client.message=x.XInternAtom(display,b'WM_PROTOCOLS',0);event.client.format=32;event.client.data.l[0]=x.XInternAtom(display,b'WM_DELETE_WINDOW',0);x.XSendEvent(display,window,0,0,C.byref(event));x.XFlush(display);code=app.wait(timeout=10);assert code==0;log.close();log=None;runs.append(dict(name=name,exit=code,command=cmd,inputs=inputs,captures=captures,final=final));app=None
   (base/'completed-runs.json').write_text(json.dumps(runs,ensure_ascii=False,indent=2)+'\n')
  (base/'receipt.json').write_text(json.dumps(dict(status='passed-rust-player-path-gui',binary_sha256=hashlib.sha256((r/'8sword-remake').read_bytes()).hexdigest(),runs=runs,no_runtime_memory_or_ip_injection=True,fixed_seed=1,actual_first_battle_outcome=anchors['outcome'],scope='Current unchanged v18 binary, full first intro and normal new game from 500 gold and 30 militia. Only keyboard/mouse purchase, original camp plus OpenKB archer, natural encounter, battle continuation and real month-end. No coordinate/resource/army/RAM/IP injection or forced outcome. Later intros skipped with normal Esc. Not a full campaign or new DOS oracle.'),ensure_ascii=False,indent=2)+'\n')
 finally:
  if app and app.poll()is None:app.terminate();app.wait(timeout=5)
  if log:log.close()
  xvfb.terminate();xvfb.wait(timeout=5)
if __name__=='__main__':main()
