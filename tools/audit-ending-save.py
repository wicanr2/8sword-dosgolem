#!/usr/bin/env python3
"""053：核對未含研究掛點的候選正常存讀、三字型與完整Draw串流。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name,path):
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('project','gui','assets','build','out'):
        p.add_argument('--'+key,type=Path,required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and not a.out.exists()
    root = a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    manifest_path = a.build/'sources.json'
    if manifest_path.exists():
        build = read(manifest_path)
    else:
        manifest_path = a.build/'build-inputs.sha256'
        build = {'files': {path.removeprefix('/project/'):digest for digest,path in
                 (line.split('  ',1) for line in manifest_path.read_text().splitlines())}}
    for name,digest in build['files'].items():
        assert sha(a.build/'src'/name) == sha(a.project/name) == digest
    assert not (a.build/'src/internal/eightsword/ending_gui_probe.go').exists()
    executables = {Path(path).name:digest for digest,path in
                   (line.split('  ',1) for line in (a.gui/'executables.sha256').read_text().splitlines())}
    for name in ('8sword','gui-check'):
        assert sha(a.build/name) == executables[name]
    saved = a.gui/'scratch/gamedata.ay'
    assert saved.stat().st_size == 2987
    assert sha(saved) == read(a.gui/'save/saved.json')['sha256']
    assert saved.read_bytes() == (a.gui/'save/snapshot-readonly/save-buffer-9e000.bin').read_bytes()
    assert saved.read_bytes() == (a.gui/'reload/snapshot-readonly/save-buffer-9e000.bin').read_bytes()
    helper = load('ending_save_stream',a.project/'tools/audit-army-dismiss.py')
    font_helper = load('ending_save_fonts',a.project/'tools/audit-source-player.py')
    profiles = helper.fonts(a.assets)
    fonts,phases = {},{}
    for name in ('save','reload'):
        q = a.gui/name
        st = read(q/'gui-final.json')
        assert st['closed'] and st['hd'] and st['source_renderer'] and st['source_frames'] > 0 and st['direct_calls'] > 0
        assert st['owned_render_fault'] is None and st['unimplemented'] == [] and 'research_ending' not in st
        for key,value in st.items():
            if key.endswith('_error'):
                assert not value,(name,key,value)
        assert not st['music']['load_error'] and not st['music']['binding_error']
        assert st['toolbar_error'] == '' and st['presentation_size'] == [2944,1264]
        assert st['ending']['active'] is False and st['ending']['bound'] is False
        assert st['text']['ComposedFrames'] == st['text']['CachedFrames'] == st['graphics']['CompositedFrames'] == 0
        assert st['text']['MissingGlyphs'] == 0 and not st['text']['Errors']
        assert read(q/'gui-input-receipt.json')['flow'] == name
        metadata = [json.loads(line) for line in (q/'intro-draw.jsonl').read_text().splitlines()]
        count = 0
        for n,step,im in helper.stream(q):
            count += 1
            assert metadata[n-1]['draw'] == n and metadata[n-1]['step'] == step
            font = metadata[n-1]['font_id']
            if font not in fonts:
                points = font_helper.font_points(im,profiles,font)
                if points:
                    fonts[font] = dict(phase=name,draw=n,opaque_points=points)
        assert count == st['recorded_frames'] == st['presented_frames'] == len(metadata)
        assert read(q/'continuous-audit.json')['recording_sha256'] == sha(q/'presentation.frames.gz')
        assert read(q/'continuous-audit.json')['frames'] == count
        if name == 'save':
            assert st['exited'] and st['exit_code'] == 0
        else:
            assert not st['exited'] and st['presented_scene'] == 'map' and st['font_id'] == 'caoshu'
            reads = [e for e in st['file_ops'] if e['Op'] == 'read' and e['Name'] == 'gamedata.ay']
            assert len(reads) == 1 and reads[0]['Pos'] == 0 and reads[0]['Len'] == 2987 and not reads[0]['Failed']
        phases[name] = dict(draws=count,source_frames=st['source_frames'],direct_calls=st['direct_calls'],
                            old_compositor_frames=0,gui_final_sha256=sha(q/'gui-final.json'),stream_sha256=sha(q/'presentation.frames.gz'))
    assert set(fonts) == {'noto','lishu','caoshu'}
    assert read(a.gui/'settings.json')['font'] == 'caoshu'
    result = dict(schema=1,spec='053',status='PASS-ending-candidate-normal-save-reload',production=False,
                  phases=phases,font_draws=fonts,save_bytes=2987,save_sha256=sha(saved),source_files=len(build['files']),
                  build_sha256=sha(manifest_path),binaries={name:executables[name] for name in ('8sword','gui-check')},tool_sha256=sha(Path(__file__)),
                  limits=['Ordinary XTEST player path, no controlled ending branch.',
                          'Snapshots are inspected at zero instructions after both real GUI sessions.',
                          'Linux software graphics and muted device; other platforms and listening remain unverified.'])
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],phases=phases,fonts=fonts)))


if __name__ == '__main__':
    main()
