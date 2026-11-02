#!/usr/bin/env python3
"""Bounded XTEST check of original F2 layout backed by the Go army fixture."""
import argparse,contextlib,hashlib,json,os,signal,subprocess,time
from pathlib import Path
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);a=p.parse_args();q=a.work;out=q/'gui-r1';out.mkdir();assert Path('/.dockerenv').exists()and os.getuid()==1000
 env=dict(os.environ,DISPLAY=':98',LIBGL_ALWAYS_SOFTWARE='1',GALLIUM_DRIVER='llvmpipe',LP_NUM_THREADS='1',GOMAXPROCS='2');children=[];streams=[];process=None;screens=[]
 pair=['gamedata.ay','gamedata.ay.army.json'];before={n:sha(q/'gui-session'/n)for n in pair}
 signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(SystemExit(143)))
 def call(*args):
  r=subprocess.run([str(q/'xcheck'),*map(str,args)],env=env,capture_output=True,text=True,timeout=10);assert r.returncode==0,(args,r.stdout,r.stderr)
 def state():
  try:return read(out/'ui-state.json')
  except(OSError,ValueError):return None
 def wait(test,seconds=90):
  end=time.monotonic()+seconds
  while time.monotonic()<end:
   if process.poll()is not None:raise AssertionError(('UI exit',process.returncode,(out/'player.log').read_text()[-3000:]))
   s=state()
   if s and test(s):return s
   time.sleep(.05)
  write(out/'timeout.json',state());raise AssertionError(('timeout',state()))
 def frames(n=6):
  u=state()['updates'];return wait(lambda s:s['updates']>=u+n,20)
 def key(k):
  u=state()['updates'];call('key',k,'down')
  try:wait(lambda s:s['updates']>=u+2,20)
  finally:call('key',k,'up')
  frames(2)
 def snap(name):
  old=state()['last_capture'];key('F12');s=wait(lambda s:s['last_capture']!=old and s['canvas_sha256']==s['presented_sha256']);call('screenshot',out/(name+'.ppm'));write(out/(name+'.json'),s);screens.append(dict(name=name,canvas=s['last_capture'],screen=name+'.ppm',metadata=name+'.json'));return s
 try:
  log=(out/'xvfb.log').open('w');streams.append(log);x=subprocess.Popen(['Xvfb',':98','-screen','0','2560x1440x24','-nolisten','tcp'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(x)
  for _ in range(100):
   if Path('/tmp/.X11-unix/X98').exists():break
   assert x.poll()is None;time.sleep(.05)
  log=(out/'player.log').open('w');streams.append(log)
  cmd=[str(q/'8sword-review-gui'),'-root','/game','-assets','/assets','-input',str(q/'inputs'),'-session',str(q/'gui-session'),'-scratch',str(out/'scratch'),'-ui-assets',str(q/'ui-assets'),'-capture-dir',str(out),'-scale','1','-mute']
  process=subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(process)
  wait(lambda s:s['draws']>0);time.sleep(.4);key('1');key('1');time.sleep(.8)
  if state()['view']!='main-menu':key('Escape')
  wait(lambda s:s['view']=='main-menu');key('Return');wait(lambda s:s['bound']and s['view']=='map')
  for _ in range(3):
   if state()['font_id']=='noto':break
   old=state()['font_id'];key('F10');wait(lambda s:s['font_id']!=old and s['presented_font']==s['font_id'])
  assert state()['font_id']=='noto'
  key('F2');wait(lambda s:s.get('original_review_ready')and s['presented_view']=='army')
  first=snap('original-f2-go-noto');assert first['world']['army']['slots'][:2]==[dict(unit='native:01',count=31),dict(unit='native:21',count=1)]
  assert first['native_rows_hex']=='01001e000000000000000000000000000000000000000000'
  key('F10');wait(lambda s:s['font_id']=='lishu'and s['presented_font']=='lishu');snap('original-f2-go-lishu')
  key('Escape');wait(lambda s:not s['original_review_active']and s['view']=='map');snap('returned-map')
  key('F2');wait(lambda s:s['original_review_opens']==2 and s.get('original_review_ready')and s['presented_view']=='army');key('Escape');wait(lambda s:s['original_review_closes']==2 and s['view']=='map')
  call('key','Control_L','down');call('key','q','down')
  try:assert process.wait(timeout=20)==0
  finally:call('key','q','up');call('key','Control_L','up')
  assert before=={n:sha(q/'gui-session'/n)for n in pair}
  write(out/'receipt.json',dict(status='passed-original-F2-Go-data-GUI',waits_for_original_panel_commit=True,research_startup_overlay=True,controlled_army=True,normal_keyboard_path=True,source_rendering=True,save_pair_unchanged=before,screenshots=screens,program_sha256=sha(q/'8sword-review-gui')))
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
