#!/usr/bin/env python3
"""規則冷讀的命令列拒絕案例。Docker；只掛 native 與本工具。"""
import hashlib,json,os,shutil,subprocess
from pathlib import Path
def main():
    assert Path('/.dockerenv').exists() and os.getuid()==1000
    r=Path('/native'); out=r/'cli-check'; out.mkdir(); results=[]
    env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_RENDER_DRIVER='software',SDL_AUDIODRIVER='dummy')
    for label,slot,option,mutation in [('battle-override','battle','native',None),('journey-override','journey','native',None),('unknown-option','battle','other',None),('unknown-marker','battle','auto','mode'),('hash-mismatch','battle','auto','hash'),('marker-symlink','battle','auto','link')]:
        d=out/label;d.mkdir(); name=slot+'.chk'
        source=r/'gui/journey-store' if slot=='journey' else r/'fixture/tactics'
        for p in source.glob(name+'*'):shutil.copy2(p,d/p.name)
        marker=d/(name+'.rules.json')
        if mutation in ['mode','hash']:
            doc=json.loads(marker.read_text());doc['rules' if mutation=='mode' else 'save_sha256']='other' if mutation=='mode' else '0'*64;marker.write_text(json.dumps(doc))
        if mutation=='link':marker.rename(d/'outside.json');marker.symlink_to('outside.json')
        before={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in d.iterdir()if p.is_file()}
        cmd=[str(r/'8sword-remake'),'--'+slot,'--assets',str(r/'pack'),'--save-dir',str(d),'--continue','--battle-rules',option,'--mute']
        run=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=15);assert run.returncode==1,(label,run.returncode,run.stderr)
        expected={'battle-override':'冷讀戰鬥的規則已固定','journey-override':'冷讀戰鬥的規則已固定','unknown-option':'規則模式無效','unknown-marker':'規則模式無效','hash-mismatch':'規則標記與進度不符','marker-symlink':'規則標記形態無效'}[label];assert expected in run.stderr,(label,run.stderr)
        assert all(hashlib.sha256((d/n).read_bytes()).hexdigest()==v for n,v in before.items())
        if mutation=='link':marker.unlink()
        results.append(dict(case=label,command=cmd,exit=run.returncode,stderr=run.stderr,files_before_sha256=before,unchanged=True))
    (out/'receipt.json').write_text(json.dumps(dict(status='passed-rust-rules-cli',cases=results),ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
