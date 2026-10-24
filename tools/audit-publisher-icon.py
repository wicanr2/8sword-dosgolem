"""016：正常冷啟動三組的客體隔離與完整畫面差異範圍。Docker only。"""
import argparse
import gzip
import hashlib
import json
import struct
from itertools import zip_longest
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def stream(root):
    with gzip.open(root/'presentation.frames.gz','rb') as f:
        def take(n):
            b=f.read(n);assert len(b)==n;return b
        assert take(8)==b'8SFRM001' and struct.unpack('<II',take(8))==(1920,1200)
        rgba=bytearray(1920*1200*4);number=0
        while header:=f.read(24):
            assert len(header)==24
            n,step,rows=struct.unpack('<QQQ',header);number+=1
            assert n==number and rows<=1200
            if n==1:assert rows==1200
            seen=set()
            for _ in range(rows):
                y,=struct.unpack('<H',take(2));assert y<1200 and y not in seen;seen.add(y)
                rgba[y*7680:(y+1)*7680]=take(7680)
            yield n,step,bytes(rgba)

def main():
    p=argparse.ArgumentParser()
    for n in ('hd','control','broken','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();roots=[a.hd,a.control,a.broken];finals=[read(d/'gui-final.json') for d in roots]
    for name in ['final.state','audio.pcm']:
        hashes=[sha(d/name) for d in roots];assert len(set(hashes))==1,name
    for key in ['input_events','exec_log','file_ops','bios_consumed','irq1_delivered','unimplemented','recorded_frames','frame_pure_count']:
        assert finals[0][key]==finals[1][key]==finals[2][key],key
    def files(root):return {str(f.relative_to(root)):sha(f) for f in root.rglob('*') if f.is_file()}
    scratch=[files(d/'scratch') for d in roots];assert scratch[0]==scratch[1]==scratch[2]
    assert all(f['recorded_frames']==f['frame_pure_count'] for f in finals)
    assert finals[0]['intro_publisher']['icon']=={'loaded':True,'load_error':''}
    assert finals[1]['intro_publisher']['icon']=={'loaded':False,'load_error':''}
    assert finals[2]['intro_publisher']['icon']=={'loaded':False,'load_error':'發行商圖案 publisher-icon.png SHA-256 不符'}
    logs=[[json.loads(x) for x in (d/'intro-draw.jsonl').read_text().splitlines()] for d in roots]
    changed=0;unchanged=0;published=0
    for triple in zip_longest(*(stream(d) for d in roots)):
        assert all(x is not None for x in triple)
        (n,step,hd),(cn,cs,control),(bn,bs,broken)=triple
        assert (n,step)==(cn,cs)==(bn,bs)
        info=[rows[n-1] for rows in logs];assert all(i['draw']==n and i['step']==step for i in info)
        assert info[0]['stage']==info[1]['stage']==info[2]['stage']
        assert broken==control,('broken differs',n)
        publisher=info[0]['stage'] in ['publisher-noto','publisher-transition']
        if publisher:published+=1
        if hd!=control:
            assert publisher,('outside publisher differs',n,info[0]['stage'])
            changed+=1
        else:unchanged+=1
    assert changed>0 and n==finals[0]['recorded_frames'] and all(len(rows)==n for rows in logs)
    result=dict(status='passed-publisher-icon-normal-isolation',frames_per_run=n,frame_purity=sum(f['frame_pure_count'] for f in finals),state_sha256=sha(a.hd/'final.state'),pcm_sha256=sha(a.hd/'audio.pcm'),scratch_files=len(scratch[0]),publisher_frames=published,changed_publisher_frames=changed,unchanged_frames=unchanged,all_broken_frames_equal_control=True,limit='Fixed normal cold-boot inputs, no guest injection; art exact RGBA and actual GUI checked separately')
    assert not a.out.exists();a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
