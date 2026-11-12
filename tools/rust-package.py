#!/usr/bin/env python3
"""056：本機完整包組裝、解壓校驗與媒體雜湊，限 Docker。"""
import gzip, hashlib, json, os, plistlib, re, shutil, subprocess, sys, tarfile, zipfile
from pathlib import Path
sys.dont_write_bytecode = True
from rust_package_settings import VERSION
Q = Path('/q'); R = Path('/r')

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p, value): p.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
def run(cmd): return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)

def media():
    prefix = 'workplace/probe-20261023/graphics-first/battle-r1/rust-player-path-r1/native/pack/'
    files = [dict(path=f['path'][len(prefix):], sha256=f['sha256'], bytes=f['bytes'])
             for f in json.loads((R/'preserved/rust-player-path-r1.json').read_text())['files'] if f['path'].startswith(prefix)]
    assert len(files) == 287 and len({f['path'] for f in files}) == 287
    root = R/prefix
    assert all(sha(root/f['path']) == f['sha256'] for f in files)
    return root, files

def common(label):
    root = Q/'stage'/f'8sword-{VERSION}-{label}'; root.mkdir()
    pack = root/'pack' if label != 'macos-universal2' else root/'8sword.app/Contents/Resources/pack'
    source, files = media(); shutil.copytree(source, pack)
    overlay = json.loads((Q/'media-overlay.json').read_text()) if (Q/'media-overlay.json').exists() else None
    if overlay:
        for f in overlay['files']:
            assert f['name'] in ['poster-wings.rgba', 'intro.bin']
            assert sha(pack/f['name']) == f['old_sha256']
            src = Q/'native/pack'/f['name']; assert sha(src) == f['sha256']
            shutil.copy2(src, pack/f['name'])
    licenses = root/'licenses'; licenses.mkdir()
    shutil.copy2(R/'LICENSE', root/'LICENSE.txt')
    for name in ['rust-package-deps.py', 'rust-package-build.py', 'rust-package.py', 'rust-package.sh', 'rust-package-macho.py', 'rust_package_settings.py', 'rust-package-defaults.env', 'prepare-head-art-package.py']:
        shutil.copy2(R/'tools'/name, licenses/name)
    source_dir = licenses/'source'; source_dir.mkdir()
    from importlib.util import spec_from_file_location, module_from_spec
    spec = spec_from_file_location('deps', R/'tools/rust-package-deps.py'); mod = module_from_spec(spec); spec.loader.exec_module(mod)
    for name, (url, digest) in mod.SOURCES.items():
        p = Q/'sources'/url.rsplit('/', 1)[1]; assert sha(p) == digest
        shutil.copy2(p, source_dir/p.name)
        for license_name in ['COPYING', 'COPYING.Xiph', 'COPYING.LGPL', 'COPYING.GPL', 'COPYING.BSD', 'LICENSE']:
            p = Q/'sources'/name/license_name
            if p.is_file(): shutil.copy2(p, licenses/(name+'-'+license_name+'.txt'))
    catalog = json.loads(gzip.decompress((R/'preserved/catalog.json.gz').read_bytes()))
    font_notices = {}
    for f in catalog['files']:
        p = f['path']; name = Path(p).name
        wanted = p.startswith('workplace/player/assets-painted-r69/') and name.startswith('font-choice-') and any(t in name for t in ['LICENSE', 'NOTICE', 'OFL'])
        if wanted: font_notices.setdefault(name, f)
    for name, f in font_notices.items():
        obj = catalog['objects'][f['sha256']]
        raw = ((R/'artwork'/obj['path']).read_bytes() if obj['codec']=='artwork'
               else gzip.decompress((R/'preserved'/obj['path']).read_bytes()))
        assert hashlib.sha256(raw).hexdigest() == f['sha256']
        (licenses/('font-'+name+'.txt')).write_bytes(raw)
    for name in ['NotoSansCJK-LICENSE.txt', 'NotoSerifCJK-LICENSE.txt']:
        noto = Q/'sources'/name
        assert sha(noto) == '6a73f9541c2de74158c0e7cf6b0a58ef774f5a780bf191f2d7ec9cc53efe2bf2'
        shutil.copy2(noto, licenses/noto.name)
    # Code snapshot allows rebuilding this engine with replacement LGPL libraries.
    with tarfile.open(source_dir/'eightsword-rust-source.tar.gz', 'w:gz') as t:
        t.add(R/'internal/remake-rust', arcname='internal/remake-rust', filter=lambda f: None if '/target/' in f.name else f)
        t.add(R/'LICENSE', arcname='LICENSE')
    (root/'THIRD-PARTY-NOTICES.txt').write_text(
        '本機完整版，含合法持有來源的原版衍生素材，未授權公開散布。\n'
        '自有程式：RRSAL-1.0。SDL2：zlib。libsndfile：LGPL-2.1-or-later。\n'
        'Xiph Ogg／Vorbis／Opus／FLAC：各原始碼內完整授權。原版與HD美術、改編音樂保留各自權利。\n'
        '字型：Noto Sans/Serif CJK 與劉建毛草使用 SIL OFL 1.1；教育部隸書3.00使用 CC BY-ND 3.0 TW，作者中華民國教育部。\n'
        'licenses 保存授權、來源與重建腳本。第三方程式的授權不由 RRSAL 取代。\n')
    location = {'linux-x86_64':'$XDG_DATA_HOME/8sword-remake 或 $HOME/.local/share/8sword-remake',
                'windows-x86_64':'%LOCALAPPDATA%\\8sword-remake',
                'macos-universal2':'~/Library/Application Support/8sword-remake'}[label]
    launch = {'linux-x86_64':'執行 ./Start.sh，或直接執行 8sword-remake。需要 glibc 2.36 以上及桌面環境。',
              'windows-x86_64':'全部解壓後，雙擊 8sword.exe。需要 Windows 10 x64 以上。不可只搬走 EXE。',
              'macos-universal2':'將 8sword.app 放到 Applications 後開啟。需要 macOS 11 以上，支援 Intel／Apple Silicon。\n此包採 ad-hoc 簽署，未公證，尚未經 Apple 真機試玩。'}[label]
    text = f'''神州八劍 Rust 獨立版 {VERSION}

{launch}
包含原圖、HD、HD音樂、Noto900／隸書風／草書、三種海報與33種兵種。
本版已修正龍虎海報與故事背景的男主角頭頸。
不需要安裝 Go、Rust、DOSBox 或 dosgolem，也不需要執行原版 DOS EXE。

開始選單可新建、繼續與欣賞音樂。方向鍵移動，Enter確認，Esc取消；滑鼠可選單、選兵與選敵。
F1人物，F2軍隊檢閱，F3解雇，F4法術，F5地圖，F6搜尋，F7保存。
右下可切換原圖／HD，工具列可選字型、海報、原版／策略AI及原版／結陣／戰術規則。
原圖模式使用原始像素素材與Rust介面，不代表DOS整屏或原動畫逐幀還原。
HD直接由Rust繪製；原版Go播放器與這個獨立版是分開的程式。

存檔：{location}
新遊戲確認會替換既有進度。備份整個存檔目錄可同時保留進度與設定。
本版旅程格式v18，讀取既有Rust v1至v17；不匯入原DOS或Go存檔。
可用 --save-dir 指定既有可寫目錄；--skip-intro 跳過開場；--version 顯示完整版號。

這是本機開發完整版。Linux／Wine代表玩家路徑抽驗，結局沿用既有受控進度驗收，未宣稱自然完整通關。
封包完整性可依 manifest.json 的SHA-256核對。無預置玩家存檔。
素材來自本機合法持有來源，本包不得直接作為公開下載包。
專案：https://github.com/wicanr2/8sword-dosgolem
'''
    (root/'README.txt').write_bytes(text.replace('\n','\r\n').encode('utf-8-sig') if label == 'windows-x86_64' else text.encode())
    write(root/'media-sources.json', dict(version=VERSION, original_runtime='rust-player-path-r1', base_media=files, overrides=overlay['files'] if overlay else []))
    return root

