#!/usr/bin/env python3
"""One normal F7 save, exit, cold Continue and Go F2 review."""
import argparse,contextlib,json,os,signal,subprocess,time
from pathlib import Path
def read(p):return json.loads(p.read_text())
def write(p,v):
    with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);q=p.parse_args().work;assert Path('/.dockerenv').exists()and os.getuid()==1000
    out=q/'gui-r1';out.mkdir();env=dict(os.environ,DISPLAY=':98',LIBGL_ALWAYS_SOFTWARE='1',GALLIUM_DRIVER='llvmpipe',LP_NUM_THREADS='1',GOMAXPROCS='2');children=[];streams=[];screens=[];process=None;phase=None;folder=None
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(SystemExit(143)))
    def call(*args):
        v=subprocess.run([str(q/'xcheck'),*map(str,args)],env=env,capture_output=True,text=True,timeout=10);assert v.returncode==0,(args,v.stdout,v.stderr)
    def state():
        try:return read(folder/'ui-state.json')
        except(OSError,ValueError):return None
    def wait(test,seconds=120):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            if process.poll()is not None:raise AssertionError(('UI exited',process.returncode,(folder/'player.log').read_text()[-1800:]))
            s=state()
            if s and test(s):return s
            time.sleep(.05)
        raise AssertionError(('UI timeout',state()))
    def key(k):
        before=state()['updates'];call('key',k,'down')
        try:wait(lambda s:s['updates']>=before+2,15)
        finally:call('key',k,'up')
        after=state()['updates'];wait(lambda s:s['updates']>=after+2,15)
    def snap(name):
        old=state()['last_capture'];key('F12');s=wait(lambda s:s['last_capture']!=old and s['canvas_sha256']==s['presented_sha256']);call('screenshot',folder/(name+'.ppm'));write(folder/(name+'.json'),s);screens.append(dict(phase=phase,canvas=s['last_capture'],screen=name+'.ppm',metadata=name+'.json'));return s
    def start(name):
        nonlocal process,phase,folder
        phase=name;folder=out/name;folder.mkdir();log=(folder/'player.log').open('w');streams.append(log)
        process=subprocess.Popen([str(q/'checkpoint-ui'),'-root','/game','-assets','/assets','-input',str(q/'inputs'),'-session',str(q/'session-gui'),'-scratch',str(folder/'scratch'),'-ui-assets',str(q/'ui-assets'),'-capture-dir',str(folder),'-scale','1','-mute'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(process)
        wait(lambda s:s['draws']>0);time.sleep(.4);key('1');key('1');time.sleep(.8)
        if state()['view']!='main-menu':key('Escape')
        wait(lambda s:s['view']=='main-menu');key('Return');return wait(lambda s:s['bound']and s['view']=='map'and s['presented_view']=='map')
    def stop():
        call('key','Control_L','down');call('key','q','down')
        try:assert process.wait(timeout=20)==0
        finally:call('key','q','up');call('key','Control_L','up')
    try:
        log=(out/'xvfb.log').open('w');streams.append(log);x=subprocess.Popen(['Xvfb',':98','-screen','0','2560x1440x24','-nolisten','tcp'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(x)
        for _ in range(100):
            if Path('/tmp/.X11-unix/X98').exists():break
            assert x.poll()is None;time.sleep(.05)
        subprocess.run([str(q/'checkpoint-probe'),'-input',str(q/'inputs'),'-session',str(q/'session-gui'),'-mode','init'],env=env,check=True,timeout=20)
        initial=start('warm');key('Down');key('Down');frames=state()['draws'];moved=wait(lambda s:s['draws']>=frames+8)
        assert initial['native_location']['raw_words']!=moved['native_location']['raw_words']
        key('F7');wait(lambda s:s['view']=='system-menu');key('Return');key('Return')
        wait(lambda s:s['native_checkpoint_saves']==1 and not s['native_checkpoint_active']and s['view']=='map'and s['presented_view']=='map');saved=snap('saved-map');stop()
        cold=start('cold');cold=snap('cold-map');assert cold['world']==saved['world']and cold['native_location']==saved['native_location']
        key('F2');wait(lambda s:s['view']=='army'and s['presented_view']=='army');snap('cold-army');key('Escape');wait(lambda s:s['view']=='map');stop()
        write(out/'receipt.json',dict(status='passed-native-checkpoint-ui-cold',initial=initial,moved=moved,saved=saved,cold=cold,screens=screens,snapshot_load=False,test_seed=False,controlled_map_write=False,controlled_starting_army=True,format_promoted=False))
    finally:
        for child in reversed(children):
            if child.poll()is None:
                with contextlib.suppress(ProcessLookupError):os.killpg(child.pid,signal.SIGTERM)
                try:child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    with contextlib.suppress(ProcessLookupError):os.killpg(child.pid,signal.SIGKILL)
                    child.wait()
        for stream in streams:stream.close()
if __name__=='__main__':main()
