"""039：從真正視窗 Draw 的相同原版狀態重生 README 比較圖。Docker only。"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, __version__


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ['project', 'font', 'out']:
        ap.add_argument('--'+name, type=Path, required=True)
    a = ap.parse_args()
    assert not a.out.exists() and a.out.parent.is_dir()
    rel = Path('workplace/player/gui/encounter7-save-r3/save/research-encounter-draws/record-07-height-25-font-noto-first-draw')
    prefix = a.project/rel
    path = lambda suffix: Path(str(prefix)+suffix)
    meta = json.loads(path('.json').read_text())
    assert (meta['record'], meta['height'], meta['font_id']) == (7, 25, 'noto')
    assert sha(path('-before.state')) == sha(path('-after.state'))
    raw = path('-native.idx').read_bytes()
    assert len(raw) == 128000 and max(raw) < 16
    palette = meta['display']['Palette']
    native = Image.frombytes('RGB', (640, 200), bytes(c for index in raw for c in palette[index]))
    native = native.resize((1920, 1200), Image.Resampling.NEAREST)
    hd = Image.open(path('.png')).convert('RGB')
    assert hd.size == native.size
    font = ImageFont.truetype(str(a.font), 36, index=3)
    small = ImageFont.truetype(str(a.font), 24, index=3)
    out = Image.new('RGB', (1920, 720), '#11251f')
    draw = ImageDraw.Draw(out)
    for i, (label, im) in enumerate(zip(['原版', 'HD'], [native, hd])):
        draw.text((i*960+24, 8), label, font=font, fill='#fff1b5')
        out.paste(im.resize((960, 600), Image.Resampling.NEAREST), (i*960, 64))
    draw.text((24, 675), '實際視窗的同一客體狀態，保留原版粉紅配色與出場高度。', font=small, fill='#fff1b5')
    a.out.mkdir()
    png = a.out/'map-encounter-7-original-hd-r1.png'
    out.save(png)
    record = dict(schema=1, spec='039', output=png.name, output_sha256=sha(png),
                  actual_draw=meta['actual_draw'], step=meta['step'],
                  source_record=dict(file='ENEMY.AY', record=7, transform='mirror-six-planes'),
                  inputs=[dict(path=str(Path(str(rel)+suffix)), sha256=sha(path(suffix))) for suffix in ['.json', '.png', '-native.idx', '-before.state', '-after.state']],
                  capture='same actual Draw; native VGA indexes and palette reconstructed independently; no guest advance between sides',
                  layout='same central viewport, nearest-neighbor resize to 960x600 on both sides',
                  tool=dict(pillow=__version__, script_sha256=sha(Path(__file__)), font_sha256=sha(a.font), font_index=3),
                  approval_basis='user requested original-versus-HD monster and battlefield overviews in README',
                  rights='requested comparison in existing private repository only; no public distribution grant; full sprites and packs remain local')
    (a.out/'map-encounter-7-original-hd-r1.json').write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(output=str(png), sha256=record['output_sha256'])))


if __name__ == '__main__':
    main()
