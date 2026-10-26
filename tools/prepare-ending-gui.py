#!/usr/bin/env python3
"""053：以凍結候選建立隔離視窗診斷，不把受控結局分支接入正式程式。"""
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
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    a.out.mkdir()
    before = {str(f.relative_to(a.source)): sha(f) for f in a.source.rglob('*') if f.is_file()}
    shutil.copytree(a.source, a.out/'src')
    source = a.out/'src'

    def replace(name, old, new):
        f = source/name
        text = f.read_text()
        assert text.count(old) == 1, name
        f.write_text(text.replace(old, new))

    replace('cmd/8sword/main.go', 'status := g.engine.Status()',
            'status := g.engine.Status()\n status["research_ending"] = g.engine.ResearchEndingStatus()')
    replace('cmd/8sword/main.go', 'started := time.Now()\n\tif err := g.engine.AdvanceCycles',
            'if err := g.engine.ResearchEndingTick(g.capture); err != nil { return err }\n started := time.Now()\n\tif err := g.engine.AdvanceCycles')
    replace('cmd/8sword/main.go', 'g.frame = g.engine.Frame()',
            'g.frame = g.engine.Frame()\n if err := g.engine.ResearchEndingFrame(g.frame); err != nil {return err}')
    replace('cmd/8sword/main.go', 'g.draws++',
            'g.draws++\n if err := g.engine.ResearchEndingDraw(g.capture,g.frame,g.draws);err!=nil {g.recordErr=err}')
    probe = a.project/'tools/ending-gui-probe.go'
    (source/'internal/eightsword/ending_gui_probe.go').write_text(probe.read_text().removeprefix('//go:build ignore\n'))
    driver = (a.project/'tools/gui-check.go').read_text()
    marker = '\tif *actorWalk && *flow == "save" {'
    assert driver.count(marker) == 1
    extension = '''
    if *flow == "ending-full" || *flow == "ending-escape" {
        d.press(73); d.scene("system-menu"); d.press(114)
        before := d.status()["steps"].(float64)
        d.press(36); d.confirmation(before); d.press(36)
        seen := func(s map[string]any,key string) bool {
            probe,_ := s["research_ending"].(map[string]any)
            found,_ := probe["seen"].(map[string]any)
            return found[key] == true
        }
        d.wait("結局Noto對話已實際Draw",120,func(s map[string]any)bool{return seen(s,"END5.AY-noto")})
        d.shot("ending-01-noto")
        if *flow == "ending-escape" {
            d.key(9,true)
        } else {
            for _, id := range []string{"lishu","caoshu","noto"} {
                d.press(76)
                d.wait("結局字型已實際Draw "+id,20,func(s map[string]any)bool{return seen(s,"END5.AY-"+id)})
                d.shot("ending-font-"+id)
            }
            d.wait("結局後段已實際Draw",180,func(s map[string]any)bool{return seen(s,"END9.AY-noto")})
        }
        d.wait("原版結局退出DOS",180,func(s map[string]any)bool{return s["closed"]==true && s["exited"]==true && s["exit_code"]==float64(0)})
        d.receipt(*flow)
        return
    }
'''
    (a.out/'gui-check.go').write_text(driver.replace(marker,extension+marker))
    after = {str(f.relative_to(source)): sha(f) for f in source.rglob('*') if f.is_file()}
    manifest = dict(schema=1,spec='053',production=False,source=str(a.source),base_inputs=before,
                    diagnostic_inputs=after,changed=[k for k in after if after[k] != before.get(k)],
                    tool_sha256=sha(Path(__file__)),probe_sha256=sha(probe),driver_sha256=sha(a.out/'gui-check.go'),
                    scope='private controlled RAM branch; actual XTEST input and Ebiten Draw')
    (a.out/'preparation.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(source_files=len(before),changes=manifest['changed'])))


if __name__ == '__main__':
    main()