def stage_linux():
    root = common('linux-x86_64'); exe = root/'8sword-remake'; shutil.copy2(Q/'build/linux/release/8sword-remake', exe)
    lib = root/'lib'; lib.mkdir(); licenses = root/'licenses/linux'; licenses.mkdir()
    output = run(['ldd', str(exe)]); assert 'not found' not in output
    excluded = {'libc.so.6','libm.so.6','libpthread.so.0','libdl.so.2','librt.so.1','ld-linux-x86-64.so.2'}
    deps = []
    for line in output.splitlines():
        m = re.match(r'\s*(\S+) => (/\S+) ', line)
        if not m or m[1] in excluded: continue
        src = Path(m[2]); shutil.copy2(src, lib/m[1]); deps.append(dict(name=m[1], source=str(src.resolve()), sha256=sha(src)))
        query = subprocess.run(['dpkg-query','-S',str(src)], text=True, capture_output=True)
        if query.returncode:
            query = subprocess.run(['dpkg-query','-S','*/'+src.resolve().name], text=True, capture_output=True, check=True)
        owner = query.stdout.splitlines()[0].split(': /')[0]
        copyright = Path('/usr/share/doc')/owner.split(':')[0]/'copyright'
        if copyright.is_file(): shutil.copy2(copyright, licenses/(owner.replace(':','-')+'.txt'))
    (Q/'logs/linux-ldd.txt').write_text(output)
    write(root/'libraries.json', deps)
    (root/'Start.sh').write_text('#!/bin/sh\nset -eu\ncd -- "$(dirname -- "$0")"\nexec ./8sword-remake "$@"\n'); (root/'Start.sh').chmod(0o755)
    assert run([str(exe), '--version']).strip() == VERSION

