#!/usr/bin/env python3
"""Sample ordinary shop inputs and cold Go stock recovery without F7."""
import argparse,contextlib,hashlib,json,os,signal,subprocess,time
from pathlib import Path
def read(p):return json.loads(p.read_text())
def write(p,v):
    with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);a=p.parse_args();q=a.work
    assert Path('/.dockerenv').exists()and os.getuid()==1000
    out=q/'gui-r1';out.mkdir();session=q/'gui-session-r1'
    subprocess.run([str(q/'camp-probe'),'-mode','init','-input',str(q/'inputs'),'-session',str(session)],check=True,timeout=15)
    env=dict(os.environ,DISPLAY=':98',LIBGL_ALWAYS_SOFTWARE='1',GALLIUM_DRIVER='llvmpipe',LP_NUM_THREADS='1',GOMAXPROCS='2');children=[];streams=[];screens=[];process=None;folder=None;phase=None
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(SystemExit(143)))
    def call(*args):
        v=subprocess.run([str(q/'xcheck'),*map(str,args)],env=env,capture_output=True,text=True,timeout=10);assert v.returncode==0,(args,v.stdout,v.stderr)
    def state():
        try:return read(folder/'ui-state.json')
        except(OSError,ValueError):return None
    def wait(test,seconds=90):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            if process.poll()is not None:raise AssertionError(('UI exited',process.returncode,(folder/'player.log').read_text()[-1800:]))
            s=state()
            if s and test(s):return s
            time.sleep(.05)
        raise AssertionError(('UI timeout',state()))
    def frames(n=6):
        before=state()['updates'];return wait(lambda s:s['updates']>=before+n)
    def key(k):
        before=state()['updates'];call('key',k,'down')
        try:wait(lambda s:s['updates']>=before+2,15)
        finally:call('key',k,'up')
        frames(2)
    def snap(name):
        old=state()['last_capture'];key('F12');s=wait(lambda s:s['last_capture']!=old and s['canvas_sha256']==s['presented_sha256']);call('screenshot',folder/(name+'.ppm'));write(folder/(name+'.json'),s);screens.append(dict(phase=phase,canvas=s['last_capture'],screen=name+'.ppm',metadata=name+'.json'));return s
    def start(name):
        nonlocal process,phase,folder
        phase=name;folder=out/name;folder.mkdir();log=(folder/'player.log').open('w');streams.append(log)
        process=subprocess.Popen([str(q/'camp-ui'),'-root','/game','-assets','/assets','-input',str(q/'inputs'),'-session',str(session),'-scratch',str(out/(name+'-shadow')),'-ui-assets',str(q/'ui-assets'),'-capture-dir',str(folder),'-scale','1','-mute'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(process)
        wait(lambda s:s['draws']>0);time.sleep(.4);key('1');key('1');time.sleep(.8)
        if state()['view']!='main-menu':key('Escape')
        wait(lambda s:s['view']=='main-menu');key('Return');return wait(lambda s:s['bound']and s['view']=='map'and s['presented_view']=='map')
    def stop():
        call('key','Control_L','down');call('key','q','down')
        try:assert process.wait(timeout=20)==0
        finally:call('key','q','up');call('key','Control_L','up')
    def shop():
        for movement in ['Left','Up']:
            key(movement);frames(8)
            if state()['recruit_icons']['active']:break
            key('F1');frames(8)
            if state()['recruit_icons']['active']:break
            key('Escape');frames(8)
        if not state()['recruit_icons']['active']:key('Up')
        return wait(lambda s:s['recruit_icons']['active']and s['recruit_icons']['ready']and s['recruit_icons']['frames']>0)
    try:
        log=(out/'xvfb.log').open('w');streams.append(log);x=subprocess.Popen(['Xvfb',':98','-screen','0','2560x1440x24','-nolisten','tcp'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(x)
        for _ in range(100):
            if Path('/tmp/.X11-unix/X98').exists():break
            assert x.poll()is None;time.sleep(.05)
        initial=start('warm');write(folder/'initial.json',initial);shop();first=snap('shop-icon');kind=first['recruit_icons']['kind'];stock=first['recruit_icons']['stock']
        key('1');key('Return');wait(lambda s:s['view']=='map'and not s['recruit_icons']['active']and s['world']['army']['gold']==4999)
        returned=snap('purchased-map');assert returned['world']['army']['slots'][0]==dict(unit='openkb:wolf',count=2500);assert returned['world']['army']['slots'][1]==dict(unit=f'native:{kind:02d}',count=1)
        assert returned['native_rows_hex']==initial['native_rows_hex'];pair=read(session/'gamedata.ay.army.json');assert pair['schema']=='eightsword-owned-world-save/4'
        keyid=next(k for k in pair['world']['army']['offers']if k.startswith('native-camp:'));assert pair['world']['army']['offers'][keyid]['stock']==stock-1
        native=(session/'gamedata.ay').read_bytes();write(folder/'pair-after-purchase.json',pair);stop()
        cold=start('cold');assert cold['world']==returned['world']and (session/'gamedata.ay').read_bytes()==native;shop();revisited=snap('shop-revisited');assert revisited['recruit_icons']['stock']==stock-1 and revisited['world']==returned['world']
        key('Escape');wait(lambda s:s['view']=='map'and not s['recruit_icons']['active']);cancelled=snap('cancelled-map');assert cancelled['world']==returned['world'];assert cancelled['pair_token']==returned['pair_token'];assert (session/'gamedata.ay').read_bytes()==native
        key('F2');wait(lambda s:s['view']=='army'and s['presented_view']=='army');army=snap('cold-army');key('Escape');wait(lambda s:s['view']=='map');stop()
        write(out/'receipt.json',dict(status='passed-actual-go-camp-stock',initial=initial,first=first,returned=returned,cold=cold,revisited=revisited,cancelled=cancelled,army=army,source_key=keyid,kind=kind,stock_before=stock,stock_after=stock-1,native_sha256=hashlib.sha256(native).hexdigest(),screens=screens,f7_used=False,controlled_initial_go_army=True,memory_injected=False,test_seed=False,formal_changed=False))
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
