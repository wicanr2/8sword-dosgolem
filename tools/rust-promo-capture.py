#!/usr/bin/env python3
"""現行Rust推廣影片實錄；原圖、HD正常新建與受控法術分開標示。限Docker。"""
import ctypes as C
import hashlib,json,os,shutil,subprocess,time,sys
from pathlib import Path
def main():
 assert Path('/.dockerenv').exists()and os.getuid()==1000
 r=Path('/runtime');base=Path('/out/capture');base.mkdir(exist_ok=True);runs=[];app=None;log=None;rec=None;rec_log=None
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
  if '--effects-only'in sys.argv:runs=json.loads((base/'completed-runs.json').read_text());assert len(runs)==2
  if '--continue-only'in sys.argv:runs=json.loads((base/'completed-runs.json').read_text());assert len(runs)==3
  for name in (['continued']if '--continue-only'in sys.argv else ['effects']if '--effects-only'in sys.argv else['original','hd','effects','continued']):
   d=base/name;d.mkdir();store=base/(name+'-store');store.mkdir();log=(d/'player.log').open('w')
   cmd=[str(r/'8sword-remake'),'--battle'if name=='effects'else'--play','--assets',str(r/'pack'),'--capture-dir',str(d),'--scale','1','--save-dir',str(store),'--seed','1','--display','original'if name=='original'else'hd']
   if name=='effects':cmd+=['--spells','--taoist']
   if name=='continued':
    cmd=cmd[:cmd.index('--seed')]+['--display','hd']
    source=r/'gui/battle-cold-store'
    for p in source.iterdir():
     if p.is_file():shutil.copy2(p,store/p.name)
    assert (store/'journey.chk').read_bytes()[:8]==b'8SJRN018'
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
    old=state()['saves'];key(0xffc4);wait(lambda s:s['saves']!=old);assert(store/'journey.chk').read_bytes()[:8]==b'8SJRN018'
   rec_log=(d/'recorder.log').open('w');record_start=time.monotonic();rec_cmd=['ffmpeg','-y','-hide_banner','-loglevel','warning','-f','x11grab','-framerate','30','-video_size','2944x1320','-draw_mouse','1','-i',f':97.0+{ox.value},{oy.value}','-an','-c:v','libx264','-preset','ultrafast','-crf','18','-threads','2','-pix_fmt','yuv420p',str(d/'live.mp4')]
   rec=subprocess.Popen(rec_cmd,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=rec_log);time.sleep(.6);markers=[]
   def mark(label):markers.append(dict(label=label,seconds=round(time.monotonic()-record_start,3),state=state()))
   def hold(seconds):
    mark('hold');end=time.monotonic()+seconds
    while time.monotonic()<end:
     assert rec.poll()is None;state();time.sleep(.05)
   def walk(symbol):
    v=state();assert v['phase']=='world';key(symbol,.06);wait(lambda s:s['phase']!='world'or s['actions']!=v['actions'])
   def attack():
    v=wait(lambda s:s['outcome']!='None'or s['actor']=='player')
    if v['outcome']!='None':return
    target=int(v['targets'].split(',')[0]);positions=[(948,498),(948,798),(948,1098),(1212,648),(1212,948),(1476,798)];time.sleep(.22);center(*positions[target]);key(0xff0d,.08);wait(lambda s:int(s['sequence'])>int(v['sequence'])or s['outcome']!='None')
   if name in ['original','hd']:
    mark('intro-start');wait(lambda s:s['phase']=='start',45);mark('menu');hold(1);key(0xff54);key(0xff0d);wait(lambda s:s['phase']=='new-confirm');center(200,1295);wait(lambda s:s['phase']=='world');mark('world-start');capture('new-world');hold(2)
    walk(0xff52);hold(1);walk(0xff52);hold(1);walk(0xff51);wait(lambda s:s['phase']=='camp');mark('recruit-start');capture('camp')
    if name=='original':hold(4)
    else:
     center(200,1295);key(54);key(48);center(200,1295);wait(lambda s:s['army']=='90,0,0,0,0,0');key(0xff1b);center(660,768);center(612,858);center(200,1295);key(49);center(200,1295);wait(lambda s:s['army']=='90,1,0,0,0,0');capture('female-archer');hold(3);key(0xff1b);key(0xff1b);wait(lambda s:s['phase']=='world');key(0xffbf);wait(lambda s:s['phase']=='review');hold(2);mark('settings-start')
     center(450,20);hold(2);center(708,20);hold(2);center(252,20);hold(1)
     click(2570,24);hold(.6);click(2680,122);hold(2);click(2570,24);click(2680,74);hold(1)
     click(2660,1295);hold(2);click(2660,1295);hold(2);capture('hd-restored');key(0xff1b);wait(lambda s:s['phase']=='world')
     mark('choices-start');click(200,24);hold(2);key(0xff1b);click(2810,24);hold(2);click(2680,122);wait(lambda s:s['battle_ai']=='target');hold(1);click(2810,24);click(2680,74);wait(lambda s:s['battle_ai']=='native');capture('choices')
     for symbol in [0xff53,0xff54,0xff54]:
      if state()['phase']!='world':break
      walk(symbol)
     for _ in range(150):
      if state()['phase']=='prompt':break
      walk(0xff54 if state()['y']=='40'else 0xff52)
     wait(lambda s:s['phase']=='prompt');mark('natural-encounter');hold(1);center(360,900);center(200,1295);wait(lambda s:s['phase']=='battle'and s['actor']=='player');mark('battle-start');capture('natural-battle');hold(2)
     for _ in range(150):
      if state()['outcome']!='None':break
      attack()
     assert state()['outcome']=='Some(Win)';mark('battle-win');capture('normal-win');hold(2);key(0xff0d);wait(lambda s:s['phase']=='world');mark('closing-start');key(0xffc4);hold(1);key(0xffbe);hold(2);key(0xff1b);key(0xffc2);hold(2);key(0xff1b);capture('world-saved');hold(4)
   elif name=='continued':
    for _ in range(4):
     if state().get('phase')!='intro':break
     key(0xff1b)
    wait(lambda s:s['phase']=='start');mark('continue-menu');hold(1);center(200,1295);wait(lambda s:s['phase']=='monthly');assert state()['gold']=='176'and state()['army']=='83,0,0,0,0,0';mark('monthly-view');capture('real-monthly-continued');hold(4);key(0xff0d);wait(lambda s:s['phase']=='world');mark('continued-world');key(0xffc4);capture('continued-world-saved');hold(3)
   else:
    wait(lambda s:s['actor']=='player');mark('effects-start')
    def goto(node):
     from collections import deque
     nav=[[0,0,0,0],[0,2,7,4],[1,3,8,4],[2,0,9,5],[0,5,2,6],[4,0,2,6],[0,0,5,0],[0,8,10,1],[7,9,10,2],[8,0,11,3],[0,11,12,8],[10,0,12,8],[0,0,0,11]]
     todo=deque([(int(state()['cursor']),[])]);seen=set()
     while todo:
      n,path=todo.popleft()
      if n==node:break
      if n in seen:continue
      seen.add(n)
      for direction,nxt in enumerate(nav[n]):
       if nxt:todo.append((nxt,path+[(direction,nxt)]))
     else:raise AssertionError('target route')
     for direction,nxt in path:key([0xff52,0xff54,0xff51,0xff53][direction]);wait(lambda s:int(s['cursor'])==nxt)
    def menu():
     for _ in range(80):
      v=wait(lambda s:s['outcome']!='active'or s['actor']=='player');assert v['outcome']=='active'
      if v['phase']=='spell-menu':return
      before=(v['half_turn'],v['raw'],v['phase'],v['spell_returns']);key(32);wait(lambda s:s['outcome']!='active'or(s['half_turn'],s['raw'],s['phase'],s['spell_returns'])!=before)
     raise AssertionError('spell-menu budget')
    for selector in [0,1,4]:
     menu();mark('spell-menu-'+str(selector));hold(1)
     while int(state()['spell_cursor'])!=selector:key(0xff54)
     before=state()['spell_returns'];key(0xff0d)
     if state()['phase']=='spell-target':
      target=int(state()['legal'].split(',')[0]);goto(target+1);key(0xff0d,.07)
     wait(lambda s:s['spell_returns']!=before);mark('spell-cast-'+str(selector));hold(1.4)
    capture('effects');hold(2)
   mark('record-end');rec.stdin.write(b'q\n');rec.stdin.flush();assert rec.wait(timeout=20)==0;rec=None;rec_log.close();rec_log=None
   final=state();event=Event();event.client.type=33;event.client.display=display;event.client.window=window;event.client.message=x.XInternAtom(display,b'WM_PROTOCOLS',0);event.client.format=32;event.client.data.l[0]=x.XInternAtom(display,b'WM_DELETE_WINDOW',0);x.XSendEvent(display,window,0,0,C.byref(event));x.XFlush(display);code=app.wait(timeout=10);assert code==0;log.close();log=None;runs.append(dict(name=name,exit=code,command=cmd,inputs=inputs,captures=captures,final=final,markers=markers,recorder_command=rec_cmd));app=None
   (base/'completed-runs.json').write_text(json.dumps(runs,ensure_ascii=False,indent=2)+'\n')
  (base/'receipt.json').write_text(json.dumps(dict(status='passed-rust-promo-live-capture',binary_sha256=hashlib.sha256((r/'8sword-remake').read_bytes()).hexdigest(),runs=runs,fixed_seed=1,no_runtime_memory_or_ip_injection=True,scope='Current native Rust client recorded live with X11 keyboard/mouse. Original means native original-asset display; HD play starts normally, buys real militia/archer and wins a natural encounter; effects are the explicit existing battle sample. Continuation reloads the actual v18 month-end checkpoint from the prior current-binary normal-player-path sample; no injected state. Audio later uses actual approved in-game HD music with synthetic narration.'),ensure_ascii=False,indent=2)+'\n')

 finally:
  if rec and rec.poll()is None:rec.terminate();rec.wait(timeout=5)
  if rec_log:rec_log.close()
  if app and app.poll()is None:app.terminate();app.wait(timeout=5)
  if log:log.close()
  xvfb.terminate();xvfb.wait(timeout=5)
if __name__=='__main__':main()
