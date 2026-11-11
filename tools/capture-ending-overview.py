#!/usr/bin/env python3
"""從既有完整結局測試產生 README 同狀態原版／HD 擷取器。限 Docker。"""
import argparse
import gzip
import hashlib
import importlib.util
import io
import json
import os
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True
BATCH = 'ending-readme-r1'
REL = 'workplace/probe-20261023/graphics-first/ending-hd-r1/readme-overview-r1'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p, value):
    assert p.parent.stat().st_uid == 1000
    with p.open('x') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write('\n')


def helper(r):
    spec = importlib.util.spec_from_file_location('army_ui', r / 'tools/prepare-owned-army-ui.py')
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)
    return h


def finish(a):
    if a.action in ['verify', 'restore']:
        index = json.loads((a.archive / (BATCH + '.json')).read_text())
        if a.action == 'restore':
            assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
            a.out.mkdir()
        for f in index['files']:
            ob = index['objects'][f['sha256']]
            p = a.archive / BATCH / ob['file']
            assert sha(p) == ob['stored_sha256']
            raw = gzip.decompress(p.read_bytes())
            assert len(raw) == f['bytes'] and hashlib.sha256(raw).hexdigest() == f['sha256']
            if a.action == 'restore':
                relative = Path(f['path']).relative_to(REL)
                assert '..' not in relative.parts
                target = a.out / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
                target.chmod(f['mode'])
        if a.action == 'restore':
            return
        write(a.out, dict(status='passed-ending-readme-detached', files=len(index['files']), objects=len(index['objects'])))
        return
    r = a.project
    q = a.work or r / REL
    if a.action == 'archive':
        folder = a.archive / BATCH
        folder.mkdir()
        files, objects = [], {}
        for p in sorted(q.rglob('*')):
            if not p.is_file():
                continue
            assert not p.is_symlink() and p.stat().st_uid == 1000
            raw, digest = p.read_bytes(), sha(p)
            if digest not in objects:
                target = folder / (digest + '.gz')
                target.write_bytes(gzip.compress(raw, 6, mtime=0))
                objects[digest] = dict(file=target.name, stored_sha256=sha(target))
            files.append(dict(path=str(Path(REL) / p.relative_to(q)), sha256=digest, bytes=len(raw), mode=p.stat().st_mode & 0o777))
        write(a.out, dict(files=files, objects=objects, rights='Full captures and original-derived data local only; README research thumbnails only; no Release'))
        return
    from PIL import Image, ImageDraw, ImageFont
    h = helper(r)
    overview = json.loads((q / 'captures/overview.json').read_text())
    assert overview['status'] == 'passed-ending-overview'
    assert overview['same_state'] and overview['full_guest_and_native_pcm_equal'] and overview['exit_code'] == 0
    assert len(overview['pairs']) == 9
    counts = {k: len(v) for k, v in h.dependencies(r).items()}
    assert list(counts.values()) == [197, 7, 923, 535]
    sources = []
    for row in sorted(overview['pairs'], key=lambda v: v['stage']):
        stage = row['stage'][:4]
        original = q / 'captures/native' / (stage + '-original.png')
        reference = q / 'captures/hd' / (stage + '-original.png')
        assert original.read_bytes() == reference.read_bytes()
        im = Image.open(original)
        assert im.size == (640, 200) and hashlib.sha256(im.convert('RGB').tobytes()).hexdigest() == row['original_rgb_sha256']
        hd = {}
        for font in ['noto', 'lishu', 'caoshu']:
            p = q / 'captures/hd' / (stage + '-' + font + '.png')
            assert Image.open(p).size == (1920, 1200)
            hd[font] = dict(path=str(p.relative_to(r)), sha256=sha(p))
        sources.append(dict(**row, original=dict(path=str(original.relative_to(r)), sha256=sha(original)), hd=hd))
    if a.action == 'audit':
        assert '--- PASS: TestEndingReadmeOverview' in (q / 'overview.log').read_text()
        write(a.out, dict(status='passed-ending-readme-audit', baseline=counts, overview=overview, sources=sources, generated_harness_sha256=sha(q / 'source/internal/eightsword/ending_overview_test.go'), capture_tool_sha256=sha(Path(__file__)), software='Go1.24.13 / dosgolem fixed923 / Pillow11.3.0', gui_window=False, rust_ending=False))
        return
    catalog = json.loads(gzip.decompress((r / 'preserved/catalog.json.gz').read_bytes()))
    assert a.out.parent.stat().st_uid == 1000
    raw = gzip.decompress((r / 'preserved' / catalog['objects'][h.FONT_SHA['noto']]['path']).read_bytes())
    font = ImageFont.truetype(io.BytesIO(raw), 34, index=3)
    # Only resize and arrange authentic screenshots; preserve every full frame.
    selected = [('END1.AY', '最終對峙'), ('END5.AY', '人物與結局文字'), ('END7.AY', '男女主角與結局場景')]
    canvas = Image.new('RGB', (1920, 3 * 670), (14, 26, 42))
    draw = ImageDraw.Draw(canvas)
    selected_sources = []
    for i, (stage, title) in enumerate(selected):
        row = next(v for v in sources if v['stage'] == stage)
        y = i * 670
        draw.text((16, y + 10), title + '｜原版', font=font, fill=(235, 215, 170))
        draw.text((976, y + 10), 'HD｜Noto Black 900', font=font, fill=(235, 215, 170))
        left = Image.open(r / row['original']['path']).convert('RGB').resize((960, 600), Image.Resampling.NEAREST)
        right = Image.open(r / row['hd']['noto']['path']).convert('RGB').resize((960, 600), Image.Resampling.LANCZOS)
        canvas.paste(left, (0, y + 60))
        canvas.paste(right, (960, y + 60))
        published = {}
        for mode in ['original', 'hd']:
            p = a.out.with_name('ending-' + stage[:4].lower() + '-' + mode + '-r1.png')
            assert not p.exists()
            src = r / row['original']['path'] if mode == 'original' else r / row['hd']['noto']['path']
            image = Image.open(src)
            if mode == 'original':
                image = image.resize((640, 400), Image.Resampling.NEAREST)
            image.save(p)
            published[mode] = dict(path=str(p.relative_to(r)), sha256=sha(p))
        row['published'] = published
        selected_sources.append(row)
    assert not a.out.exists()
    canvas.save(a.out)
    write(a.out.with_suffix('.json'), dict(image_sha256=sha(a.out), sources=selected_sources, all_pairs='../../preserved/ending-readme-audit-r1.json', scope='Independent original HD=false Oracle RGB vs current HD Engine.Frame; same guest state and steps; controlled ending branch; no natural campaign or Rust ending claim', original_logical=[640, 200], original_display_aspect=[640, 400], hd=[1920, 1200], actual_window=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action', choices=['prepare', 'audit', 'images', 'archive', 'verify', 'restore'], nargs='?', default='prepare')
    ap.add_argument('--project', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--work', type=Path)
    ap.add_argument('--archive', type=Path)
    a = ap.parse_args()
    assert Path('/.dockerenv').exists() and os.getuid() == 1000
    if a.action != 'prepare':
        finish(a)
        return
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    r, q = a.project, a.out
    q.mkdir()
    (q / 'captures').mkdir()
    source = q / 'source'
    (source / 'internal').mkdir(parents=True)
    for name in ['eightsword', 'ownedworld']:
        shutil.copytree(r / 'internal' / name, source / 'internal' / name)
    for name in ['go.mod', 'go.sum']:
        shutil.copyfile(r / name, source / name)
    mod = source / 'go.mod'
    mod.write_text(mod.read_text() + '\nrequire github.com/wicanr2/dosgolem v0.0.0\nreplace github.com/wicanr2/dosgolem => /core\n')
    original = r / 'internal/eightsword/ending_runtime_test.go'
    s = original.read_text().split('func TestEndingInputHandoffGuard')[0]
    s = s.replace('func TestEndingSourceRuntime(', 'func TestEndingReadmeOverview(')
    s = s.replace('"image/png"', '"image"\n "image/png"')
    s = s.replace('root, assets, out := endingTestPaths(t)', '''root, assets, out := endingTestPaths(t)
    targets := map[uint64]string{}
    captured := map[string]bool{}
    var pairs []map[string]any
    overviewSHA := map[string]string{}
    overviewState := map[string]string{}''', 1)
    marker = '\t\tadvance := func(ms int) {'
    assert s.count(marker) == 1
    s = s.replace(marker, '''
        overview := func() {
            stage := ""
            if hd {
                if e.ending == nil || !e.ending.bound || !e.ending.scene.mode || e.ending.active != 0 { return }
                page := e.ending.scene.pages[e.ending.scene.active]
                stage = page.stage
                if len(stage) != 7 || !strings.HasPrefix(stage, "END") || captured[stage] { return }
                if stage == "END5.AY" && page.glyphs < 12 { return }
                // END9 clears between credit cards; the existing original
                // sample has 24 glyphs, so a whole-ending total is invalid.
                if stage == "END9.AY" && page.glyphs < 12 { return }
            } else {
                stage = targets[e.Oracle.Steps()]
                if stage == "" { return }
            }
            w, h, rgb := e.Oracle.ScreenRGB()
            if w != 640 || h != 200 { t.Fatal("ending original geometry") }
            im := image.NewRGBA(image.Rect(0, 0, w, h))
            for i := 0; i < w*h; i++ { copy(im.Pix[i*4:i*4+3], rgb[i*3:i*3+3]); im.Pix[i*4+3] = 255 }
            rawName := strings.TrimSuffix(stage, ".AY") + "-original.png"
            f, er := os.Create(filepath.Join(dir, rawName)); must(er); must(png.Encode(f, im)); must(f.Close())
            digest := hash(rgb)
            guest := hash(observerGuestState(t, e))
            if hd {
                targets[e.Oracle.Steps()] = stage
                overviewSHA[stage] = digest
                overviewState[stage] = guest
                captured[stage] = true
                for _, font := range []string{"noto", "lishu", "caoshu"} {
                    must(e.SetFont(font)); saveFrame(strings.TrimSuffix(stage, ".AY") + "-" + font + ".png")
                }
                must(e.SetFont("noto"))
                if guest != hash(observerGuestState(t, e)) { t.Fatal("HD capture changed guest") }
                pairs = append(pairs, map[string]any{"stage": stage, "step": e.Oracle.Steps(), "cycles": e.Oracle.Cycles(), "original_rgb_sha256": digest, "guest_sha256": guest, "glyphs": e.ending.scene.pages[e.ending.scene.active].glyphs})
            } else {
                if digest != overviewSHA[stage] || guest != overviewState[stage] { t.Fatalf("original/HD state mismatch %s", stage) }
                // Page-flip labels omit writes to the already visible page.
                // The original RGB and entire guest state are authoritative.
                delete(targets, e.Oracle.Steps())
            }
        }
''' + marker)
    s = s.replace('\t\t\t\ttick++', '\t\t\t\toverview()\n\t\t\t\ttick++')
    start = s.index('\tnative := run("native", false, false)')
    s = s[:start] + '''
    hd := run("hd", true, false)
    native := run("native", false, false)
    if len(captured) != 9 || len(targets) != 0 { t.Fatalf("nine ending pairs missing: %v / %v", captured, targets) }
    if !bytes.Equal(native.state, hd.state) || native.steps != hd.steps || native.pcm != hd.pcm { t.Fatal("full original/HD ending state or PCM differs") }
    endingTestWrite(t, filepath.Join(out, "overview.json"), map[string]any{"status": "passed-ending-overview", "pairs": pairs, "original": "dosgolem Oracle.ScreenRGB, HD=false independent execution", "hd": "current Engine.Frame, approved assets and three fonts", "same_state": true, "full_guest_and_native_pcm_equal": true, "exit_code": 0, "scenario": "normal boot/new game/F1/F2/F7; explicit DS:56E2=1 at original 0110:020E; no natural campaign claim", "clock": "12:00:00.00, 3000 DOSBox cycles", "original_steps": native.steps, "native_pcm_sha256": native.pcm})
}
// Existing completion tests refer to this helper; the focused run selects only
// TestEndingReadmeOverview and does not invoke the completion suite.
func TestEndingSourceRuntime(t *testing.T) { TestEndingReadmeOverview(t) }
'''
    harness = source / 'internal/eightsword/ending_overview_test.go'
    harness.write_text(s)
    # Avoid compiling the same copied helpers twice.
    (source / 'internal/eightsword/ending_runtime_test.go').unlink()
    manifest = {
        str(p.relative_to(r)): hashlib.sha256(p.read_bytes()).hexdigest()
        for package in ['eightsword', 'ownedworld']
        for p in (r / 'internal' / package).rglob('*.go')
    }
    (q / 'inputs.json').write_text(json.dumps({
        'source': manifest,
        'runtime_test_sha256': hashlib.sha256(original.read_bytes()).hexdigest(),
        'generated_harness_sha256': hashlib.sha256(harness.read_bytes()).hexdigest(),
        'formal_go_unchanged': True,
    }, indent=2) + '\n')


if __name__ == '__main__':
    main()
