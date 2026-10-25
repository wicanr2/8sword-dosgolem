#!/usr/bin/env python3
"""獨立解析實際MIDI與Ogg，核對008的九曲本機候選。"""
import argparse
import array
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import struct
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode_midi(path):
    raw=path.read_bytes()
    assert raw[:8]==b'MThd\x00\x00\x00\x06'
    form,tracks,tpb=struct.unpack('>HHH',raw[8:14])
    assert form==0 and tracks==1 and raw[14:18]==b'MTrk'
    assert int.from_bytes(raw[18:22],'big')+22==len(raw)
    pos,tick=22,0
    events=[]
    def vlq():
        nonlocal pos
        value=0
        for _ in range(4):
            byte=raw[pos];pos+=1;value=(value<<7)|(byte&127)
            if not byte&128:return value
        raise ValueError('MIDI延遲超界')
    while pos<len(raw):
        tick+=vlq();status=raw[pos];pos+=1
        if status==255:
            kind=raw[pos];pos+=1;n=vlq();data=list(raw[pos:pos+n]);pos+=n
            assert kind in [0x51,0x2f]
            events.append((tick,status,kind,data))
        else:
            assert 0x80<=status<0xf0
            n=1 if status&0xf0 in [0xc0,0xd0] else 2
            data=list(raw[pos:pos+n]);pos+=n
            assert len(data)==n and all(v<128 for v in data)
            events.append((tick,status,None,data))
    assert events[-1][1:]==(255,0x2f,[])
    return tpb,events


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ['project','original','batch','out']:ap.add_argument('--'+key,type=Path,required=True)
    a=ap.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid()==1000 and not a.out.exists()
    report=json.loads((a.batch/'candidates.json').read_text())
    assert report['production'] is False and len(report['cues'])==9
    assert report['preparer_sha256']==sha(a.project/'tools/prepare-music-batch.py')
    assert report['decoder_sha256']==sha(a.project/'tools/decode-adlib-music.py')
    spec=importlib.util.spec_from_file_location('source_decoder',a.project/'tools/decode-adlib-music.py')
    decoder=importlib.util.module_from_spec(spec);spec.loader.exec_module(decoder)
    checked=[]
    for cue in report['cues']:
        source=decoder.decode(a.original/cue['score'])
        assert source['sha256']==cue['score_sha256'] and source['bank_sha256']==cue['bank_sha256']
        midi=a.batch/(cue['score'][:4].lower()+'-three.mid')
        assert sha(midi)==cue['midi_sha256']
        tpb,events=decode_midi(midi)
        assert tpb==source['header']['ticks_per_beat']
        total=source['header']['total_ticks'];rhythm=source['header']['rhythm_mode']==1
        melodic=range(6 if rhythm else 9)
        expected_notes=[];expected_bends=[];expected_programs=[];expected_volumes=[];expected_tempo=[]
        for iteration in range(3):
            base=iteration*total;volume={c:127 for c in range(6,11)}
            expected_tempo.append((base,round(60000000/source['header']['basic_bpm'])))
            expected_volumes.extend((base,0xb0|c,[7,100]) for c in melodic)
            if rhythm:expected_volumes.append((base,0xb9,[7,100]))
            for e in source['events']:
                st,d,t=e['status'],e['data'],base+e['tick'];c,k=st&15,st&240
                if st==240:
                    bpm=source['header']['basic_bpm']*d[2]+((source['header']['basic_bpm']*d[3])>>7)
                    expected_tempo.append((t,round(60000000/bpm)))
                elif st==252:continue
                elif c in melodic:
                    if k in [128,144]:expected_notes.append((t,st,d))
                    elif k==224:expected_bends.append((t,st,d))
                    elif k==192:expected_programs.append((t,st,[cue['proposed_GM_programs'][d[0]]]))
                    elif k==160:expected_volumes.append((t,0xb0|c,[7,d[0]]))
                elif k==160:volume[c]=d[0]
                elif k in [128,144]:
                    # Fixed five OPL rhythm voices, explicitly revoiced to GM.
                    note={6:36,7:38,8:45,9:49,10:42}[c]
                    expected_notes.append((t,k|9,[note,round(d[1]*volume[c]/127)]))
        actual_notes=[(t,st,d) for t,st,k,d in events if st&240 in [128,144]]
        actual_bends=[(t,st,d) for t,st,k,d in events if st&240==224 and st<240]
        actual_programs=[(t,st,d) for t,st,k,d in events if st&240==192]
        actual_volumes=[(t,st,d) for t,st,k,d in events if st&240==176 and d[0]==7]
        actual_tempo=[(t,int.from_bytes(bytes(d),'big')) for t,st,k,d in events if st==255 and k==81]
        assert actual_notes==expected_notes and actual_bends==expected_bends
        assert actual_programs==expected_programs and actual_volumes==expected_volumes
        assert actual_tempo==expected_tempo
        elapsed,last,micros=Fraction(0),0,500000
        for t,st,k,d in events:
            elapsed+=Fraction((t-last)*micros,tpb*1000000);last=t
            if st==255 and k==81:micros=int.from_bytes(bytes(d),'big')
        assert last==total*3 and round(elapsed*48000/3)==cue['frames']
        loop=a.batch/cue['loop_file'];assert sha(loop)==cue['loop_sha256']
        raw=subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(loop),'-f','f32le','-'],timeout=120)
        pcm=array.array('f',raw);assert len(pcm)==cue['frames']*2
        assert all(math.isfinite(v) for v in pcm)
        peak=max(map(abs,pcm));rms=math.sqrt(sum(v*v for v in pcm)/len(pcm))
        assert peak==cue['final_peak'] and 0<peak<.95 and rms>.0001
        assert cue['upstream_pcm']['clipped_samples']==0 and not any(abs(v)>=1 for v in pcm)
        jump=[abs(pcm[c]-pcm[-2+c]) for c in [0,1]]
        assert jump==cue['wrap_sample_jump']
        assert max(jump)<.12,('循環接點需另查',cue['title'],jump)
        measurement=subprocess.run(['ffmpeg','-hide_banner','-nostdin','-i',str(loop),'-af',
                    'loudnorm=I=-22:TP=-3:LRA=11:print_format=json','-f','null','-'],
                    check=True,capture_output=True,text=True,timeout=120).stderr
        loudness=json.loads(measurement[measurement.rindex('{'):])
        assert float(loudness['input_tp'])<=-1.5
        sample=a.batch/cue['sample_file'];assert sha(sample)==cue['sample_sha256']
        assert not cue['approved'] and cue['human_listening']=='pending'
        checked.append(dict(cue=cue['cue'],title=cue['title'],seconds=cue['frames']/48000,
                            source_note_messages=cue['melodic_messages'],three_pass_note_messages=len(actual_notes),
                            pitch_bends=len(actual_bends),volume_messages=len(actual_volumes),
                            final_peak=peak,rms=rms,wrap_sample_jump=jump,loudness=loudness,
                            ogg_sha256=sha(loop),midi_sha256=sha(midi)))
    assert {v['cue'] for v in checked}==set(range(2,11))
    preview=a.batch/report['preview_file'];assert sha(preview)==report['preview_sha256']
    result=dict(schema=1,status='PASS-technical-nine-music-candidates',production=False,cues=checked,
                candidate_manifest_sha256=sha(a.batch/'candidates.json'),preview_sha256=sha(preview),
                audit_sha256=sha(Path(__file__)),human_listening='pending',
                limits=['Original notes, timings, bends and source volumes checked against actual MIDI.',
                        'GM percussion revoicing is an arrangement, not original OPL timbre/pitch parity.',
                        'Seam discontinuity is measured; listening and approval remain pending.'])
    with a.out.open('x') as f:f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],cues=len(checked),human_listening='pending')))


if __name__=='__main__':main()
