#!/usr/bin/env python3
"""047 DRAFT：在獨立921檔核心副本增加單指令原生Go接管，不改正式核心。"""
import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000
    assert a.out.parent.stat().st_uid == 1000
    core = a.project/'workplace/player/runtime-input-r1'
    receipt = json.loads((core/'runtime-input.json').read_text())
    base = {**receipt['base_inputs'], **receipt['added']}
    assert len(base) == 921
    assert {str(p.relative_to(core/'src')) for p in (core/'src').rglob('*') if p.is_file()} == set(base)
    for name, digest in base.items():
        assert sha(core/'src'/name) == digest
    api_names = ['research-atomic-draw-machine.go', 'research-atomic-draw-oracle.go']
    api_sources = {name:sha(a.project/'tools'/name) for name in api_names}
    if a.out.exists():
        previous = json.loads((a.out/'render-core.json').read_text())
        assert previous['base_inputs'] == base and previous['total_inputs'] == 923
        assert previous['api_source_sha256'] == api_sources and previous['tool_sha256'] == sha(Path(__file__))
        assert {str(p.relative_to(a.out/'src')) for p in (a.out/'src').rglob('*') if p.is_file()} == set(previous['files'])
        for name,digest in previous['files'].items():
            assert sha(a.out/'src'/name) == digest
        print(json.dumps(dict(status='verified-existing-render-core',files=923)))
        return
    a.out.mkdir()
    for name in base:
        out = a.out/'src'/name
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(core/'src'/name, out)
    machine = a.out/'src/internal/machine/machine.go'
    text = machine.read_text()
    replacements = [
        ('type Machine struct {', 'type Machine struct {\n\thostInstructions map[uint32]HostInstruction\n\thostInstructionBits []uint64'),
        ('\tm.insnCS, m.insnIP = m.CPU.Seg[cpu.CS], m.CPU.IP\n',
         '\tm.insnCS, m.insnIP = m.CPU.Seg[cpu.CS], m.CPU.IP\n'
         '\tif m.hostInstructionBits != nil {\n'
         '\t\tkey := (uint32(m.insnCS)*16 + uint32(m.insnIP)) & 0xfffff\n'
         '\t\tif m.hostInstructionBits[key>>6] & (1 << (key&63)) != 0 {\n'
         '\t\t\tif done,err:=m.fireHostInstruction(key);err!=nil {return err} else if done {return nil}\n'
         '\t\t}\n\t}\n'),
    ]
    for old, new in replacements:
        assert text.count(old) == 1
        text = text.replace(old,new)
    machine.write_text(text)
    for src, dst in [('research-atomic-draw-machine.go','internal/machine/host-instruction.go'),
                     ('research-atomic-draw-oracle.go','oracle/host-instruction.go')]:
        text = (a.project/'tools'/src).read_text()
        assert text.startswith('//go:build ignore\n')
        (a.out/'src'/dst).write_text(text.removeprefix('//go:build ignore\n'))
    files = {str(p.relative_to(a.out/'src')):sha(p) for p in (a.out/'src').rglob('*') if p.is_file()}
    assert len(files) == 923
    (a.out/'render-core.json').write_text(json.dumps(dict(schema=1, spec='047', production=False,
        base_inputs=base, files=files, total_inputs=923, tool_sha256=sha(Path(__file__)),
        api_source_sha256=api_sources),indent=2)+'\n')
    print(json.dumps(dict(status='prepared-isolated-render-core',files=923)))


if __name__ == '__main__':
    main()
