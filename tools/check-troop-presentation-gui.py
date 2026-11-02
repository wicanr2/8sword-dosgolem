#!/usr/bin/env python3
"""Bounded transparency and corrected unit-art GUI sample; original controls retained."""
import argparse,contextlib,hashlib,json,os,signal,struct,subprocess,time,zlib
from pathlib import Path
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def png_rgb(p):
 # The player writes non-interlaced 8-bit RGB/RGBA PNGs. Decode only that
 # explicit capture contract, without adding libraries to the fixed Go image.
 raw=p.read_bytes();assert raw[:8]==b'\x89PNG\r\n\x1a\n';at=8;packed=b''
 while at<len(raw):
  n=struct.unpack('>I',raw[at:at+4])[0];kind=raw[at+4:at+8];data=raw[at+8:at+8+n];at+=n+12
  if kind==b'IHDR':w,h,depth,color,comp,filt,interlace=struct.unpack('>IIBBBBB',data);assert(depth,comp,filt,interlace)==(8,0,0,0)and color in(2,6)
  if kind==b'IDAT':packed+=data
 bpp=3 if color==2 else 4;stride=w*bpp;data=zlib.decompress(packed);assert len(data)==h*(stride+1);prior=bytearray(stride);rgb=bytearray()
 for y in range(h):
  start=y*(stride+1);f=data[start];row=bytearray(data[start+1:start+1+stride]);assert f<=4
  for i in range(stride):
   a=row[i-bpp]if i>=bpp else 0;b=prior[i];c=prior[i-bpp]if i>=bpp else 0
   if f==1:predict=a
   elif f==2:predict=b
   elif f==3:predict=(a+b)//2
   elif f==4:
    v=a+b-c;dist=[abs(v-a),abs(v-b),abs(v-c)];predict=[a,b,c][dist.index(min(dist))]
   else:predict=0
   row[i]=(row[i]+predict)&255
  if bpp==3:rgb.extend(row)
  else:
   assert all(v==255 for v in row[3::4]);rgb.extend(bytearray(v for i,v in enumerate(row)if i%4!=3))
  prior=row
 return bytes(rgb)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--native-only',action='store_true');a=p.parse_args();q=a.work;out=q/'gui-r1';out.mkdir(exist_ok=a.native_only);assert Path('/.dockerenv').exists()and os.getuid()==1000
 env=dict(os.environ,DISPLAY=':98',LIBGL_ALWAYS_SOFTWARE='1',GALLIUM_DRIVER='llvmpipe',LP_NUM_THREADS='1',GOMAXPROCS='2');children=[];streams=[];process=None;folder=None;screens=[]
 signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(SystemExit(143)))
 def call(*args):
  r=subprocess.run([str(q/'xcheck'),*map(str,args)],env=env,capture_output=True,text=True,timeout=10);assert r.returncode==0,(args,r.stdout,r.stderr)
 def state():
  try:return read(folder/'ui-state.json')
  except(OSError,ValueError):return None
 def wait(test,seconds=100):
  end=time.monotonic()+seconds
  while time.monotonic()<end:
   if process.poll()is not None:raise AssertionError(('UI exit',process.returncode,(folder/'player.log').read_text()[-3000:]))
   s=state()
   if s and test(s):return s
   time.sleep(.05)
  write(folder/'timeout.json',state());raise AssertionError(('timeout',state()))
 def frames(n=6):
  u=state()['updates'];return wait(lambda s:s['updates']>=u+n,25)
 def key(k):
  u=state()['updates'];call('key',k,'down')
  try:wait(lambda s:s['updates']>=u+2,25)
  finally:call('key',k,'up')
  frames(2)
 def snap(name):
  old=state()['last_capture'];key('F12');s=wait(lambda s:s['last_capture']!=old and s['canvas_sha256']==s['presented_sha256']);expected=png_rgb(folder/s['last_capture']);rgba=bytearray(len(expected)//3*4);rgba[0::4]=expected[0::3];rgba[1::4]=expected[1::3];rgba[2::4]=expected[2::3];rgba[3::4]=b'\xff'*(len(expected)//3);captured_sha=hashlib.sha256(rgba).hexdigest();end=time.monotonic()+8;attempts=0
  # The original numeric editor blinks its cursor while X11 is captured.
  # Wait for the captured cursor phase, requiring every RGB byte to match.
  while True:
   s=state()
   if s['canvas_sha256']!=captured_sha or s['presented_sha256']!=captured_sha:
    assert time.monotonic()<end,('capture metadata phase',name);time.sleep(.05);continue
   attempts+=1;attempt=folder/(name+'-attempt-'+str(attempts)+'.ppm');call('screenshot',attempt);raw=attempt.read_bytes();header=raw.split(b'\n',3);assert header[:3]==[b'P6',b'1920 1200',b'255']
   if header[3]==expected:attempt.rename(folder/(name+'.ppm'));break
   assert time.monotonic()<end,('X11 frame did not synchronize',name)
   time.sleep(.05)
  s['x11_capture_attempts']=attempts;write(folder/(name+'.json'),s);screens.append(dict(phase=folder.name,name=name,canvas=s['last_capture'],screen=name+'.ppm',metadata=name+'.json'));return s
 def shop(first):
  if first:
   for k in ['Left','Up']:
    key(k);frames(8)
    if state()['recruit_icons']['active']:break
    key('F1');frames(8)
    if state()['recruit_icons']['active']:break
    key('Escape');frames(8)
   if not state()['recruit_icons']['active']:key('Up')
  else:key('Down');frames(8);key('Up')
  return wait(lambda s:s['recruit_icons']['active']and s['recruit_icons']['ready']and s['recruit_icons']['frames']>0)
 def click(x,y):call('click',x,y);frames(4)
 def enter_quantity():
  click(600,65);wait(lambda s:s['reinforcements']['active']);key('Return');wait(lambda s:s['reinforcement_quantity']['phase']=='input'and s['reinforcement_quantity']['ready']and s['presented_view']=='recruit');frames(8)
 def map_ready():return wait(lambda s:s['view']=='map'and not s['recruit_icons']['active'])
 def start(name):
  nonlocal process,folder
  folder=out/name;folder.mkdir();log=(folder/'player.log').open('w');streams.append(log)
  args=[str(q/'8sword-presentation-gui'),'-root','/game','-assets','/assets','-input',str(q/'inputs'),'-session',str(q/'gui-session'),'-scratch',str(folder/'scratch'),'-ui-assets',str(q/'ui-assets'),'-capture-dir',str(folder),'-scale','1','-mute']
  process=subprocess.Popen(args,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(process);wait(lambda s:s['draws']>0);time.sleep(.4);key('1');key('1');time.sleep(.8)
  if state()['view']!='main-menu':key('Escape')
  wait(lambda s:s['view']=='main-menu');key('Return');return wait(lambda s:s['bound']and s['view']=='map')
 def stop():
  call('key','Control_L','down');call('key','q','down')
  try:assert process.wait(timeout=20)==0
  finally:call('key','q','up');call('key','Control_L','up')
 try:
  log=(out/('xvfb-native-redo.log'if a.native_only else'xvfb-warm.log')).open('w');streams.append(log);x=subprocess.Popen(['Xvfb',':98','-screen','0','2560x1440x24','-nolisten','tcp'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);children.append(x)
  for _ in range(100):
   if Path('/tmp/.X11-unix/X98').exists():break
   assert x.poll()is None;time.sleep(.05)
  if a.native_only:
   initial=start('native-redo')
   for _ in range(3):
    if state()['font_id']=='lishu':break
    key('F10');frames(4)
   shop(True);snap('native-transparent');stop();prior=read(out/'receipt.json');write(out/'receipt-before-native-sync.json',prior);prior['screenshots']=screens+[x for x in prior['screenshots']if x['name']!='native-transparent'];prior['native_metadata_resampled']=True;tmp=out/'receipt-resampled.json';write(tmp,prior);tmp.replace(out/'receipt.json');return
  initial=start('warm')
  for _ in range(3):
   if state()['font_id']=='lishu':break
   key('F10');frames(4)
  assert state()['font_id']=='lishu'
  shop(True);snap('native-transparent')
  click(600,65);wait(lambda s:s['reinforcements']['active']);click(200,350);wait(lambda s:s['reinforcements']['selected']==0);snap('new-eight')
  click(1100,350);wait(lambda s:s['reinforcements']['selected']==2);key('Return');wait(lambda s:s['reinforcement_quantity']['phase']=='input'and s['reinforcement_quantity']['ready']and s['presented_view']=='recruit');frames(8);snap('new-wolf-input')
  key('Escape');map_ready();key('F2');wait(lambda s:s.get('original_review_ready')and s['presented_view']=='army');last=snap('army-reviewed')
  assert last['world']['army']['slots']==initial['world']['army']['slots']and last['world']['army']['gold']==initial['world']['army']['gold']and last['native_rows_hex']==initial['native_rows_hex']
  stop();write(out/'receipt.json',dict(status='passed-troop-presentation-GUI',controlled_army=True,normal_keyboard_path=True,memory_injected=False,screenshots=screens,program_sha256=sha(q/'8sword-presentation-gui'),initial_world=initial['world'],final_world=last['world']))
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
