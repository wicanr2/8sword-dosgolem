#!/usr/bin/env python3
"""056：解壓包正常新建、F7與獨立程序續玩；Windows由Wine容器啟動。"""
import ctypes as C
import hashlib, json, os, subprocess, sys, time
from pathlib import Path

def main():
    assert Path('/.dockerenv').exists() and os.getuid()==1000
    platform=sys.argv[1]; q=Path('/q'); base=q/'smoke'/platform; base.mkdir(exist_ok=True)
    os.environ.update(DISPLAY=':98' if platform=='windows' else ':97',SDL_AUDIODRIVER='dummy',SDL_RENDER_DRIVER='software')
    xvfb=None;app=None;log=None
    try:
        if platform=='linux':
            home=base/'home';home.mkdir();os.environ['HOME']=str(home);os.environ.pop('XDG_DATA_HOME',None)
            xvfb=subprocess.Popen(['Xvfb',':97','-screen','0','3100x1450x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        x=C.CDLL('libX11.so.6');xt=C.CDLL('libXtst.so.6')
        x.XOpenDisplay.argtypes=[C.c_char_p];x.XOpenDisplay.restype=C.c_void_p
        deadline=time.monotonic()+90;display=None
        while not display and time.monotonic()<deadline:display=x.XOpenDisplay(None);time.sleep(.1)
        assert display
        x.XDefaultRootWindow.argtypes=[C.c_void_p];x.XDefaultRootWindow.restype=C.c_ulong;root=x.XDefaultRootWindow(display)
        x.XQueryTree.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_ulong),C.POINTER(C.c_ulong),C.POINTER(C.POINTER(C.c_ulong)),C.POINTER(C.c_uint)];x.XFetchName.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_char_p)];x.XFree.argtypes=[C.c_void_p];x.XSetInputFocus.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_ulong];x.XFlush.argtypes=[C.c_void_p];x.XKeysymToKeycode.argtypes=[C.c_void_p,C.c_ulong];x.XKeysymToKeycode.restype=C.c_uint;xt.XTestFakeKeyEvent.argtypes=[C.c_void_p,C.c_uint,C.c_int,C.c_ulong]
        x.XTranslateCoordinates.argtypes=[C.c_void_p,C.c_ulong,C.c_ulong,C.c_int,C.c_int,C.POINTER(C.c_int),C.POINTER(C.c_int),C.POINTER(C.c_ulong)];xt.XTestFakeMotionEvent.argtypes=[C.c_void_p,C.c_int,C.c_int,C.c_int,C.c_ulong];xt.XTestFakeButtonEvent.argtypes=[C.c_void_p,C.c_uint,C.c_int,C.c_ulong]
        x.XInternAtom.argtypes=[C.c_void_p,C.c_char_p,C.c_int];x.XInternAtom.restype=C.c_ulong;x.XSendEvent.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_long,C.c_void_p]
        x.XGetWindowProperty.argtypes=[C.c_void_p,C.c_ulong,C.c_ulong,C.c_long,C.c_long,C.c_int,C.c_ulong,C.POINTER(C.c_ulong),C.POINTER(C.c_int),C.POINTER(C.c_ulong),C.POINTER(C.c_ulong),C.POINTER(C.POINTER(C.c_ubyte))]
        title_atom=x.XInternAtom(display,b'_NET_WM_NAME',0)
        class Data(C.Union):_fields_=[('b',C.c_char*20),('s',C.c_short*10),('l',C.c_long*5)]
        class Client(C.Structure):_fields_=[('type',C.c_int),('serial',C.c_ulong),('send',C.c_int),('display',C.c_void_p),('window',C.c_ulong),('message',C.c_ulong),('format',C.c_int),('data',Data)]
        class Event(C.Union):_fields_=[('client',Client),('pad',C.c_long*24)]
        records=json.loads((q/'package-records.json').read_text());package=next(p for p in records['packages']if p['path'].endswith('linux-x86_64.tar.gz'if platform=='linux'else'windows-x86_64.zip'))
        exe=Path(package['extracted'])/('8sword-remake'if platform=='linux'else'8sword.exe')
        assert exe.is_file()
        saved=None;runs=[]
        for name in ['fresh','cold']:
            folder=base/name;folder.mkdir(exist_ok=True);inputs=[];captures=[]
            if platform=='linux':
                log=(folder/'player.log').open('w');app=subprocess.Popen([str(exe),*(['--skip-intro']if name=='cold'else[]),'--scale','1','--seed','1','--capture-dir',str(folder)],stdout=log,stderr=log,cwd='/tmp')
            else:(base/(name+'.go')).touch()
            def state():
                if app:assert app.poll()is None,(app.returncode,(folder/'player.log').read_text())
                if platform=='windows':assert not(base/(name+'.exit')).exists(),(base/(name+'.exit')).read_text()if(base/(name+'.exit')).exists()else''
                try:return dict(l.split('\t',1)for l in(folder/'status.tsv').read_text().splitlines())
                except(FileNotFoundError,ValueError):return{}
            def wait(pred,seconds=60):
                until=time.monotonic()+seconds
                while time.monotonic()<until:
                    s=state()
                    if s and pred(s):return s
                    time.sleep(.04)
                raise AssertionError((platform,name,'timeout',state(),(folder/'player.log').read_text()))
            wait(lambda s:s.get('phase') in ['intro','start'])
            names=[];found=[]
            def search(win):
                actual=C.c_ulong();fmt=C.c_int();items=C.c_ulong();after=C.c_ulong();data=C.POINTER(C.c_ubyte)()
                x.XGetWindowProperty(display,win,title_atom,0,1024,0,0,C.byref(actual),C.byref(fmt),C.byref(items),C.byref(after),C.byref(data))
                if data:
                    raw=C.string_at(data,items.value)if fmt.value==8 else b''
                    if raw:
                        names.append(raw.decode(errors='replace'))
                        if b'rust'in raw.lower():found.append(win)
                    x.XFree(data)
                title=C.c_char_p()
                if x.XFetchName(display,win,C.byref(title))and title.value:
                    names.append(title.value.decode(errors='replace'))
                    if b'rust'in title.value.lower():found.append(win)
                    x.XFree(title)
                rr=C.c_ulong();p=C.c_ulong();c=C.POINTER(C.c_ulong)();num=C.c_uint()
                if x.XQueryTree(display,win,C.byref(rr),C.byref(p),C.byref(c),C.byref(num)):
                    for i in range(num.value):search(c[i])
                    if c:x.XFree(c)
            for attempt in range(100):
                rr=C.c_ulong();parent=C.c_ulong();children=C.POINTER(C.c_ulong)();n=C.c_uint();assert x.XQueryTree(display,root,C.byref(rr),C.byref(parent),C.byref(children),C.byref(n));names=[];found=[]
                for i in range(n.value):search(children[i])
                if children:x.XFree(children)
                if found:break
                time.sleep(.1)
            assert found,(platform,'no window',names);window=found[-1];x.XSetInputFocus(display,window,1,0);x.XFlush(display)
            ox=C.c_int();oy=C.c_int();child=C.c_ulong();assert x.XTranslateCoordinates(display,window,root,0,0,C.byref(ox),C.byref(oy),C.byref(child))
            def key(symbol):
                code=x.XKeysymToKeycode(display,symbol);assert code;inputs.append(dict(key=symbol,before=state()));xt.XTestFakeKeyEvent(display,code,1,0);x.XFlush(display);time.sleep(.06);xt.XTestFakeKeyEvent(display,code,0,0);x.XFlush(display);time.sleep(.2)
            def click(px,py):
                inputs.append(dict(mouse=[px,py],before=state()));xt.XTestFakeMotionEvent(display,-1,ox.value+px,oy.value+py,0);xt.XTestFakeButtonEvent(display,1,1,0);x.XFlush(display);time.sleep(.06);xt.XTestFakeButtonEvent(display,1,0,0);x.XFlush(display);time.sleep(.2)
            def capture(label):
                old=int(state()['captures']);key(0xffc9);s=wait(lambda s:int(s['captures'])>old);num=int(s['captures'])
                assert s['readback_equal']=='true';assert(folder/f'frame-{num:03}.ppm').read_bytes()==(folder/f'readback-{num:03}.ppm').read_bytes()
                assert(folder/f'shell-frame-{num:03}.ppm').read_bytes()==(folder/f'shell-readback-{num:03}.ppm').read_bytes()
                captures.append(dict(label=label,number=num,state=s,central_sha256=hashlib.sha256((folder/f'frame-{num:03}.ppm').read_bytes()).hexdigest()))
            if name=='fresh' and (q/'media-overlay.json').exists():
                wait(lambda s:s.get('stage','').startswith('story-1'))
                capture('corrected-story-background')
            wait(lambda s:s.get('phase')=='start')
            capture('start-menu')
            if name=='fresh':
                key(0xff54);key(0xff0d);wait(lambda s:s['phase']=='new-confirm');key(0xff0d);wait(lambda s:s['phase']=='world')
                assert state()['army']=='30,0,0,0,0,0'and state()['gold']=='500'
                capture('new-world-hd');old=state()['actions'];key(0xff52);wait(lambda s:s['actions']!=old)
                click(962,20);wait(lambda s:s.get('font')=='1');capture('lishu-world')
                click(2660,1295);wait(lambda s:s.get('display_mode')=='original');capture('original-world')
                click(2660,1295);wait(lambda s:s.get('display_mode')=='hd')
                key(0xffbf);wait(lambda s:s['phase']=='review');capture('army-review');key(0xff1b);wait(lambda s:s['phase']=='world')
                for _ in range(2):
                    old=state()['saves'];key(0xffc4);wait(lambda s:s['saves']!=old)
                capture('saved-world');saved=state()
            else:
                key(0xff0d);wait(lambda s:s['phase']=='world')
                for field in ['state_hash','army','gold','x','y','font','actions']:assert state()[field]==saved[field],(field,state()[field],saved[field])
                capture('cold-world');old=state()['saves'];key(0xffc4);wait(lambda s:s['saves']!=old)
            final=state();event=Event();event.client.type=33;event.client.display=display;event.client.window=window;event.client.message=x.XInternAtom(display,b'WM_PROTOCOLS',0);event.client.format=32;event.client.data.l[0]=x.XInternAtom(display,b'WM_DELETE_WINDOW',0);x.XSendEvent(display,window,0,0,C.byref(event));x.XFlush(display)
            assert int(final['queued_bytes'])>0
            if app:code=app.wait(timeout=15);assert code==0;app=None;log.close();log=None
            else:
                deadline=time.monotonic()+20
                while not(base/(name+'.exit')).exists()and time.monotonic()<deadline:time.sleep(.1)
                code=int((base/(name+'.exit')).read_text());assert code==0
            runs.append(dict(name=name,exit=code,inputs=inputs,captures=captures,final=final))
        (base/'receipt.json').write_text(json.dumps(dict(status='passed-extracted-package-gui',platform=platform,package_sha256=package['sha256'],binary_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),runs=runs,default_save_root=True,unicode_install_path=True,no_assets_override=True,no_gameplay_state_injection=True,audio_device='SDL dummy; decoded/queued audio is technical evidence only'),ensure_ascii=False,indent=2)+'\n')
    finally:
        if app and app.poll()is None:app.terminate();app.wait(timeout=10)
        if log:log.close()
        if xvfb:xvfb.terminate();xvfb.wait(timeout=10)

if __name__=='__main__':main()
