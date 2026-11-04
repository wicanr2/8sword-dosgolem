#!/usr/bin/env python3
"""原版操作整合候選：來源凍結、收據核對及本機永久保存。只在 Docker 執行。"""
import argparse, gzip, hashlib, importlib.util, json, os, shutil
from pathlib import Path

REL = 'workplace/probe-20261023/graphics-first/battle-r1/original-player-integration-r1'
BATCH = 'original-player-integration-r1'

def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p, data):
    with p.open('x') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['freeze', 'audit', 'archive', 'verify'])
    p.add_argument('--project', type=Path)
    p.add_argument('--archive', type=Path)
    p.add_argument('--out', type=Path)
    a = p.parse_args()
    assert Path('/.dockerenv').exists() and os.getuid() == 1000
    if a.action == 'verify':
        index = read(a.archive / (BATCH + '.json'))
        for row in index['files']:
            ob = index['objects'][row['sha256']]
            f = a.archive / BATCH / ob['file']
            assert sha(f) == ob['stored_sha256']
            raw = gzip.decompress(f.read_bytes())
            assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
        write(a.out, dict(status='passed-detached-original-player-integration', files=len(index['files']), objects=len(index['objects'])))
        return
    r = a.project
    q = r / REL
    spec = importlib.util.spec_from_file_location('baseline', r / 'tools/prepare-owned-army-ui.py')
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    assert baseline.dependencies(r) == read(q / 'baseline.json')
    spec = importlib.util.spec_from_file_location('art', r / 'tools/original-battle-art.py')
    art = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(art)
    if a.action == 'freeze':
        names = set(read(r / 'preserved/owned-player-source-manifest-r1.json')) | {str(f.relative_to(r)) for f in (r / 'internal/ownedworld').glob('*.go')} | set(art.EXTRA)
        assert not (q / 'source').exists()
        for n in sorted(names):
            dst = q / 'source' / n
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(art.patched_scene(r) if n == art.SCENE else (r / n).read_bytes())
        write(q / 'source-manifest.json', {n: sha(q / 'source' / n) for n in sorted(names)})
        shutil.copyfile(r / 'tools/source-battle-art.patch', q / 'source-battle-art.patch')
        return
    if a.action == 'audit':
        manifest = read(q / 'source-manifest.json')
        for n, d in manifest.items():
            assert sha(q / 'source' / n) == d
            assert (hashlib.sha256(art.patched_scene(r)).hexdigest() if n == art.SCENE else sha(r / n)) == d, n
        assert sha(r / art.SCENE) == read(r / 'preserved/owned-player-source-manifest-r1.json')[art.SCENE]
        chain = read(q / 'player-chain-r1/receipt.json')
        cold = read(q / 'player-chain-r1/process-cold/receipt.json')
        assert [v['mode'] for v in chain['phases']] == ['random', 'guard', 'random']
        assert [v['round_result'] for v in chain['phases']] == ['retreat', 'win', 'retreat']
        assert chain['F7'] == 1 and chain['F2_F3_original'] and chain['same_process']
        assert not chain['legacy_card_controller'] and not cold['legacy_card_controller']
        for key in ['army', 'resources', 'location', 'world_sha256']: assert chain[key] == cold[key], key
        assert cold['separate_process'] and not cold['snapshot_loaded']
        for n in ['tests-chain-r2.log', 'tests-cold-r1.log']:
            assert (q/n).read_text().rstrip().endswith('PASS'), n
        gui = read(q/'gui-r1/receipt.json')
        assert gui['F2'] and gui['F3'] and gui['cancel_preserves_token'] and gui['canvas_matches_presented'] and not gui['legacy_card']
        rust = read(q/'rust-native-r1.json')
        assert rust['vectors'] == 201 and rust['tests_passed'] == 2 and not rust['original_executable_mounted'] and not rust['go_mounted']
        assert sha(q/'rust-reference.tsv') == sha(r/'internal/remake-rust/reference.tsv') == rust['reference_sha256']
        assert (q/'tests-rust-reference-r1.log').read_text().rstrip().endswith('PASS')
        write(a.out, dict(status='passed-original-player-integration-audit', source_files=len(manifest), chain=chain, cold=cold, GUI=gui, Rust=rust, source_manifest_sha256=sha(q/'source-manifest.json'), formal_runtime_unchanged=True, schema_unchanged=True, limits=['Engine normal-input sampling with explicit army/coordinate fixtures; not natural clear.', 'Original battle rules only. Native rules/AI toolbar and hand-drawn action poses move to the Rust phase.', 'Prepared development entry continues an imported world save. New-game creation and mid-battle restart are not enabled.']))
        return
    folder = a.archive / BATCH
    folder.mkdir()
    files, objects = [], {}
    for f in sorted(q.rglob('*')):
        if not f.is_file() or any(n in f.relative_to(q).parts for n in ['build-cache', 'rust-target']): continue
        assert f.stat().st_uid == 1000 and not f.is_symlink()
        raw = f.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        obj = folder / (digest + '.gz')
        if digest not in objects:
            obj.write_bytes(gzip.compress(raw, 6, mtime=0))
            objects[digest] = dict(file=obj.name, stored_sha256=sha(obj))
        files.append(dict(path=str(f.relative_to(r)), bytes=len(raw), sha256=digest, mode=f.stat().st_mode & 0o777))
    write(a.out, dict(files=files, objects=objects, rights='Original data, full frames, states and binaries remain local only. No release.'))

if __name__ == '__main__': main()
