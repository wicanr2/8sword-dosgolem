"""041：正常軍隊頁的來源、完整畫面、客體隔離與實際 Draw。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
from itertools import zip_longest
from pathlib import Path
from PIL import ImageChops


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def files(root):
    return {str(p.relative_to(root)): sha(p) for p in root.rglob('*') if p.is_file()}


def packets(root, model, stream):
    paths = sorted((root/'research-army21-draws').glob('*-first-draw.json'))
    assert paths
    results = [model.frame(p.with_suffix('')) for p in paths]
    assert {(read(p)['background_id'],read(p)['font_id']) for p in paths} == {(b,f) for b in [47,48] for f in ['noto','lishu','caoshu']}
    source_path = root/'research-army21-sources.json'
    calls = read(source_path)['calls'] if source_path.exists() else [read(p) for p in sorted(root.glob('unit21-*-call.json'))]
    raw = (root/'unit21-01-source.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == '5168810f892b3d4723a990d7c231f1a14801568166030fd9eef661140d937f30'
    for p,r in zip(paths,results):
        meta = read(p)
        assert meta['family'] == 'MAN21.EGG' and meta['record'] == 0 and meta['height'] == 50
        assert meta['source_sha256'] == '5168810f892b3d4723a990d7c231f1a14801568166030fd9eef661140d937f30'
        assert 150 in r['actor_ids']
        prior = [c for c in calls if c['return_step'] <= meta['step']]
        assert prior
        native = p.with_name(p.name.removesuffix('.json')+'-native.idx').read_bytes()
        count = 0
        for y in range(50):
            for x in range(88):
                at,bit = y*11+x//8,7-x%8
                if raw[4+5*550+at] >> bit & 1:
                    color = sum(((raw[4+q*550+at] >> bit)&1)<<q for q in range(4))
                    assert native[(73+y)*640+24+x] == color
                    count += 1
        r['original_masked_pixels'] = count
        r['original_return_step'] = max(c['return_step'] for c in prior)
        assert meta['source_return_step'] == r['original_return_step']
    wanted = {r['actual_draw']:r for r in results}
    for ordinal,step,frame in stream(root):
        if ordinal in wanted:
            r = wanted.pop(ordinal)
            assert r['step'] == step and r['rgba_sha256'] == hashlib.sha256(frame.tobytes()).hexdigest()
    assert not wanted
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ['assets','original','cache','out']:
        ap.add_argument('--'+name,type=Path,required=True)
    for name in ['hd','old','bad','gui']:
        ap.add_argument('--'+name,type=Path)
    a = ap.parse_args()
    assert not a.out.exists()
    model = module('army_model','audit-encounter-gui.py').Model(a.assets,a.original,a.cache)
    helper = module('army_stream','audit-army-dismiss.py')
    if a.gui:
        phases = {}
        for phase in ['save','reload']:
            root = a.gui/phase
            phases[phase] = packets(root,model,helper.stream)
            source = read(root/'research-army21-sources.json')
            assert not source['error'] and len(source['calls']) >= 3
            for call in source['calls']:
                assert call['source_sha256'] == '5168810f892b3d4723a990d7c231f1a14801568166030fd9eef661140d937f30'
                assert (call['x_byte'],call['y'],call['width_bytes'],call['height']) == (3,73,11,50)
                raw = (root/(f"unit21-{call['serial']:02d}-source.bin")).read_bytes()
                before = (root/(f"unit21-{call['serial']:02d}-before.idx")).read_bytes()
                after = (root/(f"unit21-{call['serial']:02d}-after.idx")).read_bytes()
                verify_source(raw,before,after)
        result = dict(status='passed-independent-actual-F2-F3-Draws',phases=phases,actual_stream_link=True,three_fonts=True)
    else:
        assert a.hd and a.old and a.bad
        roots = [a.hd,a.old,a.bad]
        metas = [read(r/'final.json') for r in roots]
        assert all(m['frame_pure_count'] == m['recorded_frames'] == 406 for m in metas)
        assert all(m['exited'] and m['exit_code'] == 0 and not m['snapshot_loaded'] and not m['guest_injection'] for m in metas)
        assert len({sha(r/'final.state') for r in roots}) == len({sha(r/'audio.pcm') for r in roots}) == 1
        for r,m in zip(roots,metas):
            assert files(r/'scratch') == files(a.old/'scratch')
            for key in ['steps','input_events','file_ops','exec_log','strings']:
                assert m[key] == metas[1][key],key
        assert not metas[0]['army_man21_error'] and metas[2]['army_man21_error']
        calls = sorted(a.hd.glob('unit21-*-call.json'))
        assert len(calls) == 3
        for call in calls:
            prefix = call.name.removesuffix('-call.json')
            raw = (a.hd/(prefix+'-source.bin')).read_bytes()
            verify_source(raw,(a.hd/(prefix+'-before.idx')).read_bytes(),(a.hd/(prefix+'-after.idx')).read_bytes())
            assert all((root/call.name).read_bytes() == call.read_bytes() for root in roots)
        results = packets(a.hd,model,helper.stream)
        changed = []
        for records in zip_longest(*(helper.stream(r) for r in roots)):
            assert all(r is not None for r in records)
            (n,step,hd),(nn,ss,old),(bn,bs,bad) = records
            assert n == nn == bn and step == ss == bs and old.tobytes() == bad.tobytes()
            bbox = ImageChops.difference(hd,old).convert('RGB').getbbox()
            if bbox:
                assert 72 <= bbox[0] < bbox[2] <= 336 and 438 <= bbox[1] < bbox[3] <= 738,(n,bbox)
                changed.append(dict(frame=n,step=step,bbox=bbox))
        assert n == 406 and changed
        for name in ['05-character-hd.png','08-back-map-hd.png','09-saved-hd.png']:
            assert len({sha(r/name) for r in roots}) == 1
        result = dict(status='passed-normal-F2-F3-isolation',frames_per_group=n,pure_frames=1218,
                      changed_frames=changed,packets=results,source_calls=len(calls),source_pixels=13200,
                      state_sha256=sha(a.hd/'final.state'),pcm_sha256=sha(a.hd/'audio.pcm'),
                      work_files=len(files(a.hd/'scratch')),broken_group_matches_old=True)
    result['tool_sha256'] = sha(Path(__file__))
    result['model_sha256'] = sha(Path(__file__).with_name('audit-encounter-gui.py'))
    result['scope'] = '041 fixed source and sampled normal F2/F3 paths; no gameplay/RNG or whole-game parity claim'
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['packets','phases','changed_frames']}))


def verify_source(raw,before,after):
    assert hashlib.sha256(raw).hexdigest() == '5168810f892b3d4723a990d7c231f1a14801568166030fd9eef661140d937f30'
    assert len(before) == len(after) == 4400
    expected = bytearray(before)
    for y in range(50):
        for x in range(88):
            at,bit = y*11+x//8,7-x%8
            if raw[4+5*550+at] >> bit & 1:
                expected[y*88+x] = sum(((raw[4+q*550+at] >> bit)&1)<<q for q in range(4))
    assert bytes(expected) == after


if __name__ == '__main__':
    main()
