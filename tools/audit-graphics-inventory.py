#!/usr/bin/env python3
"""核對全圖形清單、完整來源邊界、既有解碼器、README 圖集及 IDA 來源。"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import runpy

from PIL import Image


def read(path):
    return json.loads(path.read_text())


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('project','catalog','out'):parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args();root=args.project;data=read(args.catalog/'catalog.json')
    original=root/'workplace/intake-20261023/sources/game/8sword'
    tools=root/'tools';api=runpy.run_path(str(tools/'catalog-all-graphics.py'))
    unpack=runpy.run_path(str(tools/'prepare-hd-intro.py'))['decode']
    decode_battle=runpy.run_path(str(tools/'catalog-battle-actors.py'))['decode']
    decode_enemy=runpy.run_path(str(tools/'catalog-encounter.py'))['decode']
    assert data['source_files']==158 and data['graphics_files']==104 and data['graphics_records']==333
    assert data['script_sha256']==sha((tools/'catalog-all-graphics.py').read_bytes())
    actual={p.name for p in original.iterdir() if p.is_file()}
    assert {f['file'] for f in data['files']}==actual
    records=defaultdict(list)
    for record in data['records']:records[record['source_file']].append(record)
    independent=0
    for file in data['files']:
        raw=(original/file['file']).read_bytes();assert sha(raw)==file['sha256'] and len(raw)==file['bytes']
        if 'record_count' not in file:continue
        decoded=unpack(raw) if file['packed'] else raw
        assert sha(decoded)==file['decoded_sha256'] and len(decoded)==file['decoded_bytes']
        group=records[file['file']];assert len(group)==file['record_count']
        end=0
        for number,record in enumerate(group):
            assert record['record']==number and record['decoded_offset']==end
            piece=decoded[end:end+record['bytes']];assert sha(piece)==record['record_sha256'];end+=record['bytes']
            if record['format']=='planar' and record['planes']==6 and record['width'] in (64,88):
                image=decode_battle(piece) if record['width']==88 else decode_enemy(piece)
                current=api['planar'](decoded,(record['decoded_offset'],record['width']//8,record['height'],6))
                assert sha(current.tobytes())==record['decoded_rgba_sha256']
                # The older ENEMY decoder zeros RGB below alpha=0, while the
                # inventory preserves those source color bits. Verify the mask
                # and visible result; hidden RGB is not a display difference.
                assert image.getchannel('A').tobytes()==current.getchannel('A').tobytes()
                base=Image.new('RGBA',image.size,(31,47,53,255))
                assert Image.alpha_composite(base,image).tobytes()==Image.alpha_composite(base,current).tobytes()
                independent+=1
        assert end==len(decoded),file['file']
    assert len(records)==104 and independent>=130
    assert len({(x['source_file'],x['record']) for x in data['records']})==333
    assert data['categories']['troops']==100 and data['categories']['special-markers']==4
    assert data['categories']['map-encounters']==14 and data['categories']['hero-and-icons']==29
    assert data['hd_troop_records']==len(data['hd_registrations'])==20
    for value in data['hd_registrations']:
        assert sha((root/'workplace/player/assets-painted-r48'/value['image']).read_bytes())==value['image_sha256']
    for name,digest in data['outputs'].items():
        assert sha((args.catalog/name).read_bytes())==digest
        assert sha((root/'docs/images'/name).read_bytes())==digest
        with Image.open(args.catalog/name) as im:im.verify()
    native=(original/'MAN01.EGG').read_bytes();iff=unpack((original/'X01.AY').read_bytes())
    bad_iff=bytearray(iff);bmhd=iff.index(b'BMHD')+8;bad_iff[bmhd+10]=99
    negative=[lambda:api['split_records'](native[:-1],(6,)),lambda:api['ilbm'](iff[:-1]),lambda:api['ilbm'](bytes(bad_iff))]
    for check in negative:
        try:check()
        except ValueError:pass
        else:raise AssertionError('Malformed input was accepted')
    ida=root/'workplace/probe-20261023/graphics-first'
    evidence={}
    for name,count in [('ida-graphics-inventory-r2.json',521),('ida-intro-graphics-inventory-r1.json',185)]:
        record=read(ida/name);assert record['tool']=='IDA 9.4' and record['uid']==1000 and record['function_count']==count
        evidence[name]=dict(sha256=sha((ida/name).read_bytes()),resource_strings=len(record['resources']),
                            relative_operand_candidates=len(record['relative_filename_operand_candidates']))
    assert sha((root/'workplace/probe-20261023/text-first/PAM.i64').read_bytes())==read(ida/'ida-graphics-inventory-r2.json')['database_sha256']
    assert sha((root/'workplace/probe-20261023/music-first/intro-events-r1/PREDELLA-runtime.i64').read_bytes())==read(ida/'ida-intro-graphics-inventory-r1.json')['database_sha256']
    result=dict(status='PASS-static-graphics-inventory-and-readme-sheets',source_files=158,graphics_files=104,graphics_records=333,
                categories=data['categories'],independent_six_plane_records=independent,malformed_inputs_rejected=len(negative),
                comparison_sheets=len(data['outputs']),ida=evidence,unclassified_files=data['unclassified_files'],
                limits=['MAN27 original role is unknown; four taiji records are not assumed to be a unit.',
                        'Seven unclassified files remain; not proof all original graphics are exhausted.',
                        'Static decoding and comparison sheets are not live-path or HD completion proof.'])
    assert args.out.parent.is_dir() and args.out.parent.stat().st_uid==1000 and not args.out.exists()
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
