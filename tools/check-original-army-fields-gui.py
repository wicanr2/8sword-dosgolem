#!/usr/bin/env python3
"""Bounded XTEST of original F2/F3 layout with Go-owned extended units."""
import argparse,contextlib,hashlib,json,os,signal,subprocess,time
from pathlib import Path
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--resume-cold',action='store_true');a=p.parse_args();q=a.work;out=q/'gui-r1';out.mkdir(exist_ok=a.resume_cold);assert Path('/.dockerenv').exists()and os.getuid()==1000
 env=dict(os.environ,DISPLAY=':98',LIBGL_ALWAYS_SOFTWARE='1',GALLIUM_DRIVER='llvmpipe',LP_NUM_THREADS='1',GOMAXPROCS='2');children=[];streams=[];process=None;folder=None;screens=[]
 pair=['gamedata.ay','gamedata.ay.army.json'];initial=q/'runtime-r1/initial-session'if a.resume_cold else q/'gui-session';before={n:sha(initial/n)for n in pair}
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
  write(folder/'timeout.json',state());raise AssertionError(('timeout',state()))
 def key(k):
  u=state()['updates'];call('key',k,'down')
  try:wait(lambda s:s['updates']>=u+2,20)
  finally:call('key',k,'up')
  u=state()['updates'];wait(lambda s:s['updates']>=u+2,20)
 def ready(view):return wait(lambda s:s.get('original_review_ready')and s['presented_view']==view)
 def map_ready():return wait(lambda s:not s['original_review_active']and s['original_review_map_ready']and s['presented_view']=='map')
 def snap(name):
  old=state()['last_capture'];key('F12');s=wait(lambda s:s['last_capture']!=old and s['canvas_sha256']==s['presented_sha256']);call('screenshot',folder/(name+'.ppm'));write(folder/(name+'.json'),s);screens.append(dict(phase=folder.name,name=name,canvas=s['last_capture'],screen=name+'.ppm',metadata=name+'.json'));return s
 def start(name):
  nonlocal process,folder
  folder=out/name;folder.mkdir();log=(folder/'player.log').open('w');streams.append(log)
  cmd=[str(q/'8sword-fields-gui'),'-root','/game','-assets','/assets','-input',str(q/'inputs'),'-session',str(q/'gui-session'),'-scratch',str(folder/'scratch'),'-ui-assets',str(q/'ui-assets'),'-capture-dir',str(folder),'-scale','1','-mute']
  process=subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(process);wait(lambda s:s['draws']>0);time.sleep(.4);key('1');key('1');time.sleep(.8)
  if state()['view']!='main-menu':key('Escape')
  wait(lambda s:s['view']=='main-menu');key('Return');return wait(lambda s:s['bound']and s['view']=='map')
 def stop():
  call('key','Control_L','down');call('key','q','down')
  try:assert process.wait(timeout=20)==0
  finally:call('key','q','up');call('key','Control_L','up')
 try:
  log=(out/('xvfb-r2.log'if a.resume_cold else'xvfb.log')).open('w');streams.append(log);x=subprocess.Popen(['Xvfb',':98','-screen','0','2560x1440x24','-nolisten','tcp'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(x)
  for _ in range(100):
   if Path('/tmp/.X11-unix/X98').exists():break
   assert x.poll()is None;time.sleep(.05)
  if a.resume_cold:
   for name in ['f2-noto','f3-wolf-noto','f3-wolf-lishu','f3-after-wolf-lishu']:
    meta=read(out/'warm'/(name+'.json'));assert meta['canvas_sha256']==meta['presented_sha256'];screens.append(dict(phase='warm',name=name,canvas=meta['last_capture'],screen=name+'.ppm',metadata=name+'.json'))
   warm_world=read(out/'warm/ui-state.json')['world'];assert read(q/'gui-session/gamedata.ay.army.json')['world']==warm_world and warm_world['army']['slots'][1]==dict(unit='openkb:drag',count=1)
  else:
   start('warm')
   for _ in range(3):
    if state()['font_id']=='noto':break
    old=state()['font_id'];key('F10');wait(lambda s:s['font_id']!=old and s['presented_font']==s['font_id'])
   key('F2');ready('army');first=snap('f2-noto');assert len(first['text_fields'])>=30;key('Escape');map_ready()
   key('F3');ready('dismiss');key('Down');wait(lambda s:s['original_dismiss_selected']==1 and s['original_review_ready']);snap('f3-wolf-noto');key('F10');wait(lambda s:s['font_id']=='lishu'and s['presented_font']=='lishu');snap('f3-wolf-lishu');key('Escape');map_ready();assert before=={n:sha(q/'gui-session'/n)for n in pair}
   key('F3');ready('dismiss');key('Down');wait(lambda s:s['original_dismiss_selected']==1 and s['original_review_ready']);key('Return');wait(lambda s:s['original_dismiss_transactions']==1 and s['original_review_ready']);after=snap('f3-after-wolf-lishu');assert after['world']['army']['slots'][1]==dict(unit='openkb:drag',count=1);key('Escape');map_ready();warm_world=state()['world'];stop()
  warm_pair={n:sha(q/'gui-session'/n)for n in pair};assert warm_pair['gamedata.ay']==before['gamedata.ay']and warm_pair['gamedata.ay.army.json']!=before['gamedata.ay.army.json']
  cold=start('cold-r2'if a.resume_cold else'cold');assert cold['world']==warm_world and cold['font_id']=='lishu';key('F2');ready('army');snap('cold-f2-lishu');key('Escape');map_ready();key('F10');wait(lambda s:s['font_id']=='caoshu'and s['presented_font']=='caoshu');key('F2');ready('army');snap('cold-f2-caoshu');key('Escape');map_ready();stop()
  write(out/'receipt.json',dict(status='passed-original-army-fields-GUI',waits_for_original_panel_commit=True,research_startup_overlay=True,controlled_army=True,normal_keyboard_path=True,cancel_pair_unchanged=True,warm_pair=warm_pair,cold_world_equal=True,resumed_cold_after_outer_time_limit=a.resume_cold,screenshots=screens,program_sha256=sha(q/'8sword-fields-gui')))
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
