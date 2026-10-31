#!/usr/bin/env python3
"""Independent source/VM/PCM/alpha-card/X11 audit for recruitment icons."""
import argparse,gzip,hashlib,importlib.util,json,os,struct,tempfile
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw,ImageFont
REL='workplace/probe-20261023/graphics-first/battle-r1/recruit-icons-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):
    with p.open('x')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
    r=a.project;q=r/REL;sp=importlib.util.spec_from_file_location('prep',r/'tools/prepare-recruit-icons.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);h=m.helper(r);deps=h.dependencies(r);assert deps==read(q/'baseline.json')
    assert all(sha(q/'go-src'/n)==v for n,v in deps['source_inputs'].items())
    old=read(r/'preserved/battle-resume-r1.json')
    with tempfile.TemporaryDirectory()as td:
        temp=Path(td);(temp/'tools').mkdir();names=[]
        for f in old['files']:
            marker='/battle-resume-r1/go-src/tools/'
            if marker not in f['path']:continue
            n=f['path'].split(marker,1)[1];(temp/'tools'/n).write_bytes(h.stored(r,'battle-resume-r1',marker+n));names.append(n)
        m.patch(temp)
        for n in names:
            if n in m.NEW or n=='probe-world-army.go':continue
            assert(temp/'tools'/n).read_bytes()==(q/'go-src/tools'/n).read_bytes(),n
        p=temp/'tools/probe-world-army.go';p.write_bytes((r/'tools/probe-world-army.go').read_bytes());m.patch_probe(p);assert p.read_bytes()==(q/'go-src/tools/probe-world-army.go').read_bytes()
    for n in m.NEW:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n),n
    for n,dst in [('research-recruit-icons.go','recruit_icons_candidate.go'),('research-recruit-icons_test.go','recruit_icons_candidate_test.go')]:assert(r/'tools'/n).read_text().removeprefix('//go:build ignore\n')==(q/'go-src/internal/eightsword'/dst).read_text()
    ida=read(q/'ida/ida-recruit-shop-r2.json');assert ida['function_count']==521 and ida['exporter_sha256']==sha(r/'tools/export-recruit-shop-ida.py')and ida['index_sha256']==sha(r/'docs/spec/world-army-consumers-r1.json')
    pam=(q/'inputs/PAM.AY').read_bytes();assert hashlib.sha256(pam).hexdigest()==ida['source_sha256'];header=struct.unpack_from('<H',pam,8)[0]*16;relocs=[];lines=0
    for i in range(struct.unpack_from('<H',pam,6)[0]):off,seg=struct.unpack_from('<HH',pam,struct.unpack_from('<H',pam,24)[0]+i*4);relocs.append(header+seg*16+off)
    for f in ida['functions']:
        for l in f['lines']:
            pos=l['file_offset'];want=bytes.fromhex(l['bytes']);b=bytearray(pam[pos:pos+len(want)]);assert pos==l['ida_linear']-0x10000+header
            for off in relocs:
                if pos<=off and off+2<=pos+len(want):struct.pack_into('<H',b,off-pos,(struct.unpack_from('<H',b,off-pos)[0]+0x1000)&65535)
            assert bytes(b)==want;lines+=1
    asset=read(q/'asset-test-r2/receipt.json');assert asset['status']=='passed-25-real-recruitment-icons'and len(asset['rows'])==25
    for row in asset['rows']:
        im=Image.open(q/'asset-test-r2'/row['file']).convert('RGBA');raw=(q/f"asset-test-r2/kind{row['kind']:02d}.rgba").read_bytes();assert im.size==(264,300)and len(raw)==264*300*4 and hashlib.sha256(raw).hexdigest()==row['rgba_sha256'];assert im.getchannel('A').getbbox()
    assert all(asset[k]for k in ['cache_immutable','native_mode_nil','unknown_kind_nil','missing_material_nil'])
    c,d=q/'control-r3',q/'icons-r3';states=[]
    for n in ['projected-map.state','shop-maximum.state','before-commit.state','after-commit.state','final-map.state']:
        assert sha(c/n)==sha(d/n),n;states.append(dict(file=n,sha256=sha(c/n)))
    assert sha(c/'PCM.raw')==sha(d/'PCM.raw')and(c/'PCM.raw').stat().st_size>0
    for n in ['native-army-before.bin','native-army-after.bin','pair-before.json','pair-after.json']:assert(c/n).read_bytes()==(d/n).read_bytes(),n
    control,icons=read(c/'receipt.json'),read(d/'receipt.json');assert control==icons and icons['maximum']==70 and icons['guest_gold']==299
    events=read(d/'icons.json');assert events['cached_kinds']==25 and events['frames']>0 and not events['active']
    entry=next(v for v in events['events']if v['event']=='entry');after=next(v for v in events['events']if v['event']=='native-stock-after');assert entry['stock']==3000 and after['stock']==2999 and after['count']==1 and entry['row']==after['row']
    # Rebuild the card from the separately dumped immutable actor cache.
    base=Image.open(c/'shop-maximum.png').convert('RGBA');actual=Image.open(d/'shop-maximum.png').convert('RGBA');expected=base.copy();paint=ImageDraw.Draw(expected)
    card=(1060,96,1324,618);paint.rectangle((1060,96,1323,617),fill=(176,150,85,255));paint.rectangle((1063,99,1320,614),fill=(7,36,26,255))
    icon=Image.open(q/'asset-test-r2/kind01.png').convert('RGBA');raw=(q/'asset-test-r2/kind01.rgba').read_bytes();box=icon.getchannel('A').getbbox();sw,sh=box[2]-box[0],box[3]-box[1];w,hh=222,480
    if w*sh>hh*sw:w=hh*sw//sh
    else:hh=w*sh//sw
    x0,y0=1081+(222-w)//2,117+(480-hh)//2
    for y in range(hh):
        for x in range(w):
            sx,sy=box[0]+x*sw//w,box[1]+y*sh//hh;at=(sy*264+sx)*4;pixel=raw[at:at+4];alpha=pixel[3]
            if alpha:expected.putpixel((x0+x,y0+y),tuple((pixel[i]+((7,36,26)[i]*(255-alpha)+127)//255)&255 for i in range(3))+(255,))
    assert expected.tobytes()==actual.tobytes(),'card reconstruction mismatch'
    bbox=ImageChops.difference(base.convert('RGB'),actual.convert('RGB')).getbbox();assert bbox and bbox[0]>=card[0]and bbox[1]>=card[1]and bbox[2]<=card[2]and bbox[3]<=card[3]
    assert(c/'final-map.png').read_bytes()==(d/'final-map.png').read_bytes(),'icon leaked after departure'
    gui=read(q/'gui-r4/receipt.json');assert gui['status']=='passed-actual-hd-recruit-icons'and gui['cold']['native_rows_hex']==gui['saved']['native_rows_hex']and gui['cold']['recruit_icons']['native_gold']==gui['saved']['recruit_icons']['native_gold']
    capture_timing=[]
    for s in gui['screens']:
        folder=q/'gui-r4'/s['phase'];im=Image.open(folder/s['canvas']).convert('RGBA');screen=Image.open(folder/s['screen']).convert('RGBA');meta=read(folder/s['metadata']);assert hashlib.sha256(screen.tobytes()).hexdigest()==meta['canvas_sha256']==meta['presented_sha256']
        # F12 PNG precedes the later X11/metadata sample. Numeric input has a
        # moving underline; compare X11 against its actual submitted Go SHA.
        if im.tobytes()!=screen.tobytes():
            assert im.crop(card).tobytes()==screen.crop(card).tobytes()
            diff=ImageChops.difference(im.convert('RGB'),screen.convert('RGB')).getbbox();assert diff and diff[1]>=1030 and diff[3]<=1080
            capture_timing.append(dict(phase=s['phase'],png=s['canvas'],difference_bbox=diff,png_rgba_sha256=hashlib.sha256(im.tobytes()).hexdigest(),x11_matches_submitted_sha256=meta['presented_sha256']))
    write(a.out,dict(status='passed-hd-recruit-icons-candidate',asset_test=asset,ida_lines=lines,native_stock_entry=entry,native_stock_after=after,identical_states=states,pcm_sha256=sha(c/'PCM.raw'),pcm_bytes=(c/'PCM.raw').stat().st_size,card_bbox=bbox,card_independently_rebuilt=True,gui=gui,verified_x11_frames=len(gui['screens']),capture_timing=capture_timing,dependencies=deps,source_tools={n:sha(r/'tools'/n)for n in m.NEW},formal_changed=False,production_promoted=False,limits=['Shared 25-native-unit cache mapping, one real shop UI sample; eight openKB candidate portraits are not added.','Native stock decrement observed; persistent Go shop identity, refresh and interrupted purchase still DRAFT.']))
if __name__=='__main__':main()
