#!/usr/bin/env python3
"""Spec030 held original enemy targeting: prepare, audit and detached preservation."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/original-battle-actions-r1'
BATCH='original-battle-actions-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','audit','publish','archive','verify'])
 for n in ['project','archive','out']:p.add_argument('--'+n,type=Path)
 a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   o=d['objects'][f['sha256']];z=(a.archive/BATCH/o['file']).read_bytes();assert hashlib.sha256(z).hexdigest()==o['stored_sha256'];raw=gzip.decompress(z);assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-original-battle-actions',files=len(d['files']),objects=len(d['objects'])));return
 r=a.project;q=r/REL;s=importlib.util.spec_from_file_location('helper',r/'tools/prepare-owned-army-ui.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h);deps=h.dependencies(r)
 if a.action=='prepare':
  assert q.is_dir()and not(q/'inputs').exists();parent=q.parent/'original-battle-setup-r1'
  shutil.copytree(parent/'inputs',q/'inputs');shutil.copytree(parent/'ui-assets',q/'ui-assets')
  for n in ['probe.mod','probe.sum']:shutil.copyfile(parent/n,q/n)
  write(q/'baseline.json',deps)
 if a.action in ['prepare','freeze']:
  assert deps==read(q/'baseline.json');names=set(read(r/'preserved/owned-player-source-manifest-r1.json'))|{str(p.relative_to(r))for p in(r/'internal/ownedworld').glob('*.go')}
  for n in sorted(names):dst=q/'source'/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,dst)
  (q/'source-manifest.json').write_text(json.dumps({n:sha(q/'source'/n)for n in sorted(names)},ensure_ascii=False,indent=2)+'\n')
  for n in ['original-battle-actions.py','export-original-battle-actions-ida.py']:shutil.copyfile(r/'tools'/n,q/n)
  return
 if a.action=='audit':
  from PIL import Image
  assert deps==read(q/'baseline.json')
  for n,d in read(q/'source-manifest.json').items():assert sha(r/n)==sha(q/'source'/n)==d
  ida=read(q/'ida/ida-actions.json');assert ida['function_count']==521 and len(ida['functions'])==14 and ida['exporter_sha256']==sha(r/'tools/export-original-battle-actions-ida.py')
  pam=(q/'inputs/PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()==ida['source_sha256'];im=bytearray(pam);word=lambda at:int.from_bytes(pam[at:at+2],'little');header=word(8)*16
  for i in range(word(6)):
   at=word(24)+i*4;off=header+word(at+2)*16+word(at);im[off:off+2]=((word(off)+0x1000)&65535).to_bytes(2,'little')
  lines={}
  for f in ida['functions']:
   for l in f['lines']:
    raw=bytes.fromhex(l['bytes']);assert im[l['file_offset']:l['file_offset']+len(raw)]==raw;lines[l['ida_linear']]=l
  controls=read(q/'presence-controls.json');assert controls['status']=='passed-original-battle-presence-controls'and controls['original_RAM_unchanged']and len(controls['native_pairs'])==65 and len(controls['extension_reads'])==80 and len(controls['refusals'])==10
  aliases=controls['transient_alias_pairs'];assert [v['Value']for v in aliases]==[0,1]
  for v in aliases:assert v['Slot']==0 and v['BX']==v['MapWord']*4%65536 and v['Offset']==(v['BX']+0x56ea)%65536
  guards=read(q/'presence-guards.json');assert guards['held_model_refusals']==5 and guards['target_gate_refusals']==6 and guards['held_capture_refusal']and guards['state_unchanged']
  for row in controls['native_pairs']:
   l=lines[row['ida']];assert l['bytes']in ['83bf025700','83bfea5600'];v=row['count'];flags=0xad7&~0x8d5
   if v==0:flags|=0x40
   if v&0x8000:flags|=0x80
   if (v&255).bit_count()%2==0:flags|=4
   assert flags==row['flags']and row['next_ip']==row['ida']-0x1e570+5
  cold=read(q/'cold-receipt.json');assert cold['normal_cold_start']and not cold['snapshot_loaded']and cold['seed']==0x12345678
  for hd in [False,True]:
   rows=[v for v in cold['rows']if v['hd']==hd];assert len(rows)==2 and rows[0]['comparisons']==0 and rows[1]['comparisons']>0
   assert rows[1]['transient_alias_reads']and all(v['BX']==v['MapWord']*4%65536 and v['Offset']==(v['BX']+0x56ea)%65536 for v in rows[1]['transient_alias_reads'])
   for key in ['target','units_hex','frame_rgba_sha256','seed_after']:assert rows[0][key]==rows[1][key]
   x=Image.open(q/'cold-r1'/f'hd-{str(hd).lower()}-mode-0/frame.png').convert('RGBA');y=Image.open(q/'cold-r1'/f'hd-{str(hd).lower()}-mode-1/frame.png').convert('RGBA');assert x.tobytes()==y.tobytes()and hashlib.sha256(x.tobytes()).hexdigest()==rows[0]['frame_rgba_sha256']
  expanded=read(q/'expanded-receipt.json');assert not expanded['playable']and not expanded['actual_window_verified']and len(expanded['rows'])==2
  catalog=read(q/'inputs/combat-catalog.json')['profiles'];original=(q/'inputs/setup-world.json')
  for row in expanded['rows']:
   target=row['target'];assert target['Target']['unit'].startswith('openkb:')and target['Target']['count']>0 and row['extended_reads']>0 and row['held_retries']==5 and row['projection_captures']==0 and row['controlled_enemy_first_argument']
   assert row['plan']['rows'][0][target['TargetRaw']]==target['Target']
   raw=bytes.fromhex(row['native_rows_hex'])
   for i,s in enumerate(row['plan']['rows'][0]):
    if s['unit']and catalog[s['unit']].get('native_kind',0)==0:assert raw[i*4:i*4+4]==bytes(4)
   assert bytes.fromhex(row['shadow_hex'])==bytes.fromhex(cold['rows'][0]['units_hex'])[:24]
  assert(q/'tests-r1.log').read_text().rstrip().endswith('PASS')
  assert(q/'projection-regression.log').read_text().rstrip().endswith('PASS')and len(read(q/'models-r1.json')['refusals'])==19
  write(a.out,dict(status='passed-original-battle-actions-audit',source_files=len(read(q/'source-manifest.json')),ida_functions=14,native_comparison_pairs=65,extended_uint32_reads=80,comparison_refusals=10,held_model_refusals=5,target_gate_refusals=6,held_capture_refusal=True,transient_alias_pairs=2,cold_native_HD_pairs=2,expanded_enemy_targets=2,controlled_enemy_first_argument=True,held_retries_each=5,native_projection_regression_refusals=19,new_ids_in_original_tables=0,ordinary_player_entry_disabled=True,not_verified=['expanded player turn/attack/casualties/spells','complete battle','GUI','world battle save lifecycle']));return
 if a.action=='publish':
  import io
  from PIL import Image,ImageDraw,ImageFont
  assert read(r/'preserved/original-battle-actions-audit-r1.json')['status']=='passed-original-battle-actions-audit'
  idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),32,index=3)
  out=Image.new('RGB',(1920,750),'#11251f');draw=ImageDraw.Draw(out);sources=[];receipt=read(q/'expanded-receipt.json')
  for i,title in enumerate(['混合編成：電腦選到2野狼','全新增編成：電腦選到3農民槍兵']):
   source=q/'expanded-r1'/str(i)/'frame.png';out.paste(Image.open(source).resize((960,600),Image.Resampling.NEAREST),(i*960,64));draw.text((i*960+20,10),title,font=font,fill='#fff1b5');sources.append(dict(path=str(source.relative_to(r)),sha256=sha(source),target=receipt['rows'][i]['target']))
  draw.text((24,679),'原版HD戰場；敵先手為受控條件，只驗Go存活與原版選敵，扣兵前暫停。尚不可戰鬥。',font=font.font_variant(size=26),fill='#fff1b5')
  dest=a.out/'original-battle-extended-target-r1.png';assert not dest.exists();out.save(dest)
  write(a.out/'original-battle-extended-target-r1.json',dict(schema=1,output_sha256=sha(dest),inputs=sources,actual_window_verified=False,playable=False,controlled_typed_override=True,controlled_enemy_first_argument=True,scope='Original HD enemy selection only; held before damage; original RNG retained.'));return
 if a.action=='archive':
  assert read(r/'preserved/original-battle-actions-audit-r1.json')['status']=='passed-original-battle-actions-audit';folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
  for f in sorted(q.rglob('*')):
   if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
   assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();digest=hashlib.sha256(raw).hexdigest();obj=folder/(digest+'.gz')
   if digest not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[digest]=dict(file=obj.name,stored_sha256=sha(obj))
   files.append(dict(path=str(f.relative_to(r)),bytes=len(raw),sha256=digest,mode=f.stat().st_mode&0o777))
  write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Full original data, images, states and binaries local only. Expanded battle is held before damage.'))
if __name__=='__main__':main()
