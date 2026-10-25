#!/usr/bin/env python3
"""在 Pillow Docker 盤點全來源，保留圖像記錄／變體／未分類檔與解碼證據。"""
import argparse
from collections import Counter
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import runpy
import struct

from PIL import Image, ImageDraw, ImageFont, __version__

IFF_SPEC = 'https://wiki.amigaos.net/wiki/ILBM_IFF_Interleaved_Bitmap'
EGA = [(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),(170,85,0),(170,170,170),
       (85,85,85),(85,85,255),(85,255,85),(85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def split_records(data, planes):
    @lru_cache(None)
    def parse(at):
        if at == len(data):
            return [()]
        if at + 4 > len(data):
            return []
        w, h = struct.unpack_from('<HH', data, at)
        if not 1 <= w <= 80 or not 1 <= h <= 200:
            return []
        paths = []
        for count in planes:
            end = at + 4 + w*h*count
            if end > len(data):
                continue
            for tail in parse(end):
                paths.append(((at, w, h, count),) + tail)
                if len(paths) == 2:
                    return paths
        return paths
    paths = parse(0)
    if len(paths) != 1:
        raise ValueError(f'完整結構解析不是唯一解：{len(paths)}')
    return paths[0]


def planar(data, record):
    at, wb, h, planes = record
    area, width = wb*h, wb*8
    raw = data[at:at+4+area*planes]
    out = Image.new('RGBA', (width, h))
    pixels = out.load()
    for y in range(h):
        for x in range(width):
            b, bit = y*wb+x//8, 7-x%8
            index = sum(((raw[4+p*area+b] >> bit)&1) << p for p in range(min(planes, 4)))
            alpha = 255 if planes != 6 or (raw[4+5*area+b] >> bit)&1 else 0
            color = EGA[index] if planes > 1 else ((255,255,255) if index else (0,0,0))
            pixels[x,y] = color + (alpha,)
    return out


def ilbm(data):
    if data[:4] != b'FORM' or data[8:12] != b'ILBM' or struct.unpack_from('>I', data, 4)[0] + 8 != len(data):
        raise ValueError('IFF FORM長度或種類不符')
    chunks = {}
    offsets = []
    at = 12
    while at < len(data):
        if at + 8 > len(data):
            raise ValueError('IFF區塊表頭截斷')
        name, n = data[at:at+4], struct.unpack_from('>I',data,at+4)[0]
        if at+8+n > len(data) or name in chunks and name in (b'BMHD',b'CMAP',b'BODY',b'CAMG'):
            raise ValueError('IFF區塊越界或必要區塊重複')
        offsets.append(dict(name=name.decode('ascii'),offset=at+8,bytes=n))
        chunks[name] = data[at+8:at+8+n]
        at += 8 + n + (n&1)
    if at != len(data) or len(chunks.get(b'BMHD', b'')) != 20:
        raise ValueError('IFF對齊或BMHD不符')
    w,h,_,_,depth,mask,compression,_,transparent,xa,ya,_,_ = struct.unpack('>HHhhBBBBHBBhh',chunks[b'BMHD'])
    camg = struct.unpack('>I', chunks.get(b'CAMG', b'\0\0\0\0'))[0]
    if not 1<=w<=2048 or not 1<=h<=1024 or not 1<=depth<=8 or mask not in (0,1,2) or compression not in (0,1) or camg & 0x880:
        raise ValueError('未支援的ILBM尺寸／平面／mask／壓縮／HAM或EHB')
    palette = chunks.get(b'CMAP', b'')
    if len(palette)%3 or len(palette)//3 < 2**depth:
        raise ValueError('ILBM色盤不完整')
    body, cursor, rows = chunks[b'BODY'], 0, []
    row_bytes = ((w+15)//16)*2
    for _ in range(h*(depth+(mask==1))):
        row = bytearray()
        if compression == 0:
            row.extend(body[cursor:cursor+row_bytes]); cursor += row_bytes
        else:
            while len(row) < row_bytes:
                if cursor >= len(body):
                    raise ValueError('ByteRun1資料截斷')
                command=body[cursor]; cursor+=1
                if command < 128:
                    count=command+1; row.extend(body[cursor:cursor+count]); cursor+=count
                elif command > 128:
                    if cursor >= len(body):
                        raise ValueError('ByteRun1重複資料截斷')
                    row.extend(body[cursor:cursor+1]*(257-command)); cursor+=1
        if len(row) != row_bytes or cursor > len(body):
            raise ValueError('ILBM列越界')
        rows.append(row)
    if cursor != len(body):
        raise ValueError('ILBM BODY有未解析資料')
    out=Image.new('RGBA',(w,h));pixels=out.load()
    for y in range(h):
        row=rows[y*(depth+(mask==1)):(y+1)*(depth+(mask==1))]
        for x in range(w):
            bit=7-x%8; index=sum(((row[p][x//8]>>bit)&1)<<p for p in range(depth))
            alpha=255
            if mask==1:alpha=255*((row[-1][x//8]>>bit)&1)
            elif mask==2 and index==transparent:alpha=0
            pixels[x,y]=tuple(palette[index*3:index*3+3])+(alpha,)
    return out, dict(format='IFF ILBM',width=w,height=h,planes=depth,mask=mask,compression=compression,
                     aspect=[xa,ya],chunks=offsets,specification=IFF_SPEC,camg=camg)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();root,out=args.project,args.out
    assert __version__=='11.3.0' and not out.exists() and out.parent.stat().st_uid==1000
    original=root/'workplace/intake-20261023/sources/game/8sword'
    assets=root/'workplace/player/assets-painted-r48'
    huffman=runpy.run_path(str(root/'tools/prepare-hd-intro.py'))['decode']
    fontpath=root/'workplace/probe-20261023/graphics-first/font-settings-r1/NotoSansCJK-Black.ttc'
    fonts={size:ImageFont.truetype(str(fontpath),size,index=3) for size in (18,22,28,38)}
    files=[];images=[];unclassified=[]
    for path in sorted(p for p in original.iterdir() if p.is_file()):
        raw=path.read_bytes();name=path.name
        file=dict(file=name,bytes=len(raw),sha256=sha(raw),category=None)
        family=None;packed=False;choices=(4,5,6)
        if re.fullmatch(r'MAN\d{2}\.EGG',name):family='special-markers' if name=='MAN27.EGG' else 'troops';choices=(6,)
        elif name in ('PON.EGG','CHOI.EGG'):family='effects';choices=(6,)
        elif name=='MAN.AY':family='hero-and-icons'
        elif name=='ENEMY.AY':family='map-encounters';choices=(6,)
        elif name=='PMAP.AY':family='map-tiles';choices=(5,)
        elif name in ('BUMBOO.AY','BUMBOOH.AY','MSGBOX.AY','MSGBOXH.AY'):
            family='ui';choices=(1,) if 'H.' in name else (4,)
        elif name.startswith(('TIT','END','LIVE','GRO','CUBE','X')) and path.suffix in ('.AY','.EG'):
            family='opening' if name.startswith('TIT') else 'ending' if name.startswith('END') else 'buildings' if name.startswith('LIVE') else 'battle-backgrounds' if name.startswith('GRO') else 'illustrations' if name.startswith('X') else 'ui'
            packed=True;choices=(1,) if 'H.' in name else (4,5,6)
        if family:
            decoded=huffman(raw) if packed else raw
            file.update(category=family,packed=packed,decoded_bytes=len(decoded),decoded_sha256=sha(decoded))
            if decoded[:12].startswith(b'FORM'):
                im,meta=ilbm(decoded)
                images.append((dict(source_file=name,record=0,decoded_offset=0,bytes=len(decoded),record_sha256=sha(decoded),**meta),im))
                file['record_count']=1
            elif name=='TIT6V.AY':
                if len(decoded)!=64768 or max(decoded[:768])>63:raise ValueError('VGA8來源形狀不符')
                im=Image.frombytes('P',(320,200),decoded[768:]);im.putpalette([v*255//63 for v in decoded[:768]])
                images.append((dict(source_file=name,record=0,decoded_offset=0,bytes=len(decoded),format='VGA8 palette+indices',
                                    width=320,height=200,planes=8,record_sha256=sha(decoded),evidence_level='structural format; palette scaled 6-to-8 bits; runtime parity not claimed'),im.convert('RGBA')))
                file['record_count']=1
            else:
                records=split_records(decoded,choices);file['record_count']=len(records)
                for number,record in enumerate(records):
                    at,wb,h,planes=record;n=4+wb*h*planes
                    images.append((dict(source_file=name,record=number,decoded_offset=at,bytes=n,format='planar',width=wb*8,height=h,planes=planes,
                                        record_sha256=sha(decoded[at:at+n]),evidence_level='unique full-consumption structure and source pixels; runtime use checked separately'),planar(decoded,record)))
        elif raw.startswith(b'MZ'):file['category']='program'
        elif re.fullmatch(r'MAP\d{1,2}\.AY',name):file['category']='map-layout'
        elif re.fullmatch(r'[MS](INT|WLK|WAR|ONE|TWO|THR|FOU|FIV|SIX|END|FIG)\.AY',name) or name=='MWAR.EG':file['category']='music-or-score'
        elif path.suffix=='.BAT':file['category']='launcher'
        elif name=='GAMEDATA.AY':file['category']='save'
        elif name in ('YANG1.AY','YANG2.AY') and raw==name.removesuffix('.AY').encode('ascii'):file['category']='five-byte-marker'
        else:file['category']='unclassified';unclassified.append(name)
        files.append(file)
    assert len({f['file'] for f in files})==len(files)
    assert len([r for r,im in images if re.fullmatch(r'MAN\d{2}\.EGG',r['source_file'])])==104
    out.mkdir()
    by_file={};metadata=[]
    for row,im in images:
        row['decoded_rgba_sha256']=sha(im.tobytes());metadata.append(row)
        by_file.setdefault(row['source_file'],[]).append((row,im))
    # Archive coverage uses the validated six original record manifests.
    registered={}
    hd_manifests={}
    for name in ['battle-actors.json','battle-man06.json','battle-man11.json','battle-man21.json','battle-man01.json','battle-militia.json']:
        m=json.loads((assets/name).read_text());assert sha((original/m['source_file']).read_bytes())==m['source_sha256']
        hd_manifests[name]=sha((assets/name).read_bytes())
        for entry in m.get('frames',[m] if 'record' in m else []):
            image=entry.get('image',dict(file=entry.get('image_file'),sha256=entry.get('image_sha256')))
            assert sha((assets/image['file']).read_bytes())==image['sha256']
            registered[(m['source_file'],entry['record'])]=dict(image=image['file'],image_sha256=image['sha256'],transform=m.get('transform','identity'))
    assert len(registered)==20
    def text(draw,xy,value,size=22,color='#ded7bf'):draw.text(xy,value,font=fonts[size],fill=color)
    def display(im,box):
        # Planar EGA game samples use the established 640x200 to 640x400 aspect.
        return im.resize((im.width,im.height*2),Image.Resampling.NEAREST).copy() if box else im.copy()
    def paste(sheet,im,rect,correct=True):
        im=display(im,correct)
        scale=min((rect[2]-rect[0])/im.width,(rect[3]-rect[1])/im.height)
        im=im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))),Image.Resampling.NEAREST if correct else Image.Resampling.LANCZOS)
        x=rect[0]+(rect[2]-rect[0]-im.width)//2;y=rect[1]+(rect[3]-rect[1]-im.height)//2
        sheet.paste(im,(x,y),im)
    troop_names=sorted(n for n in by_file if re.fullmatch(r'MAN\d{2}\.EGG',n))
    sheet=Image.new('RGB',(1600,120+7*260),'#112026');draw=ImageDraw.Draw(sheet)
    text(draw,(24,16),'全部 26 份 MAN 圖像／104 筆記錄：原版與 HD 覆蓋',38,'#f2d28b')
    text(draw,(24,70),'每格取第 0 筆。空白表示未正式接入；MAN27 是太極圖，原版用途尚未證實。',22)
    for index,name in enumerate(troop_names):
        x=20+(index%4)*395;y=120+(index//4)*260
        text(draw,(x,y),name,22,'#f2d28b');count=sum((name,i) in registered for i in range(4));text(draw,(x+184,y),f'HD {count}/4',18)
        text(draw,(x+52,y+30),'原版',18);text(draw,(x+236,y+30),'HD',18)
        item=registered.get((name,0))
        native=by_file[name][0][1]
        if item and item['transform']=='mirror-six-planes':native=native.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        paste(sheet,native,(x+8,y+58,x+180,y+244))
        if item:
            with Image.open(assets/item['image']) as im:paste(sheet,im.convert('RGBA'),(x+190,y+58,x+370,y+244),False)
        else:text(draw,(x+204,y+120),'未正式接入',22,'#9bafa9')
    sheet.save(out/'troops-all-original-hd-r1.png')
    # Every source record is visible, including MAN27. Do not silently renumber
    # the missing MAN26 filename or equate file groups with proven unit names.
    sheet=Image.new('RGB',(1500,112+13*268),'#112026');draw=ImageDraw.Draw(sheet)
    text(draw,(24,12),'全部 104 筆原版 MAN 圖像記錄',38,'#f2d28b');text(draw,(24,66),'金色 HD 表示已有正式登錄。MAN27 是太極圖；檔名與記錄號不等同兵種及動作名稱。',22)
    for index,name in enumerate(troop_names):
        x=20+(index%2)*745;y=112+(index//2)*268;text(draw,(x,y),name,22,'#f2d28b')
        for number,(row,im) in enumerate(by_file[name]):
            xx=x+number*182;paste(sheet,im,(xx,y+40,xx+176,y+236));hd=(name,number) in registered
            text(draw,(xx+28,y+240),f'{number}'+('  HD' if hd else ''),18,'#f2d28b' if hd else '#a1aba8')
    sheet.save(out/'troops-all-poses-original-r1.png')
    sheets=[]
    category_labels={'effects':'戰場效果','ending':'結局圖像','map-encounters':'地圖遭遇','battle-backgrounds':'戰場背景與原版變體',
                     'buildings':'建築與原版變體','hero-and-icons':'主角與圖示','map-tiles':'地圖圖塊','opening':'開場圖像',
                     'illustrations':'原版編輯圖集與插畫','ui':'介面圖像','special-markers':'太極圖來源，原版用途未證實'}
    for category in sorted({f['category'] for f in files if 'record_count' in f}-{'troops'}):
        group=[(row,im) for row,im in images if next(f['category'] for f in files if f['file']==row['source_file'])==category]
        cols=4;rows=(len(group)+cols-1)//cols
        sheet=Image.new('RGB',(1280,80+rows*238),'#112026');draw=ImageDraw.Draw(sheet)
        text(draw,(22,14),f'{category_labels[category]}／{len(group)} 筆原版圖像',28,'#f2d28b')
        for index,(row,im) in enumerate(group):
            x=(index%cols)*320;y=80+(index//cols)*238
            text(draw,(x+8,y),f'{row["source_file"]} #{row["record"]}',18)
            text(draw,(x+8,y+26),f'{row["width"]}x{row["height"]} / {row["planes"]} planes',18,'#9bafa9')
            paste(sheet,im,(x+8,y+58,x+312,y+226),row['format'] in ('planar','IFF ILBM'))
        name='original-'+category+'-r1.png';sheet.save(out/name);sheets.append(name)
    report=dict(schema=1,status='static-original-graphics-inventory',source_files=len(files),graphics_files=sum('record_count' in f for f in files),
                graphics_records=len(images),categories=dict(Counter(next(f['category'] for f in files if f['file']==r['source_file']) for r,im in images)),
                hd_troop_records=len(registered),unclassified_files=unclassified,files=files,records=metadata,
                font_source=dict(file=fontpath.name,sha256=sha(fontpath.read_bytes())),hd_manifests=hd_manifests,
                hd_registrations=[dict(source_file=name,record=record,**value) for (name,record),value in sorted(registered.items())],
                sheets=sheets+['troops-all-original-hd-r1.png','troops-all-poses-original-r1.png'],
                script_sha256=sha(Path(__file__).read_bytes()),huffman_script_sha256=sha((root/'tools/prepare-hd-intro.py').read_bytes()),pillow=__version__,
                outputs={p.name:sha(p.read_bytes()) for p in out.glob('*.png')},
                limits=['Static file inventory and decoded pictures are not normal-path reachability or complete HD.',
                        'H filenames are source variants, not our HD mode.', 'Unclassified files are retained explicitly.',
                        'VGA8 palette conversion and ILBM file colors do not assert original runtime palette parity.'],
                specifications=[IFF_SPEC],rights='User-requested comparison documentation in the existing private repository; originals and full asset packs remain local.')
    (out/'catalog.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['source_files','graphics_files','graphics_records','categories','unclassified_files']},ensure_ascii=False))


if __name__=='__main__':main()
