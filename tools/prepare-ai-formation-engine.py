#!/usr/bin/env python3
"""030 READY: freeze formation-aware AI; keep all assets and the 923-file core."""
import argparse,hashlib,json,os,pathlib,shutil
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser()
 for n in ['project','player','out']:p.add_argument('--'+n,type=pathlib.Path,required=True)
 a=p.parse_args();r=a.project;old=json.loads((r/'preserved/formation-engine-audit-r1.json').read_text());assert os.getuid()==a.player.stat().st_uid==1000 and not a.out.exists()
 for n,h in old['programs'].items():assert sha(a.player/n)==h
 for n,h in old['asset_hashes'].items():assert sha(a.player/'assets-painted-r67'/n)==h
 core=json.loads((a.player/'runtime.json').read_text());assert core['total_inputs']==len(core['files'])==923
 for n,h in core['files'].items():assert sha(a.player/'runtime-render-r1/src'/n)==h
 a.out.mkdir();digests={}
 for n in sorted(old['source_inputs']):
  f=r/n;assert f.stat().st_uid==1000;out=a.out/'src'/n;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,out);digests[n]=sha(f)
 assert len(digests)==184
 changed={n for n in digests if digests[n]!=old['source_inputs'][n]};assert changed=={'internal/eightsword/battle_ai.go','internal/eightsword/battle_ai_policy.go','internal/eightsword/battle_ai_policy_test.go','internal/eightsword/battle_ai_runtime_test.go','internal/eightsword/battle_rules.go'},changed
 (a.out/'build-inputs.sha256').write_text(''.join(f'{h}  /project/{n}\n'for n,h in digests.items()));(a.out/'runtime.json').write_text(json.dumps(core,indent=2)+'\n');(a.out/'preparation.json').write_text(json.dumps(dict(source_inputs=digests,source_count=184,core_files=923,previous_programs=old['programs'],changed=sorted(changed)),indent=2)+'\n');print('frozen 184 inputs; assets r67 and core unchanged')
if __name__=='__main__':main()
