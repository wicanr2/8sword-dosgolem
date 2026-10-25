#!/usr/bin/env python3
"""047 DRAFT：建立獨立核心研究副本，補平面 VGA 的讀取前觀測。"""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--event-budget', action='store_true', help='研究雙重步數／週期事件預算，尚未接入玩家')
    args = parser.parse_args()
    root, out = args.project, args.out
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000
    assert not out.exists() and out.parent.stat().st_uid == 1000
    base = root/'workplace/dosgolem'
    excluded = {'.git', 'workplace', 'docs', 'bootroot'}
    original = {}
    for p in sorted(base.rglob('*')):
        rel = p.relative_to(base)
        if not p.is_file() or set(rel.parts) & excluded or p.suffix == '.test':
            continue
        dest = out/'src'/rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = p.read_bytes()
        dest.write_bytes(data)
        original[str(rel)] = hashlib.sha256(data).hexdigest()
    edits = {}
    path = out/'src/internal/machine/machine.go'
    before = path.read_text()
    after = before.replace('onVideoWrite       func(VideoWrite)',
                           'onVideoWrite       func(VideoWrite)\n\tonVideoRead func(VideoRead)\n\tpreparePlanarRead, preparePlanarWrite func(uint32)')
    marker = '\t\treturn m.VGA.Read(a - vgaLo)'
    assert after.count(marker) == 1
    after = after.replace(marker, '''
		if m.preparePlanarRead != nil { m.preparePlanarRead(a-vgaLo) }
		if m.onVideoRead != nil {
			cs, ip := m.CPU.OpAddr()
			m.onVideoRead(VideoRead{Step:m.Steps, CS:cs, IP:ip, Offset:a-vgaLo})
		}
''' + marker)
    marker = '\tif m.onVideoWrite != nil && a >= vgaLo && a < vgaHi {'
    assert after.count(marker) == 1
    after = after.replace(marker, '''
	if m.planarOn && a >= vgaLo && a < vgaHi && m.preparePlanarWrite != nil {
		m.preparePlanarWrite(a-vgaLo)
	}
''' + marker)
    assert after != before
    edits[str(path.relative_to(out/'src'))] = (before, after)
    path.write_text(after)
    additions = {
        'internal/machine/video_read_observe.go': '''package machine

// VideoRead reports a planar CPU read before VGA.Read loads all four latches.
// Observers are transient host callbacks and are not serialized guest state.
type VideoRead struct {
	Step uint64
	CS, IP uint16
	Offset uint32
}

// ObserveVideoReads replaces the single planar pre-read observer; nil disables it.
// A diagnostic observer must not read through Read8 recursively.
func (m *Machine) ObserveVideoReads(fn func(VideoRead)) { m.onVideoRead = fn }

// PreparePlanarAccess installs an explicit compatibility-backing provider.
// It runs before read-only observations and before the real VGA operation.
// Providers may update plane bytes directly, but must not recurse through
// Read8/Write8 or alter CPU, latches, event queues or device registers.
// This transient provider is not part of serialized guest state.
func (m *Machine) PreparePlanarAccess(read, write func(uint32)) {
	m.preparePlanarRead, m.preparePlanarWrite = read, write
}
''',
        'oracle/video_read_observe.go': '''package oracle

import "github.com/wicanr2/dosgolem/internal/machine"

type VideoRead = machine.VideoRead

func (o *Oracle) ObserveVideoReads(fn func(VideoRead)) { o.m.ObserveVideoReads(fn) }
''',
        'video_observe.go': '''package dosgolem

import "github.com/wicanr2/dosgolem/internal/machine"

type VideoRead = machine.VideoRead
type VideoWrite = machine.VideoWrite
type VideoModeChange = machine.ModeChange
''',
    }
    if args.event_budget:
        for name in ('research-host-work.go', 'research-host-work_test.go'):
            data = (root/'tools'/name).read_text()
            assert data.startswith('//go:build ignore\n')
            additions['internal/machine/'+name.replace('research-', '')] = data.replace('//go:build ignore\n', '', 1)
    for name, after in additions.items():
        path = out/'src'/name
        assert not path.exists()
        path.write_text(after)
        edits[name] = ('', after)
    patch = ''.join(''.join(difflib.unified_diff(a.splitlines(True), b.splitlines(True),
                    fromfile='a/'+name if a else '/dev/null', tofile='b/'+name))
                    for name, (a, b) in sorted(edits.items()))
    (out/'video-read.patch').write_text(patch)
    report = dict(schema=1, production=False, base_inputs=original,
                  changed={n: hashlib.sha256(b.encode()).hexdigest() for n, (_, b) in edits.items()},
                  patch_sha256=hashlib.sha256(patch.encode()).hexdigest(),
                  note='Independent research copy. Fixed project core and common dosgolem are read-only.')
    (out/'source-manifest.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(files=len(original), changed=list(edits), out=str(out))))


if __name__ == '__main__':
    main()
