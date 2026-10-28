#!/usr/bin/env python3
"""專案永久保存：內容去重、無損壓縮及不依賴workplace的核對／還原。Docker only。"""
import argparse
import collections
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
import time


def safe(root, name):
    rel = Path(name)
    if not rel.parts or rel.is_absolute() or '..' in rel.parts:
        raise ValueError('不安全的相對路徑：'+name)
    target = root
    for part in rel.parts:
        target = target/part
        if target.is_symlink(): raise ValueError('輸出路徑包含符號連結：'+str(target))
    return target


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()


def write_json(path, value, compressed=False):
    assert not path.exists()
    if compressed:
        with path.open('xb') as raw, gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0,compresslevel=6) as f:
            f.write((json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n').encode())
    else:
        with path.open('x') as f: f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def category(name):
    p=Path(name); lower=p.name.lower()
    if p.suffix.lower() in ['.i64','.idb','.id0','.id1','.id2','.nam','.til']: return '逆向資料庫'
    if p.suffix.lower() in ['.ttf','.ttc','.otf','.bdf','.sfd']: return '字型'
    if p.suffix.lower() in ['.ogg','.wav','.pcm','.mid','.midi','.sf2','.sf3','.mp3']: return '音樂與音源'
    if any(v in p.parts for v in ['scratch','saves']) or p.suffix.lower()=='.state': return '存檔與狀態'
    if p.suffix.lower() in ['.go','.py','.sh','.c','.h','.mod','.sum','.patch']: return '原始碼與重建工具'
    if p.suffix.lower()=='.png': return '圖像與取樣畫面'
    if p.suffix.lower() in ['.json','.jsonl','.txt','.md','.log','.sha256','.tsv','.csv']: return '收據與文件'
    if lower.endswith('.frames.gz'): return '最新存讀錄影'
    return '其他必要輸入'


def compressed_source(path, head):
    return path.suffix.lower() in ['.png','.jpg','.jpeg','.webp','.ogg','.mp3','.zip','.gz','.rar','.7z','.lz4','.xz','.bz2'] or head.startswith((b'\x89PNG',b'OggS',b'PK\x03\x04',b'\x1f\x8b'))


def capture(project, archive):
    assert project.is_dir() and (project/'workplace').is_dir()
    assert archive.stat().st_uid==1000 and not (archive/'manifest.json').exists()
    assert shutil.disk_usage(archive).free > 25*(1<<30)
    art=project/'artwork'; art_manifest=json.loads((art/'manifest.json').read_text())
    external={r['sha256']:r for r in art_manifest['files']}
    objects={}; rows=[]; links=[]; skipped=[]; inodes={}; verified_external=set(); last=time.monotonic()
    kept_stream='workplace/player/gui/compat-pixels-save-r2/'
    files=[]
    for folder,dirs,names in os.walk(project/'workplace',followlinks=False):
        rel=Path(folder).relative_to(project)
        if rel==Path('workplace') and 'gocache' in dirs:
            dirs.remove('gocache'); skipped.append(dict(path='workplace/gocache/',reason='可重建的Go編譯快取，整個目錄排除'))
        for name in list(dirs):
            f=Path(folder)/name
            if f.is_symlink():
                links.append(dict(path=str(f.relative_to(project)),target=os.readlink(f))); dirs.remove(name)
        for name in names:
            f=Path(folder)/name; name=str(f.relative_to(project))
            if f.is_symlink(): links.append(dict(path=name,target=os.readlink(f))); continue
            s=f.stat()
            if not stat.S_ISREG(s.st_mode): raise ValueError('未知檔案型態：'+name)
            if name.endswith('.frames.gz') and not name.startswith(kept_stream):
                skipped.append(dict(path=name,bytes=s.st_size,reason='舊大型逐幀錄影；另存最新已驗證存讀錄影，原檔未刪除')); continue
            files.append((name,f))
    for name in ['8sword.zip','珍092-神州八劍.rar']:
        f=project/name
        if f.is_file(): files.append((name,f))
    total=len(files)
    for i,(name,f) in enumerate(sorted(files),1):
        s=f.stat()
        if s.st_uid!=1000: raise ValueError('來源擁有者不符：'+name)
        key=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
        sha=inodes.get(key)
        if sha is None:
            sha=digest(f); inodes[key]=sha
        if sha not in objects:
            if sha in external:
                ref=external[sha]; target=safe(art,ref['path'])
                if sha not in verified_external:
                    if digest(target)!=sha: raise ValueError('永久美術來源SHA不符')
                    verified_external.add(sha)
                objects[sha]=dict(codec='artwork',path=ref['path'],bytes=s.st_size,stored_bytes=0)
            else:
                with f.open('rb') as src: head=src.read(16)
                codec='raw' if compressed_source(f,head) else 'gzip'
                rel=f'objects/{sha[:2]}/{sha}.{codec}'
                target=safe(archive,rel); target.parent.mkdir(parents=True,exist_ok=True)
                if target.exists(): raise ValueError('新保存批次已有未登錄物件：'+rel)
                fd,temp=tempfile.mkstemp(prefix='.preserve-',dir=target.parent); os.close(fd)
                h=hashlib.sha256(); count=0
                try:
                    with f.open('rb') as src, open(temp,'wb') as raw:
                        sink=gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0,compresslevel=1) if codec=='gzip' else raw
                        try:
                            for chunk in iter(lambda:src.read(1<<20),b''):
                                h.update(chunk); count+=len(chunk); sink.write(chunk)
                        finally:
                            if codec=='gzip': sink.close()
                    if h.hexdigest()!=sha or count!=s.st_size: raise ValueError('複製期間來源改變：'+name)
                    os.link(temp,target)
                finally: Path(temp).unlink(missing_ok=True)
                if (target.stat().st_dev,target.stat().st_ino)==(s.st_dev,s.st_ino): raise ValueError('永久物件與研究檔共用inode')
                objects[sha]=dict(codec=codec,path=rel,bytes=count,stored_bytes=target.stat().st_size)
        after=f.stat()
        if after.st_size!=s.st_size or after.st_mtime_ns!=s.st_mtime_ns: raise ValueError('保存期間來源改變：'+name)
        rows.append(dict(path=name,sha256=sha,bytes=s.st_size,mode=stat.S_IMODE(s.st_mode)&0o777,category=category(name)))
        if time.monotonic()-last>12:
            print(json.dumps(dict(progress=i,total=total,unique_objects=len(objects),stored_bytes=sum(v['stored_bytes'] for v in objects.values()))),flush=True); last=time.monotonic()
    catalog=dict(schema=1,files=rows,objects=objects,links=links)
    write_json(archive/'catalog.json.gz',catalog,True)
    write_json(archive/'exclusions.json.gz',skipped,True)
    counts=collections.Counter(r['category'] for r in rows)
    summary=dict(schema=1,status='captured-not-yet-detached-verified',files=len(rows),symbolic_link_records=len(links),unique_objects=len(objects),external_artwork_objects=len(verified_external),logical_bytes=sum(r['bytes'] for r in rows),stored_bytes=sum(o['stored_bytes'] for o in objects.values()),categories=dict(counts),catalog_sha256=digest(archive/'catalog.json.gz'),exclusions_sha256=digest(archive/'exclusions.json.gz'),excluded_stream_files=sum(v.get('path','').endswith('.frames.gz') for v in skipped),excluded_stream_bytes=sum(v.get('bytes',0) for v in skipped),artwork_manifest_sha256=digest(art/'manifest.json'),tool_sha256=digest(Path(__file__)),rights='Local-only originals, derivatives, fonts, source revisions and saves. Objects are not added to Git or public releases.')
    write_json(archive/'manifest.json',summary)
    print(json.dumps(summary,ensure_ascii=False),flush=True)


def load(archive):
    summary=json.loads((archive/'manifest.json').read_text())
    if digest(archive/'catalog.json.gz')!=summary['catalog_sha256'] or digest(archive/'exclusions.json.gz')!=summary['exclusions_sha256']:
        raise ValueError('保存目錄清單SHA不符')
    with gzip.open(archive/'catalog.json.gz','rt') as f: catalog=json.load(f)
    if len(catalog['files'])!=summary['files'] or len(catalog['objects'])!=summary['unique_objects']: raise ValueError('保存數量不符')
    return summary,catalog


def object_file(archive, artwork, row):
    root=artwork if row['codec']=='artwork' else archive
    if root is None: raise ValueError('需要指定已保存的artwork目錄')
    path=safe(root,row['path'])
    if not path.is_file(): raise ValueError('缺少永久物件：'+str(path))
    return gzip.open(path,'rb') if row['codec']=='gzip' else path.open('rb')


def verify(archive, artwork):
    summary,catalog=load(archive); last=time.monotonic()
    if artwork is not None and digest(artwork/'manifest.json')!=summary['artwork_manifest_sha256']: raise ValueError('永久美術清單SHA不符')
    for i,(sha,row) in enumerate(catalog['objects'].items(),1):
        h=hashlib.sha256(); size=0
        with object_file(archive,artwork,row) as f:
            for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk);size+=len(chunk)
        if h.hexdigest()!=sha or size!=row['bytes']: raise ValueError('永久物件SHA／大小不符：'+sha)
        if time.monotonic()-last>12:
            print(json.dumps(dict(verified_objects=i,total=len(catalog['objects']))),flush=True);last=time.monotonic()
    seen=set()
    for row in catalog['files']:
        safe(Path('/validation'),row['path'])
        if row['path'] in seen or row['sha256'] not in catalog['objects'] or row['bytes']!=catalog['objects'][row['sha256']]['bytes']: raise ValueError('檔案索引不符')
        seen.add(row['path'])
    return dict(status='PASS-detached-project-preservation',files=len(seen),unique_objects=len(catalog['objects']),symbolic_link_records=len(catalog['links']),stored_bytes=summary['stored_bytes'],catalog_sha256=summary['catalog_sha256'],workplace_required=False)


