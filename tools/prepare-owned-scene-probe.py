#!/usr/bin/env python3
"""047 DRAFT：在既有研究區建立可丟棄的即時場景命令探針，不改正式程式。"""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--gui', action='store_true', help='只在研究副本接入實際視窗，不改正式入口')
    args = parser.parse_args()
    root, out = args.project, args.out
    assert root.is_dir() and not out.exists()
    assert out.parent.stat().st_uid == root.stat().st_uid == 1000
    seed = root / 'workplace/probe-20261023/graphics-first/battle-r1/friendly21-validation-build-r2/src'
    source = out / 'src'
    paths = [root / 'go.mod', root / 'go.sum', *sorted((root / 'internal/eightsword').glob('*.go'))]
    hashes = {}
    for p in paths:
        dest = source / p.relative_to(root)
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = p.read_bytes()
        dest.write_bytes(data)
        hashes[str(p.relative_to(root))] = hashlib.sha256(data).hexdigest()
    for p in (seed / 'internal/eightsword').glob('research_*.go'):
        (source / 'internal/eightsword' / p.name).write_bytes(p.read_bytes())
    data = (root / 'tools/research-owned-scene.go').read_text()
    assert data.startswith('//go:build ignore\n')
    (source / 'internal/eightsword/research_owned_scene.go').write_text(data.replace('//go:build ignore\n', '', 1))
    probe = (seed / 'tools/probe-friendly.go').read_text()
    probe = probe.replace('install := func() { installMap(); installBattle(); installPalace() }',
                          'installOwned, ownedFrame, finishOwned := e.ResearchOwnedScene(*out)\n'
                          '\tdefer func(){must(finishOwned())}()\n'
                          '\tinstall := func() { installMap(); installBattle(); installPalace(); installOwned() }')
    probe = probe.replace('im := e.Frame()', 'im := e.Frame()\n\t\tif own:=ownedFrame();own!=nil {im=own}')
    probe = probe.replace('write("-hd", e.Frame())',
                          'write("-hd", e.Frame())\n\t\twrite("-owned", ownedFrame())')
    (source / 'tools').mkdir()
    (source / 'tools/probe-owned.go').write_text(probe)
    if args.gui:
        for p in sorted((root / 'cmd/8sword').glob('*.go')):
            dest = source / p.relative_to(root)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(p.read_bytes())
            hashes[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
        (source / 'tools/gui-check.go').write_bytes((root / 'tools/gui-check.go').read_bytes())
        gui_script = (root / 'tools/gui-check.sh').read_text()
        gui_script = gui_script.replace('  /bin-player/8sword -root',
                                        '  EIGHTSWORD_RESEARCH_OWNED="$phase_out" /bin-player/8sword -root')
        (out / 'gui-check-owned.sh').write_text(gui_script)
        path = source / 'internal/eightsword/engine.go'
        engine = path.read_text()
        engine = engine.replace('type Engine struct {', 'type Engine struct {\n'
                                '\tresearchOwnedInstall func()\n'
                                '\tresearchOwnedRender func()*image.RGBA\n'
                                '\tresearchOwnedClose func()error\n')
        engine = engine.replace('\te.syncPresentationObservers()\n\treturn e, nil',
                                '\te.syncPresentationObservers()\n'
                                '\tif dir:=os.Getenv("EIGHTSWORD_RESEARCH_OWNED");dir!="" {\n'
                                '\t e.researchOwnedInstall,e.researchOwnedRender,e.researchOwnedClose=e.ResearchOwnedScene(dir)\n}\n'
                                '\treturn e, nil')
        engine = engine.replace('func (e *Engine) Close() {',
                                'func (e *Engine) Close() {\n'
                                '\tif e.researchOwnedClose!=nil {if err:=e.researchOwnedClose();err!=nil {panic(err)}}')
        engine = engine.replace('\t\te.Tracker.Bind()\n', '\t\te.Tracker.Bind()\n'
                                '\t\tif e.researchOwnedInstall!=nil {e.researchOwnedInstall()}\n')
        engine = engine.replace('func (e *Engine) Frame() *image.RGBA {',
                                'func (e *Engine) Frame() (result *image.RGBA) {\n'
                                '\tif e.researchOwnedRender!=nil {defer func(){if own:=e.researchOwnedRender();own!=nil {result=own}}()}')
        assert engine.count('e.researchOwnedInstall()') == 2
        path.write_text(engine)
    (out / 'source-inputs.json').write_text(json.dumps(hashes, indent=2) + '\n')
    commands = '''key 0x3b 100 700
shot 02-character
font lishu
shot 03-lishu
font noto
key 0x01 100 400
key 0x3c 100 700
shot 04-army
key 0x01 100 400
key 0x4d 100 500
key 0x4b 100 500
shot 05-returned-map
quit
'''
    (out / 'commands.txt').write_text(commands)
    print(json.dumps({'out': str(out), 'production_inputs': len(hashes), 'research_only': True}))


if __name__ == '__main__':
    main()
