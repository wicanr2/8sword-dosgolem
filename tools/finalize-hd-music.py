#!/usr/bin/env python3
"""008: merge existing nine cues into current assets, audit PCM, preserve, promote."""
import argparse
import array
import ast
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import urllib.parse


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    with path.open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


def catalog(folder):
    assert folder.is_dir() and folder.stat().st_uid == 1000
    assert all(f.is_file() and not f.is_symlink() for f in folder.iterdir())
    return {f.name: sha(f) for f in sorted(folder.iterdir())}


def compare_pcm(run, assets):
    receipt = read(run / 'receipt.json')
    assert receipt['status'] == 'PASS-candidate-only-normal-ten-music-entries'
    assert receipt['normal_inputs'] and not receipt['ram_injection'] and not receipt['snapshot_loaded']
    assert receipt['native_pcm_equal_after_escape']
    control = read(run / 'control/final-receipt.json')
    candidate = read(run / 'candidate/final-receipt.json')
    for key in ['file_ops', 'input_events']:
        assert control[key] == candidate[key]
    assert control['music']['events'] == candidate['music']['events']
    assert sha(run / 'control/final.state') == sha(run / 'candidate/final.state')
    for status, count in [(control, 1), (candidate, 10)]:
        assert status['source_renderer'] and status['hd']
        assert status['owned_render_fault'] is None
        assert not any(status[k] for k in ['unimplemented', 'asset_error', 'graphics_error'])
        assert status['music']['loaded_cues'] == count
        assert not status['music']['load_error'] and not status['music']['binding_error']
    pcm = array.array('h', (run / 'candidate/output-s16le-stereo.pcm').read_bytes())
    native = array.array('h', (run / 'control/output-s16le-stereo.pcm').read_bytes())
    assert len(pcm) == len(native) == receipt['audio_frames'] * 2
    assert pcm[-96000:] == native[-96000:]
    cues = {v['id']: v for v in read(assets / 'music.json')['cues']}
    measured = []
    for point in receipt['checkpoints']:
        name = point['name']
        assert sha(run / 'control' / (name + '.png')) == sha(run / 'candidate' / (name + '.png'))
        if not name.endswith('-cue-first'):
            continue
        ident = int(name[:2])
        cue = cues[ident]
        assert sha(assets / cue['file']) == cue['sha256']
        info = json.loads(subprocess.check_output([
            'ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(assets / cue['file'])], timeout=30))['streams']
        assert len(info) == 1 and info[0]['codec_name'] == 'vorbis'
        assert int(info[0]['sample_rate']) == 48000 and info[0]['channels'] == 2
        raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-nostdin', '-i', str(assets / cue['file']),
                                       '-f', 'f32le', '-'], timeout=120)
        decoded = array.array('f', raw)
        frames = cue['frames']
        assert len(decoded) == frames * 2 and all(math.isfinite(x) for x in decoded)
        peak = max(abs(v) for v in decoded)
        rms_full = math.sqrt(sum(v * v for v in decoded) / len(decoded))
        assert .001 < peak < 1 and rms_full > .0001
        join = max(abs(decoded[c] - decoded[-2 + c]) for c in range(2))
        assert join < .1
        status = point['candidate_music']
        assert status['mode'] == 'hd' and status['cue'] == ident
        position, absolute = status['frame'], point['audio_frame']
        assert absolute > 4800 and frames > position > 4800
        actual = pcm[(absolute - 4800) * 2:absolute * 2]
        comparisons = []
        for offset in range(-3, 4):
            squared = 0
            maximum = 0
            for i, value in enumerate(actual):
                frame = (position - 4800 + i // 2 + offset) % frames
                expected = decoded[frame * 2 + i % 2] * 32767
                expected = math.floor(expected + .5) if expected >= 0 else math.ceil(expected - .5)
                delta = value - expected
                squared += delta * delta
                maximum = max(maximum, abs(delta))
            comparisons.append((math.sqrt(squared / len(actual)), offset, maximum))
        rms, offset, maximum = min(comparisons)
        assert rms < 32, (ident, rms, offset)
        measured.append(dict(cue=ident, title=cue['title'], frames=frames, peak=peak,
                             rms_full=rms_full, loop_join=join, compared_stereo_frames=4800,
                             rms_int16=rms, calibration_frames=offset, max_int16_error=maximum))
    assert {v['cue'] for v in measured} == set(range(1, 11))
    points = {v['name']: v for v in receipt['checkpoints']}
    assert len(points) == 14
    first, full, restart = [points[n]['candidate_music'] for n in
                            ['06-cue-first', '06-cue-full-loop', '06-cue-restart']]
    assert full['loops'] > first['loops']
    assert restart['starts'] == full['starts'] + 1 and restart['frame'] < 48000
    return dict(compared_cues=measured, checkpoints=14, audio_frames=receipt['audio_frames'],
                native_equal_after_escape_frames=48000,
                full_state_sha256=sha(run / 'candidate/final.state'))


def verify(archive, out):
    index = archive / 'hd-music-r1.json'
    data = read(index)
    checked = set()
    for item in data['files']:
        path = Path(item['path'])
        assert not path.is_absolute() and '..' not in path.parts
        h = item['sha256']
        obj = data['objects'][h]
        f = archive / 'hd-music-r1' / obj['file']
        assert sha(f) == obj['stored_sha256']
        raw = gzip.decompress(f.read_bytes())
        assert hashlib.sha256(raw).hexdigest() == h and len(raw) == item['bytes']
        checked.add(h)
    write(out, dict(status='passed-detached-hd-music', files=len(data['files']), objects=len(checked),
                    workplace_required=False, index_sha256=sha(index)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'audit', 'archive', 'verify', 'promote', 'integrity'])
    parser.add_argument('--project', type=Path)
    parser.add_argument('--archive', type=Path)
    parser.add_argument('--out', type=Path)
    a = parser.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000
    if a.action == 'verify':
        verify(a.archive, a.out)
        return
    r = a.project
    player = r / 'workplace/player'
    base = player / 'assets-painted-r68'
    music = r / 'workplace/probe-20261023/music-first'
    batch = music / 'hd-music-batch-r1'
    q = music / 'hd-music-integration-r1'
    assets = q / 'assets-candidate-r1'
    baseline = read(r / 'preserved/map-spell-color-audit-r2.json')
    if a.action == 'prepare':
        assert not q.exists() and not (player / 'assets-painted-r69').exists()
        assert catalog(base) == baseline['asset_hashes'] and len(baseline['asset_hashes']) == 525
        technical = read(music / 'hd-music-batch-audit-r1.json')
        assert technical['status'] == 'PASS-technical-nine-music-candidates'
        assert sha(music / 'hd-music-batch-audit-r1.json') == '8fde615ca253f248121d7c028e5d2502b74cde0eec080db8b7b1ba71f5cc7704'
        assert technical['candidate_manifest_sha256'] == sha(batch / 'candidates.json')
        q.mkdir()
        shutil.copytree(base, assets)
        manifest = read(base / 'music.json')
        assert len(manifest['cues']) == 1 and manifest['cues'][0]['id'] == 1
        assert manifest['cues'][0]['sha256'] == '4012e14dc7d03c017a532c5c56655794a03a62f395972c026273a2ec99fcbc91'
        candidates = read(batch / 'candidates.json')['cues']
        assert len(candidates) == 9 and {v['cue'] for v in candidates} == set(range(2, 11))
        for cue in candidates:
            assert cue['loop_file'] == Path(cue['loop_file']).name
            assert sha(batch / cue['loop_file']) == cue['loop_sha256']
            name = 'music-' + cue['score'][:4].lower() + '-batch-r1.ogg'
            assert not (assets / name).exists()
            shutil.copyfile(batch / cue['loop_file'], assets / name)
            manifest['cues'].append(dict(id=cue['cue'], title=cue['title'], score_sha256=cue['score_sha256'],
                bank_sha256=cue['bank_sha256'], file=name, sha256=cue['loop_sha256'], sample_rate=48000,
                channels=2, frames=cue['frames'], loop_start_frame=0, loop_end_frame=cue['frames'],
                rights='original-derived-local'))
        decoded = sum(v['frames'] * 4 for v in manifest['cues'])
        assert decoded == 88202596 and decoded < 256 * 2**20
        (assets / 'music.json').unlink()
        write(assets / 'music.json', manifest)
        record = dict(schema=1, status='same-spec-nine-cue-integration-candidate', base='assets-painted-r68',
            base_files=baseline['asset_hashes'], changed_existing_files=['music.json'], cues=10,
            decoded_int16_bytes=decoded, candidate_manifest_sha256=sha(batch / 'candidates.json'),
            technical_audit_sha256=sha(music / 'hd-music-batch-audit-r1.json'),
            authorization='Persistent user instruction to complete remaining work under the same specification without asking again; selected B palette.',
            human_listening='Nine individual new human listening approvals not claimed.',
            rights='original-derived-local; no public or Git audio distribution')
        write(assets / 'music-hd-integration.json', record)
        assert len(catalog(assets)) == 535
        source = q / 'build/src'
        for name, h in baseline['source_inputs'].items():
            assert sha(r / name) == h
            dest = source / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(r / name, dest)
        shutil.copyfile(r / 'tools/music-batch-check.go', source / 'tools/music-batch-check.go')
        write(q / 'preparation.json', dict(status='prepared-ten-hd-cues', asset_hashes=catalog(assets),
            source_inputs=baseline['source_inputs'], programs=baseline['programs'], core_files=baseline['core_files'],
            runtime_before_sha256=sha(player / 'runtime.json'), checker_source_sha256=sha(r / 'tools/music-batch-check.go')))
        print('Prepared 535 assets; 524 unchanged; 193 application sources unchanged.')
        return
    prep = read(q / 'preparation.json')
    if a.action == 'audit':
        assert catalog(base) == baseline['asset_hashes']
        assert catalog(assets) == prep['asset_hashes']
        for name, h in baseline['asset_hashes'].items():
            if name != 'music.json':
                assert sha(assets / name) == h
        for name, h in prep['source_inputs'].items():
            assert sha(r / name) == h
        for name, h in prep['core_files'].items():
            assert sha(player / 'runtime-render-r1/src' / name) == h
        for name, h in prep['programs'].items():
            assert sha(player / name) == h
        assert sha(player / 'runtime.json') == prep['runtime_before_sha256']
        built = {}
        for line in (q / 'build/inputs.sha256').read_text().splitlines():
            h, name = line.split('  ', 1)
            assert sha(q / 'build/src' / name) == h
            built[str(Path(name))] = h
        assert set(built) == set(prep['source_inputs']) | {'tools/music-batch-check.go'}
        for name, h in prep['source_inputs'].items():
            if name != 'go.mod':
                assert built[name] == h
        assert built['tools/music-batch-check.go'] == prep['checker_source_sha256']
        assert 'go1.24.13' in (q / 'build/go-version.txt').read_text()
        log = (q / 'build/tests.log').read_text()
        assert 'PASS' in log and 'FAIL' not in log and 'SKIP' not in log
        assert not (q / 'build/vet.log').read_text().strip()
        result = compare_pcm(q / 'run-r1', assets)
        result.update(status='passed-current-ten-hd-music', source_count=193, assets=535,
            preserved_assets=524, source_inputs=prep['source_inputs'], programs=prep['programs'],
            core_files=prep['core_files'], asset_hashes=prep['asset_hashes'],
            checker_sha256=sha(q / 'build/checker'), audit_tool_sha256=sha(Path(__file__)),
            audio_image=os.environ['EIGHTSWORD_AUDIO_IMAGE'],
            ffmpeg_version=subprocess.check_output(['ffmpeg', '-version'], text=True).splitlines()[0],
            limits=['Normal music-appreciation menu; not all gameplay music triggers.',
                    'No new human listening, GUI, real audio device or save/load claim.',
                    'Prior nine-cue MIDI/source audit retained; MFIG remains unmapped.'])
        write(a.out, result)
        print('Passed ten Ogg/actual PCM comparisons and 14 normal-input checkpoints.')
        return
    if a.action == 'archive':
        audit = read(q / 'audit-r1.json')
        assert audit['status'] == 'passed-current-ten-hd-music'
        storage = a.archive / 'hd-music-r1'
        index = a.archive / 'hd-music-r1.json'
        assert not storage.exists() and not index.exists()
        storage.mkdir()
        selected = set(f for folder in [q, batch, player / 'runtime-render-r1/src']
                       for f in folder.rglob('*') if f.is_file())
        selected.update(r / n for n in prep['source_inputs'])
        selected.update(player / n for n in prep['programs'])
        selected.update([player / 'runtime.json', music / 'hd-music-batch-audit-r1.json',
            music / 'hd-music-runtime-audit-r1.json', r / 'tools/finalize-hd-music.py',
            r / 'tools/music-batch-check.go', r / 'docs/spec/008-music-events-and-playback.md'])
        files, objects = [], {}
        for f in sorted(selected):
            assert f.stat().st_uid == 1000 and not f.is_symlink()
            raw = f.read_bytes()
            h = hashlib.sha256(raw).hexdigest()
            if h not in objects:
                blob = gzip.compress(raw, compresslevel=6, mtime=0)
                name = h + '.gzip'
                (storage / name).write_bytes(blob)
                objects[h] = dict(file=name, stored_sha256=hashlib.sha256(blob).hexdigest(), stored_bytes=len(blob))
            files.append(dict(path=str(f.relative_to(r)), sha256=h, bytes=len(raw), mode=f.stat().st_mode & 0o777))
        write(index, dict(schema=1, files=files, objects=objects, audit_sha256=sha(q / 'audit-r1.json'),
            dependencies={'preserved/catalog.json.gz': sha(r / 'preserved/catalog.json.gz')},
            note='Original game and module objects use the existing permanent catalog. Current Git documents supersede historical READY snapshots.'))
        write(a.out, dict(status='preserved-ten-hd-music', files=len(files), objects=len(objects),
                          stored_bytes=sum(v['stored_bytes'] for v in objects.values())))
        return
    audit = read(a.archive / 'hd-music-audit-r1.json')
    verified = read(a.archive / 'hd-music-verification-r1.json')
    assert verified['workplace_required'] is False
    assert verified['index_sha256'] == sha(a.archive / 'hd-music-r1.json')
    assert read(a.archive / 'hd-music-r1.json')['audit_sha256'] == sha(a.archive / 'hd-music-audit-r1.json')
    if a.action == 'promote':
        assert audit['status'] == 'passed-current-ten-hd-music'
        assert sha(player / 'runtime.json') == prep['runtime_before_sha256']
        assert not (player / 'assets-painted-r69').exists()
        assert catalog(assets) == audit['asset_hashes']
        for name, h in audit['programs'].items():
            assert sha(player / name) == h
        shutil.copytree(assets, player / 'assets-painted-r69')
        assert catalog(player / 'assets-painted-r69') == audit['asset_hashes']
        runtime = read(player / 'runtime.json')
        runtime.update(assets='assets-painted-r69', hd_music_cues=10,
                       music_spec='docs/spec/008-music-events-and-playback.md')
        temp = player / '.hd-music-runtime.tmp'
        write(temp, runtime)
        os.replace(temp, player / 'runtime.json')
        write(a.out, dict(status='promoted-ten-hd-music', assets='assets-painted-r69', cues=10,
                          files=535, programs_unchanged=audit['programs'], audit_sha256=sha(a.archive / 'hd-music-audit-r1.json')))
        return
    assert catalog(player / 'assets-painted-r69') == audit['asset_hashes']
    assert catalog(base) == baseline['asset_hashes']
    for name, h in audit['programs'].items():
        assert sha(player / name) == h
    for name, h in audit['source_inputs'].items():
        assert sha(r / name) == h
    for name, h in audit['core_files'].items():
        assert sha(player / 'runtime-render-r1/src' / name) == h
    art = read(r / 'artwork/manifest.json')
    assert len(art['files']) == 1040
    for item in art['files']:
        assert sha(r / 'artwork' / item['path']) == item['sha256']
    assert read(player / 'runtime.json')['assets'] == 'assets-painted-r69'
    for folder in [q, player / 'assets-painted-r69', a.archive / 'hd-music-r1']:
        assert not subprocess.check_output(['find', str(folder), '-user', 'root', '-o', '-type', 'd', '-name', '*.md'])
    assert not any(f.is_file() for f in (r / 'workplace/gocache').rglob('*'))
    ast.parse(Path(__file__).read_text())
    links = 0
    for doc in list(r.glob('*.md')) + [p for d in ['docs', 'artwork', 'preserved'] for p in (r / d).rglob('*.md')]:
        for target in re.findall(r'\[[^\]]*\]\(([^\s)]+)(?:\s+"[^\"]*")?\)', doc.read_text()):
            path = urllib.parse.unquote(target.strip('<>').split('#', 1)[0])
            if not path or path.startswith('/') or re.match('[a-zA-Z][a-zA-Z0-9+.-]*:', path):
                continue
            assert (doc.parent / path).exists() or (doc.parent / path).resolve() == a.out.resolve(), (doc, target)
            links += 1
    write(a.out, dict(status='passed-ten-hd-music-integrity', assets=535, cues=10, preserved_prior_assets=524,
                      unchanged_sources=193, unchanged_programs=7, unchanged_core=923, unchanged_artwork=1040,
                      markdown_links=links, root_owned_outputs=0, workspace_cache_files=0))
    print('Passed assets, programs, core, art, ownership and documentation links.')


if __name__ == '__main__':
    main()
