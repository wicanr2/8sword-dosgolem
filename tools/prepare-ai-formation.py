#!/usr/bin/env python3
"""030 DRAFT: disposable pure policy with the already approved formation rule."""
import argparse,hashlib,json,os,pathlib
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();assert os.getuid()==1000 and not a.out.exists();a.out.mkdir();r=a.project;s=(r/'tools/research-ai-policy.go').read_text()
 s=s.replace(' Route string\n',' Route string\n Formation bool `json:",omitempty"`\n',1)
 needle='  encoded:=uint16(c.Amount/hp+1)';assert s.count(needle)==1
 s=s.replace(needle,'''  if v.Formation && slot<3 && u.Kind==1 {
   support:=false
   for i:=uint16(0);i<3;i++ {if i!=slot && v.Friendly[v.FriendlySlots[i]].Count>0 {support=true}}
   if support {c.Amount=uint16(uint32(c.Amount)*80/100)}
  }
'''+needle)
 (a.out/'policy.go').write_text(s);(a.out/'probe.go').write_bytes((r/'tools/probe-ai-formation.go').read_bytes())
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();(a.out/'preparation.json').write_text(json.dumps(dict(schema=1,status='DRAFT',sources={n:sha(r/'tools'/n)for n in ['research-ai-policy.go','probe-ai-formation.go','prepare-ai-formation.py']},generated={n:sha(a.out/n)for n in ['policy.go','probe.go']}),indent=2)+'\n');print('isolated formation-aware policy and original probe prepared')
if __name__=='__main__':main()
