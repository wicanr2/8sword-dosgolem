#!/usr/bin/env python3
"""053 READY：獨立Pillow重建正式候選結局完整Frame，核對客體與實際Go接管。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
from PIL import Image, ImageMath, __version__


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def verify_rendering(batch, run, inputs_dir):
    """新週期時鐘的來源畫面獨立重建，不把舊指令時鐘動畫當同狀態。"""
    data = read(inputs_dir/'ending.json')
    portraits = {}
    if (inputs_dir/'ending-portrait.json').exists():
        for record in read(inputs_dir/'ending-portrait.json')['records']:
            assert sha(inputs_dir/record['file']) == record['sha256']
            portraits[record['source_sha256']] = Image.open(inputs_dir/record['file']).convert('RGBA')
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
    snapshots = [dict(read(run/(m['prefix']+'.json')),sample=int(m['prefix'].split('-')[-1])) for m in read(run/'runtime.json')['snapshots']]
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
        name = 'sample-%02d' % snap['sample']
        rgb = Image.new('RGB', canvas.size)
        rgb.putdata([ega[i] for i in canvas.tobytes()])
        rendered = rgb.convert('RGBA').resize((1920,1200), Image.Resampling.NEAREST)
        assert rendered.tobytes() == Image.open(run/(name+'-native.png')).convert('RGBA').tobytes()
    selected = snapshots
    hd = []
    for profile in data['profiles']:
        atlas = Image.open(inputs_dir/profile['atlas']).convert('RGBA').getchannel('A')
        font = {g['codepoint']: g for g in profile['glyphs']}
        title = Image.open(inputs_dir/('ending-title-'+profile['id']+'.png')).convert('RGBA')
        channels = [ImageMath.lambda_eval(lambda a: a['convert'](a['c']*a['a']*257/65280,'L'),
            c=c.convert('I'),a=title.getchannel('A').convert('I')) for c in title.split()[:3]]
        title_rgb = Image.merge('RGB',channels).convert('RGBA')
        end7 = Image.open(inputs_dir/'ending-end7-r2.png').convert('RGBA')
        glyph_cache = {}
        for snap in selected:
            out = Image.new('RGBA',(1920,1200),(0,0,0,255))
            for op in snap['ops']:
                x,y,w,h = op['X']*3,op['Y']*6,op['W']*3,op['H']*6
                if op['kind'] == 'bitmap':
                    if op['SourceSHA'] in portraits:
                        out.paste(portraits[op['SourceSHA']],(x,y))
                    elif op['SourceFile'] == 'END7.AY':
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
            path = run/('sample-%02d-%s.png' % (snap['sample'],profile['id']))
            assert out.tobytes() == Image.open(path).convert('RGBA').tobytes(), path.name
            hd.append(dict(sample=snap['sample'],stage=snap['stage'],font=profile['id'],image_sha256=sha(path)))
    return hd


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--runtime', default='runtime-r3')
    parser.add_argument('--sources', default='engine-build-r3')
    parser.add_argument('--binary', default='ending-engine-tests-r3')
    parser.add_argument('--assets', default='assets-candidate-r3')
    parser.add_argument('--portrait', action='store_true', help='verify the separate five-texture END5 group')
    parser.add_argument('--additional-tests-log', type=Path, help='separately completed asset-fault job using the identical test binary')
    args = parser.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not args.out.exists() and args.out.parent.stat().st_uid == 1000
    p = args.project
    b = p/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    run = b/args.runtime
    assets = b/args.assets
    assert sha(assets/'ending.json') == 'f66ddeebfecd728ccca16e4c958e386046f2383ecf83a662b280582785ffbd7b'
    manifest = read(assets/'ending.json')
    for name, digest in manifest['files'].items():
        assert sha(assets/name) == digest
    assert manifest['art_source_sha256'] == '50dc8cfd675457526810c709a0e5197bcb46eff7aef1fdc0d12a6b7774fdde27'
    formal = read(p/'workplace/probe-20261023/graphics-first/story-art-r1/blue-person-correction-r4/runtime-audit-r4.json')
    for name, digest in formal['asset_hashes'].items():
        assert not (assets/name).is_symlink() and (assets/name).is_file() and sha(assets/name) == digest
    assert len(list(assets.iterdir())) == (439 if args.portrait else 433)
    if args.portrait:
        assert sha(assets/'ending-portrait.json') == '384bc2ecb1e280dd487ce3ed6fb3981d2e28da0c98031cd132ccefce4519eb80'
        previous = read(b/'ending-promotion-audit-r1.json')['asset_hashes']
        assert len(previous) == 433
        for name,digest in previous.items():
            assert sha(assets/name) == digest
    core = read(b/'runtime-input-r1/runtime-input.json')
    assert len(core['base_inputs']) == 919 and len(core['added']) == 2
    for name, digest in {**core['base_inputs'], **core['added']}.items():
        assert sha(b/'runtime-input-r1/src'/name) == digest
    sources = read(b/args.sources/'sources.json')
    for name, digest in sources['files'].items():
        assert sha(p/name) == sha(b/args.sources/'src'/name) == digest
    runs = {n: read(run/n/'runtime.json') for n in ['native', 'hd', 'native-escape', 'hd-escape']}
    for left, right in [('native', 'hd'), ('native-escape', 'hd-escape')]:
        a, z = runs[left], runs[right]
        for field in ['steps', 'state_sha256', 'native_pcm_sha256', 'mutations', 'inputs', 'overlays', 'file_ops', 'unimplemented']:
            assert a[field] == z[field], (left, right, field)
        assert sha(run/left/'final.state') == sha(run/right/'final.state') == a['state_sha256']
        assert a['unimplemented'] == [] and len(a['mutations']) == 1
        assert a['mutations'][0]['address'] == dict(Seg=0x1e88, Off=0x56e2)
    assert (run/'native/final.state').read_bytes() == (b/'runtime-r1/native/final.state').read_bytes()
    assert (run/'native-escape/escape-before.state').read_bytes() == (run/'hd-escape/escape-before.state').read_bytes()
    assert runs['native']['steps'] == 138507913 and runs['native-escape']['steps'] == 100264740
    direct = runs['hd']['ending']['direct']
    assert direct['direct-skipped-x86-instructions'] == 3086215
    assert direct['masked-skipped-x86'] == 38659302 and direct['glyph-skipped-x86'] == 11194884
    assert direct['glyph-go-rows'] == 317357 and direct['masked-run-batches'] == 291603
    assert runs['hd']['ending']['input_api'] is True and runs['hd']['ending']['input_discarded'] == [0, 1, 0]
    for name in ['hd', 'hd-escape']:
        assert runs[name]['ending']['error'] == '' and runs[name]['ending']['pending'] == 0
        for sample in runs[name]['snapshots']:
            assert (run/name/(sample['prefix']+'-before.state')).read_bytes() == (run/name/(sample['prefix']+'-after.state')).read_bytes()
    if args.portrait:
        assert runs['hd']['ending']['portrait'] == dict(loaded=True,textures=5,error='')
        assert len(runs['hd']['portrait_snapshots']) >= 3
    log = (b/(args.runtime+'.log')).read_text()
    test_logs = [log]
    if args.additional_tests_log:
        extra = args.additional_tests_log
        assert extra.with_name(extra.stem+'-exit.txt').read_text().strip() == 'passed'
        digest, executable = extra.with_name(extra.stem+'-binary.sha256').read_text().split()
        assert digest == sha(b/args.binary) and Path(executable).name == args.binary
        supplemental = extra.read_text()
        assert supplemental.endswith('PASS\n') and '--- FAIL:' not in supplemental
        test_logs.append(supplemental)
    for test in ['TestEndingSourceRuntime', 'TestEndingInputHandoffGuard', 'TestEndingAssetsFaults']:
        assert any('--- PASS: '+test in text for text in test_logs)
    assert not any('--- FAIL:' in text for text in test_logs)
    if args.portrait:
        assert '--- PASS: TestEndingPortraitLoadAndAtomicFallback' in log
    native_go = (p/'internal/eightsword/ending_scene.go').read_text()
    assert 'oracle' not in native_go and 'ScreenRGB' not in native_go and 'EGAPlane' not in native_go
    for name in ['ending_direct.go', 'ending_masked.go', 'ending_glyphs.go']:
        code = (p/'internal/eightsword'/name).read_text()
        assert all(forbidden not in code for forbidden in ['.Step(', '.Run(', '.Stub('])
    frames = verify_rendering(b, run/'hd', assets)
    escaped = verify_rendering(b, run/'hd-escape', assets)
    assert len(frames) == 12 and len(escaped) == 3
    result = dict(schema=1, spec='053', status='verified-Engine-ending-candidate', production=False,
                  runtime_directory=args.runtime, source_directory=args.sources, binary=args.binary,
                  tool_sha256=sha(Path(__file__)), binary_sha256=sha(b/args.binary),
                  source_manifest_sha256=sha(b/args.sources/'sources.json'),
                  core_manifest_sha256=sha(b/'runtime-input-r1/runtime-input.json'),
                  asset_manifest_sha256=sha(assets/'ending.json'), total_assets=439 if args.portrait else 433,
                  unchanged_base_assets=433 if args.portrait else 425, original_core_preserved=919, private_core_inputs=921,
                  complete_steps=138507913, escape_steps=100264740, frames=frames, escape_frames=escaped,
                  guest_state_sha256=runs['hd']['state_sha256'], native_pcm_sha256=runs['hd']['native_pcm_sha256'],
                  escape_state_sha256=runs['hd-escape']['state_sha256'], escape_pcm_sha256=runs['hd-escape']['native_pcm_sha256'],
                  direct_counts=direct, actual_handoff_skipped_x86=52940401,
                  run_receipts={n: sha(run/n/'runtime.json') for n in runs},
                  limits=['Actual original overlay follows controlled cleanup branch, not natural victory.',
                          'Headless Engine Frame evidence, not GUI Draw or new save/reload acceptance.',
                          'END7 uses corrected r2; optional END5 uses five source-identified textures. Other unconverted art remains source pixels rendered by Go.',
                          'Candidate uses ordinary files; this read-only audit does not promote formal assets.',
                          'Native Go admits batches under existing event limits; boundary/clear/copy loops remain native.'])
    if args.portrait:
        result['portrait_manifest_sha256'] = sha(assets/'ending-portrait.json')
        result['portrait_representatives'] = runs['hd']['portrait_snapshots']
    if args.additional_tests_log:
        result['separate_asset_tests_sha256'] = sha(args.additional_tests_log)
        result['aggregate_deadline_exceeded'] = 'panic: test timed out' in log
    with args.out.open('x') as handle:
        handle.write(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(frames=len(frames), escape_frames=len(escaped), skipped_x86=52940401, sha256=sha(args.out))))


if __name__ == '__main__':
    main()
