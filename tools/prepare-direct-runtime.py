#!/usr/bin/env python3
"""047 DRAFT：在新的研究核心接入受事件預算限制的 Oracle 呼叫替換。"""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root, out = args.project, args.out
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000
    assert not out.exists() and out.parent.stat().st_uid == 1000
    subprocess.run(['python3', str(root/'tools/prepare-vga-read-probe.py'), '--project', str(root),
                    '--out', str(out), '--event-budget'], check=True)
    core = out/'src'

    def replace(name, before, after):
        path = core/name
        text = path.read_text()
        assert text.count(before) == 1, (name, before)
        path.write_text(text.replace(before, after))

    replace('oracle/oracle.go', 'type Oracle struct {', 'type Oracle struct {\n\thostCalls map[uint32]HostCall')
    replace('oracle/run.go', 'type Cond struct {',
            'type Cond struct {\n\thostLimits func(*Oracle) HostWorkLimits')
    replace('oracle/run.go', '\t\t\to.fireCallHooksAt(key)\n', '''
			o.fireCallHooksAt(key)
			if done,err:=o.fireHostCall(key,c,deadline);err!=nil {return err} else if done {continue}
''')
    marker = '\t\tname: fmt.Sprintf("再跑 %d 道指令", n),'
    replace('oracle/run.go', marker, marker+'''
		hostLimits:func(o *Oracle) HostWorkLimits {
			if o.m.Steps>=target {return HostWorkLimits{}}
			return HostWorkLimits{target-o.m.Steps,^uint64(0)}
		},''')
    marker = '\t\tname:  fmt.Sprintf("再跑 %d 個 cycle", n),'
    replace('oracle/live.go', marker, marker+'''
		hostLimits:func(o *Oracle) HostWorkLimits {
			if o.m.CPU.Cycles>=target {return HostWorkLimits{}}
			return HostWorkLimits{^uint64(0),target-o.m.CPU.Cycles}
		},''')
    for name in ('research-oracle-host-call.go', 'research-oracle-host-call_test.go'):
        data = (root/'tools'/name).read_text()
        assert data.startswith('//go:build ignore\n')
        (core/'oracle'/name.removeprefix('research-')).write_text(data.replace('//go:build ignore\n', '', 1))
    (core/'internal/machine/host_video_observe.go').write_text('''package machine

// NotifyHostVideoWrite reports an explicitly routed compatibility write.
// CS:IP identifies its legacy consumer; no CPU opcode is executed here.
// The host adapter owns the plane update. Observers remain read-only.
func (m *Machine) NotifyHostVideoWrite(w VideoWrite) {
	if m.onVideoWrite!=nil {m.onVideoWrite(w)}
}
''')
    manifest = json.loads((out/'source-manifest.json').read_text())
    changed = {}
    patch = []
    for path in sorted(core.rglob('*')):
        if not path.is_file():
            continue
        name = str(path.relative_to(core))
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest == manifest['base_inputs'].get(name):
            continue
        changed[name] = digest
        base = root/'workplace/dosgolem'/name
        before = base.read_text() if base.is_file() else ''
        patch.extend(difflib.unified_diff(before.splitlines(True), raw.decode().splitlines(True),
                     fromfile='a/'+name if before else '/dev/null', tofile='b/'+name))
    text = ''.join(patch)
    (out/'runtime.patch').write_text(text)
    manifest.update(changed=changed, patch_sha256=hashlib.sha256(text.encode()).hexdigest(),
                    patch='runtime.patch', scope='research-only controlled Oracle host calls')
    (out/'runtime-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(dict(out=str(out), changed=list(changed))))


if __name__ == '__main__':
    main()
