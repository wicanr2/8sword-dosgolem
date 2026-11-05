#!/usr/bin/env python3
"""停時／鳥瞰：原式商店、F4、一次延長與暫時全圖冷讀。"""
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
  for name in ['stop','stop-cold','bird','bird-cold']:
   d=base/name;d.mkdir();store=base/(name+'-store');store.mkdir();log=(d/'player.log').open('w');cmd=[str(r/'8sword-remake'),'--journey','--assets',str(r/'pack'),'--capture-dir',str(d),'--scale','1','--save-dir',str(store)]
   if name=='bird':
    subprocess.run([str(r/'survey-fixture'),str(r/'pack'),str(base/'stop-cold-store/journey.chk'),str(r/'fixture-bird'),'bird'],check=True,timeout=10)
   src={'stop':r/'fixture-stop/journey.chk','stop-cold':base/'stop-store/journey.chk','bird':r/'fixture-bird/journey.chk','bird-cold':base/'bird-store/journey.chk'}[name]
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
    code=x.XKeysymToKeycode(display,symbol);assert code;inputs.append(dict(diagnostic_key=symbol));xt.XTestFakeKeyEvent(display,code,1,0);x.XFlush(display);time.sleep(.04);xt.XTestFakeKeyEvent(display,code,0,0);x.XFlush(display);time.sleep(.16)
   def capture(label):
    old=int(state()['captures']);key(0xffc9);s=wait(lambda s:int(s['captures'])>old);n=int(s['captures']);cap=dict(line.split('\t',1)for line in(d/f'capture-{n:03}.tsv').read_text().splitlines());assert cap['readback_equal']=='true';captures.append(dict(label=label,number=n,captured=cap));return cap
   def save():
    old=state()['saves'];click(1644,1296);wait(lambda s:s['saves']!=old);assert(store/'journey.chk').read_bytes()[:8]==b'8SJRN007'
   def phased(label,light):
    for attempt in range(8):
     wait(lambda s:s['minimap_light']==str(light).lower());cap=capture(label+'-phase-probe')
     if cap['minimap_light']==str(light).lower():
      captures[-1]['label']=label;return cap
    raise AssertionError(('capture phase unavailable',label,light))
   def leave_event():
    if state()['phase']=='prompt':
     key(0xff0d);wait(lambda s:s['phase']=='battle');key(0xff1b);wait(lambda s:s['outcome']!='None');time.sleep(.25);key(0xff0d);wait(lambda s:s['phase']=='world')
   def buy():
    before=int(state()['gold']);click(230,1296);wait(lambda s:int(s['gold'])==before-100);click(690,1296);wait(lambda s:s['phase']!='magic-shop');leave_event()
   def cast(index):
    click(1640,680);wait(lambda s:s['phase']=='magic-menu');click(900,210+index*120);wait(lambda s:s['selected']==str(index));click(230,1296);wait(lambda s:s['phase']!='magic-menu')
   def phased(label):
    for attempt in range(10):
     wait(lambda s:s['minimap_light']=='true');cap=capture(label+'-phase-probe')
     if cap['minimap_light']=='true':captures[-1]['label']=label;return cap
    raise AssertionError('marker phase capture unavailable')
   if name in ['stop','bird']:
    mode='stop' if name=='stop' else 'bird';meta=dict(l.split('\t',1)for l in(r/('fixture-'+mode)/'fixture.tsv').read_text().splitlines());key(int(meta['key']));wait(lambda s:s['phase']=='magic-shop');buy();before=state()
    if name=='stop':
     capture('before');cast(4);wait(lambda s:s['phase']=='world');assert state()['stopped']=='true' and state()['tempo']=='8' and int(state()['steps'])==int(before['steps'])*8//6;assert state()['seed']==before['seed'] and state()['actions']==before['actions'];time.sleep(1.3);stop_anchor=capture('once');save()
    else:
     cast(5);wait(lambda s:s['phase']=='birdseye');assert state()['world_hash']==before['world_hash'] and state()['explored']==before['explored'];phased('full');old=state()['state_hash'];key(0x20);key(0xff52);click(600,600);assert state()['state_hash']==old and state()['phase']=='birdseye'
     click(450,20);wait(lambda s:s['font']=='1');phased('lishu');click(708,20);wait(lambda s:s['font']=='2');phased('caoshu');click(450,20);wait(lambda s:s['font']=='1');bird_anchor=phased('anchor');save()
   elif name=='stop-cold':
    assert state()['state_hash']==stop_anchor['state_hash'] and state()['stopped']=='true';capture('cold');key(0x20);wait(lambda s:s['phase']=='magic-shop');buy();before=state();cast(4);wait(lambda s:s['phase']=='world');assert state()['steps']==before['steps'] and state()['tempo']=='8' and json.loads(state()['magic_charges'])[4]==0 and state()['seed']==before['seed'];time.sleep(1.3);capture('repeat');save()
   else:
    assert state()['phase']=='birdseye' and state()['state_hash']==bird_anchor['state_hash'];cap=phased('cold');assert cap['frame_hash']==bird_anchor['frame_hash'];key(0xff0d);wait(lambda s:s['phase']=='world');assert state()['world_hash']==bird_anchor['world_hash'] and state()['explored']==bird_anchor['explored'] and json.loads(state()['magic_charges'])[5]==0
    key(0xffc2);wait(lambda s:s['phase']=='minimap');phased('explored');assert int(state()['explored'])<5600;key(0xff1b);wait(lambda s:s['phase']=='world');save()
   final=state();event=Event();event.client.type=33;event.client.display=display;event.client.window=window;event.client.message=x.XInternAtom(display,b'WM_PROTOCOLS',0);event.client.format=32;event.client.data.l[0]=x.XInternAtom(display,b'WM_DELETE_WINDOW',0);x.XSendEvent(display,window,0,0,C.byref(event));x.XFlush(display);code=app.wait(timeout=10);assert code==0;log.close();log=None;runs.append(dict(name=name,exit=code,command=cmd,inputs=inputs,captures=captures,final=final));app=None
  (base/'receipt.json').write_text(json.dumps(dict(status='passed-rust-survey-spells-gui',binary_sha256=hashlib.sha256((r/'8sword-remake').read_bytes()).hexdigest(),runs=runs,source='Previous real v6 progress; only shop relocation; source resources, army and RNG preserved',gameplay_input='XTest original shop/F4, repeat stop, full bird map versus F5 exploration; F12 diagnostic capture',controlled_initial_progress=True,no_runtime_memory_or_ip_injection=True),ensure_ascii=False,indent=2)+'\n')
 finally:
  if app and app.poll()is None:app.terminate();app.wait(timeout=5)
  if log:log.close()
  xvfb.terminate();xvfb.wait(timeout=5)
if __name__=='__main__':main()
