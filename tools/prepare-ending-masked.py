#!/usr/bin/env python3
"""053 DRAFT：從已封存的週期時鐘場景建立六平面Go接管研究副本。"""
import argparse
import hashlib
import json
import os
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    root = a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    main_path = root/'direct-build-r3/ending-main.go'
    direct_path = root/'direct-build-r3/ending-direct.go'
    assert sha(main_path) == '43c1626127c074b231005e3ca8554a3f4edc4d4fd7d10cc970c07e239e54f3ca'
    assert sha(direct_path) == '42e68964f73e808e774446a436bfb9d094f8e51583c84934e0f3f0add7e120d4'
    source = main_path.read_text()
    changes = [
        ('installEndingDirect(o, counts)', 'installEndingDirect(o, counts); installEndingMasked(o, counts)'),
        ('Optional native Go four/five-plane copy skips admitted x86 loops; other loops remain native.',
         'Optional native Go four/five-plane and masked batches skip admitted x86 loops; glyph and other loops remain native.'),
    ]
    for old, new in changes:
        assert source.count(old) == 1, old
        source = source.replace(old, new)
    a.out.mkdir()
    (a.out/'ending-main.go').write_text(source)
    (a.out/'ending-direct.go').write_bytes(direct_path.read_bytes())
    masked = a.project/'tools/research-ending-masked.go'
    (a.out/'ending-masked.go').write_bytes(masked.read_bytes())
    result = dict(schema=1, spec='053', production=False, status='research-masked-source-preparation',
                  base_main_sha256=sha(main_path), base_direct_sha256=sha(direct_path),
                  masked_source_sha256=sha(masked), tool_sha256=sha(Path(__file__)),
                  files={p.name: sha(p) for p in a.out.iterdir()}, clock_cycles_per_ms=3000,
                  limits=['Research only. Build through the read-only /project alias.',
                          'Frozen owned-inputs-r1 retained for CPU/scene oracle; its END7 r1 art is rejected and must not be promoted.',
                          'No production handoff, natural completion, GUI or overall FPS claim.'])
    with (a.out/'preparation.json').open('x') as f:
        f.write(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
