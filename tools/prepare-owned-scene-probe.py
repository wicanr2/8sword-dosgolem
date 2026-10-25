#!/usr/bin/env python3
"""047 DRAFT：在既有研究區建立可丟棄的即時場景命令探針，不改正式程式。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--gui', action='store_true', help='只在研究副本接入實際視窗，不改正式入口')
    parser.add_argument('--modal-menus', action='store_true', help='研究GUI的存前路徑追加F2至F6取消抽樣')
    parser.add_argument('--main-menu', action='store_true', help='無頭探針停在主選單，由普通命令繼續；GUI追加音樂與取消確認抽樣')
    parser.add_argument('--build', action='store_true', help='在固定Go Docker內編譯並保存全部私有來源與程式雜湊')
    parser.add_argument('--intro', action='store_true', help='研究版接PREDELLA來源場景；須搭配--gui以提供診斷Frame參考')
    parser.add_argument('--natural-intro', action='store_true', help='無頭探針與研究視窗等待開場自然結束，不按Escape')
    parser.add_argument('--vga-read-trace', action='store_true', help='研究核心須有VGA讀取前觀測；只記位置，不替換繪圖')
    args = parser.parse_args()
    root, out = args.project, args.out
    assert os.getuid() == 1000
    assert not args.modal_menus or args.gui
    assert not args.intro or args.gui
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
    if args.intro:
        data = (root/'tools/research-owned-intro.go').read_text()
        assert data.startswith('//go:build ignore\n')
        (source/'internal/eightsword/research_owned_intro.go').write_text(data.replace('//go:build ignore\n', '', 1))
    if args.vga_read_trace:
        data = (root/'tools/research-vga-reads.go').read_text()
        assert data.startswith('//go:build ignore\n')
        (source/'internal/eightsword/research_vga_reads.go').write_text(data.replace('//go:build ignore\n', '', 1))
    probe = (seed / 'tools/probe-friendly.go').read_text()
    if args.vga_read_trace:
        marker = '\te.EnableLiveClock(3000)'
        assert probe.count(marker) == 1
        probe = probe.replace(marker, marker + '\n\tfinishVGAReads:=e.ResearchVGAReads(*out)\n\tdefer func(){must(finishVGAReads())}()')
    probe = probe.replace('install := func() { installMap(); installBattle(); installPalace() }',
                          'installOwned, ownedFrame, finishOwned := e.ResearchOwnedScene(*out)\n'
                          '\tdefer func(){must(finishOwned())}()\n'
                          '\tinstall := func() { installMap(); installBattle(); installPalace(); installOwned() }')
    probe = probe.replace('im := e.Frame()', 'im := e.Frame()\n\t\tif own:=ownedFrame();own!=nil {im=own}')
    probe = probe.replace('write("-hd", e.Frame())',
                          'write("-hd", e.Frame())\n\t\twrite("-owned", ownedFrame())')
    if args.intro:
        probe = probe.replace('e.ResearchOwnedScene(*out)', 'e.ResearchOwnedEverything(*out)')
        marker = '\tpreload := flag.String("commands", "", "ordinary command prefix, then continue reading stdin")'
        assert probe.count(marker) == 1
        probe = probe.replace(marker, marker + '\n\tintroEscapeStep := flag.Uint64("intro-escape-step", 0, "ordinary Escape after this guest step; zero waits naturally")')
    if args.natural_intro:
        marker='\tadvance(3000)\n\tpress(1, 100, 100)\n\twait("main-menu")'
        assert probe.count(marker)==1
        loop = '\tfor i:=0;e.Tracker.VisibleScene!="main-menu" && i<10000;i++ {advance(10)}\n\twait("main-menu")'
        if args.intro:
            loop = '''
	for i:=0;e.Tracker.VisibleScene!="main-menu" && i<10000;i++ {
		advance(10)
		if *introEscapeStep != 0 && e.Oracle.Steps() >= *introEscapeStep {
			raw,err:=json.MarshalIndent(map[string]any{"requested_step":*introEscapeStep,"actual_step":e.Oracle.Steps(),"elapsed_ms":elapsed,"method":"ordinary keyboard Escape; no guest writes or snapshot loading"},"","  ");must(err)
			must(os.WriteFile(filepath.Join(*out,"intro-escape.json"),append(raw,10),0644))
			press(1,100,100)
			*introEscapeStep=0
		}
	}
	wait("main-menu")'''
        probe=probe.replace(marker,loop)
    if args.main_menu:
        start = probe.index('\tif *gameSave == "" {', probe.index('\twait("main-menu")'))
        end = probe.index('\treply("ready")', start)
        assert 'shot("01-continued-map")' in probe[start:end]
        probe = probe[:start] + '\tadvance(500)\n\tphase = "main-menu"\n\tshot("00-main-menu")\n\n' + probe[end:]
    (source / 'tools').mkdir()
    (source / 'tools/probe-owned.go').write_text(probe)
    if args.gui:
        for p in sorted((root / 'cmd/8sword').glob('*.go')):
            dest = source / p.relative_to(root)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(p.read_bytes())
            hashes[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
        gui_driver = (root / 'tools/gui-check.go').read_text()
        if args.natural_intro:
            marker = '\tif *flow != "story" && *flow != "captions" && !*showHeroine && !*showMuseum {\n\t\td.press(9)\n\t} // 原版 Esc，未直接進入 PAM。'
            assert gui_driver.count(marker) == 1
            gui_driver = gui_driver.replace(marker, '''
	if stage:=os.Getenv("EIGHTSWORD_RESEARCH_INTRO_ESCAPE_STAGE");stage!="" {
		d.wait("研究開場來源完成 "+stage,180,func(s map[string]any)bool{
			raw,err:=os.ReadFile(filepath.Join(d.out,"owned-intro-commands.jsonl"));if err!=nil{return false}
			for _,line:=range bytes.Split(raw,[]byte{'\\n'}) {
				var event struct {Command,Kind string}
				if json.Unmarshal(line,&event)==nil && event.Command=="capture" && event.Kind==stage {return true}
			}
			return false
		})
		first:=d.status()["presented_frames"].(float64)
		d.wait("研究開場完成來源後的實際Draw",20,func(s map[string]any)bool{return s["presented_frames"].(float64)>=first+2})
		d.shot("owned-intro-before-escape")
		raw,err:=json.MarshalIndent(map[string]any{"stage":stage,"status":d.status(),"method":"XTEST Escape after source event and later Draw; actual image independently checked"},"","  ");check(err)
		check(os.WriteFile(filepath.Join(d.out,"owned-intro-escape-request.json"),append(raw,10),0644))
		d.press(9)
	}
	d.wait("研究開場自然結束或Escape交接",300,func(s map[string]any)bool{return s["presented_scene"]=="main-menu"})''')
        if args.modal_menus:
            marker = '\tif *flow == "menus" {\n\t\t// Fixed new-game pages'
            assert gui_driver.count(marker) == 1
            gui_driver = gui_driver.replace(marker, '\tif *flow == "menus" || *flow == "save" {\n\t\t// Fixed new-game pages')
            marker = '\t\t\t{"f5-map", 71, 1070, []float64{1278, 1304}},'
            assert gui_driver.count(marker) == 1
            gui_driver = gui_driver.replace(marker, marker + '\n\t\t\t{"f6-search", 72, 1090, []float64{9690}},')
        if args.main_menu:
            marker = '\n\td.press(116)\n\td.press(36)\n\td.scene("new-game-confirm")\n\td.shot("04-confirm")'
            assert gui_driver.count(marker) == 1
            extra = '''
	if *flow == "save" {
		researchShot := func(name string) {
			first := d.status()["presented_frames"].(float64)
			d.wait("研究主選單已實際呈現", 20, func(s map[string]any) bool { return s["presented_frames"].(float64) >= first+2 })
			d.shot(name)
		}
		d.press(111) // 原版向上循環至音樂欣賞。
		researchShot("main-menu-wrapped")
		d.press(36)
		d.wait("音樂欣賞完整目錄", 25, func(s map[string]any) bool {
			for _, item := range s["strings"].([]any) {
				if item.(map[string]any)["Source"] == float64(758) { return true }
			}
			return false
		})
		researchShot("main-menu-music")
		d.press(116)
		researchShot("main-menu-music-selection")
		d.press(9)
		d.scene("main-menu")
		d.press(116)
		d.press(36)
		d.scene("new-game-confirm")
		researchShot("main-menu-new-confirm")
		d.press(114) // 原版選「否」，再確定取消。
		researchShot("main-menu-new-no")
		d.press(36)
		d.scene("main-menu")
		researchShot("main-menu-cancelled")
		d.press(111) // 回到預設繼續；下方既有流程再選新遊戲。
	}
'''
            gui_driver = gui_driver.replace(marker, extra + marker)
        (source / 'tools/gui-check.go').write_text(gui_driver)
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
        if args.intro:
            engine=engine.replace('type Engine struct {','type Engine struct {\n\tresearchOwnedReference *image.RGBA\n')
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
        if args.intro:
            engine=engine.replace('e.ResearchOwnedScene(dir)','e.ResearchOwnedEverything(dir)')
            engine=engine.replace('if e.researchOwnedRender!=nil {defer func(){if own:=e.researchOwnedRender();own!=nil {result=own}}()}',
                'defer func(){e.researchOwnedReference=result;if e.researchOwnedRender!=nil {if own:=e.researchOwnedRender();own!=nil {result=own}}}()')
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
    if args.build:
        assert Path('/.dockerenv').is_file() and Path('/dosgolem/go.mod').is_file()
        for name in ('GOCACHE', 'GOMODCACHE'):
            cache = Path(os.environ[name])
            assert cache.is_dir() and cache.stat().st_uid == 1000
        version = subprocess.check_output(['go', 'version'], text=True)
        assert version.startswith('go version go1.24.13 linux/amd64')
        work = Path('/tmp/8sword-owned.work')
        work.write_text(f'go 1.24.0\nuse (\n {source}\n /dosgolem\n)\n')
        env = dict(os.environ, GOWORK=str(work), GOMAXPROCS='2')
        format_paths = [source/'internal/eightsword/research_owned_scene.go', source/'internal/eightsword/engine.go',
                        source/'tools/probe-owned.go']
        if args.gui:
            format_paths.append(source/'tools/gui-check.go')
        if args.intro:
            format_paths.append(source/'internal/eightsword/research_owned_intro.go')
        if args.vga_read_trace:
            format_paths.append(source/'internal/eightsword/research_vga_reads.go')
        subprocess.run(['gofmt', '-w', *map(str, format_paths)], check=True, timeout=30)
        targets = [('probe', './tools/probe-owned.go')]
        if args.gui:
            targets += [('8sword', './cmd/8sword'), ('gui-check', './tools/gui-check.go')]
        for name, package in targets:
            subprocess.run(['go', 'build', '-o', str(out/name), package], cwd=source, env=env, check=True, timeout=120)
        (out/'build-go-version.txt').write_text(version)
        digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
        inputs = {str(p.relative_to(source)): digest(p) for p in sorted(source.rglob('*')) if p.is_file()}
        (out/'build-inputs.sha256').write_text(''.join(h+'  '+n+'\n' for n,h in inputs.items()))
        (out/'build-outputs.sha256').write_text(''.join(digest(out/n)+'  '+n+'\n' for n,_ in targets))
    print(json.dumps({'out': str(out), 'production_inputs': len(hashes), 'research_only': True}))


if __name__ == '__main__':
    main()
