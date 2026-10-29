#!/usr/bin/env python3
"""Decode saved states through the independent std-only reader, then check RAM."""
import argparse,gzip,hashlib,json,pathlib,struct,subprocess,tempfile
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser()
 for n in ['project','reader','out']:p.add_argument('--'+n,type=pathlib.Path,required=True)
 a=p.parse_args();assert not a.out.exists();q=a.project/'workplace/probe-20261023/graphics-first/battle-r1/ai-formation-r1/original-r2';count=0
 with tempfile.TemporaryDirectory()as tmp:
  decoded=pathlib.Path(tmp)/'decoded';subprocess.run([str(a.reader),'-calls',str(q),'-out',str(decoded)],check=True);index=json.loads((decoded/'index.json').read_text());assert len(index)==108
  for f in sorted(q.glob('*/*/final.state')):
   key=str(f.relative_to(q));entry=index[key];raw=gzip.decompress((decoded/(entry['memory_sha256']+'.ram.gz')).read_bytes());assert hashlib.sha256(raw).hexdigest()==entry['memory_sha256'];t=json.loads((f.parent/'trace.json').read_text());units=list(struct.unpack_from('<24H',raw,0x1e88*16+0x56e8));assert units==t['AfterUnits'];assert entry['steps']==t['EndStep'];count+=1
  assert count==36
 result=dict(status='passed-independent-saved-RAM',decoded_states=108,final_unit_arrays_verified=36,reader_sha256=sha(a.reader),reader_source='tools/inspect-formation-states.go plus fixed 923-core state-schema types',method='std-only gob decoding; no Machine, CPU execution or game helper calls',tool_sha256=sha(pathlib.Path(__file__)))
 a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
