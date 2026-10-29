#!/usr/bin/env python3
"""030 DRAFT capacity research preparation and evidence audit; no production writes."""
import argparse
import ast
import gzip
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import struct
import urllib.parse


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['prepare', 'prepare-probe-r2', 'prepare-owned', 'audit', 'page', 'archive', 'verify', 'integrity'])
    p.add_argument('--project', type=Path)
    p.add_argument('--archive', type=Path)
    p.add_argument('--out', type=Path)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000
    if a.action == 'verify':
        index = a.archive / 'troop-capacity-r1.json'
        data = read(index)
        checked = set()
        for item in data['files']:
            path = Path(item['path'])
            assert not path.is_absolute() and '..' not in path.parts
            obj = data['objects'][item['sha256']]
            f = a.archive / 'troop-capacity-r1' / obj['file']
            assert sha(f) == obj['stored_sha256']
            raw = gzip.decompress(f.read_bytes())
            assert hashlib.sha256(raw).hexdigest() == item['sha256'] and len(raw) == item['bytes']
            checked.add(item['sha256'])
        assert not a.out.exists()
        a.out.write_text(json.dumps(dict(status='passed-detached-troop-capacity', files=len(data['files']),
            objects=len(checked), index_sha256=sha(index), workplace_required=False), indent=2)+'\n')
        return
    r = a.project
    q = r / 'workplace/probe-20261023/graphics-first/battle-r1/troop-capacity-r1'
    if a.action == 'prepare':
        assert not q.exists() and q.parent.is_dir() and q.parent.stat().st_uid == 1000
        q.mkdir()
        (q / 'ida').mkdir()
        smoke = '''import hashlib,json,os\nfrom pathlib import Path\nimport ida_auto,idaapi,idautils\nida_auto.auto_wait()\np=Path('/game/PAM.AY')\nPath('/out/ida-smoke.json').write_text(json.dumps(dict(schema=1,uid=os.getuid(),version=idaapi.get_kernel_version(),functions=len(list(idautils.Functions())),source_sha256=hashlib.sha256(p.read_bytes()).hexdigest())))\nidaapi.qexit(0)\n'''
        (q / 'ida/smoke.py').write_text(smoke)
        base = read(r / 'preserved/hd-music-audit-r1.json')
        for group, folder in [('source_inputs', r), ('core_files', r / 'workplace/player/runtime-render-r1/src'),
                              ('programs', r / 'workplace/player'), ('asset_hashes', r / 'workplace/player/assets-painted-r69')]:
            for name, h in base[group].items():
                assert sha(folder / name) == h
        (q / 'baseline.json').write_text(json.dumps(dict(source_inputs=base['source_inputs'], core_files=base['core_files'],
            programs=base['programs'], asset_hashes=base['asset_hashes']), indent=2) + '\n')
        src = q / 'probe-build/src'
        for name in base['source_inputs']:
            dest = src / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(r / name, dest)
        shutil.copyfile(r / 'tools/probe-troop-capacity.go', src / 'tools/probe-troop-capacity.go')
        print('Prepared isolated capacity study; production 193/923/535 unchanged.')
        return
    if a.action == 'prepare-probe-r2':
        src = q / 'probe-build-r2/src'
        assert not src.exists()
        for name, h in read(q / 'baseline.json')['source_inputs'].items():
            assert sha(r / name) == h
            dest = src / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(r / name, dest)
        shutil.copyfile(r / 'tools/probe-troop-capacity.go', src / 'tools/probe-troop-capacity.go')
        print('Prepared native save/cold-reload probe r2')
        return
    if a.action == 'prepare-owned':
        out = q / 'owned'
        assert not out.exists()
        out.mkdir()
        catalog = read(r / 'docs/images/troop-traits-reference-r1.json')
        pam = r / 'workplace/intake-20261023/sources/game/8sword/PAM.AY'
        assert sha(pam) == catalog['original_pam_sha256']
        ida = read(q / 'ida/ida-capacity-r2.json')
        prices = next(t for t in ida['tables'] if t['label'] == 'price-index-candidate')
        assert pam.read_bytes()[prices['file_offset']:prices['file_offset']+52].hex() == prices['bytes']
        values = struct.unpack('<26H', bytes.fromhex(prices['bytes']))
        profiles = [dict(id=f'native:{v["kind"]:02d}', name=v['name'], origin='native',
                        native_kind=v['kind'], gold=values[v['kind']], command=(v['kind']-1)%5+1,
                        rank=(v['kind']-1)%5) for v in catalog['native_names']]
        for index in [8, 10, 3, 4, 17, 19, 21, 24]:
            v = catalog['openkb_troops'][index]
            profiles.append(dict(id='openkb:'+v['file'], name=v['name'], origin='openkb-reference-prototype',
                gold=int(v['gold']), command=int(v['hp']), rank=int(v['skill'])-1,
                reference_abilities=[] if v['abilities']=='none' else [s.strip() for s in v['abilities'].split(',')]))
        assert len(profiles) == 33 and len({v['id'] for v in profiles}) == 33
        (out / 'catalog.json').write_text(json.dumps(dict(schema='eightsword-owned-catalog/1', profiles=profiles,
            source_sha256={'PAM.AY':sha(pam), 'openkb-troops.ini':catalog['openkb_sources']['data/free/troops.ini']}),
            ensure_ascii=False, indent=2)+'\n')
        (out / 'src').mkdir()
        for name in ['research-owned-army.go','research-owned-army_test.go']:
            (out / 'src' / name).write_text((r / 'tools' / name).read_text().removeprefix('//go:build ignore\n'))
        (out / 'src/go.mod').write_text('module owned-army-prototype\n\ngo 1.24.0\n')
        print('Prepared Go-owned 25 native + 8 namespaced reference profiles')
        return
    if a.action == 'audit':
        base = read(q / 'baseline.json')
        pam = r / 'workplace/intake-20261023/sources/game/8sword/PAM.AY'
        raw = pam.read_bytes()
        ida = read(q / 'ida/ida-capacity-r2.json')
        assert sha(pam) == ida['source_sha256'] == '83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0'
        assert sha(r / 'workplace/probe-20261023/text-first/PAM.i64') == ida['database_sha256']
        assert sha(r / 'tools/export-troop-capacity-ida.py') == ida['tool_sha256']
        assert ida['function_count'] == 521 and len(ida['bodies']) <= 90
        word = lambda at: struct.unpack_from('<H', raw, at)[0]
        header = word(8)*16
        def relocated(base):
            result = bytearray(raw[header:])
            for i in range(word(6)):
                at = word(24)+i*4
                target = word(at+2)*16+word(at)
                struct.pack_into('<H', result, target, (struct.unpack_from('<H', result, target)[0]+base)&65535)
            return result
        ida_bytes, runtime = relocated(0x1000), relocated(0x110)
        lines = 0
        for body in ida['bodies']:
            for line in body['lines']:
                off = line['ida_linear']-0x10000
                data = bytes.fromhex(line['bytes'])
                assert line['file_offset'] == off+header and ida_bytes[off:off+len(data)] == data
                lines += 1
        for table in ida['tables']:
            off = table['file_offset']
            assert raw[off:off+table['size']].hex() == table['bytes']
        native = read(q / 'native-r2/receipt.json')
        assert native['normal_inputs'] and not native['normal_ram_injection'] and not native['normal_snapshot_loaded']
        for point in native['normal_records']:
            ip = point['ip']
            assert point['runtime_bytes'] == runtime[ip:ip+16].hex()
        assert len(native['helper_cases']) == 75
        for case in native['helper_cases']:
            kind = case['kind']
            assert case['leadership_per_unit'] == (kind-1)%5+1
            army = case['army']
            used = sum(army[i+1]*((army[i]-1)%5+1) for i in range(0,12,2) if army[i])&65535
            capacity = any(army[i] in (0,kind) for i in range(0,12,2))
            assert case['used_leadership'] == used and case['capacity'] == int(capacity)
        decoded = read(q / 'decoded-r2/index.json')
        memories = {}
        for name, meta in decoded.items():
            data = gzip.decompress((q / 'decoded-r2' / meta['memory_file']).read_bytes())
            assert len(data) == 1<<20 and hashlib.sha256(data).hexdigest() == meta['memory_sha256']
            memories[name] = data
        ds = native['before']['registers']['DS']
        for name, point in [('before-commit.state',native['before']), ('after-commit.state',native['after'])]:
            mem = memories[name]
            assert decoded[name]['ip'] == point['ip']
            assert list(struct.unpack_from('<12H',mem,ds*16+0x54a)) == point['army']
            assert struct.unpack_from('<H',mem,ds*16+0x4f8)[0] == point['gold']
        before, after = native['before'], native['after']
        assert before['army'] == [1,30]+[0]*10 and after['army'] == [1,31]+[0]*10
        assert before['gold'] == 500 and after['gold'] == 499
        saved = (q / 'native-r2/saved-gamedata.ay').read_bytes()
        reload = native['native_save_cycle']
        assert reload['fresh_engine'] and not reload['snapshot_loaded'] and reload['buffer_equal']
        assert len(saved) == reload['original_bytes'] == 2987
        assert sha(q / 'native-r2/saved-gamedata.ay') == reload['original_sha256']
        mem = memories['reload.state']
        assert mem[0x9e000:0x9e000+2987] == saved
        assert list(struct.unpack_from('<12H',mem,ds*16+0x54a)) == after['army']
        assert struct.unpack_from('<H',mem,ds*16+0x4f8)[0] == 499
        catalog = read(q / 'owned/catalog.json')
        assert len(catalog['profiles']) == 33
        source = read(r / 'docs/images/troop-traits-reference-r1.json')
        prices = next(v for v in ida['tables'] if v['label']=='price-index-candidate')
        price_values = struct.unpack('<26H',bytes.fromhex(prices['bytes']))
        profiles = {v['id']:v for v in catalog['profiles']}
        assert len(profiles) == 33
        for native_name in source['native_names']:
            kind = native_name['kind'];v = profiles[f'native:{kind:02d}']
            assert v['native_kind']==kind and v['name']==native_name['name']
            assert v['gold']==price_values[kind] and v['command']==(kind-1)%5+1
        for v in catalog['profiles'][25:]:
            original = next(x for x in source['openkb_troops'] if 'openkb:'+x.get('file','')==v['id'])
            assert v['origin']=='openkb-reference-prototype' and 'native_kind'not in v
            assert (v['name'],v['gold'],v['command'],v['rank']) == (original['name'],int(original['gold']),int(original['hp']),int(original['skill'])-1)
        demo = read(q / 'owned/demo-r1/receipt.json')
        cold = read(q / 'owned/cold-load-r2/receipt.json')
        assert demo['status']=='passed-owned-army-prototype' and cold['status']=='passed-owned-army-cold-load'
        assert not demo['production'] and not cold['production']
        assert demo['army']==cold['army'] and demo['catalog_sha256']==cold['catalog_sha256']
        gold=10000; command=0; slots=[]
        for receipt in demo['receipts']:
            v=profiles[receipt['Unit'] if 'Unit'in receipt else receipt['unit']]
            assert receipt['count']==1 and receipt['spent']==v['gold']
            gold-=v['gold'];command+=v['command'];slots.append(dict(unit=v['id'],count=1))
        assert demo['army']['slots']==slots and demo['army']['gold']==gold and command<=10000
        assert all(v['stock']==19 for v in demo['army']['offers'].values())
        sidecar=read(q/'owned/demo-r1/gamedata.ay.army.json')
        assert sidecar['army']==demo['army'] and sidecar['original_sha256']==sha(q/'owned/demo-r1/gamedata.ay')
        assert sidecar['catalog_sha256']==cold['catalog_sha256']
        final_cold=read(q/'owned/cold-load-r3/receipt.json')
        assert final_cold==cold
        for name in ['research-owned-army.go','research-owned-army_test.go']:
            assert (r/'tools'/name).read_text().removeprefix('//go:build ignore\n')==(q/'owned/src-r3'/name).read_text()
        browser=read(q/'browser-r2/browser-r1.json')
        assert browser['status']=='passed-offline-recruitment-prototype'and browser['gold']==419 and browser['wolf_count']==2
        assert not browser['mobile_horizontal_overflow']and not browser['game_executed']
        for name in ['tests-r1.log','tests-r2.log','tests-r3.log']:
            log=(q/'owned'/name).read_text();assert 'PASS'in log and 'FAIL'not in log and 'SKIP'not in log
        assert not(q/'owned/vet-r3.log').read_text().strip()
        for group, folder in [('source_inputs',r),('programs',r/'workplace/player'),
                              ('core_files',r/'workplace/player/runtime-render-r1/src'),
                              ('asset_hashes',r/'workplace/player/assets-painted-r69')]:
            for name,h in base[group].items():assert sha(folder/name)==h
        result=dict(status='passed-troop-capacity-and-owned-army-prototype',production=False,
            ida_functions=len(ida['bodies']),ida_instruction_lines=lines,helper_cases=75,profiles=33,
            native_before_count=30,native_after_count=31,native_before_gold=500,native_after_gold=499,
            native_save_sha256=reload['original_sha256'],native_save_bytes=2987,native_fresh_engine=True,
            owned_disk_roundtrip=True,owned_cold_process_equal=True,owned_transactions=6,
            owned_source_sha256={n:sha(r/'tools'/n)for n in ['research-owned-army.go','research-owned-army_test.go']},
            owned_binary_sha256=sha(q/'owned/owned-army-r3'),browser_receipt_sha256=sha(q/'browser-r2/browser-r1.json'),
            unchanged_sources=193,unchanged_programs=7,unchanged_core=923,unchanged_assets=535,
            prototype_catalog_sha256=demo['catalog_sha256'],audit_tool_sha256=sha(Path(__file__)),
            limits=['New units exist only in a disposable Go prototype; not connected to normal recruitment or battle UI.',
                    'Native helper contracts and one ordinary purchase are verified; no full overflow or all-native-rule parity claim.',
                    'OpenKB prototype gold/HP/rank are reference values; abilities are inactive metadata.',
                    'Owned sidecar remains DRAFT: integration must own resource reconciliation, native-mode refusal and save lifecycle; not a production save format.'])
        assert a.out and not a.out.exists();a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print('Verified native bytes/RAM/cold save, 75 helper cases and Go-owned recruitment/save prototype')
        return
    if a.action == 'page':
        audit=read(q/'audit-r1.json');assert audit['status']=='passed-troop-capacity-and-owned-army-prototype'
        catalog=read(q/'owned/catalog.json');native=read(q/'native-r2/receipt.json')
        data=dict(profiles=catalog['profiles'],gold=native['after']['gold'],leadership=native['after']['leadership'],
            army=[dict(unit='native:01',count=31)]+[dict(unit='',count=0)for _ in range(5)])
        template='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>神州八劍：Go招募與存檔原型</title><style>
