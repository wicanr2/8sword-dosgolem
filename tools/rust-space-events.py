#!/usr/bin/env python3
"""Space事件：準備、核對、永久保存及還原。只在Docker執行。"""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-space-events-r1';REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
def module(r,n):
    s=importlib.util.spec_from_file_location(n,r/'tools'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','freeze','audit','images','archive','verify','restore'])
    for n in ['project','work','out','archive']:p.add_argument('--'+n,type=Path)
    a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
    r=a.project;q=a.work or r/REL;h=module(r,'prepare-owned-army-ui.py')
    if a.action in ['archive','verify','restore']:
        m=module(r,'rust-combat-inventory.py');m.BATCH=BATCH;m.REL=REL;m.main();return
    if a.action=='prepare':
        assert not q.exists()and q.parent.stat().st_uid==1000
        (q/'native/pack').mkdir(parents=True);(q/'evidence').mkdir()
        previous='rust-land-shore-r1';prefix='workplace/probe-20261023/graphics-first/battle-r1/'+previous+'/native/pack/'
        for f in json.loads((r/'preserved'/f'{previous}.json').read_text())['files']:
            if f['path'].startswith(prefix):
                p=q/'native/pack'/f['path'][len(prefix):];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(h.stored(r,previous,f['path']));p.chmod(f['mode'])
        (q/'native/legacy-v17.chk').write_bytes(h.stored(r,previous,'native/gui/shop-cold-store/journey.chk'))
        evidence=json.loads(h.stored(r,previous,'evidence/ida-land-shore.json'))
        raw=h.stored(r,'rust-world-r1','evidence/ida-world-movement-r2.json');old=json.loads(raw)
        evidence['functions'].extend(f for f in old['functions']if f['start']in [0x10bdc,0x10c32])
        evidence['inputs'].append(dict(batch='rust-world-r1',name='ida-world-movement-r2.json',sha256=hashlib.sha256(raw).hexdigest()))
        assert len(evidence['functions'])==9
        evidence['semantics'].append(dict(level='confirmed',source='PAM.AY MZ10000:10C0C,126D6..126DF,12DDE',meaning='Space precredits a step; blocked skips final debit; same coordinates reach existing consumers, including guard prompt without boat gate'))
        (q/'evidence/ida-space-events.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n');return
    if a.action=='freeze':
        shutil.copytree(r/'internal/remake-rust',q/'rust-source');(q/'tools').mkdir()
        for n in ['rust-space-events.py','rust-space-events-reference.go','rust-space-events-gui.py','rust-native-player.sh']:shutil.copy2(r/'tools'/n,q/'tools'/n)
        return
    if a.action in ['audit','images']:
        from PIL import Image,ImageDraw,ImageFont
        import io
        gui=json.loads((q/'native/gui/receipt.json').read_text())
        assert gui['status']=='passed-rust-space-events-gui' and len(gui['runs'])==6
        assert gui['binary_sha256']==sha(q/'native/8sword-remake')
        if a.action=='images':
            audit=json.loads((r/'preserved/rust-space-events-audit-r1.json').read_text())
            idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()))
            font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),28,index=3)
            canvas=Image.new('RGB',(1920,960),(9,36,29));draw=ImageDraw.Draw(canvas);sources=[]
            for i,(run,label,title) in enumerate([('shop','same-site-fireball','原地Space：拒絕後仍賣火球'),('camp','same-site-camp','原地Space：同地募兵'),('guard','battle-saved','拒絕上岸仍可確認攻城／F7'),('guard-cold','guard-return-once','戰中冷讀、撤退回場：只結算一次')]):
                cap=next(v for v in audit['captures'] if v['run']==run and v['label']==label)
                p=q/'native/gui'/run/f"shell-frame-{cap['number']:03}.ppm";assert sha(p)==cap['full_sha256']
                x=i%2*960;y=i//2*480;draw.text((x+12,y+8),title,font=font,fill=(239,216,155))
                canvas.paste(Image.open(p).resize((960,430),Image.Resampling.LANCZOS),(x,y+50));sources.append(cap)
            canvas.save(a.out);a.out.with_suffix('.json').write_text(json.dumps(dict(image_sha256=sha(a.out),binary_sha256=gui['binary_sha256'],scope=gui['scope'],sources=sources),ensure_ascii=False,indent=2)+'\n');return
        assert '212 passed; 0 failed' in(q/'native/tests.log').read_text()
        assert '存檔格式v18' in(q/'native/self-check.log').read_text()
        redata=json.loads((q/'evidence/ida-space-events.json').read_text());assert len(redata['functions'])==9
        pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes()
        assert hashlib.sha256(pam).hexdigest()==redata['source_sha256']
        assert sha(r/'workplace/probe-20261023/text-first/PAM.i64')==redata['database_sha256']
        word=lambda at:struct.unpack_from('<H',pam,at)[0];header=word(8)*16
        relocs=[header+word(word(24)+i*4+2)*16+word(word(24)+i*4) for i in range(word(6))];checked=0
        for fun in redata['functions']:
            for v in fun['lines']:
                at=v.get('file_offset',v.get('original_file_offset'));want=bytes.fromhex(v['bytes']);assert at==v['ida_linear']-0x10000+header
                raw=bytearray(pam[at:at+len(want)])
                for off in relocs:
                    if at<=off and off+2<=at+len(want):struct.pack_into('<H',raw,off-at,(struct.unpack_from('<H',raw,off-at)[0]+0x1000)&65535)
                assert bytes(raw)==want;checked+=1
        raw=(q/'evidence/space-events-reference.tsv').read_bytes();assert raw==(r/'internal/remake-rust/space-events-reference.tsv').read_bytes()
        rows=raw.decode().splitlines();assert sum(l.startswith('SPACE\t') for l in rows)==132 and sum(l.startswith('GUARD\t') for l in rows)==16 and sum(l.startswith('LOOK\t') for l in rows)==28
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
        assert len(captures)==15
        cold_pairs=[]
        for left,right,label1,label2 in [('shop','shop-cold','purchase-saved','purchase-cold'),('camp','camp-cold','camp-saved','camp-cold'),('guard','guard-cold','battle-saved','battle-cold')]:
            x=next(c for c in captures if c['run']==left and c['label']==label1);y=next(c for c in captures if c['run']==right and c['label']==label2)
            assert x['captured']['state_hash']==y['captured']['state_hash']
            equal=x['central_sha256']==y['central_sha256']
            if left in ['shop','camp']:assert y['captured']['message']==''
            else:assert equal
            cold_pairs.append(dict(left=left,right=right,state_hash=x['captured']['state_hash'],central_equal=equal,transient_purchase_message=left in ['shop','camp']))
        previous='rust-combat-inventory-r1';prefix='workplace/probe-20261023/graphics-first/battle-r1/'+previous+'/native/pack/'
        media=[f for f in json.loads((r/'preserved'/f'{previous}.json').read_text())['files'] if f['path'].startswith(prefix)]
        assert len(media)==287 and all(sha(q/'native/pack'/f['path'][len(prefix):])==f['sha256'] for f in media)
        crate={str(p.relative_to(r/'internal/remake-rust')):sha(p) for p in(r/'internal/remake-rust').rglob('*') if p.is_file()}
        assert all(sha(q/'rust-source'/n)==v for n,v in crate.items())
        baseline={k:len(v) for k,v in h.dependencies(r).items()};assert list(baseline.values())==[197,7,923,535]
        spec=(r/'docs/spec/031-rust-independent-remake.md').read_text();marker='SPACE-EVENTS-RESOLVED-20261112'
        older=[l for l in spec.splitlines() if marker in l];assert len(older)>=6
        assert 'SPACE-CLOCK-CORRECTION-20261112' in spec
        assert all(marker in(r/f).read_text()for f in ['CONTEXT.md','WORKLOG.md','RESEARCH-LOG.md'])
        a.out.write_text(json.dumps(dict(status='passed-rust-space-events-audit',tests=212,original_space_cases=132,original_guard_cases=16,original_lookup_cases=28,inherited_ida_functions=9,ida_relocated_lines_verified=checked,gui=gui,captures=captures,cold_pairs=cold_pairs,unchanged_media=287,runtime_files=288,crate=crate,baseline=baseline,resolution_backlinks=dict(keys=['DOS/PAM.AY/MZ10000:10BDC:10C0C','DOS/PAM.AY/MZ10000:12446:126D6-126DF','DOS/PAM.AY/MZ10000:12DDE'],older_references=len(older),required_marker=marker),execution=json.loads((q/'execution.json').read_text()),limits=['Original controlled CPU executes Space input and dispatch slices; supplied shore answer, skipped draw/UI/loaders/consumer bodies, rand fixed0. Only clock/boat/dispatch and guard prompt fields compared, not full RNG sequence or whole-game parity.','True v17 GUI input explicitly relocates to original sites, boat2, facing3, remaining1, seed1; existing resources and army unchanged. No natural acquisition or campaign completion claim.','Native v18 adds one wait-transaction byte; v1..17 read with no inferred transaction. u16 overflow refuses atomically instead of DOS word wrap.','Linux scale1/dummy audio. Earlier HD/media/UI verification retained; no new platform/audio listening or Release claim.']),ensure_ascii=False,indent=2)+'\n');return
    raise NotImplementedError(a.action)
if __name__=='__main__':main()
