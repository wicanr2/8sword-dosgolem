#!/usr/bin/env python3
"""053 DRAFT：從封存的自有場景建立唯讀建置用PAE直接繪圖研究來源。"""
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
    base = a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1/owned-scene-r3/tool-at-run.go'
    assert sha(base) == '86c36a8ba1f00095ded1f7e35be7febdf992ad16e657bff06f20fefdf9e37671'
    source = base.read_text()
    changes = [
        ('root := flag.String(', 'direct := flag.Bool("direct", false, "research native Go planar copy")\n\troot := flag.String('),
        ('o.SetClock(12, 0, 0, 0)', 'o.SetClock(12, 0, 0, 0)\n\to.SetDOSBoxCycles(3000)'),
        ('if apply != nil {\n\t\t\t\tpanic("ending source nesting")\n\t\t\t}',
         'if apply != nil {\n\t\t\t\tif sp == o.Regs().SP { counts["reobserved-entry"]++; return }\n\t\t\t\tpanic("ending source nesting")\n\t\t\t}'),
        ('err := o.Run(200000000)', 'if *direct { installEndingDirect(o, counts) }\n\terr := o.Run(200000000)'),
        ('"production": false, "source_sha256"', '"production": false, "direct_enabled": *direct, "clock_cycles_per_ms": 3000, "source_sha256"'),
        ('Source-only owned scene; original CPU pixel loops are still executed. Unconverted ending artwork remains source pixels.',
         'Source-only owned scene. Optional native Go four/five-plane copy skips admitted x86 loops; other loops remain native. Unconverted ending artwork remains source pixels.'),
    ]
    for old, new in changes:
        assert source.count(old) == 1, old
        source = source.replace(old, new)
    a.out.mkdir()
    (a.out/'ending-main.go').write_text(source)
    direct = a.project/'tools/research-ending-direct.go'
    (a.out/'ending-direct.go').write_bytes(direct.read_bytes())
    result = dict(schema=1, spec='053', production=False, status='research-direct-source-preparation',
                  base_sha256=sha(base), direct_tool_sha256=sha(direct), tool_sha256=sha(Path(__file__)),
                  files={p.name: sha(p) for p in a.out.iterdir()},
                  clock_cycles_per_ms=3000, original_unchanged=True,
                  limits=['Build from this directory through the read-only /project alias.',
                          'Standalone PAE research only. No production promotion or normal PAM handoff.'])
    with (a.out/'preparation.json').open('x') as f:
        f.write(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
