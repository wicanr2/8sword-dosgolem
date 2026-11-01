#!/usr/bin/env python3
"""Read-only camp inventory and disposable recruitment decision prototype."""
import argparse,base64,gzip,hashlib,importlib.util,io,json,os,struct
from pathlib import Path
from PIL import Image
REL='workplace/probe-20261023/graphics-first/battle-r1/openkb-camp-proposal-r1';BATCH='openkb-camp-proposal-r1'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,d):
    with p.open('x')as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def helper(r):
    s=importlib.util.spec_from_file_location('h',r/'tools/prepare-owned-army-ui.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','audit','publish','archive','verify']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--out',type=Path);p.add_argument('--images',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
    if a.action=='verify':
        d=read(a.archive/(BATCH+'.json'))
        for f in d['files']:
            blob=(a.archive/BATCH/d['objects'][f['sha256']]['file']).read_bytes();assert sha(blob)==d['objects'][f['sha256']]['stored_sha256'];raw=gzip.decompress(blob);assert len(raw)==f['bytes']and sha(raw)==f['sha256']
        write(a.out,dict(status='passed-detached-openkb-camp-proposal',files=len(d['files']),objects=len(d['objects'])));return
    r=a.project;q=r/REL;h=helper(r);deps=h.dependencies(r)
    if a.action=='prepare':
        assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir();(q/'inputs').mkdir();write(q/'baseline.json',deps)
        catalog=h.stored(r,'sword-guards-r1','/inputs/army-catalog.json');native=h.stored(r,'sword-guards-r1','/inputs/original-save.ay');(q/'inputs/army-catalog.json').write_bytes(catalog);(q/'inputs/original-save.ay').write_bytes(native)
        (q/'owned-army-model.go').write_bytes(h.stored(r,'sword-guards-r1','/go-src/tools/owned-army-model.go'))
        profiles=json.loads(catalog)['profiles'];idx={p['id']:p for p in profiles};camps=[]
        for group in range(5):
            for row in range(24):
                words=[]
                for f in range(5):
                    at=2*(18+row*25+f*5+group);words.append((struct.unpack_from('<H',native,at)[0]-at-3)&65535)
                assert words[3]<=25 and words[4]<=32767
                if not words[3]:assert words[4]==0;continue
                unit=f'native:{words[3]:02d}';camps.append(dict(id=f'native-camp:{group:02d}:{row:02d}',group=group,row=row,region=row//3,x=words[1],y=words[2],unit=unit,name=idx[unit]['name'],stock=words[4],gold=idx[unit]['gold'],raw_words=words))
        units=[]
        for u in profiles:
            if not u['id'].startswith('openkb:'):continue
            name=u['id'].split(':')[1];name='trol'if name=='troll'else name;raw=h.stored(r,'sword-guards-r1','/ui-assets/unit-'+name+'.png');im=Image.open(io.BytesIO(raw));im.thumbnail((220,150),Image.Resampling.LANCZOS);b=io.BytesIO();im.save(b,format='PNG');units.append(dict(u,portrait='data:image/png;base64,'+base64.b64encode(b.getvalue()).decode(),portrait_source_sha256=sha(raw)))
        assert len(profiles)==33 and len(units)==8
        data=dict(schema=1,status='DRAFT-gameplay-decision-pending',catalog_sha256=sha(catalog),native_sha256=sha(native),raw_camp_capacity=120,camps=camps,units=units,sample=dict(gold=5000,leadership=1000,used=30,rank=1),stock_policy='Proposal only: floor(native current stock * native price / new unit price); independent pools. Monthly policy still requires the chosen branch spec.',native_modified=False,production_promoted=False)
        write(q/'proposal-data.json',data)
        template=(r/'tools/openkb-camp-proposal.html').read_text();assert template.count('__PROPOSAL_DATA__')==1;(q/'proposal.html').write_text(template.replace('__PROPOSAL_DATA__',json.dumps(data,ensure_ascii=False).replace('</',r'<\/')))
        for n in ['prepare-openkb-camp-proposal.py','openkb-camp-proposal.html','research-openkb-camp-quotes.go','check-openkb-camp-proposal.js']:
            if(r/'tools'/n).exists():(q/n).write_bytes((r/'tools'/n).read_bytes())
        return
    assert deps==read(q/'baseline.json')
    if a.action=='audit':
        d=read(q/'proposal-data.json');c={x['id']:x for x in d['camps']};u={x['id']:x for x in d['units']};g=read(q/'quotes-r1.json');assert g['status']=='passed-disposable-camp-quotes'and len(g['rows'])==len(c)*8*2
        assert sha((q/'inputs/original-save.ay').read_bytes())==d['native_sha256']and sha((q/'inputs/army-catalog.json').read_bytes())==d['catalog_sha256']
        for row in g['rows']:
            camp,unit=c[row['camp']],u[row['unit']];stock=camp['stock']*camp['gold']//unit['gold'];expected=0 if row['rank']<unit['rank']else min(stock,5000//unit['gold'],970//unit['command']);assert row['candidate_stock']==stock and row['maximum']==expected,row
        write(a.out,dict(status='passed-independent-camp-proposal-quotes',camps=len(c),units=8,quotes=len(g['rows']),native_unchanged=True,production_changed=False,decision_pending=True));return
    if a.action=='publish':
        assert read(q/'browser-r1.json')['status']=='passed-camp-proposal-browser'and read(q/'quotes-audit-r1.json')['status']=='passed-independent-camp-proposal-quotes'
        dest=a.images/'openkb-camp-proposal-r1.html';assert not dest.exists();dest.write_bytes((q/'proposal.html').read_bytes());(a.images/'openkb-camp-proposal-data-r1.json').write_bytes((q/'proposal-data.json').read_bytes())
        canvas=Image.new('RGB',(1440,660),'#061f18')
        for i,n in enumerate(['a','b']):im=Image.open(q/('proposal-'+n+'.png'));im=im.resize((720,660),Image.Resampling.LANCZOS);canvas.paste(im,(i*720,0))
        canvas.save(a.images/'openkb-camp-proposal-comparison-r1.png');write(a.images/'openkb-camp-proposal-runtime-r1.json',dict(status='prototype-only-decision-pending',html_sha256=sha(dest.read_bytes()),data_sha256=sha((q/'proposal-data.json').read_bytes()),native_modified=False,formal_promoted=False));return
    folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
    for f in sorted(q.rglob('*')):
        if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
        assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();digest=sha(raw);obj=folder/(digest+'.gz')
        if digest not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[digest]=dict(file=obj.name,stored_sha256=sha(obj.read_bytes()))
        files.append(dict(path=str(f.relative_to(r)),bytes=len(raw),sha256=digest,mode=f.stat().st_mode&0o777))
    write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Original inputs local-only; disposable proposal, no gameplay decision or production change.'))
if __name__=='__main__':main()
