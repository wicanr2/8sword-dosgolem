#!/usr/bin/env python3
"""Native boss and final rosters; UI combat, sword checkpoint and cold HD ending."""
import argparse,contextlib,json,os,signal,subprocess,time,shutil
from pathlib import Path
def read(p):return json.loads(p.read_text())
def write(p,v):
    with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--resume-final',action='store_true');p.add_argument('--resume-ending',action='store_true');a=p.parse_args();q=a.work;out=q/('gui-r3'if a.resume_ending else'gui-r2'if a.resume_final else'gui-r1');out.mkdir();session=q/'session-boss-r1';assert Path('/.dockerenv').exists()and os.getuid()==1000
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
            if process.poll()is not None:raise AssertionError(('UI exit',process.returncode,(folder/'player.log').read_text()[-3000:]))
            s=state()
            if s and test(s):return s
            time.sleep(.05)
        write(folder/'timeout.json',state());raise AssertionError(('UI timeout',state().get('view'),state().get('battle_message'),state().get('ending')))
    def key(k):
        before=state()['updates'];call('key',k,'down')
        try:wait(lambda s:s['updates']>=before+2,20)
        finally:call('key',k,'up')
        before=state()['updates'];wait(lambda s:s['updates']>=before+2,20)
    def snap(name):
        old=state()['last_capture'];key('F12');s=wait(lambda s:s['last_capture']!=old and s['canvas_sha256']==s['presented_sha256']);call('screenshot',folder/(name+'.ppm'));write(folder/(name+'.json'),s);screens.append(dict(name=name,phase=phase,canvas=s['last_capture'],screen=name+'.ppm',metadata=name+'.json'));return s
    def start(name,fixture=''):
        nonlocal process,phase,folder
        phase=name;folder=out/name;folder.mkdir();log=(folder/'player.log').open('w');streams.append(log)
        args=[str(q/('sword-guards-fixture'if fixture else'sword-guards-ui')),'-root','/game','-assets','/assets','-input',str(q/'inputs'),'-session',str(session),'-scratch',str(folder/'scratch'),'-ui-assets',str(q/'ui-assets'),'-capture-dir',str(folder),'-scale','1','-mute']
        if fixture:args+=['-controlled-sword-position',fixture]
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
        call('click',180+(slot%3)*290+side*960,420+(slot//3)*260);wait(lambda s:s['battle_source'if side==0 else'battle_target']==slot,20)
    def fight():
        profiles=read(q/'inputs/combat-catalog.json')['profiles']
        for turn in range(240):
            s=state()['world']['battle']['state']
            if s['result']=='win':return
            assert s['result']=='',s['result'];acted=s['acted'];rows=s['rows'];targets=[i for i,v in enumerate(rows[1])if v['count']];source=next((i for i,v in enumerate(rows[0])if v['count']and not acted[0][i]),None)
            if source is not None:
                card(0,source);ranged=profiles[rows[0][source]['unit']].get('ranged',False)
                if source>=3 and not ranged:action(890,900);continue
                target=source if source<3 and not ranged and rows[1][source]['count']else targets[0];card(1,target);action(200,900)
            elif any(v['count']and not acted[1][i]for i,v in enumerate(rows[1])):action(540,900)
            else:action(1190,900)
        raise AssertionError('bounded combat did not finish')
    def engage():
        key('Left');key('Return');time.sleep(.4);key('Return');return wait(lambda s:s['view']=='battle'and s['presented_view']=='battle')
    try:
        log=(out/'xvfb.log').open('w');streams.append(log);x=subprocess.Popen(['Xvfb',':98','-screen','0','2560x1440x24','-nolisten','tcp'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(x)
        for _ in range(100):
            if Path('/tmp/.X11-unix/X98').exists():break
            assert x.poll()is None;time.sleep(.05)
        if a.resume_final or a.resume_ending:
            old={}
            for k,ph,n in[('boss_opened','boss','boss-opened'),('boss_won','boss','boss-won'),('boss_return','boss','boss-return'),('boss_character','boss','boss-character'),('checkpoint','boss','boss-checkpoint'),('boss_cold','cold-boss','boss-cold-character')]:
                old[k]=read(q/'gui-r1'/ph/(n+'.json'));screens.append(dict(name=n,phase=ph,canvas=old[k]['last_capture'],screen=n+'.ppm',metadata=n+'.json',batch='gui-r1'))
            boss_opened,boss_won,boss_return,boss_character,checkpoint,boss_cold=[old[k]for k in['boss_opened','boss_won','boss_return','boss_character','checkpoint','boss_cold']]
        else:
            start('boss','boss');engage();boss_opened=snap('boss-opened');fight();boss_won=snap('boss-won');shutil.copytree(session,q/'session-won-r1');action(1600,900);wait(lambda s:s['battle_finished']and s['view']=='map');boss_return=snap('boss-return');assert boss_return['swords']==[True]+[False]*7
            key('F1');wait(lambda s:s['view']=='character');boss_character=snap('boss-character');key('Escape');key('F7');wait(lambda s:s['view']=='system-menu');key('Return');key('Return');wait(lambda s:s['native_checkpoint_saves']==1 and not s['native_checkpoint_active']and s['view']=='map');checkpoint=snap('boss-checkpoint');stop()
            start('cold-boss');wait(lambda s:s['view']=='map');key('F1');wait(lambda s:s['view']=='character');boss_cold=snap('boss-cold-character');assert boss_cold['swords']==boss_return['swords']and boss_cold['world']==checkpoint['world'];stop()
        if a.resume_ending:
            start('cold-boss-hud');wait(lambda s:s['view']=='map');key('F1');wait(lambda s:s['view']=='character');boss_cold=snap('boss-sword-hud');assert any(t['Role']=='swords'and t['Text']=='八劍: 1 / 8'for t in boss_cold['text_fields']);stop()
            old={}
            for k,n in[('final_opened','final-opened'),('final_won','final-won'),('committed','ending-committed')]:
                old[k]=read(q/'gui-r2/final'/(n+'.json'));screens.append(dict(name=n,phase='final',canvas=old[k]['last_capture'],screen=n+'.ppm',metadata=n+'.json',batch='gui-r2'))
            final_opened,final_won,committed=[old[k]for k in['final_opened','final_won','committed']];session=q/'session-final-r2'
        else:
            session=q/('session-final-r2'if a.resume_final else'session-final-r1');start('final','final');engage();final_opened=snap('final-opened');fight();final_won=snap('final-won');action(1600,900);committed=snap('ending-committed');shutil.copytree(session,q/'session-final-return-r1');stop()
        start('cold-ending');wait(lambda s:s.get('ending',{}).get('active'));wait(lambda s:s.get('ending',{}).get('stage')=='END7.AY',seconds=240);ending=snap('hd-ending');wait(lambda s:s.get('engine_exited'),seconds=240);complete=snap('ending-complete');assert complete['engine_exit_code']==0 and complete['world']==committed['world']and complete['pair_token']==committed['pair_token'];stop()
        write(out/'receipt.json',dict(status='passed-sword-guards-ui',boss_opened=boss_opened,boss_won=boss_won,boss_return=boss_return,boss_character=boss_character,checkpoint=checkpoint,boss_cold=boss_cold,final_opened=final_opened,final_won=final_won,committed=committed,ending=ending,complete=complete,screens=screens,controlled_initial_army_and_position=True,native_enemies_unmodified=True,test_seed=False,formal_promoted=False))
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
