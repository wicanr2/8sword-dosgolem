#!/usr/bin/env python3
"""056：Linux 或三目標交叉建置。由 rust-package.sh 在 Docker 呼叫。"""
import os, subprocess, sys
from pathlib import Path
from rust_package_settings import VERSION

def main():
    assert Path('/.dockerenv').exists() and os.getuid() == 1000
    q = Path('/q'); env = dict(os.environ, EIGHTSWORD_BUILD_VERSION=VERSION)
    def run(cmd, name, **kw):
        with (q/'logs'/name).open('w') as log:
            subprocess.run(cmd, check=True, env=env, cwd='/crate', stdout=log, stderr=subprocess.STDOUT, **kw)
    if sys.argv[1] == 'linux':
        env['CARGO_TARGET_DIR'] = '/q/build/linux'
        env['RUSTFLAGS'] = '-C link-arg=-Wl,--disable-new-dtags,-rpath,$ORIGIN/lib'
        run(['cargo', 'fmt', '--all', '--check'], 'format.log')
        run(['cargo', 'test', '--offline', '--locked', '--features', 'desktop'], 'linux-test.log')
        run(['cargo', 'build', '--offline', '--locked', '--release', '--features', 'desktop'], 'linux-build.log')
        run(['/q/build/linux/release/8sword-remake', '--self-check'], 'linux-self-check.log')
        return
    for label, target, linker in [
        ('windows', 'x86_64-pc-windows-gnu', '/usr/bin/x86_64-w64-mingw32-gcc'),
        ('mac-x86_64', 'x86_64-apple-darwin', '/osxcross/bin/o64-clang'),
        ('mac-arm64', 'aarch64-apple-darwin', '/osxcross/bin/oa64-clang'),
    ]:
        env['CARGO_TARGET_DIR'] = '/q/build/cross'
        env['CARGO_TARGET_' + target.upper().replace('-', '_') + '_LINKER'] = linker
        env['MACOSX_DEPLOYMENT_TARGET'] = '11.0'
        libs = '/opt/sdl2/windows/x86_64-w64-mingw32/lib' if label == 'windows' else '/q/deps/mac-common'
        if label != 'windows':
            common = q/'deps/mac-common'; common.mkdir(exist_ok=True)
            import shutil
            sdl = common/'libSDL2.dylib'
            if not sdl.exists():
                shutil.copy2('/opt/sdl2/macos/lib/libSDL2.dylib', sdl)
                subprocess.run(['/osxcross/bin/x86_64-apple-darwin24.5-install_name_tool', '-id', '@rpath/libSDL2.dylib', str(sdl)], check=True)
        env['RUSTFLAGS'] = f'-L native=/q/deps/{label}/lib -L native={libs}'
        if label != 'windows': env['RUSTFLAGS'] += ' -C link-arg=-Wl,-rpath,@executable_path/../Frameworks'
        run(['cargo', 'build', '--offline', '--locked', '--release', '--features', 'desktop', '--target', target], label+'-build.log')
        if label == 'windows':
            run(['cargo', 'test', '--offline', '--locked', '--features', 'desktop', '--target', target, '--no-run'], 'windows-test-build.log')
        print(label, 'Rust built', flush=True)

if __name__ == '__main__': main()
