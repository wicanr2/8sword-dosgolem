#!/usr/bin/env python3
"""Rust重製推廣影片：Docker內旁白、合成、驗收與保存。"""
import argparse,asyncio,gzip,hashlib,importlib.util,json,math,os,re,shutil,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
BATCH='rust-promo-r1';REL='workplace/probe-20261023/graphics-first/battle-r1/'+BATCH
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def checksum_manifest(out):
    version=json.loads((out/'manifest.json').read_text())['version']
    write(out.parent/'SHA256SUMS.json',dict(version=version,kind='local-development-promo-preview',files=[dict(path=str(p.relative_to(out.parent)),sha256=sha(p),bytes=p.stat().st_size)for p in sorted(out.rglob('*'))if p.is_file()]))
def run(args,log=None):
    result=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    if log:log.write_bytes(result.stdout+result.stderr)
    if result.returncode:raise RuntimeError((args,result.stderr.decode(errors='replace')[-2500:]))
    return result.stdout
def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','voice','plan','cards','compose','audit','contact','archive','verify','restore'])
    for n in ['project','work','out','archive']:p.add_argument('--'+n,type=Path)
    p.add_argument('--version');p.add_argument('--only-scenes');a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
    r=a.project;q=a.work or r/REL
    if a.action=='prepare':
        q.mkdir(parents=True,exist_ok=True);assert q.stat().st_uid==1000
        for n in ['voice','capture','assets','evidence','segments']:(q/n).mkdir(exist_ok=True)
        data=json.loads((r/'tools/rust-promo-scenes.json').read_text())
        def immutable(path,raw):
            if path.exists():assert path.read_bytes()==raw
            else:path.write_bytes(raw)
        immutable(q/'storyboard.json',(r/'tools/rust-promo-scenes.json').read_bytes())
        for scene in data['scenes']:immutable(q/'voice'/f"{scene['id']:02}.txt",scene['narration'].encode())
        s=importlib.util.spec_from_file_location('helper',r/'tools/prepare-owned-army-ui.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
        catalog=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()))
        for name in ['noto','lishu']:
            digest=h.FONT_SHA[name];raw=gzip.decompress((r/'preserved'/catalog['objects'][digest]['path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==digest;immutable(q/'assets'/(name+'.font'),raw)
        old='workplace/probe-20261023/graphics-first/battle-r1/rust-player-path-r1/';files=[]
        for f in json.loads((r/'preserved/rust-player-path-r1.json').read_text())['files']:
            sub=str(Path(f['path']).relative_to(old))
            if sub=='native/8sword-remake'or sub.startswith('native/pack/'):
                assert sha(r/f['path'])==f['sha256'];files.append(f)
        assert len(files)==288;write(q/'evidence/runtime.json',dict(files=files,rights='Original-derived runtime media stays local',product_head='732dd48',runtime_source_head='4c1fe9f'))
        immutable(q/'assets/score.ogg',(r/old/'native/pack/start-music-1.ogg').read_bytes());return
    if a.action=='voice':
        import edge_tts
        async def speak():
            for source in sorted(q.glob('*.txt')):
                target=source.with_suffix('.mp3');assert not target.exists()
                await edge_tts.Communicate(source.read_text(),'zh-TW-HsiaoChenNeural',rate='-8%').save(str(target))
            write(q/'voice-source.json',dict(provider='Microsoft Edge online TTS',voice='zh-TW-HsiaoChenNeural',rate='-8%',synthetic=True,files={p.name:sha(p)for p in q.glob('*.mp3')}))
        asyncio.run(speak());return
    if a.action=='plan':
        data=json.loads((q/'storyboard.json').read_text());start=0
        for scene in data['scenes']:
            source=q/'voice'/f"{scene['id']:02}.mp3"
            probe=json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(source)]))
            speech=float(probe['format']['duration']);duration=max(8,math.ceil((speech+1.2)*30)/30)
            scene.update(start=round(start,6),speech_duration=speech,duration=duration,voice_sha256=sha(source));start+=duration
        data['duration']=round(start,6);write(q/'timeline.json',data);return
    if a.action=='cards':
        from PIL import Image,ImageDraw,ImageFont
        data=json.loads((q/'timeline.json').read_text());fontfile=str(q/'assets/noto.font')
        caption=ImageFont.truetype(fontfile,44,index=3);header=ImageFont.truetype(fontfile,34,index=3);small=ImageFont.truetype(fontfile,28,index=3)
        titlefont=ImageFont.truetype(str(q/'assets/lishu.font'),148);records=[]
        tags=['HD重製開場','原圖模式（Rust）','原式地圖與管理','HD開場｜美術停格','字型／海報／畫面設定','正常募兵＋可選AI／規則','受控法術示範（Rust）','自然戰鬥／正常進度續玩','開發中／Linux代表路徑已驗']
        def centered(draw,text,font,y,color=(255,241,181,255),left=40,right=1880):
            width=draw.textlength(text,font=font);assert width<=right-left,(text,width)
            box=draw.textbbox(((left+right-width)/2,y),text,font=font,anchor='lt');assert 0<=box[0]and box[2]<=1920 and 0<=box[1]and box[3]<=1080
            draw.text(((left+right-width)/2,y),text,font=font,fill=color,anchor='lt');return list(box)
        for scene,tag in zip(data['scenes'],tags):
            image=Image.new('RGBA',(1920,1080),(0,0,0,0));draw=ImageDraw.Draw(image)
            draw.rectangle((0,0,1919,71),fill=(9,36,29,255));draw.rectangle((0,934,1919,1079),fill=(9,36,29,255))
            assert draw.textlength(scene['title'],font=header)<1100
            draw.text((40,18),scene['title'],font=header,fill=(239,216,155,255),anchor='lt')
            width=draw.textlength(tag,font=small);assert width<700;draw.text((1880-width,22),tag,font=small,fill=(225,224,206,255),anchor='lt')
            lines=[];line=''
            for char in scene['narration']:
                if draw.textlength(line+char,font=caption)>1728:lines.append(line);line=char
                else:line+=char
            if line:lines.append(line)
            assert len(lines)<=2
            boxes=[centered(draw,line,caption,948+(2-len(lines))*28+i*58)for i,line in enumerate(lines)]
            if scene['id']in [1,9]:
                draw.rounded_rectangle((330,300,1590,758),radius=22,fill=(4,20,17,225),outline=(206,170,74,255),width=2)
                centered(draw,'神州八劍',titlefont,348)
                centered(draw,'保存經典，繼續冒險'if scene['id']==9 else'從DOS原作，走向Rust獨立重製',header,552)
                centered(draw,'開發中｜本機預覽',small,624)
                if scene['id']==9:centered(draw,'wicanr2 / 8sword-dosgolem',small,686)
                if scene['id']==9:
                    draw.rectangle((0,878,1919,933),fill=(9,36,29,235))
                    centered(draw,'原版版權標示：智冠科技｜旁白：合成華語｜配樂：遊戲內HD〈幻〉',small,890)
            output=q/'assets'/f"card-{scene['id']:02}.png";image.save(output)
            records.append(dict(id=scene['id'],subtitle_lines=lines,boxes=boxes,sha256=sha(output)))
        write(q/'evidence/text-layout.json',dict(size=[1920,1080],font_sha256=sha(q/'assets/noto.font'),title_font_sha256=sha(q/'assets/lishu.font'),safe_rect=[96,934,1728,146],scenes=records));return
    if a.action=='compose':
        assert a.version and re.fullmatch(r'v\.[0-9]+\.[0-9]+\.[0-9]+-[0-9]{8}',a.version)
        data=json.loads((q/'timeline.json').read_text());assert a.version==data['delivery_id']
        out=a.out or r/'dist-all'/a.version/'promo';assert out.name=='promo'and out.parent.name==a.version
        selected=set(map(int,a.only_scenes.split(',')))if a.only_scenes else set(range(1,10))
        if out.exists():
            assert a.only_scenes;old=json.loads((out/'manifest.json').read_text());assert old['not_a_game_release']and old['version']==a.version and old['sha256']==sha(out/old['file'])
            prior=json.loads((q/'evidence/cards-before-refine.json').read_text());current=json.loads((q/'evidence/text-layout.json').read_text())
            assert all(x['sha256']==y['sha256']for x,y in zip(prior['scenes'],current['scenes'])if x['id']not in selected)
        else:out.mkdir(parents=True)
        capture=json.loads((q/'capture/receipt.json').read_text());assert capture['status']=='passed-rust-promo-live-capture'
        def marker(name,label):return next(m['seconds']for m in next(v for v in capture['runs']if v['name']==name)['markers']if m['label']==label)
        def probe(path):return json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)]))
        inputs={name:q/'capture'/name/'live.mp4'for name in ['original','hd','effects','continued']};lengths={name:float(probe(path)['format']['duration'])for name,path in inputs.items()};sources=[]
        if a.only_scenes:sources=[v for v in json.loads((out/'sources.json').read_text())['sources']if v['scene']not in selected]
        common=['-hide_banner','-loglevel','warning','-threads','2','-filter_threads','1','-filter_complex_threads','1']
        for scene in data['scenes']:
            i=scene['id'];duration=scene['duration']
            if i not in selected:assert(q/'segments'/f'{i:02}.mkv').is_file();continue
            choices={1:[('hd',7,duration)],2:[('original',marker('original','world-start')-.5,duration)],3:[('hd',marker('hd','world-start'),duration)],4:[('hd',7.9,4,1),('hd',13.8,duration-4)],5:[('hd',marker('hd','settings-start'),duration)],6:[('hd',marker('hd','settings-start')-6,duration/2),('hd',marker('hd','choices-start'),duration-duration/2)],7:[('effects',marker('effects','effects-start'),duration)],8:[('hd',marker('hd','natural-encounter'),5),('continued',marker('continued','monthly-view')-1,duration-5)],9:[('hd',marker('hd','closing-start')-1,duration)]}[i]
            pieces=[]
            for n,choice in enumerate(choices):
                name,start,seconds=choice[:3];span=choice[3]if len(choice)>3 else None
                extension=max(0,start+seconds-lengths[name]);assert extension<2.1,(i,extension)
                output=q/'segments'/f'{i:02}-{n}.mp4';pieces.append(output)
                limit=['-t',str(span)]if span else[]
                run(['ffmpeg','-y',*common,'-ss',str(start),*limit,'-i',str(inputs[name]),'-an','-vf',f'tpad=stop_mode=clone:stop_duration=3,scale=1920:862:flags=lanczos,fps=30,setsar=1','-frames:v',str(round(seconds*30)),'-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p',str(output)],q/'segments'/f'{i:02}-{n}.log')
                sources.append(dict(scene=i,source=name,start=start,duration=seconds,intentional_art_hold=seconds-span if span else 0,intentional_outro_hold=extension,source_sha256=sha(inputs[name])))
            playlist=q/'segments'/f'{i:02}-parts.txt';playlist.write_text(''.join(f"file '{v.name}'\n"for v in pieces));base=q/'segments'/f'{i:02}-base.mp4'
            run(['ffmpeg','-y',*common,'-f','concat','-safe','0','-i',str(playlist),'-c','copy',str(base)])
            result=q/'segments'/f'{i:02}.mkv';graph=f'[0:v]pad=1920:1080:0:72:color=0x09241d[b];[b][1:v]overlay=0:0,fade=t=in:d=0.18:color=0x09241d,fade=t=out:st={duration-.18}:d=0.18:color=0x09241d,format=yuv420p[v];[2:a]loudnorm=I=-16:TP=-3:LRA=7,aformat=sample_rates=48000:channel_layouts=stereo,adelay=400|400,apad,atrim=duration={duration}[a]'
            run(['ffmpeg','-y',*common,'-i',str(base),'-loop','1','-i',str(q/'assets'/f'card-{i:02}.png'),'-i',str(q/'voice'/f'{i:02}.mp3'),'-filter_complex',graph,'-map','[v]','-map','[a]','-t',str(duration),'-r','30','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','pcm_s16le',str(result)],q/'segments'/f'{i:02}.log')
        listing=q/'segments/concat.txt';listing.write_text(''.join(f"file '{i:02}.mkv'\n"for i in range(1,10)));rough=q/'segments/rough.mkv'
        run(['ffmpeg','-y',*common,'-f','concat','-safe','0','-i',str(listing),'-map','0:v','-map','0:a','-c','copy',str(rough)])
        music=q/'assets/score.ogg';assert music.is_file();final=out/f'8sword-rust-promo-{a.version}.mp4'
        graph=f'[1:a]volume=0.10,afade=t=in:d=0.8,afade=t=out:st={data["duration"]-1.5}:d=1.5[m];[0:a][m]amix=inputs=2:duration=first:normalize=0,volume=1.35,alimiter=limit=0.89:level=0[a]'
        run(['ffmpeg','-y',*common,'-i',str(rough),'-stream_loop','-1','-i',str(music),'-filter_complex',graph,'-map','0:v','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-t',str(data['duration']),'-movflags','+faststart',str(final)],q/'evidence/final-encode.log')
        def stamp(value):
            ms=round(value*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
        (out/'繁體字幕.srt').write_text('\n\n'.join(f'{i}\n{stamp(s["start"]+.1)} --> {stamp(s["start"]+s["duration"]-.1)}\n{s["narration"]}'for i,s in enumerate(data['scenes'],1))+'\n')
        write(out/'storyboard.json',data);write(out/'sources.json',dict(capture=capture,sources=sources,music=dict(path='runtime/pack/start-music-1.ogg',title='幻',kind='approved in-game HD arrangement, not original OPL capture',sha256=sha(music)),voice=json.loads((q/'voice/voice-source.json').read_text()),rights='Local development preview only; original-derived game media and melody, no public distribution or Release authorization asserted',product_head='732dd48',runtime_source_head='4c1fe9f'))
        write(out/'manifest.json',dict(version=a.version,kind='local-development-promo-preview',file=final.name,sha256=sha(final),bytes=final.stat().st_size,duration=data['duration'],width=1920,height=1080,fps=30,not_a_game_release=True));write(q/'delivery.json',dict(directory=str(out.relative_to(r)),video=final.name));return
    if a.action=='audit':
        delivery=json.loads((q/'delivery.json').read_text());out=r/delivery['directory'];movie=out/delivery['video'];digest=sha(movie);manifest=json.loads((out/'manifest.json').read_text());assert digest==manifest['sha256']
        data=json.loads((q/'timeline.json').read_text());probe=json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(movie)]));write(out/'ffprobe.json',probe)
        video=next(s for s in probe['streams']if s['codec_type']=='video');audio=next(s for s in probe['streams']if s['codec_type']=='audio')
        assert video['codec_name']=='h264'and(video['width'],video['height'])==(1920,1080)and video['r_frame_rate']=='30/1'
        assert audio['codec_name']=='aac'and audio['sample_rate']=='48000'and audio['channels']==2
        assert abs(float(probe['format']['duration'])-data['duration'])<.2
        log=out/'audio-video-check.log'
        run(['ffmpeg','-hide_banner','-threads','2','-filter_threads','1','-i',str(movie),'-vf','blackdetect=d=0.4:pix_th=0.10:pic_th=0.98,freezedetect=n=-50dB:d=2','-af','volumedetect,silencedetect=noise=-45dB:d=0.7','-f','null','-'],log)
        text=log.read_text();peak=float(re.search(r'max_volume: ([-0-9.]+) dB',text).group(1));mean=float(re.search(r'mean_volume: ([-0-9.]+) dB',text).group(1));assert -8<peak<-.1 and -30<mean<-8,(peak,mean)
        black=[float(v)for v in re.findall(r'black_duration:([0-9.]+)',text)];silence=[float(v)for v in re.findall(r'silence_duration: ([0-9.]+)',text)];assert not any(v>.5 for v in black);assert not any(v>1 for v in silence)
        freezes=[];starts=list(map(float,re.findall(r'freeze_start: ([0-9.]+)',text)));ends=list(map(float,re.findall(r'freeze_end: ([0-9.]+)',text)))
        for i,start in enumerate(starts):
            finish=ends[i]if i<len(ends)else float(probe['format']['duration']);length=finish-start;scene=next(s for s in data['scenes']if s['start']<=start<s['start']+s['duration'])
            assert length<6 or scene['id']in[1,9],(start,length,scene['id'])
            freezes.append(dict(start=start,end=finish,duration=length,scene=scene['id'],classification='intentional title/outro card'if scene['id']in[1,9]else 'explicit HD art appreciation hold'if scene['id']==4 else 'bounded pause in actual intro/menu/input footage'))
        frames=out/'frames';frames.mkdir(exist_ok=True);samples=[]
        positions=[(f"scene-{s['id']:02}",s['start']+s['duration']/2,s['id'])for s in data['scenes']]+[('opening-title',1.0,1),('outro-credit',data['duration']-1.4,9),('heroine-detail',data['scenes'][3]['start']+2,4),('real-monthly',data['scenes'][7]['start']+data['scenes'][7]['duration']-1.5,8)]
        for label,at,scene in positions:
            target=frames/(label+'.jpg');run(['ffmpeg','-y','-hide_banner','-loglevel','error','-threads','2','-filter_threads','1','-ss',str(at),'-i',str(movie),'-frames:v','1','-q:v','2',str(target)]);samples.append(dict(label=label,seconds=at,scene=scene,sha256=sha(target)))
        runtime=json.loads((q/'evidence/runtime.json').read_text());capture=json.loads((q/'capture/receipt.json').read_text());assert len(runtime['files'])==288
        binary=next(v for v in runtime['files']if v['path'].endswith('/native/8sword-remake'));assert capture['binary_sha256']==binary['sha256']
        report=dict(status='passed-rust-promo-technical-audit',version=manifest['version'],movie_sha256=digest,duration=float(probe['format']['duration']),resolution=[1920,1080],fps=30,video_codec='h264',audio_codec='aac',audio_rate=48000,audio_channels=2,peak_db=peak,mean_db=mean,black_durations=black,silence_durations=silence,freezes=freezes,samples=samples,voices=9,live_runs=len(capture['runs']),runtime_binary_sha256=binary['sha256'],visual_contact_review_pending=True,hearing_review_claimed=False,rights='Local preview; no public distribution permission asserted',limits=['Current Rust original-asset mode is not a new DOS capture.','Main recruitment/natural win follows normal seed1 new game; separate spell sample is controlled and labeled.','HD in-game arrangement and synthetic narration are explicitly credited; no original OPL or human narration claim.','No full campaign, platform release or mobile acceptance claim.'])
        write(out/'audit.json',report);write(q/'evidence/technical-audit.json',report);return
    if a.action=='contact':
        from PIL import Image,ImageDraw,ImageFont
        delivery=json.loads((q/'delivery.json').read_text());out=r/delivery['directory'];report=json.loads((out/'audit.json').read_text());data=json.loads((q/'timeline.json').read_text());font=ImageFont.truetype(str(q/'assets/noto.font'),32,index=3)
        canvas=Image.new('RGB',(2880,1758),(9,36,29));draw=ImageDraw.Draw(canvas)
        for i,scene in enumerate(data['scenes']):
            x=i%3*960;y=i//3*586;draw.text((x+16,y+8),f"{scene['id']:02}｜{scene['name']}：{scene['title']}",font=font,fill=(239,216,155));im=Image.open(out/'frames'/f"scene-{scene['id']:02}.jpg");canvas.paste(im.resize((960,540),Image.Resampling.LANCZOS),(x,y+46))
        canvas.save(out/'contact-sheet.jpg',quality=94)
        assert a.out;shutil.copy2(out/'contact-sheet.jpg',a.out)
        write(a.out.with_suffix('.json'),dict(movie_sha256=report['movie_sha256'],image_sha256=sha(a.out),source_frames=report['samples'][:9],scope='Midpoint of each scene from the final encoded local preview; live Rust footage, controlled spell clip labeled.'));return
    if a.action in ['archive','verify']:
        if a.action=='archive':
            delivery=json.loads((q/'delivery.json').read_text());folder=r/delivery['directory'];checksum_manifest(folder);shutil.copy2(folder.parent/'SHA256SUMS.json',q/'root-SHA256SUMS.json');shutil.copytree(folder,q/'delivery');(q/'tools').mkdir(exist_ok=True)
            for name in ['rust-promo.py','rust-promo-capture.py','rust-promo-scenes.json','rust-promo.sh']:shutil.copy2(r/'tools'/name,q/'tools'/name)
        s=importlib.util.spec_from_file_location('archive',r/'tools/rust-combat-inventory.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.BATCH=BATCH;m.REL=REL;m.main()
        if a.action=='archive':
            index=json.loads(a.out.read_text());index['rights']='Local promotional development preview; original-derived game images/melody, approved HD arrangement and synthetic narration. No public distribution or game Release authorization asserted.';write(a.out,index)
        return
    if a.action=='restore':
        assert a.out;index=json.loads((r/'preserved'/f'{BATCH}.json').read_text());count=0
        for f in index['files']:
            sub=Path(f['path']).relative_to(REL)
            if sub.parts[0]!='delivery':continue
            obj=index['objects'][f['sha256']];source=r/'preserved'/BATCH/obj['file'];assert sha(source)==obj['stored_sha256'];raw=gzip.decompress(source.read_bytes());assert hashlib.sha256(raw).hexdigest()==f['sha256']
            target=a.out/Path(*sub.parts[1:]);target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():assert target.read_bytes()==raw
            else:target.write_bytes(raw);target.chmod(f['mode'])
            count+=1
        assert count>=18
        if a.out.name=='promo'and a.out.parent.name==json.loads((a.out/'manifest.json').read_text())['version']:checksum_manifest(a.out)
        return
    raise NotImplementedError(a.action)
if __name__=='__main__':main()
