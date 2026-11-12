#!/usr/bin/env python3
"""057：將已批准PNG編碼成既有材質資料；不修改美術、玩法或開場命令。"""
import gzip, hashlib, json, math, os, shutil, struct
from pathlib import Path
from PIL import Image
from rust_package_settings import REL, VERSION

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def fnv(raw):
    n = 14695981039346656037
    for b in raw: n = ((n ^ b) * 1099511628211) & 0xffffffffffffffff
    return n
def panels(path):
    im = Image.open(path).convert('RGBA'); assert im.getextrema()[3] == (255,255)
    w,h=im.size; src=im.tobytes(); out=bytearray(1024*1200*4)
    for side,(left,right) in enumerate([(160,469),(1640,1949)]):
        xs=[]
        for x in range(512):
            fx=max(0,min(w-1,left+(x+.5)*(right-left)/512-.5));x0=int(fx)
            fade=min(1,max(0,((512-x) if side==0 else x)/112));fade=fade*fade*(3-2*fade)
            xs.append((x0,min(x0+1,w-1),fx-x0,fade))
        for y in range(1200):
            fy=max(0,min(h-1,(y+.5)*724/1200-.5));y0=int(fy);y1=min(y0+1,h-1);v=fy-y0
            for x,(x0,x1,u,f) in enumerate(xs):
                a=(y0*w+x0)*4;b=(y0*w+x1)*4;c=(y1*w+x0)*4;d=(y1*w+x1)*4;at=(y*1024+side*512+x)*4
                for k,base in enumerate([8,36,23]):
                    sample=math.floor(src[a+k]*(1-u)*(1-v)+src[b+k]*u*(1-v)+src[c+k]*(1-u)*v+src[d+k]*u*v+.5)
                    out[at+k]=math.floor(sample*f+base*(1-f)+.5)
                out[at+3]=255
    raw=b'8SRGBA01'+struct.pack('<II',1024,1200)+out
    return raw+struct.pack('<Q',fnv(raw))

def main():
    assert Path('/.dockerenv').exists() and os.getuid()==1000
    r=Path('/r');q=r/REL;pack=q/'native/pack';base=r/'workplace/probe-20261023/graphics-first/battle-r1/rust-player-path-r1/native/pack'
    prefix='workplace/probe-20261023/graphics-first/battle-r1/rust-player-path-r1/native/pack/'
    files=[f for f in json.loads((r/'preserved/rust-player-path-r1.json').read_text())['files']if f['path'].startswith(prefix)]
    assert len(files)==287
    for f in files:
        p=r/f['path'];assert sha(p)==f['sha256'];dest=pack/f['path'][len(prefix):];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    rebuilt=panels(r/'docs/images/poster-wings-approved-r1.png');assert rebuilt==(base/'poster-wings.rgba').read_bytes(),'panel normalization must match previous Go builder exactly'
    (pack/'poster-wings.rgba').write_bytes(panels(r/'docs/images/poster-wings-head-fixed-r2.png'))
    raw=(base/'intro.bin').read_bytes();at=128020;count=struct.unpack_from('<I',raw,at)[0];at+=4;rows=[]
    for i in range(count):
        start=at;w,h,kind,x,y,cw,ch=struct.unpack_from('<HHBHHHH',raw,at);at+=13;end=at+cw*ch*(8 if kind==0 else 4)
        assert end<len(raw)
        rows.append(dict(index=i,start=start,data_start=at,end=end,width=w,height=h,kind=kind,crop=[x,y,cw,ch],sha256=hashlib.sha256(raw[at:end]).hexdigest()));at=end
    table=dict(count=count,textures=rows,tail_offset=at,source_sha256=sha(base/'intro.bin'))
    (q/'evidence/intro-textures.json').write_text(json.dumps(table,indent=2)+'\n');tex=rows[96]
    assert (tex['width'],tex['height'],tex['kind'],tex['crop'])==(1920,1200,0,[0,0,1920,1200])
    im=Image.open(r/'docs/images/story-background-head-fixed-r5.png').convert('RGBA').resize((1920,1200),Image.Resampling.LANCZOS)
    assert im.getextrema()[3]==(255,255)
    rgba=im.tobytes();wide=bytearray(len(rgba)*2);wide[::2]=rgba;wide[1::2]=rgba
    lo,hi=tex['data_start'],tex['end'];assert len(wide)==hi-lo
    body=raw[:lo]+wide+raw[hi:-8];checksum=fnv(body);updated=body+struct.pack('<Q',checksum)
    assert len(updated)==len(raw)and updated[:lo]==raw[:lo]and updated[hi:-8]==raw[hi:-8]
    (pack/'intro.bin').write_bytes(updated)
    previous=json.loads((r/'preserved/rust-package-r1.json').read_text())
    f=next(f for f in previous['files']if f['path'].endswith('/frozen-source/intro-plan.tsv'));obj=previous['objects'][f['sha256']]
    old_plan=gzip.decompress((r/'preserved/rust-package-r1'/obj['file']).read_bytes()).decode();assert hashlib.sha256(old_plan.encode()).hexdigest()==f['sha256']
    plan=r/'internal/remake-rust/intro-plan.tsv';values=old_plan.split();assert len(values)==3 and int(values[1],16)==struct.unpack_from('<Q',raw,len(raw)-8)[0]
    values[1]=format(checksum,'016x');plan.write_text('\t'.join(values)+'\n')
    replacements=[]
    for name in['poster-wings.rgba','intro.bin']:
        replacements.append(dict(name=name,old_sha256=sha(base/name),sha256=sha(pack/name),bytes=(pack/name).stat().st_size))
    assert {f['path'][len(prefix):]for f in files if sha(pack/f['path'][len(prefix):])!=f['sha256']}=={'poster-wings.rgba','intro.bin'}
    evidence=dict(version=VERSION,files=replacements,unchanged_media=285,texture_index=96,texture_bytes=[lo,hi],intro_all_other_bytes_unchanged=True,source_intro_sha256=sha(base/'intro.bin'),source_plan=old_plan,new_plan=plan.read_text(),old_panel_rebuild_equal=True,masters=[dict(path=n,sha256=sha(r/n))for n in['docs/images/poster-wings-head-fixed-r2.png','docs/images/story-background-head-fixed-r5.png']],scope='Asset encoding only. Entire cinematic program, original-mode blobs, glyphs, timeline and music references remain unchanged.')
    (q/'media-overlay.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n');im.save(q/'evidence/corrected-story-normalized.png')
    print(json.dumps(dict(status='passed-two-art-asset-preparation',changed_media=2,unchanged_media=285,plan=values)))

if __name__=='__main__':main()
