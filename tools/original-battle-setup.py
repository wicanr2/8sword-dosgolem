#!/usr/bin/env python3
"""Spec030 original formation/HP host bridge and held expanded setup evidence."""
import argparse,gzip,hashlib,importlib.util,json,os,re,shutil
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
REL='workplace/probe-20261023/graphics-first/battle-r1/original-battle-setup-r1';BATCH='original-battle-setup-r1'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','audit','publish','archive','verify']);
 for n in ['project','archive','out']:p.add_argument('--'+n,type=Path)
 a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   o=d['objects'][f['sha256']];z=(a.archive/BATCH/o['file']).read_bytes();assert hashlib.sha256(z).hexdigest()==o['stored_sha256'];raw=gzip.decompress(z);assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-original-battle-setup',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL;s=importlib.util.spec_from_file_location('helper',r/'tools/prepare-owned-army-ui.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h);deps=h.dependencies(r)
 if a.action=='prepare':
  assert q.is_dir()and not(q/'inputs').exists();(q/'inputs').mkdir();parent=q.parent/'original-battle-bridge-r1'
  for n in ['probe.mod','probe.sum']:shutil.copyfile(parent/n,q/n)
  for n in ['army-catalog.json','combat-catalog.json','PAM.AY','start.state']:shutil.copyfile(parent/'inputs'/n,q/'inputs'/n)
  latest=q.parent/'troop-presentation-fix-r1';shutil.copytree(latest/'ui-assets',q/'ui-assets');shutil.copyfile(latest/'initial-session/gamedata.ay.army.json',q/'inputs/setup-world.json');write(q/'baseline.json',deps)
 if a.action in ['prepare','freeze']:
  assert deps==read(q/'baseline.json');names=set(read(r/'preserved/owned-player-source-manifest-r1.json'))|{str(p.relative_to(r))for p in(r/'internal/ownedworld').glob('*.go')}
  for n in sorted(names):dst=q/'source'/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,dst)
  (q/'source-manifest.json').write_text(json.dumps({n:sha(q/'source'/n)for n in sorted(names)},ensure_ascii=False,indent=2)+'\n')
  for n in ['original-battle-setup.py','export-original-battle-setup-ida.py']:shutil.copyfile(r/'tools'/n,q/n)
  return
 if a.action=='audit':
  from PIL import Image
  assert deps==read(q/'baseline.json')
  for n,d in read(q/'source-manifest.json').items():assert sha(r/n)==sha(q/'source'/n)==d
  ida=read(q/'ida/ida-setup.json');assert ida['function_count']==521 and len(ida['functions'])==12 and ida['exporter_sha256']==sha(r/'tools/export-original-battle-setup-ida.py')
  pam=(q/'inputs/PAM.AY').read_bytes();im=bytearray(pam);word=lambda at:int.from_bytes(pam[at:at+2],'little');header=word(8)*16
  for i in range(word(6)):
   at=word(24)+i*4;off=header+word(at+2)*16+word(at);im[off:off+2]=((word(off)+0x1000)&65535).to_bytes(2,'little')
  for f in ida['functions']:
   for l in f['lines']:
    raw=bytes.fromhex(l['bytes']);assert im[l['file_offset']:l['file_offset']+len(raw)]==raw
  controls=read(q/'controls-r1/receipt.json');assert controls['status']=='passed-original-battle-setup-controls'and len(controls['helper_pairs'])==12 and len(controls['extension_models'])==8
  refusals=read(q/'refusals-r1.json');assert refusals['status']=='passed-original-battle-setup-refusals'and len(refusals['cases'])==12 and refusals['state_unchanged']
  first=read(q/'source-before-extra-tests.json');current=read(q/'source-manifest.json')
  changed=[]
  for n in first:
   if not n.endswith('_test.go')and first[n]!=current[n]:changed.append(n)
  assert changed==['internal/ownedworld/original_battle_setup.go']
  old_ops,new_ops=[host_ops(q/n)for n in ['cold-host-setup-asm.txt','final-host-setup-asm.txt']];assert old_ops==new_ops and len(old_ops)==2180
  assert read(q/'host-code-comparison-r1.json')['normalized_sha256']==hashlib.sha256('\n'.join(old_ops).encode()).hexdigest()
  catalog=read(q/'inputs/combat-catalog.json')['profiles']
  for c in controls['helper_pairs']:
   plan=c['plan']
   for side in range(2):
    for i,s in enumerate(c['rows'][side]):
     hp=catalog[s['unit']]['hp']*s['count']if s['unit']else 0;assert plan['hp'][side][i]==hp and plan['native_hp'][side][i]==hp%65536
  for c in controls['extension_models']:
   assert c['plan']['hp'][0][0]==catalog[c['id']]['hp']*4294967295 and c['plan']['native_hp'][0][0]==0
  action=read(q/'action-r1/receipt.json');assert action['normal_cold_start']and not action['snapshot_loaded']and len(action['rows'])==4
  for hd in [False,True]:
   rows=[x for x in action['rows']if x['hd']==hd];assert {k:v for k,v in rows[0].items()if k!='mode'}=={k:v for k,v in rows[1].items()if k!='mode'}
   x=Image.open(q/'action-r1'/f'hd-{str(hd).lower()}-mode-0/frame.png');y=Image.open(q/'action-r1'/f'hd-{str(hd).lower()}-mode-1/frame.png');assert x.tobytes()==y.tobytes()
  preview=read(q/'preview-r1/receipt.json');assert not preview['playable']and not preview['actual_window_verified']and len(preview['rows'])==2
  raw_art=read(q/'raw-art-r1/receipt.json');assert not raw_art['game_renderer_used'];art={v['id']:v for v in raw_art['rows']};composition=[]
  for row in preview['rows']:
   assert row['round_entries']==0 and row['held_retries']==5 and row['plan']['extended'];raw=bytes.fromhex(row['native_rows_hex'])
   for i,s in enumerate(row['plan']['rows'][0]):
    if s['unit']and catalog[s['unit']].get('native_kind',0)==0:assert raw[i*4:i*4+4]==bytes(4)and row['plan']['hp'][0][i]>0
   im=Image.open(q/'preview-r1'/str(row['case'])/'frame.png').convert('RGBA');assert im.size==(1920,1200)and hashlib.sha256(im.tobytes()).hexdigest()==row['frame_rgba_sha256']
   # Fixed coordinate bytes come from the pristine PAM data segment. Source
   # and result PNGs are actual Engine frames; reconstruct new actors from
   # standard-library-decoded premultiplied source bytes, not game drawing.
   coords=bytes.fromhex(row['coords_hex']);offset=header+(0x1e88-0x110)*16+0x703c;assert pam[offset:offset+12]==coords
   base=Image.open(q/'preview-r1'/str(row['case'])/'source.png').convert('RGBA');out=bytearray(base.tobytes());assert all(v==255 for v in out[3::4]);sprites=0
   for slot,raw_index in enumerate(row['plan']['slots'][0]):
    if raw_index>=6:continue
    s=row['plan']['rows'][0][raw_index]
    if not s['unit']or catalog[s['unit']].get('native_kind',0):continue
    item=art[s['unit']];pixels=(q/'raw-art-r1'/item['file']).read_bytes();assert len(pixels)==512*512*4 and hashlib.sha256(pixels).hexdigest()==item['rgba_sha256']and sha(q/'ui-assets'/item['source_file'])==item['source_sha256'];alpha=Image.frombytes('RGBA',(512,512),pixels).getchannel('A');x0,y0,x1,y1=alpha.getbbox();sw,sh=x1-x0,y1-y0;w,h=264,300
    if w*sh>h*sw:w=h*sw//sh
    else:h=w*sh//sw
    left=coords[slot*2]*24+(264-w)//2;top=coords[slot*2+1]*6+(300-h)//2
    for y in range(h):
     for x in range(w):
      src=((y0+y*sh//h)*512+x0+x*sw//w)*4;dest=((top+y)*1920+left+x)*4;a0=pixels[src+3]
      for channel in range(3):out[dest+channel]=pixels[src+channel]+(out[dest+channel]*(255-a0)+127)//255
    sprites+=1
   assert bytes(out)==im.tobytes();composition.append(dict(case=row['case'],sprites=sprites,whole_frame_reconstructed=True,coords_pristine_PAM=True))
  assert(q/'tests-r1.log').read_text().rstrip().endswith('PASS')and(q/'tests-extra-r1.log').read_text().rstrip().endswith('PASS')
  write(a.out,dict(status='passed-original-battle-setup-audit',source_files=len(read(q/'source-manifest.json')),ida_functions=len(ida['functions']),direct_operand_sites=len(ida['direct_consumers']),helper_pairs=12,runtime_refusals=12,extended_uint32_models=8,cold_native_hd_pairs=2,held_preview_cases=2,held_retries_each=5,independent_composition=composition,new_ids_in_original_tables=0,ordinary_player_entry_disabled=True,not_verified=['playable expanded battle','new-unit targeting/casualties/spells','GUI','world battle save lifecycle']));return
 if a.action=='publish':
  import io
  from PIL import Image,ImageDraw,ImageFont
  assert read(r/'preserved/original-battle-setup-audit-r1.json')['status']=='passed-original-battle-setup-audit';idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),34,index=3);out=Image.new('RGB',(1920,750),'#11251f');draw=ImageDraw.Draw(out);sources=[]
  for i,title in enumerate(['既有Go進度：30民兵＋2野狼','明示六隊：女弓箭手、農民與其餘新兵']):
   p=q/'preview-r1'/str(i)/'frame.png';out.paste(Image.open(p).resize((960,600),Image.Resampling.NEAREST),(i*960,64));draw.text((i*960+20,10),title,font=font,fill='#fff1b5');sources.append(dict(path=str(p.relative_to(r)),sha256=sha(p)))
  draw.text((24,679),'原版HD戰場的初始陣位；Go持有身份與完整HP，新增ID不進原表。出手前暫停，尚未可玩。',font=font.font_variant(size=24),fill='#fff1b5');p=a.out/'original-battle-extended-setup-r1.png';assert not p.exists();out.save(p);write(a.out/'original-battle-extended-setup-r1.json',dict(schema=1,output_sha256=sha(p),inputs=sources,actual_window_verified=False,playable=False,controlled_typed_override=True,scope='Initial formation and HP only; host gate holds before every action.'));return
 if a.action=='archive':
  assert read(r/'preserved/original-battle-setup-audit-r1.json')['status']=='passed-original-battle-setup-audit';folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
  for f in sorted(q.rglob('*')):
   if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
   assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();digest=hashlib.sha256(raw).hexdigest();obj=folder/(digest+'.gz')
   if digest not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[digest]=dict(file=obj.name,stored_sha256=sha(obj))
   files.append(dict(path=str(f.relative_to(r)),bytes=len(raw),sha256=digest,mode=f.stat().st_mode&0o777))
  write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Complete original data, full PNGs, states and binaries local only. Expanded preview is not playable.'))
def host_ops(path):
 rows=[];base=None
 for line in path.read_text().splitlines():
  if line.startswith('TEXT'):rows.append(line);base=None;continue
  match=re.match(r'\s+\S+:\d+\s+(0x[0-9a-f]+)\s+([0-9a-f]+)\s+(\w+)\s*(.*)',line)
  if not match:continue
  pc,code,op,args=match.groups();pc=int(pc,16);args=args.strip()
  if base is None:base=pc
  if op.startswith('J')and re.fullmatch('0x[0-9a-f]+',args):args='relative:'+str(int(args,16)-base)
  rows.append(op+' '+re.sub(r'0x[0-9a-f]+\(IP\)','PCREL_DATA(IP)',args))
 return rows
if __name__=='__main__':main()
