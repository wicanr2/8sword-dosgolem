#!/usr/bin/env python3
"""非水特殊地點八方向：Docker 內核對及永久保存。"""
import argparse, gzip, hashlib, importlib.util, json, os, shutil, struct, sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-land-shore-r1'
REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
def module(r,n):
    s=importlib.util.spec_from_file_location(n,r/'tools'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','freeze','audit','images','archive','verify','restore'])
    for n in ['project','work','archive','out']:ap.add_argument('--'+n,type=Path)
    a=ap.parse_args();assert Path('/.dockerenv').exists() and os.getuid()==1000
    r=a.project;q=a.work or r/REL;h=module(r,'prepare-owned-army-ui.py')
    if a.action in ['archive','verify','restore']:
        m=module(r,'rust-combat-inventory.py');m.BATCH=BATCH;m.REL=REL;m.main();return
    if a.action=='prepare':
        assert not q.exists() and q.parent.stat().st_uid==1000
        (q/'native/pack').mkdir(parents=True);(q/'evidence').mkdir()
        old='rust-combat-inventory-r1';prefix='workplace/probe-20261023/graphics-first/battle-r1/'+old+'/native/pack/'
        for f in json.loads((r/'preserved'/f'{old}.json').read_text())['files']:
            if f['path'].startswith(prefix):
                p=q/'native/pack'/f['path'][len(prefix):];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(h.stored(r,old,f['path']));p.chmod(f['mode'])
        (q/'native/legacy-v17.chk').write_bytes(h.stored(r,old,'native/gui/world-cold-store/journey.chk'))
        chosen=[];inputs=[]
        for batch,name,want in [('rust-special-shore-r1','ida-shore.json',{0x12446,0x10d72,0x15354,0x13aec}),('rust-guards-r1','ida-guards.json',{0x12dde}),('rust-world-r1','ida-world-movement-r3.json',{0x145fa,0x10b38})]:
            raw=h.stored(r,batch,'evidence/'+name);obj=json.loads(raw)
            inputs.append(dict(batch=batch,name=name,sha256=hashlib.sha256(raw).hexdigest()))
            chosen.extend(f for f in obj['functions'] if f['start'] in want)
        assert len(chosen)==7
        (q/'evidence/ida-land-shore.json').write_text(json.dumps(dict(tool='IDA Pro 9.4 inherited export',source_sha256='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0',database_sha256='a9089db0a8921c732a96f9d4082020f7d3575c98af0925c2c1fb91c3c7ad21ac',address_space='IDA MZ base10000h; runtime CS0110 IP=linear-10000h; DS1E88 offsets separate; file offsets explicit',inputs=inputs,functions=chosen,semantics=[dict(level='confirmed',source='PAM.AY MZ10000 sub_12446 12500..12519',meaning='Shore predicate uses target tile, boat2 and blocked flag; no origin tile constraint'),dict(level='confirmed',source='PAM.AY MZ10000 sub_12446 12566..1258C',meaning='accept clears boat; refusal inverse-moves and marks blocked before target-tile consumers')]),ensure_ascii=False,indent=2)+'\n')
        print('prepared 287 media, true v17 and seven inherited IDA functions');return
    if a.action=='freeze':
        shutil.copytree(r/'internal/remake-rust',q/'rust-source')
        (q/'tools').mkdir()
        for n in ['rust-land-shore.py','rust-land-shore-reference.go','rust-land-shore-gui.py','rust-native-player.sh']:
            shutil.copy2(r/'tools'/n,q/'tools'/n)
        return
    if a.action in ['audit','images']:
        from PIL import Image,ImageDraw,ImageFont
        import io
        gui=json.loads((q/'native/gui/receipt.json').read_text())
        assert gui['status']=='passed-rust-land-shore-gui' and len(gui['runs'])==6
        assert gui['binary_sha256']==sha(q/'native/8sword-remake')
        if a.action=='images':
            audit=json.loads((r/'preserved/rust-land-shore-audit-r1.json').read_text())
            idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()))
            font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),28,index=3)
            canvas=Image.new('RGB',(1920,960),(9,36,29));draw=ImageDraw.Draw(canvas);sources=[]
            for i,(run,label,title) in enumerate([('notice','notice-before-shore','原提示先顯示，再確認上岸'),('notice-cold','accepted-monthly','陸地上岸確認後，正常進月報'),('shop','refused-shop-bridge','拒絕上岸：原式預設造橋店'),('guard-cold','guard-after-landing','接受上岸：回到原守軍確認')]):
                cap=next(v for v in audit['captures'] if v['run']==run and v['label']==label)
                p=q/'native/gui'/run/f"shell-frame-{cap['number']:03}.ppm";assert sha(p)==cap['full_sha256']
                x=i%2*960;y=i//2*480;draw.text((x+12,y+8),title,font=font,fill=(239,216,155))
                canvas.paste(Image.open(p).resize((960,430),Image.Resampling.LANCZOS),(x,y+50));sources.append(cap)
            canvas.save(a.out);a.out.with_suffix('.json').write_text(json.dumps(dict(image_sha256=sha(a.out),binary_sha256=gui['binary_sha256'],scope=gui['scope'],sources=sources),ensure_ascii=False,indent=2)+'\n');return
        assert '207 passed; 0 failed' in(q/'native/tests.log').read_text()
        assert '存檔格式v17' in(q/'native/self-check.log').read_text()
        redata=json.loads((q/'evidence/ida-land-shore.json').read_text());assert len(redata['functions'])==7
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
        raw=(q/'evidence/land-shore-reference.tsv').read_bytes();assert raw==(r/'internal/remake-rust/land-shore-reference.tsv').read_bytes()
        rows=raw.decode().splitlines();assert sum(l.startswith('FLOW\t') for l in rows)==352 and sum(l.startswith('LOOK\t') for l in rows)==28
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
        for left,right,label1,label2 in [('notice','notice-cold','refusal-saved','refusal-cold'),('shop','shop-cold','bridge-purchased-saved','bridge-cold'),('guard','guard-cold','guard-refused-saved','guard-refused-cold')]:
            x=next(c for c in captures if c['run']==left and c['label']==label1);y=next(c for c in captures if c['run']==right and c['label']==label2)
            assert x['captured']['state_hash']==y['captured']['state_hash']
            equal=x['central_sha256']==y['central_sha256']
            if left=='shop':assert x['captured']['message']=='已購入法術' and y['captured']['message']==''
            else:assert equal
            cold_pairs.append(dict(left=left,right=right,state_hash=x['captured']['state_hash'],central_equal=equal,transient_shop_message=left=='shop'))
        previous='rust-combat-inventory-r1';prefix='workplace/probe-20261023/graphics-first/battle-r1/'+previous+'/native/pack/'
        media=[f for f in json.loads((r/'preserved'/f'{previous}.json').read_text())['files'] if f['path'].startswith(prefix)]
        assert len(media)==287 and all(sha(q/'native/pack'/f['path'][len(prefix):])==f['sha256'] for f in media)
        crate={str(p.relative_to(r/'internal/remake-rust')):sha(p) for p in(r/'internal/remake-rust').rglob('*') if p.is_file()}
        assert all(sha(q/'rust-source'/n)==v for n,v in crate.items())
        baseline={k:len(v) for k,v in h.dependencies(r).items()};assert list(baseline.values())==[197,7,923,535]
        def table(name):return [list(map(int,l.split('\t'))) for l in(r/'internal/remake-rust'/name).read_text().splitlines() if l and not l.startswith('#')]
        sites={'shop':[(v[0],v[2],v[3])for v in table('magic-shops.tsv')],
            'guard':[(v[0],v[2],v[3])for v in table('guard-catalog.tsv')]}
        for kind in range(5):sites['camp'+str(kind)]=[(v[2],v[3],v[4])for v in table('camp-catalog.tsv')if v[0]==kind and v[5]>0]
        # A declined directional approach cannot land on a different matching consumer.
        # Space keeps the current coordinate and is deliberately outside this contract.
        adjacency={}
        for name,positions in sites.items():
            pairs=[(a,b)for i,a in enumerate(positions)for b in positions[i+1:]if a[0]==b[0]and min((a[1]-b[1])%70,(b[1]-a[1])%70)<=1 and min((a[2]-b[2])%80,(b[2]-a[2])%80)<=1]
            assert not pairs;adjacency[name]=dict(sites=len(positions),adjacent_matches=0)
        spec=(r/'docs/spec/031-rust-independent-remake.md').read_text();marker='LAND-SHORE-RESOLVED-20261112'
        older=[l for l in spec.splitlines() if '非水特殊點組合' in l and marker in l];assert len(older)>=3
        assert all(marker in(r/f).read_text()for f in ['CONTEXT.md','WORKLOG.md','RESEARCH-LOG.md'])
        a.out.write_text(json.dumps(dict(status='passed-rust-land-shore-audit',tests=207,original_flow_cases=352,original_lookup_cases=28,inherited_ida_functions=7,ida_relocated_lines_verified=checked,gui=gui,captures=captures,cold_pairs=cold_pairs,consumer_adjacency=adjacency,unchanged_media=287,runtime_files=288,crate=crate,baseline=baseline,resolution_backlinks=dict(keys=['DOS/PAM.AY/MZ10000:12446:12500-12519','DOS/PAM.AY/MZ10000:12446:126D6','DOS/PAM.AY/MZ10000:10B38:10BD0'],older_references=len(older),required_marker=marker),execution=json.loads((q/'execution.json').read_text()),limits=['Eight-direction special-site approach only; Space on special sites remains a separate boundary.','Original controlled CPU slice starts at1255E after a supplied answer; UI/draw/loaders and consumer bodies skipped; original rand fixed0, Rust fixtures seed1. Only documented branch/clock/dispatch fields compared, not full RNG sequence or whole-game parity.','GUI initial land coordinates, boat2 and remaining1/2 explicit; subsequent normal input. No natural acquisition or full campaign claim.','Linux scale1/dummy audio; previously verified HD/UI/media retained, no new release/platform/audio listening claim.']),ensure_ascii=False,indent=2)+'\n');return
    raise NotImplementedError(a.action)
if __name__=='__main__':main()
