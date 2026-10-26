#!/usr/bin/env python3
"""053 DRAFT：從獨立解碼RGBA與原字模核對自有結局場景。Docker only。"""
import argparse
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageMath, __version__


EGA = [(0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170),
       (170, 0, 0), (170, 0, 170), (170, 85, 0), (170, 170, 170),
       (85, 85, 85), (85, 85, 255), (85, 255, 85), (85, 255, 255),
       (255, 85, 85), (255, 85, 255), (255, 255, 85), (255, 255, 255)]
ROOT = 'workplace/probe-20261023/graphics-first/ending-hd-r1'
STATE = '1eb84df52aa580d8ee52a3b04a41120d372e78528b4a128aae87c68628ec83b9'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def same(a, b, label):
    assert a.mode == b.mode and a.size == b.size, label
    assert a.tobytes() == b.tobytes(), label


def original_mask(bits, width):
    raw = bytes.fromhex(bits)
    assert len(raw) == width * 15 // 8
    return Image.frombytes('1', (width, 15), raw).convert('L')


def validate_compositor():
    """核對Pillow整數混合，避免把C實作的四捨五入當成未驗證假設。"""
    old = Image.frombytes('L', (256, 256), bytes(range(256)) * 256)
    alpha = Image.frombytes('L', (256, 256), bytes(a for a in range(256) for _ in range(256)))
    for fg in (0, 85, 170, 255):
        got = Image.composite(Image.new('L', old.size, fg), old, alpha).tobytes()
        want = bytes((fg*a + v*(255-a) + 127)//255 for a in range(256) for v in range(256))
        assert got == want, ('Pillow alpha rounding', fg)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    b = a.project/ROOT
    run = b/'owned-scene-r3'
    inputs_dir = b/'owned-inputs-r1'
    result = load(run/'owned-result.json')
    provenance = load(run/'provenance.json')
    assert provenance['tool_sha256'] == sha(run/'tool-at-run.go') == sha(a.project/'tools/research-ending-owned.go')
    assert provenance['binary_sha256'] == sha(b/'ending-owned-r3')
    assert provenance['output_sha256'] == sha(run/'owned-result.json')
    assert result['production'] is False and result['steps'] == 142648289
    assert result['unknown_writes'] == {} and result['unimplemented'] == []
    assert result['flips'] == 1049 and result['frame_purity'] == 41
    assert result['counts'] == dict(ascii=13523, cjk=7789,
        **{'bitmap-4': 1320, 'bitmap-5': 953, 'bitmap-6': 1462, 'clear-15': 896,
           'copy-page-1-to-0': 1, 'native-full-frame-checked': 1050,
           'idempotent-or-empty-glyph': 13523})
    native = load(b/'observation-r4/source-observation.json')
    for key in ('file_ops', 'exec_log', 'steps', 'run_error', 'unimplemented'):
        assert result[key] == native[key], ('native control', key)
    assert sha(run/'final.state') == STATE == sha(b/'observation-r4/final.state')
    assert (run/'before.state').read_bytes() == (run/'after.state').read_bytes()
    inputs_path = inputs_dir/'inputs.json'
    assert sha(inputs_path) == result['inputs_sha256'] == '19497ef75d6a1eb26c8e5e07b806f4a4ccc1ceada43fb1710a7e850fdd7a6ef2'
    inputs = load(inputs_path)
    assert len(inputs['cjk']) == 127 and len(inputs['ascii']) == 256
    for name, expected in inputs['files'].items():
        assert sha(inputs_dir/name) == expected, name
    ram_path = b/'startup-r3/ram-00000-9ffff.bin'
    assert sha(ram_path) == inputs['source_ram_sha256']
    ram = ram_path.read_bytes()
    glyphs = {}
    for g in inputs['cjk']:
        i = g['index']
        assert bytes.fromhex(g['code']) == ram[0x7e40+0x448+2*i:0x7e40+0x44a+2*i]
        assert bytes.fromhex(g['code']).decode('big5', errors='strict') == g['character']
        assert bytes.fromhex(g['bits']) == ram[0x28ee+30*i:0x28ee+30*(i+1)]
        glyphs[('cjk', i)] = (g['character'], original_mask(g['bits'], 16))
    for i, bits in enumerate(inputs['ascii']):
        assert bytes.fromhex(bits) == ram[0x7e40+0x548+15*i:0x7e40+0x548+15*(i+1)]
        glyphs[('ascii', i)] = (chr(i), original_mask(bits, 8))
    catalog_path = b/'source.json'
    assert sha(catalog_path) == '6b30b1d4d9fd70045cb4842dd6c0301d0fb7bd899f65c3934ed5d1baf88c3cc8'
    records = {r['record_sha256']: r for r in load(catalog_path)['records'] if r['color_variant']}
    sources = {}
    for source in (run/'sources').glob('*.bin'):
        key = source.stem
        r = records[key]
        assert sha(source) == key == sha(b/r['native'])
        rgba = Image.open(b/r['image']).convert('RGBA')
        assert hashlib.sha256(rgba.tobytes()).hexdigest() == r['decoded_rgba_sha256']
        assert rgba.size == (r['width'], r['height'])
        colors = {(red, green, blue): i for i, (red, green, blue) in enumerate(EGA)}
        index = Image.frombytes('L', rgba.size, bytes(colors[pixel[:3]] for pixel in rgba.getdata()))
        mask = rgba.getchannel('A')
        assert set(mask.tobytes()) <= {0, 255}
        sources[key] = (r, index, mask, rgba)
    assert len(sources) == 30
    validate_compositor()
    snapshots = []
    native_checks = []
    for meta in result['samples']:
        path = run/meta['scene']
        snap = load(path)
        assert snap['sample'] == meta['sample'] and snap['step'] == meta['step']
        assert snap['stage'] == meta['stage'] and snap['glyphs'] == meta['glyphs']
        assert len(snap['ops']) == meta['ops']
        assert snap['palette'] == [list(c) for c in EGA]
        canvas = Image.new('L', (640, 200), 0)
        for op in snap['ops']:
            x, y, w, h = (op[k] for k in ('X', 'Y', 'W', 'H'))
            assert x >= 0 and y >= 0 and x+w <= 640 and y+h <= 200
            if op['kind'] == 'bitmap':
                r, index, mask, _ = sources[op['SourceSHA']]
                assert op['SourceFile'] == r['source_file'] and index.size == (w, h)
                canvas.paste(index, (x, y), mask)
            else:
                char, mask = glyphs[(op['kind'], op['Code'])]
                assert ord(char) == op['Char'] and mask.size == (w, h)
                assert 0 <= op['FG'] < 16 and (op['BG'] == 255 or 0 <= op['BG'] < 16)
                if op['BG'] != 255:
                    canvas.paste(op['BG'], (x, y, x+w, y+h))
                canvas.paste(op['FG'], (x, y), mask)
        prefix = run/path.stem
        assert canvas.tobytes() == prefix.with_suffix('.idx').read_bytes(), ('native indices', path.name)
        colored = Image.new('RGB', canvas.size)
        colored.putdata([EGA[i] for i in canvas.tobytes()])
        full = colored.convert('RGBA').resize((1920, 1200), Image.Resampling.NEAREST)
        native_path = prefix.with_name(prefix.name+'-source-native.png')
        same(full, Image.open(native_path).convert('RGBA'), ('native RGB', path.name))
        native_checks.append(dict(sample=snap['sample'], stage=snap['stage'],
            scene_sha256=sha(path), indices_sha256=sha(prefix.with_suffix('.idx')),
            image_sha256=sha(native_path), pixels=128000))
        snapshots.append(snap)
    assert len(snapshots) == 41
    selected = [next(s for s in snapshots if s['stage'] == stage and s['glyphs'] >= minimum)
                for stage, minimum in [('END5.AY', 1), ('END7.AY', 0), ('END8.AY', 0), ('END9.AY', 36)]]
    hd_checks = []
    for profile in inputs['profiles']:
        atlas = Image.open(inputs_dir/profile['atlas']).convert('RGBA').getchannel('A')
        font = {g['codepoint']: g for g in profile['glyphs']}
        title = Image.open(inputs_dir/('title-'+profile['id']+'.png')).convert('RGBA')
        # Go 1.24 image/draw.drawNRGBAOver onto opaque black, using its 16-bit intermediates.
        channels = [ImageMath.lambda_eval(lambda a: a['convert'](a['c']*a['a']*257/65280, 'L'),
                    c=c.convert('I'), a=title.getchannel('A').convert('I')) for c in title.split()[:3]]
        opaque_title = Image.merge('RGB', channels).convert('RGBA')
        end7 = Image.open(inputs_dir/'end7.png').convert('RGBA')
        masks = {}
        for snap in selected:
            out = Image.new('RGBA', (1920, 1200), EGA[0]+(255,))
            for op in snap['ops']:
                x, y, w, h = op['X']*3, op['Y']*6, op['W']*3, op['H']*6
                if op['kind'] == 'bitmap':
                    if op['SourceFile'] == 'END7.AY':
                        assert (x, y, w, h) == (0, 0, 1920, 1200)
                        out.paste(end7, (x, y))
                    elif op['SourceFile'] == 'END8.AY':
                        assert (w, h) == opaque_title.size
                        out.paste(opaque_title, (x, y))
                    else:
                        rgba = sources[op['SourceSHA']][3].resize((w, h), Image.Resampling.NEAREST)
                        out.paste(rgba, (x, y), rgba.getchannel('A'))
                    continue
                if op['BG'] != 255:
                    out.paste(EGA[op['BG']]+(255,), (x, y, x+w, y+h))
                if op['Char'] == 32:
                    continue
                key = op['Char'], w, h
                if key not in masks:
                    g = font[op['Char']]
                    gx, gy, iw, ih = g['ink']
                    dw, dh = min(w, iw), min(h, ih)
                    # Explicit edge-aligned integer sampling; Pillow NEAREST uses pixel centres.
                    mask = Image.frombytes('L', (dw, dh), bytes(atlas.getpixel((gx+px*iw//dw, gy+py*ih//dh))
                        for py in range(dh) for px in range(dw)))
                    masks[key] = mask
                mask = masks[key]
                dw, dh = mask.size
                out.paste(EGA[op['FG']]+(255,), (x+(w-dw)//2, y+(h-dh)//2), mask)
            path = run/('sample-%03d-%s.png' % (snap['sample'], profile['id']))
            same(out, Image.open(path).convert('RGBA'), ('HD RGB', path.name))
            hd_checks.append(dict(sample=snap['sample'], stage=snap['stage'], font=profile['id'],
                image_sha256=sha(path), pixels=out.width*out.height))
    report = dict(schema=1, spec='053', status='research-owned-source-verified', production=False,
        tool_sha256=sha(Path(__file__)), provenance_sha256=sha(run/'provenance.json'),
        run_sha256=sha(run/'owned-result.json'), inputs_sha256=sha(inputs_path),
        catalog_sha256=sha(catalog_path), original_final_state_sha256=STATE,
        file_ops_equal=True, exec_equal=True, frame_purity=41, native_page_checks=1050,
        unknown_writes={}, source_records=30, native_frames=native_checks, hd_frames=hd_checks,
        native_sample_pixels=sum(c['pixels'] for c in native_checks),
        hd_sample_pixels=sum(c['pixels'] for c in hd_checks), pillow=__version__,
        limits=['Standalone PAE diagnostic; no normal PAM handoff or natural completion.',
                'Original CPU pixel loops still execute; this proves source-only rendering, not direct loop replacement.',
                'Only ending text, END7 and END8 use new HD assets. Other ending art remains source pixels.',
                'No production promotion, GUI, save/reload or overall HD completion claim.'])
    with a.out.open('x') as f:
        f.write(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(native_frames=len(native_checks), hd_frames=len(hd_checks),
        native_pixels=report['native_sample_pixels'], hd_pixels=report['hd_sample_pixels'], sha256=sha(a.out))))


if __name__ == '__main__':
    main()
