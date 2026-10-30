#!/usr/bin/env python3
"""030 DRAFT: prepare and preserve the isolated Go F3 candidate."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,struct,re
from pathlib import Path
REL='workplace/probe-20261023/graphics-first/battle-r1/owned-world-army-dismiss-r1'
BATCH='owned-world-army-dismiss-r1'
NEW=['research-world-army-dismiss.go','world-army-dismiss_draw.go','research-world-army-dismiss_test.go','prepare-world-army-dismiss.py','check-world-army-dismiss.py','world-army-dismiss.sh']
COMMON=['research-owned-army.go','research-owned-world.go','research-native-progress.go','research-paired-progress.go','research-world-army-port.go','research-world-army-review.go','world-army-review_draw.go','world-army-review_main.go','research-world-army-review_test.go','owned-army-ui.go','owned-army-ui_draw.go','owned-army-ui-xcheck.go','prepare-owned-army-ui.py','prepare-world-army-review.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def load(r,n):
 s=importlib.util.spec_from_file_location(n,r/'tools'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','archive','verify','audit','integrity']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
 if a.action=='verify':
  d=read(a.archive/(BATCH+'.json'))
  for f in d['files']:
   o=d['objects'][f['sha256']];obj=a.archive/BATCH/o['file'];assert sha(obj)==o['stored_sha256'];raw=gzip.decompress(obj.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  write(a.out,dict(status='passed-detached-dismiss',files=len(d['files']),objects=len(d['objects']),workplace_required=False));return
 r=a.project;q=r/REL;m=load(r,'prepare-owned-army-ui.py');deps=m.dependencies(r)
 if a.action=='integrity':
  assert deps==read(q/'baseline-r1.json');assert read(r/'preserved/owned-world-army-dismiss-audit-r1.json')['status']=='passed-draft-f3-dismiss';assert read(r/'preserved/owned-world-army-dismiss-verification-r1.json')['status']=='passed-detached-dismiss'
  docs=['README.md','AGENTS.md','CONTEXT.md','WORKLOG.md','RESEARCH-LOG.md','preserved/README.md','docs/spec/030-battle-expansion-proposal.md'];links=0
  # Positive control ensures the parser sees the existing F2 tool index.
  assert 'tools/world-army-review_main.go)'in(r/'docs/spec/030-battle-expansion-proposal.md').read_text()
  for name in docs:
   p=r/name
   for ref in re.findall(r'\]\(([^)]+)\)',p.read_text()):
    ref=ref.split('#')[0]
    if not ref or re.match(r'[a-z]+://',ref):continue
    target=(p.parent/ref).resolve()
    if target==a.out.resolve():continue
    assert target.exists(),(name,ref);links+=1
  for root in [q,r/'preserved'/BATCH]:
   for p in root.rglob('*'):assert p.stat().st_uid==1000 and not(p.is_dir()and p.name.endswith('.md')),(str(p),p.stat().st_uid)
  for n in NEW+COMMON:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n)
  write(a.out,dict(status='passed-dismiss-integrity',dependencies=deps,local_links=links,source_tools={n:sha(r/'tools'/n)for n in NEW+COMMON},ownership='uid1000',production_changed=False));return
 if a.action=='prepare':
  assert not q.exists();q.mkdir();assert q.stat().st_uid==1000
  for n in ['inputs','ui-assets','ida']: (q/n).mkdir()
  src=q/'go-src'
  for n in deps['source_inputs']:
   t=src/n;t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/n,t)
  (src/'tools').mkdir(exist_ok=True)
  for n in NEW+COMMON:shutil.copyfile(r/'tools'/n,src/'tools'/n)
  t=(r/'tools/research-owned-army.go').read_text().removeprefix('//go:build ignore\n');t=t[:t.index('func main()')].replace('\n\t"flag"\n','\n');(src/'tools/owned-army-model.go').write_text(t)
  for ext in ['mod','sum']:shutil.copyfile(src/('go.'+ext),q/('probe.'+ext))
  with(q/'probe.mod').open('a')as f:f.write('\nrequire github.com/wicanr2/dosgolem v0.0.0\nreplace github.com/wicanr2/dosgolem => /core\n')
  for n in ['army-catalog.json','combat-catalog.json']:(q/'inputs'/n).write_bytes(m.stored(r,'owned-world-army-r1','/inputs/'+n))
  native=m.stored(r,'owned-world-army-r1','/port-r2/paired-save/gamedata.ay');world=m.stored(r,'owned-world-army-r1','/port-r2/paired-save/gamedata.ay.army.json');(q/'inputs/review-save.json').write_bytes(world)
  (q/'inputs/map01.ay').write_bytes(m.stored(r,'owned-world-army-r1','/port-r2/scratch/map01.ay'))
  for name in ['session-r1','session-preview-r1']:
   folder=q/name;folder.mkdir();(folder/'gamedata.ay').write_bytes(native);(folder/'gamedata.ay.army.json').write_bytes(world)
  (q/'ida/ida-army-view-r1.json').write_bytes(m.stored(r,'owned-world-army-view-r1','/ida/ida-army-view-r1.json'))
  load(r,'prepare-world-army-review.py').fonts(r,q,m,['world-army-dismiss_draw.go'])
  write(q/'baseline-r1.json',deps);return
 if a.action=='audit':
  assert deps==read(q/'baseline-r1.json')
  gui=read(q/'gui-r1/receipt.json');assert gui['status']=='passed-actual-f3-dismiss'
  from PIL import Image
  for s in gui['screens']:
   folder=q/'gui-r1'/s['phase'];im=Image.open(folder/s['canvas']);screen=Image.open(folder/s['screen']);assert im.size==screen.size==(1920,1200)and im.convert('RGB').tobytes()==screen.convert('RGB').tobytes();state=read(folder/s['metadata']);assert hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()==state['canvas_sha256']==state['presented_sha256']
   for f in state['text_fields']or[]:
    rect,ink=f['Rect'],f['Ink'];assert ink==[0,0,0,0]or(rect[0]<=ink[0]<=ink[2]<=rect[2]and rect[1]<=ink[1]<=ink[3]<=rect[3])
   assert state['native_rows_hex']==gui['native_rows_hex']and state['native_row_draw_calls']==0
  # Independent world calculation from the original paired fixture; no Go helper.
  initial=read(q/'inputs/review-save.json')['world'];expected=json.loads(json.dumps(initial));expected['revision']+=1;slots=expected['army']['slots'];expected['army']['slots']=slots[1:]+[dict(unit='',count=0)]
  wolf=read(q/'gui-r1/owned/wolf-lishu.json')['world'];assert wolf==expected
  expected['revision']+=1;expected['army']['slots']=[dict(unit='',count=0)for _ in range(6)]
  assert read(q/'session-r1/gamedata.ay.army.json')['world']==expected
  assert (q/'session-r1/gamedata.ay').read_bytes()==(q/'session-preview-r1/gamedata.ay').read_bytes()
  # Cross-check all old IDA bytes against this exact MZ, including relocations.
  ida=read(q/'ida/ida-army-view-r1.json');raw=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes();assert ida['source_sha256']==hashlib.sha256(raw).hexdigest();header=struct.unpack_from('<H',raw,8)[0]*16;reloc=[]
  for i in range(struct.unpack_from('<H',raw,6)[0]):off,seg=struct.unpack_from('<HH',raw,struct.unpack_from('<H',raw,24)[0]+i*4);reloc.append(header+seg*16+off)
  lines=0
  for b in ida['functions']:
   for l in b['lines']:
    pos=l['file_offset'];want=bytes.fromhex(l['bytes']);actual=bytearray(raw[pos:pos+len(want)]);assert pos==l['ida_linear']-0x10000+header
    for loc in reloc:
     if pos<=loc and loc+2<=pos+len(want):struct.pack_into('<H',actual,loc-pos,(struct.unpack_from('<H',actual,loc-pos)[0]+0x1000)&65535)
    assert bytes(actual)==want;lines+=1
  for n in NEW+COMMON:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n)
  log=(q/'go-test-r1.log').read_text();assert'PASS'in log and'FAIL'not in log and'SKIP'not in log
  for n in ['go-build-r1.log','go-vet-r1.log','xcheck-build-r1.log','f2-build-r1.log']:assert(q/n).stat().st_size==0
  write(a.out,dict(status='passed-draft-f3-dismiss',dependencies=deps,source_tools={n:sha(r/'tools'/n)for n in NEW+COMMON},ida_lines=lines,independent_world_equal=True,gui=gui,production_changed=False));return
 assert a.action=='archive';files=[];objects={};dest=a.archive/BATCH;dest.mkdir(exist_ok=True);assert dest.stat().st_uid==1000
 for f in sorted(q.rglob('*')):
  if not f.is_file():continue
  raw=f.read_bytes();h=hashlib.sha256(raw).hexdigest();name=h+'.gz';obj=dest/name
  if not obj.exists():obj.write_bytes(gzip.compress(raw,compresslevel=6,mtime=0))
  else:assert gzip.decompress(obj.read_bytes())==raw
  objects[h]=dict(file=name,stored_sha256=sha(obj));files.append(dict(path=str(f.relative_to(r)),bytes=len(raw),sha256=h,mode=f.stat().st_mode&0o777))
 write(a.out,dict(schema=1,batch=BATCH,files=files,objects=objects,rights='Private original game data and generated research; objects excluded from Git.'))
if __name__=='__main__':main()
