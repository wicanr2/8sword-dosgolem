#!/usr/bin/env python3
"""030 DRAFT: prepare bounded original controls for approved tactics."""
import argparse,hashlib,json,os,pathlib
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();r=a.project;assert os.getuid()==1000 and not a.out.exists();a.out.mkdir();helpers=a.out/'helpers';battles=a.out/'battles';helpers.mkdir();battles.mkdir();(helpers/'main.go').write_bytes((r/'tools/probe-tactics-helpers.go').read_bytes())
 s=(r/'tools/research-ai-policy.go').read_text();s=s.replace(' Route string\n',' Route string\n Formation, Pressure bool\n',1);needle='  encoded:=uint16(c.Amount/hp+1)';assert s.count(needle)==1
 s=s.replace(needle,'''  if v.Pressure && source.Kind==3 && v.SourceSlot<3 && v.Friendly[v.FriendlySlots[v.SourceSlot]].Count>0 {c.Amount=uint16(uint32(c.Amount)*75/100)}
  if v.Formation && slot<3 && u.Kind==1 {
   support:=false;for i:=uint16(0);i<3;i++ {if i!=slot && v.Friendly[v.FriendlySlots[i]].Count>0 {support=true}}
   if support {c.Amount=uint16(uint32(c.Amount)*80/100)}
  }
'''+needle);(battles/'policy.go').write_text(s)
 s=(r/'tools/probe-ai-formation.go').read_text();start=s.index('var formationCases=');end=s.index('\nfunc must',start)
 s=s[:start]+'''var formationCases=[]formationCase{
 {"archer-front",0,3,-1,[6]uint16{0,1,5,5,5,5},[3]uint16{20,22,0},[3]uint16{1,21,0}},
 {"archer-rear-target",0,3,-1,[6]uint16{0,2,5,1,5,5},[3]uint16{20,22,100},[3]uint16{1,21,21}},
 {"archer-open-lane",0,3,-1,[6]uint16{5,0,5,1,5,5},[3]uint16{20,22,0},[3]uint16{1,21,0}},
 {"archer-back",3,3,-1,[6]uint16{0,1,5,5,5,5},[3]uint16{20,22,0},[3]uint16{1,21,0}},
 {"bird-front",0,24,-1,[6]uint16{0,1,5,5,5,5},[3]uint16{20,22,0},[3]uint16{1,21,0}},
 {"melee-locked",0,6,-1,[6]uint16{0,1,5,5,5,5},[3]uint16{20,22,0},[3]uint16{1,21,0}},
 {"special0",3,12,0,[6]uint16{0,1,5,5,5,5},[3]uint16{31,69,0},[3]uint16{1,21,0}},
}'''+s[end:]
 replacements=[('[]string{"native","formation"}','[]string{"native","formation","tactics"}'),('view.Formation=rules=="formation"&&mode=="aware"','view.Formation=rules!="native";view.Pressure=rules=="tactics"&&mode=="aware"'),('actualView.Formation=rules=="formation"','actualView.Formation=rules!="native";actualView.Pressure=rules=="tactics"'),('before:=c.R[cpu.AX];if rules=="formation"&&eligible{c.R[cpu.AX]=uint16(uint32(before)*80/100)}','before:=c.R[cpu.AX];pressure:=sc.Kind==3&&sc.Source<3&&words(m,ds,0x56ea+mapping[sc.Source]*4,1)[0]>0;if rules=="tactics"&&pressure{c.R[cpu.AX]=uint16(uint32(c.R[cpu.AX])*75/100)};if rules!="native"&&eligible{c.R[cpu.AX]=uint16(uint32(c.R[cpu.AX])*80/100)}'),('"InsideExecutor":executing','"InsideExecutor":executing,"PressureEligible":pressure')]
 for old,new in replacements:assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new)
 (battles/'main.go').write_text(s);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();(a.out/'preparation.json').write_text(json.dumps(dict(schema=1,sources={n:sha(r/'tools'/n)for n in ['research-ai-policy.go','probe-ai-formation.go','probe-tactics-helpers.go','prepare-tactics-controls.py']},generated={str(p.relative_to(a.out)):sha(p)for p in a.out.rglob('*.go')}),indent=2)+'\n');print('prepared 48 helper and 63 full-executor controls')
if __name__=='__main__':main()
