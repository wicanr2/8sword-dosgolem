#!/usr/bin/env python3
"""Buildable owned command: actual native import, recruitment and existing battle resume."""
import argparse,contextlib,json,os,signal,subprocess,time,shutil
from pathlib import Path
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--batch',default='gui-r1');a=p.parse_args();q=a.work;out=q/a.batch;out.mkdir();session=q/'session-native-r1';assert Path('/.dockerenv').exists()and os.getuid()==1000
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
  process=subprocess.Popen([str(q/'8sword-owned'),'-root','/game','-assets','/assets','-input',str(q/'inputs'),'-session',str(session),'-scratch',str(folder/'scratch'),'-ui-assets',str(q/'ui-assets'),'-capture-dir',str(folder),'-scale','1','-mute'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(process);wait(lambda s:s['draws']>0);time.sleep(.4);key('1');key('1');time.sleep(.8)
  if state()['view']!='main-menu':key('Escape')
  wait(lambda s:s['view']=='main-menu');key('Return');return wait(lambda s:s['bound'])
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
  imported=subprocess.run([str(q/'8sword-owned'),'-root','/game','-input',str(q/'inputs'),'-session',str(session),'-import-native','/game','-import-only'],env=env,capture_output=True,text=True,timeout=30);(out/'import-cli.log').write_text(imported.stdout+imported.stderr);assert imported.returncode==0
  shutil.copytree(session,q/'initial-import')
  initial=start('imported');wait(lambda s:s['view']=='map');assert initial['world']['army']['gold']==500 and initial['world']['army']['leadership']==100 and initial['world']['army']['rules']=='native'and initial['world']['progress']['merit']==0
  key('F2');wait(lambda s:s['view']=='army');army=snap('native-import-army');assert army['world']['army']['slots'][0]==dict(unit='native:01',count=30);key('Escape');wait(lambda s:s['view']=='map')
  shop();click(600,65);wait(lambda s:s['view']=='reinforcements');click(1700,180);wait(lambda s:s['world']['army']['rules']=='tactics');camp=snap('native-import-camp');click(1600,940);wait(lambda s:s['view']=='map'and s['reinforcements']['purchases']==1);purchased=snap('native-import-purchased');assert purchased['world']['army']['gold']==460 and purchased['world']['army']['slots'][1]==dict(unit='openkb:wolf',count=1)
  key('F7');wait(lambda s:s['view']=='system-menu');key('Return');key('Return');wait(lambda s:s.get('native_checkpoint_saves')==1 and not s.get('native_checkpoint_active')and s['view']=='map');checkpoint=snap('native-import-saved');stop()
  cold=start('cold-import');wait(lambda s:s['view']=='map');assert cold['world']==checkpoint['world'];key('F2');wait(lambda s:s['view']=='army');cold_army=snap('native-import-cold-army');stop()
  session=q/'session-battle-r1';before=read(session/'gamedata.ay.army.json');battle=start('cold-battle');wait(lambda s:s['view']=='battle');battle=snap('owned-command-cold-battle');assert battle['world']==before['world']and battle['world']['battle']['state']['acted'][0][1];assert battle['world']['army']['slots'][1]==dict(unit='openkb:wolf',count=1);stop()
  write(out/'receipt.json',dict(status='passed-owned-player-native-import-ui',initial=initial,army=army,camp=camp,purchased=purchased,checkpoint=checkpoint,cold=cold,cold_army=cold_army,battle=battle,screens=screens,native_import_fixture_army_used=False,legacy_battle_origin_controlled_initial_army=True,memory_injected=False,old_battle_from_actual_saved_pair=True,formal_default_changed=False))
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
