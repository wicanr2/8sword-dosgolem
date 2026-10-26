#!/usr/bin/env python3
"""053 DRAFT：從已封存PAE診斷RAM建立只供IDA分析的16-bit MZ包裝。Docker only。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000
    assert not a.out.exists() and a.out.parent.stat().st_uid == 1000
    batch = a.project/'workplace/probe-20261023/graphics-first/ending-hd-r1'
    ram = (batch/'startup-r3/ram-00000-9ffff.bin').read_bytes()
    assert len(ram) == 0xa0000 and sha(ram) == '0ccfd6a0d14ca315dc42ca8e70961e83c076f2c857509df70840402faf00ee60'
    assert sha((batch/'startup-r3/source-startup.json').read_bytes()) == '5225833719edf6393fe442c107b86ded17474a92bdcca6c599fc5b4f9fa34c84'
    # Exclude low DOS state, video RAM and relocated packer workspace.
    # The wrapper is an analysis input, never a runnable replacement.
    begin, end = 0x1100, 0xa4f0
    body = ram[begin:end]
    size = len(body)+32
    header = struct.pack('<14H', 0x5a4d, size%512, (size+511)//512, 0, 2, 0, 0xffff,
                         0x7e4-0x110, 0x33a2, 0, 0, 0, 0x1c, 0)+bytes(4)
    wrapper = header+body
    a.out.mkdir()
    (a.out/'PAE-runtime-analysis.exe').write_bytes(wrapper)
    (a.out/'runtime-linear-1100-a4ef.bin').write_bytes(body)
    report = dict(schema=1, spec='053', status='analysis-wrapper-only', production=False,
                  ram_sha256=sha(ram), runtime_begin=begin, runtime_end_exclusive=end,
                  wrapper='PAE-runtime-analysis.exe', wrapper_sha256=sha(wrapper), header_bytes=32,
                  body_sha256=sha(body), first16=body[:16].hex(), ida_load_segment=0x110,
                  query_runtime_linear=[0x1100, 0x3930+0x56a, 0x6340+0x153f, 0x4ca0+0x46],
                  address_space='dosgolem runtime linear; IDA wrapper loaded with -b110; wrapper file offset = runtime-linear - 0x1100 + 32',
                  tool_sha256=sha(Path(__file__).read_bytes()),
                  limits=['Relocated post-unpack RAM, not original PAE file offsets or an executable replacement.',
                          'Mutable data is the 20000000-step diagnostic state. Only immutable code supports later code fingerprints.'])
    (a.out/'preparation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(wrapper_sha256=report['wrapper_sha256'], bytes=size)))


if __name__ == '__main__':
    main()
