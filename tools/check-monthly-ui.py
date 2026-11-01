#!/usr/bin/env python3
"""One controlled countdown boundary with ordinary movement, monthly report and cold F2."""
import argparse,contextlib,json,os,signal,subprocess,time
from pathlib import Path
def read(p):return json.loads(p.read_text())
def write(p,v):
    with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);a=p.parse_args();q=a.work;out=q/'gui-r1';out.mkdir();session=q/'session-gui-r1';assert Path('/.dockerenv').exists()and os.getuid()==1000
    subprocess.run([str(q/'monthly-candidate'),'-input',str(q/'inputs'),'-mode','init','-session',str(session)],check=True,timeout=20)
    env=dict(os.environ,DISPLAY=':98',LIBGL_ALWAYS_SOFTWARE='1',GALLIUM_DRIVER='llvmpipe',LP_NUM_THREADS='1',GOMAXPROCS='2');children=[];streams=[];screens=[];process=None;folder=None;phase=None
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(SystemExit(143)))
    def call(*args):
        r=subprocess.run([str(q/'xcheck'),*map(str,args)],env=env,capture_output=True,text=True,timeout=10);assert r.returncode==0,(args,r.stdout,r.stderr)
    def state():
        try:return read(folder/'ui-state.json')
        except(OSError,ValueError):return None
    def wait(test,seconds=120):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            if process.poll()is not None:raise AssertionError(('UI exit',process.returncode,(folder/'player.log').read_text()[-2200:]))
            s=state()
            if s and test(s):return s
            time.sleep(.05)
        raise AssertionError(('UI timeout',state()))
    def key(k):
        before=state()['updates'];call('key',k,'down')
        try:wait(lambda s:s['updates']>=before+2,15)
        finally:call('key',k,'up')
        before=state()['updates'];wait(lambda s:s['updates']>=before+2,15)
    def snap(name):
        old=state()['last_capture'];key('F12');s=wait(lambda s:s['last_capture']!=old and s['canvas_sha256']==s['presented_sha256']);call('screenshot',folder/(name+'.ppm'));write(folder/(name+'.json'),s);screens.append(dict(phase=phase,canvas=s['last_capture'],screen=name+'.ppm',metadata=name+'.json'));return s
    def start(name):
        nonlocal process,phase,folder
        phase=name;folder=out/name;folder.mkdir();evidence=folder/'evidence';evidence.mkdir();log=(folder/'player.log').open('w');streams.append(log)
        args=[str(q/('monthly-ui-fixture'if name=='warm'else'monthly-ui')),'-root','/game','-assets','/assets','-input',str(q/'inputs'),'-session',str(session),'-scratch',str(folder/'scratch'),'-ui-assets',str(q/'ui-assets'),'-capture-dir',str(folder),'-monthly-evidence',str(evidence),'-scale','1','-mute']
        if name=='warm':args+=['-controlled-monthly-boundary']
        process=subprocess.Popen(args,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(process);wait(lambda s:s['draws']>0);time.sleep(.4);key('1');key('1');time.sleep(.8)
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
        initial=start('warm');write(folder/'initial.json',initial);assert initial['world']['army']['gold']==500 and initial['world']['army']['offers']['native-camp:00:01']['stock']==2900
        key('Down');wait(lambda s:s['monthly']['saves']==1 and s['monthly']['committed']);report=snap('monthly-report');assert report['world']['army']['gold']==370 and report['world']['army']['offers']['native-camp:00:01']['stock']==3000
        if state()['monthly']['active']:key('Return')
        wait(lambda s:not s['monthly']['active']and s['view']=='map'and s['presented_view']=='map');returned=snap('monthly-map');assert returned['native_rows_hex']==initial['native_rows_hex'];assert returned['world']['army']['slots']==initial['world']['army']['slots'];stop()
        cold=start('cold');assert cold['world']==returned['world']and cold['pair_token']==returned['pair_token']and cold['monthly']['saves']==0;key('F2');wait(lambda s:s['view']=='army'and s['presented_view']=='army');army=snap('cold-army');assert army['world']==returned['world'];key('Escape');wait(lambda s:s['view']=='map');stop()
        write(out/'receipt.json',dict(status='passed-monthly-ui-cold',initial=initial,report=report,returned=returned,cold=cold,army=army,screens=screens,controlled_countdown=True,controlled_initial_army=True,ordinary_continue_and_movement=True,native_army_unchanged=True,f7_used=False,formal_changed=False))
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
