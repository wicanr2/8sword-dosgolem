"""由既有四姿勢清單產生鏡射研究快取；不修改 PNG 或正式素材。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
import struct
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, __version__


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ['assets','source','manifest','font','out']:
        ap.add_argument('--'+name,type=Path,required=True)
    a = ap.parse_args()
    assert not a.out.exists() and a.out.parent.is_dir()
    m = json.loads(a.manifest.read_text())
    source = a.source.read_bytes()
    assert m['source_file'] == a.source.name and m['source_sha256'] == sha(source)
    assert len(source) == 13216 and len(m['frames']) == 4
    spec = importlib.util.spec_from_file_location('sample',Path(__file__).with_name('audit-encounter-gui.py'))
    sampler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sampler)
    rev = [int(f'{v:08b}'[::-1],2) for v in range(256)]
    palette = sampler.EGA
    font = ImageFont.truetype(str(a.font),24,index=3)
    out = Image.new('RGB',(2112,344),'#11251f')
    draw = ImageDraw.Draw(out)
    records = []
    a.out.mkdir()
    for i,f in enumerate(m['frames']):
        assert f['record'] == i
        entry = f['image']
        image = a.assets/entry['file']
        assert sha(image.read_bytes()) == entry['sha256']
        x,y,w,h = f['target_rect']
        assert 0 <= x < x+w <= 264 and 0 <= y < y+h <= 300
        pixels = sampler.sample(image,w,h,actor=True,rect=entry['source_rect'])
        original = bytearray(264*300*4)
        for row in range(h):
            at = ((y+row)*264+x)*4
            original[at:at+w*4] = pixels[row*w*4:(row+1)*w*4]
        mirrored = b''.join(original[(row*264+col)*4:(row*264+col+1)*4] for row in range(300) for col in range(263,-1,-1))
        raw = source[i*3304:(i+1)*3304]
        assert struct.unpack_from('<HH',raw) == (11,50)
        transformed = raw[:4]+bytes(rev[v] for row in range(4,3304,11) for v in raw[row:row+11][::-1])
        native = Image.new('RGB',(88,50))
        colors = []
        for yy in range(50):
            for xx in range(88):
                at,bit = yy*11+xx//8,7-xx%8
                color = sum(((transformed[4+p*550+at]>>bit)&1)<<p for p in range(4))
                colors.append(tuple(palette[color]) if transformed[4+5*550+at]>>bit&1 else (0,0,0))
        native.putdata(colors)
        draw.text((i*528+8,5),f'記錄 {i}：原版／HD 友軍方向',font=font,fill='#fff1b5')
        out.paste(native.resize((264,300),Image.Resampling.NEAREST),(i*528,36))
        out.paste(Image.frombytes('RGB',(264,300),bytes(mirrored[q] for q in range(len(mirrored)) if q%4!=3)),(i*528+264,36))
        name = f'record-{i}-mirror.rgba'
        (a.out/name).write_bytes(mirrored)
        records.append(dict(record=i,source_id=entry['source_index']+1,source_offset=i*3304,
                            native_sha256=sha(transformed[:2204]),six_plane_sha256=sha(transformed),
                            original_cache_sha256=sha(original),cache_file=name,cache_sha256=sha(mirrored),
                            source_rect_xywh=entry['source_rect'],original_target_xywh=f['target_rect'],
                            mirrored_target_xywh=[264-x-w,y,w,h],image_file=entry['file'],image_sha256=entry['sha256']))
    out.save(a.out/'comparison.png')
    result = dict(schema=1,status='mirror-cache-prototype',source_file=a.source.name,source_sha256=sha(source),
                  input_manifest_sha256=sha(a.manifest.read_bytes()),entries=records,
                  comparison_sha256=sha((a.out/'comparison.png').read_bytes()),production_registered=False,
                  normal_source_verified=False,PNG_bytes_unchanged=True,
                  tool=dict(pillow=__version__,script_sha256=sha(Path(__file__).read_bytes())))
    (a.out/'registration.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],records=len(records),cache_sha256=[e['cache_sha256'] for e in records])))


if __name__ == '__main__':
    main()
