#!/usr/bin/env python3
"""030 READY: freeze an AI candidate using the existing verified 923-file core."""
import argparse,hashlib,json,os,pathlib,shutil
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--player',type=pathlib.Path,required=True);p.add_argument('--name',required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();r=a.project
 assert os.getuid()==1000 and a.player.stat().st_uid==1000 and a.out.parent.is_dir() and not a.out.exists();assert a.name.replace('-','').isalnum()
 candidate=a.player/a.name;assert not candidate.exists();old=r/'workplace/player';core=json.loads((old/'runtime.json').read_text());assert core['total_inputs']==923
 for name,digest in core['files'].items():assert sha(old/'runtime-render-r1/src'/name)==digest
 previous=json.loads((r/'preserved/completion-r65-audit.json').read_text())
 for name,digest in previous['programs'].items():assert sha(old/name)==digest
 files=[line.split(None,1)[1].removeprefix('/project/') for line in (old/'build-inputs.sha256').read_text().splitlines()]
 for name in ['battle_ai.go','battle_ai_policy.go','battle_ai_policy_test.go','battle_ai_runtime_test.go']:files.append('internal/eightsword/'+name)
 assert len(files)==len(set(files))==181
 candidate.mkdir();a.out.mkdir();digests={}
 for name in sorted(files):
  source=r/name;assert source.stat().st_uid==1000;target=candidate/'src'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);digests[name]=sha(source)
 (candidate/'build-inputs.sha256').write_text(''.join(f'{digest}  /project/{name}\n' for name,digest in digests.items()))
 (candidate/'runtime.json').write_bytes((old/'runtime.json').read_bytes())
 (a.out/'preparation.json').write_text(json.dumps(dict(schema=1,spec='030 READY',candidate=a.name,source_inputs=digests,source_count=181,core_files=923,core_metadata_sha256=sha(old/'runtime.json'),previous_programs=previous['programs'],assets=previous['asset_hashes']),indent=2)+'\n')
 print(json.dumps(dict(candidate=a.name,inputs=181,core=923)))
if __name__=='__main__':main()
