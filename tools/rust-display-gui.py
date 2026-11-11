#!/usr/bin/env python3
"""Rust策略AI切換、選敵與冷讀抽驗。限Docker。"""
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
  for name in os.environ.get('RUST_DISPLAY_CASES','world,world-cold,battle,battle-cold,openkb,intro,ending').split(','):
   d=base/name;d.mkdir();store=base/(name+'-store');store.mkdir();log=(d/'player.log').open('w')
   mode='--play' if name in ['world','intro'] else '--battle' if name in ['battle','battle-cold','openkb'] else '--journey'
   cmd=[str(r/'8sword-remake'),mode,'--assets',str(r/'pack'),'--capture-dir',str(d),'--scale','1','--save-dir',str(store)]
   if name=='world':shutil.copy2(r/'legacy-v16.chk',store/'journey.chk');cmd+=['--skip-intro']
   elif name=='intro':cmd+=['--seed','1','--display','original']
   elif name=='ending':shutil.copy2(r/'legacy-ending.chk',store/'journey.chk');cmd+=['--continue']
   elif name.endswith('-cold'):
    source=base/(name.replace('-cold','')+'-store')
    for p in source.iterdir():
     if p.is_file():shutil.copy2(p,store/p.name)
    cmd+=['--continue']
   else:
    source=r/('openkb-fixture' if name=='openkb' else 'fixture')
    for p in source.iterdir():shutil.copy2(p,store/p.name)
    cmd+=['--continue']
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
   def save():
    old=state()['saves'];click(1644,1296);wait(lambda s:s['saves']!=old);assert(store/'journey.chk').read_bytes()[:8]==b'8SJRN016'

   assert state()
   def mode(i):
    click(2800,20);click(2600,74+i*48)
    if 'battle_ai'in state():wait(lambda s:s['battle_ai']==['native','target'][i])
   def center(px,py):click(px+512,py)
   def first_enemy_hit():
    for _ in range(16):
     if int(state()['sequence'])>=1:break
     wait(lambda s:s.get('actor')=='player'or int(s['sequence'])>=1)
     if int(state()['sequence'])>=1:break
     key(32,pause=.30)
    return wait(lambda s:int(s['sequence'])>=1)
   def image_mode(wanted,stable=True):
    before=state();
    if before['display_mode']!=wanted:click(2600,1296);wait(lambda s:s['display_mode']==wanted)
    after=state();
    if stable:
     for k in ['state_hash','checkpoint_hash','seed','army','steps','gold','sequence']:
      if k in before:assert before[k]==after[k],(name,k,before[k],after[k])
    return after
   def f7():
    before=state()['saves'];key(0xffc4);wait(lambda s:s['saves']!=before);time.sleep(1.4)
   def settled():wait(lambda s:s.get('actor')=='player'or s.get('outcome','None')!='None');time.sleep(1.4)
   if name=='world':
    wait(lambda s:s['phase']=='start');image_mode('original');capture('start-original');key(0xff0d);wait(lambda s:s['phase']=='world');time.sleep(1.4)
    capture('world-original');image_mode('hd');anchors['world-hd']=capture('world-hd');image_mode('original');
    key(0xffbe);wait(lambda s:s.get('phase')=='character');capture('character-original');image_mode('hd');capture('character-hd');key(0xffc7);wait(lambda s:s['font']=='1');image_mode('original');key(0xff1b);wait(lambda s:s['phase']=='world')
    key(0xffbf);wait(lambda s:s['phase']=='review');capture('army-original');image_mode('hd');capture('army-hd');image_mode('original');key(0xff1b);wait(lambda s:s['phase']=='world')
    # True v16 is one step east of the original new-game origin.
    for symbol in [0xff51,0xff52,0xff52,0xff51]:key(symbol)
    wait(lambda s:s['phase']=='camp');capture('camp-original');image_mode('hd');capture('camp-hd');image_mode('original');key(0xff0d);wait(lambda s:s['phase']=='quantity');key(49);key(0xff0d);wait(lambda s:s['army'].startswith('31,'));capture('purchased-original');key(0xff1b);wait(lambda s:s['phase']=='camp');key(0xff1b);wait(lambda s:s['phase']=='world');f7();anchors['world-saved']=capture('world-saved')
   elif name=='world-cold':
    wait(lambda s:s['phase']=='world');time.sleep(1.4);assert state()['display_mode']=='original';cap=capture('cold-original');assert cap['state_hash']==anchors['world-saved']['state_hash']and cap['frame_hash']==anchors['world-saved']['frame_hash']
   elif name in ['battle','openkb']:
    settled();hd=capture('battle-hd');image_mode('original');capture('battle-original');image_mode('hd');again=capture('battle-hd-return');assert hd['checkpoint_hash']==again['checkpoint_hash']and hd['frame_hash']==again['frame_hash']
    if name=='battle':
     image_mode('original');mode(1);assert state()['battle_rules']=='formation'and state()['rules_locked']=='true';first_enemy_hit();settled();capture('hit-original');image_mode('hd');anchors['battle-hit-hd']=capture('hit-hd');image_mode('original');f7();anchors['battle-saved']=capture('battle-saved')
   elif name=='battle-cold':
    settled();assert state()['display_mode']=='original'and state()['battle_rules']=='formation';cap=capture('cold-original');assert cap['checkpoint_hash']==anchors['battle-saved']['checkpoint_hash']and cap['frame_hash']==anchors['battle-saved']['frame_hash'];image_mode('hd');cap=capture('cold-hd');assert cap['frame_hash']==anchors['battle-hit-hd']['frame_hash'];image_mode('original')
   elif name=='intro':
    wait(lambda s:s.get('stage')=='museum-portrait');time.sleep(.18);assert state()['display_mode']=='original'and state()['hd']=='false';capture('portrait-original');image_mode('hd',False);capture('portrait-hd');key(104);wait(lambda s:s['display_mode']=='original');key(0xff1b);wait(lambda s:s['phase']=='start');capture('start-inherited-original')
   elif name=='ending':
    wait(lambda s:s['phase']=='ending');assert state()['ending_hd']=='false'and state()['display_mode']=='original';capture('ending-original');resources=state()['resources'];steps=state()['steps'];image_mode('hd',False);wait(lambda s:s['ending_hd']=='true');capture('ending-hd');key(104);wait(lambda s:s['ending_hd']=='false');assert state()['resources']==resources and state()['steps']==steps;f7();capture('ending-saved-original')
   final=state();event=Event();event.client.type=33;event.client.display=display;event.client.window=window;event.client.message=x.XInternAtom(display,b'WM_PROTOCOLS',0);event.client.format=32;event.client.data.l[0]=x.XInternAtom(display,b'WM_DELETE_WINDOW',0);x.XSendEvent(display,window,0,0,C.byref(event));x.XFlush(display);code=app.wait(timeout=10);assert code==0;log.close();log=None;runs.append(dict(name=name,exit=code,command=cmd,inputs=inputs,captures=captures,final=final));app=None
   (base/'completed-runs.json').write_text(json.dumps(runs,ensure_ascii=False,indent=2)+'\n')
  (base/'receipt.json').write_text(json.dumps(dict(status='passed-rust-display-gui',binary_sha256=hashlib.sha256((r/'8sword-remake').read_bytes()).hexdigest(),runs=runs,no_runtime_memory_or_ip_injection=True,scope='True v16 normal Continue/F1/F2/camp/purchase/F7/cold; explicit formation battle and OpenKB AI fixture; archived real v15 ending checkpoint; normal opening. Original pictures with shared native UI/fonts, no full-DOS-frame parity claim.'),ensure_ascii=False,indent=2)+'\n')
 finally:
  if app and app.poll()is None:app.terminate();app.wait(timeout=5)
  if log:log.close()
  xvfb.terminate();xvfb.wait(timeout=5)
if __name__=='__main__':main()
