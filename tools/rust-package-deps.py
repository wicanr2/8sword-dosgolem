#!/usr/bin/env python3
"""056：只在固定交叉工具鏈容器執行；來源下載後離線建置。"""
import hashlib, os, subprocess, sys, tarfile
from pathlib import Path

SOURCES = {
    "libogg-1.3.5": ("https://downloads.xiph.org/releases/ogg/libogg-1.3.5.tar.xz", "c4d91be36fc8e54deae7575241e03f4211eb102afb3fc0775fbbc1b740016705"),
    "libvorbis-1.3.7": ("https://downloads.xiph.org/releases/vorbis/libvorbis-1.3.7.tar.xz", "b33cc4934322bcbf6efcbacf49e3ca01aadbea4114ec9589d1b1e9d20f72954b"),
    "flac-1.4.3": ("https://downloads.xiph.org/releases/flac/flac-1.4.3.tar.xz", "6c58e69cd22348f441b861092b825e591d0b822e106de6eb0ee4d05d27205b70"),
    "opus-1.5.2": ("https://downloads.xiph.org/releases/opus/opus-1.5.2.tar.gz", "65c1d2f78b9f2fb20082c38cbe47c951ad5839345876e46941612ee87f9a7ce1"),
    "libsndfile-1.2.2": ("https://github.com/libsndfile/libsndfile/releases/download/1.2.2/libsndfile-1.2.2.tar.xz", "3799ca9924d3125038880367bf1468e53a1b7e3686a934f098b7e1d286cdb80e"),
}
EXTRAS = {
    'NotoSansCJK-LICENSE.txt': ('https://raw.githubusercontent.com/notofonts/noto-cjk/Sans2.004/LICENSE', '6a73f9541c2de74158c0e7cf6b0a58ef774f5a780bf191f2d7ec9cc53efe2bf2'),
    'NotoSerifCJK-LICENSE.txt': ('https://raw.githubusercontent.com/notofonts/noto-cjk/Serif2.003/Serif/LICENSE', '6a73f9541c2de74158c0e7cf6b0a58ef774f5a780bf191f2d7ec9cc53efe2bf2'),
    'apple-codesign-0.29.0-x86_64-unknown-linux-musl.tar.gz': ('https://github.com/indygreg/apple-platform-rs/releases/download/apple-codesign%2F0.29.0/apple-codesign-0.29.0-x86_64-unknown-linux-musl.tar.gz', 'dbe85cedd8ee4217b64e9a0e4c2aef92ab8bcaaa41f20bde99781ff02e600002'),
}

def run(cmd, log):
    subprocess.run(cmd, check=True, stdout=log, stderr=subprocess.STDOUT)

