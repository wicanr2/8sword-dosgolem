#!/usr/bin/env python3
"""053：整理已驗八劍原版／HD及同狀態Engine Frame，完整原圖留本機。"""
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
    assert audit['status'] == 'PASS-scoped-053-ending-swords'
    r = a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    fontpath = a.project/'workplace/probe-20261023/graphics-first/font-settings-r1/NotoSansCJK-Black.ttc'
    assert sha(fontpath) == '3cffb10242b4b7e6edd439ebf3bd7e392345525e093ea08149e0a0158a1b5151'
    font = ImageFont.truetype(str(fontpath),24,index=3)
    out = Image.new('RGB',(1280,944),'#111722')
    draw = ImageDraw.Draw(out)
    for x,label in [(20,'原版八劍'),(660,'HD八劍，保留原配色與排列')]:
        draw.text((x,10),label,font=font,fill='#ead4a0')
    source = r/'end3-ay-00-reference.png'
    target = r/'assets-swords-candidate-r3/ending-swords.png'
    for x,path in [(56,source),(696,target)]:
        im = Image.open(path).convert('RGBA').resize((528,420),Image.Resampling.NEAREST if path==source else Image.Resampling.LANCZOS)
        tile = Image.new('RGBA',im.size,(0,0,0,255));tile.alpha_composite(im)
        out.paste(tile.convert('RGB'),(x,54))
    for x,label in [(20,'相同狀態的原版來源重建'),(660,'實際Go畫布，僅本組八劍換HD')]:
        draw.text((x,494),label,font=font,fill='#ead4a0')
    framepaths = [r/'runtime-swords-r1/hd'/('sample-01-'+v+'.png') for v in ['native','noto']]
    assert sha(framepaths[1]) == next(f['image_sha256'] for f in audit['frames'] if f['font']=='noto')
    for x,path in zip([20,660],framepaths):
        out.paste(Image.open(path).convert('RGB').resize((600,375),Image.Resampling.LANCZOS),(x,540))
    out.save(a.out)
    generation = json.loads((r/'swords-art-r1/generation-r2.json').read_text())
    report = dict(schema=1,spec='053',image=a.out.name,image_sha256=sha(a.out),audit_sha256=sha(a.audit),
                  source_sha256=sha(source),runtime_frames={str(p.relative_to(a.project)):sha(p) for p in framepaths},
                  generation=generation,initial_prompt=(r/'swords-art-r1/actual.prompt.txt').read_text(),
                  cleanup_prompt=(r/'swords-art-r1/cleanup-r2.prompt.txt').read_text(),tool_sha256=sha(Path(__file__)),
                  scope='Verified source/HD textures and same-state Engine Frame. Other characters remain source pixels; no new GUI or natural-victory claim.')
    with a.out.with_suffix('.json').open('x') as f:
        f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(sha(a.out))


if __name__ == '__main__':
    main()
