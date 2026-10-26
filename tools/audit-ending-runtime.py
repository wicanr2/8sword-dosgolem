#!/usr/bin/env python3
"""053 DRAFT：獨立核對PAE原版來源、隱藏頁色碼、觀測隔離與字集候選。Docker only。"""
import argparse
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, __version__


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
    project = a.project
    batch = project/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    current = batch/'observation-r3'
    observed = read(current/'source-observation.json')
    previous = read(batch/'observation-r2/source-observation.json')
    assert observed['steps'] == 142648289 and not observed['unimplemented'] and not observed['guest_patches']
    assert observed['bitmap_calls'] == previous['bitmap_calls'] and observed['strings'] == previous['strings']
    assert len(observed['bitmap_calls']) == 3735 and len(observed['strings']) == 1134
    state = sha(batch/'startup-r4/final.state')
    for name in ('observation-r1', 'observation-r2', 'observation-r3'):
        assert sha(batch/name/'final.state') == state
    control_ops = sum([read(batch/f'startup-r{i}/source-startup.json')['file_ops'] for i in (2, 3, 4)], [])
    assert observed['file_ops'] == control_ops
    sources = read(batch/'source.json')
    by_hash = {row['record_sha256']:row for row in sources['records']}
    palette = [(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),(170,85,0),(170,170,170),
               (85,85,85),(85,85,255),(85,255,85),(85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]
    checked, total = set(), 0
    for sample in observed['source_return_samples']:
        key = sample['source_sha256']
        assert key not in checked
        checked.add(key)
        row = by_hash[key]
        assert sha(current/'sources'/f'{key}.bin') == sha(batch/row['native']) == key
        native = (current/sample['native_indices']).read_bytes()
        assert len(native) == 128000 and sha(current/sample['native_indices']) == sample['native_indices_sha256']
        assert sample['destination'] in (0xa000, 0xa400)
        assert sample['plane_byte_start'] == (sample['destination']-0xa000)*16
        original = Image.open(batch/row['image']).convert('RGBA')
        assert hashlib.sha256(original.tobytes()).hexdigest() == row['decoded_rgba_sha256']
        x, y, w, h = sample['xywh']
        assert original.size == (w, h)
        written = 0
        for yy in range(h):
            for xx in range(w):
                expected = original.getpixel((xx, yy))
                if expected[3] == 0:
                    continue
                assert palette[native[(y+yy)*640+x+xx]] == expected[:3], (key,xx,yy)
                written += 1
        assert written == sample['written_pixels']
        total += written
    assert len(checked) == observed['unique_sources'] == 30 and total == observed['checked_native_pixels'] == 348584
    missing = sorted(f"{row['source_file']}#{row['record']}" for row in sources['records'] if row['color_variant'] and row['record_sha256'] not in checked)
    assert missing == ['END2.AY#3', 'END2.AY#4', 'END2.AY#5']
    preparation = read(batch/'runtime-analysis-r1/preparation.json')
    image = (batch/'runtime-analysis-r1/PAE-runtime-analysis.exe').read_bytes()
    assert hashlib.sha256(image).hexdigest() == preparation['wrapper_sha256']
    ida_root = batch/'runtime-analysis-r1/ida-r2'
    ida = read(ida_root/'ida-runtime-r2.json')
    assert ida['tool'] == 'IDA 9.4' and ida['uid'] == 1000 and ida['function_count'] == 163
    assert ida['source_sha256'] == preparation['wrapper_sha256']
    assert ida['tool_sha256'] == sha(project/'tools/export-ending-runtime-ida.py')
    lines = 0
    for body in ida['bodies']:
        for line in body['lines']:
            raw = bytes.fromhex(line['bytes'])
            at = line['ida_linear']-0x1100+32
            assert line['wrapper_file_offset'] == at and image[at:at+len(raw)] == raw
            lines += 1
    fonts_root = batch/'text-candidates-r1'
    fonts = read(fonts_root/'ending-fonts.json')
    catalog = read(fonts_root/'text-catalog.json')
    assert fonts['tool_sha256'] == sha(project/'tools/prepare-ending-text.py')
    assert fonts['text_catalog_sha256'] == sha(fonts_root/'text-catalog.json')
    assert catalog['occurrences'] == [dict(**r,text=bytes.fromhex(r['raw_hex']).decode('big5')) for r in observed['strings']]
    chars = set(catalog['characters'])
    assert len(chars) == fonts['source_characters'] == 128
    assert fonts['existing_union_missing'] == '們做健傷先吧展屬我敢更正當算萬謝辰陰難須'
    for profile in fonts['profiles']:
        assert sha(fonts_root/profile['atlas']) == profile['atlas_sha256']
        atlas = Image.open(fonts_root/profile['atlas']).convert('RGBA')
        assert atlas.size == (1024,512) and {g['character'] for g in profile['glyphs']} == chars
        for g in profile['glyphs']:
            x,y,w,h = g['ink']
            cx,cy,cw,ch = g['cell']
            assert 0 <= cx <= x < x+w <= cx+cw <= 1024 and 0 <= cy <= y < y+h <= cy+ch <= 512
            if g['character'] != ' ':
                assert atlas.crop((x,y,x+w,y+h)).getchannel('A').getbbox()
    result = dict(schema=1, spec='053', status='PASS-original-source-and-text-candidate', production=False,
                  bitmap_calls=3735, native_sources=30, checked_native_pixels=total, observed_string_calls=1134,
                  final_state_sha256=state, unobserved_color_records=missing, ida_functions=163, ida_lines_checked=lines,
                  candidate_characters=128, font_profiles=3, observation_sha256=sha(current/'source-observation.json'),
                  ida_sha256=sha(ida_root/'ida-runtime-r2.json'), font_manifest_sha256=sha(fonts_root/'ending-fonts.json'),
                  tool_sha256=sha(Path(__file__)),
                  limits=['Standalone diagnostic with fixed command tail, not natural PAM handoff or player completion.',
                          'Native source written pixels on actual destination pages only; no preserved transparent-pixel or HD scene claim.',
                          'Font caches are candidates; original glyph interpretation, scene ownership and font switching remain to integrate.'])
    with a.out.open('x') as f:
        f.write(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
