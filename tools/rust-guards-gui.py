#!/usr/bin/env python3
"""原守軍確認、戰中冷讀、殘兵再戰、頭目與八劍抽驗。限Docker。"""
import ctypes as C
import hashlib,json,os,shutil,subprocess,time
from pathlib import Path
def main():
 assert Path('/.dockerenv').exists()and os.getuid()==1000
 r=Path('/native');base=r/'gui';base.mkdir();runs=[];app=None;log=None
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
  for name in ['empty','battle','cold-battle','cold-report','cold-win','boss','cold-boss']:
   d=base/name;d.mkdir();store=base/(name+'-store');store.mkdir();log=(d/'player.log').open('w');cmd=[str(r/'8sword-remake'),'--journey','--assets',str(r/'pack'),'--capture-dir',str(d),'--scale','1','--save-dir',str(store),'--continue']
   src={'empty':r/'fixture-empty/journey.chk','battle':r/'fixture-army/journey.chk','cold-battle':base/'battle.chk','cold-report':base/'retreat.chk','cold-win':base/'won.chk','boss':r/'fixture-boss/journey.chk','cold-boss':base/'boss-won.chk'}[name]
   shutil.copy2(src,store/'journey.chk');app=subprocess.Popen(cmd,stdout=log,stderr=log);inputs=[];captures=[]
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
   def click(px,py):
    inputs.append(dict(mouse=[px,py],before=state()));xt.XTestFakeMotionEvent(display,-1,ox.value+px,oy.value+py,0);xt.XTestFakeButtonEvent(display,1,1,0);x.XFlush(display);time.sleep(.04);xt.XTestFakeButtonEvent(display,1,0,0);x.XFlush(display);time.sleep(.10)
   def key(symbol,pause=.16):
    code=x.XKeysymToKeycode(display,symbol);assert code;inputs.append(dict(key=symbol,before=state()));xt.XTestFakeKeyEvent(display,code,1,0);x.XFlush(display);time.sleep(.04);xt.XTestFakeKeyEvent(display,code,0,0);x.XFlush(display);time.sleep(pause)
   def capture(label):
    old=int(state()['captures']);key(0xffc9);s=wait(lambda s:int(s['captures'])>old);num=int(s['captures']);cap=dict(line.split('\t',1)for line in(d/f'capture-{num:03}.tsv').read_text().splitlines());assert cap['readback_equal']=='true';captures.append(dict(label=label,number=num,captured=cap));return cap
   def save():
    old=state()['saves'];click(1644,1296);wait(lambda s:s['saves']!=old);assert(store/'journey.chk').read_bytes()[:8]==b'8SJRN014'
   meta=dict(l.split('\t',1)for l in(r/('fixture-boss'if name in ['boss','cold-boss']else 'fixture-army')/'fixture.tsv').read_text().splitlines())
   def stage(wanted):return wait(lambda s:s['guard_stage']=='Some('+wanted+')')
   def attack():
    s=wait(lambda s:s['phase']=='battle'and(s['actor']=='player'or s['outcome']!='None'))
    if s['outcome']!='None':return False
    time.sleep(.20);s=state();assert s['actor']=='player';target=int(s['targets'].split(',')[0]);px,py=[(816,300),(816,600),(816,900),(1080,450),(1080,750),(1344,600)][target];old=s['sequence'];click(px+120,py+150);key(0xff0d);wait(lambda s:s['sequence']!=old or s['outcome']!='None');return True
   def play():
    for i in range(100):
     if state()['outcome']!='None':break
     attack()
    wait(lambda s:s['outcome']=='Some(Win)')
   def enter():
    key(0xff52);stage('Prompt');assert state()['steps']==meta['steps']
   if name=='empty':
    assert state()['army']=='0,0,0,0,0,0';enter();capture('prompt');key(0xff1b);wait(lambda s:s['phase']=='world');capture('cancelled');assert int(state()['steps'])==int(meta['steps'])-1
    key(0x20);stage('Prompt');key(0xff0d);stage('NoArmy');capture('no-army');key(0xff0d);wait(lambda s:s['phase']=='world');assert int(state()['steps'])==int(meta['steps'])-1;save()
   elif name=='battle':
    assert state()['army']=='1000,200,0,0,0,0';enter();click(252,20);wait(lambda s:s['font']=='0');capture('noto');click(708,20);wait(lambda s:s['font']=='2');capture('caoshu');click(450,20);wait(lambda s:s['font']=='1');capture('prompt')
    key(0xff0d);wait(lambda s:s['phase']=='battle'and s['actor']=='player');battle_anchor=capture('battle');save();shutil.copy2(store/'journey.chk',base/'battle.chk')
   elif name=='cold-battle':
    cap=capture('cold-battle');assert cap['state_hash']==battle_anchor['state_hash']and cap['frame_hash']==battle_anchor['frame_hash'];attack();key(0xff1b);wait(lambda s:s['outcome']=='Some(Retreat)');key(0xff0d);stage('Retreat');assert state()['guard0']!='30,40,30,40,20,0';retreat_anchor=capture('retreat');assert int(state()['gold'])<int(meta['gold'])and state()['steps']==meta['steps'];save();shutil.copy2(store/'journey.chk',base/'retreat.chk');survivors=state()['guard0']
   elif name=='cold-report':
    cap=capture('cold-report');assert cap['state_hash']==retreat_anchor['state_hash']and cap['frame_hash']==retreat_anchor['frame_hash'];gold=state()['gold'];key(0xff0d);wait(lambda s:s['phase']=='world');assert state()['gold']==gold and int(state()['steps'])==int(meta['steps'])-1
    key(0x20);stage('Prompt');assert state()['guard0']==survivors;key(0xff0d);wait(lambda s:s['phase']=='battle');play();key(0xff0d);stage('Win');assert state()['gold']==gold and state()['guard0']=='0,0,0,0,0,0';capture('win');key(0xff0d);wait(lambda s:s['phase']=='world');won_anchor=capture('returned');save();shutil.copy2(store/'journey.chk',base/'won.chk')
   elif name=='cold-win':
    cap=capture('cold-world');assert cap['state_hash']==won_anchor['state_hash']and cap['frame_hash']==won_anchor['frame_hash'];income=int(meta['income'])+20;assert state()['resources'].split(',')[2]==str(income)
    key(0xffbe);wait(lambda s:s['phase']=='character');capture('income');key(0xff1b);wait(lambda s:s['phase']=='world');key(0x20);stage('Cleared');capture('cleared');key(0xff0d);wait(lambda s:s['phase']=='world');assert state()['resources'].split(',')[2]==str(income);save()
   elif name=='boss':
    enter();key(0xff0d);wait(lambda s:s['phase']=='battle');capture('battle');play();key(0xff0d);stage('Win');capture('win');assert state()['swords'].startswith('[true, false');key(0xff0d);wait(lambda s:s['phase']=='world')
    key(0xffbe);wait(lambda s:s['phase']=='character');key(0xff0d);wait(lambda s:s['character_swords']=='true');boss_anchor=capture('sword');save();shutil.copy2(store/'journey.chk',base/'boss-won.chk')
   else:
    assert state()['swords'].startswith('[true, false');key(0xffbe);wait(lambda s:s['phase']=='character');key(0xff0d);wait(lambda s:s['character_swords']=='true');cap=capture('sword-cold');assert cap['state_hash']==boss_anchor['state_hash']and cap['frame_hash']==boss_anchor['frame_hash'];save()
   final=state();event=Event();event.client.type=33;event.client.display=display;event.client.window=window;event.client.message=x.XInternAtom(display,b'WM_PROTOCOLS',0);event.client.format=32;event.client.data.l[0]=x.XInternAtom(display,b'WM_DELETE_WINDOW',0);x.XSendEvent(display,window,0,0,C.byref(event));x.XFlush(display);code=app.wait(timeout=10);assert code==0;log.close();log=None;runs.append(dict(name=name,exit=code,command=cmd,inputs=inputs,captures=captures,final=final));app=None
  (base/'receipt.json').write_text(json.dumps(dict(status='passed-rust-guards-gui',binary_sha256=hashlib.sha256((r/'8sword-remake').read_bytes()).hexdigest(),runs=runs,source='Real v13 origin, resources and magic retained. Original guard adjacent positions and seed1 controlled; combat fixtures explicitly set1000militia/200archers, empty fixture retains actual empty army. Subsequent movement,confirmation,combat,F7/cold uses XTest only. No runtime memory/IP injection',controlled_initial_progress=True,no_runtime_memory_or_ip_injection=True),ensure_ascii=False,indent=2)+'\n')
 finally:
  if app and app.poll()is None:app.terminate();app.wait(timeout=5)
  if log:log.close()
  xvfb.terminate();xvfb.wait(timeout=5)
if __name__=='__main__':main()