def stage_cross():
    root = common('windows-x86_64')
    shutil.copy2(Q/'build/cross/x86_64-pc-windows-gnu/release/8sword-remake.exe', root/'8sword.exe')
    shutil.copy2('/opt/sdl2/windows/x86_64-w64-mingw32/bin/SDL2.dll', root/'SDL2.dll')
    for p in (Q/'deps/windows/bin').glob('*.dll'): shutil.copy2(p, root/p.name)
    shutil.copy2('/opt/mm3-sdl-license/SDL2-LICENSE.txt', root/'licenses/SDL2-LICENSE.txt')
    # Compiler runtime imports are checked recursively against the bundled DLLs.
    system = {'advapi32.dll','gdi32.dll','imm32.dll','kernel32.dll','msvcrt.dll','ole32.dll','oleaut32.dll','setupapi.dll','shell32.dll','user32.dll','version.dll','winmm.dll','bcrypt.dll','bcryptprimitives.dll','ntdll.dll','userenv.dll','ws2_32.dll','api-ms-win-core-synch-l1-2-0.dll'}
    queue = list(root.glob('*.dll'))+[root/'8sword.exe']; imports = {}
    while queue:
        p = queue.pop(); output = run(['x86_64-w64-mingw32-objdump','-p',str(p)])
        names = re.findall(r'DLL Name: (\S+)', output); imports[p.name] = names
        for name in names:
            if name.lower() in system: continue
            if any(v.name.lower()==name.lower() for v in root.glob('*.dll')): continue
            matches = list(Path('/usr/lib/gcc/x86_64-w64-mingw32/14-posix').glob(name)) + list(Path('/usr/x86_64-w64-mingw32/lib').glob(name))
            assert matches, (p, name)
            shutil.copy2(matches[0], root/name); queue.append(root/name)
    write(root/'libraries.json', imports)
    root = common('macos-universal2'); app = root/'8sword.app'; contents=app/'Contents'
    bin = contents/'MacOS'; bin.mkdir(); frameworks=contents/'Frameworks'; frameworks.mkdir()
    prefix = '/osxcross/bin/x86_64-apple-darwin24.5-'
    subprocess.run([prefix+'lipo','-create',str(Q/'build/cross/x86_64-apple-darwin/release/8sword-remake'),str(Q/'build/cross/aarch64-apple-darwin/release/8sword-remake'),'-output',str(bin/'8sword-remake')], check=True)
    shutil.copy2(Q/'deps/mac-common/libSDL2.dylib', frameworks/'libSDL2.dylib')
    subprocess.run([prefix+'lipo','-create',str(Q/'deps/mac-x86_64/lib/libsndfile.1.dylib'),str(Q/'deps/mac-arm64/lib/libsndfile.1.dylib'),'-output',str(frameworks/'libsndfile.1.dylib')], check=True)
    shutil.copy2('/opt/mm3-sdl-license/SDL2-LICENSE.txt', root/'licenses/SDL2-LICENSE.txt')
    for p in [bin/'8sword-remake',*frameworks.glob('*.dylib')]: p.chmod(0o755)
    numeric = VERSION.split('-')[0][2:]
    (contents/'Info.plist').write_bytes(plistlib.dumps(dict(CFBundleExecutable='8sword-remake',CFBundleIdentifier='org.wicanr2.eightsword',CFBundleName='神州八劍',CFBundleDisplayName='神州八劍',CFBundlePackageType='APPL',CFBundleShortVersionString=numeric,CFBundleVersion=numeric,EightswordFullVersion=VERSION,LSMinimumSystemVersion='11.0',NSHighResolutionCapable=True)))
    sign = Q/'sources/apple-codesign-0.29.0-x86_64-unknown-linux-musl/rcodesign'
    assert sha(Q/'sources/apple-codesign-0.29.0-x86_64-unknown-linux-musl.tar.gz') == 'dbe85cedd8ee4217b64e9a0e4c2aef92ab8bcaaa41f20bde99781ff02e600002'
    (Q/'logs/macos-sign.log').write_text(run([str(sign), 'sign', '--digest', 'sha256', str(app)]))
    legacy = subprocess.run([str(sign),'verify',str(bin/'8sword-remake')],text=True,capture_output=True)
    (Q/'logs/macos-rcodesign-verify-limit.log').write_text(legacy.stdout+legacy.stderr)
    (Q/'logs/macos-sign-verify.log').write_text(run(['python3',str(R/'tools/rust-package-macho.py'),str(app)]))
    inspect_mac(root)

