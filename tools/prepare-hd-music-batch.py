#!/usr/bin/env python3
"""008候選匯入：保留既有344素材，加入九首待批准音樂供隔離測試。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ['base','batch','audit','out']:ap.add_argument('--'+key,type=Path,required=True)
    a=ap.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid()==1000
    assert 'candidate' in a.out.name and not a.out.exists()
    assert a.out.parent.stat().st_uid==1000
    before={f.name:sha(f) for f in a.base.iterdir() if f.is_file()}
    assert len(before)==344 and all(f.is_file() and not f.is_symlink() for f in a.base.iterdir())
    manifest=json.loads((a.base/'music.json').read_text())
    assert manifest['schema']==1 and len(manifest['cues'])==1
    approved=manifest['cues'][0]
    assert approved['id']==1 and approved['sha256']=='4012e14dc7d03c017a532c5c56655794a03a62f395972c026273a2ec99fcbc91'
    assert sha(a.base/approved['file'])==approved['sha256']
    candidate=json.loads((a.batch/'candidates.json').read_text())
    audit=json.loads(a.audit.read_text())
    assert audit['status']=='PASS-technical-nine-music-candidates' and not audit['production']
    assert audit['candidate_manifest_sha256']==sha(a.batch/'candidates.json')
    assert {v['cue'] for v in candidate['cues']}==set(range(2,11))
    assert len(candidate['cues'])==9 and all(not v['approved'] for v in candidate['cues'])
    for cue in candidate['cues']:
        assert cue['loop_file']==Path(cue['loop_file']).name
        assert sha(a.batch/cue['loop_file'])==cue['loop_sha256']
    shutil.copytree(a.base,a.out)
    for cue in candidate['cues']:
        name='music-'+cue['score'][:4].lower()+'-batch-r1.ogg'
        assert not (a.out/name).exists()
        shutil.copyfile(a.batch/cue['loop_file'],a.out/name)
        manifest['cues'].append(dict(id=cue['cue'],title=cue['title'],score_sha256=cue['score_sha256'],
            bank_sha256=cue['bank_sha256'],file=name,sha256=cue['loop_sha256'],
            sample_rate=48000,channels=2,frames=cue['frames'],loop_start_frame=0,
            loop_end_frame=cue['frames'],rights='original-derived-local'))
    assert sum(v['frames']*4 for v in manifest['cues'])<256*2**20
    (a.out/'music.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    preserved={name:digest for name,digest in before.items() if name!='music.json'}
    assert all(sha(a.out/name)==digest for name,digest in preserved.items())
    record=dict(schema=1,production=False,approved=False,status='candidate-only-awaiting-music-approval',
        base_files=before,preserved_files=preserved,changed_existing_files=['music.json'],
        candidate_manifest_sha256=sha(a.batch/'candidates.json'),technical_audit_sha256=sha(a.audit),
        catalog_sha256=sha(a.out/'music.json'),cues=10,decoded_int16_bytes=sum(v['frames']*4 for v in manifest['cues']),
        importer_sha256=sha(Path(__file__)),rights='original-derived-local; no public or Git distribution')
    (a.out/'music-batch-import.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    assert all(f.stat().st_uid==1000 for f in a.out.iterdir()) and len(list(a.out.iterdir()))==354
    print(json.dumps(dict(status=record['status'],files=354,preserved=len(preserved),
                         cues=10,decoded_bytes=record['decoded_int16_bytes'])))


if __name__=='__main__':main()
