#!/usr/bin/env python3
"""Extend the preserved monthly candidate with wide arithmetic and Go reports."""
import argparse,gzip,hashlib,importlib.util,io,json,os,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,__version__
REL='workplace/probe-20261023/graphics-first/battle-r1/monthly-wide-r1'
BATCH='monthly-wide-r1'
NEW=['prepare-monthly-wide.py','monthly-wide-ui.go','monthly-wide-checks.go','monthly-wide-ui_test.go','check-monthly-wide.py','check-monthly-wide-ui.py','monthly-wide.sh']
PATCHED=['research-monthly.go','monthly-port.go','monthly-store.go','world-army-review_main.go','probe-monthly-candidate.go']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
    with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def helper(r):
    sp=importlib.util.spec_from_file_location('h',r/'tools/prepare-owned-army-ui.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
def replace(p,a,b):
    s=p.read_text();assert s.count(a)==1,(p,a,s.count(a));p.write_text(s.replace(a,b))
def patch(src):
    p=src/'tools/research-monthly.go';s=p.read_text();start=s.index('\t// This first source-UI slice');end=s.index('\tv.Charged =',start);s=s[:start]+'\tif a.Gold > 30000 || income > 30000 { return v, errors.New("monthly native resource domain") }\n'+s[end:];p.write_text(s)
    p=src/'tools/monthly-port.go';s=p.read_text();start=s.index('\t\t\t\tm.Write16(0x1e880+uint32(r.BP)-8');end=s.index('\t\t\t\tm.CPU.Cycles++',start);s=s[:start]+'\t\t\t\tm.CPU.IP = 0x2803 // Go report owns wide values; no native expense word.\n'+s[end:];p.write_text(s)
    replace(src/'tools/monthly-store.go','eightsword-pair-intent/monthly-1','eightsword-pair-intent/monthly-2')
    replace(src/'tools/world-army-review_main.go','func (g *armyReviewApp) view() string {','func (g *armyReviewApp) view() string {\n if wideMonthlyVisible() {return "monthly"}')
    p=src/'tools/probe-monthly-candidate.go';replace(p,'if which == "large" {','if which == "wide-paid" {w.Army.Gold=30000;w.Progress.Legacy04F6=10000;w.Army.Slots[1].Count=999}\n if which == "wide-income" {w.Army.Gold=30000;w.Progress.Legacy04F6=30000}\n if which == "large" {');replace(p,'[]string{"native", "mixed", "bankrupt"}','[]string{"native", "mixed", "bankrupt", "large", "wide-paid", "wide-income"}')
    s=p.read_text();start=s.index('\t// A budget beyond');end=s.index('\tmcWrite(filepath.Join(*out, "receipt.json")',start);s=s[:start]+'\truleCases:=wideMonthlyRuleChecks(c)\n'+s[end:];s=s.replace('"wide_budget_rejected": true','"wide_budget_supported": true, "rule_cases":ruleCases');p.write_text(s)
def fonts(r,q):
    assert __version__=='11.3.0';m=helper(r);d=read(q/'ui-assets/army-ui-fonts.json');original=json.loads(json.dumps(d));have={g['character']for g in d['glyphs']};text='神州八劍每月收支統計月初金錢月薪收入軍費應付實付現金餘額金錢不足全軍離隊本次軍費免收返回地圖教育部隸書草書';extra=sorted(set(text)-have);height=((len(have)+len(extra)+15)//16)*64;index=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));faces={}
    for id,h in m.FONT_SHA.items():
        raw=gzip.decompress((r/'preserved'/index['objects'][h]['path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==h;faces[id]=ImageFont.truetype(io.BytesIO(raw),48,index=3 if id in['noto','serif']else 0)
    old_count=len(d['glyphs'])
    for i,c in enumerate(extra,old_count):d['glyphs'].append(dict(character=c,cell=[i%16*64,i//16*64,64,64]))
    for profile in d['profiles']:
        id=profile['id'];file=q/'ui-assets'/profile['file'];old=Image.open(file);atlas=Image.new('RGBA',(1024,height));atlas.paste(old);face=faces[id];missing=face.getmask('\U0010ffff');missing=(missing.size,bytes(missing));fallbacks=profile['fallback_characters']
        for i,c in enumerate(extra,old_count):
            mask=face.getmask(c);primary=id=='noto'or((mask.size,bytes(mask))!=missing and bool(mask.getbbox()));selected=face if primary else faces['serif']if id=='lishu'else faces['noto'];fallbacks+=c if not primary else'';box=selected.getbbox(c);ink=Image.new('RGBA',(box[2]-box[0],box[3]-box[1]));ImageDraw.Draw(ink).text((-box[0],-box[1]),c,font=selected,fill='white');ink.thumbnail((48,52),Image.Resampling.LANCZOS);atlas.paste(ink,(i%16*64+(64-ink.width)//2,i//16*64+(64-ink.height)//2))
        # Preserve every existing glyph, including partially occupied last rows.
        for g in original['glyphs']:
            x,y,w,h=g['cell'];assert old.crop((x,y,x+w,y+h)).tobytes()==atlas.crop((x,y,x+w,y+h)).tobytes()
        atlas.save(file);profile.update(sha=sha(file),height=height,fallbacks=len(fallbacks),fallback_characters=fallbacks)
    (q/'ui-assets/army-ui-fonts.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');write(q/'font-additions-r1.json',dict(prior_glyphs=old_count,added=extra,pillow=__version__,source_hashes=m.FONT_SHA,old_cells_unchanged=True))
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','freeze','archive','verify','publish']);p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--images',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
    if a.action=='verify':
        d=read(a.archive/(BATCH+'.json'))
        for f in d['files']:
            obj=d['objects'][f['sha256']];p=a.archive/BATCH/obj['file'];assert sha(p)==obj['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
        write(a.out,dict(status='passed-detached-monthly-wide',files=len(d['files']),objects=len(d['objects'])));return
    r=a.project;q=r/REL;m=helper(r);deps=m.dependencies(r)
    if a.action=='prepare':
        assert not q.exists()and q.parent.stat().st_uid==1000;q.mkdir();d=read(r/'preserved/monthly-r1.json')
        for f in d['files']:
            rel=f['path'].split('/monthly-r1/',1)[1]
            if not(rel.startswith(('go-src/','inputs/','ui-assets/'))or rel in['probe.mod','probe.sum','xcheck','monthly-execution-r1.json']):continue
            t=q/rel;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(m.stored(r,'monthly-r1','/monthly-r1/'+rel));t.chmod(f['mode'])
        write(q/'baseline.json',deps);fonts(r,q)
    else:assert deps==read(q/'baseline.json')
    if a.action in['prepare','freeze']:
        if a.action=='freeze':
            for n in PATCHED:(q/'go-src/tools'/n).write_bytes(m.stored(r,'monthly-r1','/monthly-r1/go-src/tools/'+n))
        patch(q/'go-src')
        for n in NEW:
            if(r/'tools'/n).exists():shutil.copyfile(r/'tools'/n,q/'go-src/tools'/n)
        e=read(q/'monthly-execution-r1.json');e.pop('original_build');e.pop('previous_ui');e['ui_build']=e['ui_build'].replace('/out/monthly-ui','/out/monthly-wide-ui')+' tools/monthly-wide-ui.go';e['fixture_build']=e['ui_build'].replace('/out/monthly-wide-ui','/out/monthly-wide-ui-fixture')+' tools/monthly-fixture.go';e['candidate_build']=e['candidate_build'].replace('/out/monthly-candidate','/out/monthly-wide-candidate')+' tools/monthly-wide-checks.go';e['ui_test']=e['ui_build'].replace('go build','go test').replace('-o /out/monthly-wide-ui ','')+' tools/monthly-wide-ui_test.go -run ^TestWideMonthly';(q/'monthly-wide-execution-r1.json').write_text(json.dumps(e,indent=2)+'\n');return
    if a.action=='publish':
        g=read(q/'gui-r1/receipt.json');row=g['screens'][0];source=q/'gui-r1'/row['phase']/row['canvas'];dest=a.images/'monthly-go-wide-report-r1.png';assert not dest.exists();im=Image.open(source);im.thumbnail((960,600),Image.Resampling.LANCZOS);im.save(dest);write(a.images/'monthly-go-wide-report-r1.json',dict(source=str(source.relative_to(r)),source_sha256=sha(source),published_sha256=sha(dest),controlled_countdown=True,controlled_initial_army=True,budget=g['report']['monthly']['budget'],production_promoted=False));return
    folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
    for f in sorted(q.rglob('*')):
        if not f.is_file()or'build-cache'in f.relative_to(q).parts:continue
        assert f.stat().st_uid==1000 and not f.is_symlink();raw=f.read_bytes();h=hashlib.sha256(raw).hexdigest();obj=folder/(h+'.gz')
        if h not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[h]=dict(file=obj.name,stored_sha256=sha(obj))
        files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(raw),mode=f.stat().st_mode&0o777))
    write(a.out,dict(files=files,objects=objects,dependencies=deps,rights='Original inputs, VM objects and full frames local-only; no production promotion.'))
if __name__=='__main__':main()
