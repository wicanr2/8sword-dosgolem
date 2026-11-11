#!/usr/bin/env python3
"""整組素材／偏好拒絕案例。Docker，僅 native 與本工具。"""
import hashlib,json,os,shutil,struct,subprocess
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fnv(b):
 v=14695981039346656037
 for x in b:v=((v^x)*1099511628211)&0xffffffffffffffff
 return v
def main():
 assert Path('/.dockerenv').exists()and os.getuid()==1000
 r=Path('/native');out=r/'cli-check';out.mkdir();runs=[];env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_RENDER_DRIVER='software',SDL_AUDIODRIVER='dummy')
 def pack(name,original=True):
  dest=out/name;dest.mkdir()
  for p in(r/'pack').rglob('*'):
   rel=p.relative_to(r/'pack')
   if not original and rel.parts[0]=='original':continue
   if p.is_file():(dest/rel).parent.mkdir(parents=True,exist_ok=True);os.link(p,dest/rel)
  return dest
 old=pack('old-pack',False);(old/'poster-font.bin').unlink();shutil.copy2(r/'legacy-poster-font.bin',old/'poster-font.bin')
 for name in ['bad-option','missing-group','missing-entry','bad-sha','bad-dimensions','bad-preference','linked-preference']:
  store=out/(name+'-store');store.mkdir()
  for p in(r/'fixture').iterdir():shutil.copy2(p,store/p.name)
  media=r/'pack';mode='auto';expected=''
  if name=='bad-option':mode='other';expected='畫面模式無效'
  if name=='missing-group':media=old;mode='original';expected='此資料包沒有原圖素材組'
  if name in ['missing-entry','bad-sha','bad-dimensions']:
   media=pack(name+'-pack')
   if name=='missing-entry':p=media/'original/images.tsv';raw=p.read_bytes().splitlines(keepends=True);p.unlink();p.write_bytes(b''.join(raw[:1]+raw[2:]));expected='原圖素材組不完整'
   else:
    p=media/'original/map-tile-64.rgba';raw=bytearray(p.read_bytes());p.unlink()
    if name=='bad-sha':raw[16]^=1;expected='原圖素材SHA不符'
    else:struct.pack_into('<I',raw,8,191);expected='圖片尺寸或長度不符'
    raw[-8:]=struct.pack('<Q',fnv(raw[:-8]));p.write_bytes(raw)
  if name=='bad-preference':(store/'display.json').write_text('{"schema":1,"mode":"other"}');expected='畫面偏好無效'
  if name=='linked-preference':(store/'outside').write_text('untouched');(store/'display.json').symlink_to('outside');expected='畫面偏好形態無效'
  before={p.name:sha(p)for p in store.iterdir()if p.is_file()};cmd=[str(r/'8sword-remake'),'--battle','--assets',str(media),'--save-dir',str(store),'--continue','--display',mode,'--mute'];p=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=20);assert p.returncode==1 and expected in p.stderr,(name,p.returncode,p.stderr);assert all(sha(store/n)==v for n,v in before.items())
  if name=='linked-preference':(store/'display.json').unlink()
  runs.append(dict(name=name,command=cmd,exit=p.returncode,stderr=p.stderr,files_before_sha256=before,unchanged=True))
 (out/'receipt.json').write_text(json.dumps(dict(status='passed-rust-display-cli',cases=runs),ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
