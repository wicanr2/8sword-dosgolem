#!/usr/bin/env python3
"""One normal Continue/movement/encounter/return/save chain."""
import argparse, contextlib, json, os, signal, subprocess, time
from pathlib import Path
def read(p): return json.loads(p.read_text())
def write(p,v):
    with p.open('x') as f: json.dump(v,f,ensure_ascii=False,indent=2); f.write('\n')
def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--work',type=Path,required=True)
    p.add_argument('--encounters',type=int,choices=[1,2],default=1); args=p.parse_args(); q=args.work
    assert Path('/.dockerenv').exists() and os.getuid()==1000
    out=q/'gui-r1'; out.mkdir(); env=dict(os.environ,DISPLAY=':98',LIBGL_ALWAYS_SOFTWARE='1',GALLIUM_DRIVER='llvmpipe',LP_NUM_THREADS='1',GOMAXPROCS='2')
    children=[]; streams=[]; screens=[]; battles=[]; returns=[]; process=None
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(SystemExit(143)))
    def call(*args):
        v=subprocess.run([str(q/'xcheck'),*map(str,args)],env=env,capture_output=True,text=True,timeout=10); assert v.returncode==0,(args,v.stdout,v.stderr)
    def state():
        try: return read(out/'ui-state.json')
        except (OSError,ValueError): return None
    def wait(test,seconds=120):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            if process.poll() is not None: raise AssertionError(('UI exited',process.returncode,(out/'player.log').read_text()[-2500:]))
            s=state()
            if s and test(s): return s
            time.sleep(.05)
        raise AssertionError(('UI timeout',state()))
    def key(k):
        # Keep XTEST transitions across actual Update calls. The full HD canvas
        # can render more slowly than the helper's default 80ms key pulse.
        before=state()['updates']; call('key',k,'down')
        try: wait(lambda s:s['updates']>=before+2,15)
        finally: call('key',k,'up')
        after=state()['updates']; wait(lambda s:s['updates']>=after+2,15)
    def snap(name):
        old=state()['last_capture']; key('F12'); s=wait(lambda s:s['last_capture']!=old and s['canvas_sha256']==s['presented_sha256'])
        call('screenshot',out/(name+'.ppm')); write(out/(name+'.json'),s)
        screens.append(dict(canvas=s['last_capture'],screen=name+'.ppm',metadata=name+'.json')); return s
    try:
        log=(out/'xvfb.log').open('w'); streams.append(log)
        x=subprocess.Popen(['Xvfb',':98','-screen','0','2560x1440x24','-nolisten','tcp'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True); children.append(x)
        for _ in range(100):
            if Path('/tmp/.X11-unix/X98').exists(): break
            assert x.poll() is None; time.sleep(.05)
        subprocess.run([str(q/'paired-reader'),'-input',str(q/'inputs'),'-dir',str(q/'session'),'-world','world-normal.json','-mode','init'],check=True,env=env,timeout=20)
        log=(out/'player.log').open('w'); streams.append(log)
        process=subprocess.Popen([str(q/'normal-ui'),'-root','/game','-assets','/assets','-input',str(q/'inputs'),'-session',str(q/'session'),'-scratch',str(out/'scratch'),'-ui-assets',str(q/'ui-assets'),'-capture-dir',str(out),'-encounter-evidence',str(out),'-scale','1','-mute'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True); children.append(process)
        wait(lambda s:s['draws']>0); time.sleep(.4); key('1'); time.sleep(.4); key('1'); time.sleep(.8)
        if state()['view']!='main-menu': key('Escape')
        wait(lambda s:s['view']=='main-menu'); key('Return')
        initial=wait(lambda s:s['bound'] and s['view']=='map' and s['presented_view']=='map'); write(out/'initial.json',initial)
        # The saved hero starts beside the militia town. Leave the town's row
        # before alternating horizontally; Right from the initial cell opens
        # recruitment instead of advancing the encounter path.
        moves=['Down','Down']
        for k in moves: key(k)
        for sequence in range(1,args.encounters+1):
            for n in range(128):
                s=state()
                if s['presence_prompt'] and s['encounter_sequence']==sequence: break
                k='Right' if n%2==0 else 'Left'; key(k); moves.append(k)
            # The legacy scene classifier can keep "map" for this real prompt.
            # Use the original confirmation context, as in the saved GUI proof.
            wait(lambda s:s['presence_prompt'] and s['encounter_sequence']==sequence)
            prompt=snap('confirmation-%d'%sequence)
            raw=(out/screens[-1]['screen']).read_bytes().split(b'\n',3)[3]
            red=sum(raw[(y*1920+x)*3]>180 and raw[(y*1920+x)*3+1]<120 and raw[(y*1920+x)*3+2]<130 for y in range(798,888) for x in range(624,720))
            # The original red selection rectangle at No is visible in X11.
            # Choose Yes only when No is selected; do not assume Left clamps.
            if red>1000: key('Left')
            key('Return')
            b=wait(lambda s:s['battle_opened'] and s['encounter_sequence']==sequence and s['view']=='battle' and s['presented_view']=='battle' and s['world']['battle'] is not None)
            battles.append(b)
            if sequence==1: snap('battle-first')
            call('click',280,225)
            back=wait(lambda s:s['battle_finished'] and s['presence_completed']==sequence and not s['presence_active'] and s['world']['battle'] is None and s['view']=='map' and s['presented_view']=='map')
            returns.append(back)
        snap('returned-map')
        key('F2'); wait(lambda s:s['view']=='army' and s['presented_view']=='army'); snap('army-after'); key('Escape'); wait(lambda s:s['view']=='map')
        call('key','Control_L','down'); call('key','q','down')
        try: assert process.wait(timeout=20)==0
        finally: call('key','q','up'); call('key','Control_L','up')
        subprocess.run([str(q/'paired-reader'),'-input',str(q/'inputs'),'-dir',str(q/'session'),'-world','world-normal.json','-mode','read','-out',str(out/'cold.json')],check=True,env=env,timeout=20)
        write(out/'receipt.json',dict(status='passed-normal-map-entry',encounters=args.encounters,initial=initial,battles=battles,returns=returns,final=read(out/'ui-final.json'),cold=read(out/'cold.json'),screens=screens,moves=moves,snapshot_load=False,test_seed=False,controlled_starting_army=True))
    finally:
        for child in reversed(children):
            if child.poll() is None:
                with contextlib.suppress(ProcessLookupError): os.killpg(child.pid,signal.SIGTERM)
                try: child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    with contextlib.suppress(ProcessLookupError): os.killpg(child.pid,signal.SIGKILL)
                    child.wait()
        for stream in streams: stream.close()
if __name__=='__main__': main()
