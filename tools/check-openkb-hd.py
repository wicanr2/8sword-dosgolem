#!/usr/bin/env python3
"""Independent source, alpha, ID mapping, safe geometry and actual X11 audit."""
import argparse,gzip,hashlib,importlib.util,json,os,tempfile
from pathlib import Path
from PIL import Image
REL='workplace/probe-20261023/graphics-first/battle-r1/openkb-hd-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def overlap(a,b):return max(a[0],b[0])<min(a[2],b[2])and max(a[1],b[1])<min(a[3],b[3])
def inside(a,b):return b[0]<=a[0]<=a[2]<=b[2]and b[1]<=a[1]<=a[3]<=b[3]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();assert Path('/.dockerenv').exists()and os.getuid()==1000
    r=a.project;q=r/REL;sp=importlib.util.spec_from_file_location('prep',r/'tools/prepare-openkb-hd.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);h=m.helper(r);deps=h.dependencies(r);assert deps==read(q/'baseline.json');assert all(sha(q/'go-src'/n)==v for n,v in deps['source_inputs'].items())
    with tempfile.TemporaryDirectory()as td:
        t=Path(td);(t/'tools').mkdir()
        for n in m.PATCHED:(t/'tools'/n).write_bytes(h.stored(r,'camp-stock-r1','/camp-stock-r1/go-src/tools/'+n))
        m.patch(t)
        for n in m.PATCHED:assert(t/'tools'/n).read_bytes()==(q/'go-src/tools'/n).read_bytes(),n
    for n in m.NEW:assert sha(r/'tools'/n)==sha(q/'go-src/tools'/n),n
    # The existing 1040 artwork rows retain their exact metadata and bytes.
    manifest=read(r/'artwork/manifest.json')
    assert len(manifest['files'])==1066;art=read(r/'artwork/openkb-hd-preservation-r1.json');assert art['prior_files']==1040 and art['added_files']==26
    previous=dict(manifest);previous['files']=manifest['files'][:1040];previous['additions']=manifest['additions'][:-1];assert hashlib.sha256((json.dumps(previous,ensure_ascii=False,indent=2)+'\n').encode()).hexdigest()==art['prior_manifest_sha256']
    verified=read(r/'preserved/openkb-hd-artwork-verification-r1.json');assert verified['status']=='PASS-independent-artwork-archive'and verified['files']==1066 and verified['manifest_sha256']==sha(r/'artwork/manifest.json')
    proof=read(q/'art-probe-r1/receipt.json');assert proof['status']=='passed-eight-openkb-art-cache'and proof['immutable']and proof['unknown_and_missing_fallback']and proof['catalog_mismatch_fallback']
    raw_cache={};entries=read(q/'ui-assets/unit-art.json')['rows'];by_id={v['id']:v for v in art['rows']}
    for entry,row in zip(entries,proof['rows']):
        assert entry['id']==row['id'];native=r/'artwork'/by_id[entry['id']]['reference'];master=r/'artwork'/by_id[entry['id']]['master'];assert sha(master)==by_id[entry['id']]['master_sha256']and sha(native)==by_id[entry['id']]['reference_sha256'];im=Image.open(master);assert im.mode=='RGBA'and im.getchannel('A').getextrema()==(0,255)
        # Rebuild the normalized source from its full permanent master.
        im=im.crop(im.getchannel('A').getbbox());im.thumbnail((472,472),Image.Resampling.LANCZOS);expected=Image.new('RGBA',(512,512));expected.alpha_composite(im,((512-im.width)//2,(512-im.height)//2));actual=Image.open(q/'ui-assets'/entry['file']).convert('RGBA');assert expected.tobytes()==actual.tobytes()and sha(q/'ui-assets'/entry['file'])==entry['sha256']
        raw=(q/'art-probe-r1'/row['raw']).read_bytes();assert len(raw)==512*512*4 and hashlib.sha256(raw).hexdigest()==row['sha256'];raw_cache[entry['id']]=(raw,512,512)
    def source(id):
        if id not in raw_cache:
            assert id.startswith('native:');kind=int(id.split(':')[1]);raw=h.stored(r,'recruit-icons-r1',f'/recruit-icons-r1/asset-test-r2/kind{kind:02d}.rgba');assert len(raw)==264*300*4;raw_cache[id]=(raw,264,300)
        return raw_cache[id]
    def rebuild(im,stamp,background):
        raw,w,hh=source(stamp['id']);assert stamp['source']==[w,hh]and hashlib.sha256(raw).hexdigest()==stamp['rgba_sha256'];alpha=Image.frombytes('RGBA',(w,hh),raw).getchannel('A');box=alpha.getbbox();area=stamp['area'];dw,dh=area[2]-area[0],area[3]-area[1];bw,bh=box[2]-box[0],box[3]-box[1]
        if dw*bh>dh*bw:dw=dh*bw//bh
        else:dh=dw*bh//bw
        x0,y0=area[0]+(area[2]-area[0]-dw)//2,area[1]+(area[3]-area[1]-dh)//2;assert stamp['destination']==[x0,y0,x0+dw,y0+dh]
        pixels=bytearray(dw*dh*4)
        for y in range(dh):
            sy=box[1]+y*bh//dh
            for x in range(dw):
                sx=box[0]+x*bw//dw
                if stamp['mirror']:sx=box[2]-1-x*bw//dw
                at=(sy*w+sx)*4;p=raw[at:at+4];a=p[3];offset=(y*dw+x)*4;pixels[offset:offset+4]=bytes([p[k]+(background[k]*(255-a)+127)//255 for k in range(3)]+[255])
        assert im.crop((x0,y0,x0+dw,y0+dh)).tobytes()==bytes(pixels),(stamp['id'],stamp['destination'])
    probe=Image.open(q/'art-probe-r1/drawn.png').convert('RGBA');assert hashlib.sha256(probe.tobytes()).hexdigest()==proof['canvas_rgba_sha256']
    for stamp in proof['stamps']:rebuild(probe,stamp,(20,56,41))
    gui=read(q/'gui-r1/receipt.json');assert gui['status']=='passed-actual-openkb-hd-ui'and gui['controlled_initial_armies']and gui['controlled_battle_entry']and not gui['natural_acquisition'];assert gui['cold']['world']==gui['saved']['world']and gui['cold']['pair_token']==gui['saved']['pair_token'];seen=set();stamps=0;frames=[]
    for frame in gui['screens']:
        folder=q/'gui-r1'/frame['phase'];meta=read(folder/frame['metadata']);im=Image.open(folder/frame['screen']).convert('RGBA');digest=hashlib.sha256(im.tobytes()).hexdigest();assert digest==meta['canvas_sha256']==meta['presented_sha256'];assert meta['unit_art']['loaded']==33 and not meta['unit_art']['failures']
        view=meta['unit_art']['view'];assert view in ['review','dismiss','battle'];background=(20,57,42)if view=='battle'else(20,56,41)
        for stamp in meta['unit_art']['stamps']:
            assert inside(stamp['destination'],stamp['area'])and inside(stamp['area'],[0,0,1920,1200]);assert not any(overlap(stamp['area'],t['Rect'])for t in meta['text_fields']if t['Text']),('image/text overlap',stamp)
            bg=background
            if view=='dismiss':
                selected=meta['dismiss_selected'];x,y=60+selected//3*920,245+selected%3*250
                if stamp['area']==[x+16,y+66,x+200,y+210]:bg=(104,47,38)
            rebuild(im,stamp,bg);seen.add(stamp['id']);stamps+=1
        for t in meta['text_fields']:assert inside(t['Ink'],t['Rect'])or t['Ink']==[0,0,0,0]
        frames.append(dict(phase=frame['phase'],screen=frame['screen'],rgba_sha256=digest,stamps=len(meta['unit_art']['stamps'])))
    wanted=set(by_id);assert wanted.issubset(seen);assert gui['armies'][0]['native_rows_hex']==gui['armies'][1]['native_rows_hex']==gui['opened']['native_rows_hex']==gui['cold']['native_rows_hex']
    value=dict(status='passed-openkb-hd-presentation',dependencies=deps,source_tools={n:sha(r/'tools'/n)for n in m.NEW},binaries={n:sha(q/n)for n in ['openkb-ui','openkb-ui-fixture','openkb-probe']},artwork_files=1066,artwork_manifest_sha256=sha(r/'artwork/manifest.json'),unit_ids=sorted(wanted),verified_x11_frames=frames,independently_rebuilt_stamps=stamps,gui=gui,formal_changed=False,production_promoted=False,limits=['Controlled starting armies; one controlled native encounter entry for the battle view. No natural openKB acquisition or complete world-integration claim.','Eight single static HD sprites, no new attack animation or rule changes.','Formal owned-army sidecar guard remains enabled.'])
    with a.out.open('x')as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
if __name__=='__main__':main()
