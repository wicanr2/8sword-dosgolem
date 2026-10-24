"""016：匯入已選 B 圖案，從固定 TIT1 重建清除遮罩。只在 Docker 執行。"""
import argparse
import hashlib
import importlib.util
import json
import shutil
import struct
from pathlib import Path
from PIL import Image, ImageChops, __version__

SOURCE='8e971808ea94931ceb3ba78f3d1918984290584bd592d13ce7d081dfb08a34ac'
DECODED='d0bcfa366f8d8c13745c253fbeef1a04691aad24d4a5718cebd9645c17fc1308'
APPROVED='21b9bb5de42c011434160cb208ff9a28354959a2d751e286c078a6b68699f2a0'
MASK='124dd022ac27ef2070195bf53baeb59915600317531766f5ae197ce6970c417d'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser()
    for name in ('base','orig','approved','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    assert __version__=='11.3.0' and a.out.is_dir() and not any(a.out.iterdir()) and a.out.stat().st_uid==1000
    assert sha(a.orig/'TIT1.AY')==SOURCE and sha(a.approved)==APPROVED
    spec=importlib.util.spec_from_file_location('intro',Path(__file__).with_name('prepare-hd-intro.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    data=module.decode((a.orig/'TIT1.AY').read_bytes())
    assert hashlib.sha256(data).hexdigest()==DECODED and struct.unpack_from('<HH',data)==(63,160)
    idx=bytearray(640*200)
    for y in range(160):
        for x in range(504):idx[(y+20)*640+x+64]=sum(((data[4+plane*63*160+y*63+x//8]>>(7-x%8))&1)<<plane for plane in range(4))
    assert hashlib.sha256(idx).hexdigest()=='dfebfbd028187e9022d45743d40ab1d38f209ebd3ffd589149585a1a54459d9e'
    alive={i for i,v in enumerate(idx) if v};mask=Image.new('L',(640,200));groups=[]
    while alive:
        todo=[alive.pop()];points=[]
        while todo:
            i=todo.pop();points.append(i);x,y=i%640,i//640
            for yy in range(max(0,y-1),min(200,y+2)):
                for xx in range(max(0,x-1),min(640,x+2)):
                    at=yy*640+xx
                    if at in alive:alive.remove(at);todo.append(at)
        box=[min(i%640 for i in points),min(i//640 for i in points),max(i%640 for i in points)+1,max(i//640 for i in points)+1]
        if box in ([295,20,347,36],[219,37,425,138]):
            groups.append(dict(pixels=len(points),bbox=box))
            for i in points:mask.putpixel((i%640,i//640),255)
    assert len(groups)==2 and sum(v!=0 for v in mask.getdata())==11924 and hashlib.sha256(mask.tobytes()).hexdigest()==MASK
    im=Image.open(a.approved).convert('RGBA');assert im.size==(1920,1200) and im.getchannel('A').getbbox()==(655,117,1278,825)
    files=sorted(a.base.iterdir());assert len(files)==152 and all(f.is_file() and not f.is_symlink() for f in files)
    before={f.name:sha(f) for f in files};assert 'publisher-icon.json' not in before
    for font in ('noto','lishu','caoshu'):
        words=Image.open(a.base/f'publisher-{font}.png').getchannel('A')
        assert ImageChops.multiply(im.getchannel('A').point(lambda x:255 if x else 0),words.point(lambda x:255 if x else 0)).getbbox() is None
    for f in files:shutil.copyfile(f,a.out/f.name)
    shutil.copyfile(a.approved,a.out/'publisher-icon.png');mask.save(a.out/'publisher-icon-erase.png')
    manifest=dict(schema=1,source_sha256=SOURCE,decoded_sha256=DECODED,approved_sha256=APPROVED,image='publisher-icon.png',image_sha256=APPROVED,width=1920,height=1200,mask='publisher-icon-erase.png',mask_sha256=sha(a.out/'publisher-icon-erase.png'),rights='local-only original-brand derivative; approved private reference, no public distribution permission')
    (a.out/'publisher-icon.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    receipt=dict(schema=1,approved_option='B：柔和漸層',source_sha256=SOURCE,decoded_sha256=DECODED,approved_sha256=APPROVED,mask_raw_sha256=MASK,groups=groups,base_files_sha256=before,pillow=__version__,method='copy approved PNG without resampling; reconstruct original mask from fixed TIT1 planes',rights=manifest['rights'])
    (a.out/'publisher-icon-import.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    assert len(list(a.out.iterdir()))==156 and all(sha(a.out/n)==h for n,h in before.items())
    print('156 files; 152 base files unchanged; approved B copied without resampling')

if __name__=='__main__':main()
