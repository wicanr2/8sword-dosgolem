#!/usr/bin/env python3
"""053 DRAFT：核對原生Go繪圖的呼叫效果、完整結局成對輸出及成對耗時。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import statistics

from PIL import Image, ImageMath, __version__


def verify_rendering(batch, run):
    """新週期時鐘的來源畫面獨立重建，不把舊指令時鐘動畫當同狀態。"""
    inputs_dir = batch/'owned-inputs-r1'
    data = read(inputs_dir/'inputs.json')
    ega = [(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),(170,85,0),(170,170,170),
           (85,85,85),(85,85,255),(85,255,85),(85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]
    rgb_to_index = {rgb: i for i, rgb in enumerate(ega)}
    sources = {}
    for r in read(batch/'source.json')['records']:
        if not r['color_variant']:
            continue
        im = Image.open(batch/r['image']).convert('RGBA')
        assert hashlib.sha256(im.tobytes()).hexdigest() == r['decoded_rgba_sha256']
        alpha = im.getchannel('A')
        assert set(alpha.tobytes()) <= {0, 255}
        index = Image.frombytes('L', im.size, bytes(rgb_to_index[p[:3]] for p in im.getdata()))
        sources[r['record_sha256']] = im, index, alpha
    masks = {}
    for g in data['cjk']:
        masks[('cjk', g['index'])] = Image.frombytes('1', (16,15), bytes.fromhex(g['bits'])).convert('L')
    for i, bits in enumerate(data['ascii']):
        masks[('ascii', i)] = Image.frombytes('1', (8,15), bytes.fromhex(bits)).convert('L')
    snapshots = [read(run/m['scene']) for m in read(run/'owned-result.json')['samples']]
    for snap in snapshots:
        assert snap['palette'] == [list(c) for c in ega]
        canvas = Image.new('L', (640,200), 0)
        for op in snap['ops']:
            x,y,w,h = (op[k] for k in ('X','Y','W','H'))
            if op['kind'] == 'bitmap':
                _, image, alpha = sources[op['SourceSHA']]
                canvas.paste(image, (x,y), alpha)
            else:
                if op['BG'] != 255:
                    canvas.paste(op['BG'], (x,y,x+w,y+h))
                canvas.paste(op['FG'], (x,y), masks[(op['kind'],op['Code'])])
        name = 'sample-%03d' % snap['sample']
        assert canvas.tobytes() == (run/(name+'.idx')).read_bytes(), name
        rgb = Image.new('RGB', canvas.size)
        rgb.putdata([ega[i] for i in canvas.tobytes()])
        rendered = rgb.convert('RGBA').resize((1920,1200), Image.Resampling.NEAREST)
        assert rendered.tobytes() == Image.open(run/(name+'-source-native.png')).convert('RGBA').tobytes()
    selected = [next(s for s in snapshots if s['stage'] == stage and s['glyphs'] >= minimum)
                for stage, minimum in [('END5.AY',1),('END7.AY',0),('END8.AY',0),('END9.AY',36)]]
    hd = []
    for profile in data['profiles']:
        atlas = Image.open(inputs_dir/profile['atlas']).convert('RGBA').getchannel('A')
        font = {g['codepoint']: g for g in profile['glyphs']}
        title = Image.open(inputs_dir/('title-'+profile['id']+'.png')).convert('RGBA')
        channels = [ImageMath.lambda_eval(lambda a: a['convert'](a['c']*a['a']*257/65280,'L'),
            c=c.convert('I'),a=title.getchannel('A').convert('I')) for c in title.split()[:3]]
        title_rgb = Image.merge('RGB',channels).convert('RGBA')
        end7 = Image.open(inputs_dir/'end7.png').convert('RGBA')
        glyph_cache = {}
        for snap in selected:
            out = Image.new('RGBA',(1920,1200),(0,0,0,255))
            for op in snap['ops']:
                x,y,w,h = op['X']*3,op['Y']*6,op['W']*3,op['H']*6
                if op['kind'] == 'bitmap':
                    if op['SourceFile'] == 'END7.AY':
                        out.paste(end7,(x,y))
                    elif op['SourceFile'] == 'END8.AY':
                        out.paste(title_rgb,(x,y))
                    else:
                        image = sources[op['SourceSHA']][0].resize((w,h),Image.Resampling.NEAREST)
                        out.paste(image,(x,y),image.getchannel('A'))
                    continue
                if op['BG'] != 255:
                    out.paste(ega[op['BG']]+(255,),(x,y,x+w,y+h))
                if op['Char'] == 32:
                    continue
                key = op['Char'],w,h
                if key not in glyph_cache:
                    gx,gy,iw,ih = font[op['Char']]['ink']
                    dw,dh = min(iw,w),min(ih,h)
                    glyph_cache[key] = Image.frombytes('L',(dw,dh),bytes(atlas.getpixel((gx+px*iw//dw,gy+py*ih//dh)) for py in range(dh) for px in range(dw)))
                alpha = glyph_cache[key]
                out.paste(ega[op['FG']]+(255,),(x+(w-alpha.width)//2,y+(h-alpha.height)//2),alpha)
            path = run/('sample-%03d-%s.png' % (snap['sample'],profile['id']))
            assert out.tobytes() == Image.open(path).convert('RGBA').tobytes(), path.name
            hd.append(dict(sample=snap['sample'],stage=snap['stage'],font=profile['id'],image_sha256=sha(path)))
    return hd


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    b = a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    build = b/'direct-build-r3'
    prep = read(build/'preparation.json')
    assert prep['production'] is False
    assert prep['direct_tool_sha256'] == sha(a.project/'tools/research-ending-direct.go')
    assert prep['tool_sha256'] == sha(a.project/'tools/prepare-ending-direct.py')
    for file, expected in prep['files'].items():
        assert sha(build/file) == expected
    source = (build/'ending-direct.go').read_text()
    assert '.Step(' not in source and '.Run(' not in source and '.Stub(' not in source
    assert 'copy(m.EGAPlane(' in source and 'm.CPU.IP = p.registers, p.segments, p.Return' in source
    calls = read(b/'direct-call-audit-r2.json')
    assert len(calls['cases']) == 20 and len(calls['row_cases']) == 24
    for c in calls['cases']+calls['row_cases']:
        assert c['complete_state_equal'] and c['ordered_metadata_equal']
        assert c['replacement_x86_pixel_instructions'] == 0
    assert all(c['rejected_short_quota_without_effects'] for c in calls['row_cases'])
    assert len(calls['benchmarks']) == 9
    benchmark = []
    for file in sorted({c['source'] for c in calls['benchmarks']}):
        rows = [c for c in calls['benchmarks'] if c['source'] == file]
        assert len(rows) == 3 and all(c['calls'] == 16 for c in rows)
        benchmark.append(dict(source=file, native_ns=statistics.median(c['native_ns_per_call'] for c in rows),
            go_ns=statistics.median(c['go_ns_per_call'] for c in rows),
            median_ratio=statistics.median(c['ratio'] for c in rows)))
    control, direct = b/'direct-control-r3', b/'direct-direct-r3'
    normal, fast = read(control/'owned-result.json'), read(direct/'owned-result.json')
    assert normal['direct_enabled'] is False and fast['direct_enabled'] is True
    for key in normal:
        if key not in ('counts', 'direct_enabled'):
            assert normal[key] == fast[key], key
    assert fast['steps'] == 96283141 and fast['unimplemented'] == [] and fast['unknown_writes'] == {}
    assert fast['flips'] == 1049 and fast['frame_purity'] == 41 and fast['clock_cycles_per_ms'] == 3000
    assert '回傳碼 0' in fast['run_error']
    for key, value in normal['counts'].items():
        assert value == fast['counts'][key], key
    extra = {k: v for k, v in fast['counts'].items() if k not in normal['counts']}
    assert extra == {'direct-accepted-0769': 512, 'direct-fallback-quota-or-event': 1761,
        'direct-indexed-readback-bytes': 21927905, 'direct-row-batches': 10845,
        'direct-row-copies': 356654, 'direct-row-fallback-quota-or-event': 3976,
        'direct-skipped-x86-instructions': 3087088}
    files = lambda root: {str(p.relative_to(root)): sha(p) for p in root.rglob('*')
                         if p.is_file() and p.name != 'owned-result.json'}
    original, replaced = files(control), files(direct)
    assert original == replaced, 'full output trees differ'
    assert sha(control/'final.state') == sha(direct/'final.state') == '6ba949eba04aacfe090837dced381e1caaaeab341cda974aaff53410b7f46919'
    assert (direct/'before.state').read_bytes() == (direct/'after.state').read_bytes()
    independent = read(b/'owned-audit-r1.json')
    assert len(independent['native_frames']) == 41 and len(independent['hd_frames']) == 12
    hd_reference = verify_rendering(b, control)
    result = dict(schema=1, spec='053', status='research-native-go-direct-ending-verified', production=False,
        tool_sha256=sha(Path(__file__)), source_preparation_sha256=sha(build/'preparation.json'),
        binary_sha256=sha(b/'ending-direct-scene-r3'), single_call_binary_sha256=sha(b/'ending-direct-call-r2'),
        single_call_report_sha256=sha(b/'direct-call-audit-r2.json'),
        control_report_sha256=sha(control/'owned-result.json'), direct_report_sha256=sha(direct/'owned-result.json'),
        independent_scene_audit_sha256=sha(b/'owned-audit-r1.json'),
        full_call_cases=20, row_cases=24, matched_files=len(original), matched_samples=41,
        matched_source_and_hd_png=164, full_state_sha256=sha(direct/'final.state'),
        independent_native_frames=41, independent_hd_frames=hd_reference,
        direct_counts=extra, benchmark=benchmark, go='1.24.13',
        limits=['Standalone PAE cold research pair, not normal PAM handoff or natural completion.',
                'Only admitted four/five-plane copies use native Go. Masked actors, glyphs and budget-boundary rows may still execute x86.',
                'Game virtual time and indexed readback preserved. Benchmark is call cost, not overall FPS.',
                'No production promotion, PCM listening, GUI or save/reload claim.'])
    with a.out.open('x') as f:
        f.write(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(files=len(original), png=164, skipped_x86=extra['direct-skipped-x86-instructions'],
                          go_row_batches=extra['direct-row-batches'], sha256=sha(a.out))))


if __name__ == '__main__':
    main()
