#!/usr/bin/env python3
"""056：交付核對與內容定址永久保存；不保存建置快取或 Wine prefix。"""
import argparse, gzip, hashlib, importlib.util, io, json, os, re, shutil, sys, tarfile
from pathlib import Path
sys.dont_write_bytecode=True
from rust_package_settings import BATCH, REL, VERSION, AUDIT
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','audit','images','archive','verify','restore','restore-native'])
    p.add_argument('--project',type=Path,required=True);p.add_argument('--out',type=Path);a=p.parse_args()
    assert Path('/.dockerenv').exists()and os.getuid()==1000
    r=a.project;q=r/REL;index=r/'preserved'/f'{BATCH}.json';archive=r/'preserved'/BATCH
    if a.action=='restore-native':
        data=json.loads(index.read_text());entry=next(f for f in data['files']if f['path'].endswith('-linux-x86_64.tar.gz'))
        obj=data['objects'][entry['sha256']];blob=(archive/obj['file']).read_bytes();assert hashlib.sha256(blob).hexdigest()==obj['stored_sha256']
        raw=gzip.decompress(blob);assert hashlib.sha256(raw).hexdigest()==entry['sha256'];count=0
        with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz')as t:
            for member in t:
                parts=Path(member.name).parts
                if not member.isfile()or len(parts)<2:continue
                rel=Path(*parts[1:]);assert '..'not in rel.parts
                if str(rel)!='8sword-remake'and rel.parts[0]!='pack':continue
                content=t.extractfile(member).read();dst=q/'native'/rel;dst.parent.mkdir(parents=True,exist_ok=True)
                if dst.exists():assert dst.read_bytes()==content
                else:dst.write_bytes(content);dst.chmod(member.mode&0o777)
                count+=1
        assert count==288;print('288 current native runtime files restored');return
    if a.action=='prepare':
        q.mkdir(parents=True,exist_ok=True)
        for d in ['sources','deps','build','logs','stage','smoke','smoke/x11','smoke/windows']:(q/d).mkdir(exist_ok=True)
        previous=json.loads((r/'preserved/rust-player-path-r1.json').read_text())
        prefix='workplace/probe-20261023/graphics-first/battle-r1/rust-player-path-r1/native/pack/'
        for f in previous['files']:
            if not f['path'].startswith(prefix):continue
            obj=previous['objects'][f['sha256']];raw=gzip.decompress((r/'preserved/rust-player-path-r1'/obj['file']).read_bytes());assert hashlib.sha256(raw).hexdigest()==f['sha256']
            dst=r/f['path'];dst.parent.mkdir(parents=True,exist_ok=True)
            if dst.exists():assert sha(dst)==f['sha256']
            else:dst.write_bytes(raw);dst.chmod(f['mode'])
        source_batch=BATCH if index.exists() else 'rust-package-r1'
        source_index=r/'preserved'/f'{source_batch}.json'
        if source_index.exists():
            data=json.loads(source_index.read_text())
            source_rel='workplace/probe-20261023/graphics-first/battle-r1/'+source_batch
            for f in data['files']:
                if not f['path'].startswith(source_rel+'/sources/')or len(Path(f['path']).relative_to(source_rel+'/sources').parts)!=1:continue
                obj=data['objects'][f['sha256']];raw=gzip.decompress((r/'preserved'/source_batch/obj['file']).read_bytes());assert hashlib.sha256(raw).hexdigest()==f['sha256']
                dst=q/'sources'/Path(f['path']).name
                if dst.exists():assert sha(dst)==f['sha256']
                else:dst.write_bytes(raw)
        print('287 media restored; build directories and pinned source downloads prepared.');return
    if a.action in ['verify','restore']:
        data=json.loads(index.read_text());objects={}
        for f in data['files']:
            if f['sha256']not in objects:
                o=data['objects'][f['sha256']];blob=(archive/o['file']).read_bytes();assert hashlib.sha256(blob).hexdigest()==o['stored_sha256']
                raw=gzip.decompress(blob);assert hashlib.sha256(raw).hexdigest()==f['sha256'];objects[f['sha256']]=raw
            raw=objects[f['sha256']];assert len(raw)==f['bytes']
            if a.action=='restore' and f['path'].startswith('dist-all/'):
                out=a.out or r;dst=out/f['path'];dst.parent.mkdir(parents=True,exist_ok=True)
                if dst.exists():assert sha(dst)==f['sha256']
                else:dst.write_bytes(raw);dst.chmod(f['mode'])
        print(json.dumps(dict(status='passed-package-preservation-'+a.action,files=len(data['files']),objects=len(objects))))
        return
    if a.action=='archive':
        archive.mkdir(exist_ok=True);prior=json.loads(index.read_text())if index.exists()else dict(files=[],objects={})
        filemap={f['path']:f for f in prior['files']};objects=prior['objects'];paths=[]
        paths+=list((r/'dist-all'/VERSION/'full-local').rglob('*'))
        paths+=list((r/'dist-all'/VERSION/'promo').rglob('*'))
        paths+=list((r/'dist-all'/VERSION/'smoke').rglob('*'))
        paths+=[r/'dist-all'/VERSION/'SHA256SUMS.json']
        paths+=list((q/'logs').rglob('*'))
        paths+=list((q/'evidence').rglob('*'))
        paths+=list((q/'frozen-source').rglob('*'))
        paths+=list((q/'frozen-tools').rglob('*'))
        paths+=[v for v in(q/'sources').iterdir()if v.is_file()]
        paths+=[q/'package-records.json',q/'execution.json',q/'cleanup-plan.json',q/'cleanup.json',q/'media-overlay.json']
        for name in ['linux','windows']:
            paths+=list((q/'smoke'/name).rglob('*'))
        for path in sorted(set(paths)):
            if not path.is_file():continue
            assert path.stat().st_uid==1000 and not path.is_symlink()
            raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest();obj=archive/(digest+'.gz')
            if digest not in objects:
                if obj.exists():assert gzip.decompress(obj.read_bytes())==raw
                else:obj.write_bytes(gzip.compress(raw,6,mtime=0))
                objects[digest]=dict(file=obj.name,stored_sha256=sha(obj))
            entry=dict(path=str(path.relative_to(r)),sha256=digest,bytes=len(raw),mode=path.stat().st_mode&0o777)
            if entry['path']in filemap:assert filemap[entry['path']]==entry,entry['path']
            filemap[entry['path']]=entry
        files=[filemap[k]for k in sorted(filemap)]
        write(index,dict(version=VERSION,files=files,objects=objects,rights='Full original-derived local packages and captures stay local; no public Release.',excludes=['Cargo target','dependency build/install intermediates','Wine prefix','duplicate extracted packages','staging trees','private X11 sockets']))
        print(json.dumps(dict(files=len(files),objects=len(objects),stored_bytes=sum(p.stat().st_size for p in archive.glob('*.gz')))))
        return
    if a.action=='images':
        from PIL import Image,ImageDraw,ImageFont
        catalog=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));digest='3cffb10242b4b7e6edd439ebf3bd7e392345525e093ea08149e0a0158a1b5151'
        font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/catalog['objects'][digest]['path']).read_bytes())),28,index=3)
        im=Image.new('RGB',(1920,960),(9,36,29));draw=ImageDraw.Draw(im);sources=[]
        chosen=[('linux','fresh','new-world-hd','Linux：正常新遊戲'),('windows','fresh','lishu-world','Windows／Wine：教育部隸書'),('linux','fresh','original-world','Linux：原圖模式'),('windows','cold','cold-world','Windows／Wine：重啟續玩')]
        if (q/'media-overlay.json').exists():
            chosen[0]=('linux','fresh','corrected-story-background','Linux：深藍故事背景頭頸修正')
            chosen[1]=('windows','fresh','new-world-hd','Windows／Wine：修正版龍虎海報')
        for i,(platform,run,label,title)in enumerate(chosen):
            receipt=json.loads((q/'smoke'/platform/'receipt.json').read_text());rr=next(v for v in receipt['runs']if v['name']==run);cap=next(c for c in rr['captures']if c['label']==label)
            source=q/'smoke'/platform/run/f"shell-frame-{cap['number']:03}.ppm";x=i%2*960;y=i//2*480
            draw.text((x+12,y+8),title,font=font,fill=(239,216,155));im.paste(Image.open(source).resize((960,430),Image.Resampling.LANCZOS),(x,y+50));sources.append(dict(platform=platform,run=run,label=label,sha256=sha(source),package_sha256=receipt['package_sha256']))
        im.save(a.out);write(a.out.with_suffix('.json'),dict(image_sha256=sha(a.out),sources=sources,limits='Actual extracted Linux and Windows/Wine packages; no macOS execution image.'))
        return
    records=json.loads((q/'package-records.json').read_text());assert records['version']==VERSION and len(records['packages'])==3
    tests=(q/'logs/linux-test.log').read_text();assert '214 passed; 0 failed'in tests
    receipts={name:json.loads((q/'smoke'/name/'receipt.json').read_text())for name in ['linux','windows']}
    for name,receipt in receipts.items():
        assert receipt['status']=='passed-extracted-package-gui'and len(receipt['runs'])==2
        assert all(v['exit']==0 for v in receipt['runs'])
        fresh,cold=receipt['runs'];assert fresh['final']['state_hash']==cold['final']['state_hash']
        assert all(int(v['final']['queued_bytes'])>0 for v in receipt['runs'])
    saves=[q/'smoke/linux/home/.local/share/8sword-remake/journey.chk',*list((q/'smoke/windows-prefix/drive_c/users').glob('*/AppData/Local/8sword-remake/journey.chk'))]
    assert len(saves)==2 and all(p.read_bytes()[:8]==b'8SJRN018'for p in saves)
    saved_checkpoints=[]
    for name,source in zip(['linux','windows'],saves):
        dest=q/'smoke'/name/'saved-default';dest.mkdir(exist_ok=True)
        for source_file in source.parent.iterdir():
            if source_file.is_file():shutil.copy2(source_file,dest/source_file.name)
        saved_checkpoints.append(dict(platform=name,default_path=str(source.relative_to(q)),sha256=sha(source),bytes=source.stat().st_size))
    wt=list((q/'smoke/windows').glob('eightsword_remake-*.log'));assert len(wt)==1
    win_tests=re.search(r'test result: ok\. (\d+) passed; 0 failed',wt[0].read_text());assert win_tests
    assert(q/'smoke/windows/version.txt').read_text().strip()==VERSION
    mac=json.loads((q/'logs/macos-sign-verify.log').read_text());assert mac['status']=='passed-static-adhoc-pages-and-resources'and mac['resources']==287
    for record in records['packages']:
        archive_path=r/'dist-all'/VERSION/record['path'];assert sha(archive_path)==record['sha256']
        root=q/Path(record['extracted']).relative_to('/q');manifest=json.loads((root/'manifest.json').read_text());assert manifest['version']==VERSION
        for f in manifest['files']:
            p=root/f['path'];assert sha(p)==f['sha256']and p.stat().st_mode&0o777==f['mode']
        assert not any(p.name in ['journey.chk','battle.chk']for p in root.rglob('*'))
        record['extracted_files_verified']=len(manifest['files'])
    spec=importlib.util.spec_from_file_location('owned',r/'tools/prepare-owned-army-ui.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
    baseline={k:len(v)for k,v in h.dependencies(r).items()};assert list(baseline.values())==[197,7,923,535]
    out=r/'dist-all'/VERSION/'smoke'
    for name,receipt in receipts.items():write(out/(name+'-receipt.json'),receipt)
    shutil.copy2(q/'logs/macos-sign-verify.log',out/'macos-static-signatures.json')
    for name in ['linux-test.log','linux-self-check.log','windows-build.log','windows-test-build.log','mac-x86_64-build.log','mac-arm64-build.log']:
        shutil.copy2(q/'logs'/name,out/name)
    shutil.copy2(wt[0],out/'windows-test.log');shutil.copy2(q/'smoke/windows/version.txt',out/'windows-version.txt')
    audit=dict(status='passed-three-platform-local-package-audit',version=VERSION,linux_tests=214,windows_wine_tests=int(win_tests[1]),packages=records['packages'],unchanged_media_per_package=287,gui=receipts,macos_static=mac,baseline=baseline,execution=json.loads((q/'execution.json').read_text()),limits=['macOS universal2 cross-built; architecture, dependency closure, CodeDirectory pages and bundle resources checked; no Apple codesign/Gatekeeper, notarization or native Mac acceptance.','Windows GUI and tests ran under Wine9, not a native Windows machine.','SDL dummy audio confirms decoding and queued nonzero buffers, not human listening or physical audio devices.','Representative normal new-game/save/restart path only; previous bounded battle/ending evidence retained, not a new natural complete campaign or live DOS parity.','Full original-derived art/music and original assets remain local. No tag or public Release.'])
    audit['saved_checkpoints']=saved_checkpoints
    if (q/'media-overlay.json').exists():
        overlay=json.loads((q/'media-overlay.json').read_text());audit['art_corrections']=overlay;audit['unchanged_media_per_package']=285
        prefix='workplace/probe-20261023/graphics-first/battle-r1/rust-player-path-r1/native/pack/'
        base=[f for f in json.loads((r/'preserved/rust-player-path-r1.json').read_text())['files']if f['path'].startswith(prefix)]
        overrides={f['name']:f['sha256']for f in overlay['files']}
        for record in records['packages']:
            root=q/Path(record['extracted']).relative_to('/q');pack=root/('8sword.app/Contents/Resources/pack'if'macos'in record['path']else'pack')
            assert all(sha(pack/f['path'][len(prefix):])==overrides.get(f['path'][len(prefix):],f['sha256'])for f in base)
        audit['intro_reference_diff']=json.loads((q/'evidence/intro-reference-diff.json').read_text())
        assert audit['intro_reference_diff']['unchanged']==42 and len(audit['intro_reference_diff']['changed'])==30
        previous=json.loads((r/'preserved/rust-package-audit-r1.json').read_text())
        comparisons=[]
        for platform,receipt in receipts.items():
            cap=next(c for c in receipt['runs'][0]['captures']if c['label']=='corrected-story-background')
            src=q/'smoke'/platform/'fresh'/f"shell-frame-{cap['number']:03}.ppm";shutil.copy2(src,out/f'{platform}-corrected-story.ppm')
            old=next(c for c in previous['gui'][platform]['runs'][0]['captures']if c['label']=='saved-world')
            new=next(c for c in receipt['runs'][0]['captures']if c['label']=='saved-world')
            assert old['central_sha256']==new['central_sha256'] and old['state']['state_hash']==new['state']['state_hash']
            comparisons.append(dict(platform=platform,state_hash=new['state']['state_hash'],central_sha256=new['central_sha256'],same_state_previous_world_central_equal=True))
        audit['previous_world_comparison']=comparisons
    write(r/'preserved'/AUDIT,audit);write(out/'audit.json',audit)
    for name,receipt in receipts.items():
        for run in receipt['runs']:
            cap=run['captures'][-1];src=q/'smoke'/name/run['name']/f"shell-frame-{cap['number']:03}.ppm";shutil.copy2(src,out/f"{name}-{run['name']}.ppm")
    manifest=r/'dist-all'/VERSION/'SHA256SUMS.json';current=json.loads(manifest.read_text());current['files']=[f for f in current['files']if not f['path'].startswith('smoke/')]+[dict(path=str(p.relative_to(out.parent)),sha256=sha(p),bytes=p.stat().st_size)for p in sorted(out.rglob('*'))if p.is_file()]
    assert all(sha(out.parent/f['path'])==f['sha256']for f in current['files']);write(manifest,current)
    print(json.dumps(dict(status=audit['status'],packages=3,linux_tests=214,windows_tests=int(win_tests[1]))))

if __name__=='__main__':main()
