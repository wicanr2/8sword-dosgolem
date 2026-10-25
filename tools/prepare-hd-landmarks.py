#!/usr/bin/env python3
"""045：匯入第48、49／54或52／56筆，保留基底並獨立核對草地合成。Docker only。"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

PMAP_SHA = "9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02"
STYLE_SHA = "2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6"
RECORDS = {
    48: dict(native="8faa16d2679f1bad38deefebd4615cb1491b7ae17f8cc472ee5e38562ac587a4", record="e0b751a64138af9343d01b6831271bf328e854ac761491bb00000e1f1570d975", image="d5f29bde62da0724e2a486f0b5f61dfd676c26e6fcf3751a17d679bca412ffc1", prompt="6017520959477aa58a8695f468a8bb10cc39d1f56f25b022da94a1a324ad6f45", cache="62d3072d49922f2a73f9cdce83f91f53e1f65b8f38aa51e5eacb9f1309102d49"),
    49: dict(native="5af28dbd172be266d77a5d07af241ee6488b1f97d7e5d08ba29df2ae1f842667", record="d8858e3a2f3006a4813c4ba4cc28b4c633b85f072adad416f2f4842f179f4e39", image="347e485c9450754b28bb5f1db743a8d6aea83d51836ae8a1298e7f45919cd303", prompt="7b17151cf823ea36f0e1d6e138c622c11993656eb7c6625052f9b12f363dea94", cache="210fd08b77ac192c962a3e41e3bfd522e7f144f64b4ac4ecbbb6f85934375870"),
    54: dict(native="f57a3908342e7c2a8a5986374d745f749af596306e3d310b7633533b7909e602", record="023ad63010f68e3cb8ea140b69c8870301a787ab739f2425a53d0fd7d10cb0fc", image="328c5a99cf1758062778c7381742129f4a755af5bb0d35693084a78c7c35d7b5", prompt="5d4050ebc5704301ed88acdf271cf708b3c2773a0a4222f93f9c544c1dbfff22", cache="79b142d453644177050a596082bcbc2607e9e48b3dfebb07e9f7981e686e7706"),
    52: dict(native='e6b6adc005119cfcdf87cfe55cfe601f967a22b4f8796232c33733a65cd3f146', record='28988f39adf2e0b5835163e413b63fc1f550dcfdc3097538143e028f5424018d', image='bfa21fb69c92918d2a27380077153377dbba5d5d84f1a3d1dac6c7ab85fc7e83', prompt='e20995cda826aa2192c23e9f6666e061d3d678ffd8f5ce18ade488258da1765d', cache='8147efffe2e0f26f26295391bdd1b2a3e5db621539ee55cc65ed2b48c9e2a6c8'),
    56: dict(native='c94b51a07f43d19768b4bc6b0d6c1ef57154f1be4d0024470bc8dc3755e420b6', record='74d93a7872784953e405930f6046b04e326939dc9e0b8be488936f82a7ea218d', image='7188d67ebf710df40d2adfcaa520d21c1f9781008748a214a497629c2b0a542d', prompt='26e77d40d3b0759102cb961146c23f01d00f55677ef2daae03a56802265ecd52', cache='412af4cb89b40adc1b0b56b2b5605fd016918b51712a081a4cea01938d0e9fd4'),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("base", "original", "art", "out", "cache-out"):
        parser.add_argument("--"+name, type=Path, required=True)
    parser.add_argument("--group",choices=["48","49-54","52-56"],default="49-54")
    a = parser.parse_args()
    indices, base_count = {"48":([48],213),"49-54":([49,54],197),"52-56":([52,56],205)}[a.group]
    assert not a.out.exists() and not a.cache_out.exists()
    base = {p.name: sha(p) for p in a.base.iterdir() if p.is_file()}
    assert len(base) == len(list(a.base.iterdir())) == base_count
    raw = (a.original/"PMAP.AY").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PMAP_SHA
    spec = importlib.util.spec_from_file_location("landmarks_sampling", Path(__file__).with_name("audit-encounter-gui.py"))
    sampling = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sampling)
    model = sampling.Model(a.base, a.original, a.cache_out)
    prepared = []
    for index in indices:
        source=RECORDS[index]
        record = raw[index*1004:(index+1)*1004]
        assert hashlib.sha256(record).hexdigest() == source["record"]
        assert hashlib.sha256(record[:804]).hexdigest() == source["native"]
        image = a.art/f"pmap-{index}-painted-r{2 if index == 48 else 1}.png"
        prompt = a.art/"pmap-48-prompts-complete-r2.txt" if index == 48 else a.art/f"pmap-{index}-painted-r1.prompt.txt"
        assert sha(image) == source["image"] and sha(prompt) == source["prompt"]
        tile = sampling.sample(image, 192, 150, actor=True, background=model.material(1)[0])
        assert hashlib.sha256(tile).hexdigest() == source["cache"]
        prepared.append((index, source, image, prompt, tile))
    a.out.mkdir()
    a.cache_out.mkdir()
    for name in base:
        shutil.copyfile(a.base/name, a.out/name)
    for index, source, image, prompt, tile in prepared:
        revision = 2 if index == 48 else 1
        filename = f"map-landmark-{index}-r{revision}.png"
        shutil.copyfile(image, a.out/filename)
        shutil.copyfile(prompt, a.out/f"map-landmark-{index}-r{revision}.prompt.txt")
        manifest = dict(schema=1, source_file="PMAP.AY", source_sha256=PMAP_SHA, style_reference_sha256=STYLE_SHA,
                        source_index=index, native_sha256=source["native"], record_sha256=source["record"], cache_sha256=source["cache"],
                        grass_source=0, sampling="bilinear-full-alpha-over-grass",
                        image=dict(file=filename, sha256=source["image"], width=1419, height=1108))
        provenance = dict(schema=1, tool="built-in image_gen", source_sha256=PMAP_SHA, source_index=index,
                          image_sha256=source["image"], prompt_sha256=source["prompt"], cache_sha256=source["cache"],
                          style_reference_sha256=STYLE_SHA, generation_style_sha256="744a39bb04c869803c0583604ac3c5c0481e174ad3153c4a8489f1219ad50a97",
                          rights="local-only original-derived; no public distribution grant",
                          approval="existing B style; no individual image approval claimed", base_sha256=base)
        if index == 48:
            provenance["generation_style_sha256"] = "347e485c9450754b28bb5f1db743a8d6aea83d51836ae8a1298e7f45919cd303"
            provenance["prompt_chain"] = "initial generation and position refinement; complete prompts preserved"
            provenance["local_art_provenance_sha256"] = sha(a.art/"pmap-48-art-provenance-r2.json")
        for name, value in [(f"map-landmark-{index}.json", manifest), (f"map-landmark-{index}-provenance.json", provenance)]:
            (a.out/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n")
        (a.cache_out/f"landmark-{index}.rgba").write_bytes(tile)
    assert len(list(a.out.iterdir())) == base_count+4*len(indices)
    assert all(sha(a.out/name) == digest for name, digest in base.items())
    print(json.dumps(dict(files=base_count+4*len(indices), base_files_preserved=base_count, independent_caches=len(indices))))


if __name__ == "__main__":
    main()