body{background:#102b24;color:#eee6cb;font:18px/1.7 system-ui,sans-serif;max-width:1080px;margin:30px auto;padding:20px}h1,h2{color:#efd59c}section{border:1px solid #89704a;padding:20px;margin:22px 0;border-radius:8px}button,select,input{font:inherit;background:#213b30;color:#fff0c4;padding:10px;border:1px solid #b4985a;max-width:100%;box-sizing:border-box}button{cursor:pointer;margin:8px}select{width:100%}table{border-collapse:collapse;width:100%}td,th{padding:10px;border-bottom:1px solid #57675a;text-align:left}.note{color:#dbc5a3}#slots{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.slot{border:1px solid #82907b;padding:16px}#result{min-height:2em;color:#f4d58b}@media(max-width:650px){#slots{grid-template-columns:1fr}body{margin:0}}
</style><h1>Go 自有招募與存檔原型</h1><p class="note">離線研究原型，尚未接入遊戲。候選金錢／領導力數值只供試算；特性標記尚未實作成戰鬥效果。</p><section><h2>目前已驗證</h2><ul><li>正常原版招募：民兵30→31，金錢500→499。</li><li>真正F7存檔後，以全新Engine冷啟動繼續，軍隊、金錢及2987 bytes讀檔緩衝區相同。</li><li>75組原版容量／領導力控制，25種原版及8種獨立編號候選。</li><li>Go六次招募後保存全部軍隊與庫存，另一個程序完整讀回。</li></ul></section><section><h2>從實際招募結果接續試算</h2><p>初始為已驗的31民兵／499金。以下點選只改瀏覽器內的試算資料，不寫遊戲存檔。</p><select id="unit"></select><p id="profile"></p><label>數量 <input id="quantity" type="number" min="1" max="10000" value="2"></label><button id="recruit">試算招募</button><button id="reset">重設</button><p id="totals"></p><p id="result" role="status"></p><div id="slots"></div></section><section><h2>存檔處理</h2><p>原型附檔保存獨立兵種ID、六隊數量、招募庫存、金錢、領導力與規則。它綁定原版進度及兵種資料SHA，錯版本、錯進度、缺欄位與未知兵種會拒絕讀取；寫入使用暫存、sync及rename。</p><p>正式接入還須銜接原版資源、完整存檔生命週期與新增兵種的戰鬥路徑。這份原型不是正式可玩的新增兵種包。</p></section><script>
const initial=DATA,profiles=new Map(initial.profiles.map(p=>[p.id,p]));let state;
const unit=document.querySelector('#unit'),quantity=document.querySelector('#quantity'),result=document.querySelector('#result');
for(const p of initial.profiles){const o=document.createElement('option');o.value=p.id;o.textContent=p.name+'　'+(p.origin==='native'?'原版':'openKB候選');unit.append(o)}unit.value='openkb:wolf';
function render(){const p=profiles.get(unit.value),used=state.army.reduce((s,v)=>s+(v.unit?profiles.get(v.unit).command*v.count:0),0);document.querySelector('#profile').textContent=p.id+'｜單價 '+p.gold+'｜每名領導力 '+p.command+'｜參考特性 '+(p.reference_abilities?.join('、')||'無');document.querySelector('#totals').textContent='金錢 '+state.gold+'｜領導力 '+used+'/'+initial.leadership;document.querySelector('#slots').replaceChildren(...state.army.map(v=>{const e=document.createElement('div');e.className='slot';e.textContent=v.unit?profiles.get(v.unit).name+' × '+v.count:'空隊';return e}))}
function reset(){state=JSON.parse(JSON.stringify(initial));state.stock=Object.fromEntries(initial.profiles.map(p=>[p.id,20]));result.textContent='';render()}
unit.onchange=render;document.querySelector('#reset').onclick=reset;document.querySelector('#recruit').onclick=()=>{const p=profiles.get(unit.value),n=Number(quantity.value);let slot=state.army.findIndex(v=>v.unit===p.id);if(slot<0)slot=state.army.findIndex(v=>!v.unit);const used=state.army.reduce((s,v)=>s+(v.unit?profiles.get(v.unit).command*v.count:0),0),max=slot<0?0:Math.min(state.stock[p.id],Math.floor(state.gold/p.gold),Math.floor((initial.leadership-used)/p.command));if(!Number.isInteger(n)||n<1||n>max){result.textContent='未變更：目前最多可招募 '+max+' 名。';return}state.gold-=n*p.gold;state.stock[p.id]-=n;state.army[slot].unit=p.id;state.army[slot].count+=n;result.textContent='已試算招募 '+p.name+' '+n+' 名。剩餘庫存 '+state.stock[p.id]+'。';render()};reset();
</script></html>'''
        text=template.replace('DATA',json.dumps(data,ensure_ascii=False).replace('<','\\u003c'))
        target=r/'docs/images/owned-army-prototype-r1.html';assert not target.exists();target.write_text(text)
        print('Created clearly labeled offline recruitment prototype')
        return
    if a.action == 'archive':
        assert read(q/'audit-r2.json')['status']=='passed-troop-capacity-and-owned-army-prototype'
        folder=a.archive/'troop-capacity-r1';index=a.archive/'troop-capacity-r1.json'
        assert not folder.exists()and not index.exists();folder.mkdir()
        selected={f for f in q.rglob('*')if f.is_file()}
        selected.update(r/'tools'/n for n in ['export-troop-capacity-ida.py','probe-troop-capacity.go','audit-troop-capacity.py','read-troop-capacity-states.go','research-owned-army.go','research-owned-army_test.go'])
        selected.update(r/n for n in ['docs/spec/030-battle-expansion-proposal.md','docs/images/troop-traits-reference-r1.json','docs/images/owned-army-prototype-r1.html'])
        files=[];objects={}
        for f in sorted(selected):
            assert not f.is_symlink()and f.stat().st_uid==1000
            data=f.read_bytes();h=hashlib.sha256(data).hexdigest()
            if h not in objects:
                blob=gzip.compress(data,compresslevel=6,mtime=0);name=h+'.gzip';(folder/name).write_bytes(blob)
                objects[h]=dict(file=name,stored_sha256=hashlib.sha256(blob).hexdigest(),stored_bytes=len(blob))
            files.append(dict(path=str(f.relative_to(r)),sha256=h,bytes=len(data),mode=f.stat().st_mode&0o777))
        index.write_text(json.dumps(dict(schema=1,files=files,objects=objects,audit_sha256=sha(q/'audit-r2.json'),
            dependencies={'preserved/hd-music-r1.json':sha(r/'preserved/hd-music-r1.json'),'preserved/catalog.json.gz':sha(r/'preserved/catalog.json.gz')},
            limits='Research prototype only. Current Git documents supersede historical DRAFT snapshots.'),indent=2)+'\n')
        result=dict(status='preserved-troop-capacity-and-owned-prototype',files=len(files),objects=len(objects),stored_bytes=sum(v['stored_bytes']for v in objects.values()))
        assert not a.out.exists();a.out.write_text(json.dumps(result,indent=2)+'\n');return
    base=read(q/'baseline.json')
    for group,folder in [('source_inputs',r),('programs',r/'workplace/player'),('core_files',r/'workplace/player/runtime-render-r1/src'),('asset_hashes',r/'workplace/player/assets-painted-r69')]:
        for name,h in base[group].items():assert sha(folder/name)==h
    art=read(r/'artwork/manifest.json');assert len(art['files'])==1040
    for item in art['files']:assert sha(r/'artwork'/item['path'])==item['sha256']
    verification=read(a.archive/'troop-capacity-verification-r1.json')
    assert not verification['workplace_required']and verification['index_sha256']==sha(a.archive/'troop-capacity-r1.json')
    assert read(a.archive/'troop-capacity-r1.json')['audit_sha256']==sha(a.archive/'troop-capacity-audit-r1.json')
    for folder in [q,a.archive/'troop-capacity-r1']:
        assert all(f.stat().st_uid==1000 for f in folder.rglob('*'))
        assert not any(f.is_dir()and f.name.endswith('.md')for f in folder.rglob('*'))
    assert not any(f.is_file()for f in(r/'workplace/gocache').rglob('*'))
    ast.parse(Path(__file__).read_text());links=0
    for doc in list(r.glob('*.md'))+[f for d in ['docs','artwork','preserved']for f in(r/d).rglob('*.md')]:
        for target in re.findall(r'\[[^\]]*\]\(([^\s)]+)(?:\s+"[^\"]*")?\)',doc.read_text()):
            path=urllib.parse.unquote(target.strip('<>').split('#',1)[0])
            if not path or path.startswith('/')or re.match('[a-zA-Z][a-zA-Z0-9+.-]*:',path):continue
            assert(doc.parent/path).exists()or(doc.parent/path).resolve()==a.out.resolve(),(doc,target)
            links+=1
    assert not a.out.exists();a.out.write_text(json.dumps(dict(status='passed-owned-army-prototype-integrity',production_changed=False,
        sources=193,programs=7,core=923,assets=535,artwork=1040,markdown_links=links,root_owned_outputs=0,workspace_cache_files=0),indent=2)+'\n')
    print('Verified unchanged production, permanent evidence, ownership and document links')


if __name__ == '__main__':
    main()
