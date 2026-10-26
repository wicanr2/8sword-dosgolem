#!/usr/bin/env python3
"""014：獨立核對深藍人物修正、五頁金字混合及普通開場隔離。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from PIL import Image, ImageChops, __version__


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def blend_check(old, new, old_bg, new_bg):
    """Find a common integer alpha for both backgrounds at each changed pixel."""
    def mask(image, background):
        channels = ImageChops.difference(image, background).split()
        return ImageChops.lighter(ImageChops.lighter(channels[0], channels[1]), channels[2])
    changed = ImageChops.lighter(mask(old, old_bg), mask(new, new_bg))
    bounds = changed.getbbox()
    if bounds is None:
        return dict(text_pixels=0, ambiguous_pixels=0)
    op, np, ob, nb, mp = old.load(), new.load(), old_bg.load(), new_bg.load(), changed.load()
    foreground = (245, 207, 113)
    count = ambiguous = 0
    for y in range(bounds[1], bounds[3]):
        for x in range(bounds[0], bounds[2]):
            if not mp[x, y]:
                continue
            ov, nv, bv, cv = op[x, y], np[x, y], ob[x, y], nb[x, y]
            delta = foreground[0] - bv[0]
            assert delta > 0
            scaled = (ov[0] - bv[0]) * 255
            low = max(0, -((127 - scaled) // delta))
            high = min(255, (scaled + 127) // delta)
            matches = []
            for alpha in range(low, high + 1):
                if all((f * alpha + b * (255-alpha) + 127) // 255 == v
                       for f, b, v in zip(foreground * 2, bv + cv, ov + nv)):
                    matches.append(alpha)
            assert matches, ('gold alpha mismatch', x, y, ov, nv)
            count += 1
            ambiguous += len(matches) > 1
    return dict(text_pixels=count, ambiguous_pixels=ambiguous)


def promote(a):
    result = read(a.audit)
    assert result['status'] == 'PASS-corrected-blue-five-pages'
    player = a.player
    build = player/'source-candidate-story-blue-r4'
    previous = player/'source-candidate-prelude-r3'
    assets, target = player/'assets-story-blue-corrected-r4', player/'assets-painted-r56'
    assert not target.exists() and not a.out.exists()
    assert sha(build/'build-inputs.sha256') == result['build_inputs_sha256']
    for name, expected in result['programs'].items():
        assert sha(build/name) == expected
        assert sha(player/name) == sha(previous/name) == result['previous_programs'][name]
    assert len(list(assets.iterdir())) == 425
    for name, expected in result['asset_hashes'].items():
        assert Path(name).name == name and sha(assets/name) == expected
        assert not (assets/name).is_symlink() and (assets/name).stat().st_uid == 1000
    target.mkdir()
    for name in result['asset_hashes']:
        os.link(assets/name, target/name)
    staged = {}
    try:
        for name in result['programs']:
            temp = player/('.blue-corrected-'+name+'.tmp')
            assert not temp.exists() and (player/name).stat().st_uid == 1000
            os.link(build/name, temp)
            staged[name] = temp
        metadata = {n: (build/n).read_bytes() for n in
                    ['build-inputs.sha256', 'build-source-checks.log', 'build-go-version.txt', 'runtime.json', 'build-outputs.sha256']}
        for name, data in metadata.items():
            temp = player/('.blue-corrected-'+name+'.tmp')
            assert (player/name).stat().st_uid == 1000
            with temp.open('xb') as f:
                f.write(data)
            staged[name] = temp
        for name, temp in staged.items():
            os.replace(temp, player/name)
    finally:
        for temp in staged.values():
            if temp.exists():
                temp.unlink()
    for name, expected in result['programs'].items():
        assert sha(player/name) == expected and sha(previous/name) == result['previous_programs'][name]
    report = dict(schema=1, status='promoted-corrected-blue-r4', assets=target.name,
                  files=425, preserved_files=422, build=build.name, programs=result['programs'],
                  previous_programs=result['previous_programs'], audit_sha256=sha(a.audit), tool_sha256=sha(Path(__file__)))
    with a.out.open('x') as f:
        f.write(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(status=report['status'], assets=target.name)))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('project', 'research', 'out'):
        p.add_argument('--'+key, type=Path, required=True)
    p.add_argument('--promote', action='store_true')
    p.add_argument('--player', type=Path)
    p.add_argument('--audit', type=Path)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000 and __version__ == '11.3.0'
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    if a.promote:
        promote(a)
        return
    project, research = a.project, a.research
    player = project/'workplace/player'
    assets, base = player/'assets-story-blue-corrected-r4', player/'assets-painted-r55'
    build, previous = player/'source-candidate-story-blue-r4', player/'source-candidate-prelude-r3'
    reg = read(research/'registration-r4.json')
    assert sha(research/'registration-r4.json') == 'b13eb367050ae0667250854962ba37546d8c9e037c6cbd06974c763b7b06a568'
    assert sha(research/'importer-at-generation.py') == reg['tool_sha256']
    correction = read(research/'metadata-path-correction.json')
    assert sha(project/'tools/prepare-story-background-correction.py') == correction['current_helper_sha256']
    assert sha(project/'docs/images/story-background-corrected-r4.json') == correction['metadata_after_sha256']
    replaced = set(reg['replaced'])
    assert replaced == {'story-background.png', 'story-background.json', 'story-background-import.json'}
    assert len(list(assets.iterdir())) == len(reg['base_files_sha256']) == 425
    for name, expected in reg['base_files_sha256'].items():
        assert sha(base/name) == expected
        if name not in replaced:
            assert sha(assets/name) == expected
    generation = read(research/'correction-r4.json')
    assert sha(research/'correction-r4.json') == reg['generation_sha256']
    assert generation['tool'] == 'built-in image_gen'
    assert sha(research/generation['prompt']) == generation['prompt_sha256']
    assert generation['actual_prompt'] == (research/generation['prompt']).read_text()
    assert sha(research/generation['image']) == reg['config']['approved_sha256']
    image = Image.open(research/generation['image']).convert('RGBA').resize((1920, 1200), Image.Resampling.LANCZOS)
    assert image.tobytes() == Image.open(assets/'story-background.png').convert('RGBA').tobytes()
    assert sha(assets/'story-background.png') == reg['config']['image_sha256']
    assert read(assets/'story-background.json') == reg['config']
    def inputs(root, current):
        result = {}
        for line in (root/'build-inputs.sha256').read_text().splitlines():
            expected, name = line.split(None, 1)
            name = name.removeprefix('/project/')
            assert sha(root/'src'/name) == expected
            if current:
                assert sha(project/name) == expected
            result[name] = expected
        return result
    new, old = inputs(build, True), inputs(previous, False)
    assert len(new) == 141 and len(old) == 140
    assert {n for n, value in old.items() if new.get(n) != value} == {'internal/eightsword/story_background.go'}
    assert set(new)-set(old) == {'internal/eightsword/story_background_correction_test.go'}
    log = (research/'tests-r4.log').read_text()
    for name in ['CorrectionPairs', 'CorruptionPreservesTextAndOtherHD']:
        assert '--- PASS: TestStoryBackground'+name in log
    assert '\nPASS\n' in log and '--- SKIP:' not in log and '\nFAIL' not in log
    programs = {}
    for line in (build/'build-outputs.sha256').read_text().splitlines():
        expected, name = line.split(None, 1)
        name = Path(name).name
        assert sha(build/name) == expected
        programs[name] = expected
    prior_research = project/'workplace/probe-20261023/graphics-first/story-art-r1/heroine-correction-r2'
    old_programs = read(prior_research/'promotion-r3.json')['programs']
    assert len(programs) == len(old_programs) == 7
    for name, expected in old_programs.items():
        assert sha(previous/name) == sha(player/name) == expected
    assert sha(prior_research/'runtime-audit-r3.json') == '7f7d2d4be4cd96c76fa54c3ea4b9283064fc6758f5cc29cfd6e7dce835ae08b0'
    helpers = module(project/'tools/audit-story-prelude.py', 'prelude_helpers')
    newroot, oldroot = research/'normal-blue-r4', prior_research/'normal-new-r3'
    isolation = helpers.isolation(newroot, oldroot)
    nm, om = helpers.metadata(newroot), helpers.metadata(oldroot)
    old_bg, new_bg = Image.open(base/'story-background.png').convert('RGB'), image.convert('RGB')
    assert old_bg.getextrema()[0][1] < 245
    cache, pages, samples = {}, {}, {}
    outside = 0
    for new_frame, old_frame in zip(helpers.stream(newroot/'presentation.frames.gz'), helpers.stream(oldroot/'presentation.frames.gz'), strict=True):
        number, step, rgba, size = new_frame
        on, ost, orig, shape = old_frame
        assert (number, step, size) == (on, ost, shape)
        info, control = nm[number-1], om[number-1]
        assert info == control and info['draw'] == number and info['step'] == step
        if info['stage'] != 'story-noto':
            assert rgba == orig, ('outside story changed', number, info['stage'])
            outside += 1
            continue
        assert info['font_id'] == 'noto' and size == (1920, 1200)
        page = str(info['story_pages'])
        key = (hashlib.sha256(orig).hexdigest(), hashlib.sha256(rgba).hexdigest())
        if key not in cache:
            old_image = Image.frombytes('RGBA', size, orig).convert('RGB')
            new_image = Image.frombytes('RGBA', size, rgba).convert('RGB')
            cache[key] = blend_check(old_image, new_image, old_bg, new_bg)
        count = cache[key]
        pages[page] = pages.get(page, 0) + 1
        if page not in samples or count['text_pixels'] > samples[page]['text_pixels']:
            samples[page] = dict(draw=number, step=step, **count, rgba=rgba)
    assert number == len(nm) == len(om) == 548 and set(pages) == set('12345')
    for page, sample in samples.items():
        assert sample['text_pixels'] > 0
        target = research/f'story-{page}-corrected-actual.png'
        rgba = sample.pop('rgba')
        if target.exists():
            assert Image.open(target).convert('RGBA').tobytes() == rgba
        else:
            Image.frombytes('RGBA', (1920, 1200), rgba).save(target)
        sample.update(image=target.name, image_sha256=sha(target))
    final = read(newroot/'gui-final.json')
    assert final['source_renderer'] and final['source_frames'] > 0 and final['owned_render_fault'] is None
    assert final['graphics']['CompositedFrames'] == 0
    result = dict(schema=1, spec='014', status='PASS-corrected-blue-five-pages', files=425, preserved_files=422,
                  programs=programs, previous_programs=old_programs, frames=number, story_frames=pages,
                  outside_equal_frames=outside, unique_gold_checks=len(cache), isolation=isolation, samples=samples,
                  build_inputs=141, build_inputs_sha256=sha(build/'build-inputs.sha256'), tests_sha256=sha(research/'tests-r4.log'),
                  registration_sha256=sha(research/'registration-r4.json'), source_frames=final['source_frames'],
                  asset_hashes={f.name:sha(f) for f in sorted(assets.iterdir())}, tool_sha256=sha(Path(__file__)),
                  limits=['Common admissible integer alpha, not unique original alpha; quantization ambiguities reported.',
                          'Normal headless opening; immutable prior normal control reused. No new GUI/save or full-game claim.'])
    with a.out.open('x') as f:
        f.write(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['status','frames','story_frames','outside_equal_frames','unique_gold_checks']}))


if __name__ == '__main__':
    main()