def main():
    assert Path('/.dockerenv').exists() and os.getuid() == 1000
    q = Path('/q')
    for name, (url, digest) in EXTRAS.items():
        p = q/'sources'/name
        if '--fetch' in sys.argv:
            subprocess.run(['curl', '-fL', '--retry', '2', '-o', str(p), url], check=True)
        assert hashlib.sha256(p.read_bytes()).hexdigest() == digest
        if name.endswith('.tar.gz') and not (q/'sources'/name[:-7]).exists():
            with tarfile.open(p) as t: t.extractall(q/'sources', filter='data')
    for name, (url, sha) in SOURCES.items():
        archive = q/'sources'/url.rsplit('/', 1)[1]
        if '--fetch' in sys.argv:
            subprocess.run(['curl', '-fL', '--retry', '2', '-o', str(archive), url], check=True)
        assert hashlib.sha256(archive.read_bytes()).hexdigest() == sha, archive
        if not (q/'sources'/name).exists():
            with tarfile.open(archive) as t: t.extractall(q/'sources', filter='data')
    if '--fetch' in sys.argv: return
    for target in sys.argv[1:] or ['windows', 'mac-x86_64', 'mac-arm64']:
        prefix = q/'deps'/target
        prefix.mkdir(exist_ok=True)
        common = ['-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_POSITION_INDEPENDENT_CODE=ON',
                  f'-DCMAKE_INSTALL_PREFIX={prefix}', f'-DCMAKE_PREFIX_PATH={prefix}',
                  '-DBUILD_TESTING=OFF', '-DBUILD_EXAMPLES=OFF', '-DBUILD_PROGRAMS=OFF',
                  '-DINSTALL_DOCS=OFF', '-DCMAKE_INSTALL_LIBDIR=lib', '-DPKG_CONFIG_EXECUTABLE=/bin/false',
                  '-DBUILD_CXXLIBS=OFF', '-DBUILD_UTILS=OFF', '-DBUILD_DOCS=OFF',
                  '-DBUILD_PROGRAMS=OFF', '-DOPUS_BUILD_PROGRAMS=OFF', '-DOPUS_BUILD_TESTING=OFF']
        if target == 'windows':
            common += ['-DCMAKE_SYSTEM_NAME=Windows', '-DCMAKE_C_COMPILER=x86_64-w64-mingw32-gcc',
                       # C-only codecs still declare CXX; use the installed Clang
                       # frontend without requiring an unused C++ standard library.
                       '-DCMAKE_CXX_COMPILER=/usr/bin/clang++',
                       '-DCMAKE_CXX_COMPILER_TARGET=x86_64-w64-windows-gnu',
                       '-DCMAKE_CXX_FLAGS=-nostdlib++ -L/usr/lib/gcc/x86_64-w64-mingw32/14-posix',
                       '-DCMAKE_RC_COMPILER=x86_64-w64-mingw32-windres',
                       '-DCMAKE_SHARED_LINKER_FLAGS=-static-libgcc']
        else:
            arch = 'x86_64' if target == 'mac-x86_64' else 'arm64'
            cc = 'o64-clang' if arch == 'x86_64' else 'oa64-clang'
            common += ['-DCMAKE_SYSTEM_NAME=Darwin', f'-DCMAKE_C_COMPILER=/osxcross/bin/{cc}',
                       '-DCMAKE_AR=/osxcross/bin/x86_64-apple-darwin24.5-ar',
                       '-DCMAKE_RANLIB=/osxcross/bin/x86_64-apple-darwin24.5-ranlib',
                       '-DCMAKE_C_CREATE_STATIC_LIBRARY=/osxcross/bin/x86_64-apple-darwin24.5-libtool -static -o <TARGET> <OBJECTS>',
                       f'-DCMAKE_CXX_COMPILER=/osxcross/bin/{cc}++',
                       f'-DCMAKE_OSX_ARCHITECTURES={arch}', '-DCMAKE_OSX_DEPLOYMENT_TARGET=11.0',
                       '-DCMAKE_OSX_SYSROOT=/osxcross/SDK/MacOSX15.5.sdk', '-DCMAKE_INSTALL_NAME_DIR=@rpath']
        with (q/'logs'/f'deps-{target}.log').open('w') as log:
            for name in SOURCES:
                build = q/'build'/f'{target}-{name}'
                extra = ['-DBUILD_SHARED_LIBS=OFF']
                if name.startswith('libsndfile'):
                    extra = ['-DBUILD_SHARED_LIBS=ON', '-DENABLE_EXTERNAL_LIBS=ON', '-DENABLE_MPEG=OFF',
                             '-DENABLE_CPACK=OFF', '-DENABLE_PACKAGE_CONFIG=OFF',
                             '-DCMAKE_DISABLE_FIND_PACKAGE_FLAC=OFF', '-DCMAKE_DISABLE_FIND_PACKAGE_Opus=OFF',
                             '-DCMAKE_DISABLE_FIND_PACKAGE_ALSA=ON', '-DCMAKE_DISABLE_FIND_PACKAGE_Sndio=ON',
                             f'-DOGG_INCLUDE_DIR={prefix}/include', f'-DOGG_LIBRARY={prefix}/lib/libogg.a']
                    if target == 'windows': extra += ['-DCMAKE_C_FLAGS=-DFLAC__NO_DLL']
                run(['cmake', '-G', 'Ninja', '-S', str(q/'sources'/name), '-B', str(build), *common, *extra], log)
                run(['cmake', '--build', str(build), '-j2'], log)
                run(['cmake', '--install', str(build)], log)
                print(target, name, 'installed', flush=True)

if __name__ == '__main__': main()
