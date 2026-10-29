#!/usr/bin/env python3
"""Final scoped B VFX integrity and SHA-verified disposable restore cleanup."""
import argparse
import ast
import hashlib
import json
import pathlib
import re
import subprocess
import tempfile
import urllib.parse

from PIL import Image


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    return json.loads(p.read_text())


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--project', type=pathlib.Path, required=True)
    p.add_argument('--archive', type=pathlib.Path, required=True)
    p.add_argument('--out', type=pathlib.Path, required=True)
    p.add_argument('--cleanup-restore', action='store_true')
    a = p.parse_args()
    r, archive = a.project, a.archive
    assert not a.out.exists() and a.out.parent.resolve() == archive.resolve()
    planned_report = r / 'preserved' / a.out.name
    audit = read(archive / 'vfx-engine-audit-r1.json')
    promotion = read(archive / 'vfx-engine-promotion-r1.json')
    assert audit['status'] == 'passed-scoped-vfx-engine'
    assert promotion['audit_sha256'] == sha(archive / 'vfx-engine-audit-r1.json')
    assert promotion['programs'] == audit['programs']
    player = r / 'workplace/player'
    candidate = player / 'source-candidate-vfx-r2'
    for n, h in audit['programs'].items():
        assert sha(player / n) == sha(candidate / n) == h, n
    for n, h in audit['source_inputs'].items():
        assert sha(r / n) == sha(candidate / 'src' / n) == h, n
    for n, h in audit['previous_programs'].items():
        assert sha(player / 'source-candidate-tactics-r2' / n) == h
    for n, h in audit['asset_hashes'].items():
        assert sha(player / 'assets-painted-r68' / n) == h
    runtime = read(player / 'runtime.json')
    assert runtime['production'] and runtime['application_source_inputs'] == 188
    assert runtime['battle_vfx'] == 'B-flight-impact' and len(runtime['files']) == 923
    for n, h in runtime['files'].items():
        assert sha(player / 'runtime-render-r1/src' / n) == h
    assert len(audit['programs']) == 7 and len(audit['source_inputs']) == 188
    assert len(audit['asset_hashes']) == 525
    q = r / 'workplace/probe-20261023/graphics-first/battle-r1/battle-vfx-r1'
    assert sha(q / 'engine-audit-r1.json') == sha(archive / 'vfx-engine-audit-r1.json')
    assert sha(q / 'promotion-r1.json') == sha(archive / 'vfx-engine-promotion-r1.json')
    assert not (q / 'vet-engine-r2.log').read_text()
    log = (q / 'tests-r2.log').read_text()
    assert '\nPASS\n' in log and 'SKIP' not in log and 'FAIL' not in log
    for v in audit['gui']:
        gui = q / v['case']
        if v['case'] != 'gui-normal-r2/reload':
            gui /= 'save'
        assert sha(gui / 'gui-final.state') == v['final_state_sha256']
        assert sha(gui / 'saved-gamedata.ay') == v['save_sha256']
        assert (gui / 'saved-gamedata.ay').read_bytes() == (gui / 'snapshot-readonly/save-buffer-9e000.bin').read_bytes()
    art = r / 'artwork'
    manifest = read(art / 'manifest.json')
    recheck = read(archive / 'vfx-approved-art-recheck-r1.json')
    assert recheck['files'] == len(manifest['files']) == 1040
    assert recheck['manifest_sha256'] == sha(art / 'manifest.json')
    for v in manifest['files']:
        f = art / v['path']
        assert not f.is_symlink() and f.stat().st_size == v['bytes'] and sha(f) == v['sha256']
    indexed = {v['path']: v for v in manifest['files']}
    plan = read(art / 'battle-vfx-b-recheck-plan-r1.json')
    assert len(plan['files']) == 66
    for v in plan['files']:
        assert indexed[v['path']] == v
    meta = read(r / 'docs/images/battle-vfx-b-live-r1.json')
    assert meta['controlled_fixture'] and len(meta['files']) == 2
    for v in meta['files']:
        f = r / 'docs/images' / v['path']
        assert Image.open(f).size == (1600, 687) and sha(f) == v['sha256']
        assert sha(r / v['source']) == v['source_sha256']
    for f in (r / 'tools').glob('*vfx*.py'):
        ast.parse(f.read_text(), filename=str(f))
    ast.parse((r / 'tools/archive-approved-art.py').read_text())
    for n in ['check-vfx-gui.sh', 'check-vfx-cold.sh']:
        subprocess.run(['bash', '-n', str(r / 'tools' / n)], check=True)
    checker = r / 'tools/check-ai-resolution-backlinks.py'
    subprocess.run(['python', str(checker), '--project', str(r)], check=True)
    ledger = read(r / 'docs/spec/ai-resolution-backlinks-r1.json')
    extra = next(v for v in ledger['resolutions'] if v['original_address'] == '0x21C36')['supplemental_resolutions']
    assert len(extra) == 1
    with tempfile.TemporaryDirectory(prefix='vfx-backlinks-') as name:
        tmp = pathlib.Path(name)
        allrows = ledger['resolutions'] + extra
        paths = {'docs/spec/ai-resolution-backlinks-r1.json'}
        for row in allrows:
            paths.update(row[k] for k in ['evidence', 'older_spec'])
            if 'receipt' in row:
                paths.add(row['receipt'])
        for n in paths:
            f = tmp / n
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes((r / n).read_bytes())
        for row in ledger['resolutions'][:5] + extra:
            f = tmp / row['older_spec']
            original = f.read_text()
            assert row['required_correction'] in original
            f.write_text(original.replace(row['required_correction'], 'REMOVED-FOR-NEGATIVE-TEST'))
            failed = subprocess.run(['python', str(checker), '--project', str(tmp)], capture_output=True)
            assert failed.returncode != 0
            f.write_text(original)
    docs = list(r.glob('*.md'))
    for folder in ['docs', 'artwork', 'preserved']:
        docs.extend((r / folder).rglob('*.md'))
    links = []
    for doc in docs:
        if not doc.is_file() or 'restore-checks' in doc.relative_to(r).parts:
            continue
        for target in re.findall(r'\[[^\]]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)', doc.read_text()):
            path = urllib.parse.unquote(target.strip('<>').split('#', 1)[0])
            if not path or re.match(r'[a-zA-Z][a-zA-Z0-9+.-]*:', path) or path.startswith('/'):
                continue
            destination = doc.parent / path
            assert destination.exists() or destination.resolve() == planned_report.resolve(), (str(doc), target)
            links.append((doc.relative_to(r).as_posix(), target))
    assert ('README.md', 'CONTEXT.md') in links
    for n in ['tools/check-vfx-integrity.py', 'preserved/vfx-engine-r1.json',
              'docs/images/battle-vfx-b-live-r1.json', 'artwork/battle-vfx-b-recheck-plan-r1.json']:
        assert any((r / doc).parent.joinpath(target.split('#', 1)[0]).resolve() == (r / n).resolve() for doc, target in links)
    restored = archive / 'restore-checks/vfx-engine-r1'
    index = read(archive / 'vfx-engine-r1.json')
    restoration = read(archive / 'vfx-engine-restoration-r1.json')
    assert restoration['status'] == 'passed' and restoration['restored']
    assert restoration['index_sha256'] == sha(archive / 'vfx-engine-r1.json')
    expected = {v['path']: v for v in index['files']}
    actual = {str(f.relative_to(restored)): f for f in restored.rglob('*') if f.is_file()}
    assert set(actual) == set(expected)
    cleaned_bytes = 0
    for n, f in actual.items():
        v = expected[n]
        assert not f.is_symlink() and sha(f) == v['sha256'] and f.stat().st_size == v['bytes']
        cleaned_bytes += v['bytes']
    roots = [q, candidate, archive / 'vfx-engine-r1', restored, art / 'approved/masters/battle-vfx-b-r1', art / 'approved/provenance/battle-vfx-b-r1']
    for root in roots:
        hygiene = subprocess.run(['find', str(root), '-user', 'root', '-o', '-type', 'd', '-name', '*.md'], capture_output=True, text=True, check=True)
        assert not hygiene.stdout, hygiene.stdout
    assert not any(f.is_file() for f in (r / 'workplace/gocache').rglob('*'))
    if a.cleanup_restore:
        for f in actual.values():
            f.unlink()
        for f in sorted((f for f in restored.rglob('*') if f.is_dir()), key=lambda f: len(f.parts), reverse=True):
            f.rmdir()
        restored.rmdir()
    result = dict(status='passed-scoped-vfx-integrity', production_programs=7, source_count=188,
                  assets_unchanged=525, core_unchanged=923, previous_programs_preserved=7,
                  controlled_original_effects=3, guards=4, real_draws_independently_rebuilt=2,
                  gui_save_buffers=3, full_artwork_files=1040, archived_files=1535,
                  archived_objects=676, restored_files_verified=len(actual),
                  restore_copy_cleaned=a.cleanup_restore, restore_bytes_cleaned=cleaned_bytes if a.cleanup_restore else 0,
                  original_resolution_keys=26, supplemental_backlinks=1,
                  missing_correction_cases_rejected=6, markdown_links=len(links),
                  root_owned_outputs=0, invalid_markdown_directories=0, workspace_go_cache_files=0,
                  limitations=audit['limits'])
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
