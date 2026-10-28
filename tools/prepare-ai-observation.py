#!/usr/bin/env python3
"""030 DRAFT: restore only immutable inputs needed for a read-only AI probe."""
import argparse,gzip,hashlib,json,os,pathlib
CATALOG='8ab4fd7c02d82e23ac45a475ab2e0bfa7283d0f4ca53f4234525d7796e458b6b'
INPUTS=['ai-hook-audit-r1.json','ida-ai-candidates-r1.json','ida-ai-entry-r3.json','ida-ai-parents-r2.json','ai-hook-trace-r1.json','choi-hd-r1/03-attack-00-before.state','choi-hd-r1/02-active-before.state','choi-hd-r1/inputs.json','choi-hd-r1/receipt.json']
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--multi',action='store_true');a=p.parse_args();r=a.project;assert os.getuid()==1000 and not a.out.exists();raw=(r/'preserved/catalog.json.gz').read_bytes();assert sha(raw)==CATALOG
 catalog=json.loads(gzip.decompress(raw));lookup={v['path']:v for v in catalog['files']};prefix='workplace/probe-20261023/graphics-first/battle-r1/';rows=[];ready=[]
 selected=[(name,prefix+name)for name in INPUTS]
 if a.multi:selected.append(('choi-hd-r1/multi-ready-before.state',prefix+'friendly21-normal-old-r3/full-07-battle-ready-before.state'))
 for name,original in selected:
  v=lookup[original];obj=catalog['objects'][v['sha256']];f=(r/'artwork'if obj['codec']=='artwork'else r/'preserved')/obj['path'];blob=f.read_bytes();blob=gzip.decompress(blob)if obj['codec']=='gzip'else blob;assert sha(blob)==v['sha256'];ready.append((name,blob));rows.append(dict(original_path=v['path'],file=name,sha256=v['sha256'],bytes=len(blob)))
 a.out.mkdir(parents=True)
 for name,blob in ready:
  f=a.out/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(blob)
 (a.out/'inputs.json').write_text(json.dumps(dict(schema=1,catalog_sha256=CATALOG,files=rows,spec='030 DRAFT',production_changed=False),indent=2)+'\n');print(json.dumps(dict(restored=len(rows),bytes=sum(v['bytes']for v in rows))))
if __name__=='__main__':main()