def restore(archive,artwork,out,prefixes):
    _,catalog=load(archive)
    assert out.is_dir() and not out.is_symlink() and out.stat().st_uid==1000
    count=0; total=0
    for row in catalog['files']:
        if prefixes and not any(row['path']==p.rstrip('/') or row['path'].startswith(p.rstrip('/')+'/') for p in prefixes): continue
        target=safe(out,row['path']); target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():
            if not target.is_file() or digest(target)!=row['sha256']:raise ValueError('拒絕覆寫不同檔案：'+str(target))
        else:
            fd,temp=tempfile.mkstemp(prefix='.restore-',dir=target.parent);os.close(fd)
            h=hashlib.sha256(); size=0
            try:
                with object_file(archive,artwork,catalog['objects'][row['sha256']]) as src,open(temp,'wb') as dst:
                    for chunk in iter(lambda:src.read(1<<20),b''):h.update(chunk);size+=len(chunk);dst.write(chunk)
                if h.hexdigest()!=row['sha256'] or size!=row['bytes']:raise ValueError('還原SHA／大小不符')
                os.chmod(temp,row['mode']);os.link(temp,target)
            finally:Path(temp).unlink(missing_ok=True)
        count+=1;total+=row['bytes']
    if not count:raise ValueError('前綴未選到任何已保存檔案')
    # Historical links are indexed but never recreated implicitly.
    return dict(status='PASS-byte-exact-restore',files=count,bytes=total,prefixes=prefixes,symlinks_recreated=0)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    for name in ['capture','verify','restore']:mode.add_argument('--'+name,action='store_true')
    p.add_argument('--project',type=Path);p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--artwork',type=Path);p.add_argument('--out',type=Path)
    p.add_argument('--prefix',action='append',default=[]);p.add_argument('--report',type=Path)
    a=p.parse_args();assert Path('/.dockerenv').is_file() and os.getuid()==1000
    assert a.archive.is_dir() and not a.archive.is_symlink()
    if a.capture: capture(a.project,a.archive);return
    result=verify(a.archive,a.artwork) if a.verify else restore(a.archive,a.artwork,a.out,a.prefix)
    if a.report:
        assert a.report.parent.stat().st_uid==1000;write_json(a.report,result)
    print(json.dumps(result,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