def inspect_mac(root=None):
    root = root or Q/'stage'/f'8sword-{VERSION}-macos-universal2'
    contents=root/'8sword.app/Contents';bin=contents/'MacOS';frameworks=contents/'Frameworks'
    prefix='/osxcross/bin/x86_64-apple-darwin24.5-'
    details = {}
    for p in [bin/'8sword-remake',*frameworks.glob('*.dylib')]:
        arch = run([prefix+'lipo','-archs',str(p)]); assert set(arch.split()) == {'x86_64','arm64'}
        deps = '\n'.join(l for l in run([prefix+'otool','-L',str(p)]).splitlines()if l.startswith('\t'))
        assert '/q/' not in deps and '/opt/' not in deps and '/osxcross/' not in deps
        details[str(p.relative_to(root))] = dict(architectures=arch.strip(), dependencies=deps, signature='CodeDirectory pages and bundle resources checked independently; see macos-sign-verify.log')
    write(root/'libraries.json', details)

def pack():
    out = R/'dist-all'/VERSION; full = out/'full-local'; full.mkdir(parents=True,exist_ok=True); (out/'smoke').mkdir(exist_ok=True)
    records=[]
    for root in sorted((Q/'stage').iterdir()):
        label=root.name.split(VERSION+'-')[1]
        for p in root.rglob('*'):
            p.chmod(0o755 if p.is_dir()or p.stat().st_mode&0o111 else 0o644)
        files=[dict(path=str(p.relative_to(root)),bytes=p.stat().st_size,sha256=sha(p),mode=p.stat().st_mode&0o777)for p in sorted(root.rglob('*'))if p.is_file()and p!=root/'manifest.json']
        assert len([f for f in files if f['path'].startswith('pack/' if label!='macos-universal2' else '8sword.app/Contents/Resources/pack/')])==287
        write(root/'manifest.json',dict(version=VERSION,platform=label,rights='full-local-only',save_schema='8SJRN018',no_go_dos_or_emulator_runtime=True,files=files))
        (root/'manifest.json').chmod(0o644)
        archive=full/(root.name+('.tar.gz'if label=='linux-x86_64'else'.zip')); assert not archive.exists()
        if label=='linux-x86_64':
            with tarfile.open(archive,'w:gz',compresslevel=6)as t:t.add(root,arcname=root.name)
        else:
            with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
                for p in sorted(root.rglob('*')):
                    if p.is_file():z.write(p,root.name+'/'+str(p.relative_to(root)))
            with zipfile.ZipFile(archive)as z:
                assert z.testzip()is None
                assert all(v.flag_bits&0x800 for v in z.infolist()if not v.filename.isascii())
        extracted=Q/'smoke'/('解壓 測試-'+label);extracted.mkdir()
        if label=='linux-x86_64':
            with tarfile.open(archive)as t:t.extractall(extracted,filter='data')
        else:
            with zipfile.ZipFile(archive)as z:
                z.extractall(extracted)
                for i in z.infolist():
                    mode=(i.external_attr>>16)&0o777
                    if mode:(extracted/i.filename).chmod(mode)
        for f in files:
            p=extracted/root.name/f['path'];assert sha(p)==f['sha256']and p.stat().st_size==f['bytes'],f['path']
            assert p.stat().st_mode&0o777==f['mode'],f['path']
        if label=='windows-x86_64':
            readme=(extracted/root.name/'README.txt').read_bytes();assert readme.startswith(b'\xef\xbb\xbf')and b'\n'not in readme.replace(b'\r\n',b'')
        records.append(dict(path=str(archive.relative_to(out)),bytes=archive.stat().st_size,sha256=sha(archive),files=len(files)+1,media=287,extracted=str(extracted/root.name)))
    write(Q/'package-records.json',dict(version=VERSION,packages=records))
    old=json.loads((out/'SHA256SUMS.json').read_text()) if (out/'SHA256SUMS.json').exists() else dict(version=VERSION,files=[]); assert old['version']==VERSION
    old['kind']='local-full-three-platforms-and-promo';old['files']=[f for f in old['files']if not f['path'].startswith('full-local/')]+[{k:v for k,v in p.items()if k in ['path','sha256','bytes']}for p in records]
    assert all(sha(out/f['path'])==f['sha256']for f in old['files']);write(out/'SHA256SUMS.json',old)
    print(json.dumps(records,ensure_ascii=False,indent=2))

if __name__=='__main__':
    assert Path('/.dockerenv').exists()and os.getuid()==1000
    {'stage-linux':stage_linux,'stage-cross':stage_cross,'inspect-mac':inspect_mac,'pack':pack}[sys.argv[1]]()
