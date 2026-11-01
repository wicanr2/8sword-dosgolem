#!/usr/bin/env python3
"""Controlled total loss, cold choice, return replay, full checkpoint and F2."""
import argparse,contextlib,json,os,signal,subprocess,time,shutil
from pathlib import Path
def read(p):return json.loads(p.read_text())
def write(p,v):
    with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);a=p.parse_args();q=a.work;out=q/'gui-r1';out.mkdir();session=q/'session-gui-r1';assert Path('/.dockerenv').exists()and os.getuid()==1000
    env=dict(os.environ,DISPLAY=':98',LIBGL_ALWAYS_SOFTWARE='1',GALLIUM_DRIVER='llvmpipe',LP_NUM_THREADS='1',GOMAXPROCS='2');children=[];streams=[];screens=[];process=None;folder=None;phase=None
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(SystemExit(143)))
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
        old=state()['last_capture'];key('F12');s=wait(lambda s:s['last_capture']!=old and s['canvas_sha256']==s['presented_sha256']);call('screenshot',folder/(name+'.ppm'));write(folder/(name+'.json'),s);screens.append(dict(name=name,phase=phase,canvas=s['last_capture'],screen=name+'.ppm',metadata=name+'.json'));return s
    def start(name,fixture=False):
        nonlocal process,phase,folder
        phase=name;folder=out/name;folder.mkdir();log=(folder/'player.log').open('w');streams.append(log)
        args=[str(q/('annihilation-roam-fixture'if fixture else'annihilation-roam-ui')),'-root','/game','-assets','/assets','-input',str(q/'inputs'),'-session',str(session),'-scratch',str(folder/'scratch'),'-ui-assets',str(q/'ui-assets'),'-capture-dir',str(folder),'-scale','1','-mute']
        if fixture:args+=['-controlled-resume-fixture',str(q/'inputs/battle-before.state'),'-controlled-rear-enemy']
        process=subprocess.Popen(args,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(process);wait(lambda s:s['draws']>0);time.sleep(.4);key('1');key('1');time.sleep(.8)
        if state()['view']!='main-menu':key('Escape')
        wait(lambda s:s['view']=='main-menu');key('Return');return wait(lambda s:s['bound'])
    def stop():
        call('key','Control_L','down');call('key','q','down')
        try:assert process.wait(timeout=20)==0
        finally:call('key','q','up');call('key','Control_L','up')
    def action(x,y):
        token=state()['pair_token'];call('click',x,y);return wait(lambda s:s['pair_token']!=token)
    try:
        log=(out/'xvfb.log').open('w');streams.append(log);x=subprocess.Popen(['Xvfb',':98','-screen','0','2560x1440x24','-nolisten','tcp'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(x)
        for _ in range(100):
            if Path('/tmp/.X11-unix/X98').exists():break
            assert x.poll()is None;time.sleep(.05)
        start('warm',True);wait(lambda s:s['presence_prompt']);key('Return');opened=wait(lambda s:s['view']=='battle' and s['presented_view']=='battle')
        action(540,900);loss=snap('loss');assert loss['world']['battle']['state']['result']=='loss'
        shutil.copytree(session,q/'session-loss-r1');stop()
        start('cold-loss');wait(lambda s:s['view']=='battle' and s['presented_view']=='battle');cold=snap('cold-loss');assert cold['world']==loss['world']and cold['pair_token']==loss['pair_token']
        action(300,225);wait(lambda s:s['battle_finished']and s['view']=='map' and s['presented_view']=='map');returned=snap('returned');stop()
        start('cold-return');wait(lambda s:s['battle_finished']and s['view']=='map' and s['presented_view']=='map');replayed=snap('replayed');assert replayed['world']==returned['world']and replayed['pair_token']==returned['pair_token']and replayed['native_location']==returned['native_location']
        key('F7');wait(lambda s:s['view']=='system-menu');key('Return');key('Return');wait(lambda s:s['native_checkpoint_saves']==1 and not s['native_checkpoint_active']and s['view']=='map');checkpoint=snap('checkpoint');stop()
        start('cold-checkpoint');wait(lambda s:s['view']=='map' and s['presented_view']=='map');final=snap('checkpoint-cold');assert final['world']==checkpoint['world']and final['native_location']==checkpoint['native_location']
        key('F2');wait(lambda s:s['view']=='army' and s['presented_view']=='army');army=snap('empty-army');stop()
        write(out/'receipt.json',dict(status='passed-annihilation-roam-ui',opened=opened,loss=loss,cold=cold,returned=returned,replayed=replayed,checkpoint=checkpoint,final=final,army=army,screens=screens,controlled_initial_army=True,controlled_native_entry_and_enemy=True,normal_ui_clicks=True,test_seed=False,formal_changed=False))
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
