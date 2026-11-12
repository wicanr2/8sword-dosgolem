#!/usr/bin/env python3
"""056：離線核對 universal Mach-O 的 ad-hoc CodeDirectory 頁與資源雜湊。

不取代 Apple codesign／Gatekeeper 或真機驗收。接受 SHA-1／SHA-256，逐項核對。
"""
import hashlib, json, plistlib, struct, sys
from pathlib import Path

def digest(raw, kind, size):
    assert kind in (1,2,3,4)
    return {1:hashlib.sha1,2:hashlib.sha256,3:hashlib.sha256,4:hashlib.sha384}[kind](raw).digest()[:size]

def check(path, info=None, resources=None):
    raw=path.read_bytes();magic,n=struct.unpack_from('>II',raw)
    assert magic==0xcafebabe and n==2
    result=[]
    for i in range(n):
        cpu,sub,offset,size,align=struct.unpack_from('>IIIII',raw,8+20*i)
        b=raw[offset:offset+size];assert len(b)==size
        header=struct.unpack_from('<8I',b);assert header[0]==0xfeedfacf
        pos=32;signature=None
        for _ in range(header[4]):
            cmd,length=struct.unpack_from('<II',b,pos);assert length>=8
            if cmd==0x1d:signature=struct.unpack_from('<II',b,pos+8)
            pos+=length
        assert signature
        start,length=signature;blob=b[start:start+length]
        magic,total,count=struct.unpack_from('>III',blob);assert magic==0xfade0cc0 and total<=len(blob)
        entries={}
        for j in range(count):
            kind,at=struct.unpack_from('>II',blob,12+8*j)
            _,length=struct.unpack_from('>II',blob,at);entries[kind]=blob[at:at+length]
        assert 0 in entries
        cds=[]
        for kind,cd in entries.items():
            if kind!=0 and not 0x1000<=kind<=0x1005:continue
            fields=struct.unpack_from('>9I4BI',cd)
            magic,length,version,flags,hash_offset,ident,special,slots,limit,hash_size,hash_type,platform,page,spare=fields
            assert magic==0xfade0c02 and length==len(cd) and flags&2
            assert (hash_type,hash_size)in[(1,20),(2,32)] and page in range(12,17)
            if info is not None:assert hash_type==2
            assert limit==start and slots==(limit+(1<<page)-1)//(1<<page)
            for k in range(slots):
                expected=cd[hash_offset+k*hash_size:hash_offset+(k+1)*hash_size]
                assert digest(b[k*(1<<page):min(limit,(k+1)*(1<<page))],hash_type,hash_size)==expected,(path,i,k)
            for k in range(1,special+1):
                expected=cd[hash_offset-k*hash_size:hash_offset-(k-1)*hash_size]
                if expected==bytes(hash_size):continue
                content=info if k==1 else resources if k==3 else entries.get(k)
                assert content is not None,(path,'unknown special slot',k)
                assert digest(content,hash_type,hash_size)==expected,(path,i,'special',k)
            cds.append(dict(sha256=hashlib.sha256(cd).hexdigest(),cdhash=digest(cd,hash_type,20).hex(),hash_type=hash_type,pages=slots,special_slots=special))
        result.append(dict(cpu=cpu,subtype=sub,code_directories=cds))
    assert {r['cpu']for r in result}=={0x01000007,0x0100000c}
    return result

def main():
    app=Path(sys.argv[1]);c=app/'Contents';info=(c/'Info.plist').read_bytes();resources=(c/'_CodeSignature/CodeResources').read_bytes()
    executables={}
    for p in [c/'MacOS/8sword-remake',*sorted((c/'Frameworks').glob('*.dylib'))]:
        executables[str(p.relative_to(c))]=check(p,info if p.parent.name=='MacOS'else None,resources if p.parent.name=='MacOS'else None)
    plist=plistlib.loads(resources);checked=0
    for name,row in plist['files2'].items():
        p=c/name
        if 'hash2'in row:assert hashlib.sha256(p.read_bytes()).digest()==row['hash2'];checked+=1
        if 'hash'in row:assert hashlib.sha1(p.read_bytes()).digest()==row['hash']
        if 'cdhash'in row:
            hashes={bytes.fromhex(cd['cdhash'])for arch in executables[name]for cd in arch['code_directories']}
            assert row['cdhash']in hashes,(name,'cdhash')
    assert checked>=287
    print(json.dumps(dict(status='passed-static-adhoc-pages-and-resources',resources=checked,executables=executables,limit='Not Apple codesign, trust assessment, notarization or native execution.'),indent=2))

if __name__=='__main__':main()
