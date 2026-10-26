#!/usr/bin/env python3
"""053：保存END7原始生成圖，核對END8與開場標題的共用字圖。Docker only。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

from PIL import Image, ImageDraw, ImageFont, __version__


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('project', 'batch', 'image', 'out'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not args.out.exists() and args.out.parent.stat().st_uid == args.batch.stat().st_uid == 1000
    source = json.loads((args.batch/'source.json').read_text())
    assert source['spec'] == '053' and len(source['records']) == 37
    row = next(r for r in source['records'] if r['source_file'] == 'END7.AY')
    assert row['record'] == 0 and row['width'] == 640 and row['height'] == 200 and row['planes'] == 4
    assert sha(args.batch/row['reference']) == row['reference_sha256']
    prompt = args.batch/'end7-r1.prompt.txt'
    assert prompt.is_file() and args.image.is_file()
    image = Image.open(args.image)
    assert image.format == 'PNG' and min(image.size) >= 512 and max(image.size) <= 4096
    assert image.convert('RGBA').getchannel('A').getextrema() == (255, 255)
    raw = args.batch/'end7-r1.png'
    assert not raw.exists()
    shutil.copyfile(args.image, raw)
    generation = dict(schema=1, spec='053', status='generated-not-registered', production=False,
                      tool='built-in image_gen', image=raw.name, image_sha256=sha(raw), size=list(image.size),
                      transparent_background=False, alpha_extrema=[255, 255], prompt=prompt.name,
                      prompt_sha256=sha(prompt), actual_prompt=prompt.read_text(), reference=row['reference'],
                      reference_sha256=row['reference_sha256'], source_file='END7.AY',
                      source_sha256=row['source_sha256'], decoded_sha256=row['record_sha256'],
                      source_receipt_sha256=sha(args.batch/'source.json'), tool_sha256=sha(Path(__file__)),
                      rights='original-derived candidate local only; no public distribution permission')
    write(args.batch/'end7-r1.json', generation)
    args.out.mkdir()
    # END8 is literally the same packed file and planar record as TIT2.
    root = args.project/'workplace/intake-20261023/sources/game/8sword'
    packed = (root/'END8.AY').read_bytes()
    assert packed == (root/'TIT2.AY').read_bytes()
    assert hashlib.sha256(packed).hexdigest() == 'ff31a0a4916ee1b27a56f2f7da32ec06df3716b42f831b547ed5518586f64060'
    native = args.batch/'end8-ay-00.bin'
    assert sha(native) == '5f62f595ac003c069acace22770cd71b99e14d48bdd43db671598f5320c74f65'
    assets = args.project/'workplace/player/assets-painted-r56'
    title = json.loads((assets/'intro.json').read_text())
    choices = json.loads((assets/'font-choices.json').read_text())
    assert title['source_sha256'] == sha(root/'END8.AY') and title['decoded_sha256'] == sha(native)
    assert title['text'] == '神州八劍' and title['weight'] == 900
    entries = [dict(id='noto', file=title['file'], sha256=title['sha256'], source_sha256=title['font_sha256'])]
    entries += [dict(id=p['id'], file=p['title'], sha256=p['title_sha256'], source_sha256=p['source_sha256'])
                for p in choices['profiles']]
    assert {e['id'] for e in entries} == {'noto', 'lishu', 'caoshu'}
    assert next(e for e in entries if e['id'] == 'lishu')['source_sha256'] == 'f0ba5eda31727ad89cc0b1f6b9a7dfda02f061fa101c18548b6f8ea0145c108b'
    fontpath = args.project/'workplace/probe-20261023/graphics-first/font-settings-r1/NotoSansCJK-Black.ttc'
    font = ImageFont.truetype(str(fontpath), 30, index=3)
    sheet = Image.new('RGB', (1280, 1290), '#112026')
    draw = ImageDraw.Draw(sheet)
    draw.text((22, 12), '結局素材候選：原版構圖／HD手繪', font=font, fill='#f2d28b')
    draw.text((22, 54), '尚未接入正式結局流程', font=font, fill='#ded7bf')
    def paste(art, rect):
        art = art.convert('RGBA')
        art.thumbnail((rect[2]-rect[0], rect[3]-rect[1]), Image.Resampling.LANCZOS)
        xy = (rect[0]+(rect[2]-rect[0]-art.width)//2, rect[1]+(rect[3]-rect[1]-art.height)//2)
        sheet.paste(art, xy, art)
    paste(Image.open(args.batch/row['reference']), (20, 110, 630, 500))
    paste(image, (650, 110, 1260, 500))
    draw.text((22, 516), 'END8與開場TIT2完全相同，沿用三種既有字圖', font=font, fill='#f2d28b')
    for i, entry in enumerate(entries):
        assert sha(assets/entry['file']) == entry['sha256']
        art = Image.open(assets/entry['file']).convert('RGBA')
        assert art.size == (1776, 570)
        bounds = art.getchannel('A').getbbox()
        assert bounds and 24 <= bounds[0] < bounds[2] <= 1752 and 24 <= bounds[1] < bounds[3] <= 546
        entry['ink_rect'] = list(bounds)
        shutil.copyfile(assets/entry['file'], args.out/entry['file'])
        y = 570+i*230
        draw.text((24, y), {'noto':'Noto Black 900', 'lishu':'教育部隸書', 'caoshu':'劉建毛草'}[entry['id']], font=font, fill='#ded7bf')
        paste(art, (340, y, 1250, y+215))
    sheet.save(args.out/'ending-candidates-r1.png')
    report = dict(schema=1, spec='053', status='art-and-title-candidates-not-runtime', production=False,
                  source_receipt_sha256=sha(args.batch/'source.json'), generation_sha256=sha(args.batch/'end7-r1.json'),
                  title_packed_equal=True, title_source_sha256=sha(root/'END8.AY'), title_decoded_sha256=sha(native),
                  title_profiles=entries, title_manifest_sha256=sha(assets/'intro.json'),
                  font_choices_sha256=sha(assets/'font-choices.json'),
                  comparison='ending-candidates-r1.png', comparison_sha256=sha(args.out/'ending-candidates-r1.png'),
                  tool_sha256=sha(Path(__file__)), pillow=__version__,
                  limits=['Candidate art and exact source identity only; no ending runtime hook or natural completion claim.'],
                  rights='full art and original references local only; compact comparison in existing private repository')
    write(args.out/'art-preparation-r1.json', report)
    print(json.dumps(dict(status=report['status'], raw_sha256=generation['image_sha256'], size=image.size,
                          profiles=[e['id'] for e in entries], receipt_sha256=sha(args.out/'art-preparation-r1.json'))))


if __name__ == '__main__':
    main()
