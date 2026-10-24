#!/usr/bin/env python3
"""在 Docker 內獨立重建 CHOI 四個實際 Draw，核對正常來源與逐幀串流。"""
from pathlib import Path
import argparse,gzip,hashlib,json,runpy,struct
from PIL import Image
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('gui',type=Path)
parser.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[1])
parser.add_argument('--battle',type=Path)
args=parser.parse_args()
r=args.project; b=args.battle or r/'workplace/probe-20261023/graphics-first/battle-r1'; g=args.gui; s=g/'save' 
read=lambda p:json.loads(p.read_text())
sha=lambda data:hashlib.sha256(data).hexdigest()
original=r/'workplace/intake-20261023/sources/game/8sword'
source=read(s/'research-sources.json')
assert source['error']=='' and source['source']=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
raw=(original/'CHOI.EGG').read_bytes(); lookup={sha(raw[i*3304:(i+1)*3304]):i for i in range(4)}
calls=[c for c in source['calls'] if c['source_sha256'] in lookup]
returns={c['serial']:c for c in source['returns']}
assert calls and set(lookup[c['source_sha256']] for c in calls)==set(range(4))
for c in calls:
 assert c['serial'] in returns and returns[c['serial']]['source_sha256']==c['source_sha256']
 assert c['entry']==0x4f2 and c['marker_accepted'] and c['effect_source']==108+lookup[c['source_sha256']]
 assert (s/('battle-source-'+c['source_sha256']+'.bin')).read_bytes()==raw[lookup[c['source_sha256']]*3304:(lookup[c['source_sha256']]+1)*3304]
