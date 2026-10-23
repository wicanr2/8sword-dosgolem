#!/usr/bin/env python3
"""Import the approved local MINT candidate; preserve the existing image pack.

Contract: docs/spec/008-music-events-and-playback.md. All inputs are read-only.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--music", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    assert args.base.is_dir() and args.base.stat().st_uid == 1000
    assert args.out.is_dir() and args.out.stat().st_uid == 1000
    assert not any(args.out.iterdir()), "拒絕覆寫既有素材組"
    assert (args.base/"font.json").is_file()
    assert (args.base/"terrain.json").is_file()
    approved = "4012e14dc7d03c017a532c5c56655794a03a62f395972c026273a2ec99fcbc91"
    assert sha(args.music) == approved, "來源不是已批准的修正版候選"
    before = {str(p.relative_to(args.base)): sha(p) for p in args.base.rglob("*") if p.is_file()}
    assert "music.json" not in before, "基底已含音樂，請先審查來源"
    shutil.copytree(args.base, args.out, dirs_exist_ok=True)
    target = args.out/"music-mint-plucked-flute-r2.ogg"
    shutil.copyfile(args.music, target)
    cue = dict(id=1, title="幻", score_sha256="1c5ba39af1d9d4ca4c0648182a4a5f2295cf4a4eed7c9da888d11d0ab40ed900",
               bank_sha256="663d8ad480ce03883ad66262bb586cc8716a1a7b5a690d04a0f1cb26fde903df",
               file=target.name, sha256=approved, sample_rate=48000, channels=2,
               frames=4108980, loop_start_frame=0, loop_end_frame=4108980,
               rights="original-derived-local")
    catalog = dict(schema=1, pam_sha256="83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0", cues=[cue])
    (args.out/"music.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2)+"\n")
    metadata_dir = args.music.parent
    notice = metadata_dir/"soundfont-copyright.txt"
    assert notice.is_file(), "缺少音源庫授權紀錄"
    shutil.copyfile(notice, args.out/"music-soundfont-NOTICE.txt")
    assert all(sha(args.out/name) == digest for name,digest in before.items())
    assert all(p.stat().st_uid == 1000 for p in args.out.rglob("*"))
    provenance = dict(base_files=before, imported_audio_sha256=sha(target),
                      catalog_sha256=sha(args.out/"music.json"), source="approved B MINT r2",
                      production= json.loads((metadata_dir/"b-approved-full-loop-r2.json").read_text()),
                      toolchain=json.loads((metadata_dir/"render-toolchain.json").read_text()),
                      soundfont_notice_sha256=sha(notice),
                      rights="local-only original-derived music; no Git/public distribution")
    (args.out/"music-import.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(dict(preserved_files=len(before), cues=1, catalog_sha256=provenance["catalog_sha256"])))


if __name__ == "__main__":
    main()
