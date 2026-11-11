#!/usr/bin/env python3
"""Rust策略AI：來源準備、核對與永久保存。限Docker。"""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-ai-r1';REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def module(r,n):
 s=importlib.util.spec_from_file_location(n,r/'tools'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','audit','images','freeze','archive','verify','restore'])
 for n in ['project','work','out','archive']:ap.add_argument('--'+n,type=Path)
 a=ap.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=json.loads((a.archive/(BATCH+'.json')).read_text())
  for f in d['files']:
   ob=d['objects'][f['sha256']];p=a.archive/BATCH/ob['file'];assert sha(p)==ob['stored_sha256'];b=gzip.decompress(p.read_bytes());assert len(b)==f['bytes']and hashlib.sha256(b).hexdigest()==f['sha256']
  a.out.write_text(json.dumps(dict(status='passed-rust-ai-detached',files=len(d['files']),objects=len(d['objects'])))+'\n');return
 r=a.project;q=a.work or r/REL;h=module(r,'prepare-owned-army-ui.py')
 if a.action=='archive':m=module(r,'rust-world-exits.py');m.BATCH=BATCH;m.REL=REL;m.main();return
 if a.action=='restore':
  for f in json.loads((r/'preserved'/(BATCH+'.json')).read_text())['files']:
   rel=Path(f['path']).relative_to(REL)
   if str(rel)=='native/8sword-remake'or str(rel).startswith('native/pack/'):
    p=q/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(h.stored(r,BATCH,f['path']));p.chmod(f['mode'])
  return
 if a.action=='freeze':
  shutil.copytree(r/'internal/remake-rust',q/'rust-source');(q/'tools').mkdir()
  for n in ['rust-ai.py','rust-ai-gui.py','rust-ai-reference-main.txt','rust-native-player.sh']:shutil.copy2(r/'tools'/n,q/'tools'/n)
  (q/'media.json').write_text(json.dumps({p.name:sha(p)for p in(q/'native/pack').iterdir()if p.is_file()},indent=2)+'\n');return
 if a.action in ['audit','images']:
  from PIL import Image,ImageDraw,ImageFont
  import io,struct
  gui=json.loads((q/'native/gui/receipt.json').read_text());assert gui['status']=='passed-rust-ai-gui'and len(gui['runs'])==7 and gui['binary_sha256']==sha(q/'native/8sword-remake');captures=[]
  for run in gui['runs']:
   assert run['exit']==0
   for c in run['captures']:
    folder=q/'native/gui'/run['name'];n=c['number'];p=folder/f'frame-{n:03}.ppm';full=folder/f'shell-frame-{n:03}.ppm';assert p.read_bytes()==p.with_name(f'readback-{n:03}.ppm').read_bytes();assert full.read_bytes()==full.with_name(f'shell-readback-{n:03}.ppm').read_bytes();assert Image.open(full).convert('RGB').crop((512,0,2432,1320)).tobytes()==Image.open(p).convert('RGB').tobytes();captures.append(dict(run=run['name'],**c,central_sha256=sha(p),full_sha256=sha(full)))
  assert len(captures)==20
  if a.action=='images':
   idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),28,index=3);canvas=Image.new('RGB',(1920,980),(8,36,23));draw=ImageDraw.Draw(canvas);chosen=[]
   for i,(run,label,title)in enumerate([('native','native-hit','原版AI首擊：97猴妖／2僵屍'),('target','target-hit','策略AI首擊：100猴妖／0僵屍'),('journey','natural-ai-hit','正常旅程：三次策略決策，沒有改選'),('legacy','target-hit','舊工具列字集：ASCII策略AI')]):
    c=next(c for c in captures if c['run']==run and c['label']==label);im=Image.open(q/'native/gui'/run/f'shell-frame-{c["number"]:03}.ppm');x=i%2*960;y=i//2*490;draw.text((x+8,y+8),title,font=font,fill=(239,216,155));canvas.paste(im.resize((960,430),Image.Resampling.LANCZOS),(x,y+50));chosen.append(c)
   canvas.save(a.out);a.out.with_suffix('.json').write_text(json.dumps(dict(image_sha256=sha(a.out),binary_sha256=gui['binary_sha256'],sources=chosen,scope=gui['scope']),ensure_ascii=False,indent=2)+'\n');return
  assert '183 passed; 0 failed'in(q/'native/tests.log').read_text();ref=json.loads((q/'reference/receipt.json').read_text());assert ref['vectors']==408;assert(q/'reference/ai-reference.tsv').read_bytes()==(r/'internal/remake-rust/ai-reference.tsv').read_bytes()
  for name in ['native','target','cold-native','cold-target','legacy']:
   row=next(v for v in gui['runs']if v['name']==name);before=row['captures'][0]['captured'];after=row['captures'][-1]['captured'];assert before['seed']=='1'and after['seed']=='752224798'and after['sequence']=='1';assert after['army']==('97,2,0,0,0,0'if name in ['native','cold-native']else'100,0,0,0,0,0')
  random=1;rolls=[]
  for _ in range(128):
   random=(random*214013+2531011)&0xffffffff;slot=((random>>16)&32767)%6;rolls.append(slot)
   if slot in [0,1]:break
  assert len(rolls)==7 and slot==0 and random==752224798
  prior=json.loads((r/'preserved/rust-poster-audit-r1.json').read_text());oldcap=next(c for c in prior['gui']['runs']if c['name']=='world')['captures'][0];newcap=next(c for c in captures if c['run']=='journey'and c['label']=='world-target');assert oldcap['captured']['state_hash']==newcap['captured']['state_hash'];raw=h.stored(r,'rust-poster-r1',f'native/gui/world/frame-{oldcap["number"]:03}.ppm');(q/'evidence/previous-world.ppm').write_bytes(raw);assert Image.open(io.BytesIO(raw)).convert('RGB').tobytes()==Image.open(q/'native/gui/journey'/f'frame-{newcap["number"]:03}.ppm').convert('RGB').tobytes()
  previous=json.loads((r/'preserved/rust-poster-r1.json').read_text());old={Path(f['path']).name:f['sha256']for f in previous['files']if'/native/pack/'in f['path']};assert len(old)==159 and all(sha(q/'native/pack'/n)==v for n,v in old.items()if n!='poster-font.bin')
  def glyphs(b):return{chr(struct.unpack_from('<I',b,12+i*4100)[0]):b[16+i*4100:12+(i+1)*4100]for i in range(struct.unpack_from('<I',b,8)[0])}
  oldglyph=glyphs(h.stored(r,'rust-poster-r1','native/pack/poster-font.bin'));newglyph=glyphs((q/'native/pack/poster-font.bin').read_bytes());assert len(oldglyph)==16 and len(newglyph)==22 and all(newglyph[c]==v for c,v in oldglyph.items())
  crate={str(p.relative_to(r/'internal/remake-rust')):sha(p)for p in(r/'internal/remake-rust').rglob('*')if p.is_file()};assert all(sha(q/'rust-source'/n)==v for n,v in crate.items())
  a.out.write_text(json.dumps(dict(status='passed-rust-ai-audit',tests=183,go_vectors=ref,fixed_spell_seeds=list(range(1,65)),controlled_rng=dict(seed=1,raw_slot_rolls=rolls,final_seed=random),unchanged_media=158,old_poster_glyphs_unchanged=16,new_poster_glyphs=6,runtime_files=160,crate=crate,gui=gui,captures=captures,same_state_previous_world_equal=True,execution=json.loads((q/'execution.json').read_text()),limits=['Existing Go target-ranking policy, not a win-rate or cross-spell planner claim.','Native word estimator remains distinct from widened Rust battle arithmetic; scoring does not alter damage.','Eight old original-controlled views plus384 generated and16 synthetic OpenKB stat views; no new DOS oracle.','Explicit battle fixture; natural v16 journey has3 decisions/0 changed.','Mode session-only, native default at restart; CLI target is explicit.']),ensure_ascii=False,indent=2)+'\n');return
 assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir()
 for n in ['native/pack','evidence','reference']:(q/n).mkdir(parents=True)
 for f in json.loads((r/'preserved/rust-poster-r1.json').read_text())['files']:
  if '/native/pack/'in f['path']:(q/'native/pack'/Path(f['path']).name).write_bytes(h.stored(r,'rust-poster-r1',f['path']))
 (q/'native/legacy-v16.chk').write_bytes(h.stored(r,'rust-poster-r1','native/legacy-v16.chk'))
 for name in ['front-ranged-mixed','normal-choice','normal-locked','normal-rear-only','rear-ranged-mixed','special0-choice','special2-choice','special5-empty-original']:
  prefix='ai-policy-extra-r2'if name=='special5-empty-original'else'ai-policy-r1';(q/'reference'/(name+'.json')).write_bytes(h.stored(r,'ai-policy-r1',prefix+'/'+name+'/shadow/trace.json'))
 (q/'reference/unit-catalog.tsv').write_bytes((r/'internal/remake-rust/unit-catalog.tsv').read_bytes())
 source=(r/'internal/eightsword/battle_ai_policy.go').read_text();assert hashlib.sha256(source.encode()).hexdigest()=='54ac5e33643b4f11079284d397a1bb7fd7dafa90d5b41c8966bbbb3e6dd9fa5a';(q/'evidence/battle_ai_policy.go').write_text(source)
 rules=(r/'internal/eightsword/battle_rules.go').read_text();functions=''
 for name in ['formationEligible','formationDamage','archerPressureEligible','archerPressureDamage']:
  start=rules.index('func '+name+'(');stop=rules.find('\nfunc ',start+6);functions+=rules[start:stop]+'\n'
 go=source.replace('package eightsword','package main',1).replace('import "fmt"','import ("fmt";"os";"encoding/json";"errors";"strings";"strconv")',1)+'\nvar errBattleAINoTarget=errors.New("none")\n'+functions
 go+=(r/'tools/rust-ai-reference-main.txt').read_text();(q/'reference-go.go').write_text(go)
 from PIL import Image,ImageDraw,ImageFont
 import io,struct
 path=q/'native/pack/poster-font.bin';raw=path.read_bytes();assert raw[:8]==b'8SGLYP01';old={chr(struct.unpack_from('<I',raw,12+i*4100)[0]):raw[16+i*4100:12+(i+1)*4100]for i in range(struct.unpack_from('<I',raw,8)[0])};assert len(old)==16
 idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),56,index=3);glyphs=dict(old)
 for ch in '原版策略AI':
  im=Image.new('L',(64,64));ImageDraw.Draw(im).text((32,32),ch,font=font,fill=255,anchor='mm');glyphs[ch]=im.tobytes()
 b=bytearray(b'8SGLYP01'+struct.pack('<I',len(glyphs)))
 for ch,ink in sorted(glyphs.items()):b+=struct.pack('<I',ord(ch))+ink
 b+=struct.pack('<Q',module(r,'rust-native-player.py').fnv(b));path.write_bytes(b);assert all(glyphs[c]==v for c,v in old.items())
 (q/'evidence/assets.json').write_text(json.dumps(dict(old_poster_glyphs=16,preserved=True,new_glyphs=6,total=len(glyphs),font_source=h.FONT_SHA['noto'],font_index=3),indent=2)+'\n')
 print('prepared',q)
if __name__=='__main__':main()
