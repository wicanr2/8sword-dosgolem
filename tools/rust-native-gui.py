#!/usr/bin/env python3
"""有界Xvfb中的Rust原生戰鬥抽驗。輸入只經X11事件，不改遊戲記憶體。"""
import ctypes as C
import json, hashlib
import os
from pathlib import Path
import subprocess
import time
from collections import deque

NAV = [[0,0,0,0],[0,2,7,4],[1,3,8,4],[2,0,9,5],[0,5,2,6],[4,0,2,6],
       [0,0,5,0],[0,8,10,1],[7,9,10,2],[8,0,11,3],[0,11,12,8],
       [10,0,12,8],[0,0,0,11]]
ARROWS = [0xff52, 0xff54, 0xff51, 0xff53]

class Key(C.Structure):
    _fields_=[('type',C.c_int),('serial',C.c_ulong),('send_event',C.c_int),('display',C.c_void_p),('window',C.c_ulong),('root',C.c_ulong),('subwindow',C.c_ulong),('time',C.c_ulong),('x',C.c_int),('y',C.c_int),('x_root',C.c_int),('y_root',C.c_int),('state',C.c_uint),('keycode',C.c_uint),('same_screen',C.c_int)]
class Button(C.Structure):
    _fields_=Key._fields_[:-2]+[('button',C.c_uint),('same_screen',C.c_int)]
class Event(C.Union):
    _fields_=[('key',Key),('button',Button),('padding',C.c_long*24)]

