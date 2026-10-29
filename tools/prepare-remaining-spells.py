"""Freeze all ten remaining cue inputs from the current quake production baseline."""
import argparse,hashlib,json,os,pathlib,shutil
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();r=a.project;assert os.getuid()==1000 and not a.out.exists();old=json.loads((r/'preserved/player-quake-audit-r1.json').read_text());player=r/'workplace/player'
 for n,h in old['programs'].items():assert sha(player/n)==h
 names=set(old['source_inputs'])|{'internal/eightsword/spell_cues.go','internal/eightsword/spell_cues_draw.go','internal/eightsword/spell_cues_test.go'};a.out.mkdir();inputs={}
 for n in sorted(names):
  f=r/n;assert f.stat().st_uid==1000;target=a.out/'src'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target);inputs[n]=sha(f)
 assert len(inputs)==193;shutil.copyfile(player/'runtime.json',a.out/'runtime.json');(a.out/'preparation.json').write_text(json.dumps(dict(source_inputs=inputs,source_count=193,core_files=923,previous_programs=old['programs'],changed=[n for n,h in inputs.items()if old['source_inputs'].get(n)!=h]),indent=2)+'\n');print('Frozen 193 source inputs')
if __name__=='__main__':main()
