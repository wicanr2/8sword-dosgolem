#!/usr/bin/env python3
"""Rust 已批准規則的準備、證據與保存入口；只在 Docker 執行。"""
import argparse, gzip, hashlib, importlib.util, json, os, shutil, sys
from pathlib import Path
sys.dont_write_bytecode = True
BATCH = 'rust-rules-r1'
REL = 'workplace/probe-20261023/graphics-first/battle-r1/' + BATCH
def module(r, n):
    spec = importlib.util.spec_from_file_location(n, r / 'tools' / n)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('action', choices=['prepare','audit','images','freeze','archive','verify','restore'])
    for n in ['project','work','out','archive']: ap.add_argument('--'+n, type=Path)
    a = ap.parse_args(); assert Path('/.dockerenv').exists() and os.getuid()==1000
    r = a.project; q = a.work or (r / REL if r else None)
    if a.action=='verify':
        d=json.loads((a.archive/(BATCH+'.json')).read_text())
        for f in d['files']:
            obj=d['objects'][f['sha256']]; p=a.archive/BATCH/obj['file']; assert sha(p)==obj['stored_sha256']
            raw=gzip.decompress(p.read_bytes()); assert len(raw)==f['bytes'] and hashlib.sha256(raw).hexdigest()==f['sha256']
        a.out.write_text(json.dumps(dict(status='passed-rust-rules-detached',files=len(d['files']),objects=len(d['objects'])))+'\n'); return
    if a.action=='archive':
        m=module(r,'rust-world-exits.py'); m.BATCH=BATCH; m.REL=REL; m.main(); return
    if a.action=='restore':
        h=module(r,'prepare-owned-army-ui.py')
        for f in json.loads((r/'preserved'/(BATCH+'.json')).read_text())['files']:
            rel=Path(f['path']).relative_to(REL)
            if str(rel)=='native/8sword-remake' or str(rel).startswith('native/pack/'):
                p=q/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(h.stored(r,BATCH,f['path'])); p.chmod(f['mode'])
        return
    if a.action=='freeze':
        shutil.copytree(r/'internal/remake-rust',q/'rust-source'); (q/'tools').mkdir()
        for n in ['rust-rules.py','rust-rules-gui.py','rust-rules-cli.py','rust-ai-gui.py','rust-ai-reference-main.txt','rust-native-player.sh']:
            shutil.copy2(r/'tools'/n,q/'tools'/n)
        return
    if a.action in ['audit','images']:
        from PIL import Image, ImageDraw, ImageFont
        import io, struct
        h=module(r,'prepare-owned-army-ui.py'); gui=json.loads((q/'native/gui/receipt.json').read_text())
        assert gui['status']=='passed-rust-rules-gui' and len(gui['runs'])==7 and gui['binary_sha256']==sha(q/'native/8sword-remake')
        captures=[]
        for run in gui['runs']:
            assert run['exit']==0
            for c in run['captures']:
                folder=q/'native/gui'/run['name']; n=c['number']; center=folder/f'frame-{n:03}.ppm'; full=folder/f'shell-frame-{n:03}.ppm'
                assert center.read_bytes()==center.with_name(f'readback-{n:03}.ppm').read_bytes()
                assert full.read_bytes()==full.with_name(f'shell-readback-{n:03}.ppm').read_bytes()
                assert Image.open(full).convert('RGB').crop((512,0,2432,1320)).tobytes()==Image.open(center).convert('RGB').tobytes()
                captures.append(dict(run=run['name'],**c,central_sha256=sha(center),full_sha256=sha(full)))
        assert len(captures)==20
        if a.action=='images':
            idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes())); font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),28,index=3)
            canvas=Image.new('RGB',(1920,980),(8,36,23)); draw=ImageDraw.Draw(canvas); chosen=[]
            for i,(run,label,title) in enumerate([('native','first-hit','原版規則：民兵100→84'),('formation','first-hit','結陣試作：民兵100→88'),('journey','world-tactics','正常旅程：工具列選擇戰術規則'),('journey-cold','cold-formation','戰中冷讀：結陣固定，隸書保持')]):
                c=next(c for c in captures if c['run']==run and c['label']==label); im=Image.open(q/'native/gui'/run/f'shell-frame-{c["number"]:03}.ppm'); x=i%2*960; y=i//2*490; draw.text((x+8,y+8),title,font=font,fill=(239,216,155)); canvas.paste(im.resize((960,430),Image.Resampling.LANCZOS),(x,y+50)); chosen.append(c)
            canvas.save(a.out); a.out.with_suffix('.json').write_text(json.dumps(dict(image_sha256=sha(a.out),binary_sha256=gui['binary_sha256'],sources=chosen,scope=gui['scope']),ensure_ascii=False,indent=2)+'\n'); return
        assert '193 passed; 0 failed' in(q/'native/tests.log').read_text()
        for name,count in [('rules-reference.tsv',5184),('rules-ai-reference.tsv',1224),('sha256-reference.tsv',264)]:
            raw=(q/'reference'/name).read_bytes(); assert raw==(r/'internal/remake-rust'/name).read_bytes(); assert len([l for l in raw.splitlines() if not l.startswith(b'#')])==count
        previous=json.loads((r/'preserved/rust-ai-r1.json').read_text()); old={Path(f['path']).name:f['sha256'] for f in previous['files'] if '/native/pack/' in f['path']}
        assert len(old)==159 and all(sha(q/'native/pack'/n)==v for n,v in old.items() if n!='poster-font.bin')
        def glyphs(b): return {chr(struct.unpack_from('<I',b,12+i*4100)[0]):b[16+i*4100:12+(i+1)*4100] for i in range(struct.unpack_from('<I',b,8)[0])}
        before=glyphs(h.stored(r,'rust-ai-r1','native/pack/poster-font.bin')); after=glyphs((q/'native/pack/poster-font.bin').read_bytes()); assert len(before)==22 and len(after)==34 and all(after[k]==v for k,v in before.items())
        for folder,name in [('tactics-store','battle.chk'),('journey-store','journey.chk'),('journey-cold-store','journey.chk')]:
            d=q/'native/gui'/folder; marker=json.loads((d/(name+'.rules.json')).read_text()); assert marker['save_sha256']==sha(d/name) and marker['save_bytes']==(d/name).stat().st_size
        cli=json.loads((q/'native/cli-check/receipt.json').read_text()); assert cli['status']=='passed-rust-rules-cli' and len(cli['cases'])==6
        crate={str(p.relative_to(r/'internal/remake-rust')):sha(p) for p in(r/'internal/remake-rust').rglob('*') if p.is_file()}; assert all(sha(q/'rust-source'/n)==v for n,v in crate.items())
        a.out.write_text(json.dumps(dict(status='passed-rust-rules-audit',tests=193,go_rule_vectors=5184,go_ai_views=1224,legacy_ai_views=408,sha256_python_lengths=264,spell_seed_range=[1,64],runtime_files=160,unchanged_media=158,old_poster_glyphs_unchanged=22,new_poster_glyphs=12,crate=crate,gui=gui,cli=cli,captures=captures,execution=json.loads((q/'execution.json').read_text()),limits=['Approved Go rules, not original default DOS behavior.','Rear archer GUI samples formation; front archer pressure separately verified in both-side core tests.','True v16 natural encounter; controlled battle troops and seed are explicit.','Two-file save/marker transaction is not group atomic; mismatched existing marker rejects.','Raw native formats remain v16/8SBCHK01; file load is required to restore mode.','No new full-HD matrix, natural completion, cross-platform release, or human listening claim.']),ensure_ascii=False,indent=2)+'\n'); return
    m=module(r,'rust-ai.py'); m.BATCH=BATCH; m.REL=REL; m.main()
    # Reuse the frozen policy exporter; extend every view to all approved modes.
    p=q/'reference-go.go'; s=p.read_text()
    s=s.replace('func emit(v battleAIView,out *os.File) {','func emit(v battleAIView,out *os.File) {\n for mode:=0;mode<3;mode++ { v.Formation=mode>0;v.ArcherPressure=mode==2')
    s=s.replace('parts:=[]string{};', 'nums=append(nums,uint16(mode));parts:=[]string{};')
    s=s.replace('\n}\nfunc main(){','\n}\n}\nfunc main(){')
    s=s.replace('/out/reference/ai-reference.tsv','/out/reference/rules-ai-reference.tsv')
    s=s.replace('8+384+2*len(extras)', '(8+384+2*len(extras))*3')
    s=s.replace('func main(){','func main(){\n emitRuleVectors()')
    s+='''
func emitRuleVectors(){
 f,e:=os.Create("/out/reference/rules-reference.tsv");if e!=nil{panic(e)};defer f.Close()
 fmt.Fprintln(f,"# exact approved Go eligibility / u16 damage scaling; no DOS oracle")
 for mode:=0;mode<3;mode++{for ss:=0;ss<6;ss++{for ts:=0;ts<6;ts++{for _,sk:=range []uint16{3,24}{for _,tk:=range []uint16{1,3}{for state:=0;state<4;state++{for _,amount:=range []uint16{0,19,65535}{
  front:=[3]uint16{};if state&1!=0{front[ts%3]=20};if state&2!=0{front[(ts+1)%3]=1};sc,tc:=uint16(20),uint16(20);if state==0{sc=0;tc=0}
  n:=amount;if mode==2&&archerPressureEligible(ss,sk,sc,front){n=archerPressureDamage(n)};if mode>0&&formationEligible(ts,tk,tc,front){n=formationDamage(n)}
  fmt.Fprintf(f,"%d\\t%d\\t%d\\t%d\\t%d\\t%d\\t%d\\t%d\\t%d\\t%d\\t%d\\t%d\\n",mode,ss,sk,sc,ts,tk,tc,front[0],front[1],front[2],amount,n)
 }}}}}}}
}
'''
    p.write_text(s)
    # Python hashlib is an independent boundary-length check for the std-only digest.
    lengths=list(range(257))+[511,512,513,2987,4096,16384,131072]
    (q/'reference/sha256-reference.tsv').write_text(''.join(f'{n}\t{hashlib.sha256(bytes(i%251 for i in range(n))).hexdigest()}\n' for n in lengths))
    from PIL import Image, ImageDraw, ImageFont
    import io, struct
    h=module(r,'prepare-owned-army-ui.py'); idx=json.loads(gzip.decompress((r/'preserved/catalog.json.gz').read_bytes()))
    font=ImageFont.truetype(io.BytesIO(gzip.decompress((r/'preserved'/idx['objects'][h.FONT_SHA['noto']]['path']).read_bytes())),56,index=3)
    p=q/'native/pack/poster-font.bin'; raw=p.read_bytes(); glyphs={chr(struct.unpack_from('<I',raw,12+i*4100)[0]):raw[16+i*4100:12+(i+1)*4100] for i in range(struct.unpack_from('<I',raw,8)[0])}; old=dict(glyphs)
    for ch in '規則結陣試作戰術本場固定':
        if ch not in glyphs:
            im=Image.new('L',(64,64)); ImageDraw.Draw(im).text((32,32),ch,font=font,fill=255,anchor='mm'); glyphs[ch]=im.tobytes()
    raw=bytearray(b'8SGLYP01'+struct.pack('<I',len(glyphs)))
    for ch,ink in sorted(glyphs.items()): raw+=struct.pack('<I',ord(ch))+ink
    raw+=struct.pack('<Q',module(r,'rust-native-player.py').fnv(raw)); p.write_bytes(raw)
    assert all(glyphs[c]==v for c,v in old.items())
    (q/'evidence/rules-assets.json').write_text(json.dumps(dict(old_glyphs=len(old),total=len(glyphs),preserved=True,font_source=h.FONT_SHA['noto'],font_index=3),indent=2)+'\n')
if __name__=='__main__': main()
