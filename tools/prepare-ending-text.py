#!/usr/bin/env python3
"""053 DRAFT：從原版實際字串建立三種結局字圖候選，不改正式字集。Docker only。"""
import argparse
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, __version__


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    root = a.project/'workplace/probe-20261023/graphics-first'
    observation = root/'ending-hd-r1/observation-r2/source-observation.json'
    assert sha(observation) == '0ba72e546be276b8c6755046c4776fb8e42fa8a34d18f39108ff3f859f2cf1b2'
    observed = json.loads(observation.read_text())
    assert len(observed['strings']) == 1134 and observed['checked_native_pixels'] == 348584
    rows = [dict(**row, text=bytes.fromhex(row['raw_hex']).decode('big5', errors='strict')) for row in observed['strings']]
    chars = sorted(set(''.join(row['text'] for row in rows)))
    assert len(chars) == 128 and len({row['text'] for row in rows}) == 95
    existing = set()
    for name in ('font.json', 'story.json'):
        m = json.loads((a.project/'workplace/player/assets-painted-r56'/name).read_text())
        existing.update(row['character'] for row in m['glyphs'])
    missing = ''.join(sorted(set(chars)-existing))
    assert missing == '們做健傷先吧展屬我敢更正當算萬謝辰陰難須'
    fonts = root/'font-settings-r1'
    inputs = {
        'black': ('NotoSansCJK-Black.ttc', '3cffb10242b4b7e6edd439ebf3bd7e392345525e093ea08149e0a0158a1b5151', 3),
        'serif': ('NotoSerifCJK-Regular.ttc', '93069d8e9e45d515cc421c971a79e6a5777704b348e36a9ef86578bf58adef77', 3),
        'lishu': ('TW-MOE-Li-3.00.ttf', 'f0ba5eda31727ad89cc0b1f6b9a7dfda02f061fa101c18548b6f8ea0145c108b', 0),
        'caoshu': ('LiuJianMaoCao-Regular.ttf', 'cab396b91a5b7c0b4005a35891180d06e6751f5ac261fe680aec65c1ae209033', 0),
    }
    faces = {}
    for name, (file, expected, index) in inputs.items():
        assert sha(fonts/file) == expected
        faces[name] = ImageFont.truetype(str(fonts/file), 48, index=index)
    assert faces['lishu'].getname() == ('TW-MOE-Li', 'Regular')
    invalid = {name: (m.size, bytes(m)) for name, f in faces.items() for m in [f.getmask('\U0010ffff')]}
    def supports(name, char):
        mask = faces[name].getmask(char)
        return (mask.size, bytes(mask)) != invalid[name] and bool(mask.getbbox())
    a.out.mkdir()
    profiles = []
    atlases = {}
    for ident in ('noto', 'lishu', 'caoshu'):
        atlas = Image.new('RGBA', (1024, 512))
        glyphs = []
        for i, char in enumerate(chars):
            cjk = 0x3400 <= ord(char) <= 0x9fff
            face = ident if ident != 'noto' and cjk and supports(ident, char) else 'serif' if ident != 'noto' and cjk else 'black'
            assert char == ' ' or supports(face, char), (ident, char, face)
            font = faces[face]
            box = font.getbbox(char)
            ink = Image.new('RGBA', (max(1, box[2]-box[0]), max(1, box[3]-box[1])))
            ImageDraw.Draw(ink).text((-box[0], -box[1]), char, font=font, fill='white')
            ink.thumbnail((48, 56), Image.Resampling.LANCZOS)
            x, y = i%16*64, i//16*64
            ox, oy = x+(64-ink.width)//2, y+(64-ink.height)//2
            atlas.paste(ink, (ox, oy))
            glyphs.append(dict(character=char, codepoint=ord(char), cell=[x,y,64,64], ink=[ox,oy,ink.width,ink.height], face=face))
        filename = 'ending-font-'+ident+'.png'
        atlas.save(a.out/filename)
        profiles.append(dict(id=ident, atlas=filename, atlas_sha256=sha(a.out/filename), width=1024, height=512,
                             glyphs=glyphs, serif_fallback=[g['character'] for g in glyphs if g['face']=='serif']))
        atlases[ident] = atlas
    # A font specimen, not an original scene or a runtime screenshot.
    specimen = ['企 劃 ／ 程 式 設 計 ： 楊    第', '電    腦    繪    圖 ： 張 崑 耀', '    謝 謝 您 使 用 本 軟 體', '  身 體 健 康 ， 萬 事 如 意']
    assert set(specimen) <= {row['text'] for row in rows}
    preview = Image.new('RGBA', (1280, 1340), (17, 32, 38, 255))
    label = ImageFont.truetype(str(fonts/inputs['black'][0]), 28, index=3)
    draw = ImageDraw.Draw(preview)
    draw.text((20, 12), '結局文字候選：保留原字與空格，尚未接入', font=label, fill='#f2d28b')
    for index, profile in enumerate(profiles):
        y = 64+index*420
        draw.text((20, y), {'noto':'Noto Black 900','lishu':'教育部隸書','caoshu':'劉建毛草'}[profile['id']], font=label, fill='white')
        glyphs = {g['character']:g for g in profile['glyphs']}
        for line, text in enumerate(specimen):
            x = 32
            for char in text:
                g = glyphs[char]
                ix, iy, w, h = g['ink']
                width = 48 if 0x3400 <= ord(char) <= 0x9fff or ord(char) > 127 else 24
                if char != ' ':
                    ink = atlases[profile['id']].crop((ix,iy,ix+w,iy+h))
                    preview.alpha_composite(ink, (x+(width-w)//2,y+40+line*90+(90-h)//2))
                x += width
            assert x <= preview.width-24
    preview.convert('RGB').save(a.out/'ending-text-specimen-r1.png')
    write(a.out/'text-catalog.json', dict(schema=1, encoding='Big5 strict', observation_sha256=sha(observation),
                                       occurrences=rows, unique_texts=95, characters=''.join(chars), added_to_union=missing))
    report = dict(schema=1, spec='053', status='candidate-font-caches-not-runtime', production=False,
                  profiles=profiles, source_characters=128, observed_calls=1134, existing_union_missing=missing,
                  text_catalog_sha256=sha(a.out/'text-catalog.json'), observation_sha256=sha(observation),
                  font_sources={name:dict(file=file,sha256=expected,index=index) for name,(file,expected,index) in inputs.items()},
                  preview='ending-text-specimen-r1.png', preview_sha256=sha(a.out/'ending-text-specimen-r1.png'),
                  tool_sha256=sha(Path(__file__)), pillow=__version__,
                  rights='Local font rendering caches. MOE TTF remains unmodified; attribution and CC-BY-ND-3.0-TW contract follow spec015. Noto and LiuJianMaoCao use OFL.',
                  limits=['Original Big5 byte decoding and complete glyph availability only; ending rendering and font switching not integrated.'])
    write(a.out/'ending-fonts.json', report)
    print(json.dumps(dict(characters=128, added_to_union=missing, profiles=[dict(id=p['id'],serif_fallback=p['serif_fallback']) for p in profiles],manifest_sha256=sha(a.out/'ending-fonts.json')),ensure_ascii=False))


if __name__ == '__main__':
    main()