catalog=runpy.run_path(str(r/'tools/catalog-battle-actors.py'))
intro=runpy.run_path(str(r/'tools/prepare-hd-intro.py'))
bgnative=intro['decode']((original/'GRO02.EG').read_bytes())
palette=catalog['PALETTE']
bg=Image.open(b/'production-background-r9/sampled-background-cache.png').convert('RGBA').tobytes()
caches={87+group*4+i:(b/(unit+'-art-r1')/f'cache-frame-{i}.rgba').read_bytes() for group,unit in enumerate(['man16','man06','man11','man21']) for i in range(4)}
caches[107]=(r/'workplace/probe-20261023/graphics-first/army-r1/militia-independent-cache.rgba').read_bytes()
expected_draws={}; results=[]
for record in range(4):
 packet=s/'research-choi-draws'/f'record-{record}-first-draw'
 meta=read(Path(str(packet)+'.json'))
 assert meta['record']==record and meta['status']['visible_sources']==[]
 assert Path(str(packet)+'-before.state').read_bytes()==Path(str(packet)+'-after.state').read_bytes()
 cp=s/'research-choi-checkpoints'/meta['checkpoint']; frozen=read(Path(str(cp)+'.json'))
 assert frozen['Step']==meta['checkpoint_step']<=meta['step'] and frozen['Source']==108+record
 assert Path(str(cp)+'-before.state').read_bytes()==Path(str(cp)+'-after.state').read_bytes()
 selected=[c for c in calls if returns[c['serial']]['step']<=meta['checkpoint_step']][-1]
 assert lookup[selected['source_sha256']]==record
 x0,y0=selected['args'][2]*8,selected['args'][3]
 # Derive the pre-effect original rectangle from the latest original reset.
 reset=[c for c in source['calls'] if c['serial']<selected['serial'] and c['entry'] in (0x626,0x423) and c['args'][2:]==selected['args'][2:]][-1]
 assert reset['entry']==0x626 and reset['serial'] in returns
 resetraw=(s/('battle-source-'+reset['source_sha256']+'.bin')).read_bytes(); assert len(resetraw)==3304
 for c in source['calls'][reset['serial']+1:selected['serial']]:
  x,y=c['args'][2]*8,c['args'][3]
  assert x+88<=x0 or x>=x0+88 or y+50<=y0 or y>=y0+50,(record,c)
 base=bytearray(4400)
 for y in range(50):
  for x in range(88):
   at=y*11+x//8;bit=7-x%8
   if (resetraw[4+5*550+at]>>bit)&1:
    base[y*88+x]=sum(((resetraw[4+plane*550+at]>>bit)&1)<<plane for plane in range(4))
   else:
    at=(y0+y)*80+(x0+x)//8;bit=7-(x0+x)%8
    base[y*88+x]=sum(((bgnative[4+plane*16000+at]>>bit)&1)<<plane for plane in range(4))
 grid=list(struct.iter_unpack('<HI',Path(str(packet)+'-effects.bin').read_bytes()))
 owners=list(struct.iter_unpack('<HI',Path(str(packet)+'-background.bin').read_bytes()))
 actors=list(struct.iter_unpack('<HI',Path(str(packet)+'-actors.bin').read_bytes()))
 nativebase=Path(str(packet)+'-effect-base.idx').read_bytes()
 info=read(Path(str(packet)+'-layers.json')); assert len(info['effects'])==1
 effectid,sourceid=next(iter(info['effects'].items())); assert sourceid==108+record
 fx=(b/'choi-art-r1'/f'cache-frame-{record}.rgba').read_bytes()
 assert Path(str(packet)+f'-effect-cache-{effectid}.rgba').read_bytes()==fx
 occupied=0
 native=bytearray(Path(str(packet)+'-native.idx').read_bytes())
 for cell,(eid,local) in enumerate(grid):
  x,y=cell%640,cell//640
  if x0<=x<x0+88 and y0<=y<y0+50:
   assert eid==int(effectid) and local==(y-y0)*88+x-x0 and nativebase[cell]==base[local],(record,x,y)
   native[cell]=base[local]; occupied+=1
  else:assert eid==0
 assert occupied==4400
 im=Image.frombytes('P',(640,200),bytes(native)); im.putpalette([v for rgb in palette for v in rgb]+[0]*(768-48))
 expected=bytearray(im.convert('RGBA').resize((1920,1200),Image.Resampling.NEAREST).tobytes())
 for cell,(owner,local) in enumerate(owners):
  if not owner:continue
  assert owner==86
  x,y=cell%640,cell//640; bx,by=local%640,local//640
  for dy in range(6):
   dst=((y*6+dy)*1920+x*3)*4; src=((by*6+dy)*1920+bx*3)*4
   expected[dst:dst+12]=bg[src:src+12]
 for cell,(actor,local) in enumerate(actors):
  if not actor:continue
  assert actor in caches
  x,y=cell%640,cell//640; ax,ay=local%88,local//88; cache=caches[actor]
  for dy in range(6):
   for dx in range(3):
    dst=((y*6+dy)*1920+x*3+dx)*4; src=((ay*6+dy)*264+ax*3+dx)*4; alpha=cache[src+3]
    for channel in range(3):expected[dst+channel]=min(255,cache[src+channel]+(expected[dst+channel]*(255-alpha)+127)//255)
    expected[dst+3]=255
 for sy in range(300):
  for sx in range(264):
   src=(sy*264+sx)*4; dst=((y0*6+sy)*1920+x0*3+sx)*4; alpha=fx[src+3]
   for channel in range(3):expected[dst+channel]=min(255,fx[src+channel]+(expected[dst+channel]*(255-alpha)+127)//255)
   expected[dst+3]=255
 actual=Image.open(Path(str(packet)+'.png')).convert('RGBA').tobytes()
 assert bytes(expected)==actual,(record,sum(a!=c for a,c in zip(expected,actual)))
 assert Image.open(Path(str(cp)+'.png')).convert('RGBA').tobytes()==actual
 assert frozen['RGBA']==meta['checkpoint_rgba_sha256']==sha(actual)
 expected_draws[meta['actual_draw']]=(meta['step'],actual)
 results.append({'record':record,'actual_Draw':meta['actual_draw'],'step':meta['step'],'checkpoint':meta['checkpoint'],'checkpoint_step':meta['checkpoint_step'],'RGBA_sha256':sha(actual),'full_pixels':2304000,'native_base_cells':occupied,'reset_source_sha256':reset['source_sha256']})
# Decode the lossless wide-canvas stream independently, then take its central rectangle.
linked=[]; frame=bytearray(2944*1264*4)
with gzip.open(s/'presentation.frames.gz','rb') as stream:
 assert stream.read(8)==b'8SFRM001' and struct.unpack('<II',stream.read(8))==(2944,1264)
 while header:=stream.read(24):
  ordinal,step,rows=struct.unpack('<QQQ',header)
  for _ in range(rows):
   y,=struct.unpack('<H',stream.read(2)); data=stream.read(2944*4); assert len(data)==2944*4
   frame[y*2944*4:(y+1)*2944*4]=data
  if ordinal in expected_draws:
   targetstep,target=expected_draws[ordinal]; assert step==targetstep
   central=b''.join(frame[((y+64)*2944+512)*4:((y+64)*2944+512+1920)*4] for y in range(1200))
   assert central==target; linked.append(ordinal)
assert set(linked)==set(expected_draws)
for phase in ['save','reload']:
 st=read(g/phase/'gui-final.json')
 assert st['closed'] and not st['battle_marker_error'] and not st['battle_actor_error'] and not st['battle_effect_error']
 assert st['text']['MissingGlyphs']==0 and not st['text']['Errors']
 assert read(g/phase/'continuous-audit.json')['frames']==st['recorded_frames']
st=read(s/'gui-final.json'); stats=st['graphics']
assert stats['BattleMarkerCalls']==stats['BattleMarkerCompletions']==len(calls) and stats['BattleMarkerFallbackCalls']==0
report={'status':'PASS-scoped-four-CHOI-actual-GUI-full-frame','source_calls':len(source['calls']),'source_returns':len(source['returns']),'CHOI_calls':len(calls),'records':results,'actual_Draw_stream_link':True,'Frame_purity':True,'limits':['four sampled actual Draw central images, source and original reset bytes independently verified','checkpoint layers may precede live guest metadata at Draw; linked by complete immutable RGBA','no gameplay, AI, damage, timing, RNG or game-wide parity claim']}
(g/'choi-draw-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
