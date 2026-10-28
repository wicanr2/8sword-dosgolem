#!/usr/bin/env python3
"""核對永久物件、現行程式／素材／核心及音源。可完全不掛載workplace。"""
import argparse
import importlib.util
import json
import os
from pathlib import Path


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,required=True);p.add_argument('--artwork',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid()==1000
    spec=importlib.util.spec_from_file_location('preservation',Path(__file__).with_name('preserve-project-data.py'))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    result=mod.verify(a.archive,a.artwork)
    _,catalog=mod.load(a.archive); files={r['path']:r for r in catalog['files']}
    def read(name):
        row=files[name]
        with mod.object_file(a.archive,a.artwork,catalog['objects'][row['sha256']]) as f:return f.read()
    ending='workplace/probe-20261023/graphics-first/ending-hd-r1/'
    promotion=json.loads(read(ending+'ring-promotion-r1.json'))
    audit=json.loads(read(ending+'ring-audit-r1.json'))
    for name,sha in promotion['programs'].items():assert files['workplace/player/'+name]['sha256']==sha
    assert len(promotion['programs'])==7
    asset_prefix='workplace/player/assets-painted-r64/'
    actual={k.removeprefix(asset_prefix):v['sha256'] for k,v in files.items() if k.startswith(asset_prefix)}
    assert actual==audit['asset_hashes'] and len(actual)==462
    runtime=json.loads(read('workplace/player/runtime.json'))
    assert len(runtime['files'])==923
    for name,sha in runtime['files'].items(): assert files['workplace/player/runtime-render-r1/src/'+name]['sha256']==sha
    count=0
    for line in read('workplace/player/build-inputs.sha256').decode().splitlines():
        sha,name=line.split(None,1); name=name.removeprefix('/project/')
        assert files['workplace/player/source-candidate-ring-r3/src/'+name]['sha256']==sha; count+=1
    assert count==175
    originals=json.loads(read('workplace/intake-20261023/source-manifest.json'))['files']
    originals=[r for r in originals if r['path'].startswith('game/8sword/')]
    assert len(originals)==158
    for r in originals:assert files['workplace/intake-20261023/sources/'+r['path']]['sha256']==r['sha256']
    sf=a.archive/'toolchain'; toolchain=json.loads((sf/'manifest.json').read_text())
    for r in toolchain['files']:
        f=mod.safe(sf,r['path']);assert f.stat().st_size==r['bytes'] and mod.digest(f)==r['sha256']
    font_prefix='workplace/probe-20261023/graphics-first/font-settings-r1/'
    for name in ['NotoSansCJK-Black.ttc','NotoSerifCJK-Regular.ttc','LiuJianMaoCao-Regular.ttf','TW-MOE-Li-3.00.ttf']:
        assert files[font_prefix+name]['bytes']>0
    latest='workplace/player/gui/compat-pixels-save-r2/'
    assert files[latest+'scratch/gamedata.ay']['bytes']==2987
    for phase in ['save','reload']:
        assert files[latest+phase+'/gui-final.state']['bytes']>0
        assert files[latest+phase+'/presentation.frames.gz']['bytes']>0
    music_prefix='workplace/probe-20261023/music-first/hd-music-batch-r1/'
    cues=[name for name in files if name.startswith(music_prefix) and name.endswith('-hd-loop.ogg')]
    assert len(cues)==9
    generation=json.loads(read(music_prefix+'generation-record.json'));assert generation['approved'] is False and generation['production'] is False
    result.update(programs=7,assets=462,core_files=923,build_inputs=175,original_files=158,
                  font_sources=4,soundfont_files=len(toolchain['files']),saved_character_bytes=2987,
                  pending_music_cues=9,music_approval_unchanged=True,
                  toolchain_manifest_sha256=mod.digest(sf/'manifest.json'),audit_tool_sha256=mod.digest(Path(__file__)))
    mod.write_json(a.report,result);print(json.dumps(result,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
