#!/usr/bin/env python3
"""008候選播放核對：十曲正常輸入、完整state、實際PCM及素材隔離。"""
import argparse
import array
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess


def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ['project','run','assets','build','out']:ap.add_argument('--'+key,type=Path,required=True)
    a=ap.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid()==1000 and not a.out.exists()
    r=read(a.run/'receipt.json');assert r['status']=='PASS-candidate-only-normal-ten-music-entries'
    assert not r['production'] and r['normal_inputs'] and not r['ram_injection'] and not r['snapshot_loaded']
    assert r['sample_rate']==48000 and r['channels']==2
    assert r['native_pcm_equal_after_escape']
    baseline=a.project/'workplace/player/assets-painted-r49';imported=read(a.assets/'music-batch-import.json')
    assert not imported['production'] and not imported['approved']
    assert len(imported['base_files'])==344 and len(imported['preserved_files'])==343
    for name,digest in imported['base_files'].items():assert sha(baseline/name)==digest
    for name,digest in imported['preserved_files'].items():assert sha(a.assets/name)==digest
    assert imported['catalog_sha256']==sha(a.assets/'music.json')
    catalog=read(a.assets/'music.json');cues={v['id']:v for v in catalog['cues']};assert set(cues)==set(range(1,11))
    native=read(a.run/'control/final-receipt.json');candidate=read(a.run/'candidate/final-receipt.json')
    assert native['file_ops']==candidate['file_ops'] and native['input_events']==candidate['input_events']
    assert native['music']['events']==candidate['music']['events']
    assert sha(a.run/'control/final.state')==sha(a.run/'candidate/final.state')
    for st,count in [(native,1),(candidate,10)]:
        assert st['source_renderer'] and st['hd'] and st['owned_render_fault'] is None
        assert not st['unimplemented'] and not st['asset_error'] and not st['graphics_error']
        assert st['text']['ComposedFrames']==0 and not st['text']['MissingGlyphs']
        assert st['music']['loaded_cues']==count and not st['music']['load_error'] and not st['music']['binding_error']
    pcm=array.array('h',(a.run/'candidate/output-s16le-stereo.pcm').read_bytes())
    control=array.array('h',(a.run/'control/output-s16le-stereo.pcm').read_bytes())
    assert len(pcm)==len(control)==r['audio_frames']*2
    assert pcm[-96000:]==control[-96000:]
    measured=[];seen=set()
    for point in r['checkpoints']:
        name=point['name']
        assert sha(a.run/'control'/(name+'.png'))==sha(a.run/'candidate'/(name+'.png'))
        assert point['frame_sha256'] and point['state_sha256']
        if not name.endswith('-cue-first'):continue
        cue_id=int(name[:2]);seen.add(cue_id);cue=cues[cue_id]
        status=point['candidate_music'];assert status['mode']=='hd' and status['cue']==cue_id
        frames=cue['frames'];position=status['frame'];absolute=point['audio_frame']
        assert absolute>4800 and position>4800 and position<frames
        raw=subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(a.assets/cue['file']),'-f','f32le','-'],timeout=120)
        decoded=array.array('f',raw);assert len(decoded)==frames*2
        actual=pcm[(absolute-4800)*2:absolute*2]
        candidates=[]
        for offset in range(-3,4):
            squared=0;maximum=0
            for i,value in enumerate(actual):
                frame=(position-4800+i//2+offset)%frames
                expected=decoded[frame*2+i%2]*32767
                expected=math.floor(expected+.5) if expected>=0 else math.ceil(expected-.5)
                difference=value-expected;squared+=difference*difference;maximum=max(maximum,abs(difference))
            candidates.append((math.sqrt(squared/len(actual)),offset,maximum))
        rms,offset,maximum=min(candidates)
        assert rms<32,(cue_id,rms,offset,maximum)
        measured.append(dict(cue=cue_id,title=cue['title'],audio_frame=absolute,source_position=position,
                             compared_stereo_frames=4800,rms_int16=rms,calibration_frames=offset,max_int16_error=maximum))
    assert seen==set(range(1,11))
    full=next(v for v in r['checkpoints'] if v['name']=='06-cue-full-loop')
    first=next(v for v in r['checkpoints'] if v['name']=='06-cue-first')
    assert full['candidate_music']['loops']>first['candidate_music']['loops']
    restart=next(v for v in r['checkpoints'] if v['name']=='06-cue-restart')
    assert restart['candidate_music']['starts']==full['candidate_music']['starts']+1
    assert restart['candidate_music']['frame']<48000
    for line in (a.build/'build-inputs.sha256').read_text().splitlines():
        digest,name=line.split('  ',1);assert name.startswith('/project/')
        assert sha(a.project/name.removeprefix('/project/'))==digest
    program=(a.build/'program.sha256').read_text().split('  ',1)[0]
    assert sha(a.build/'checker')==program
    result=dict(schema=1,status='PASS-candidate-ten-cue-normal-playback',production=False,
        compared_cues=measured,checkpoints=len(r['checkpoints']),full_state_sha256=sha(a.run/'candidate/final.state'),
        audio_frames=r['audio_frames'],native_equal_after_escape_frames=48000,
        runtime_receipt_sha256=sha(a.run/'receipt.json'),candidate_import_sha256=sha(a.assets/'music-batch-import.json'),
        preserved_base_files=343,decoded_int16_bytes=imported['decoded_int16_bytes'],
        checker_sha256=program,auditor_sha256=sha(Path(__file__)),human_listening='pending',
        scope='Ordinary ten-entry menu playback, one full loop and restart; no promotion, approval, gameplay-trigger or save/load claim.')
    with a.out.open('x') as f:f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],cues=len(measured),checkpoints=result['checkpoints'])))


if __name__=='__main__':main()
