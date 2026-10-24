"""018 追加：原版 PMAP 47 黑底；沿既有材質與民兵透明合成。Docker only。"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from PIL import Image, __version__

SOURCE='9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02'
RECORD='a324cf0cd3eb5295e0470d9067ceee03740d5d7ef628af86feaa3a689036f455'
IMAGE='c47dd9465c00e9a0c8b85e9ea58d3034a0d23b9cf926113602f3460752a4eb96'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser()
    for name in ('base','source','out'):ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args()
    assert __version__=='11.3.0' and a.out.is_dir() and not any(a.out.iterdir()) and a.out.stat().st_uid==1000
    assert a.source.is_file() and sha(a.source)==SOURCE
    raw=a.source.read_bytes()[47188:48192]
    assert hashlib.sha256(raw).hexdigest()==RECORD and raw[:4]==bytes([8,0,25,0]) and raw[4:]==bytes(1000)
    files=sorted(a.base.iterdir());assert len(files)==156 and all(f.is_file() and not f.is_symlink() for f in files)
    before={f.name:sha(f) for f in files};m=json.loads((a.base/'terrain.json').read_text())
    assert m['schema']==1 and m['source_sha256']==SOURCE and m['ui']['paper_source']==46
    assert not any(v['source_index']==47 for v in m['materials'])
    assert any(v['source_index']==84 for v in m['actors'])
    for f in files:shutil.copyfile(f,a.out/f.name)
    Image.new('RGB',(1,1),(0,0,0)).save(a.out/'black-panel-r1.png')
    assert sha(a.out/'black-panel-r1.png')==IMAGE
    m['materials'].append(dict(source_index=47,file='black-panel-r1.png',sha256=IMAGE,width=1,height=1,sampling='bitmap'))
    (a.out/'terrain.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
    record=dict(schema=1,source_sha256=SOURCE,file_offset=47188,source_index=47,original_record_sha256=RECORD,image_sha256=IMAGE,method='Pillow RGB(0,0,0) 1x1; preserve original black, existing schema and actor cache',pillow=__version__,base_files_sha256=before,rights='procedural solid black; original source metadata only; complete base runtime assets stay local')
    (a.out/'black-panel-import.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    assert len(list(a.out.iterdir()))==158 and all(sha(a.out/n)==h for n,h in before.items() if n!='terrain.json')
    print('158 files; 155 non-terrain base files unchanged; one material added, schema unchanged')

if __name__=='__main__':main()
