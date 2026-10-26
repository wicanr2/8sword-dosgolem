#!/usr/bin/env python3
"""014：保存前導人物修正原PNG與實際提示，保留每輪而不覆寫。Docker only。"""
import argparse
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, __version__


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('project','batch','image','request'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--variant',type=int,required=True)
    a=p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid()==1000 and __version__=='11.3.0'
    assert a.batch.stat().st_uid==1000 and 2<=a.variant<=9
    request=json.loads(a.request.read_text())
    prompt=a.batch/request['prompt'];reference=a.batch/request['reference']
    target=a.project/request['edit_target'] if request['edit_target'].startswith('docs/') else a.batch/request['edit_target']
    assert sha(prompt)==request['prompt_sha256'] and sha(reference)==request['reference_sha256'] and sha(target)==request['edit_target_sha256']
    image=Image.open(a.image)
    assert image.format=='PNG' and min(image.size)>=512 and max(image.size)<=4096
    assert image.convert('RGBA').getchannel('A').getextrema()==(255,255)
    out=a.batch/f'correction-r{a.variant}.png';receipt=out.with_suffix('.json')
    assert not out.exists() and not receipt.exists()
    with out.open('xb') as f:f.write(a.image.read_bytes())
    result=dict(schema=1,status='generated-correction-not-registered',production=False,tool='built-in image_gen',variant=a.variant,
                image=out.name,image_sha256=sha(out),width=image.width,height=image.height,transparent_background=False,
                prompt=prompt.name,prompt_sha256=sha(prompt),actual_prompt=prompt.read_text(),
                edit_target=request['edit_target'],edit_target_sha256=sha(target),reference=reference.name,reference_sha256=sha(reference),
                request_sha256=sha(a.request),tool_sha256=sha(Path(__file__)),pillow=__version__,rights=request['rights'])
    with receipt.open('x') as f:f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['image','image_sha256','width','height']}))


if __name__=='__main__':
    main()
