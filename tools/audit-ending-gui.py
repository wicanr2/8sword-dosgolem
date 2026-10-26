#!/usr/bin/env python3
"""053：獨立重建結局視窗畫面，連回真正Draw串流與受控分支紀錄。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from PIL import Image, ImageMath, __version__


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def swords_over(out, texture, x, y):
    """Independent Go1.24 image/draw NRGBA-over arithmetic, opaque destination."""
    w, h = texture.size
    source = texture.tobytes()
    data = bytearray(out.crop((x,y,x+w,y+h)).tobytes())
    for at in range(0,len(source),4):
        sa = source[at+3]*257
        if sa == 0:
            continue
        a = (65535-sa)*257
        for channel in range(3):
            data[at+channel] = (data[at+channel]*a//65535+source[at+channel]*sa//255)>>8
        data[at+3] = 255
    out.paste(Image.frombytes('RGBA',(w,h),bytes(data)),(x,y))


def reconstruct(meta, assets, sources):
    data = read(assets/'ending.json')
    ega = [(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),(170,85,0),(170,170,170),
           (85,85,85),(85,85,255),(85,255,85),(85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]
    assert meta['palette'] == [list(c) for c in ega]
    profile = next(p for p in data['profiles'] if p['id'] == meta['font'])
    font = {g['codepoint']: g for g in profile['glyphs']}
    atlas = Image.open(assets/profile['atlas']).convert('RGBA').getchannel('A')
    title = Image.open(assets/('ending-title-'+profile['id']+'.png')).convert('RGBA')
    channels = [ImageMath.lambda_eval(lambda a: a['convert'](a['c']*a['a']*257/65280,'L'),
                c=c.convert('I'), a=title.getchannel('A').convert('I')) for c in title.split()[:3]]
    title = Image.merge('RGB',channels).convert('RGBA')
    out = Image.new('RGBA',(1920,1200),(0,0,0,255))
    portraits = {}
    if (assets/'ending-portrait.json').exists():
        for record in read(assets/'ending-portrait.json')['records']:
            assert sha(assets/record['file']) == record['sha256']
            portraits[record['source_sha256']] = Image.open(assets/record['file']).convert('RGBA')
    if (assets/'ending-duel.json').exists():
        duel = read(assets/'ending-duel.json')
        assert sha(assets/duel['image']) == duel['image_sha256']
        portraits[duel['source_sha256']] = Image.open(assets/duel['image']).convert('RGBA')
    swords = None
    effects = {}
    pairs = {}
    if (assets/'ending-pair.json').exists():
        for pair in read(assets/'ending-pair.json')['records']:
            assert sha(assets/pair['image']) == pair['image_sha256']
            pairs[pair['source_sha256']] = Image.open(assets/pair['image']).convert('RGBA')
    if (assets/'ending-effects.json').exists():
        for effect in read(assets/'ending-effects.json')['records']:
            assert sha(assets/effect['image']) == effect['image_sha256']
            effects[effect['source_sha256']] = Image.open(assets/effect['image']).convert('RGBA')
    if (assets/'ending-swords.json').exists():
        manifest = read(assets/'ending-swords.json')
        assert sha(assets/manifest['image']) == manifest['image_sha256']
        swords = Image.open(assets/manifest['image']).convert('RGBA')
    for index, op in enumerate(meta['ops']):
        x,y,w,h = op['X']*3,op['Y']*6,op['W']*3,op['H']*6
        if op['kind'] == 'bitmap':
            if op['SourceSHA'] in pairs:
                repeated = False
                for prior in reversed(meta['ops'][:index]):
                    if op['X'] >= prior['X']+prior['W'] or prior['X'] >= op['X']+op['W'] or op['Y'] >= prior['Y']+prior['H'] or prior['Y'] >= op['Y']+op['H']:
                        continue
                    repeated = all(prior[k] == op[k] for k in ['kind','SourceSHA','X','Y','W','H'])
                    break
                if not repeated:
                    native = sources[op['SourceSHA']]
                    black = Image.new('L',native.size)
                    black.putdata([255 if c[3] and c[:3] == (0,0,0) else 0 for c in native.getdata()])
                    out.paste((0,0,0,255),(x,y,x+w,y+h),black.resize((w,h),Image.Resampling.NEAREST))
                    swords_over(out,pairs[op['SourceSHA']],x,y)
            elif op['SourceSHA'] in effects:
                repeated = False
                for prior in reversed(meta['ops'][:index]):
                    if op['X'] >= prior['X']+prior['W'] or prior['X'] >= op['X']+op['W'] or op['Y'] >= prior['Y']+prior['H'] or prior['Y'] >= op['Y']+op['H']:
                        continue
                    repeated = all(prior[k] == op[k] for k in ['kind','SourceSHA','X','Y','W','H'])
                    break
                if not repeated:
                    swords_over(out,effects[op['SourceSHA']],x,y)
            elif swords is not None and op['SourceSHA'] == manifest['source_sha256']:
                repeated = False
                for prior in reversed(meta['ops'][:index]):
                    if op['X'] >= prior['X']+prior['W'] or prior['X'] >= op['X']+op['W'] or op['Y'] >= prior['Y']+prior['H'] or prior['Y'] >= op['Y']+op['H']:
                        continue
                    repeated = all(prior[k] == op[k] for k in ['kind','SourceSHA','X','Y','W','H'])
                    break
                if not repeated:
                    swords_over(out,swords,x,y)
            elif op['SourceSHA'] in portraits:
                out.paste(portraits[op['SourceSHA']],(x,y))
            elif op['SourceFile'] == 'END7.AY':
                out.paste(Image.open(assets/'ending-end7-r2.png').convert('RGBA'),(x,y))
            elif op['SourceFile'] == 'END8.AY':
                out.paste(title,(x,y))
            else:
                im = sources[op['SourceSHA']].resize((w,h),Image.Resampling.NEAREST)
                out.paste(im,(x,y),im.getchannel('A'))
            continue
        assert op['kind'] in ('cjk','ascii')
        if op['BG'] != 255:
            out.paste(ega[op['BG']]+(255,),(x,y,x+w,y+h))
        if op['Char'] == 32:
            continue
        gx,gy,iw,ih = font[op['Char']]['ink']
        dw,dh = min(iw,w),min(ih,h)
        alpha = Image.frombytes('L',(dw,dh),bytes(atlas.getpixel((gx+px*iw//dw,gy+py*ih//dh)) for py in range(dh) for px in range(dw)))
        out.paste(ega[op['FG']]+(255,),(x+(w-dw)//2,y+(h-dh)//2),alpha)
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--gui',type=Path,required=True)
    p.add_argument('--assets',type=Path,required=True)
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--escape',action='store_true')
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    root = a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    assets = read(a.assets/'ending.json')
    assert all(f.is_file() and not f.is_symlink() for f in a.assets.iterdir())
    for name,digest in assets['files'].items():
        assert sha(a.assets/name) == digest
    st = read(a.gui/'gui-final.json')
    assert st['closed'] and st['exited'] and st['exit_code'] == 0 and st['owned_render_fault'] is None
    assert st['hd'] and st['source_renderer'] and st['source_frames'] > 0 and st['direct_calls'] > 0
    for key,value in st.items():
        if key.endswith('_error'):
            assert not value, (key,value)
    assert not st['music']['load_error']
    assert st['toolbar_error'] == '' and st['presentation_size'] == [2944,1264]
    assert st['ending']['error'] == '' and st['ending']['input_api'] is True and st['ending']['input_discarded'] == [0,1,0]
    if (a.assets/'ending-portrait.json').exists():
        assert st['ending']['portrait'] == dict(loaded=True,textures=5,error='')
    assert st['ending']['counts']['unclassified-writes'] == 0 if 'unclassified-writes' in st['ending']['counts'] else True
    direct = st['ending']['direct']
    assert direct['direct-skipped-x86-instructions'] > 0 and direct['masked-skipped-x86'] > 0 and direct['glyph-skipped-x86'] > 0
    probe = st['research_ending']
    assert probe['armed'] and probe['changed'] and len(probe['mutations']) == 1
    mutation = probe['mutations'][0]
    assert mutation['old'] == 0 and mutation['new'] == 1 and mutation['address'] == dict(Seg=0x1e88,Off=0x56e2)
    required = {'END5.AY-noto'} if a.escape else {'END5.AY-'+font for font in ('noto','lishu','caoshu')} | {'END7.AY-noto','END8.AY-noto','END9.AY-noto'}
    assert required <= set(probe['seen'])
    if a.escape:
        assert not any(k.startswith('END7') for k in probe['seen'])
    preparation = read(a.build/'build-manifest.json')
    for name,digest in preparation['diagnostic_files'].items():
        assert sha(a.build/'src'/name) == digest
    for name,digest in preparation['binaries'].items():
        binary = a.project/name if name.startswith('workplace/') else root/name
        assert sha(binary) == digest
    records = read(root/'source.json')['records']
    sources = {}
    for record in records:
        if not record['color_variant']:
            continue
        im = Image.open(root/record['image']).convert('RGBA')
        assert hashlib.sha256(im.tobytes()).hexdigest() == record['decoded_rgba_sha256']
        sources[record['record_sha256']] = im
    selected = {}
    results = []
    for meta_path in sorted((a.gui/'ending-draw').glob('*.json')):
        meta = read(meta_path)
        key = meta['key']
        central = Image.open(meta_path.with_name(key+'-central.png')).convert('RGBA')
        assert reconstruct(meta,a.assets,sources).tobytes() == central.tobytes(), key
        presented = Image.open(meta_path.with_name(key+'-presented.png')).convert('RGBA')
        assert presented.size == (2944,1264) and presented.crop((512,64,2432,1264)).tobytes() == central.tobytes()
        assert any(v['key'] == key and v['draw'] == meta['draw'] and v['step'] == meta['step'] for v in probe['samples'])
        selected[meta['draw']] = central.tobytes(), key
        results.append(dict(key=key,draw=meta['draw'],step=meta['step'],central_sha256=sha(meta_path.with_name(key+'-central.png')),metadata_sha256=sha(meta_path)))
    spec = importlib.util.spec_from_file_location('ending_gui_stream',a.project/'tools/audit-army-dismiss.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    log = [json.loads(line) for line in (a.gui/'intro-draw.jsonl').read_text().splitlines()]
    matched = set()
    count = 0
    for n,step,im in module.stream(a.gui):
        count += 1
        assert log[n-1]['draw'] == n and log[n-1]['step'] == step
        if n in selected:
            raw,key = selected[n]
            assert im.tobytes() == raw, key
            matched.add(key)
    assert count == st['presented_frames'] == st['recorded_frames'] == len(log)
    assert matched == set(probe['seen']) and required <= matched
    result = dict(schema=1,spec='053',production=False,status='PASS-ending-actual-Draw',escape=a.escape,
                  samples=results,draws=count,source_frames=st['source_frames'],direct=direct,
                  actual_handoff_go_skipped_x86=sum(direct[k] for k in ('direct-skipped-x86-instructions','masked-skipped-x86','glyph-skipped-x86')),
                  mutations=probe['mutations'],build_sha256=sha(a.build/'build-manifest.json'),
                  gui_final_sha256=sha(a.gui/'gui-final.json'),stream_sha256=sha(a.gui/'presentation.frames.gz'),
                  tool_sha256=sha(Path(__file__)),limits=['Controlled original ending branch; not natural victory.',
                  'Actual Ebiten Draw and recorded CPU texture; X11 screenshots retained separately.',
                  'END7 corrected r2 and three text fonts; remaining ending art still source pixels.',
                  'Linux software graphics and muted device; no physical GPU or listening claim.'])
    if (a.assets/'ending-portrait.json').exists():
        result['portrait_manifest_sha256'] = sha(a.assets/'ending-portrait.json')
        result['portrait_loaded'] = st['ending']['portrait']['loaded']
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],draws=count,samples=len(results))))


if __name__ == '__main__':
    main()
