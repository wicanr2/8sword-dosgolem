#!/usr/bin/env python3
"""煉金／召兵：明示跨區進度的原式購買、施法、結果冷讀與戰鬥。"""
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
  for name in ['alchemy','alchemy-cold','summon','summon-cold','battle-cold']:
   d=base/name;d.mkdir();store=base/(name+'-store');store.mkdir();log=(d/'player.log').open('w');cmd=[str(r/'8sword-remake'),'--journey','--assets',str(r/'pack'),'--capture-dir',str(d),'--scale','1','--save-dir',str(store)]
   if name=='summon':
    subprocess.run([str(r/'resource-fixture'),str(r/'pack'),str(base/'alchemy-cold-store/journey.chk'),str(r/'fixture-summon'),'summon'],check=True,timeout=10)
   src={'alchemy':r/'fixture-alchemy/journey.chk','alchemy-cold':base/'alchemy-store/journey.chk','summon':r/'fixture-summon/journey.chk','summon-cold':base/'summon-store/journey.chk','battle-cold':base/'summon-cold-store/journey.chk'}[name]
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
    old=state()['saves'];click(1644,1296);wait(lambda s:s['saves']!=old);assert(store/'journey.chk').read_bytes()[:8]==b'8SJRN006'
   def phased(label,light):
    for attempt in range(8):
     wait(lambda s:s['minimap_light']==str(light).lower());cap=capture(label+'-phase-probe')
     if cap['minimap_light']==str(light).lower():
      captures[-1]['label']=label;return cap
    raise AssertionError(('capture phase unavailable',label,light))
   def leave_event():
    if state()['phase']=='prompt':
     key(0xff0d);wait(lambda s:s['phase']=='battle');key(0xff1b);wait(lambda s:s['outcome']!='None');time.sleep(.25);key(0xff0d);wait(lambda s:s['phase']=='world')
   if name in ['alchemy','summon']:
    spell=1 if name=='alchemy' else 2
    fixture=r/('fixture-alchemy' if spell==1 else 'fixture-summon');meta=dict(l.split('\t',1)for l in(fixture/'fixture.tsv').read_text().splitlines())
    assert state()['magic_book']=='true';old=state()['state_hash'];key(int(meta['key']));wait(lambda s:s['phase']=='magic-shop');assert state()['x']==meta['shop_x'] and state()['y']==meta['shop_y'];before=int(state()['gold'])
    click(230,1296);wait(lambda s:int(s['gold'])==before-100);click(230,1296);wait(lambda s:s['message']=='法術容量已滿');capture('shop');click(690,1296);wait(lambda s:s['phase']!='magic-shop');leave_event()
    before=state();click(1640,680);wait(lambda s:s['phase']=='magic-menu');click(900,210+spell*120);wait(lambda s:s['selected']==str(spell));click(230,1296);wait(lambda s:s['phase']=='resource-result');time.sleep(1.3);capture('result')
    result=state();assert result['steps']==before['steps'] and result['x']==before['x'] and result['y']==before['y'] and result['actions']==before['actions'] and result['seed']!=before['seed'];assert json.loads(result['magic_charges'])[spell]==0
    if spell==1:
     assert result['army']==before['army'] and int(result['gold'])>=int(before['gold']);alchemy_anchor=captures[-1]['captured'];save()
    else:
     assert int(result['gold'])==int(before['gold']) and result['army']!=before['army'];summon_anchor=captures[-1]['captured'];save()
   elif name in ['alchemy-cold','summon-cold']:
    anchor=alchemy_anchor if name=='alchemy-cold' else summon_anchor
    assert state()['phase']=='resource-result' and state()['state_hash']==anchor['state_hash'];cap=capture('cold');assert cap['frame_hash']==anchor['frame_hash'];gold=state()['gold'];seed=state()['seed'];army=state()['army'];click(230,1296);wait(lambda s:s['phase']=='world');assert (state()['gold'],state()['seed'],state()['army'])==(gold,seed,army)
    if name=='alchemy-cold':
     click(250,20);wait(lambda s:s['font']=='0');key(0xffbe);wait(lambda s:s['phase']=='character');capture('character');key(0xff1b);wait(lambda s:s['phase']=='world');save()
    else:
     click(450,20);wait(lambda s:s['font']=='1');key(0xffbf);wait(lambda s:s['phase']=='review');capture('review');key(0xff1b);wait(lambda s:s['phase']=='world')
     meta=dict(l.split('\t',1)for l in(r/'fixture-summon/fixture.tsv').read_text().splitlines());old=state()['actions'];key({0xff51:0xff53,0xff53:0xff51,0xff52:0xff54,0xff54:0xff52}[int(meta['key'])]);wait(lambda s:s['actions']!=old)
     # Normal Space advances rules RNG at this actual world tile; never reseed.
     for attempt in range(160):
      if state()['phase']=='prompt':break
      old=state()['actions'];key(0x20);wait(lambda s:s['actions']!=old or s['phase']=='prompt')
     assert state()['phase']=='prompt';key(0xff0d);wait(lambda s:s['phase']=='battle');summoned_attack=False;attacks=[]
     positions=[(816,300),(816,600),(816,900),(1080,450),(1080,750),(1344,600)]
     for attempt in range(60):
      st=state()
      if st['outcome']!='None':break
      if st['actor']!='player':time.sleep(.1);continue
      targets=st['targets']
      if not targets:time.sleep(.1);continue
      node=int(targets.split(',')[0]);x0,y0=positions[node];old=int(st['sequence']);click(x0+132,y0+198);key(0xff0d);wait(lambda s:int(s['sequence'])>old or s['outcome']!='None');attacks.append(dict(raw=st['raw'],before=st,after=state()))
      if st['raw']==('0' if state()['army'].split(',')[1]=='0' else '1'):summoned_attack=True;capture('battle');break
     assert summoned_attack,('summoned troop never acted',state());inputs.append(dict(summoned_actions=attacks))
     if state()['outcome']=='None':key(0xff1b);wait(lambda s:s['outcome']!='None')
     time.sleep(.3);key(0xff0d);wait(lambda s:s['phase']=='world');save();world_anchor=state()['state_hash'];key(0xffbf);wait(lambda s:s['phase']=='review');returned=capture('returned')
   else:
    assert state()['phase']=='world' and state()['state_hash']==world_anchor;key(0xffbf);wait(lambda s:s['phase']=='review');cap=capture('cold');assert cap['frame_hash']==returned['frame_hash'];click(708,20);wait(lambda s:s['font']=='2');capture('caoshu')
   final=state();event=Event();event.client.type=33;event.client.display=display;event.client.window=window;event.client.message=x.XInternAtom(display,b'WM_PROTOCOLS',0);event.client.format=32;event.client.data.l[0]=x.XInternAtom(display,b'WM_DELETE_WINDOW',0);x.XSendEvent(display,window,0,0,C.byref(event));x.XFlush(display);code=app.wait(timeout=10);assert code==0;log.close();log=None;runs.append(dict(name=name,exit=code,command=cmd,inputs=inputs,captures=captures,final=final));app=None
  (base/'receipt.json').write_text(json.dumps(dict(status='passed-rust-resource-spells-gui',binary_sha256=hashlib.sha256((r/'8sword-remake').read_bytes()).hexdigest(),runs=runs,source='Previous real v5 progress; controlled area/shop position and leadership1000; source RNG preserved',gameplay_input='XTest normal world path, F6/F4, mouse purchases and original movement; F12 diagnostic capture',controlled_initial_progress=True,no_runtime_memory_or_ip_injection=True),ensure_ascii=False,indent=2)+'\n')
 finally:
  if app and app.poll()is None:app.terminate();app.wait(timeout=5)
  if log:log.close()
  xvfb.terminate();xvfb.wait(timeout=5)
if __name__=='__main__':main()
