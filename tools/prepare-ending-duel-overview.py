#!/usr/bin/env python3
"""053：整理END1人物素材及初始／八劍階段的同狀態畫面。Docker only。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, __version__


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('project','audit','out'):
        p.add_argument('--'+name,type=Path,required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    audit = json.loads(a.audit.read_text())
    assert audit['status'] == 'PASS-scoped-053-ending-duel'
    root = a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    fontpath = a.project/'workplace/probe-20261023/graphics-first/font-settings-r1/NotoSansCJK-Black.ttc'
    assert sha(fontpath) == '3cffb10242b4b7e6edd439ebf3bd7e392345525e093ea08149e0a0158a1b5151'
    font = ImageFont.truetype(str(fontpath),24,index=3)
    out = Image.new('RGB',(1280,1128),'#111722')
    draw = ImageDraw.Draw(out)
    entries = []
    for x,caption,path in [(20,'原版對峙人物',root/'end1-ay-00-reference.png'),
                           (660,'HD人物，保留原版姿態與配色',root/'assets-duel-candidate-r1/ending-duel.png')]:
        draw.text((x,10),caption,font=font,fill='#ead4a0')
        out.paste(Image.open(path).convert('RGB').resize((600,176),Image.Resampling.NEAREST if x==20 else Image.Resampling.LANCZOS),(x,54))
        entries.append(dict(path=str(path.relative_to(a.project)),sha256=sha(path)))
    for row,stage,sample in [(0,'初始對峙','sample-01'),(1,'八劍出現後，法術仍用來源圖','sample-02')]:
        top = 260+row*426
        for x,profile,label in [(20,'native','原版來源重建'),(660,'noto','實際Go畫布')]:
            path = root/'runtime-duel-r1/hd'/(sample+'-'+profile+'.png')
            if profile != 'native':
                target = next(f for f in audit['frames'] if f['stage'] == ('END1.AY' if row==0 else 'END3.AY') and f['font']==profile)
                assert sha(path) == target['image_sha256']
            draw.text((x,top),stage+'／'+label,font=font,fill='#ead4a0')
            out.paste(Image.open(path).convert('RGB').resize((600,375),Image.Resampling.LANCZOS),(x,top+40))
            entries.append(dict(path=str(path.relative_to(a.project)),sha256=sha(path)))
    out.save(a.out)
    generation = json.loads((root/'end1-art-r1/generation-r1.json').read_text())
    report = dict(schema=1,spec='053',image=a.out.name,image_sha256=sha(a.out),audit_sha256=sha(a.audit),
                  entries=entries,generation=generation,prompt=(root/'end1-art-r1/actual.prompt.txt').read_text(),
                  tool_sha256=sha(Path(__file__)),scope='Source/HD textures and same-state Engine Frames. Original branch is controlled, not natural victory. No new GUI/save claim. END2 spell effects remain source pixels.')
    with a.out.with_suffix('.json').open('x') as f:
        f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(sha(a.out))


if __name__ == '__main__':
    main()
