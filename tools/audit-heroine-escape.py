#!/usr/bin/env python3
"""033：核對在已呈現特寫的固定時間送普通 Esc，回到原版流程。"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True

def main():
    p=argparse.ArgumentParser()
    for n in ['control','hd','normal-hd','out']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();s=importlib.util.spec_from_file_location('audit',Path(__file__).with_name('audit-heroine.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    control=json.loads((a.control/'gui-final.json').read_text());hd=json.loads((a.hd/'gui-final.json').read_text());rows=[json.loads(line) for line in (a.hd/'intro-draw.jsonl').read_text().splitlines()]
    assert control['pam_loaded'] and hd['pam_loaded'] and hd['heroine']['stats']['Retired'] and hd['heroine']['stats']['Portraits']==1 and not hd['heroine']['stats']['Errors']
    assert control['input_events']==hd['input_events'] and any(e['Scan']==1 and e['Down'] for e in hd['input_events'])
    assert control['file_ops']==hd['file_ops'] and control['exec_log']==hd['exec_log']
    for n in ['final.state','audio.pcm']:assert m.sha(a.control/n)==m.sha(a.hd/n)
    scratch=lambda r:{f.relative_to(r/'scratch').as_posix():m.sha(f) for f in (r/'scratch').rglob('*') if f.is_file()};assert scratch(a.control)==scratch(a.hd)
    visible=returned=0
    for i,(c,h,n) in enumerate(zip(m.frames(a.control),m.frames(a.hd),m.frames(a.normal_hd),strict=True)):
        assert c[:2]==h[:2];row=rows[i]
        if row['elapsed_ms']<=9100:
            assert h==n
            visible+=row['heroine_pixels']>0
        else:
            assert row['heroine_pixels']==0 and h[2]==c[2];returned+=1
    assert visible>0 and i+1==428 and control['frame_pure_count']==hd['frame_pure_count']==428
    result={'status':'passed-normal-escape-after-visible-heroine','frames_per_group':428,'visible_frames_before_escape':visible,'original_presentation_frames_after_escape':returned,'pure_frames':856,'state_sha256':m.sha(a.hd/'final.state'),'pcm_sha256':m.sha(a.hd/'audio.pcm'),'scratch_files':len(scratch(a.hd)),'input_events':len(hd['input_events']),'method':'Ordinary Esc at elapsed 9100 virtual ms after a confirmed HD Draw; no direct entry or guest injection.'};a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