def main():
    assert Path('/.dockerenv').exists() and os.getuid()==1000
    q=Path('/out'); folder=q/'gui-r5'; folder.mkdir()
    assert not Path('/game').exists() and not Path('/core').exists()
    os.environ.update(DISPLAY=':97',SDL_AUDIODRIVER='dummy',SDL_RENDER_DRIVER='software')
    xvfb=subprocess.Popen(['Xvfb',':97','-screen','0','2000x1400x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    app=None; logs=[]
    try:
        time.sleep(.5)
        x=C.CDLL('libX11.so.6')
        x.XOpenDisplay.argtypes=[C.c_char_p]; x.XOpenDisplay.restype=C.c_void_p
        display=x.XOpenDisplay(None); assert display
        x.XDefaultRootWindow.argtypes=[C.c_void_p]; x.XDefaultRootWindow.restype=C.c_ulong
        root=x.XDefaultRootWindow(display)
        x.XQueryTree.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_ulong),C.POINTER(C.c_ulong),C.POINTER(C.POINTER(C.c_ulong)),C.POINTER(C.c_uint)]
        x.XFetchName.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_char_p)]
        x.XFree.argtypes=[C.c_void_p]
        x.XSetInputFocus.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_ulong]
        x.XFlush.argtypes=[C.c_void_p]
        x.XKeysymToKeycode.argtypes=[C.c_void_p,C.c_ulong]; x.XKeysymToKeycode.restype=C.c_uint
        x.XSendEvent.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_long,C.POINTER(Event)]
        x.XWarpPointer.argtypes=[C.c_void_p,C.c_ulong,C.c_ulong,C.c_int,C.c_int,C.c_uint,C.c_uint,C.c_int,C.c_int]
        xt=C.CDLL('libXtst.so.6')
        xt.XTestFakeButtonEvent.argtypes=[C.c_void_p,C.c_uint,C.c_int,C.c_ulong]
        xt.XTestFakeKeyEvent.argtypes=[C.c_void_p,C.c_uint,C.c_int,C.c_ulong]
        def window():
            rr=C.c_ulong(); parent=C.c_ulong(); children=C.POINTER(C.c_ulong)(); count=C.c_uint()
            assert x.XQueryTree(display,root,C.byref(rr),C.byref(parent),C.byref(children),C.byref(count))
            found=[]
            for i in range(count.value):
                name=C.c_char_p()
                if x.XFetchName(display,children[i],C.byref(name)) and name.value:
                    if b'Rust' in name.value: found.append(children[i])
                    x.XFree(name)
            if children: x.XFree(children)
            assert len(found)==1,found
            return found[0]
        receipts=[]
        for mode in ['win','loss','retreat']:
            d=folder/mode; d.mkdir(); log=(d/'player.log').open('w'); logs.append(log)
            command=['/out/8sword-remake','--battle','--assets','/out/pack','--capture-dir',str(d),'--scale','1','--seed','305419896']
            if mode=='loss': command+=['--weak']
            app=subprocess.Popen(command,stdout=log,stderr=log)
            def state():
                assert app.poll() is None,(app.returncode,(d/'player.log').read_text())
                try:return dict(line.split('\t',1)for line in(d/'status.tsv').read_text().splitlines())
                except FileNotFoundError:return {}
            def wait(pred,seconds=20):
                end=time.monotonic()+seconds
                while time.monotonic()<end:
                    v=state()
                    if pred(v):return v
                    time.sleep(.08)
                raise AssertionError(('timeout',mode,state()))
            wait(lambda v:v.get('actor')=='player')
            win=window();x.XSetInputFocus(display,win,1,0);x.XFlush(display)
            def key(symbol):
                code=x.XKeysymToKeycode(display,symbol);assert code
                assert xt.XTestFakeKeyEvent(display,code,1,0);x.XFlush(display);time.sleep(.07)
                assert xt.XTestFakeKeyEvent(display,code,0,0);x.XFlush(display);time.sleep(.12)
            def click(px,py):
                x.XWarpPointer(display,0,win,0,0,0,0,px,py);x.XFlush(display);time.sleep(.15)
                assert xt.XTestFakeButtonEvent(display,1,1,0);x.XFlush(display);time.sleep(.07)
                assert xt.XTestFakeButtonEvent(display,1,0,0);x.XFlush(display);time.sleep(.2)
            captures=[]
            def capture(label):
                old=int(state().get('captures',0));key(0xffc9)
                v=wait(lambda s:int(s.get('captures',0))>old)
                assert v['readback_equal']=='true',v
                captures.append(dict(label=label,status=v))
            if mode=='win':
                time.sleep(1)
                capture('noto')
                click(450,24);wait(lambda v:v['font']=='lishu');capture('lishu')
                click(680,24);wait(lambda v:v['font']=='caoshu');capture('caoshu')
                key(0xffc7);wait(lambda v:v['font']=='noto')
                click(1020,24);off=wait(lambda v:v['music']=='off')
                time.sleep(.4);assert state()['queued_bytes']==off['queued_bytes']
                click(1020,24);wait(lambda v:v['music']=='on')
            if mode=='retreat':
                key(0xff1b)
            else:
                for _ in range(150):
                    s=wait(lambda v:v.get('actor')=='player' or v.get('outcome')!='active')
                    if s['outcome']!='active':break
                    if mode=='loss':key(32);continue
                    target=int(s['legal'].split(',')[0])+1
                    todo=deque([(int(s['cursor']),[])]);seen=set();route=None
                    while todo:
                        node,steps=todo.popleft()
                        if node==target:route=steps;break
                        if node in seen:continue
                        seen.add(node)
                        for direction,nxt in enumerate(NAV[node]):
                            if nxt:todo.append((nxt,steps+[direction]))
                    assert route is not None
                    node=int(s['cursor'])
                    for direction in route:
                        node=NAV[node][direction]
                        key(ARROWS[direction])
                        wait(lambda v:int(v['cursor'])==node)
                    wait(lambda v:int(v['cursor'])==target)
                    before=s['sequence'];key(0xff0d)
                    wait(lambda v:v['sequence']!=before or v['outcome']!='active')
                else:raise AssertionError('ordinary battle input budget')
            final=wait(lambda v:v.get('outcome')==mode)
            capture(mode);final=state();assert int(final['drains'])>0 and int(final['queued_bytes'])>0
            key(0xff1b);assert app.wait(5)==0
            receipts.append(dict(mode=mode,command=command,initial_seed=305419896,input='X11 keyboard and toolbar mouse; no RAM or state injection',captures=captures,final=final,exit=0))
            app=None;log.close()
        (folder/'receipt.json').write_text(json.dumps(dict(status='passed-rust-native-gui',binary_sha256=hashlib.sha256((q/'8sword-remake').read_bytes()).hexdigest(),rows=receipts,render_size=[1920,1320],audio_backend='SDL dummy; nonzero queued PCM and device consumption only, no human hearing claim',scope='Explicit battle rosters; no world, save, spell or full-game claim'),ensure_ascii=False,indent=2)+'\n')
    finally:
        if app is not None and app.poll() is None:
            app.terminate()
            try:app.wait(5)
            except subprocess.TimeoutExpired:app.kill();app.wait()
        xvfb.terminate();xvfb.wait(5)
        for log in logs:log.close()

