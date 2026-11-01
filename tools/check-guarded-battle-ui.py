#!/usr/bin/env python3
"""Ordinary native guard: Go strike, retreat, cold return, rematch and salary."""
import argparse,contextlib,json,os,signal,subprocess,time,shutil
from pathlib import Path
def read(p):return json.loads(p.read_text())
def write(p,v):
    with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--name',default='gui-r1');a=p.parse_args();q=a.work;out=q/a.name;out.mkdir();session=q/'session-gui-r1';assert Path('/.dockerenv').exists()and os.getuid()==1000
    env=dict(os.environ,DISPLAY=':98',LIBGL_ALWAYS_SOFTWARE='1',GALLIUM_DRIVER='llvmpipe',LP_NUM_THREADS='1',GOMAXPROCS='2');children=[];streams=[];screens=[];process=None;folder=None;phase=None
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(SystemExit(143)))
    def call(*args):
        r=subprocess.run([str(q/'xcheck'),*map(str,args)],env=env,capture_output=True,text=True,timeout=10);assert r.returncode==0,(args,r.stdout,r.stderr)
    def state():
        try:return read(folder/'ui-state.json')
        except(OSError,ValueError):return None
    def wait(test,seconds=90):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            if process.poll()is not None:raise AssertionError(('UI exit',process.returncode,(folder/'player.log').read_text()[-3000:]))
            s=state()
            if s and test(s):return s
            time.sleep(.05)
        write(folder/'timeout.json',state());raise AssertionError(('UI timeout',state().get('view'),state().get('battle_message')))
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
        args=[str(q/('guarded-battle-fixture'if fixture else'guarded-battle-ui')),'-root','/game','-assets','/assets','-input',str(q/'inputs'),'-session',str(session),'-scratch',str(folder/'scratch'),'-ui-assets',str(q/'ui-assets'),'-capture-dir',str(folder),'-scale','1','-mute']
        if fixture:args+=['-controlled-guard-position']
        process=subprocess.Popen(args,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(process);wait(lambda s:s['draws']>0);time.sleep(.4);key('1');key('1');time.sleep(.8)
        if state()['view']!='main-menu':key('Escape')
        wait(lambda s:s['view']=='main-menu');key('Return');return wait(lambda s:s['bound'])
    def stop():
        call('key','Control_L','down');call('key','q','down')
        try:assert process.wait(timeout=20)==0
        finally:call('key','q','up');call('key','Control_L','up')
    def action(x,y):
        token=state()['pair_token'];call('click',x,y);return wait(lambda s:s['pair_token']!=token)
    def card(side,slot):
        call('click',180+(slot%3)*290+side*960,420+(slot//3)*260)
        wait(lambda s:s['battle_source'if side==0 else'battle_target']==slot,15)
    def engage():
        key('Return');time.sleep(.4);key('Return');return wait(lambda s:s['view']=='battle'and s['presented_view']=='battle'and s.get('guarded_encounter'))
    try:
        log=(out/'xvfb.log').open('w');streams.append(log);x=subprocess.Popen(['Xvfb',':98','-screen','0','2560x1440x24','-nolisten','tcp'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(x)
        for _ in range(100):
            if Path('/tmp/.X11-unix/X98').exists():break
            assert x.poll()is None;time.sleep(.05)
        start('warm',True);key('Left');opened=engage();first=snap('guard-opened');action(200,900);strike=snap('guard-strike');shutil.copytree(session,q/'session-held-r1')
        key('Escape');wait(lambda s:s['battle_finished']and s['view']=='map'and s['presented_view']=='map');retreated=snap('guard-retreated');shutil.copytree(session,q/'session-retreated-r1');stop()
        start('cold-retreat');wait(lambda s:s['battle_finished']and s['view']=='map'and s['presented_view']=='map');cold=snap('guard-retreat-cold');assert cold['world']==retreated['world']and cold['pair_token']==retreated['pair_token'];key('Right');key('Left');rematch=engage();snap('guard-rematch')
        # Only normal UI commands; bounded play through the two front ranks.
        for turn in range(80):
            s=state()['world']['battle']['state']
            if s['result']=='win':break
            assert s['result']=='',s['result']
            acted=s['acted'];rows=s['rows'];targets=[i for i,v in enumerate(rows[1])if v['count']]
            source=next((i for i,v in enumerate(rows[0])if v['count']and not acted[0][i]),None)
            if source is not None:
                card(0,source)
                if source in[3,4]:action(890,900);continue
                target=source if source<3 and source not in[1,2]and rows[1][source]['count']else targets[0]
                card(1,target);action(200,900)
            elif any(v['count']and not acted[1][i]for i,v in enumerate(rows[1])):action(540,900)
            else:action(1190,900)
        else:raise AssertionError('bounded battle did not finish')
        won=snap('guard-won');action(1600,900);wait(lambda s:s['battle_finished']and s['view']=='map'and s['presented_view']=='map');settled=snap('guard-settled');shutil.copytree(session,q/'session-settled-r1');stop()
        start('cold-win');wait(lambda s:s['battle_finished']and s['view']=='map'and s['presented_view']=='map');replayed=snap('guard-win-cold');assert replayed['world']==settled['world']and replayed['pair_token']==settled['pair_token']
        key('F7');wait(lambda s:s['view']=='system-menu');key('Return');key('Return');wait(lambda s:s['native_checkpoint_saves']==1 and not s['native_checkpoint_active']and s['view']=='map');checkpoint=snap('guard-checkpoint');stop()
        start('cold-checkpoint');wait(lambda s:s['view']=='map'and s['presented_view']=='map');final=snap('guard-checkpoint-cold');assert final['world']==checkpoint['world'];key('F2');wait(lambda s:s['view']=='army'and s['presented_view']=='army');army=snap('mixed-army');stop()
        write(out/'receipt.json',dict(status='passed-guarded-battle-ui',opened=first,strike=strike,retreated=retreated,cold=cold,rematch=rematch,won=won,settled=settled,replayed=replayed,checkpoint=checkpoint,final=final,army=army,screens=screens,controlled_initial_army=True,controlled_initial_position=[6,4],native_guard_unmodified=True,normal_ui_clicks=True,test_seed=False,formal_changed=False))
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
