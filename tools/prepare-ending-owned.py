#!/usr/bin/env python3
"""053 DRAFT：準備來源場景研究的字碼、原字模與HD紋理，不提升正式素材。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct

from PIL import Image, __version__


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    root = a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    ram_path = root/'startup-r3/ram-00000-9ffff.bin'
    assert sha(ram_path) == '0ccfd6a0d14ca315dc42ca8e70961e83c076f2c857509df70840402faf00ee60'
    ram = ram_path.read_bytes()
    ds = 0x7e40
    code_bytes, = struct.unpack_from('<H', ram, ds+0x446)
    assert code_bytes == 254
    cjk = []
    for i in range(code_bytes//2):
        code = ram[ds+0x448+i*2:ds+0x44a+i*2]
        char = code.decode('big5', errors='strict')
        assert len(char) == 1
        bits = ram[0x28e0+14+i*30:0x28e0+14+(i+1)*30]
        cjk.append(dict(index=i, character=char, code=code.hex(), bits=bits.hex()))
    ascii_glyphs = [ram[ds+0x548+i*15:ds+0x548+(i+1)*15].hex() for i in range(256)]
    assert all(len(x)==30 for x in ascii_glyphs)
    fonts_path = root/'text-candidates-r1/ending-fonts.json'
    assert sha(fonts_path) == '4c6666ed06da4f839e8b37f46f0f17e762d0919c87b68c4b9337e194ea83c800'
    fonts = json.loads(fonts_path.read_text())
    art = root/'end7-r1.png'
    assert sha(art) == '99f4c89edff85d47cff3b44029174ea0b65019a219883c7f192b5d596b6f4068'
    a.out.mkdir()
    Image.open(art).convert('RGBA').resize((1920,1200),Image.Resampling.LANCZOS).save(a.out/'end7.png')
    assets = a.project/'workplace/player/assets-painted-r56'
    title_files = dict(noto='intro-title-noto-r1.png', lishu='font-title-lishu.png', caoshu='font-title-caoshu.png')
    for profile in fonts['profiles']:
        file = profile['atlas']
        assert sha(fonts_path.parent/file) == profile['atlas_sha256']
        shutil.copyfile(fonts_path.parent/file,a.out/file)
        shutil.copyfile(assets/title_files[profile['id']],a.out/('title-'+profile['id']+'.png'))
    result = dict(schema=1,spec='053',status='research-owned-inputs-not-production',production=False,
                  cjk=cjk,ascii=ascii_glyphs,profiles=fonts['profiles'],
                  source_ram_sha256=sha(ram_path),font_manifest_sha256=sha(fonts_path),
                  art_sha256=sha(art),tool_sha256=sha(Path(__file__)),
                  files={f.name:sha(f) for f in a.out.iterdir()},
                  source_addresses=dict(cjk_bits='runtime028E:000E + index*30',cjk_codes='runtime07E4:0448',ascii_bits='runtime07E4:0548 + code*15'),
                  limits=['Research-only source rendering inputs. No original framebuffer is a rendering input.','No normal PAM handoff, direct CPU-loop replacement or production promotion.'])
    with (a.out/'inputs.json').open('x') as f:f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(cjk=len(cjk),ascii=256,files=len(result['files']),input_sha256=sha(a.out/'inputs.json'))))


if __name__ == '__main__':
    main()
