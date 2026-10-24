"""041：重生正常同狀態的原版／HD 軍隊頁比較。Docker only。"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, __version__


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ['project','font','out']:
        ap.add_argument('--'+name,type=Path,required=True)
    a = ap.parse_args()
    assert not a.out.exists() and a.out.parent.is_dir()
    rel = Path('workplace/probe-20261023/graphics-first/battle-r1/army21-hd-r1')
    source = a.project/rel
    meta = json.loads((source/'02-dwarf-f2.json').read_text())
    assert meta['hd'] and not meta['army_man21_error'] and not meta['graphics_error']
    assert meta['font_id'] == 'noto' and 10580 in meta['visible_sources']
    images,inputs = [],[]
    for mode in ['native','hd']:
        p = source/f'02-dwarf-f2-{mode}.png'
        im = Image.open(p).convert('RGB')
        assert im.size == (1920,1200)
        images.append(im)
        inputs.append(dict(path=str(p.relative_to(a.project)),sha256=sha(p),mode=mode))
    out = Image.new('RGB',(1920,720),'#11251f')
    draw = ImageDraw.Draw(out)
    font = ImageFont.truetype(str(a.font),36,index=3)
    small = ImageFont.truetype(str(a.font),24,index=3)
    for i,(label,im) in enumerate(zip(['原版','HD'],images)):
        draw.text((i*960+24,8),label,font=font,fill='#fff1b5')
        out.paste(im.resize((960,600),Image.Resampling.NEAREST),(i*960,64))
    draw.text((24,675),'正常續玩的軍隊頁，兩側為同一原版狀態。',font=small,fill='#fff1b5')
    a.out.mkdir()
    png = a.out/'army-man21-original-hd-r1.png'
    out.save(png)
    record = dict(schema=1,spec='041',output=png.name,output_sha256=sha(png),inputs=inputs,
                  source_status=dict(path=str(rel/'02-dwarf-f2.json'),sha256=sha(source/'02-dwarf-f2.json')),
                  source_record=dict(file='MAN21.EGG',record=0,transform='mirror-six-planes',six_plane_sha256='5168810f892b3d4723a990d7c231f1a14801568166030fd9eef661140d937f30'),
                  step=meta['steps'],capture='normal original F7 Continue and F2; native VGA and HD captured without guest advance between images; actual GUI verified separately',
                  layout='same 1920x1200 viewport, both resized to 960x600 with nearest-neighbor',
                  tool=dict(pillow=__version__,script_sha256=sha(Path(__file__)),font_sha256=sha(a.font),font_index=3),
                  approval_basis='user requested original-versus-HD monster and battlefield overviews in README',
                  rights='comparison in existing private repository only; full original and HD packs remain local; no public distribution grant')
    (a.out/'army-man21-original-hd-r1.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(output=str(png),sha256=record['output_sha256'])))


if __name__ == '__main__':
    main()
