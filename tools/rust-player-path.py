#!/usr/bin/env python3
"""現行Rust正常玩家路徑抽驗、永久保存及還原。限Docker。"""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-player-path-r1';REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
def module(r,n):
    s=importlib.util.spec_from_file_location(n,r/'tools'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','freeze','audit','images','archive','verify','restore'])
    for n in ['project','work','out','archive']:p.add_argument('--'+n,type=Path)
    a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
    r=a.project;q=a.work or r/REL
    if a.action in ['archive','verify','restore']:
        m=module(r,'rust-combat-inventory.py');m.BATCH=BATCH;m.REL=REL;m.main();return
    if a.action=='prepare':
        previous='rust-space-events-r1';h=module(r,'prepare-owned-army-ui.py')
        prefix='workplace/probe-20261023/graphics-first/battle-r1/'+previous+'/'
        count=0
        for f in json.loads((r/'preserved'/f'{previous}.json').read_text())['files']:
            sub=Path(f['path']).relative_to(prefix)
            if str(sub)=='native/8sword-remake'or str(sub).startswith('native/pack/'):
                raw=h.stored(r,previous,f['path']);assert hashlib.sha256(raw).hexdigest()==f['sha256']
                dst=q/sub;dst.parent.mkdir(parents=True,exist_ok=True);assert not dst.exists();dst.write_bytes(raw);dst.chmod(f['mode']);count+=1
        assert count==288;return
    if a.action=='freeze':
        shutil.copytree(r/'internal/remake-rust',q/'rust-source');(q/'tools').mkdir()
        for n in ['rust-player-path.py','rust-player-path-gui.py','rust-native-player.sh']:shutil.copy2(r/'tools'/n,q/'tools'/n)
        return
    h=module(r,'prepare-owned-army-ui.py')
    if a.action in ['audit','images']:
        from PIL import Image,ImageDraw,ImageFont
        import io
        gui=json.loads((q/'native/gui/receipt.json').read_text())
        assert gui['status']=='passed-rust-player-path-gui' and len(gui['runs'])==4
        assert gui['binary_sha256']==sha(q/'native/8sword-remake')
        if a.action=='images':
            audit=json.loads((r/'preserved/rust-player-path-audit-r1.json').read_text())
            idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()))
            font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),28,index=3)
            canvas=Image.new('RGB',(1920,960),(9,36,29));draw=ImageDraw.Draw(canvas);sources=[]
            for i,(run,label,title) in enumerate([('fresh','native-and-openkb-purchased','新遊戲：原營地購入OpenKB女弓箭手'),('camp-cold','battle-saved','自然遇敵：普通出手後保存'),('battle-cold','normal-monthly-saved','正常行走跨月：原式月報'),('month-cold','army-after-month','冷讀月報、回場與原式軍隊管理')]):
                cap=next(v for v in audit['captures'] if v['run']==run and v['label']==label)
                p=q/'native/gui'/run/f"shell-frame-{cap['number']:03}.ppm";assert sha(p)==cap['full_sha256']
                x=i%2*960;y=i//2*480;draw.text((x+12,y+8),title,font=font,fill=(239,216,155))
                canvas.paste(Image.open(p).resize((960,430),Image.Resampling.LANCZOS),(x,y+50));sources.append(cap)
            canvas.save(a.out);a.out.with_suffix('.json').write_text(json.dumps(dict(image_sha256=sha(a.out),binary_sha256=gui['binary_sha256'],scope=gui['scope'],sources=sources),ensure_ascii=False,indent=2)+'\n');return
        previous_audit=json.loads((r/'preserved/rust-space-events-audit-r1.json').read_text())
        assert previous_audit['tests']==212 and previous_audit['gui']['binary_sha256']==gui['binary_sha256']
        assert '存檔格式v18' in(q/'evidence/self-check.log').read_text()
        libraries=(q/'evidence/linux-libraries.txt').read_text();assert 'not found' not in libraries and 'libSDL2' in libraries and 'libsndfile' in libraries
        captures=[];fnv=module(r,'rust-native-player.py').fnv
        for run in gui['runs']:
            assert run['exit']==0
            folder=q/'native/gui'/run['name'];labels={v['number']:v['label'] for v in run['captures']}
            for p in sorted(folder.glob('capture-*.tsv')):
                n=int(p.stem.split('-')[1]);cap=dict(l.split('\t',1)for l in p.read_text().splitlines())
                center=folder/f'frame-{n:03}.ppm';full=folder/f'shell-frame-{n:03}.ppm'
                assert center.read_bytes()==(folder/f'readback-{n:03}.ppm').read_bytes()
                assert full.read_bytes()==(folder/f'shell-readback-{n:03}.ppm').read_bytes()
                im=Image.open(center).convert('RGBA');assert cap['frame_hash']==format(fnv(im.tobytes()),'016x')
                assert Image.open(full).convert('RGB').crop((512,0,2432,1320)).tobytes()==im.convert('RGB').tobytes()
                captures.append(dict(run=run['name'],label=labels.get(n,'automatic'),number=n,captured=cap,central_sha256=sha(center),full_sha256=sha(full)))
        assert sum(c["label"]!="automatic" for c in captures)==14
        cold_pairs=[]
        for left,right,label1,label2 in [('fresh','camp-cold','native-and-openkb-purchased','camp-cold'),('camp-cold','battle-cold','battle-saved','battle-cold'),('battle-cold','month-cold','normal-monthly-saved','monthly-cold')]:
            x=next(c for c in captures if c['run']==left and c['label']==label1);y=next(c for c in captures if c['run']==right and c['label']==label2)
            assert x['captured']['state_hash']==y['captured']['state_hash']
            equal=x['central_sha256']==y['central_sha256']
            if left!='fresh':assert equal
            cold_pairs.append(dict(left=left,right=right,state_hash=x['captured']['state_hash'],central_equal=equal,camp_selection_not_persisted=left=='fresh'))
        previous='rust-combat-inventory-r1';prefix='workplace/probe-20261023/graphics-first/battle-r1/'+previous+'/native/pack/'
        media=[f for f in json.loads((r/'preserved'/f'{previous}.json').read_text())['files'] if f['path'].startswith(prefix)]
        assert len(media)==287 and all(sha(q/'native/pack'/f['path'][len(prefix):])==f['sha256'] for f in media)
        crate={str(p.relative_to(r/'internal/remake-rust')):sha(p) for p in(r/'internal/remake-rust').rglob('*')if p.is_file()}
        assert crate==previous_audit['crate']
        assert all(sha(q/'rust-source'/n)==v for n,v in crate.items())
        baseline={k:len(v)for k,v in h.dependencies(r).items()};assert list(baseline.values())==[197,7,923,535]
        assert gui['fixed_seed']==1 and gui['no_runtime_memory_or_ip_injection']
        assert gui['runs'][0]['final']['army']=='90,1,0,0,0,0' and gui['runs'][0]['final']['gold']=='190'
        assert gui['runs'][-1]['final']['months']=='1'and gui['runs'][-1]['final']['phase']=='world'
        a.out.write_text(json.dumps(dict(status='passed-rust-player-path-audit',inherited_tests=212,unchanged_product_source=True,gui=gui,captures=captures,cold_pairs=cold_pairs,unchanged_media=287,runtime_files=288,crate=crate,baseline=baseline,execution=json.loads((q/'execution.json').read_text()),limits=['Normal seed1 new game from default resources, original camp and OpenKB archer purchase; no gameplay-state fixtures, resource grants, coordinate jumps or forced outcomes.','This is a current native integration sample, not a new DOS oracle or complete natural campaign. Earlier ending and isolated behavior receipts remain bounded inherited evidence.','Camp native/extra tab selection is transient; battle and monthly central cold frames are compared exactly.','Linux scale1 SDL software/dummy audio; no new hardware audio, other-platform or Release acceptance.']),ensure_ascii=False,indent=2)+'\n');return
    raise NotImplementedError(a.action)
if __name__=='__main__':main()
