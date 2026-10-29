"""Isolated source-scene observation for normal F4 map-spell samples."""
import argparse,hashlib,json,pathlib,shutil
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser()
 for n in ['project','source','out']:p.add_argument('--'+n,type=pathlib.Path,required=True)
 a=p.parse_args();assert not a.out.exists();a.out.mkdir();shutil.copytree(a.source,a.out/'src');r=a.out/'src';before={str(f.relative_to(r)):sha(f)for f in r.rglob('*')if f.is_file()};p=r/'internal/eightsword/source_scene.go';s=p.read_text();needle='p.cachedScene = state';assert s.count(needle)==1;p.write_text(s.replace(needle,needle+'\n researchCueScene=state',1));p=r/'internal/eightsword/research_cues_test.go';p.write_text((a.project/'tools/research-remaining-spells_test.go').read_text().removeprefix('//go:build ignore\n'));after={str(f.relative_to(r)):sha(f)for f in r.rglob('*')if f.is_file()};(a.out/'preparation.json').write_text(json.dumps(dict(base_inputs=before,diagnostic_inputs=after,changed=[n for n,h in after.items()if before.get(n)!=h]),indent=2)+'\n')
if __name__=='__main__':main()
