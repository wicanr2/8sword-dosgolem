#!/usr/bin/env python3
"""Independent arithmetic, original bytes, frozen sources and X11 audit."""
import argparse,base64,copy,hashlib,importlib.util,json,os,struct,tempfile
from pathlib import Path
from PIL import Image
REL='workplace/probe-20261023/graphics-first/battle-r1/reinforcement-camps-r1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def word(b,g,r,f):
 at=2*(18+r*25+f*5+g);return(struct.unpack_from('<H',b,at)[0]-at-3)&65535
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--images',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000;r=a.project;q=r/REL
 s=importlib.util.spec_from_file_location('prep',r/'tools/prepare-reinforcement-camps.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);h=m.helper(r);deps=h.dependencies(r);assert deps==read(q/'baseline.json')
 for n,v in deps['source_inputs'].items():assert sha(q/'go-src'/n)==v,n
 for n in m.NEW:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n),n
 with tempfile.TemporaryDirectory()as td:
  t=Path(td);(t/'tools').mkdir()
  for n in m.PATCHED:(t/'tools'/n).write_bytes(h.stored(r,m.PARENT,'/'+m.PARENT+'/go-src/tools/'+n))
  m.patch(t)
  for n in m.PATCHED:assert(t/'tools'/n).read_bytes()==(q/'go-src/tools'/n).read_bytes(),n
 catalog={u['id']:u for u in read(q/'inputs/army-catalog.json')['profiles']};native=(q/'inputs/original-save.ay').read_bytes();model=read(q/'model-r1.json');assert model['status']=='passed-reinforcement-transactions'
 before=model['before']['world'];bound=copy.deepcopy(before);bound['revision']+=1
 ids=['arcr','pike','wolf','skel','troll','drui','vamp','drag'];g,row,kind=0,0,word(native,0,0,3);old=catalog[f'native:{kind:02d}']
 for suffix in ids:
  unit=catalog['openkb:'+suffix];bound['army']['offers'][f'reinforce:{g:02d}:{row:02d}:{kind:02d}:{suffix}']=dict(unit=unit['id'],stock=word(native,g,row,4)*old['gold']//unit['gold'])
 assert bound==model['bound']['world']
 def buy(w):
  w=copy.deepcopy(w);w['revision']+=1;w['army']['gold']-=40;k='reinforce:00:00:02:wolf';w['army']['offers'][k]['stock']-=1;w['army']['slots'][1]['unit']='openkb:wolf';w['army']['slots'][1]['count']+=1;return w
 purchased=buy(bound);assert purchased==model['purchased']['world'];recovered=buy(purchased);assert recovered==model['recovered']['world']
 saved=read(q/'session-camp-r2/gamedata.ay.army.json');assert saved['schema']=='eightsword-owned-world-save/5'and saved['world']==recovered
 actual=(q/'session-camp-r2/gamedata.ay').read_bytes();assert actual[12:]==native[12:]
 assert saved['original_sha256']==sha(q/'session-camp-r2/gamedata.ay')
 # Decode the fixed PAM cap table directly from MZ file coordinates.
 pam=(q/'inputs/PAM.AY').read_bytes();header=struct.unpack_from('<H',pam,8)[0]*16;monthly=copy.deepcopy(purchased);monthly['revision']+=1;expected_native=bytearray(native)
 for g in range(5):
  for row in range(24):
   kind=word(native,g,row,3)
   if not kind:continue
   stock=word(native,g,row,4);cap=struct.unpack_from('<H',pam,header+0x1d780+0x3a56+g*240+row*10)[0];next_stock=min(stock+max(stock//10,10),cap);at=2*(18+row*25+4*5+g);struct.pack_into('<H',expected_native,at,(next_stock+at+3)&65535)
   key=f'native-camp:{g:02d}:{row:02d}'
   if key in monthly['army']['offers']:monthly['army']['offers'][key]['stock']=next_stock
   for suffix in ids:
    key=f'reinforce:{g:02d}:{row:02d}:{kind:02d}:{suffix}'
    if key not in monthly['army']['offers']:continue
    o=monthly['army']['offers'][key];limit=cap*catalog[f'native:{kind:02d}']['gold']//catalog[o['unit']]['gold'];o['stock']=min(o['stock']+max(o['stock']//10,10),limit)
 due=sum(catalog[s['unit']]['gold']*s['count']for s in monthly['army']['slots']if s['count']);monthly['army']['gold']=min(30000,purchased['army']['gold']+purchased['progress']['legacy_04f6']-due);assert monthly==model['monthly_world']and due==70
 recorded=base64.b64decode(model['monthly_native']);assert recorded[12:]==bytes(expected_native)[12:]
 gui=read(q/'gui-r2/receipt.json');assert gui['status']=='passed-reinforcement-camp-ui';assert gui['pregranted_openkb_units']is False and gui['memory_injected']is False
 initial,original,opened,returned,cold,revisited=[gui[n]for n in ['initial','original','opened','returned','cold','revisited']]
 assert initial['world']['army']['slots']==[dict(unit='native:01',count=30)]+[dict(unit='',count=0)]*5
 assert len(opened['reinforcements']['offers'])==8 and opened['recruit_icons']['stock']==3000 and original['recruit_icons']['stock']==3000
 unit='reinforce:00:01:01:wolf';assert opened['world']['army']['offers'][unit]['stock']==75 and revisited['world']['army']['offers'][unit]['stock']==74
 expected=copy.deepcopy(opened['world']);expected['revision']+=1;expected['army']['gold']-=40;expected['army']['slots'][1]=dict(unit='openkb:wolf',count=1);expected['army']['offers'][unit]['stock']-=1
 assert expected==returned['world']==cold['world']==revisited['world'];assert returned['native_rows_hex']==initial['native_rows_hex'];assert gui['final']['world']==gui['checkpoint']['world']
 final_gui=read(q/'gui-r3/receipt.json');assert final_gui['status']=='passed-final-reinforcement-cold-ui'
 assert read(q/'model-final-r1/model-r1.json')==model
 frames=[]
 for batch,v in [('gui-r2',v)for v in gui['screens']]+[('gui-r3',v)for v in final_gui['screens']]:
  folder=q/batch/v['phase'];meta=read(folder/v['metadata']);im=Image.open(folder/v['canvas']).convert('RGBA');x11=Image.open(folder/v['screen']).convert('RGBA');assert im.size==x11.size==(1920,1200);assert hashlib.sha256(x11.tobytes()).hexdigest()==meta['canvas_sha256']==meta['presented_sha256'];assert im.tobytes()==x11.tobytes(),v
  frames.append(dict(name=v['name'],png_sha256=sha(folder/v['canvas']),x11_rgba_sha256=meta['presented_sha256']))
 assert model['all_active_offers']==400 and model['all_active_save_bytes']<256*1024
 if a.images:
  pubs=[]
  for name in ['original-shop','eight-hd-lishu','f7-cold-army']:
   v=next(v for v in gui['screens']if v['name']==name);source=q/'gui-r2'/v['phase']/v['canvas'];dest=a.images/('reinforcement-camps-'+name+'-r1.png');assert not dest.exists();im=Image.open(source);im.thumbnail((960,600),Image.Resampling.LANCZOS);im.save(dest);pubs.append(dict(source=str(source.relative_to(r)),source_sha256=sha(source),published=dest.name,published_sha256=sha(dest)))
  with(a.images/'reinforcement-camps-runtime-r1.json').open('x')as f:json.dump(dict(images=pubs,controlled_starting_go_army=True,pregranted_openkb_units=False,memory_injected=False,natural_camp_entry=True,formal_promoted=False),f,ensure_ascii=False,indent=2);f.write('\n')
 old_reader=read(q/'old-reader-r1.json');assert old_reader['status']=='passed-old-reader-v5-refusal-before-DOS'
 result=dict(status='passed-independent-reinforcement-camps',source_tools={n:sha(r/'tools'/n)for n in m.NEW},dependencies=deps,independent_full_world_transitions=4,all_active_offers=400,all_active_save_bytes=model['all_active_save_bytes'],frames=frames,old_reader=old_reader,original_store_preserved=True,guest_pause_checked=True,formal_promoted=False,limits=['Isolated candidate; fixed initial native militia, ordinary camp entry and one wolf purchase.','Balance and natural acquisition of higher recruitment ranks are not covered.','No new complete battle or natural playthrough claim.'])
 with a.out.open('x')as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
if __name__=='__main__':main()
