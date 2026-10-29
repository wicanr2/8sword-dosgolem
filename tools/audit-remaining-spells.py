"""Independent MZ/IDA byte audit and original ten-spell result checks."""
import argparse,hashlib,json,pathlib,struct
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();r=a.project;q=r/'workplace/probe-20261023/graphics-first/battle-r1/player-spells-r1/remaining-r1';assert not a.out.exists()
 pam=r/'workplace/intake-20261023/sources/game/8sword/PAM.AY';assert sha(pam)=='83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0';raw=pam.read_bytes();u=lambda at:struct.unpack_from('<H',raw,at)[0];header=u(8)*16;code=bytearray(raw[header:])
 for i in range(u(6)):
  off,seg=struct.unpack_from('<HH',raw,u(24)+i*4);at=seg*16+off;struct.pack_into('<H',code,at,(struct.unpack_from('<H',code,at)[0]+0x1000)&65535)
 ida=json.loads((q/'ida-r3/ida-remaining.json').read_text());assert ida['source_sha256']==sha(pam)and ida['tool']=='IDA 9.4';lines=0
 for f in ida['functions']:
  for row in f['lines']:
   b=bytes.fromhex(row['bytes']);at=row['original_file_offset']-header;assert code[at:at+len(b)]==b;lines+=1
 cases=[]
 for name,spell in [('freeze',4),('clone',6)]:
  d=json.loads((q/name/'receipt.json').read_text());assert d['state_equal'];c,v=d['runs'];assert c['completed']and v['completed']and c['charges'][spell]==v['charges'][spell]==1
  assert sha(q/name/'control/final.state')==sha(q/name/'observed/final.state');assert c['keys']==v['keys']and c['mutations']==v['mutations'];events=[e for e in v['events']if e['name']=='player-'+name];assert len(events)==(1 if name=='freeze'else 21)
  cases.append(dict(name=name,selector=spell,events=len(events),state_equal=True,final_sha256=v['state_sha256']))
 for spell in range(8):
  d=json.loads((q/f'original-map-r8/map-{spell}/receipt.json').read_text());assert d['started']and d['done']and d['spell']==spell;assert d['before'][:8]==[2]*8;expected=[2]*8;expected[spell]=1;assert d['after'][:8]==expected;assert d['events'][0]['arg']==spell;assert all(m['offset']==0x26aa or 0x2b28<=m['offset']<=0x2b36 for m in d['mutations'])
  cases.append(dict(name='map-'+str(spell),selector=spell,dispatch=True,returned=True,final_sha256=d['final_sha256']))
 result=dict(schema=1,status='passed-remaining-ten-spell-research',pam_sha256=sha(pam),ida_export_sha256=sha(q/'ida-r3/ida-remaining.json'),ida_tool='IDA 9.4',ida_lines_verified=lines,cases=cases,limits=['Explicit learned/resources and original cursor input; no natural learning claim.','Map bridge current terrain may reject change; visual cue means accepted dispatch only.','Map original control/HD same-snapshot comparison is a separate implementation gate.'])
 a.out.write_text(json.dumps(result,indent=2)+'\n');print(result['status'],lines,len(cases))
if __name__=='__main__':main()
