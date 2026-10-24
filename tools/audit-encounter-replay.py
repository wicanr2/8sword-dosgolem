"""039：正常 GUI 輸入重播的客體隔離、完整畫面及故障回退。僅在 Docker 執行。"""
import argparse
import hashlib
import importlib.util
import json
from itertools import zip_longest
from pathlib import Path
from PIL import ImageChops


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files(path):
    return {str(p.relative_to(path)): sha(p) for p in path.rglob('*') if p.is_file()}


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ['hd', 'old', 'bad', 'assets', 'original', 'cache', 'out']:
        parser.add_argument('--'+arg, required=True, type=Path)
    a = parser.parse_args()
    assert not a.out.exists()
    roots = [a.hd, a.old, a.bad]
    states, audio, counts = [], [], []
    for root in roots:
        for prefix in ['encounter', 'final']:
            before = root / (prefix+'-before.state')
            assert sha(before) == sha(root/(prefix+'-after.state'))
        states.append(sha(root/'final-before.state'))
        audio.append(sha(root/'audio.pcm'))
        meta = read(root/'final.json')
        assert meta['normal_input_replay'] and meta['ordinary_completion_path']
        assert not meta['snapshot_loaded'] and not meta['guest_memory_injection']
        assert (meta['replayed_updates'], meta['replayed_inputs'], meta['total_update_calls']) == (895, 80, 1084)
        assert meta['steps'] == 102578869 and meta['normal_source_calls'] == 14
        counts.append(meta['recorded_frames'])
    assert len(set(states)) == len(set(audio)) == 1
    assert counts == [1088]*3
    keys = ['steps', 'input_events', 'file_ops', 'exec_log', 'strings', 'visible_scene', 'music']
    baseline = read(a.old/'final.json')
    for root in roots:
        meta = read(root/'final.json')
        assert all(meta[k] == baseline[k] for k in keys)
        assert files(root/'scratch') == files(a.old/'scratch')
        assert (root/'encounter-calls.jsonl').read_bytes() == (a.old/'encounter-calls.jsonl').read_bytes()
    assert read(a.hd/'final.json')['map_encounter_7_error'] == ''
    assert read(a.bad/'final.json')['map_encounter_7_error']
    sources = [json.loads(line) for line in (a.hd/'encounter-calls.jsonl').read_text().splitlines()]
    assert len(sources) == 14
    native_pixels = 0
    for path in sorted(a.hd.glob('encounter-first-*-call.json')):
        prefix = path.name.removesuffix('-call.json')
        call = read(path)
        raw = (a.hd/(prefix+'-source.bin')).read_bytes()
        before = (a.hd/(prefix+'-before.idx')).read_bytes()
        after = (a.hd/(prefix+'-after.idx')).read_bytes()
        h = call['height']
        assert len(raw) == 4+48*h and len(before) == len(after) == 64*h
        expected = bytearray(before)
        for y in range(h):
            for x in range(64):
                at, bit = y*8+x//8, 7-x%8
                if raw[4+5*8*h+at] >> bit & 1:
                    expected[y*64+x] = sum(((raw[4+q*8*h+at] >> bit) & 1) << q for q in range(4))
        assert bytes(expected) == after
        native_pixels += len(after)
    assert native_pixels == 10816
    model_module = load('encounter_model', 'audit-encounter-gui.py')
    model = model_module.Model(a.assets, a.original, a.cache)
    packets = sorted((a.hd/'research-encounter-draws').glob('*-first-draw.json'))
    assert packets
    results = [model.frame(p.with_suffix('')) for p in packets]
    assert {r['height'] for r in results} == set(range(5, 26, 2))
    assert {r['font_id'] for r in results if r['height'] == 25} == {'noto', 'lishu', 'caoshu'}
    wanted = {r['actual_draw']: r for r in results}
    streams = load('encounter_stream', 'audit-army-dismiss.py')
    changed = []
    for triples in zip_longest(*(streams.stream(root) for root in roots)):
        assert all(t is not None for t in triples)
        (n, step, hd), (nn, ss, old), (bn, bs, bad) = triples
        assert n == nn == bn and step == ss == bs
        assert old.tobytes() == bad.tobytes()
        diff = ImageChops.difference(hd, old).convert('RGB').getbbox()
        if diff:
            assert 408 <= diff[0] < diff[2] <= 600 and 522 <= diff[1] < diff[3] <= 672, (n, step, diff)
            changed.append(dict(frame=n, step=step, bbox=diff))
        if n in wanted:
            r = wanted.pop(n)
            assert r['step'] == step and r['rgba_sha256'] == hashlib.sha256(hd.tobytes()).hexdigest()
    assert n == 1088 and not wanted and changed
    for name in ['character-after-encounter.png', 'army-after-encounter.png', 'returned-map.png', 'saved-map.png']:
        assert len({sha(root/name) for root in roots}) == 1
    result = dict(schema=1, status='passed-normal-GUI-input-replay', frames_per_group=n,
                  changed_frames=changed, original_return_pixels=native_pixels,
                  full_frame_packets=results, state_sha256=states[0], pcm_sha256=audio[0],
                  work_files=len(files(a.old/'scratch')), source_calls=len(sources),
                  frame_purity=True, three_fonts=True, broken_group_matches_old=True,
                  actual_window=False, limitation='Recorded ordinary GUI inputs replayed with exact guest update boundaries; actual window and cold save reload require separate receipts',
                  tool_sha256=sha(Path(__file__)))
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ['status', 'frames_per_group', 'source_calls', 'work_files']}))


if __name__ == '__main__':
    main()
