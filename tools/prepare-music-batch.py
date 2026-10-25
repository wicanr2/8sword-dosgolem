#!/usr/bin/env python3
"""008研究候選：保留原曲事件，批次製作撥弦／長笛配器及本機試聽頁。"""
import argparse
import array
from fractions import Fraction
import hashlib
import html
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import wave


SF = Path('/usr/share/sounds/sf2/FluidR3_GM.sf2')
SF_SHA = '74594e8f4250680adf590507a306655a299935343583256f3b722c48a1bc1cb0'
DRUMS = {6: 36, 7: 38, 8: 45, 9: 49, 10: 42}
# Proposed GM programs, indexed by verified SND instrument index. These are
# deliberate arrangements, not inferred original patches or approved runtime art.
PALETTES = {
    'MWLK.AY': ([48, 107, 107, 73, 73, 24, 0], '低弦襯底、撥弦行進、長笛主句', 4),
    'MWAR.AY': ([107, 73, 111], '撥弦重複音、長笛雙線、原節奏鼓點', 3),
    'MONE.AY': ([24, 107, 43, 73], '柔和撥弦主旋律、箏類和聲與低弦', 0),
    'MTWO.AY': ([107, 42, 73, 24, 48], '箏類與長笛交疊、低弦及清楚琶音', 0),
    'MTHR.AY': ([73, 24, 77, 107], '長笛與氣息管音、稀疏撥弦和聲', 0),
    'MFOU.AY': ([107, 48, 10, 73, 24, 14, 13], '低撥弦、細鐘音、長笛及柔弦', 3),
    'MFIV.AY': ([92, 77, 48, 43, 107], '低弦與暗色長音、氣息管音保留懸疑', 6),
    'MSIX.AY': ([10, 42, 115, 112, 107, 73, 0], '鐘音、木質節拍、箏類和聲與高長笛', 0),
    'MEND.AY': ([73, 48, 24, 107], '長笛敘句轉柔弦、撥弦維持原曲收束', 0),
}
GM = {0:'Acoustic Grand Piano',10:'Music Box',13:'Xylophone',14:'Tubular Bells',
      24:'Nylon Guitar',42:'Cello',43:'Contrabass',48:'String Ensemble',73:'Flute',
      77:'Shakuhachi',92:'Bowed Pad',107:'Koto',111:'Shanai',112:'Tinkle Bell',115:'Woodblock'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vlq(value):
    assert 0 <= value < 2**28
    result = [value & 127]
    while value >> 7:
        value >>= 7
        result.insert(0, (value & 127) | 128)
    return bytes(result)


def midi(source, patches):
    header, events = source['header'], source['events']
    rhythm = header['rhythm_mode'] == 1
    assert header['rhythm_mode'] in [0, 1]
    melodic = range(6 if rhythm else 9)
    total, tpb = header['total_ticks'], header['ticks_per_beat']
    ticks, track = 0, bytearray()
    elapsed, exact, last, bpm, micros = Fraction(0), Fraction(0), 0, header['basic_bpm'], round(60000000/header['basic_bpm'])
    notes, drums, bends, volumes = [], [], [], []
    for event in events:
        tick = event['tick']
        elapsed += Fraction((tick-last)*micros, tpb*1000000)
        exact += Fraction((tick-last)*60, tpb*bpm)
        last = tick
        if event['status'] == 0xf0:
            d = event['data']
            bpm = header['basic_bpm']*d[2]+((header['basic_bpm']*d[3]) >> 7)
            assert bpm > 0
            micros = round(60000000/bpm)

    def put(tick, data):
        nonlocal ticks
        assert tick >= ticks
        track.extend(vlq(tick-ticks)+bytes(data))
        ticks = tick

    def tempo(tick, value):
        put(tick, b'\xff\x51\x03'+round(60000000/value).to_bytes(3,'big'))

    for iteration in range(3):
        base = iteration*total
        tempo(base, header['basic_bpm'])
        for c in melodic:
            for control, value in [(101,0),(100,0),(6,header['bend_semitones']),(38,0),
                                   (101,127),(100,127),(7,100),
                                   (10,[48,58,70,80,58,70,40,88,64][c]),(91,0),(93,0)]:
                put(base,[0xb0|c,control,value])
        if rhythm:
            for control,value in [(7,100),(10,64),(91,0),(93,0)]:
                put(base,[0xb9,control,value])
        drum_volume = {c:127 for c in DRUMS}
        for event in events:
            st, d, tick = event['status'], event['data'], base+event['tick']
            kind, c = st & 0xf0, st & 15
            if st == 0xfc:
                for channel in [*melodic, *([9] if rhythm else [])]:
                    put(tick,[0xb0|channel,123,0])
            elif st == 0xf0:
                value=header['basic_bpm']*d[2]+((header['basic_bpm']*d[3]) >> 7)
                tempo(tick,value)
            elif c in melodic:
                if kind == 0xc0:
                    assert d[0] < len(patches)
                    put(tick,[st,patches[d[0]]])
                elif kind == 0xa0:
                    put(tick,[0xb0|c,7,d[0]])
                    if not iteration:volumes.append([event['tick'],c,d[0]])
                else:
                    assert kind in [0x80,0x90,0xb0,0xd0,0xe0]
                    put(tick,[st,*d])
                    if not iteration:
                        if kind in [0x80,0x90]:notes.append([event['tick'],st,d])
                        if kind == 0xe0:bends.append([event['tick'],st,d])
            else:
                assert rhythm and c in DRUMS
                if kind == 0xa0:
                    drum_volume[c]=d[0]
                elif kind in [0x80,0x90]:
                    velocity=round(d[1]*drum_volume[c]/127)
                    put(tick,[kind|9,DRUMS[c],velocity])
                    if not iteration:drums.append([event['tick'],st,d,DRUMS[c],velocity])
                else:
                    assert kind in [0xc0,0xe0]
    put(total*3,b'\xff\x2f\x00')
    expected = [[e['tick'],e['status'],e['data']] for e in events
                if e['status'] & 0xf0 in [0x80,0x90] and e['status'] & 15 in melodic]
    assert notes == expected
    assert abs(float(elapsed-exact)) < .001
    data = b'MThd'+struct.pack('>IHHH',6,0,1,tpb)+b'MTrk'+struct.pack('>I',len(track))+track
    return data, dict(source_seconds=float(exact),midi_seconds=float(elapsed),
        frames=round(elapsed*48000),melodic_messages=len(notes),bend_messages=len(bends),
        volume_messages=len(volumes),percussion_messages=len(drums),
        melodic_events_sha256=hashlib.sha256(json.dumps(notes,separators=(',',':')).encode()).hexdigest(),
        percussion_voice_to_GM_note=DRUMS if rhythm else {},
        percussion_volume='source A0 converted to note velocity; GM envelope/timbre approximation',
        duration_label='hardware-spec approximation with MIDI microsecond tempo quantization')


def run(command, **kwargs):
    return subprocess.run(command,check=True,timeout=180,**kwargs)


def pcm_stats(path):
    peak=clipped=count=0
    with wave.open(str(path)) as f:
        assert (f.getframerate(),f.getnchannels(),f.getsampwidth()) == (48000,2,2)
        while raw:=f.readframes(48000):
            samples=array.array('h',raw)
            if os.sys.byteorder != 'little':samples.byteswap()
            peak=max(peak,max(map(abs,samples)))
            clipped+=sum(abs(x)>=32767 for x in samples)
            count+=len(samples)
    assert clipped == 0 and peak > 0
    return dict(samples=count,peak=peak,clipped_samples=clipped)


def render(out, entry, source, result):
    config=out/'timidity.cfg'
    midi_path=out/(entry['score'][:4].lower()+'-three.mid')
    wav=out/(midi_path.stem+'.wav')
    command=['timidity','-c',str(config),'-Ow','-s','48000','-EFreverb=0','-EFchorus=0',
             '-A','8','-o',str(wav),str(midi_path)]
    with (out/(midi_path.stem+'.log')).open('x') as f:
        run(command,stdout=f,stderr=subprocess.STDOUT)
    result['render_command']=command
    result['upstream_pcm']=pcm_stats(wav)
    frames=result['frames']
    trim=f'atrim=start_sample={frames}:end_sample={frames*2},asetpts=PTS-STARTPTS'
    measured=run(['ffmpeg','-hide_banner','-nostdin','-i',str(wav),'-af',
                  trim+',loudnorm=I=-22:TP=-3:LRA=11:print_format=json','-f','null','-'],capture_output=True,text=True).stderr
    measure=json.loads(measured[measured.rindex('{'):])
    gain=min(-22-float(measure['input_i']),-3-float(measure['input_tp']))
    loop=out/(entry['score'][:4].lower()+'-hd-loop.ogg')
    command=['ffmpeg','-v','error','-nostdin','-i',str(wav),'-af',trim+f',volume={gain:.9f}dB',
             '-map_metadata','-1','-fflags','+bitexact','-flags:a','+bitexact','-c:a','libvorbis','-q:a','6',str(loop)]
    run(command)
    result.update(gain_db=gain,loudness_before_gain=measure,encode_command=command,
                  loop_file=loop.name,loop_sha256=sha(loop),sample_rate=48000,channels=2)
    raw=run(['ffmpeg','-v','error','-nostdin','-i',str(loop),'-f','f32le','-'],capture_output=True).stdout
    pcm=array.array('f',raw)
    assert len(pcm)==frames*2 and all(math.isfinite(v) for v in pcm)
    peak=max(map(abs,pcm));rms=math.sqrt(sum(v*v for v in pcm)/len(pcm))
    assert 0 < rms and peak < .95
    jump=[abs(pcm[c]-pcm[-2+c]) for c in [0,1]]
    boundary=pcm[-960:]+pcm[:960]
    delta=max(abs(boundary[i]-boundary[i-2]) for i in range(2,len(boundary)))
    result.update(decoded_frames=len(pcm)//2,final_peak=peak,final_rms=rms,
                  final_clipped_samples=sum(abs(v)>=1 for v in pcm),wrap_sample_jump=jump,
                  boundary_window_max_delta=delta,seam_listening='pending')
    sample=out/(entry['score'][:4].lower()+'-sample-30s.ogg')
    run(['ffmpeg','-v','error','-nostdin','-stream_loop','-1','-i',str(loop),'-t','30',
         '-af','afade=t=in:d=0.03,afade=t=out:st=29:d=1','-c:a','libvorbis','-q:a','6',str(sample)])
    result.update(sample_file=sample.name,sample_sha256=sha(sample))
    return loop


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--original',type=Path,required=True)
    ap.add_argument('--research',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid()==1000
    assert not a.out.exists() and a.out.parent.stat().st_uid==1000
    assert sha(SF)==SF_SHA
    source_map=json.loads((a.research/'menu-source-map.json').read_text())
    assert len(source_map['entries'])==10
    spec=importlib.util.spec_from_file_location('adlib_decoder',Path(__file__).with_name('decode-adlib-music.py'))
    decoder=importlib.util.module_from_spec(spec);spec.loader.exec_module(decoder)
    a.out.mkdir()
    (a.out/'timidity.cfg').write_text(f'soundfont {SF}\n')
    shutil.copyfile(a.research/'soundfont-copyright.txt',a.out/'soundfont-copyright.txt')
    results=[];loops=[]
    for entry in source_map['entries']:
        if entry['menu_index']==1:continue
        source=decoder.decode(a.original/entry['score'])
        previous=json.loads((a.research/(entry['score'][:4].lower()+'-events.json')).read_text())
        assert source==previous
        patches,direction,voice=PALETTES[source['source']]
        data,info=midi(source,patches)
        path=a.out/(entry['score'][:4].lower()+'-three.mid')
        path.write_bytes(data)
        motif=[e['data'][0] for e in source['events'] if e['status']==0x90|voice and e['data'][1]][:7]
        info.update(cue=entry['menu_index'],title=entry['title'],score=source['source'],bank=source['bank'],
                    score_sha256=source['sha256'],bank_sha256=source['bank_sha256'],
                    source_events_sha256=sha(a.research/(entry['score'][:4].lower()+'-events.json')),
                    source_instruments=source['instruments'],proposed_GM_programs=patches,
                    proposed_instruments=[GM[p] for p in patches],direction=direction,
                    source_motif_voice=voice,source_motif_midi_notes=motif,midi_sha256=sha(path),
                    authenticity='原曲衍生配器候選；GM取樣音色，非古箏／竹笛實錄',
                    rights='original-derived-local',human_listening='pending',approved=False)
        loop=render(a.out,entry,source,info)
        loops.append(loop);results.append(info)
        print(json.dumps(dict(cue=info['cue'],title=info['title'],seconds=info['frames']/48000,
                             peak=info['final_peak'],status='unapproved-candidate'),ensure_ascii=False),flush=True)
    # Compact sequential preview; separate full loops remain untouched.
    excerpts=[]
    for i,loop in enumerate(loops):
        sample=a.out/f'preview-{i+1:02d}.wav'
        run(['ffmpeg','-v','error','-nostdin','-i',str(loop),'-t','12','-af',
             'afade=t=in:d=0.03,afade=t=out:st=11.5:d=0.5','-c:a','pcm_s16le',str(sample)])
        excerpts.append(sample)
    listing=a.out/'preview-list.txt'
    listing.write_text(''.join(f"file '{f.name}'\n" for f in excerpts))
    overview=a.out/'nine-cues-preview-108s.ogg'
    run(['ffmpeg','-v','error','-nostdin','-f','concat','-safe','0','-i',str(listing),
         '-c:a','libvorbis','-q:a','6',str(overview)])
    cards=[]
    for n,row in enumerate(results):
        cards.append(f'<section><h2>{html.escape(row["title"])}</h2><p>{html.escape(row["direction"])}。全曲 {row["frames"]/48000:.3f} 秒。</p>'
                     f'<p><a href="{row["loop_file"]}">完整循環</a> · <a href="{row["sample_file"]}">30秒試聽</a></p>'
                     f'<audio controls preload="none" src="{row["sample_file"]}"></audio></section>')
    page='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>神州八劍：其餘九曲 HD 配器候選</title>
<style>body{max-width:880px;margin:3rem auto;padding:0 1rem;background:#101d20;color:#eee2c1;font:18px/1.65 sans-serif}a{color:#e1c47e}section{border-top:1px solid #6a754f;padding:1rem 0}audio{width:100%}</style>
<h1>神州八劍：其餘九曲 HD 配器候選</h1>
<p>保留原曲旋律音高、音符時刻、滑音與速度變化。配器延續撥弦與長笛，節奏音色另作 GM 重配。尚未批准，尚未切換正式音樂；全曲與來源留本機。</p>
<p>這是原曲衍生配器，使用 FluidR3 的 Koto、Flute、弦樂及其他 GM 音色，並非真正古箏或竹笛實錄。節奏聲部的固定 GM 鼓音與力度換算不稱原版音色／波形相同。</p>
<p>108秒總覽，每曲12秒，依序為遨遊、刀祭、怡唱、馳騁、幽、靈之舞、悚慄、法域、黎明。</p>
<audio controls preload="none" src="nine-cues-preview-108s.ogg"></audio>'''+''.join(cards)+'</html>'
    (a.out/'index.html').write_text(page)
    report=dict(schema=1,status='unapproved-local-music-candidates',production=False,cues=results,
                soundfont_sha256=SF_SHA,soundfont_license='soundfont-copyright.txt',
                decoder_sha256=sha(Path(__file__).with_name('decode-adlib-music.py')),
                preparer_sha256=sha(Path(__file__)),menu_map_sha256=sha(a.research/'menu-source-map.json'),
                toolchain=dict(timidity=run(['timidity','--version'],capture_output=True,text=True).stdout.splitlines()[0],
                               ffmpeg=run(['ffmpeg','-version'],capture_output=True,text=True).stdout.splitlines()[0]),
                preview_file=overview.name,preview_sha256=sha(overview),
                scope='Nine music-appreciation cues; MFIG remains unmapped; no gameplay trigger or runtime change.',
                loop_method='Three consecutive source-event passes, retain middle without fades or added rest.',
                approved_mint='Existing approved MINT loop unchanged; not regenerated by this tool.')
    (a.out/'candidates.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    for sample in excerpts:sample.unlink()
    # MIDI/logs and Ogg are sufficient for reproduction; raw PCM was audited above.
    for wav in a.out.glob('*-three.wav'):wav.unlink()


if __name__=='__main__':main()
