#!/usr/bin/env python3
"""047 DRAFT：建立獨立Go字形接管研究副本，不修改正式來源。"""
import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--intro-masked', action='store_true')
    p.add_argument('--reveal', action='store_true')
    p.add_argument('--compat-probe', action='store_true')
    p.add_argument('--compat-native', action='store_true')
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    a.out.mkdir()
    for name in ['go.mod', 'go.sum']:
        shutil.copyfile(a.project/name, a.out/name)
    shutil.copytree(a.project/'internal', a.out/'internal')
    for name in ['research-render-pages.go', 'research-render-pages_test.go',
                 'research-render-bitmap-rows.go', 'research-render-bitmap-rows_test.go']:
        production = a.project/'internal/eightsword'/name.replace('research-render-', 'source_').replace('-', '_')
        if production.is_file():
            continue
        src = a.project/'tools'/name
        text = src.read_text()
        assert text.startswith('//go:build ignore\n\n')
        (a.out/'internal/eightsword'/name.removeprefix('research-')).write_text(text.removeprefix('//go:build ignore\n\n'))
    target = a.out/'internal/eightsword/source_presentation.go'
    text = target.read_text()
    old = '\te.sourceInstall = func() {\n'
    assert text.count(old) == 1
    if 'pageInstall := e.sourcePageInstall()' not in text:
        text = text.replace(old, '\tpageInstall := e.sourcePageInstall()\n'+old+'\t\tpageInstall()\n')
    target.write_text(text)
    if a.intro_masked and not (a.project/'internal/eightsword/source_intro_masked.go').is_file():
        for name in ['research-intro-masked.go', 'research-intro-masked_test.go']:
            text = (a.project/'tools'/name).read_text()
            assert text.startswith('//go:build ignore\n\n')
            (a.out/'internal/eightsword'/name.removeprefix('research-')).write_text(text.removeprefix('//go:build ignore\n\n'))
        target = a.out/'internal/eightsword/engine.go'
        text = target.read_text()
        old = '\tsourceDirectCalls    uint64\n'
        assert text.count(old) == 1
        target.write_text(text.replace(old, old+'\tsourceIntroMaskCalls uint64\n'))
        target = a.out/'internal/eightsword/source_presentation.go'
        text = target.read_text()
        old = '\te.sourceInstall = func() {\n'
        assert text.count(old) == 1
        target.write_text(text.replace(old, '\tintroMaskedInstall := e.sourceIntroMaskedInstall()\n'+old+'\t\tintroMaskedInstall()\n'))
        for file, row in [('source_masked.go',False),('source_masked_rows.go',True)]:
            target = a.out/'internal/eightsword'/file
            text = target.read_text()
            point = 'background := entry == '+('0x6a3' if row else '0x626')
            old = '\t'+point+'\n\tif background {'
            at = '0x533d' if row else '0x52c0'
            extra = ('sourceEntry, sourceEnd = entry-0x7d, entry-0x7d+0x133\n'
                     '\t\tend,readSite,writeSite = entry+0x11,entry+0xb,entry+0xe' if row else
                     'ret,readSite,writeSite = entry+0x133,entry+0x88,entry+0x8b')
            new = ('\tmodeOff,destOff,rowTable := uint32(0x7484),uint32(0x748a),uint32(6)\n'
                   '\t'+point+'\n'
                   '\tif uint32(s[dg.CS])*16+uint32(entry)=='+at+' {\n'
                   '\t\t'+extra+'\n\t\twant=introMaskedCodeSHA\n'
                   '\t\tmodeOff,destOff,rowTable=0x1ef2,0x1ef8,4\n'
                   '\t} else if background {')
            assert text.count(old) == 1
            text = text.replace(old,new)
            for base in ['control' if row else 'ds']:
                text = text.replace(base+'+0x748c',base+'+destOff+2')
                text = text.replace(base+'+0x7484',base+'+modeOff')
                text = text.replace(base+' + 0x748a',base+' + destOff')
            assert text.count('code+6+uint32') == 1
            text = text.replace('code+6+uint32','code+rowTable+uint32')
            target.write_text(text)
    if a.reveal and not (a.project/'internal/eightsword/source_reveal.go').is_file():
        for name in ['research-reveal-native.go', 'research-reveal-native_test.go']:
            text = (a.project/'tools'/name).read_text()
            assert text.startswith('//go:build ignore\n\n')
            (a.out/'internal/eightsword'/name.removeprefix('research-')).write_text(text.removeprefix('//go:build ignore\n\n'))
        target = a.out/'internal/eightsword/engine.go'
        text = target.read_text()
        old = '\tsourceDirectCalls    uint64\n'
        assert text.count(old) == 1
        target.write_text(text.replace(old,old+'\tsourceRevealSubmit func([]sourceRevealPixel)\n\tsourceRevealTiles, sourceRevealPoints, sourceRevealAtomic, sourceRevealPixels uint64\n'))
        target = a.out/'internal/eightsword/source_intro.go'
        text = target.read_text()
        old = '\tp.bound = true\n'
        assert text.count(old) == 1
        target.write_text(text.replace(old,old+'\tp.e.sourceRevealSubmit = p.submitRevealSpan\n'))
        target = a.out/'internal/eightsword/source_presentation.go'
        text = target.read_text()
        old = '\te.sourceInstall = func() {\n'
        assert text.count(old) == 1
        target.write_text(text.replace(old,'\trevealInstall := e.sourceRevealInstall()\n'+old+'\t\trevealInstall()\n'))
    if a.compat_probe or a.compat_native:
        src = a.project/'tools/research-compat-pixels_test.go'
        text = src.read_text()
        assert text.startswith('//go:build ignore\n\n')
        (a.out/'internal/eightsword/compat-pixels_test.go').write_text(text.removeprefix('//go:build ignore\n\n'))
    if a.compat_native and not (a.project/'internal/eightsword/source_compat.go').is_file():
        for name in ['research-compat-native.go', 'research-compat-native_test.go']:
            text = (a.project/'tools'/name).read_text()
            assert text.startswith('//go:build ignore\n\n')
            (a.out/'internal/eightsword'/name.removeprefix('research-')).write_text(text.removeprefix('//go:build ignore\n\n'))
        target = a.out/'internal/eightsword/engine.go'
        text = target.read_text()
        old = 'type Engine struct {\n'
        assert text.count(old) == 1
        target.write_text(text.replace(old,old+'\tsourceCompatReads, sourceCompatWrites, sourceCompatRestores uint64\n'))
        target = a.out/'internal/eightsword/source_presentation.go'
        text = target.read_text()
        old = '\te.sourceInstall = func() {\n'
        assert text.count(old) == 1
        target.write_text(text.replace(old,'\tcompatInstall := e.sourceCompatInstall()\n'+old+'\t\tcompatInstall()\n'))
    result = dict(schema=1, spec='047', production=False, tool_sha256=sha(Path(__file__)),
                  files={str(p.relative_to(a.out)):sha(p) for p in a.out.rglob('*') if p.is_file()})
    (a.out/'preparation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(status='prepared', files=len(result['files']))))


if __name__ == '__main__':
    main()
