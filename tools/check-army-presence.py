#!/usr/bin/env python3
"""Actual XTEST: empty owned army overrides native shadow, debit and cold read."""
import argparse,contextlib,hashlib,json,os,signal,subprocess,time
from pathlib import Path
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);a=p.parse_args();q=a.work;assert Path('/.dockerenv').exists()and os.getuid()==1000
 out=q/'gui-r1';out.mkdir();env=dict(os.environ,DISPLAY=':98',LIBGL_ALWAYS_SOFTWARE='1',GALLIUM_DRIVER='llvmpipe',LP_NUM_THREADS='1',GOMAXPROCS='2');children=[];streams=[];screens=[];phase=None;process=None
 initial=read(q/'session-empty/gamedata.ay.army.json')['world'];present_before={n:sha(q/'session-present'/n)for n in ['gamedata.ay','gamedata.ay.army.json']}
 signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(SystemExit(143)));signal.signal(signal.SIGINT,lambda *_:(_ for _ in ()).throw(SystemExit(130)))
 def call(*args):
  v=subprocess.run([str(q/'xcheck'),*map(str,args)],env=env,capture_output=True,text=True,timeout=10);assert v.returncode==0,(args,v.stdout,v.stderr);return v.stdout
 def state():
  try:return read(out/phase/'ui-state.json')
  except(OSError,ValueError):return None
 def wait(test,seconds=120):
  end=time.monotonic()+seconds
  while time.monotonic()<end:
   if process.poll()is not None:raise AssertionError(('UI exited',process.returncode,(out/phase/'player.log').read_text()[-1500:]))
   s=state()
   if s and test(s):return s
   time.sleep(.05)
  raise AssertionError(('UI timeout',state()))
 def key(k):call('key',k)
 def snap(name):
  old=state()['last_capture'];key('F12');s=wait(lambda s:s['last_capture']!=old and s['canvas_sha256']==s['presented_sha256']);call('screenshot',out/phase/(name+'.ppm'));write(out/phase/(name+'.json'),s);screens.append(dict(phase=phase,canvas=s['last_capture'],screen=name+'.ppm',metadata=name+'.json'));return s
 def start(name,session):
  nonlocal phase,process
  phase=name;folder=out/name;folder.mkdir();log=(folder/'player.log').open('w');streams.append(log)
  process=subprocess.Popen([str(q/'army-presence'),'-root','/game','-assets','/assets','-input',str(q/'inputs'),'-session',str(q/session),'-scratch',str(folder/'scratch'),'-ui-assets',str(q/'ui-assets'),'-capture-dir',str(folder),'-scale','1','-mute'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(process)
  wait(lambda s:s['draws']>0);time.sleep(.4);key('1');time.sleep(.4);key('1');time.sleep(.8)
  if state()['view']!='main-menu':key('Escape')
  wait(lambda s:s['view']=='main-menu');key('Return');return wait(lambda s:s['bound']and s['view']=='map'and s['presented_view']=='map')
 def stop():
  call('key','Control_L','down');call('key','q','down')
  try:assert process.wait(timeout=20)==0
  finally:call('key','q','up');call('key','Control_L','up')
 def encounter(test):
  for n in range(128):
   if test(state()):return state()
   key('Right'if n%2==0 else'Left')
  return wait(test,25)
 try:
  log=(out/'xvfb.log').open('w');streams.append(log);xvfb=subprocess.Popen(['Xvfb',':98','-screen','0','2560x1440x24','-nolisten','tcp'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(xvfb)
  for _ in range(100):
   if Path('/tmp/.X11-unix/X98').exists():break
   assert xvfb.poll()is None;time.sleep(.05)
  first=start('empty','session-empty');rows=first['native_rows_hex'];assert not any(x['count']for x in first['world']['army']['slots'])and rows.startswith('01001e00')
  s=encounter(lambda s:s['presence_debits']==1);assert not s['presence_has_army']and s['presence_native_reads']==0;snap('no-army-loss')
  key('Return');done=wait(lambda s:s['presence_completed']==1 and not s['presence_active']);assert done['native_rows_hex']==rows
  key('F2');wait(lambda s:s['view']=='army'and s['presented_view']=='army');snap('empty-after');key('Escape');wait(lambda s:s['view']=='map');stop()
  saved=read(q/'session-empty/gamedata.ay.army.json')['world'];assert saved['army']['gold']<initial['army']['gold']
  cold=start('cold','session-empty');assert cold['world']==saved and cold['native_rows_hex']==rows;key('F2');wait(lambda s:s['view']=='army'and s['presented_view']=='army');snap('empty-cold');key('Escape');wait(lambda s:s['view']=='map');stop()
  first=start('present','session-present');s=encounter(lambda s:s['presence_prompt']and s['view']=='encounter-confirm');frames=s['draws'];wait(lambda s:s['draws']>=frames+3);snap('owned-army-confirm');assert state()['presence_has_army']and state()['presence_native_reads']==0 and state()['presence_debits']==0;stop()
  assert present_before=={n:sha(q/'session-present'/n)for n in present_before}
  write(out/'receipt.json',dict(status='passed-actual-army-presence',initial=initial,after=saved,events=done['presence_events'],native_rows_hex=rows,screens=screens,cold_equal=True,present_pair_unchanged=True,limits=['Controlled saved Go army and native shadow, then normal Continue and natural movement.','Only no-army return completes; present army is sampled to the original confirmation, not battle.','Natural RNG not reseeded or replayed for parity.']))
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
