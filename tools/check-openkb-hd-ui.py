#!/usr/bin/env python3
"""Actual F2 views covering eight openKB units, plus a controlled battle/cold read."""
import argparse,contextlib,json,os,signal,subprocess,time
from pathlib import Path
def read(p):return json.loads(p.read_text())
def write(p,v):
    with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);a=p.parse_args();q=a.work;out=q/'gui-r1';out.mkdir();assert Path('/.dockerenv').exists()and os.getuid()==1000
    env=dict(os.environ,DISPLAY=':98',LIBGL_ALWAYS_SOFTWARE='1',GALLIUM_DRIVER='llvmpipe',LP_NUM_THREADS='1',GOMAXPROCS='2');children=[];streams=[];screens=[];process=None;folder=None;phase=None
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(SystemExit(143)))
    def call(*args):
        v=subprocess.run([str(q/'xcheck'),*map(str,args)],env=env,capture_output=True,text=True,timeout=10);assert v.returncode==0,(args,v.stdout,v.stderr)
    def state():
        try:return read(folder/'ui-state.json')
        except(OSError,ValueError):return None
    def wait(test,seconds=120):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            if process.poll()is not None:raise AssertionError(('UI exited',process.returncode,(folder/'player.log').read_text()[-2200:]))
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
    def init_session(name,scenario):
        session=q/('session-'+name);subprocess.run([str(q/'openkb-probe'),'-mode','init','-input',str(q/'inputs'),'-session',str(session),'-scenario',scenario],check=True,timeout=20);return session
    def start(name,session,fixture=False):
        nonlocal process,phase,folder
        phase=name;folder=out/name;folder.mkdir();log=(folder/'player.log').open('w');streams.append(log)
        args=[str(q/('openkb-ui-fixture'if fixture else'openkb-ui')),'-root','/game','-assets','/assets','-input',str(q/'inputs'),'-session',str(session),'-scratch',str(folder/'scratch'),'-ui-assets',str(q/'ui-assets'),'-capture-dir',str(folder),'-scale','1','-mute']
        if fixture:args+=['-controlled-resume-fixture',str(q/'inputs/battle-before.state')]
        process=subprocess.Popen(args,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(process)
        wait(lambda s:s['draws']>0);time.sleep(.4);key('1');key('1');time.sleep(.8)
        if state()['view']!='main-menu':key('Escape')
        wait(lambda s:s['view']=='main-menu');key('Return');return wait(lambda s:s['bound'])
    def stop():
        call('key','Control_L','down');call('key','q','down')
        try:assert process.wait(timeout=20)==0
        finally:call('key','q','up');call('key','Control_L','up')
    try:
        log=(out/'xvfb.log').open('w');streams.append(log);x=subprocess.Popen(['Xvfb',':98','-screen','0','2560x1440x24','-nolisten','tcp'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(x)
        for _ in range(100):
            if Path('/tmp/.X11-unix/X98').exists():break
            assert x.poll()is None;time.sleep(.05)
        armies=[]
        for scenario in ['a','b']:
            session=init_session('army-'+scenario,scenario);initial=start('army-'+scenario,session);key('F2');wait(lambda s:s['view']=='army'and s['presented_view']=='army');army=snap('army-hd');assert army['world']==initial['world']and army['native_rows_hex']==initial['native_rows_hex'];assert army['unit_art']['loaded']==33 and not army['unit_art']['failures'];armies.append(army)
            if scenario=='a':key('Escape');wait(lambda s:s['view']=='map');key('F3');wait(lambda s:s['view']=='dismiss'and s['presented_view']=='dismiss');dismiss=snap('dismiss-hd');assert dismiss['world']==initial['world'];key('Escape');wait(lambda s:s['view']=='map')
            stop()
        session=init_session('battle','a');start('battle-warm',session,True);wait(lambda s:s['presence_prompt']);key('Return');wait(lambda s:s['view']=='battle'and s['presented_view']=='battle');opened=snap('battle-hd')
        token=opened['pair_token'];call('click',200,900);wait(lambda s:s['pair_token']!=token and len(s.get('combat_events',[]))>0);saved=snap('battle-action-hd');stop()
        start('battle-cold',session);wait(lambda s:s['view']=='battle'and s['presented_view']=='battle');cold=snap('battle-cold-hd');assert cold['world']==saved['world']and cold['pair_token']==saved['pair_token'];stop()
        write(out/'receipt.json',dict(status='passed-actual-openkb-hd-ui',armies=armies,dismiss=dismiss,opened=opened,saved=saved,cold=cold,screens=screens,controlled_initial_armies=True,controlled_battle_entry=True,natural_acquisition=False,formal_changed=False,test_seed=False))
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
