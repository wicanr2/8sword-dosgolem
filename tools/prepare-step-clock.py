#!/usr/bin/env python3
"""047 DRAFT：在私有副本核對步數時鐘的原生Go像素成本。"""
import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == a.out.parent.stat().st_uid == 1000
    assert not a.out.exists()
    a.out.mkdir()
    for name in ['go.mod', 'go.sum']:
        shutil.copyfile(a.project/name, a.out/name)
    shutil.copytree(a.project/'internal', a.out/'internal')
    target = a.out/'internal/eightsword'
    if "func sourceAtomicClockReady(" not in (target/"source_compat.go").read_text():
        replacements = {
            'source_pages.go': [('!m.CycleClock || !m.CPU.DOSBoxCost', '!sourceAtomicClockReady(m)'),
                                ('m.CPU.Cycles += 1 + uint64(count)', 'm.CPU.Cycles += sourceAtomicCycles(m, 1+uint64(count), 3+5*uint64(count))')],
            'source_bitmap_rows.go': [('!m.CycleClock || !m.CPU.DOSBoxCost', '!sourceAtomicClockReady(m)'),
                                      ('m.CPU.Cycles += 1 + uint64(count)', 'm.CPU.Cycles += sourceAtomicCycles(m, 1+uint64(count), 3+5*uint64(count))')],
            'source_compat.go': [('!m.CycleClock || !m.CPU.DOSBoxCost', '!sourceAtomicClockReady(m)'),
                                 ('m.CPU.Cycles += 1 + uint64(n)', 'm.CPU.Cycles += sourceAtomicCycles(m, 1+uint64(n), 3+5*uint64(n))'),
                                 ('m.CPU.Cycles++', 'm.CPU.Cycles += sourceAtomicCycles(m, 1, 7)'),
                                 ('m.CPU.Cycles += cycles', 'm.CPU.Cycles += sourceAtomicCycles(m, cycles, 7)')],
        }
        for name, pairs in replacements.items():
            path = target/name
            text = path.read_text()
            for old, new in pairs:
                assert text.count(old) == 1, (name, old)
                text = text.replace(old, new)
            path.write_text(text)
        path = target/'source_reveal.go'
        text = path.read_text()
        old = 'm.CPU.Halted || !m.CycleClock || !m.CPU.DOSBoxCost'
        assert text.count(old) == 1 and text.count('m.CPU.Cycles++') == 1
        path.write_text(text.replace(old, 'm.CPU.Halted || !sourceAtomicClockReady(m)').replace('m.CPU.Cycles++', 'm.CPU.Cycles += sourceAtomicCycles(m, 1, 7)'))
        helper = '''
    // Only the two established clock/cost pairs are admitted. Batch plans still
    // require the live clock; step replay uses these atomic Go operations.
    func sourceAtomicClockReady(m *dg.Machine) bool {
        return m.CycleClock == m.CPU.DOSBoxCost
    }

    // Fixed dosgolem category costs, not a hardware timing model or opcode decoder.
    func sourceAtomicCycles(m *dg.Machine, live, instruction uint64) uint64 {
        if m.CPU.DOSBoxCost { return live }
        return instruction
    }
    '''
        path = target/'source_compat.go'
        path.write_text(path.read_text()+helper)
        path = target/'source_pages_test.go'
        text = path.read_text()
        old = '\tm.SetDOSBoxCycles(3000)\n'
        assert text.count(old) == 1
        path.write_text(text.replace(old, old+'\tif os.Getenv("EIGHTSWORD_TEST_STEP_CLOCK") == "1" { m.SetDOSBoxCycles(0); m.IRQ0Base=128; m.SetDOSBoxCycles(0) }\n'))
    test = (a.project/'tools/research-step-clock_test.go').read_text()
    assert test.startswith('//go:build ignore\n\n')
    (target/'step-clock_test.go').write_text(test.removeprefix('//go:build ignore\n\n'))
    files = {str(p.relative_to(a.out)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in a.out.rglob('*') if p.is_file()}
    result = dict(schema=1, spec='047', production=False, files=files,
                  tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (a.out/'preparation.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(status='prepared-step-clock-research', files=len(files))))


if __name__ == '__main__':
    main()
