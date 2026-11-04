#!/usr/bin/env python3
"""Rust原生普通戰鬥：素材投影、收據核對與永久保存。只在Docker使用。"""
import argparse,array,gzip,hashlib,importlib.util,io,json,math,os,shutil,struct,sys,wave
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-native-player-r1'
REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def fnv(raw):
    v=14695981039346656037
    for b in raw:v=((v^b)*1099511628211)&((1<<64)-1)
    return v
def blob(p,raw):
    assert not p.exists();p.write_bytes(raw+struct.pack('<Q',fnv(raw)))
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['prepare','audio','audit','archive','verify'])
    for n in ['project','assets','work','archive','out']:ap.add_argument('--'+n,type=Path)
    a=ap.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
    if a.action=='verify':
        idx=read(a.archive/(BATCH+'.json'))
        for f in idx['files']:
            ob=idx['objects'][f['sha256']];p=a.archive/BATCH/ob['file'];assert sha(p)==ob['stored_sha256'];raw=gzip.decompress(p.read_bytes());assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
        write(a.out,dict(status='passed-detached-rust-native-player',files=len(idx['files']),objects=len(idx['objects'])));return
    r=a.project;q=a.work or r/REL;pack=q/'native/pack'
    if a.action=='prepare':
        from PIL import Image,ImageFont,ImageDraw,__version__
        assert __version__=='11.3.0';assets=a.assets;pack.mkdir();sources={}
        def source(root,name,expected):
            p=root/name;assert p.is_file()and sha(p)==expected,(name,'SHA');sources[str(p)]=sha(p);return p
        def image(name,im):blob(pack/name,b'8SRGBA01'+struct.pack('<II',*im.size)+im.convert('RGBA').tobytes())
        meta=read(assets/'battle-palace-background.json')['image'];p=source(assets,meta['file'],meta['sha256']);im=Image.open(p).convert('RGBA');assert im.size==(1586,992)
        image('background.rgba',im.resize((1920,1200),Image.Resampling.BILINEAR))
        for native,manifest in [(6,'battle-man06.json'),(11,'battle-man11.json'),(16,'battle-actors.json')]:
            m=read(assets/manifest)['frames'][0];v=m['image'];p=source(assets,v['file'],v['sha256']);im=Image.open(p).convert('RGBA');assert im.size==(v['width'],v['height'])
            x,y,w,h=v['source_rect'];tx,ty,tw,th=m['target_rect'];tile=Image.new('RGBA',(264,300));tile.paste(im.crop((x,y,x+w,y+h)).resize((tw,th),Image.Resampling.BILINEAR),(tx,ty));image(f'unit_native_{native:02}.rgba',tile)
        ui=r/'workplace/probe-20261023/graphics-first/battle-r1/original-player-integration-r1/ui-assets'
        for row in read(ui/'unit-art.json')['rows']:
            if row['id']not in ['openkb:wolf','openkb:arcr']:continue
            p=source(ui,row['file'],row['sha256']);im=Image.open(p).convert('RGBA');assert im.size==(512,512);box=im.getchannel('A').getbbox();assert box
            cut=im.crop(box);bw,bh=cut.size;w,h=252,288
            if w*bh>h*bw:w=h*bw//bh
            else:h=w*bh//bw
            tile=Image.new('RGBA',(264,300));tile.paste(cut.resize((w,h),Image.Resampling.NEAREST),((264-w)//2,300-h));image('unit_'+row['id'].replace(':','_')+'.rgba',tile)
        spec=importlib.util.spec_from_file_location('fonts',r/'tools/prepare-owned-army-ui.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
        idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()));faces={};font_sources={}
        for key,digest in helper.FONT_SHA.items():
            raw=gzip.decompress((r/'preserved'/idx['objects'][digest]['path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==digest
            faces[key]=ImageFont.truetype(io.BytesIO(raw),48,index=3 if key in ['noto','serif']else 0);font_sources[key]=digest
        chars=set(map(chr,range(32,127)))|{'…'}
        for p in(r/'internal/remake-rust').rglob('*.rs'):chars.update(ch for ch in p.read_text()if ord(ch)>127 and ch.isprintable())
        for row in read(r/'workplace/probe-20261023/graphics-first/battle-r1/rust-battle-core-r1/inputs/army-catalog.json')['profiles']:chars.update(row['name'])
        fonts=[]
        for key in ['noto','lishu','caoshu']:
            face=faces[key];missing=face.getmask('\U0010ffff');missing=(missing.size,bytes(missing));raw=bytearray(b'8SGLYP01'+struct.pack('<I',len(chars)));fallbacks=[]
            for ch in sorted(chars):
                mask=face.getmask(ch);cjk=0x3400<=ord(ch)<=0x9fff;native=key=='noto'or(cjk and(mask.size,bytes(mask))!=missing and bool(mask.getbbox()))
                chosen=face if native else faces['serif']if key=='lishu'and cjk else faces['noto']
                if not native:fallbacks.append(ch)
                cell=Image.new('L',(64,64));box=chosen.getbbox(ch);w,h=box[2]-box[0],box[3]-box[1]
                ImageDraw.Draw(cell).text(((64-w)//2-box[0],(64-h)//2-box[1]),ch,font=chosen,fill=255)
                raw.extend(struct.pack('<I',ord(ch)));raw.extend(cell.tobytes())
            blob(pack/f'font-{key}.bin',bytes(raw));fonts.append(dict(id=key,glyphs=len(chars),fallbacks=''.join(fallbacks),family=face.getname()))
        music=next(v for v in read(assets/'music.json')['cues']if v['id']==3);source(assets,music['file'],music['sha256'])
        write(q/'media-source-r1.json',dict(sources=sources,font_sources=font_sources,fonts=fonts,music=music,graphics='Approved original-style HD assets; no original RGB frame',native_units=5,rights='original-derived-local; full media pack stays local'))
        for p in ui.glob('font-*'):
            if p.suffix=='.txt':shutil.copy2(p,pack/p.name)
        return
    if a.action=='audio':
        raw=(pack/'music.s16le').read_bytes();m=read(q/'media-source-r1.json')['music'];assert len(raw)%4==0
        assert len(raw)//4==m['frames'],(len(raw)//4,m['frames'])
        source=a.assets/m['file'];assert sha(source)==m['sha256'];shutil.copy2(source,pack/'music.ogg')
        samples=struct.unpack('<'+'h'*(len(raw)//2),raw);rms=math.sqrt(sum(v*v for v in samples)/len(samples));assert rms>0
        write(q/'audio-r1.json',dict(frames=len(raw)//4,rate=48000,channels=2,bits=16,rms=rms,source_sha256=m['sha256'],ogg_sha256=sha(pack/'music.ogg'),sample_duration_seconds=len(raw)/192000,human_hearing_verified=False,runtime='libsndfile decodes OGG; PCM only in memory and research captures'));(pack/'music.s16le').unlink();return
    if a.action=='audit':
        from PIL import Image as PILImage
        spec=importlib.util.spec_from_file_location('baseline',r/'tools/prepare-owned-army-ui.py');baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline)
        deps=baseline.dependencies(r);counts={k:len(v)for k,v in deps.items()};assert list(counts.values())==[197,7,923,535],counts
        for n,digest in read(q/'source-manifest.json').items():assert sha(q/'source'/n)==digest,n
        crate=r/'internal/remake-rust';snapshot=q/'rust-source'
        crate_files={str(p.relative_to(crate)):sha(p)for p in crate.rglob('*')if p.is_file()}
        assert all(sha(snapshot/n)==h for n,h in crate_files.items())
        assert sha(crate/'controller-reference.tsv')==sha(q/'controller-reference-r2.tsv')
        assert(q/'tests-reference-r3.log').read_text().rstrip().endswith('PASS')
        lines=(crate/'controller-reference.tsv').read_text().splitlines();control={k:sum(s.split('\t')[0]==k for s in lines)for k in ['START','OFFER','ATTACK','SKIP','RETREAT','END']}
        assert control==dict(START=4,OFFER=71,ATTACK=42,SKIP=6,RETREAT=1,END=4),control
        tests=(q/'native/tests-rust-final.log').read_text();assert 'test result: ok. 18 passed' in tests and 'FAILED'not in tests
        cli=(q/'native/cli-final.log').read_text();assert all(s in cli for s in ['33種','201組','309組','40個','71次','42次','6次'])
        media=read(q/'media-source-r1.json');audio=read(q/'audio-r1.json');assert sha(pack/'music.ogg')==media['music']['sha256']==audio['ogg_sha256']
        assert not(pack/'music.pcm').exists();pack_files={p.name:sha(p)for p in pack.iterdir()if p.is_file()}
        for p in pack.glob('*.rgba'):
            raw=p.read_bytes();assert raw[:8]==b'8SRGBA01'and struct.unpack('<Q',raw[-8:])[0]==fnv(raw[:-8]);w,h=struct.unpack('<II',raw[8:16]);assert len(raw)==24+w*h*4
        for p in pack.glob('font-*.bin'):
            raw=p.read_bytes();assert raw[:8]==b'8SGLYP01'and struct.unpack('<Q',raw[-8:])[0]==fnv(raw[:-8]);n,=struct.unpack('<I',raw[8:12]);assert 0<n<=4096 and len(raw)==20+n*4100
        raw=(pack/'background.rgba').read_bytes();background=PILImage.frombytes('RGBA',(1920,1200),raw[16:-8]).convert('RGB')
        gui=read(q/'native/gui-r5/receipt.json');assert gui['status']=='passed-rust-native-gui'and gui['binary_sha256']==sha(q/'native/8sword-remake');samples=[];native_pcm=(q/'native/reference-music.s16le').read_bytes()
        assert len(native_pcm)==audio['frames']*4
        for row in gui['rows']:
            d=q/'native/gui-r5'/row['mode'];assert row['final']['outcome']==row['mode']and row['exit']==0
            assert int(row['final']['drains'])>0 and int(row['final']['queued_bytes'])>0
            assert int(row['final']['music_frames'])==audio['frames']
            for capture in row['captures']:
                status=capture['status'];n=int(status['captures']);assert status['readback_equal']=='true'
                left=d/f'frame-{n:03}.ppm';right=d/f'readback-{n:03}.ppm';assert left.read_bytes()==right.read_bytes()
                with wave.open(str(d/f'audio-{n:03}.wav'),'rb')as wav:
                    assert(wav.getframerate(),wav.getnchannels(),wav.getsampwidth())==(48000,2,2)
                    pcm=wav.readframes(wav.getnframes());assert pcm
                actual=array.array('h');actual.frombytes(pcm);expected=array.array('h');expected.frombytes(native_pcm[:len(pcm)])
                assert any(actual)and len(actual)==len(expected)
                max_error=max(abs(a-b)for a,b in zip(actual,expected));rms=math.sqrt(sum(v*v for v in actual)/len(actual));assert max_error<=2,max_error
                samples.append(dict(case=row['mode'],label=capture['label'],image_sha256=sha(left),pcm_sha256=hashlib.sha256(pcm).hexdigest(),frames=len(pcm)//4,rms=rms,max_error_from_ffmpeg=max_error))
            final_image=PILImage.open(d/f"frame-{int(row['final']['captures']):03}.ppm")
            if row['mode']=='win':
                assert final_image.crop((816,48,1920,1248)).tobytes()==background.crop((816,0,1920,1200)).tobytes()
            elif row['mode']=='loss':
                assert final_image.crop((0,48,816,1248)).tobytes()==background.crop((0,0,816,1200)).tobytes()
        assert len(samples)==6 and {s['label']for s in samples}>={'noto','lishu','caoshu','win','loss','retreat'}
        write(a.out,dict(status='passed-rust-native-player-audit',formal_baseline_counts=counts,controller=control,tests_passed=18,cli=cli,crate_files=crate_files,go_source_files=len(read(q/'source-manifest.json')),media=media,audio=audio,pack_files=pack_files,gui=samples,binary_sha256=sha(q/'native/8sword-remake'),execution=read(q/'execution-r1.json'),death_background_pixels=1920*1200,limits=['Explicit ordinary battle fixtures, not a world or full game.','No native spells, special units, save, new-game or ending integration yet.','Controller source order/HP/remaining compare original-interface Go; target choices controlled. Native AI has deterministic legal targets, not full original RNG-call parity.','SDL dummy proves decoding and consumption; no human hearing claim.','Linux x86_64 development binary; no Release or cross-platform acceptance.']))
        return
    folder=a.archive/BATCH;folder.mkdir();files=[];objects={}
    for p in sorted(q.rglob('*')):
        if not p.is_file()or any(n in p.relative_to(q).parts for n in ['build-cache','rust-target']):continue
        assert not p.is_symlink()and p.stat().st_uid==1000;raw=p.read_bytes();digest=hashlib.sha256(raw).hexdigest();obj=folder/(digest+'.gz')
        if digest not in objects:obj.write_bytes(gzip.compress(raw,6,mtime=0));objects[digest]=dict(file=obj.name,stored_sha256=sha(obj))
        files.append(dict(path=str(Path(REL)/p.relative_to(q)),bytes=len(raw),sha256=digest,mode=p.stat().st_mode&0o777))
    write(a.out,dict(files=files,objects=objects,rights='Original inputs, decoded media and binaries local only. No release.'))
if __name__=='__main__':main()
