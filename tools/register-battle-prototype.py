"""把既有四姿勢手繪目錄校準到原生遮罩，輸出研究快取。Docker only；不寫正式素材。"""
import argparse
import hashlib
import importlib.util
import json
import struct
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, __version__


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mirror(raw):
    assert len(raw) == 3304 and struct.unpack_from('<HH', raw) == (11, 50)
    result = bytearray(raw[:4])
    reverse = [int(f'{v:08b}'[::-1], 2) for v in range(256)]
    for row in range(4, len(raw), 11):
        result.extend(reverse[v] for v in raw[row:row+11][::-1])
    return bytes(result)


def native(raw):
    pixels, opaque = [], []
    palette = [(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),(170,85,0),(170,170,170),
               (85,85,85),(85,85,255),(85,255,85),(85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]
    for y in range(50):
        for x in range(88):
            at, bit = y*11+x//8, 7-x%8
            mask = bool(raw[4+5*550+at] >> bit & 1)
            color = sum(((raw[4+p*550+at] >> bit) & 1) << p for p in range(4))
            pixels.append(palette[color] if mask else (0,0,0))
            if mask:
                opaque.append((x,y))
    assert opaque
    bbox = [min(x for x,y in opaque), min(y for x,y in opaque), max(x for x,y in opaque)+1, max(y for x,y in opaque)+1]
    im = Image.new('RGB', (88,50))
    im.putdata(pixels)
    return im.resize((264,300), Image.Resampling.NEAREST), bbox


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ['catalog', 'source', 'out', 'font']:
        ap.add_argument('--'+name, type=Path, required=True)
    a = ap.parse_args()
    assert not a.out.exists() and a.out.parent.is_dir()
    catalog = json.loads(a.catalog.read_text())
    assert catalog['schema'] == 1 and catalog['source_record_bytes'] == 3304
    assert catalog['source_records'] == 4 and len(catalog['entries']) == 4
    assert a.source.name == catalog['source_file'] and sha(a.source) == catalog['source_file_sha256']
    raw = a.source.read_bytes()
    assert len(raw) == 13216
    spec = importlib.util.spec_from_file_location('independent_sample', Path(__file__).with_name('audit-encounter-gui.py'))
    independent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(independent)
    font = ImageFont.truetype(str(a.font), 24, index=3)
    out = Image.new('RGB', (4*528, 2*344), '#11251f')
    draw = ImageDraw.Draw(out)
    records = []
    a.out.mkdir()
    for i, entry in enumerate(catalog['entries']):
        assert entry['record'] == i and entry['native_file_offset'] == i*3304
        chunk = raw[i*3304:(i+1)*3304]
        assert hashlib.sha256(chunk).hexdigest() == entry['source_record_sha256']
        image = a.catalog.parent/entry['image_file']
        prompt = a.catalog.parent/entry['prompt_file']
        assert sha(image) == entry['image_sha256'] and sha(prompt) == entry['prompt_sha256']
        painted = Image.open(image).convert('RGBA')
        bbox = painted.getchannel('A').point(lambda v: 255 if v > 3 else 0).getbbox()
        assert list(bbox) == entry['alpha_bbox']
        sx,sy,ex,ey = bbox
        original, rect = native(chunk)
        x,y,xx,yy = rect
        target = [x*3, y*6, (xx-x)*3, (yy-y)*6]
        assert target[0]+target[2] <= 264 and target[1]+target[3] <= 300
        sampled = independent.sample(image, target[2], target[3], actor=True, rect=[sx,sy,ex-sx,ey-sy])
        full = bytearray(264*300*4)
        for row in range(target[3]):
            start = ((target[1]+row)*264+target[0])*4
            full[start:start+target[2]*4] = sampled[row*target[2]*4:(row+1)*target[2]*4]
        for direction in ['identity', 'mirror-six-planes']:
            source = chunk if direction == 'identity' else mirror(chunk)
            data = bytes(full) if direction == 'identity' else b''.join(full[(row*264+col)*4:(row*264+col+1)*4] for row in range(300) for col in range(263,-1,-1))
            assert all(data[q] <= data[q-q%4+3] for q in range(len(data)) if q%4 != 3)
            filename = f'record-{i}-{direction}.rgba'
            (a.out/filename).write_bytes(data)
            shown = Image.frombytes('RGB', (264,300), bytes(data[q] for q in range(len(data)) if q%4 != 3))
            native_shown, native_bbox = native(source)
            row = 0 if direction == 'identity' else 1
            left, top = i*528, row*344
            out.paste(native_shown, (left,top+36))
            out.paste(shown, (left+264,top+36))
            draw.text((left+8,top+4), f'記錄 {i}：原版／HD  '+('原向' if row==0 else '鏡射'),font=font,fill='#fff1b5')
            records.append(dict(record=i,transform=direction,source_offset=i*3304,
                                six_plane_sha256=hashlib.sha256(source).hexdigest(),native_sha256=hashlib.sha256(source[:4+4*550]).hexdigest(),
                                original_mask_bbox_ltrb=native_bbox,source_rect_xywh=[sx,sy,ex-sx,ey-sy],
                                target_rect_xywh=target if direction == 'identity' else [264-target[0]-target[2],target[1],target[2],target[3]],
                                cache_file=filename,cache_sha256=sha(a.out/filename),cache_size=[264,300],
                                image_file=entry['image_file'],image_sha256=sha(image),prompt_file=entry['prompt_file'],prompt_sha256=sha(prompt)))
    out.save(a.out/'comparison.png')
    result = dict(schema=1,status='static-registration-prototype',source_file=a.source.name,source_sha256=sha(a.source),
                  catalog_sha256=sha(a.catalog),entries=records,comparison_sha256=sha(a.out/'comparison.png'),
                  original_PNG_bytes_preserved=True,production_registered=False,normal_source_verified=False,
                  scope='原生遮罩與手繪取樣的位置原型；鏡射輸出只供辨識與審查，不證明正常呼叫或實際 Draw',
                  tool=dict(pillow=__version__,script_sha256=sha(Path(__file__)),independent_sampler_sha256=sha(Path(__file__).with_name('audit-encounter-gui.py'))))
    (a.out/'registration.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(records=4,directions=2,cache_files=len(records),status=result['status'])))


if __name__ == '__main__':
    main()
