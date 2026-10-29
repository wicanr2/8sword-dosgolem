#!/usr/bin/env python3
"""030 READY: extend the accepted XTEST player path with the third rules row."""
import argparse,hashlib,json,pathlib,subprocess
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
 subprocess.run(['python',str(a.project/'tools/prepare-formation-gui.py'),'--project',str(a.project),'--out',str(a.out)],check=True)
 s=(a.out/'formation-gui-check.go').read_text()
 s=s.replace('y:=88;if mode=="formation" {y=140}\n d.toolbarClick(2400,y)','y:=88;if mode=="formation" {y=140}\n if mode=="tactics" {d.press(116);d.press(36)} else {d.toolbarClick(2400,y)}')
 s=s.replace('d.selectRules("formation")','d.selectRules("formation")\n d.selectRules("tactics")')
 s=s.replace('d.rules()["Mode"]!="formation"','d.rules()["Mode"]!="tactics"')
 s=s.replace('lock formation rules','lock tactics rules')
 assert s.count('d.selectRules("tactics")')==1 and s.count('d.rules()["Mode"]!="tactics"')==2
 f=a.out/'tactics-gui-check.go';f.write_text(s)
 (a.out/'tactics-driver-source.json').write_text(json.dumps(dict(schema=1,generated_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),method='Accepted normal XTEST path, keyboard selects third rules row, no memory injection'),indent=2)+'\n')
if __name__=='__main__':main()
