#!/usr/bin/env python3
"""053：準備END2三組參考圖，或匯入三組手繪透明圖。Docker only。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
from PIL import Image, __version__


GROUPS = [('ground',[0,1,2],1,3,480,198),('flow',[3,4,5],3,1,216,336),('burst',[6,7,8,9,10],3,2,288,240)]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p,data):
    with p.open('x') as f:
        f.write(json.dumps(data,ensure_ascii=False,indent=2)+'\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['references','import'])
    for name in ['project','out']:
        p.add_argument('--'+name,type=Path,required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    root = a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    original = a.project/'workplace/intake-20261023/sources/game/8sword/END2.AY'
    assert sha(original) == 'c079973aaf332f8a30a5b4c905049d826cb1031aa568a766f60cf051c2f78d8c'
    records = [v for v in json.loads((root/'source.json').read_text())['records'] if v['source_file']=='END2.AY']
    assert [v['record'] for v in records] == list(range(11))
    for row in records:
        im = Image.open(root/row['image']).convert('RGBA')
        assert hashlib.sha256(im.tobytes()).hexdigest() == row['decoded_rgba_sha256']
        # Source masks only add coloured pixels; they do not erase with black.
        assert all(pixel != (0,0,0,255) for pixel in im.getdata())
    a.out.mkdir()
    if a.mode == 'references':
        groups = []
        for name,ids,cols,rows,w,h in GROUPS:
            sheet = Image.new('RGBA',(cols*w,rows*h),(0,0,0,0))
            for cell,index in enumerate(ids):
                im = Image.open(root/records[index]['image']).convert('RGBA').resize((w,h),Image.Resampling.NEAREST)
                sheet.paste(im,(cell%cols*w,cell//cols*h))
            target = a.out/(name+'-reference.png');sheet.save(target)
            groups.append(dict(name=name,records=ids,columns=cols,rows=rows,cell=[w,h],image=target.name,sha256=sha(target)))
        write(a.out/'references-r1.json',dict(schema=1,spec='053',groups=groups,records=records,source_sha256=sha(original),tool_sha256=sha(Path(__file__))))
        print(json.dumps(dict(groups=3,records=11)))
        return
    batch = root/'effects-art-r1'
    base = a.project/'workplace/player/assets-painted-r61'
    assert len(list(base.iterdir())) == 443
    old = {}
    for f in sorted(base.iterdir()):
        assert f.is_file() and not f.is_symlink() and f.stat().st_uid == 1000
        old[f.name] = sha(f);shutil.copyfile(f,a.out/f.name)
    textures, generations = [], {}
    for name,ids,cols,rows,w,h in GROUPS:
        version = 'r3' if name == 'burst' else 'r1'
        genpath = batch/(name+'-generation-'+version+'.json')
        gen = json.loads(genpath.read_text())
        assert gen['tool'] == 'built-in image_gen' and gen['transparent_background'] is True
        assert sha(batch/gen['image']) == gen['image_sha256'] and sha(batch/gen['prompt']) == gen['prompt_sha256']
        assert sha(batch/gen['reference']) == gen['reference_sha256']
        raw = Image.open(batch/gen['image']).convert('RGBA')
        lo, hi = raw.getchannel('A').getextrema()
        assert lo == 0 and hi > 0
        sheet = raw.resize((cols*w,rows*h),Image.Resampling.LANCZOS)
        for cell,index in enumerate(ids):
            x,y = cell%cols*w,cell//cols*h
            im = sheet.crop((x,y,x+w,y+h))
            lo, hi = im.getchannel('A').getextrema()
            assert lo == 0 and hi > 0
            filename = f'ending-effect-{index:02d}.png';im.save(a.out/filename)
            textures.append(dict(record=index,source_sha256=records[index]['record_sha256'],image=filename,
                                 image_sha256=sha(a.out/filename),width=w,height=h))
        generations[name] = sha(genpath)
    manifest = dict(schema=1,source_file='END2.AY',original_sha256=sha(original),records=textures)
    write(a.out/'ending-effects.json',manifest)
    report = dict(schema=1,spec='053',status='effects-candidate-not-promoted',files=455,preserved_files=443,
                  base_files=old,manifest=manifest,manifest_sha256=sha(a.out/'ending-effects.json'),
                  generations=generations,tool_sha256=sha(Path(__file__)))
    write(a.out.parent/'effects-registration-r1.json',report)
    print(json.dumps(dict(files=455,preserved=443,manifest_sha256=report['manifest_sha256'])))


if __name__ == '__main__':
    main()
