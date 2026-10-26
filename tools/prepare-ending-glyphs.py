#!/usr/bin/env python3
"""053 DRAFT：將Go字模列批次接到封存的結局研究場景，原版控制保持。"""
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
    batch = a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    base = batch/'masked-build-r1'
    expected = {'ending-main.go': '8bb4aa2aee183546a17d9f795da2e6fdd7563676911b58db2e3bcce71032d3ac',
                'ending-direct.go': '42e68964f73e808e774446a436bfb9d094f8e51583c84934e0f3f0add7e120d4',
                'ending-masked.go': '21818ce78bb5cb4b21e3a3624e938de29f1c2db1dfa9e957348d1d34a4a38a31'}
    for name, value in expected.items():
        assert sha(base/name) == value
    source = (base/'ending-main.go').read_text()
    replacements = [
        ('installEndingMasked(o, counts)', 'installEndingMasked(o, counts); installEndingGlyphs(o, counts)'),
        ('Optional native Go four/five-plane and masked batches skip admitted x86 loops; glyph and other loops remain native.',
         'Optional native Go planar, masked and glyph batches skip admitted x86 loops; clear/copy and boundary residues remain native.'),
    ]
    for old, new in replacements:
        assert source.count(old) == 1, old
        source = source.replace(old, new)
    a.out.mkdir()
    (a.out/'ending-main.go').write_text(source)
    for name in ('ending-direct.go', 'ending-masked.go'):
        (a.out/name).write_bytes((base/name).read_bytes())
    glyphs = a.project/'tools/research-ending-glyphs.go'
    (a.out/'ending-glyphs.go').write_bytes(glyphs.read_bytes())
    result = dict(schema=1, spec='053', production=False, status='research-glyph-source-preparation',
                  base_inputs=expected, glyph_source_sha256=sha(glyphs), tool_sha256=sha(Path(__file__)),
                  files={p.name: sha(p) for p in a.out.iterdir()}, clock_cycles_per_ms=3000,
                  limits=['Research-only source. Build through read-only /project alias.',
                          'Historical owned-inputs-r1 is a technical oracle; rejected END7 r1 must not be promoted.',
                          'No production handoff, natural completion, GUI or FPS claim.'])
    with (a.out/'preparation.json').open('x') as f:
        f.write(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
