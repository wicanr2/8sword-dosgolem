#!/usr/bin/env python3
"""XTEST sampling after an explicit fixed-state injection, never a natural-path claim."""
import argparse,contextlib,json,os,signal,subprocess,time
from pathlib import Path
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);a=p.parse_args();q=a.work;assert Path('/.dockerenv').exists()and os.getuid()==1000
 out=q/'gui-r1';out.mkdir();env=dict(os.environ,DISPLAY=':98',LIBGL_ALWAYS_SOFTWARE='1',GALLIUM_DRIVER='llvmpipe',LP_NUM_THREADS='1',GOMAXPROCS='2');children=[];streams=[];cases=[];folder=None;process=None
 signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(SystemExit(143)))
 def call(*args):
  v=subprocess.run([str(q/'xcheck'),*map(str,args)],env=env,capture_output=True,text=True,timeout=10);assert v.returncode==0,(args,v.stdout,v.stderr);return v.stdout
 def state():
  try:return read(folder/'ui-state.json')
  except(OSError,ValueError):return None
 def wait(test,seconds=120):
  end=time.monotonic()+seconds
  while time.monotonic()<end:
   if process.poll()is not None:raise AssertionError(('UI exited',process.returncode,(folder/'player.log').read_text()[-2500:]))
   s=state()
   if s and test(s):return s
   time.sleep(.05)
  raise AssertionError(('UI timeout',state()))
 def key(k):call('key',k)
 def snap(name,screens):
  old=state()['last_capture'];key('F12');s=wait(lambda s:s['last_capture']!=old and s['canvas_sha256']==s['presented_sha256']);call('screenshot',folder/(name+'.ppm'));write(folder/(name+'.json'),s);screens.append(dict(canvas=s['last_capture'],screen=name+'.ppm',metadata=name+'.json'));return s
 try:
  log=(out/'xvfb.log').open('w');streams.append(log);xvfb=subprocess.Popen(['Xvfb',':98','-screen','0','2560x1440x24','-nolisten','tcp'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(xvfb)
  for _ in range(100):
   if Path('/tmp/.X11-unix/X98').exists():break
   assert xvfb.poll()is None;time.sleep(.05)
  for name in ['win','retreat']:
   folder=out/name;folder.mkdir();screens=[]
   cmd=[str(q/'paired-reader'),'-input',str(q/'inputs'),'-dir',str(q/('session-'+name)),'-world','world-'+name+'.json','-mode','init'];subprocess.run(cmd,check=True,env=env,timeout=20)
   log=(folder/'player.log').open('w');streams.append(log)
   process=subprocess.Popen([str(q/'encounter-ui'),'-root','/game','-assets','/assets','-input',str(q/'inputs'),'-session',str(q/('session-'+name)),'-scratch',str(folder/'scratch'),'-ui-assets',str(q/'ui-assets'),'-capture-dir',str(folder),'-controlled-state',str(q/'inputs/battle-before.state'),'-controlled-evidence',str(folder),'-controlled-case',name,'-scale','1','-mute'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(process)
   wait(lambda s:s['draws']>0);time.sleep(.4);key('1');time.sleep(.4);key('1');time.sleep(.8)
   if state()['view']!='main-menu':key('Escape')
   wait(lambda s:s['view']=='main-menu');key('Return')
   s=wait(lambda s:s.get('encounter_injected')and s.get('presence_prompt')and s['canvas_sha256']==s['presented_sha256']);frames=s['draws'];wait(lambda s:s['draws']>=frames+3);snap('confirmation',screens)
   key('Return');s=wait(lambda s:s.get('battle_opened')and s['world']['battle']is not None and s['canvas_sha256']==s['presented_sha256']);first=s;steps=s['battle_guest_steps'];cycles=s['battle_guest_cycles'];held=s['battle_held_updates'];wait(lambda s:s['battle_held_updates']>=held+3);s=state();paused=dict(steps_equal=s['battle_guest_steps']==steps,cycles_equal=s['battle_guest_cycles']==cycles,updates=s['battle_held_updates']-held);assert paused['steps_equal']and paused['cycles_equal'];snap('battle-start',screens)
   # All subsequent state transitions are real clicks through the Go UI.
   def click_wait(x,y,n):
    call('click',x,y);return wait(lambda s:len(s['battle_events'])>n or s.get('battle_finished'))
   if name=='win':
    key('F10');wait(lambda s:s['font_id']=='lishu'and s['presented_font']=='lishu'and s['canvas_sha256']==s['presented_sha256']);snap('battle-lishu',screens)
    for _ in range(100):
     s=state();b=s['world']['battle']['state'];n=len(s['battle_events'])
     if b['result']=='win':break
     if not b['acted'][1][0]:click_wait(530,900,n)
     elif not b['acted'][0][0]:click_wait(200,900,n)
     else:click_wait(1200,900,n)
    assert state()['world']['battle']['state']['result']=='win';snap('victory',screens);n=len(state()['battle_events']);click_wait(1600,900,n)
   else:
    n=len(state()['battle_events']);click_wait(530,900,n);snap('before-retreat',screens);n=len(state()['battle_events']);click_wait(280,225,n)
   final=wait(lambda s:s.get('battle_finished')and not s['presence_active']and s['world']['battle']is None and s['view']=='map'and s['presented_view']=='map');frames=final['draws'];wait(lambda s:s['draws']>=frames+3);snap('returned-map',screens)
   key('F2');wait(lambda s:s['view']=='army'and s['presented_view']=='army');snap('army-after',screens);key('Escape');wait(lambda s:s['view']=='map')
   call('key','Control_L','down');call('key','q','down')
   try:assert process.wait(timeout=20)==0
   finally:call('key','q','up');call('key','Control_L','up')
   cold=folder/'cold.json';subprocess.run([str(q/'paired-reader'),'-input',str(q/'inputs'),'-dir',str(q/('session-'+name)),'-world','world-'+name+'.json','-mode','read','-out',str(cold)],check=True,env=env,timeout=20)
   cases.append(dict(case=name,paused=paused,final=read(folder/'ui-final.json'),cold=read(cold),screens=screens))
  write(out/'receipt.json',dict(status='passed-controlled-confirmation-go-ui',cases=cases,controlled_memory=True,normal_player_path=False))
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
