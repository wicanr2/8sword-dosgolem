#!/usr/bin/env python3
"""030 DRAFT: real XTEST F2, fonts, close/reopen and native-control captures."""
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
  process=subprocess.Popen([str(q/'army-review'),'-root','/game','-assets','/assets','-input',str(q/'inputs'),'-session',str(q/'session-r1'),'-scratch',str(folder/'scratch'),'-ui-assets',str(q/'ui-assets'),'-capture-dir',str(folder),'-scale','1','-mute','-owned='+str(owned).lower()],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(process)
  wait(lambda s:s['draws']>0);time.sleep(.4);key('1');time.sleep(.4);key('1');time.sleep(.8)
  if state()['view']!='main-menu':key('Escape')
  wait(lambda s:s['view']=='main-menu');key('Return');return wait(lambda s:s['bound']and s['view']=='map'and s['presented_view']=='map')
 def stop():
  call('key','Control_L','down');key('q');call('key','Control_L','up');assert process.wait(timeout=20)==0
 def open_review():
  key('F2');return wait(lambda s:s['view']=='army'and s['presented_view']=='army'and s['canvas_sha256']==s['presented_sha256'])
 try:
  log=(out/'xvfb.log').open('w');streams.append(log);xvfb=subprocess.Popen(['Xvfb',':98','-screen','0','2560x1440x24','-nolisten','tcp'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(xvfb)
  for _ in range(100):
   if Path('/tmp/.X11-unix/X98').exists():break
   assert xvfb.poll()is None;time.sleep(.05)
  initial=start('native',False);native_rows=initial['native_rows_hex'];s=open_review();assert s['native_row_draw_calls']>0;snap('native-f2');key('Escape');wait(lambda s:s['view']=='map');stop()
  initial=start('owned',True);assert initial['native_rows_hex']==native_rows;world=initial['world'];opened=open_review();data=opened['review_data'];assert data['metrics']==dict(used=46,total=36,occupied=2)
  assert data['rows'][0]['id']=='native:01'and data['rows'][0]['count']==31 and data['rows'][1]['id']=='openkb:wolf'and data['rows'][1]['count']==5
  assert opened['native_row_draw_calls']==0 and opened['review_skipped']==1;snap('go-noto')
  before_steps=state()['guest_steps'];before_audio=state()['audio_frames'];call('key','F10','down');time.sleep(.45);call('key','F10','up');wait(lambda s:s['font_id']=='lishu');time.sleep(.3);assert state()['font_id']=='lishu'and state()['view']=='army';snap('go-lishu')
  call('click',1750,75);wait(lambda s:s['font_id']=='caoshu');snap('go-caoshu');assert state()['guest_steps']>before_steps and state()['audio_frames']>before_audio
  call('click',1500,75);wait(lambda s:s['font_id']=='lishu');key('Escape');closed=wait(lambda s:s['view']=='map'and s['presented_view']=='map');assert closed['review_closes']==1 and closed['native_rows_hex']==native_rows;snap('map-return')
  again=open_review();assert again['review_data']==data and again['review_opens']==2 and again['review_skipped']==2;call('click',1680,1110);wait(lambda s:s['view']=='map'and s['review_closes']==2);stop()
  cold=start('cold',True);assert cold['world']==world and cold['font_id']=='lishu';last=open_review();assert last['review_data']==data and last['native_row_draw_calls']==0 and last['review_native_entries']==0;snap('cold-lishu');key('Return');wait(lambda s:s['view']=='map');stop()
  pair_after={n:sha(q/'session-r1'/n)for n in pair_before};assert pair_before==pair_after
  write(out/'receipt.json',dict(status='passed-actual-f2-review',cold_equal=True,font_hold_once=True,go_native_draw_calls=0,review_data=data,pair_before=pair_before,pair_after=pair_after,native_rows_hex=native_rows,screens=screens,normal_expanded_army_path=False,limits=['Controlled existing Go save; native executor uses an explicitly separate native shadow.','Read-only army review; original CPU clock parity and full world handoff not claimed.']))
  print('Actual F2 review: original dispatcher -> Go 31 militia + 5 wolves -> map, fonts and cold reopen passed')
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
