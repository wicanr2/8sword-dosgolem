#!/usr/bin/env python3
"""030 DRAFT: real XTEST F3 dismissal, paired saves and cold reopen."""
import argparse,contextlib,hashlib,json,os,signal,subprocess,time
from pathlib import Path
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);a=p.parse_args();q=a.work;assert Path('/.dockerenv').exists()and os.getuid()==1000
 out=q/'gui-r1';out.mkdir();env=dict(os.environ,DISPLAY=':98',LIBGL_ALWAYS_SOFTWARE='1',GALLIUM_DRIVER='llvmpipe',LP_NUM_THREADS='1',GOMAXPROCS='2');children=[];streams=[];screens=[];phase=None;process=None
 pair_before={n:sha(q/'session-r1'/n)for n in ['gamedata.ay','gamedata.ay.army.json']}
 signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(SystemExit(143)));signal.signal(signal.SIGINT,lambda *_:(_ for _ in ()).throw(SystemExit(130)))
 def call(*args):
  v=subprocess.run([str(q/'xcheck'),*map(str,args)],env=env,capture_output=True,text=True,timeout=10);assert v.returncode==0,(args,v.stdout,v.stderr);return v.stdout
 def state():
  try:return read(out/phase/'ui-state.json')
  except(OSError,ValueError):return None
 def wait(test,seconds=120):
  end=time.monotonic()+seconds
  while time.monotonic()<end:
   if process.poll()is not None:raise AssertionError(('UI exited',process.returncode,(out/phase/'player.log').read_text()[-2000:]))
   s=state()
   if s and test(s):return s
   time.sleep(.05)
  raise AssertionError(('UI timeout',state()))
 def key(k):call('key',k)
 def snap(name):
  old=state()['last_capture'];key('F12');s=wait(lambda s:s['last_capture']!=old and s['canvas_sha256']==s['presented_sha256']and s['view']==s['presented_view']and s['font_id']==s['presented_font']);call('screenshot',out/phase/(name+'.ppm'));write(out/phase/(name+'.json'),s);screens.append(dict(phase=phase,font=s['font_id'],view=s['view'],canvas=s['last_capture'],screen=name+'.ppm',metadata=name+'.json'));return s
 def start(name,owned):
  nonlocal phase,process
  phase=name;folder=out/name;folder.mkdir();log=(folder/'player.log').open('w');streams.append(log)
  process=subprocess.Popen([str(q/'army-dismiss'),'-root','/game','-assets','/assets','-input',str(q/'inputs'),'-session',str(q/'session-r1'),'-scratch',str(folder/'scratch'),'-ui-assets',str(q/'ui-assets'),'-capture-dir',str(folder),'-scale','1','-mute','-owned='+str(owned).lower()],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(process)
  wait(lambda s:s['draws']>0);time.sleep(.4);key('1');time.sleep(.4);key('1');time.sleep(.8)
  if state()['view']!='main-menu':key('Escape')
  wait(lambda s:s['view']=='main-menu');key('Return');return wait(lambda s:s['bound']and s['view']=='map'and s['presented_view']=='map')
 def stop():
  call('key','Control_L','down');call('key','q','down')
  try:assert process.wait(timeout=20)==0
  finally:
   call('key','q','up');call('key','Control_L','up')
 def open_review():
  key('F2');return wait(lambda s:s['view']=='army'and s['presented_view']=='army'and s['canvas_sha256']==s['presented_sha256'])
 try:
  log=(out/'xvfb.log').open('w');streams.append(log);xvfb=subprocess.Popen(['Xvfb',':98','-screen','0','2560x1440x24','-nolisten','tcp'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(xvfb)
  for _ in range(100):
   if Path('/tmp/.X11-unix/X98').exists():break
   assert xvfb.poll()is None;time.sleep(.05)
  initial=start('owned',True);native_rows=initial['native_rows_hex'];world=initial['world']
  key('F3');opened=wait(lambda s:s['view']=='dismiss'and s['presented_view']=='dismiss');assert opened['dismiss_data']['metrics']==dict(used=46,total=36,occupied=2);snap('initial-noto')
  key('Down');wait(lambda s:s['dismiss_selected']==1);key('Escape');wait(lambda s:s['view']=='map');assert pair_before=={n:sha(q/'session-r1'/n)for n in pair_before}
  key('F3');wait(lambda s:s['view']=='dismiss');call('key','Return','down');time.sleep(.6);call('key','Return','up');s=wait(lambda s:s['dismiss_transactions']==1);time.sleep(.4);assert state()['dismiss_transactions']==1
  assert s['world']['army']['slots'][0]==dict(unit='openkb:wolf',count=5)and s['world']['army']['slots'][1]==dict(unit='',count=0)
  assert s['world']['army']['gold']==world['army']['gold']and s['world']['army']['offers']==world['army']['offers'];assert sha(q/'session-r1/gamedata.ay')==pair_before['gamedata.ay']
  key('F10');wait(lambda s:s['font_id']=='lishu');snap('wolf-lishu');call('click',1750,75);wait(lambda s:s['font_id']=='caoshu');snap('wolf-caoshu');call('click',1500,75);wait(lambda s:s['font_id']=='lishu')
  key('Escape');wait(lambda s:s['view']=='map');s=open_review();assert s['review_data']['metrics']==dict(used=15,total=5,occupied=1);snap('review-after');key('Escape');wait(lambda s:s['view']=='map');stop()
  cold=start('cold',True);assert cold['world']['army']['slots'][0]==dict(unit='openkb:wolf',count=5)and cold['font_id']=='lishu'
  key('F3');wait(lambda s:s['view']=='dismiss');snap('cold-wolf');call('click',1280,1110);empty=wait(lambda s:s['dismiss_transactions']==1 and s['dismiss_data']['metrics']['total']==0);assert empty['dismiss_selected']==-1;snap('empty-lishu')
  key('Return');time.sleep(.3);assert state()['dismiss_transactions']==1;key('Escape');wait(lambda s:s['view']=='map');s=open_review();assert s['review_data']['metrics']==dict(used=0,total=0,occupied=0);assert s['native_rows_hex']==native_rows and s['native_row_draw_calls']==0;snap('empty-review');key('Escape');wait(lambda s:s['view']=='map');stop()
  last=start('empty-cold',True);assert all(x['count']==0 for x in last['world']['army']['slots']);key('F3');wait(lambda s:s['view']=='dismiss');key('Return');time.sleep(.3);assert state()['dismiss_transactions']==0;key('Escape');wait(lambda s:s['view']=='map');stop()
  pair_after={n:sha(q/'session-r1'/n)for n in pair_before};assert pair_after['gamedata.ay']==pair_before['gamedata.ay']and pair_after['gamedata.ay.army.json']!=pair_before['gamedata.ay.army.json']
  write(out/'receipt.json',dict(status='passed-actual-f3-dismiss',cancel_unchanged=True,hold_commits_once=True,cold_equal=True,empty_cold_equal=True,pair_before=pair_before,pair_after=pair_after,native_rows_hex=native_rows,screens=screens,normal_expanded_army_path=False,limits=['Controlled paired Go save and separate native shadow.','Original F3 semantics statically grounded; instruction timing and full world handoff not claimed.']))
  print('Actual F3: cancel, single held Enter, stable army, fonts, F2 refresh and two cold reopens passed')
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
