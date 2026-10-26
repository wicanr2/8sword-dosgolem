#!/usr/bin/env python3
"""014：將使用者修正的人物前導圖匯入新本機候選，保留舊版與原PNG。Docker only。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
from PIL import Image, __version__


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path,obj):
    assert not path.exists()
    with path.open('x') as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('project','batch','base','out','images'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid()==1000 and __version__=='11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid==a.images.stat().st_uid==1000
    generation=json.loads((a.batch/'correction-r3.json').read_text())
    assert generation['tool']=='built-in image_gen' and generation['variant']==3
    raw=a.batch/generation['image'];prompt=a.batch/generation['prompt']
    assert sha(raw)==generation['image_sha256'] and sha(prompt)==generation['prompt_sha256']
    assert sha(a.batch/generation['reference'])==generation['reference_sha256']
    source=a.project/'workplace/intake-20261023/sources/game/8sword/TIT6V.AY'
    assert sha(source)=='2131ac054ffd0df4c0f6edff23a393be2cf0416b72b6bb43eedc5d4d844b4212'
    old={f.name:sha(f) for f in a.base.iterdir()}
    assert len(old)==425 and all(f.is_file() and not f.is_symlink() and f.stat().st_uid==1000 for f in a.base.iterdir())
    replaced={'story-prelude.png','story-prelude.json','story-prelude-import.json'}
    assert replaced<=set(old)
    a.out.mkdir()
    for name in old:
        if name not in replaced:os.link(a.base/name,a.out/name)
    image=Image.open(raw).convert('RGBA')
    assert image.getchannel('A').getextrema()==(255,255)
    # Runtime canvas normalization; preserve the original generated PNG above.
    canvas=image.resize((1920,1200),Image.Resampling.LANCZOS)
    canvas.save(a.out/'story-prelude.png')
    manifest=dict(schema=1,source_sha256='9aadec77cf59adb1f444d47891526af7da888bebecc648a3fa16a6f0adcd6dfe',
                  approved_sha256=sha(raw),image='story-prelude.png',image_sha256=sha(a.out/'story-prelude.png'),
                  width=1920,height=1200,rights='local-only original-derived corrected HD artwork; no public distribution permission')
    write(a.out/'story-prelude.json',manifest)
    report=dict(schema=1,spec='014',status='user-corrected-candidate-not-promoted',production=False,
                correction='男主角背影、自然握劍；女主角在旁抬手遮擋並回頭露臉；移除白馬',
                config=manifest,base_files_sha256=old,preserved_files=422,replaced=sorted(replaced),files=425,
                generation_sha256=sha(a.batch/'correction-r3.json'),request_sha256=sha(a.batch/'request-r3.json'),
                source_sha256=sha(source),canvas_rgba_sha256=hashlib.sha256(canvas.tobytes()).hexdigest(),
                canvas_normalization='Pillow11.3.0 LANCZOS full-frame1920x1200, raw generation unchanged',
                tool_sha256=sha(Path(__file__)),pillow=__version__,rights=manifest['rights'])
    write(a.out/'story-prelude-import.json',report)
    write(a.batch/'registration-r3.json',report)
    image_name='story-prelude-color-corrected-r3.png'
    prompt_name='story-prelude-color-corrected-r3.prompt.txt'
    for src,name in [(raw,image_name),(prompt,prompt_name)]:
        assert not (a.images/name).exists();shutil.copyfile(src,a.images/name)
    write(a.images/'story-prelude-color-corrected-r3.json',dict(schema=1,status='user-requested-composition-correction',
          file=image_name,sha256=sha(raw),size=list(image.size),prompt=prompt_name,prompt_sha256=sha(prompt),
          method='built-in image_gen edit',supersedes='story-prelude-color-approved-r1.png',
          user_correction=report['correction'],reference_sha256=generation['reference_sha256'],
          generation_receipt_sha256=report['generation_sha256'],rights='corrected art in existing private repository; original reference stays local'))
    assert len(list(a.out.iterdir()))==425 and all(sha(a.out/n)==v for n,v in old.items() if n not in replaced)
    print(json.dumps(dict(files=425,preserved=422,raw_sha256=sha(raw),canvas_sha256=manifest['image_sha256'],rgba_sha256=report['canvas_rgba_sha256'],registration_sha256=sha(a.batch/'registration-r3.json'))))


if __name__=='__main__':
    main()
