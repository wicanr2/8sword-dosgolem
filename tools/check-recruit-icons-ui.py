#!/usr/bin/env python3
"""One normal Continue -> HD shop icon -> purchase -> F7 -> cold F2 sample."""
import argparse,contextlib,json,os,signal,subprocess,time,shutil,struct
from pathlib import Path
def read(p):return json.loads(p.read_text())
def write(p,v):
    with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--run',choices=['gui-r3','gui-r4'],default='gui-r4');p.add_argument('--cold-only',action='store_true');a=p.parse_args();q=a.work;assert Path('/.dockerenv').exists()and os.getuid()==1000
    out=q/a.run;session=q/('native-session-'+a.run)
    if not a.cold_only:
        out.mkdir();session.mkdir();shutil.copyfile(q/'inputs/original-save.ay',session/'gamedata.ay')
        for f in (q/'inputs/maps').iterdir():shutil.copyfile(f,session/f.name)
    else:
        assert out.is_dir()and (session/'gamedata.ay').is_file()and not(out/'receipt.json').exists()
    profiles={p['native_kind']:p for p in read(q/'inputs/army-catalog.json')['profiles']if p.get('native_kind',0)>0}
    env=dict(os.environ,DISPLAY=':98',LIBGL_ALWAYS_SOFTWARE='1',GALLIUM_DRIVER='llvmpipe',LP_NUM_THREADS='1',GOMAXPROCS='2');children=[];streams=[];screens=[];process=None;phase=None;folder=None
    def rows(s):
        words=struct.unpack('<12H',bytes.fromhex(s['native_rows_hex']));return {words[i]:words[i+1]for i in range(0,12,2)if words[i]}
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
        process=subprocess.Popen([str(q/'recruit-ui'),'-native-game','-root','/game','-assets','/assets','-saves',str(session),'-ui-assets',str(q/'ui-assets'),'-capture-dir',str(folder),'-scale','1','-mute'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(process)
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
        if not a.cold_only:
            initial=start('warm')
            write(folder/'initial.json',initial)
            for movement in ['Left','Up']:
                key(movement);frames(8)
                if state()['recruit_icons']['active']:break
                key('F1');frames(8)
                if state()['recruit_icons']['active']:break
                key('Escape');frames(8)
            if not state()['recruit_icons']['active']:key('Up')
            wait(lambda s:s['recruit_icons']['active']and s['recruit_icons']['ready']and s['recruit_icons']['frames']>0)
            shop=snap('shop-icon');kind=shop['recruit_icons']['kind'];stock=shop['recruit_icons']['stock'];cost=profiles[kind]['gold'];assert shop['recruit_icons']['cached_kinds']==25
            key('1');typed=snap('shop-quantity');key('Return')
            wait(lambda s:s['view']=='map'and s['presented_view']=='map'and not s['recruit_icons']['active']and s['recruit_icons']['native_gold']==initial['recruit_icons']['native_gold']-cost)
            returned=snap('returned-map');assert rows(returned).get(kind)==rows(initial).get(kind,0)+1
            records=returned['recruit_icons']['events'];assert any(v['event']=='native-stock-after'and v['stock']==stock-1 and v['count']==1 for v in records)
            before=(session/'gamedata.ay').read_bytes();key('F7');wait(lambda s:s['view']=='system-menu');key('Return');key('Return');wait(lambda s:s['view']=='map'and s['presented_view']=='map');saved=snap('saved-map');assert (session/'gamedata.ay').read_bytes()!=before;stop()
        else:
            initial=read(out/'warm/initial.json')
            shop=read(out/'warm/shop-icon.json');typed=read(out/'warm/shop-quantity.json');returned=read(out/'warm/returned-map.json');saved=read(out/'warm/saved-map.json')
            kind=shop['recruit_icons']['kind'];stock=shop['recruit_icons']['stock'];cost=profiles[kind]['gold']
            for name in ['shop-icon','shop-quantity','returned-map','saved-map']:
                v=read(out/'warm'/(name+'.json'));screens.append(dict(phase='warm',canvas=v['last_capture'],screen=name+'.ppm',metadata=name+'.json'))
        cold=start('cold-final'if a.cold_only else 'cold');assert cold['native_rows_hex']==saved['native_rows_hex']and cold['recruit_icons']['native_gold']==saved['recruit_icons']['native_gold'];key('F2');wait(lambda s:s['view']=='army'and s['presented_view']=='army');army=snap('cold-army');key('Escape');wait(lambda s:s['view']=='map');stop()
        write(out/'receipt.json',dict(status='passed-actual-hd-recruit-icons',initial=initial,shop=shop,typed=typed,returned=returned,saved=saved,cold=cold,army=army,screens=screens,native_army_path=True,controlled_starting_army=False,memory_injected=False,test_seed=False,formal_changed=False,kind=kind,stock=stock,cost=cost))
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
