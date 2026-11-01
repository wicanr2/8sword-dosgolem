#!/usr/bin/env python3
"""Purchased v5 army -> normal encounter -> wolf action -> cold battle -> retreat and F7."""
import argparse,contextlib,json,os,signal,subprocess,time
from pathlib import Path
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--batch',default='gui-r1');a=p.parse_args();q=a.work;out=q/a.batch;out.mkdir();session=q/'session';assert Path('/.dockerenv').exists()and os.getuid()==1000
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
  process=subprocess.Popen([str(q/'reinforcement-ui'),'-root','/game','-assets','/assets','-input',str(q/'inputs'),'-session',str(session),'-scratch',str(folder/'scratch'),'-ui-assets',str(q/'ui-assets'),'-capture-dir',str(folder),'-encounter-evidence',str(folder),'-scale','1','-mute'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(process);wait(lambda s:s['draws']>0);time.sleep(.4);key('1');key('1');time.sleep(.8)
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
  initial=start('warm');wait(lambda s:s['view']=='map');initial=snap('purchased-army-map');assert initial['world']['army']['slots'][1]==dict(unit='openkb:wolf',count=1)
  offers=initial['reinforcements']['offers'];moves=[]
  for k in ['Down','Down','Down','Right']:
   if state()['presence_prompt']:break
   key(k);moves.append(k)
  for n in range(128):
   if state()['presence_prompt']:break
   k='Right'if n%2==0 else'Left';key(k);moves.append(k)
  wait(lambda s:s['presence_prompt']);prompt=snap('natural-confirmation')
  raw=(folder/'natural-confirmation.ppm').read_bytes().split(b'\n',3)[3]
  red=sum(raw[(y*1920+xx)*3]>180 and raw[(y*1920+xx)*3+1]<120 and raw[(y*1920+xx)*3+2]<130 for y in range(798,888)for xx in range(624,720))
  if red>1000:key('Left')
  key('Return');wait(lambda s:s['view']=='battle'and s['world']['battle']is not None);opened=snap('purchased-wolf-battle');assert not opened['guarded_encounter']
  battle=opened['world']['battle']['state'];rows=battle['rows'];assert rows[0][1]==dict(unit='openkb:wolf',count=1)
  target=1 if rows[1][1]['count']else next(i for i,r in enumerate(rows[1])if r['count'])
  click(480,420);click(1140+(target%3)*290,420+(target//3)*260)
  token=state()['pair_token'];click(200,900);wait(lambda s:s['pair_token']!=token);acted=snap('wolf-acted');assert acted['world']['battle']['state']['acted'][0][1]
  write(folder/'pair-after-action.json',read(session/'gamedata.ay.army.json'));stop()
  cold=start('cold-battle');wait(lambda s:s['view']=='battle');cold=snap('cold-wolf-action');assert cold['world']==acted['world']and cold['pair_token']==acted['pair_token'];assert cold['reinforcements']['offers']==offers
  held=state()['guest_steps'];frames(12);assert state()['guest_steps']==held
  click(280,225);wait(lambda s:s['battle_finished']and s['view']=='map'and s['world']['battle']is None);returned=snap('returned-map');assert returned['reinforcements']['offers']==offers
  write(folder/'pair-after-return.json',read(session/'gamedata.ay.army.json'));stop()
  cold_return=start('cold-return');wait(lambda s:s['view']=='map');cold_return=snap('cold-return');assert cold_return['world']==returned['world']and cold_return['pair_token']==returned['pair_token']
  key('F7');wait(lambda s:s['view']=='system-menu');key('Return');key('Return');wait(lambda s:s.get('native_checkpoint_saves')==1 and not s.get('native_checkpoint_active')and s['view']=='map');saved=snap('f7-map');assert saved['reinforcements']['offers']==offers;stop()
  final=start('cold-f7');wait(lambda s:s['view']=='map');assert final['world']==saved['world'];key('F2');wait(lambda s:s['view']=='army');army=snap('cold-recruited-army');stop()
  write(out/'receipt.json',dict(status='passed-purchased-reinforcement-v5-battle',initial=initial,prompt=prompt,opened=opened,acted=acted,cold_battle=cold,returned=returned,cold_return=cold_return,saved=saved,final=final,army=army,moves=moves,target=target,screens=screens,memory_injected=False,test_seed=False,pregranted_openkb_units=False,formal_promoted=False))
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
