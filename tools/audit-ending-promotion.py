#!/usr/bin/env python3
"""053：核對完整結局、故障、實際Draw、正常存讀及七程式提升輸入。"""
import argparse
import hashlib
import json
import os
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(path):
    return {Path(name).name:digest for digest,name in
            (line.split('  ',1) for line in path.read_text().splitlines())}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--save-audit',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and not a.out.exists()
    player = a.project/'workplace/player'
    root = a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    candidate = player/'source-candidate-ending-r1'
    previous = player/'source-candidate-story-blue-r4'
    programs = manifest(candidate/'build-outputs.sha256')
    names = {'8sword','8sword-replay','gui-check','music-check','heroine-check','museum-check','story-prelude-check'}
    assert set(programs) == names
    old = manifest(previous/'build-outputs.sha256')
    for name in names:
        assert sha(candidate/name) == programs[name]
        assert sha(previous/name) == sha(player/name) == old[name]
    inputs = {}
    for line in (candidate/'build-inputs.sha256').read_text().splitlines():
        digest,name = line.split('  ',1)
        relative = name.removeprefix('/project/')
        assert sha(a.project/relative) == sha(candidate/'src'/relative) == digest
        inputs[relative] = digest
    assert len(inputs) == 150
    base = read(root/'engine-build-r5/sources.json')['files']
    assert all(inputs[name] == digest for name,digest in base.items())
    private = read(root/'gui-build-r2/build-manifest.json')
    assert private['base']['files'] == base
    expected = {**read(player/'runtime-input-r1/runtime-input.json')['base_inputs'],
                **read(player/'runtime-input-r1/runtime-input.json')['added']}
    assert len(expected) == 921
    for name,digest in expected.items():
        assert sha(player/'runtime-input-r1/src'/name) == sha(root/'runtime-input-r1/src'/name) == digest
    core = read(player/'runtime-direct-r1/runtime-manifest.json')['base_inputs'] | read(player/'runtime-direct-r1/player-runtime.json')['changed']
    assert len(core) == 919
    for name,digest in core.items():
        assert sha(player/'runtime-direct-r1/src'/name) == expected[name] == digest
    formal = read(a.project/'workplace/probe-20261023/graphics-first/story-art-r1/blue-person-correction-r4/runtime-audit-r4.json')['asset_hashes']
    assets = root/'assets-candidate-r3'
    hashes = {f.name:sha(f) for f in assets.iterdir()}
    assert len(hashes) == 433 and len(formal) == 425
    for name,digest in formal.items():
        assert sha(player/'assets-painted-r56'/name) == hashes[name] == digest
    assert all(f.is_file() and not f.is_symlink() and f.stat().st_uid == 1000 for f in assets.iterdir())
    engine = read(root/'engine-audit-r5.json')
    assert engine['status'] == 'verified-Engine-ending-candidate' and engine['actual_handoff_skipped_x86'] == 52940401
    assert engine['tool_sha256'] == sha(a.project/'tools/audit-ending-engine.py')
    assert engine['source_manifest_sha256'] == sha(root/'engine-build-r5/sources.json')
    assert engine['asset_manifest_sha256'] == hashes['ending.json']
    assert engine['binary_sha256'] == sha(root/'ending-engine-tests-r5')
    for name,digest in engine['run_receipts'].items():
        assert sha(root/'runtime-r5'/name/'runtime.json') == digest
    log = (root/'runtime-r5.log').read_text()
    for test in ('EndingSourceFaultStops','EndingSourceRuntime','EndingInputHandoffGuard','EndingAssetsFaults','SourceRuntimeNormalAndControlledFault'):
        assert '--- PASS: Test'+test in log
    assert log.endswith('PASS\n') and '--- FAIL:' not in log
    faults = {}
    for name,reason in [('display-mode','unhandled-display-mode'),('unknown-source','unclassified-source-bitmap'),('required-noto','missing-or-invalid-ending-assets')]:
        f = root/'runtime-r5'/('fault-'+name)/'fault.json'
        data = read(f)
        assert data['fault']['phase'] == 'ending' and data['fault']['reason'] == reason and data['rejected_advances'] == 6
        faults[name] = dict(reason=reason,sha256=sha(f),held_pixels=data['held_pixels'])
    for name,escape in [('gui-full-audit-r2.json',False),('gui-escape-audit-r1.json',True)]:
        report = read(root/name)
        assert report['status'] == 'PASS-ending-actual-Draw' and report['escape'] == escape
        assert report['tool_sha256'] == sha(a.project/'tools/audit-ending-gui.py')
        assert report['build_sha256'] == sha(root/'gui-build-r2/build-manifest.json')
    save = read(a.save_audit)
    assert save['status'] == 'PASS-ending-candidate-normal-save-reload'
    assert save['build_sha256'] == sha(candidate/'build-inputs.sha256') and save['source_files'] == 150
    assert save['tool_sha256'] == sha(a.project/'tools/audit-ending-save.py')
    assert save['binaries'] == {n:programs[n] for n in ('8sword','gui-check')}
    assert save['save_bytes'] == 2987 and set(save['font_draws']) == {'noto','lishu','caoshu'}
    original = read(a.project/'workplace/intake-20261023/source-manifest.json')
    originals = [f for f in original['files'] if f['path'].startswith('game/8sword/')]
    assert len(originals) == 158
    for row in originals:
        assert sha(a.project/'workplace/intake-20261023/sources'/row['path']) == row['sha256']
    result = dict(schema=1,spec='053',status='PASS-scoped-053-ending-engine',production=False,
                  candidate=candidate.name,previous=previous.name,assets='assets-candidate-r3',target_assets='assets-painted-r57',
                  programs=programs,previous_programs=old,build_inputs_sha256=sha(candidate/'build-inputs.sha256'),
                  asset_hashes=hashes,preserved_assets=425,core_files=921,original_files=158,
                  runtime_sha256=sha(candidate/'runtime.json'),faults=faults,
                  engine_audit_sha256=sha(root/'engine-audit-r5.json'),full_draw_audit_sha256=sha(root/'gui-full-audit-r2.json'),
                  escape_draw_audit_sha256=sha(root/'gui-escape-audit-r1.json'),save_audit_sha256=sha(a.save_audit),
                  tool_sha256=sha(Path(__file__)),limits=['Ending source scene and three fonts only; other ending art remains source pixels.',
                  'Controlled original ending branch, no natural victory claim. Original music remains native OPL.',
                  'GUI uses Linux software graphics with muted device; no physical GPU or other-platform claim.'])
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],programs=7,assets=433,source_files=150,core_files=921)))


if __name__ == '__main__':
    main()
