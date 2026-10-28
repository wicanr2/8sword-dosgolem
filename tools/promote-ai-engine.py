#!/usr/bin/env python3
"""030: promote only an independently accepted seven-program AI candidate."""
import argparse,hashlib,json,os,pathlib
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser()
 for name in ['project','player','audit','receipt']:p.add_argument('--'+name,type=pathlib.Path,required=True)
 a=p.parse_args();assert os.getuid()==a.player.stat().st_uid==1000 and not a.receipt.exists();d=json.loads(a.audit.read_text());assert d['status']=='PASS-scoped-030-optional-target-AI' and d['source_input_count']==181 and d['core_files']==923 and d['asset_files']==525
 assert pathlib.Path(d['candidate']).name==d['candidate'];candidate=a.player/d['candidate'];assert sha(candidate/'build-inputs.sha256')==d['build_inputs_sha256'] and sha(candidate/'runtime.json')==d['runtime_sha256']
 for name,digest in d['programs'].items():assert pathlib.Path(name).name==name and sha(candidate/name)==digest and sha(a.player/name)==d['previous_programs'][name] and (a.player/name).stat().st_uid==(candidate/name).stat().st_uid==1000
 for name,digest in d['source_inputs'].items():assert sha(a.project/name)==sha(candidate/'src'/name)==digest
 for name,digest in d['asset_hashes'].items():assert sha(a.player/d['assets']/name)==digest
 staged={}
 try:
  for name in d['programs']:
   tmp=a.player/('.ai-promote-'+name+'.tmp');assert not tmp.exists();os.link(candidate/name,tmp);staged[name]=tmp
  runtime=json.loads((candidate/'runtime.json').read_text());runtime.update(production=True,application_spec='docs/spec/030-battle-expansion-proposal.md',application_source_inputs=181,battle_ai_modes=['native','target'],battle_ai_default='native')
  metadata={n:(candidate/n).read_bytes() for n in ['build-inputs.sha256','build-source-checks.log','build-go-version.txt']};metadata['runtime.json']=(json.dumps(runtime,indent=2)+'\n').encode();metadata['build-outputs.sha256']=''.join(f'{digest}  /out/{name}\n' for name,digest in d['programs'].items()).encode()
  for name,data in metadata.items():
   tmp=a.player/('.ai-promote-'+name+'.tmp');assert not tmp.exists();tmp.write_bytes(data);staged[name]=tmp
  for name,tmp in staged.items():os.replace(tmp,a.player/name)
 finally:
  for tmp in staged.values():
   if tmp.exists():tmp.unlink()
 for name,digest in d['programs'].items():assert sha(a.player/name)==digest
 result=dict(schema=1,status='promoted-scoped-030-optional-target-AI',candidate=d['candidate'],programs=d['programs'],previous_programs=d['previous_programs'],source_inputs=181,core_files=923,assets=d['assets'],asset_files=525,audit_sha256=sha(a.audit),tool_sha256=sha(pathlib.Path(__file__)),default='native',optional='target')
 a.receipt.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],programs=7,default='native')))
if __name__=='__main__':main()
