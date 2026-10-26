#!/usr/bin/env python3
"""053：核對END5幾何、五來源與實際演出的獨立完整Frame。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from PIL import Image, ImageChops, __version__


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--runtime',default='runtime-r6')
    p.add_argument('--assets',default='assets-end5-candidate-r1')
    p.add_argument('--promotion',action='store_true')
    p.add_argument('--engine-audit',type=Path)
    p.add_argument('--gui-audit',type=Path)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    root = a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    assets = root/a.assets
    manifest = read(assets/'ending-portrait.json')
    assert sha(assets/'ending-portrait.json') == '384bc2ecb1e280dd487ce3ed6fb3981d2e28da0c98031cd132ccefce4519eb80'
    registration = read(root/'end5-registration-r1/registration.json')
    normalized = {}
    for name,record in registration['inputs'].items():
        assert sha(root/record['image']) == record['sha256'] and sha(root/record['prompt']) == record['prompt_sha256']
        im = Image.open(root/record['image']).convert('RGBA')
        normalized[name] = im.crop(record['source_rect']).resize((1920,600),Image.Resampling.LANCZOS)
    expected = [normalized['base'],normalized['base'].crop((1464,108,1656,288)),normalized['blink'].crop((1464,108,1656,288)),
                normalized['speech'].crop((1488,390,1608,480)),normalized['base'].crop((1488,390,1608,480))]
    records = read(root/'source.json')['records']
    sources = {}
    for record in records:
        if record['color_variant']:
            im = Image.open(root/record['image']).convert('RGBA')
            assert hashlib.sha256(im.tobytes()).hexdigest() == record['decoded_rgba_sha256']
            sources[record['record_sha256']] = im
    ids = {}
    for i,record in enumerate(manifest['records']):
        assert record['record'] == i
        path = assets/record['file']
        assert sha(path) == record['sha256']
        assert expected[i].tobytes() == Image.open(path).convert('RGBA').tobytes()
        ids[record['source_sha256']] = i
    spec = importlib.util.spec_from_file_location('end5_pillow',a.project/'tools/audit-ending-gui.py')
    model = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model)
    run = root/a.runtime/'hd'
    receipt = read(run/'runtime.json')
    assert receipt['ending']['portrait'] == dict(loaded=True,textures=5,error='')
    results,seen = [],set()
    for snapshot in receipt['portrait_snapshots']:
        key = snapshot['pose']
        meta = read(run/('portrait-'+key+'.json'))
        assert meta['pose'] == key and meta['step'] == snapshot['step'] and meta['pure'] and meta['font'] == 'noto'
        eye,mouth = 1,4
        for op in meta['ops']:
            if op['kind'] != 'bitmap' or op['SourceSHA'] not in ids:
                continue
            record = ids[op['SourceSHA']]
            seen.add(record)
            if record == 0: eye,mouth = 1,4
            elif record in (1,2): eye = record
            else: mouth = record
        assert key == f'eye-{eye}-mouth-{mouth}'
        path = run/('portrait-'+key+'.png')
        assert model.reconstruct(meta,assets,sources).tobytes() == Image.open(path).convert('RGBA').tobytes()
        results.append(dict(pose=key,step=meta['step'],image_sha256=sha(path),metadata_sha256=sha(run/('portrait-'+key+'.json'))))
    assert len(results) >= 3 and seen == {0,1,2,3,4}
    unchanged = []
    for sample in (2,3,4):
        for font in ('noto','lishu','caoshu'):
            filename = f'sample-{sample:02d}-{font}.png'
            assert (run/filename).read_bytes() == (root/'runtime-r5/hd'/filename).read_bytes()
            unchanged.append(filename)
    for font in ('noto','lishu','caoshu'):
        current = Image.open(run/f'sample-01-{font}.png').convert('RGB')
        old = Image.open(root/'runtime-r5/hd'/f'sample-01-{font}.png').convert('RGB')
        bbox = ImageChops.difference(current,old).getbbox()
        assert bbox and bbox[0] >= 0 and bbox[1] >= 300 and bbox[2] <= 1920 and bbox[3] <= 900
    result = dict(schema=1,spec='053',status='PASS-END5-five-texture-runtime',production=False,
                  texture_sources=sorted(seen),representatives=results,unchanged_other_scene_frames=unchanged,
                  difference_within_original_base_rectangle=True,original_art_inputs_preserved=True,
                  runtime_sha256=sha(run/'runtime.json'),manifest_sha256=sha(assets/'ending-portrait.json'),
                  registration_sha256=sha(root/'end5-registration-r1/registration.json'),
                  tool_sha256=sha(Path(__file__)),model_tool_sha256=sha(a.project/'tools/audit-ending-gui.py'),
                  limits=['Original cleanup branch is controlled; no natural victory claim.',
                          'Source-clock headless Frames; actual GUI and formal promotion are separate gates.'])
    if a.promotion:
        assert a.engine_audit and a.gui_audit
        engine,gui = read(a.engine_audit),read(a.gui_audit)
        assert engine['tool_sha256'] == sha(a.project/'tools/audit-ending-engine.py')
        assert engine['total_assets'] == 439 and engine['unchanged_base_assets'] == 433
        assert engine['portrait_manifest_sha256'] == sha(assets/'ending-portrait.json')
        assert gui['status'] == 'PASS-ending-actual-Draw' and gui['portrait_loaded'] is True
        assert gui['tool_sha256'] == sha(a.project/'tools/audit-ending-gui.py')
        player = a.project/'workplace/player'
        candidate,previous = player/'source-candidate-end5-r1',player/'source-candidate-ending-r1'
        programs = {Path(n).name:d for d,n in (line.split('  ',1) for line in (candidate/'build-outputs.sha256').read_text().splitlines())}
        old = {Path(n).name:d for d,n in (line.split('  ',1) for line in (previous/'build-outputs.sha256').read_text().splitlines())}
        assert len(programs) == len(old) == 7
        for name,digest in programs.items():
            assert sha(candidate/name) == digest
            assert sha(player/name) == sha(previous/name) == old[name]
        inputs = {}
        for line in (candidate/'build-inputs.sha256').read_text().splitlines():
            digest,name = line.split('  ',1)
            relative = name.removeprefix('/project/')
            assert sha(a.project/relative) == sha(candidate/'src'/relative) == digest
            inputs[relative] = digest
        assert len(inputs) == 152
        frozen = read(root/'engine-build-r6/sources.json')['files']
        assert all(inputs[n] == d for n,d in frozen.items())
        private = read(root/'gui-build-r4/build-manifest.json')
        assert private['base']['files'] == frozen and gui['build_sha256'] == sha(root/'gui-build-r4/build-manifest.json')
        core = read(player/'runtime-input-r1/runtime-input.json')
        for name,digest in (core['base_inputs']|core['added']).items():
            assert sha(player/'runtime-input-r1/src'/name) == digest
        old_assets = read(root/'ending-promotion-audit-r1.json')['asset_hashes']
        assert len(old_assets) == 433
        for name,digest in old_assets.items():
            assert sha(player/'assets-painted-r57'/name) == sha(assets/name) == digest
        assert len(list(assets.iterdir())) == 439 and all(not f.is_symlink() for f in assets.iterdir())
        result.update(status='PASS-scoped-053-ending-portrait',candidate=candidate.name,previous=previous.name,
                      assets=a.assets,target_assets='assets-painted-r58',programs=programs,previous_programs=old,
                      build_inputs_sha256=sha(candidate/'build-inputs.sha256'),runtime_sha256=sha(candidate/'runtime.json'),
                      asset_hashes={f.name:sha(f) for f in assets.iterdir()},preserved_assets=433,core_files=921,source_inputs=152,
                      engine_audit_sha256=sha(a.engine_audit),gui_audit_sha256=sha(a.gui_audit),
                      normal_save_reference_sha256=sha(root/'gui-formal-save-audit-r1.json'),
                      normal_save_scope='r57 true-save GUI evidence retained; this change adds only END5 display assets and loader. No new save claim.')
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],sources=5,representatives=len(results))))


if __name__ == '__main__':
    main()
