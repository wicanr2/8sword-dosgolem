#!/usr/bin/env python3
"""053 DRAFT：按原版幾何準備既有END5候選材質，不改原始生成PNG。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
from PIL import Image, ImageDraw, __version__


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    root = a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    inputs = {
        'base': ('c975bd28029b627dd043389583a70ca8a46896110fe30c62e5f2fd9d5a243fa2',(2243,701),(0,0,2243,701)),
        'blink': ('95f0ff09dd7dcf63ee2de6936793a435dbf64740f05e7ee4637bc4b180287379',(2171,724),(0,23,2171,703)),
        'speech': ('d6fb1269dfce807bacd9a20c9c0ed2e6b3a88413e2b334133eaea0771ed882af',(2171,724),(0,21,2171,703)),
    }
    normal = {}
    provenance = {}
    for name,(digest,size,rect) in inputs.items():
        f = root/('end5-'+name+'-r1.png')
        assert sha(f) == digest
        record = json.loads((root/('end5-'+name+'-r1.json')).read_text())
        assert record['image_sha256'] == digest and sha(root/record['prompt']) == record['prompt_sha256']
        im = Image.open(f).convert('RGBA')
        assert im.size == size and im.getchannel('A').getextrema() == (255,255)
        normal[name] = im.crop(rect).resize((1920,600),Image.Resampling.LANCZOS)
        provenance[name] = dict(image=f.name,sha256=digest,size=size,source_rect=rect,
                                generation_receipt_sha256=sha(root/('end5-'+name+'-r1.json')),
                                prompt=record['prompt'],prompt_sha256=record['prompt_sha256'])
    catalog = json.loads((root/'source.json').read_text())
    sources = sorted([r for r in catalog['records'] if r['source_file'] == 'END5.AY'],key=lambda r:r['record'])
    assert len(sources) == 5 and [(r['width'],r['height'],r['planes']) for r in sources] == [(640,100,5),(64,30,5),(64,30,5),(40,15,5),(40,15,5)]
    a.out.mkdir()
    textures = [normal['base'],normal['base'].crop((1464,108,1656,288)),normal['blink'].crop((1464,108,1656,288)),
                normal['speech'].crop((1488,390,1608,480)),normal['base'].crop((1488,390,1608,480))]
    records = []
    positions = [(0,50),(488,68),(488,68),(496,115),(496,115)]
    for i,(source,im) in enumerate(zip(sources,textures)):
        assert sha(root/source['native']) == source['record_sha256']
        filename = 'ending-end5-'+str(i)+'.png'
        im.save(a.out/filename)
        records.append(dict(record=i,source_sha256=source['record_sha256'],source_file='END5.AY',file=filename,
                            sha256=sha(a.out/filename),size=list(im.size),position=positions[i],native_size=[source['width'],source['height']]))
    previews = []
    for eye,mouth,label in [(1,4,'open / rest'),(2,4,'blink / rest'),(1,3,'open / speech'),(2,3,'blink / speech')]:
        im = textures[0].copy()
        im.paste(textures[eye],(1464,108))
        im.paste(textures[mouth],(1488,390))
        im.save(a.out/('preview-'+str(eye)+'-'+str(mouth)+'.png'))
        previews.append((im,label))
    sheet = Image.new('RGB',(1920,4*342),'#132027')
    draw = ImageDraw.Draw(sheet)
    for i,(im,label) in enumerate(previews):
        draw.text((12,i*342+8),label,fill='white')
        small = im.resize((960,300),Image.Resampling.LANCZOS).convert('RGB')
        sheet.paste(small,(0,i*342+30))
        eye = im.crop((1410,60,1710,330)).resize((300,270),Image.Resampling.NEAREST)
        mouth = im.crop((1458,360,1638,510)).resize((300,250),Image.Resampling.NEAREST)
        sheet.paste(eye,(1000,i*342+30));sheet.paste(mouth,(1380,i*342+30))
    sheet.save(a.out/'registration-preview.png')
    result = dict(schema=1,spec='053',production=False,status='geometry-prototype-not-registered',inputs=provenance,records=records,
                  source_receipt_sha256=sha(root/'source.json'),tool_sha256=sha(Path(__file__)),pillow=__version__,
                  comparison='registration-preview.png',comparison_sha256=sha(a.out/'registration-preview.png'),
                  limits=['Existing image_gen paintings are unchanged; fixed source rectangles remove generated letterbox padding.',
                          'No runtime hook, source-geometry or animation timing change. Material seams require inspection.'])
    (a.out/'registration.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(records=5,comparison=result['comparison'],sha256=sha(a.out/'registration.json'))))


if __name__ == '__main__':
    main()
