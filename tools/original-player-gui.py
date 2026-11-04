#!/usr/bin/env python3
"""在有界 Docker/Xvfb 內抽驗原版操作入口，輸入只經 X11 事件。"""
import ctypes as C
import json, os, shutil, subprocess, time
from pathlib import Path

def main():
    assert Path('/.dockerenv').exists() and os.getuid() == 1000
    q = Path('/out'); d = q/'gui-r1'; d.mkdir()
    shutil.copytree(q/'player-chain-r1/session', d/'session')
    os.environ['DISPLAY'] = ':97'
    xvfb = subprocess.Popen(['Xvfb', ':97', '-screen', '0', '2000x1300x24', '-nolisten', 'tcp'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    app = None
    log = (d/'player.log').open('w')
    try:
        time.sleep(.6)
        x = C.CDLL('libX11.so.6')
        x.XOpenDisplay.argtypes=[C.c_char_p]; x.XOpenDisplay.restype=C.c_void_p
        display = x.XOpenDisplay(None); assert display
        x.XDefaultRootWindow.argtypes=[C.c_void_p]; x.XDefaultRootWindow.restype=C.c_ulong
        root = x.XDefaultRootWindow(display)
        x.XQueryTree.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_ulong),C.POINTER(C.c_ulong),C.POINTER(C.POINTER(C.c_ulong)),C.POINTER(C.c_uint)]
        x.XSetInputFocus.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_ulong]
        x.XFlush.argtypes=[C.c_void_p]
        x.XKeysymToKeycode.argtypes=[C.c_void_p,C.c_ulong]; x.XKeysymToKeycode.restype=C.c_uint
        class KeyEvent(C.Structure):
            _fields_=[('type',C.c_int),('serial',C.c_ulong),('send_event',C.c_int),('display',C.c_void_p),('window',C.c_ulong),('root',C.c_ulong),('subwindow',C.c_ulong),('time',C.c_ulong),('x',C.c_int),('y',C.c_int),('x_root',C.c_int),('y_root',C.c_int),('state',C.c_uint),('keycode',C.c_uint),('same_screen',C.c_int)]
        class Event(C.Union):
            _fields_=[('key',KeyEvent),('padding',C.c_long*24)]
        x.XSendEvent.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_long,C.POINTER(Event)]
        app = subprocess.Popen(['/out/8sword-original-player','-root','/game','-assets','/assets','-input','/out/inputs','-ui-assets','/out/ui-assets','-session',str(d/'session'),'-scratch',str(d/'scratch'),'-capture-dir',str(d),'-scale','1','-mute'], stdout=log, stderr=log)
        def state():
            assert app.poll() is None, (app.returncode, (d/'player.log').read_text())
            try: return json.loads((d/'ui-state.json').read_text())
            except (FileNotFoundError,json.JSONDecodeError): return {}
        def wait(pred, seconds=30):
            end=time.monotonic()+seconds
            while time.monotonic()<end:
                v=state()
                if pred(v): return v
                time.sleep(.15)
            raise AssertionError(('GUI timeout',state()))
        wait(lambda v:v.get('draws',0)>3)
        rr=C.c_ulong(); parent=C.c_ulong(); children=C.POINTER(C.c_ulong)(); count=C.c_uint()
        assert x.XQueryTree(display,root,C.byref(rr),C.byref(parent),C.byref(children),C.byref(count)) and count.value
        window=children[count.value-1]
        x.XSetInputFocus(display,window,1,0); x.XFlush(display)
        def key(symbol):
            code=x.XKeysymToKeycode(display,symbol); assert code
            ev=Event(); ev.key=KeyEvent(type=2,display=display,window=window,root=root,keycode=code,same_screen=1)
            assert x.XSendEvent(display,window,0,1,C.byref(ev)); x.XFlush(display); time.sleep(.18)
            ev.key.type=3
            assert x.XSendEvent(display,window,0,2,C.byref(ev)); x.XFlush(display); time.sleep(.6)
        key(ord('1')); key(ord('1')); time.sleep(2); key(0xff1b)
        wait(lambda v:v.get('view')=='main-menu',45)
        time.sleep(.6)
        key(0xff0d)
        wait(lambda v:v.get('bound') and v.get('view')=='map',45)
        key(0xffbf)  # F2
        army=wait(lambda v:v.get('view')=='army' and v.get('presented_view')=='army')
        key(0xffc9)  # F12
        captured=wait(lambda v:bool(v.get('last_capture')) and v.get('view')=='army')
        assert captured['canvas_sha256']==captured['presented_sha256']
        key(0xff1b)
        wait(lambda v:v.get('view')=='map')
        key(0xffc0)  # F3
        wait(lambda v:v.get('view')=='dismiss' and v.get('presented_view')=='dismiss')
        key(0xff1b)
        final=wait(lambda v:v.get('view')=='map')
        assert army['pair_token']==final['pair_token']
        (d/'receipt.json').write_text(json.dumps(dict(status='passed-original-player-gui',input='X11 key events',F2=True,F3=True,cancel_preserves_token=True,canvas_matches_presented=True,capture=captured['last_capture'],initial_token=army['pair_token'],final_token=final['pair_token'],legacy_card=False,limits='Native original F2/F3 presentation sampling; no new full battle X11 or natural recruitment claim.'),indent=2)+'\n')
    finally:
        if app is not None and app.poll() is None:
            app.terminate()
            try: app.wait(5)
            except subprocess.TimeoutExpired: app.kill(); app.wait()
        xvfb.terminate(); xvfb.wait(5); log.close()

if __name__=='__main__': main()
