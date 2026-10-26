#!/usr/bin/env python3
"""永久保存定稿原圖。以固定清單逐SHA複製；驗證模式不需workplace。Docker only。"""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from PIL import Image, __version__


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''): h.update(chunk)
    return h.hexdigest()


def inside(root, name):
    rel = Path(name)
    if rel.is_absolute() or '..' in rel.parts or not rel.parts:
        raise ValueError('路徑必須位於指定目錄內：'+name)
    path = root
    for part in rel.parts:
        path = path/part
        if path.is_symlink(): raise ValueError('永久原圖不可依賴符號連結：'+str(path))
    return path


def check(path, digest, size=None):
    if not path.is_file() or path.is_symlink(): raise ValueError('缺少一般檔案：'+str(path))
    if size is not None and path.stat().st_size != size: raise ValueError('大小不符：'+str(path))
    if sha(path) != digest: raise ValueError('SHA不符：'+str(path))


def verify(archive):
    manifest = json.loads((archive/'manifest.json').read_text())
    seen = set(); counts = collections.Counter(); total = 0
    for row in manifest['files']:
        if row['path'] in seen or not row['path'].startswith('approved/'):
            raise ValueError('重複或無效的永久路徑')
        seen.add(row['path'])
        path = inside(archive,row['path'])
        check(path,row['sha256'],row['bytes'])
        if 'image' in row:
            with Image.open(path) as im:
                if [*im.size] != row['image']['size'] or im.mode != row['image']['mode']:
                    raise ValueError('原圖形狀不符：'+str(path))
                im.verify()
        counts[row['role']] += 1; total += row['bytes']
    return dict(status='PASS-independent-artwork-archive',files=len(seen),bytes=total,roles=dict(counts),manifest_sha256=sha(archive/'manifest.json'),workplace_required=False,symbolic_links=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--project',type=Path)
    p.add_argument('--plan',type=Path)
    p.add_argument('--verify',action='store_true')
    p.add_argument('--report',type=Path)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid()==1000 and __version__=='11.3.0'
    assert a.archive.is_dir() and not a.archive.is_symlink()
    if not a.verify:
        assert a.project is not None and a.plan is not None and a.archive.stat().st_uid==1000
        plan = json.loads(a.plan.read_text()); rows=[]; seen=set()
        for source in plan['files']:
            name=source['path']
            if name in seen or not name.startswith('approved/'): raise ValueError('重複或無效的輸出路徑')
            seen.add(name)
            original=inside(a.project,source['source']); target=inside(a.archive,name)
            check(original,source['sha256'])
            if original.stat().st_uid != 1000: raise ValueError('來源擁有者不符：'+str(original))
            target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():
                check(target,source['sha256'])
            else:
                fd,temp=tempfile.mkstemp(prefix='.archive-',dir=target.parent)
                os.close(fd)
                try:
                    shutil.copyfile(original,temp)
                    check(Path(temp),source['sha256'])
                    # Source bytes are copied to a distinct inode; no workspace links.
                    os.link(temp,target)
                finally:
                    Path(temp).unlink(missing_ok=True)
            if target.stat().st_uid != 1000: raise ValueError('輸出擁有者不符')
            if (original.stat().st_dev,original.stat().st_ino)==(target.stat().st_dev,target.stat().st_ino):
                raise ValueError('永久原圖不可與研究來源共用inode')
            row=dict(source,bytes=target.stat().st_size)
            if target.suffix.lower()=='.png':
                with Image.open(target) as im: row['image']=dict(size=list(im.size),mode=im.mode)
            rows.append(row)
        manifest=dict(schema=1,scope='User-approved or production-adopted artwork; runtime inputs are separately classified.',plan_sha256=sha(a.plan),tool_sha256=sha(Path(__file__)),files=rows)
        text=json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'; dest=a.archive/'manifest.json'
        if dest.exists():
            if dest.read_text()!=text: raise ValueError('既有永久清單不同，請另存新修訂版')
        else:
            with dest.open('x') as f: f.write(text)
    result=verify(a.archive)
    if a.report:
        assert not a.report.exists() and a.report.parent.stat().st_uid==1000
        a.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__': main()
