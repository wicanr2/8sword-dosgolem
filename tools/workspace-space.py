"""Docker-only workspace cleanup: preserve evidence paths and bytes via hard links.

Use detach before modifying a shared artifact. Originals, saves and source code
are outside the allowed artifact set. No global Docker resources are removed.
"""
import argparse
import hashlib
import json
import os
import shutil
import stat
import tempfile
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        while data := f.read(1024 * 1024):
            h.update(data)
    return h.hexdigest()


def artifact(root, relative):
    p = Path(relative)
    if p.is_absolute() or '..' in p.parts or not p.parts or p.parts[0] not in ('player', 'probe-20261023'):
        raise ValueError('Artifact outside cleanup scope: ' + relative)
    path = root / p
    if path.resolve() != path or not path.is_file() or path.is_symlink():
        raise ValueError('Artifact is not a direct regular file: ' + relative)
    if not path.name.endswith(('.png', '.frames.gz', '.state', '.idx', '.pcm', '.wav', '.ogg')):
        raise ValueError('Mutable file type excluded: ' + relative)
    if path.stat().st_size < 65536 or path.stat().st_uid != os.getuid():
        raise ValueError('Artifact size or ownership differs: ' + relative)
    return path


def same_bytes(a, b):
    with a.open('rb') as x, b.open('rb') as y:
        while data := x.read(1024 * 1024):
            if data != y.read(len(data)):
                return False
        return not y.read(1)


def verify(root, plan, require_shared=False):
    files = 0
    for group in plan['groups']:
        paths = [artifact(root, n) for n in group['paths']]
        if len(paths) < 2:
            raise ValueError('Invalid duplicate group')
        first = paths[0].stat()
        for p in paths:
            info = p.stat()
            if info.st_size != group['bytes'] or digest(p) != group['sha256']:
                raise ValueError('Artifact bytes changed: ' + str(p))
            if require_shared and ((info.st_dev, info.st_ino) != (first.st_dev, first.st_ino) or info.st_mode & 0o222):
                raise ValueError('Artifact not shared and read-only: ' + str(p))
            files += 1
    return files


def apply(root, plan, receipt, plan_path):
    if receipt.exists():
        raise ValueError('Refuse to overwrite cleanup receipt')
    files = verify(root, plan)
    report = dict(schema=1, status='running', plan_sha256=digest(plan_path),
                  method='byte-identical-read-only-hardlinks', files_verified_before=files,
                  groups=[], cache_removed_bytes=0)
    def save():
        temp = receipt.with_suffix(receipt.suffix+'.tmp')
        temp.write_text(json.dumps(report, indent=2)+'\n')
        os.replace(temp, receipt)
    save()
    for group in plan['groups']:
        paths = [artifact(root, n) for n in group['paths']]
        canonical = paths[0]
        old_modes = {n: stat.S_IMODE(p.stat().st_mode) for n, p in zip(group['paths'], paths)}
        canonical.chmod(stat.S_IMODE(canonical.stat().st_mode) & ~0o222)
        linked = 0
        for path in paths[1:]:
            if path.samefile(canonical):
                continue
            if not same_bytes(canonical, path):
                raise ValueError('Duplicate differs before linking: ' + str(path))
            temp = path.with_name(path.name+'.space-link-tmp')
            if temp.exists() or temp.is_symlink():
                raise ValueError('Temporary link already exists')
            try:
                os.link(canonical, temp)
                os.replace(temp, path)
            finally:
                if temp.exists():
                    temp.unlink()
            linked += 1
        report['groups'].append(dict(sha256=group['sha256'], bytes=group['bytes'],
                                     paths=group['paths'], old_modes=old_modes, linked=linked))
        save()
    cache = root/'gocache'
    if cache.is_symlink() or not cache.is_dir() or cache.stat().st_uid != os.getuid():
        raise ValueError('Go cache directory differs')
    for p in cache.rglob('*'):
        if p.is_file() and not p.is_symlink():
            report['cache_removed_bytes'] += p.stat().st_blocks * 512
    for p in cache.iterdir():
        if p.is_dir() and not p.is_symlink():
            shutil.rmtree(p)
        else:
            p.unlink()
    report['status'] = 'PASS'
    report['files_verified_after'] = verify(root, plan, require_shared=True)
    report['deduplicated_bytes'] = sum(g['bytes']*g['linked'] for g in report['groups'])
    save()
    print(json.dumps({k:v for k,v in report.items() if k!='groups'}))


def detach(root, relative):
    path = artifact(root, relative)
    before = digest(path)
    mode = stat.S_IMODE(path.stat().st_mode)
    fd, name = tempfile.mkstemp(prefix='.space-detach-', dir=path.parent)
    os.close(fd)
    temp = Path(name)
    try:
        shutil.copyfile(path, temp)
        if digest(temp) != before:
            raise ValueError('Detached copy differs')
        temp.chmod(mode | 0o200)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()
    print('Detached private writable copy: ' + relative)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('action', choices=['apply', 'verify', 'detach'])
    parser.add_argument('path', nargs='?')
    args = parser.parse_args()
    root = args.workspace.resolve(strict=True)
    if os.getuid() == 0 or root.stat().st_uid != os.getuid():
        raise ValueError('Run as workspace owner, never root')
    if args.action == 'detach':
        if not args.path:
            parser.error('detach requires relative artifact path')
        detach(root, args.path)
    else:
        if not args.plan or (args.action == 'apply' and not args.receipt):
            parser.error('plan and apply receipt required')
        plan = json.loads(args.plan.read_text())
        if args.action == 'apply':
            apply(root, plan, args.receipt, args.plan)
        else:
            print('PASS: '+str(verify(root, plan, require_shared=True))+' paths, hashes and read-only links verified')
