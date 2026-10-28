#!/usr/bin/env python3
"""在隔離還原副本試跑現行程式，並核對真正存讀的2987-byte人物資料。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['restored','out','report']:p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();assert Path('/.dockerenv').is_file() and os.getuid()==1000
    assert not a.out.exists() and a.out.parent.stat().st_uid==1000 and not a.report.exists()
    a.out.mkdir(); player=a.restored/'workplace/player'; original=a.restored/'workplace/intake-20261023/sources/game/8sword'
    assets=player/'assets-painted-r64'; commands=[]
    def run(name,args):
        result=subprocess.run([str(v) for v in args],capture_output=True,text=True,timeout=60)
        (a.out/(name+'.stdout.txt')).write_text(result.stdout);(a.out/(name+'.stderr.txt')).write_text(result.stderr)
        commands.append(dict(name=name,args=[str(v) for v in args],returncode=result.returncode))
        if result.returncode!=0:raise RuntimeError(name+' failed: '+result.stderr[-1600:])
    for mode in ['native','hd']:
        run('boot-'+mode,[player/'8sword-replay','-root',original,'-assets',assets,'-out',a.out/mode,'-hd='+str(mode=='hd').lower(),'-until','4000000','-frame-every','1000000'])
    native=json.loads((a.out/'native/receipt.json').read_text());hd=json.loads((a.out/'hd/receipt.json').read_text())
    assert (a.out/'native/final.state').read_bytes()==(a.out/'hd/final.state').read_bytes()
    for key,value in hd.items():
        if key.endswith('_error'):assert not value,(key,value)
    assert hd['hd'] is True and native['hd'] is False
    assert not hd.get('owned_render_fault') and not hd.get('render_fault')
    saved=player/'gui/compat-pixels-save-r2/scratch/gamedata.ay'
    assert saved.stat().st_size==2987
    buffers={}
    for phase in ['save','reload']:
        state=player/'gui/compat-pixels-save-r2'/phase/'gui-final.state'
        run('inspect-'+phase,[player/'eightsword-inspect','-state',state,'-root',original,'-out',a.out/('inspect-'+phase),'-until','0','-save-buffer'])
        buf=a.out/('inspect-'+phase)/'save-buffer-9e000.bin'
        assert buf.read_bytes()==saved.read_bytes();buffers[phase]=sha(buf)
    result=dict(status='PASS-detached-current-restore',boot_steps=4000000,native_hd_state_sha256=sha(a.out/'hd/final.state'),
                assets=462,originals=158,saved_bytes=2987,saved_character_sha256=sha(saved),save_buffers=buffers,
                commands=commands,tool_sha256=sha(Path(__file__)),
                limits=['Existing binaries restored byte-for-byte; boot smoke and read-only save inspection, no new full GUI or gameplay parity claim.','No old workplace or external project tree mounted.'])
    a.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['commands','limits']},ensure_ascii=False))


if __name__=='__main__':main()
