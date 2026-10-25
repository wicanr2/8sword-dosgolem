#!/usr/bin/env python3
"""047 DRAFT：核對即時場景原型的代表幀、客體隔離與正常視窗存讀。"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def records(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def compare(a, b):
    with Image.open(a) as first, Image.open(b) as second:
        first, second = first.convert('RGBA'), second.convert('RGBA')
        assert first.size == second.size == (1920, 1200)
        return sum(x != y for x, y in zip(first.getdata(), second.getdata())), ImageChops.difference(first, second).convert('RGB').getbbox()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    args = parser.parse_args()
    root = args.project
    battle = root / 'workplace/probe-20261023/graphics-first/battle-r1'
    menus = battle / 'owned-menus-r7'
    run = battle / 'owned-battle-r4'
    control = battle / 'palace-normal-hd-r1'
    gui = root / 'workplace/player/gui/owned-scene-save-r2'
    report = {'status': 'PASS-scoped-live-owned-scene-prototype', 'production': False,
              'spec_status': 'DRAFT', 'stable_samples': [], 'completed_commands': []}
    receipt = read(menus / 'owned-receipt.json')
    assert receipt['active_at_end'] == 0
    assert receipt['commands'].get('writes-outside-command', 0) == 0
    assert receipt['commands']['plot'] == 100272
    assert not any('reject' in key for key in receipt['commands'])
    report['menu_command_counts'] = receipt['commands']
    for name in ['01-continued-map', '03-character', '04-lishu', '05-army', '06-returned']:
        count, _ = compare(menus / (name + '-owned.png'), menus / (name + '-hd.png'))
        assert count == 0, (name, count)
        report['stable_samples'].append({'run': 'owned-menus-r7', 'name': name, 'full_pixels': 2304000, 'different_pixels': count})
    for name in ['battle-font-noto', 'battle-font-lishu', 'battle-font-caoshu']:
        count, _ = compare(run / (name + '-owned.png'), run / (name + '-hd.png'))
        assert count == 0, (name, count)
        report['stable_samples'].append({'run': 'owned-battle-r4', 'name': name, 'full_pixels': 2304000, 'different_pixels': count})
    for event in records(run / 'owned-commands.jsonl'):
        if event['command'] != 'completed-capture':
            continue
        assert event['different_pixels'] == 0
        count, _ = compare(run / (event['kind'] + '-owned.png'), run / (event['kind'] + '-legacy.png'))
        assert count == 0
        report['completed_commands'].append(event)
    assert {x['kind'] for x in report['completed_commands']} == {'army-complete', 'battle-actor-complete', 'battle-effect-complete'}
    for name in ['final.state', 'audio.pcm']:
        assert sha(run / name) == sha(control / name)
    files = lambda d: {p.name: sha(p) for p in d.iterdir() if p.is_file()}
    assert files(run / 'scratch') == files(control / 'scratch')
    final = read(run / 'final.json')
    assert final['recorded_frames'] == final['frame_pure_count'] == 595
    report['guest_isolation'] = {'frames': 595, 'pure_frame_calls': 595, 'scratch_files': 32,
                               'state_sha256': sha(run / 'final.state'), 'pcm_sha256': sha(run / 'audio.pcm')}
    # A real legacy partial actor image preceded completion; the owned scene
    # still showed the preceding completed state at that same guest step.
    first = battle / 'owned-live-r3'
    shot = next(x for x in records(first / 'commands.jsonl') if x['command'] == 'shot 04-army')
    completion = next(x for x in records(first / 'owned-commands.jsonl') if x['command'] == 'bitmap' and x['actor'] == 150)
    assert shot['step'] == 31243831 < completion['step'] == 31258792
    count, bbox = compare(first / '04-army-owned.png', first / '04-army-hd.png')
    assert count == 16103 and bbox == (75, 516, 288, 702)
    report['partial_actor_evidence'] = {'sample_step': shot['step'], 'completion_step': completion['step'],
                                        'different_pixels': count, 'difference_bbox': bbox,
                                        'limit': '同一筆來源尚未完成；完整角色返回時已另抽樣全圖同值。'}
    # Intentional repair: the old observer invalidated all eight pixels for a
    # one-pixel plot. Preserve the other pixels' HD paper rather than its strips.
    count, bbox = compare(menus / '02-f5-map-owned.png', menus / '02-f5-map-hd.png')
    assert count == 23040 and bbox == (288, 78, 1152, 1038)
    with Image.open(menus / '02-f5-map-owned.png') as a, Image.open(menus / '02-f5-map-hd.png') as b:
        columns = {x // 3 for y in range(0, 1200, 6) for x in range(0, 1920, 3) if a.getpixel((x, y)) != b.getpixel((x, y))}
    assert columns == {96, 97, 98, 99, 380, 381, 382, 383}
    report['intentional_f5_repair'] = {'different_hd_pixels': count, 'different_native_pixels': 1280,
                                      'native_columns': sorted(columns), 'native_rows': [13, 172],
                                      'reason': '單點繪圖只改指定像素，保留相鄰像素的HD材質；移除舊觀察器整byte失效產生的兩條原版色帶。'}
    for phase in ['save', 'reload']:
        current = read(gui / phase / 'gui-final.json')
        native = read(gui / phase / 'owned-receipt.json')
        assert current['closed'] and all(not value for key, value in current.items() if key.endswith('_error'))
        assert native['active_at_end'] == 0
        assert native['commands'].get('writes-outside-command', 0) == 0
        assert read(gui / phase / 'continuous-audit.json')['frames'] == current['recorded_frames']
    assert read(gui / 'save-cycle-audit.json')['status'] == 'passed-scoped-normal-gui-save-exit-reload'
    report['gui'] = {'root': str(gui.relative_to(root)), 'save_draws': read(gui / 'save/gui-final.json')['recorded_frames'],
                     'reload_draws': read(gui / 'reload/gui-final.json')['recorded_frames'],
                     'save_sha256': sha(gui / 'scratch/gamedata.ay')}
    # Verify the immutable source that produced these receipts. Later research
    # revisions must not rewrite this historical gate as their own validation.
    verified_source = battle / 'owned-live-build-r8/src/internal/eightsword/research_owned_scene.go'
    source = verified_source.read_text()
    pure = source[source.index('func renderOwnedScene('):source.index('func (e *Engine) ResearchOwnedScene(')]
    for forbidden in ['Oracle', '.Screen(', '.ScreenRGB(', 'PlanarBytePixels', '.Before', '.owners']:
        assert forbidden not in pure, forbidden
    report['renderer_input_audit'] = 'pure scene function; no Oracle, VGA framebuffer, legacy frame, prior native ink, or legacy ownership input'
    report['pam_sha256'] = sha(root / 'workplace/intake-20261023/sources/game/8sword/PAM.AY')
    assert report['pam_sha256'] == '83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
    assert read(battle / 'owned-observer-audit-r8.json')['status'] == 'PASS-shared-observer-same-run'
    for name in ['final.state', 'audio.pcm', 'presentation.frames.gz']:
        assert sha(battle / 'owned-menus-r8' / name) == sha(menus / name)
    assert '.ObserveVideoWrites(' not in source
    report['verified_source_sha256'] = sha(verified_source)
    report['verified_source_revision'] = 'owned-live-build-r8; later research source is not covered by these receipts'
    report['shared_observer_revision'] = 'r8 uses ObservePresentation and unsubscribes at close; same guest state, PCM and full lossless stream as r7'
    report['limits'] = ['整個面板跨命令仍逐塊重建；須補完整場景交易，不能宣稱全面消除閃爍。',
                        '尚非正式路徑；正式r48程式與素材保持。', '開場、未知繪圖操作與故障回退尚未全面接管。',
                        'r4戰場含尚未接管的逐點寫入；r7小地圖補該共用契約，未為此重跑已過的四姿勢驗收。',
                        '這些代表案例不證明全遊戲不閃爍。']
    target = battle / 'owned-live-audit-r1.json'
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
