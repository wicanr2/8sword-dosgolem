#!/usr/bin/env python3
"""045：從 r43 匯入第49／54筆，完整保留基底並獨立核對草地合成。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

PMAP_SHA = "9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02"
STYLE_SHA = "2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6"
RECORDS = {
    49: dict(native="5af28dbd172be266d77a5d07af241ee6488b1f97d7e5d08ba29df2ae1f842667", record="d8858e3a2f3006a4813c4ba4cc28b4c633b85f072adad416f2f4842f179f4e39", image="347e485c9450754b28bb5f1db743a8d6aea83d51836ae8a1298e7f45919cd303", prompt="7b17151cf823ea36f0e1d6e138c622c11993656eb7c6625052f9b12f363dea94", cache="210fd08b77ac192c962a3e41e3bfd522e7f144f64b4ac4ecbbb6f85934375870"),
    54: dict(native="f57a3908342e7c2a8a5986374d745f749af596306e3d310b7633533b7909e602", record="023ad63010f68e3cb8ea140b69c8870301a787ab739f2425a53d0fd7d10cb0fc", image="328c5a99cf1758062778c7381742129f4a755af5bb0d35693084a78c7c35d7b5", prompt="5d4050ebc5704301ed88acdf271cf708b3c2773a0a4222f93f9c544c1dbfff22", cache="79b142d453644177050a596082bcbc2607e9e48b3dfebb07e9f7981e686e7706"),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("base", "original", "art", "out", "cache-out"):
        parser.add_argument("--"+name, type=Path, required=True)
    a = parser.parse_args()
    assert not a.out.exists() and not a.cache_out.exists()
    base = {p.name: sha(p) for p in a.base.iterdir() if p.is_file()}
    assert len(base) == len(list(a.base.iterdir())) == 197
    raw = (a.original/"PMAP.AY").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PMAP_SHA
    spec = importlib.util.spec_from_file_location("landmarks_sampling", Path(__file__).with_name("audit-encounter-gui.py"))
    sampling = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sampling)
    model = sampling.Model(a.base, a.original, a.cache_out)
    prepared = []
    for index, source in RECORDS.items():
        record = raw[index*1004:(index+1)*1004]
        assert hashlib.sha256(record).hexdigest() == source["record"]
        assert hashlib.sha256(record[:804]).hexdigest() == source["native"]
        image = a.art/f"pmap-{index}-painted-r1.png"
        prompt = a.art/f"pmap-{index}-painted-r1.prompt.txt"
        assert sha(image) == source["image"] and sha(prompt) == source["prompt"]
        tile = sampling.sample(image, 192, 150, actor=True, background=model.material(1)[0])
        assert hashlib.sha256(tile).hexdigest() == source["cache"]
        prepared.append((index, source, image, prompt, tile))
    a.out.mkdir()
    a.cache_out.mkdir()
    for name in base:
        shutil.copyfile(a.base/name, a.out/name)
    for index, source, image, prompt, tile in prepared:
        filename = f"map-landmark-{index}-r1.png"
        shutil.copyfile(image, a.out/filename)
        shutil.copyfile(prompt, a.out/f"map-landmark-{index}-r1.prompt.txt")
        manifest = dict(schema=1, source_file="PMAP.AY", source_sha256=PMAP_SHA, style_reference_sha256=STYLE_SHA,
                        source_index=index, native_sha256=source["native"], record_sha256=source["record"], cache_sha256=source["cache"],
                        grass_source=0, sampling="bilinear-full-alpha-over-grass",
                        image=dict(file=filename, sha256=source["image"], width=1419, height=1108))
        provenance = dict(schema=1, tool="built-in image_gen", source_sha256=PMAP_SHA, source_index=index,
                          image_sha256=source["image"], prompt_sha256=source["prompt"], cache_sha256=source["cache"],
                          style_reference_sha256=STYLE_SHA, generation_style_sha256="744a39bb04c869803c0583604ac3c5c0481e174ad3153c4a8489f1219ad50a97",
                          rights="local-only original-derived; no public distribution grant",
                          approval="existing B style; no individual image approval claimed", base_sha256=base)
        for name, value in [(f"map-landmark-{index}.json", manifest), (f"map-landmark-{index}-provenance.json", provenance)]:
            (a.out/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n")
        (a.cache_out/f"landmark-{index}.rgba").write_bytes(tile)
    assert len(list(a.out.iterdir())) == 205
    assert all(sha(a.out/name) == digest for name, digest in base.items())
    print(json.dumps(dict(files=205, base_files_preserved=197, independent_caches=2)))


if __name__ == "__main__":
    main()