def scaled():
    assert Path('/.dockerenv').exists() and os.getuid()==1000
    q=Path('/out');d=q/'gui-scale-r1';d.mkdir()
    os.environ.update(DISPLAY=':96',SDL_AUDIODRIVER='dummy',SDL_RENDER_DRIVER='software')
    xvfb=subprocess.Popen(['Xvfb',':96','-screen','0','1400x1000x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    app=None;log=(d/'player.log').open('w')
    try:
        time.sleep(.5)
        app=subprocess.Popen(['/out/8sword-remake','--battle','--assets','/out/pack','--seed','305419896'],stdout=log,stderr=log)
        time.sleep(1.2)
        x=C.CDLL('libX11.so.6');xt=C.CDLL('libXtst.so.6')
        x.XOpenDisplay.argtypes=[C.c_char_p];x.XOpenDisplay.restype=C.c_void_p;display=x.XOpenDisplay(None);assert display
        x.XDefaultRootWindow.argtypes=[C.c_void_p];x.XDefaultRootWindow.restype=C.c_ulong;root=x.XDefaultRootWindow(display)
        x.XQueryTree.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_ulong),C.POINTER(C.c_ulong),C.POINTER(C.POINTER(C.c_ulong)),C.POINTER(C.c_uint)]
        x.XFetchName.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_char_p)]
        x.XFree.argtypes=[C.c_void_p];x.XFlush.argtypes=[C.c_void_p]
        rr=C.c_ulong();parent=C.c_ulong();children=C.POINTER(C.c_ulong)();count=C.c_uint()
        assert x.XQueryTree(display,root,C.byref(rr),C.byref(parent),C.byref(children),C.byref(count))
        found=[]
        for i in range(count.value):
            name=C.c_char_p()
            if x.XFetchName(display,children[i],C.byref(name)) and name.value:
                if b'Rust' in name.value:found.append(children[i])
                x.XFree(name)
        x.XFree(children);assert len(found)==1;win=found[0]
        x.XSetInputFocus.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_ulong];x.XSetInputFocus(display,win,1,0)
        x.XWarpPointer.argtypes=[C.c_void_p,C.c_ulong,C.c_ulong,C.c_int,C.c_int,C.c_uint,C.c_uint,C.c_int,C.c_int]
        xt.XTestFakeButtonEvent.argtypes=[C.c_void_p,C.c_uint,C.c_int,C.c_ulong]
        class Image(C.Structure):
            _fields_=[('width',C.c_int),('height',C.c_int),('xoffset',C.c_int),('format',C.c_int),('data',C.c_void_p),('byte_order',C.c_int),('bitmap_unit',C.c_int),('bitmap_bit_order',C.c_int),('bitmap_pad',C.c_int),('depth',C.c_int),('bytes_per_line',C.c_int),('bits_per_pixel',C.c_int),('red_mask',C.c_ulong),('green_mask',C.c_ulong),('blue_mask',C.c_ulong)]
        x.XGetImage.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_int,C.c_uint,C.c_uint,C.c_ulong,C.c_int];x.XGetImage.restype=C.POINTER(Image)
        x.XDestroyImage.argtypes=[C.POINTER(Image)]
        files=[]
        for n,name in enumerate(['noto','lishu','caoshu']):
            if n:
                px=int((144+n*228+100)*2/3);py=16
                x.XWarpPointer(display,0,win,0,0,0,0,px,py);x.XFlush(display);time.sleep(.15)
                xt.XTestFakeButtonEvent(display,1,1,0);x.XFlush(display);time.sleep(.07)
                xt.XTestFakeButtonEvent(display,1,0,0);x.XFlush(display);time.sleep(.3)
            assert app.poll() is None,(app.returncode,(d/'player.log').read_text())
            im=x.XGetImage(display,win,0,0,1280,880,C.c_ulong(-1).value,2);assert im
            try:
                v=im.contents;assert v.width==1280 and v.height==880 and v.bits_per_pixel==32 and v.byte_order==0
                assert(v.red_mask,v.green_mask,v.blue_mask)==(0xff0000,0xff00,0xff)
                raw=C.string_at(v.data,v.bytes_per_line*v.height);rgb=bytearray()
                for row in range(v.height):
                    line=raw[row*v.bytes_per_line:row*v.bytes_per_line+v.width*4]
                    for pixel in range(0,len(line),4):rgb.extend(line[pixel:pixel+3][::-1])
                file=d/(name+'.ppm');file.write_bytes(b'P6\n1280 880\n255\n'+rgb);files.append(dict(font=name,sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
            finally:x.XDestroyImage(im)
        (d/'receipt.json').write_text(json.dumps(dict(status='passed-rust-production-scale-capture',size=[1280,880],binary_sha256=hashlib.sha256((q/'8sword-remake').read_bytes()).hexdigest(),files=files,input='XTest toolbar clicks at production-scaled coordinates; XGetImage captures; no diagnostics or memory injection',limits='Visual and scaled geometry check; not native pixel parity'),indent=2)+'\n')
    finally:
        if app is not None and app.poll() is None:
            app.terminate();app.wait(5)
        xvfb.terminate();xvfb.wait(5);log.close()

if __name__=='__main__':
    import sys
    scaled() if sys.argv[1:]==['--scale-check'] else main()
