"""006 追加：沿既有 B 風格與材質格式匯入 PMAP 45。Docker only。"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from PIL import Image, __version__

SOURCE='9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02'
RECORD='fb5ce418cd148e59050d07869bd932ef9ad8a1d26d1971182b00a4ddf55eb88b'
IMAGE='f778eee7b8d058cc7dd1ff8c989e78ffed1a33b3e2270ebfbb2076dd59f1f880'
PROMPT='626ceb0a1e368f1068952c39270c525a50c9ba64c7c52e162b824ce4450cf3f6'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ['base','orig','refs','out']:ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args()
    assert __version__=='11.3.0' and a.out.is_dir() and not any(a.out.iterdir()) and a.out.stat().st_uid==1000
    source=a.orig/'PMAP.AY';assert source.is_file() and sha(source)==SOURCE
    assert hashlib.sha256(source.read_bytes()[45180:46184]).hexdigest()==RECORD
    art=a.refs/'bamboo-painted-r1.png';prompt=a.refs/'bamboo-painted-r1.prompt.txt';assert sha(art)==IMAGE and sha(prompt)==PROMPT
    with Image.open(art) as im:assert im.format=='PNG' and im.mode=='RGB' and im.size==(1419,1108)
    before={f.name:sha(f) for f in a.base.iterdir() if f.is_file()}
    assert len(before)==162 and all(f.is_file() and not f.is_symlink() for f in a.base.iterdir())
    m=json.loads((a.base/'terrain.json').read_text());assert m['schema']==1 and m['source_sha256']==SOURCE and m['style']=='B-bright-painted-r1'
    assert not any(v['source_index']==45 for v in m['materials'])
    for name in before:shutil.copyfile(a.base/name,a.out/name)
    shutil.copyfile(art,a.out/art.name);shutil.copyfile(prompt,a.out/prompt.name)
    entry=dict(source_index=45,file=art.name,sha256=IMAGE,width=1419,height=1108,sampling='bitmap',prompt_file=prompt.name,prompt_sha256=PROMPT)
    m['materials'].append(entry);(a.out/'terrain.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
    (a.out/'bamboo-import.json').write_text(json.dumps(dict(schema=1,spec='006 PMAP45 appendix',source_sha256=SOURCE,source_index=45,file_offset=45180,record_sha256=RECORD,image_sha256=IMAGE,prompt_sha256=PROMPT,preserved_files=before,approval_basis='existing approved B style and original tile geometry, no separate user approval of this PNG',original_png_bytes_preserved=True,rights='local-only original-derived; no public distribution grant'),indent=2)+'\n')
    assert len(list(a.out.iterdir()))==165 and all(sha(a.out/name)==h for name,h in before.items() if name!='terrain.json')
    assert all(f.stat().st_uid==1000 for f in a.out.iterdir())
    print('165 files; 161 non-terrain base files unchanged; material 45 added to existing schema')

if __name__=='__main__':main()
