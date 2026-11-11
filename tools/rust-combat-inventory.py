#!/usr/bin/env python3
"""Rust 旅程戰鬥法術庫存：Docker 內準備、核對、保存與還原。"""
import argparse, gzip, hashlib, importlib.util, json, os, shutil, struct, sys
from pathlib import Path
sys.dont_write_bytecode = True
BATCH = 'rust-combat-inventory-r1'
REL = 'workplace/probe-20261023/graphics-first/battle-r1/' + BATCH
def module(r, name):
    s = importlib.util.spec_from_file_location(name, r/'tools'/name)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['prepare', 'freeze', 'archive', 'verify', 'restore', 'audit', 'images'])
    for n in ['project', 'work', 'out', 'archive']: p.add_argument('--'+n, type=Path)
    a = p.parse_args(); assert Path('/.dockerenv').exists() and os.getuid() == 1000
    r = a.project; q = a.work or r/REL
    if a.action == 'verify':
        m = module(r, 'rust-world-exits.py'); m.BATCH = BATCH; m.REL = REL; m.main(); return
    if a.action == 'archive':
        # Content-addressed local objects are immutable. An unpublished index may be rebuilt.
        folder=a.archive/BATCH; folder.mkdir(exist_ok=True); files=[]; objects={}
        for path in sorted(q.rglob('*')):
            if not path.is_file() or any(n in path.relative_to(q).parts for n in ['rust-target','go-cache','detached']): continue
            assert path.stat().st_uid==1000 and not path.is_symlink()
            raw=path.read_bytes(); digest=hashlib.sha256(raw).hexdigest(); obj=folder/(digest+'.gz')
            if digest not in objects:
                if obj.exists(): assert gzip.decompress(obj.read_bytes())==raw
                else: obj.write_bytes(gzip.compress(raw,6,mtime=0))
                objects[digest]=dict(file=obj.name,stored_sha256=sha(obj))
            files.append(dict(path=str(Path(REL)/path.relative_to(q)),sha256=digest,bytes=len(raw),mode=path.stat().st_mode&0o777))
        a.out.write_text(json.dumps(dict(files=files,objects=objects,rights='Full original-derived assets and binary local only; no Release'),ensure_ascii=False,indent=2)+'\n'); return
    h = module(r, 'prepare-owned-army-ui.py')
    if a.action == 'restore':
        for f in json.loads((r/'preserved'/f'{BATCH}.json').read_text())['files']:
            rel = Path(f['path']).relative_to(REL)
            if str(rel) == 'native/8sword-remake' or str(rel).startswith('native/pack/'):
                dst = q/rel; dst.parent.mkdir(parents=True, exist_ok=True)
                raw = h.stored(r, BATCH, f['path'])
                if dst.exists() and dst.read_bytes() != raw: raise ValueError('目的地已有不同資料')
                dst.write_bytes(raw); dst.chmod(f['mode'])
        return
    if a.action == 'freeze':
        shutil.copytree(r/'internal/remake-rust', q/'rust-source')
        (q/'tools').mkdir()
        for name in ['rust-combat-inventory.py', 'rust-combat-inventory-gui.py', 'rust-native-player.sh']:
            shutil.copy2(r/'tools'/name, q/'tools'/name)
        return
    if a.action in ['audit', 'images']:
        from PIL import Image, ImageDraw, ImageFont
        import io
        gui = json.loads((q/'native/gui/receipt.json').read_text())
        assert gui['status'] == 'passed-rust-combat-inventory-gui' and len(gui['runs']) == 6
        assert gui['binary_sha256'] == sha(q/'native/8sword-remake')
        if a.action == 'images':
            audit = json.loads((r/'preserved/rust-combat-inventory-audit-r1.json').read_text())
            chosen = [('shop','purchased-two','原火球店：買入兩次'),('shop-cold','inventory-two','F4兩欄持有次數'),
                ('shop-cold','spell-menu','原式戰場：選擇法術'),('spell-cold','target-cold','選敵途中保存與冷讀'),
                ('world-cold','inventory-one-cold','施法回場：冷讀剩一次'),('guard-cold','guard-world','守軍複製術：回場60民兵')]
            idx = json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()))
            font_raw = gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())
            font = ImageFont.truetype(io.BytesIO(font_raw), 28, index=3)
            canvas = Image.new('RGB',(1920,1440),(9,36,29)); draw=ImageDraw.Draw(canvas); sources=[]
            for i,(run,label,title) in enumerate(chosen):
                cap=next(c for c in audit['captures'] if c['run']==run and c['label']==label)
                src=q/'native/gui'/run/f"shell-frame-{cap['number']:03}.ppm"; assert sha(src)==cap['full_sha256']
                x=i%2*960; y=i//2*480; draw.text((x+12,y+8),title,font=font,fill=(239,216,155))
                canvas.paste(Image.open(src).resize((960,430),Image.Resampling.LANCZOS),(x,y+50)); sources.append(cap)
            canvas.save(a.out)
            a.out.with_suffix('.json').write_text(json.dumps(dict(image_sha256=sha(a.out),binary_sha256=gui['binary_sha256'],
                scope=gui['scope'],sources=sources),ensure_ascii=False,indent=2)+'\n'); return
        assert '203 passed; 0 failed' in (q/'native/tests.log').read_text()
        evidence=json.loads((q/'evidence/shop-inventory.json').read_text())
        pam=(r/'workplace/intake-20261023/sources/game/8sword/PAM.AY').read_bytes()
        assert hashlib.sha256(pam).hexdigest()==evidence['probe']['source_sha256']
        assert sha(r/'workplace/probe-20261023/text-first/PAM.i64')==evidence['probe']['database_sha256']
        word=lambda at:struct.unpack_from('<H',pam,at)[0];header=word(8)*16
        relocs=[header+word(word(24)+i*4+2)*16+word(word(24)+i*4) for i in range(word(6))]
        count=0
        for f in evidence['functions']:
            for v in f['lines']:
                at=v['file_offset'];want=bytes.fromhex(v['bytes']);assert at==v['ida_linear']-0x10000+header
                raw=bytearray(pam[at:at+len(want)])
                for off in relocs:
                    if at<=off and off+2<=at+len(want):struct.pack_into('<H',raw,off-at,(struct.unpack_from('<H',raw,off-at)[0]+0x1000)&65535)
                assert bytes(raw)==want;count+=1
        caps=[]; fnv=module(r,'rust-native-player.py').fnv
        for run in gui['runs']:
            assert run['exit']==0
            folder=q/'native/gui'/run['name']; labels={c['number']:c['label'] for c in run['captures']}
            for meta in sorted(folder.glob('capture-*.tsv')):
                n=int(meta.stem.split('-')[1]); cap=dict(l.split('\t',1) for l in meta.read_text().splitlines())
                center=folder/f'frame-{n:03}.ppm'; full=folder/f'shell-frame-{n:03}.ppm'
                assert center.read_bytes()==(folder/f'readback-{n:03}.ppm').read_bytes()
                assert full.read_bytes()==(folder/f'shell-readback-{n:03}.ppm').read_bytes()
                im=Image.open(center).convert('RGBA');assert cap['frame_hash']==format(fnv(im.tobytes()),'016x')
                assert Image.open(full).convert('RGB').crop((512,0,2432,1320)).tobytes()==im.convert('RGB').tobytes()
                caps.append(dict(run=run['name'],label=labels.get(n,'automatic'),number=n,captured=cap,central_sha256=sha(center),full_sha256=sha(full)))
        assert len(caps)==21
        pairs=[]
        for left,right,label1,label2 in [('shop','shop-cold','purchased-two','shop-cold'),('shop-cold','spell-cold','target-saved','target-cold'),('guard','guard-cold','clone-target-saved','clone-target-cold')]:
            x=next(c for c in caps if c['run']==left and c['label']==label1);y=next(c for c in caps if c['run']==right and c['label']==label2)
            assert x['captured']['state_hash']==y['captured']['state_hash']
            equal=x['central_sha256']==y['central_sha256']
            if left == 'shop':
                assert x['captured']['message']=='已購入法術' and y['captured']['message']==''
            else: assert equal
            pairs.append(dict(left=left,right=right,state_hash=x['captured']['state_hash'],central_equal=equal,
                transient_message='purchase success message is not persisted' if left=='shop' else None))
        crate={str(p.relative_to(r/'internal/remake-rust')):sha(p) for p in (r/'internal/remake-rust').rglob('*') if p.is_file()}
        assert all(sha(q/'rust-source'/n)==v for n,v in crate.items())
        baseline={k:len(v) for k,v in h.dependencies(r).items()};assert list(baseline.values())==[197,7,923,535]
        spec=(r/'docs/spec/031-rust-independent-remake.md').read_text()
        marker='RUST-COMBAT-INVENTORY-RESOLVED-20261111'
        older=[l for l in spec.splitlines() if any(v in l for v in ['只開放offer0','不支援商品','未支援商品'])]
        assert len(older)>=4 and all(marker in l for l in older)
        assert all(marker in (r/n).read_text() for n in ['CONTEXT.md','WORKLOG.md','RESEARCH-LOG.md'])
        old=json.loads((r/'preserved/rust-display-r1.json').read_text())
        prefix='workplace/probe-20261023/graphics-first/battle-r1/rust-display-r1/native/pack/'
        media=[f for f in old['files'] if f['path'].startswith(prefix)]
        assert len(media)==287
        for f in media: assert sha(q/'native/pack'/f['path'].split('/native/pack/')[1])==f['sha256']
        a.out.write_text(json.dumps(dict(status='passed-rust-combat-inventory-audit',tests=203,shops=46,map_shops=23,battle_shops=23,
            inherited_ida_functions=3,ida_relocated_lines_verified=count,gui=gui,captures=caps,cold_pairs=pairs,unchanged_media=287,runtime_files=288,
            crate=crate,baseline=baseline,resolution_backlinks=dict(keys=['DOS/PAM.AY/MZ10000:1512C','DOS/PAM.AY/MZ10000:154B0','DOS/PAM.AY/DS1E88:2AA8'],older_references=len(older),required_marker=marker),execution=json.loads((q/'execution.json').read_text()),
            limits=['Purchase semantics grounded in preserved IDA9.4 and PAM data; no new live DOS oracle capture in this slice.',
            'Initial positions, caster, book search and guard test charges explicit. Natural random encounter after normal shop exit and walking, not natural acquisition or campaign completion.',
            'Clone checkpoint upper bound is conservative from consumed charges, not exact per-stack clone provenance.',
            'Linux dummy audio and scale1 GUI; earlier default scale and HD media validations retained; no Release/mobile claim.']),ensure_ascii=False,indent=2)+'\n');return
    if a.action == 'prepare':
        assert not q.exists() and q.parent.stat().st_uid == 1000
        q.mkdir(); (q/'evidence').mkdir(); (q/'native/pack').mkdir(parents=True)
        raw = h.stored(r, 'rust-world-magic-r1', 'evidence/ida-world-magic.json')
        old = json.loads(raw)
        assert old['probe']['version'] == '9.4' and old['probe']['functions'] == 521
        fs = [f for f in old['functions'] if f['start'] in [0x1512c, 0x15354, 0x154b0]]
        assert len(fs) == 3
        lines = {v['ida_linear']: v for f in fs for v in f['lines']}
        for at, code in {0x1515f:'8b87882a', 0x151b5:'ff84982a', 0x154cb:'8b84a82a', 0x154d2:'8b84282b'}.items():
            assert lines[at]['bytes'] == code
        source = r/'workplace/intake-20261023/sources/game/8sword/PAM.AY'
        assert sha(source) == old['probe']['source_sha256']
        b = source.read_bytes(); ds = struct.unpack_from('<H', b, 8)[0]*16 + 0x1d780
        prices = list(struct.unpack_from('<8H', b, ds+0x2a98))
        assert prices == [20,40,60,100,200,300,500,5000]
        offers = [int(l.split('\t')[4]) for l in (r/'internal/remake-rust/magic-shops.tsv').read_text().splitlines() if not l.startswith('#')]
        evidence = dict(probe=old['probe'], tool=old['tool'], address_space=old['address_space'],
            inherited_export_sha256=hashlib.sha256(raw).hexdigest(), functions=fs,
            battle_prices=dict(ds_offset='2A98', file_offset=ds+0x2a98, bytes=b[ds+0x2a98:ds+0x2aa8].hex(), values=prices),
            map_shops=sum(v<8 for v in offers), battle_shops=sum(v>=8 for v in offers),
            semantics=[dict(level='confirmed', source='IDA sub_1512C 1514A..15163,151A8..151B9,15283..152A5', meaning='offer 0..7 map; 8..15 battle; battle price DS2A88+2*offer; charge DS2A98+2*offer'),
            dict(level='confirmed', source='IDA sub_154B0 154C6..154E9', meaning='sum DS2AA8[8] plus DS2B28[8], shared capacity DS04FC')])
        (q/'evidence/shop-inventory.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2)+'\n')
        previous = json.loads((r/'preserved/rust-display-r1.json').read_text())
        for f in previous['files']:
            rel = Path(f['path']).relative_to('workplace/probe-20261023/graphics-first/battle-r1/rust-display-r1')
            if str(rel).startswith('native/pack/'):
                dst=q/rel; dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(h.stored(r, 'rust-display-r1', f['path'])); dst.chmod(f['mode'])
        (q/'native/legacy-v16.chk').write_bytes(h.stored(r, 'rust-display-r1', 'native/legacy-v16.chk'))
        print(json.dumps(dict(map_shops=evidence['map_shops'], battle_shops=evidence['battle_shops'], prices=prices)))
        return
    raise NotImplementedError(a.action)
if __name__ == '__main__': main()
