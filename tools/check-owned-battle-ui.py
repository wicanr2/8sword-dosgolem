#!/usr/bin/env python3
"""030 DRAFT: XTEST recruit, combat actions, in-flight cold resume and settlement."""
import argparse,contextlib,hashlib,json,os,signal,subprocess,time
from pathlib import Path
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);a=p.parse_args();q=a.work;assert Path('/.dockerenv').exists() and os.getuid()==1000
 out=q/'gui-r1';out.mkdir();env=dict(os.environ,DISPLAY=':98',LIBGL_ALWAYS_SOFTWARE='1',GALLIUM_DRIVER='llvmpipe',LP_NUM_THREADS='1',GOMAXPROCS='2');children=[];streams=[];screens=[];phase=None;process=None
 signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(SystemExit(143)));signal.signal(signal.SIGINT,lambda *_:(_ for _ in ()).throw(SystemExit(130)))
 def call(*args):
  s=subprocess.run([str(q/'xcheck'),*map(str,args)],env=env,capture_output=True,text=True,timeout=10);assert s.returncode==0,(args,s.stdout,s.stderr);return s.stdout
 def state():
  try:return read(out/phase/'ui-state.json')
  except (OSError,ValueError):return None
 def wait(test,seconds=20):
  end=time.monotonic()+seconds
  while time.monotonic()<end:
   if process.poll() is not None:raise AssertionError(('UI exited',process.returncode,(out/phase/'player.log').read_text()[-2000:]))
   s=state()
   if s and test(s):return s
   time.sleep(.05)
  raise AssertionError(('UI timeout',state()))
 def key(name):call('key',name)
 def click(x,y):call('click',x,y)
 def snap(label):
  old=state()['last_capture'];key('F12');s=wait(lambda s:s['last_capture']!=old and s['canvas_sha256']==s['presented_sha256'] and s['font_id']==s['presented_font']);ppm=label+'.ppm';call('screenshot',out/phase/ppm);meta=label+'.json';write(out/phase/meta,s);screens.append(dict(phase=phase,font=s['font_id'],canvas=s['last_capture'],screen=ppm,metadata=meta));return s
 def start(name):
  nonlocal phase,process
  phase=name;(out/name).mkdir();log=(out/name/'player.log').open('w');streams.append(log)
  process=subprocess.Popen([str(q/'battle-ui'),'-catalog',str(q/'inputs/army-catalog.json'),'-combat',str(q/'inputs/combat-catalog.json'),'-seed',str(q/'inputs/seed-world.json'),'-ui-assets',str(q/'ui-assets'),'-session',str(q/'session-r1'),'-capture-dir',str(out/name),'-scale','1'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(process)
  return wait(lambda s:s['draws']>0 and s['canvas_sha256']==s['presented_sha256'])
 def stop():
  call('key','Control_L','down');key('q');call('key','Control_L','up');assert process.wait(timeout=20)==0;assert not(q/'session-r1/.owned-battle-ui.lock').exists()
 def commit(x,y):
  old=state()['session_sha256'];click(x,y);return wait(lambda s:s['session_sha256']!=old and s['presented_sha256']==s['canvas_sha256'])
 try:
  log=(out/'xvfb.log').open('w');streams.append(log);xvfb=subprocess.Popen(['Xvfb',':98','-screen','0','2560x1440x24','-nolisten','tcp'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(xvfb)
  for _ in range(100):
   if Path('/tmp/.X11-unix/X98').exists():break
   assert xvfb.poll() is None;time.sleep(.05)
  initial=start('fresh');assert initial['world']['army']['gold']==5000;snap('initial-noto')
  recruited=commit(200,225);assert recruited['world']['army']['slots'][0]['count']==30 and recruited['world']['army']['gold']==3800
  commit(500,225);saved=state()['session_sha256'];click(1200,900);s=wait(lambda s:'尚有部隊未行動' in s['message']);assert s['session_sha256']==saved
  mid=commit(550,900);assert mid['world']['battle']['state']['acted'][1][0];key('F10');wait(lambda s:s['font_id']=='lishu');snap('mid-lishu');stop()
  cold=start('resumed');assert cold['world']==mid['world'] and cold['session_sha256']==mid['session_sha256'] and cold['font_id']=='lishu';snap('cold-mid-lishu')
  saved=cold['session_sha256'];click(550,900);s=wait(lambda s:'敵軍已出手' in s['message']);assert s['session_sha256']==saved
  # Real mouse selection of the empty sixth target must be rejected.
  click(1730,670);wait(lambda s:s['target']==5);click(200,900);s=wait(lambda s:'目標不合法' in s['message']);assert s['session_sha256']==saved
  click(1150,400);wait(lambda s:s['target']==0);s=commit(200,900)
  key('F10');wait(lambda s:s['font_id']=='caoshu');snap('action-caoshu');key('F10');wait(lambda s:s['font_id']=='noto');key('F10');wait(lambda s:s['font_id']=='lishu')
  while s['world']['battle']['state']['result']=='':
   assert s['world']['battle']['state']['round']<40
   commit(1200,900);s=commit(550,900)
   if s['world']['battle']['state']['result']=='':s=commit(200,900)
  assert s['world']['battle']['state']['result']=='win';snap('victory-lishu');settled=commit(1600,900);world=settled['world'];assert world['army']['gold']==4400 and world['army']['slots'][0]['count']==29 and world['progress']['rank']==2
  saved=settled['session_sha256'];click(1600,900);s=wait(lambda s:'only completed victory' in s['message']);assert s['session_sha256']==saved;snap('settled-lishu');stop()
  final=start('final');assert final['world']==world and final['session_sha256']==saved;snap('cold-final-lishu');stop()
  assert hashlib.sha256((q/'session-r1/gamedata.ay').read_bytes()).hexdigest()==hashlib.sha256((q/'inputs/original-save.ay').read_bytes()).hexdigest()
  actions=len(read(out/'fresh/ui-final.json')['events'])+len(read(out/'resumed/ui-final.json')['events']);assert actions==28
  write(out/'receipt.json',dict(status='passed-real-go-battle-ui',actions=actions,mid_cold_equal=True,final_cold_equal=True,duplicate_enemy_rejected=True,duplicate_reward_rejected=True,invalid_target_rejected=True,early_round_rejected=True,final_world=world,screens=screens,guest_instructions=0,normal_original_world=False))
  print('Actual battle UI: recruit -> 28 actions -> save/cold resume -> single reward passed')
 finally:
  for child in reversed(children):
   if child.poll() is None:
    with contextlib.suppress(ProcessLookupError):os.killpg(child.pid,signal.SIGTERM)
    try:child.wait(timeout=5)
    except subprocess.TimeoutExpired:
     with contextlib.suppress(ProcessLookupError):os.killpg(child.pid,signal.SIGKILL)
     child.wait()
  for stream in streams:stream.close()
if __name__=='__main__':main()
