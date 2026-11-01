#!/usr/bin/env python3
"""Normal camp -> eight HD offers -> owned purchase -> F7 and cold reopen."""
import argparse,contextlib,json,os,signal,subprocess,time
from pathlib import Path
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--batch',default='gui-r2');p.add_argument('--cold-only',action='store_true');a=p.parse_args();q=a.work;out=q/a.batch;out.mkdir();session=q/'session-gui-r2';assert Path('/.dockerenv').exists()and os.getuid()==1000
 env=dict(os.environ,DISPLAY=':98',LIBGL_ALWAYS_SOFTWARE='1',GALLIUM_DRIVER='llvmpipe',LP_NUM_THREADS='1',GOMAXPROCS='2');children=[];streams=[];screens=[];process=None;folder=None;phase=None
 signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(SystemExit(143)))
 def call(*args):
  p=subprocess.run([str(q/'xcheck'),*map(str,args)],env=env,capture_output=True,text=True,timeout=10);assert p.returncode==0,(args,p.stdout,p.stderr)
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
  write(folder/'timeout.json',state());raise AssertionError(('timeout',state().get('view'),state().get('reinforcements')))
 def frames(n=6):
  u=state()['updates'];return wait(lambda s:s['updates']>=u+n,20)
 def key(k):
  u=state()['updates'];call('key',k,'down')
  try:wait(lambda s:s['updates']>=u+2,20)
  finally:call('key',k,'up')
  frames(2)
 def click(x,y):call('click',x,y);frames(4)
 def snap(name):
  old=state()['last_capture'];key('F12');s=wait(lambda s:s['last_capture']!=old and s['canvas_sha256']==s['presented_sha256']);call('screenshot',folder/(name+'.ppm'));write(folder/(name+'.json'),s);screens.append(dict(name=name,phase=phase,canvas=s['last_capture'],screen=name+'.ppm',metadata=name+'.json'));return s
 def start(name):
  nonlocal process,phase,folder
  phase=name;folder=out/name;folder.mkdir();log=(folder/'player.log').open('w');streams.append(log)
  process=subprocess.Popen([str(q/'reinforcement-ui'),'-root','/game','-assets','/assets','-input',str(q/'inputs'),'-session',str(session),'-scratch',str(folder/'scratch'),'-ui-assets',str(q/'ui-assets'),'-capture-dir',str(folder),'-scale','1','-mute'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(process);wait(lambda s:s['draws']>0);time.sleep(.4);key('1');key('1');time.sleep(.8)
  if state()['view']!='main-menu':key('Escape')
  wait(lambda s:s['view']=='main-menu');key('Return');return wait(lambda s:s['bound']and s['view']=='map')
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
  if a.cold_only:
   final=start('cold-final');assert final['world']==read(q/'gui-r2/receipt.json')['checkpoint']['world'];key('F2');wait(lambda s:s['view']=='army');army=snap('final-cold-army');key('Escape');wait(lambda s:s['view']=='map');shop();click(600,65);wait(lambda s:s['view']=='reinforcements');opened=snap('final-cold-offers');assert next(o['stock']for o in opened['reinforcements']['offers'].values()if o['unit']=='openkb:wolf')==74;stop();write(out/'receipt.json',dict(status='passed-final-reinforcement-cold-ui',army=army,opened=opened,screens=screens));return
  initial=start('warm');shop();original=snap('original-shop');stock=original['recruit_icons']['stock'];kind=original['recruit_icons']['kind']
  click(600,65);wait(lambda s:s['view']=='reinforcements');opened=snap('eight-hd-units');assert len(opened['reinforcements']['offers'])==8;wolf_stock=next(o['stock']for o in opened['reinforcements']['offers'].values()if o['unit']=='openkb:wolf')
  steps=opened['guest_steps'];frames(20);assert state()['guest_steps']==steps,'Go page advanced guest'
  key('F10');lishu=snap('eight-hd-lishu');assert lishu['font_id']=='lishu'
  key('Escape');wait(lambda s:s['view']=='recruit');assert not state()['reinforcements']['active'];click(600,65);wait(lambda s:s['view']=='reinforcements');assert state()['pair_token']==opened['pair_token']
  click(1600,940);returned=wait(lambda s:s['view']=='map'and not s['recruit_icons']['active']and s['reinforcements']['purchases']==1);returned=snap('recruited-map')
  assert returned['world']['army']['gold']==460 and returned['world']['army']['slots'][1]==dict(unit='openkb:wolf',count=1);assert returned['native_rows_hex']==initial['native_rows_hex']
  saved_before=read(session/'gamedata.ay.army.json');assert saved_before['schema']=='eightsword-owned-world-save/5';stop()
  cold=start('cold-no-f7');assert cold['world']==returned['world'];shop();assert state()['recruit_icons']['kind']==kind and state()['recruit_icons']['stock']==stock
  click(600,65);wait(lambda s:s['view']=='reinforcements');revisited=snap('stock-cold');assert next(o['stock']for o in revisited['reinforcements']['offers'].values()if o['unit']=='openkb:wolf')==wolf_stock-1
  # Native rules cannot silently drop a recruited openKB stack.
  click(1100,180);assert state()['world']['army']['rules']=='tactics';key('Escape');key('Escape');wait(lambda s:s['view']=='map'and not s['reinforcements']['shop_open'])
  key('F2');wait(lambda s:s['view']=='army');army=snap('recruited-army');key('Escape');wait(lambda s:s['view']=='map')
  key('F7');wait(lambda s:s['view']=='system-menu');key('Return');key('Return');wait(lambda s:s.get('native_checkpoint_saves')==1 and not s.get('native_checkpoint_active')and s['view']=='map');checkpoint=snap('f7-checkpoint');stop()
  final=start('cold-f7');assert final['world']==checkpoint['world'];key('F2');wait(lambda s:s['view']=='army');final_army=snap('f7-cold-army');stop()
  write(out/'receipt.json',dict(status='passed-reinforcement-camp-ui',initial=initial,original=original,opened=opened,returned=returned,cold=cold,revisited=revisited,army=army,checkpoint=checkpoint,final=final,final_army=final_army,guest_held_steps=steps,screens=screens,controlled_starting_go_army=True,pregranted_openkb_units=False,memory_injected=False,natural_camp_entry=True,test_seed=False,formal_promoted=False))
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
