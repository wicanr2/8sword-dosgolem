#!/usr/bin/env python3
"""052：審查16張透明器物圖並建立獨立快取與候選，不覆寫舊素材。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil

from PIL import Image, ImageDraw, ImageFont, __version__


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, obj):
    with path.open('x') as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=2)+'\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('project', 'batch', 'base', 'out', 'review'):
        p.add_argument('--'+key, required=True, type=Path)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and not a.review.exists()
    assert a.out.parent.stat().st_uid == a.review.parent.stat().st_uid == 1000
    request = json.loads((a.batch/'request.json').read_text())
    assert len(request['jobs']) == 16
    source = (a.project/'workplace/intake-20261023/sources/game/8sword/MAN.AY').read_bytes()
    assert sha(source) == request['source_sha256'] == '9849714498718f6616644ad717906cc426c3f3f5f335cdb99dbcc8173c8dbe12'
    assert len(source) == 22660
    spec = importlib.util.spec_from_file_location('sampler', a.project/'tools/audit-encounter-gui.py')
    sampler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sampler)
    base = {f.name:sha(f.read_bytes()) for f in a.base.iterdir()}
    assert len(base) == 391 and all(f.is_file() and not f.is_symlink() and f.stat().st_uid == 1000 for f in a.base.iterdir())
    a.out.mkdir()
    a.review.mkdir()
    for name in base:
        os.link(a.base/name, a.out/name)
    entries, receipts = [], []
    font = ImageFont.truetype(str(a.project/'workplace/probe-20261023/graphics-first/font-settings-r1/NotoSansCJK-Black.ttc'), 18, index=3)
    sheet = Image.new('RGB', (1280, 848), '#172b2d')
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 8), 'MAN器物與武器：每格左原版／右HD；素材圖集，非自然取得畫面', font=font, fill='#f1d69b')
    for slot, job in enumerate(request['jobs']):
        i = job['index']
        variant = 2 if i in [16,21,22,23,24,25,26,27,28] else 1
        receipt_path = a.batch/f'man-{i:02d}-r{variant}.json'
        receipt = json.loads(receipt_path.read_text())
        assert receipt['index'] == i and receipt['tool'] == 'built-in image_gen' and receipt['alpha_extrema'] == [0,255]
        assert receipt['tool_sha256'] == sha((a.project/'tools/save-man-icon.py').read_bytes())
        raw = source[job['offset']:job['offset']+388]
        assert raw[:4] == bytes((4,0,16,0)) and sha(raw) == job['record_sha256'] == receipt['record_sha256']
        assert sha(raw[:260]) == job['native_sha256'] == receipt['native_sha256']
        for name, key in [('image','image_sha256'),('prompt','prompt_sha256'),('reference','reference_sha256')]:
            assert sha((a.batch/receipt[name]).read_bytes()) == receipt[key]
        image = Image.open(a.batch/receipt['image']).convert('RGBA')
        assert image.size == (receipt['width'],receipt['height']) and image.getchannel('A').getextrema() == (0,255)
        cache = sampler.sample(a.batch/receipt['image'],96,96,actor=True)
        (a.review/f'man-{i:02d}.rgba').write_bytes(cache)
        (a.review/f'man-{i:02d}-native.bin').write_bytes(raw)
        for name in ('image','prompt'):
            shutil.copyfile(a.batch/receipt[name],a.out/receipt[name])
        entries.append(dict(source_index=i,offset=job['offset'],native_sha256=job['native_sha256'],record_sha256=job['record_sha256'],
                            cache_sha256=sha(cache),prompt_file=receipt['prompt'],prompt_sha256=receipt['prompt_sha256'],
                            image=dict(source_index=851+slot,file=receipt['image'],sha256=receipt['image_sha256'],
                                       width=image.width,height=image.height,sampling='bitmap')))
        receipts.append(dict(index=i,variant=variant,receipt=receipt_path.name,receipt_sha256=sha(receipt_path.read_bytes())))
        x,y=(slot%4)*320+8,(slot//4)*200+48
        draw.text((x,y),f'MAN {i:02d}   原版 / HD',font=font,fill='#f1d69b')
        original=Image.open(a.batch/job['reference']).convert('RGBA').resize((144,144),Image.Resampling.NEAREST)
        hd=Image.frombytes('RGBA',(96,96),cache).resize((144,144),Image.Resampling.NEAREST)
        # Runtime caches are premultiplied; composite those bytes directly.
        for pic,px,premult in [(original,x,False),(hd,x+152,True)]:
            if not premult:
                back=Image.new('RGBA',pic.size,'#172b2d');back.alpha_composite(pic);sheet.paste(back.convert('RGB'),(px,y+28))
            else:
                data=bytearray(pic.tobytes());bg=(23,43,45)
                for at in range(0,len(data),4):
                    alpha=data[at+3]
                    for c in range(3):data[at+c]=min(255,data[at+c]+(bg[c]*(255-alpha)+127)//255)
                    data[at+3]=255
                sheet.paste(Image.frombytes('RGBA',pic.size,bytes(data)).convert('RGB'),(px,y+28))
    assert len({e['native_sha256'] for e in entries}) == 16
    manifest = dict(schema=1,source_file='MAN.AY',source_sha256=request['source_sha256'],style='B-bright-painted-r1',
                    style_reference_sha256='2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6',
                    sampling='bilinear-full-premultiplied-alpha-lte3',entries=entries)
    write(a.out/'man-items.json',manifest)
    sheet.save(a.review/'comparison.png')
    report = dict(schema=1,spec='052',status='candidate-registration-review',production=False,config=manifest,
                  manifest_sha256=sha((a.out/'man-items.json').read_bytes()),base_files=base,candidate_files=425,preserved_files=391,
                  request_sha256=sha((a.batch/'request.json').read_bytes()),generation_receipts=receipts,
                  comparison_sha256=sha((a.review/'comparison.png').read_bytes()),tool_sha256=sha(Path(__file__).read_bytes()),
                  pillow=__version__,rights=request['rights'])
    write(a.out/'man-items-provenance.json',report)
    write(a.review/'registration.json',report)
    assert len(list(a.out.iterdir())) == 425 and all(sha((a.out/n).read_bytes())==v for n,v in base.items())
    print(json.dumps(dict(images=16,files=425,preserved=391,manifest_sha256=report['manifest_sha256'],registration_sha256=sha((a.review/'registration.json').read_bytes()))))


if __name__ == '__main__':
    main()
