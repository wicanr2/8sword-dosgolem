#!/usr/bin/env python3
"""053 READY：從固定919檔核心建立輸入交接revision，不更動現行核心。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    core = a.project/'workplace/player/runtime-direct-r1'
    base = {**json.loads((core/'runtime-manifest.json').read_text())['base_inputs'],
            **json.loads((core/'player-runtime.json').read_text())['changed']}
    assert len(base) == 919
    for name, digest in base.items():
        assert sha(core/'src'/name) == digest
    a.out.mkdir()
    for name in base:
        target = a.out/'src'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(core/'src'/name, target)
    added = {}
    for source, target in [('ending-input-machine.go', 'internal/machine/ending-input.go'),
                           ('ending-input-oracle.go', 'oracle/ending-input.go')]:
        code = (a.project/'tools'/source).read_text()
        assert code.startswith('//go:build ignore\n')
        (a.out/'src'/target).write_text(code.removeprefix('//go:build ignore\n'))
        added[target] = sha(a.out/'src'/target)
    with (a.out/'runtime-input.json').open('x') as f:
        f.write(json.dumps(dict(schema=1, spec='053', production=False,
            base_inputs=base, added=added, total_inputs=921,
            tool_sha256=sha(Path(__file__)),
            api_source_sha256={n: sha(a.project/'tools'/n) for n in ['ending-input-machine.go', 'ending-input-oracle.go']}),
            ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(base_files=919, added=added, files=921)))


if __name__ == '__main__':
    main()
