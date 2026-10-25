#!/usr/bin/env python3
"""049：只將已核對的縮小素材總覽與來源清單保存到README圖像目錄。"""
import argparse
import hashlib
import json
import os
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('registration', 'audit', 'promotion', 'out'):
        p.add_argument('--' + key, type=Path, required=True)
    a = p.parse_args()
    assert Path('/.dockerenv').is_file() and os.getuid() == 1000
    assert a.out.is_dir() and a.out.stat().st_uid == 1000
    reg = json.loads((a.registration / 'registration.json').read_text())
    audit, promotion = json.loads(a.audit.read_text()), json.loads(a.promotion.read_text())
    assert audit['status'] == 'PASS-scoped-049-map-encounter-batch'
    assert promotion['status'] == 'promoted-scoped-049-map-encounters' and promotion['audit_sha256'] == sha(a.audit)
    assert sha(a.registration / 'registration.json') == audit['registration_sha256']
    image = a.registration / 'comparison.png'
    assert sha(image) == reg['comparison_sha256']
    target = a.out / 'map-encounters-original-hd-r1.png'
    record = a.out / 'map-encounters-original-hd-r1.json'
    assert not target.exists() and not record.exists()
    with target.open('xb') as f:
        f.write(image.read_bytes())
    report = dict(schema=1, status='registered-asset-overview-not-natural-encounter-screenshots',
                  image=target.name, image_sha256=sha(target), source='ENEMY.AY', source_sha256=reg['source_sha256'],
                  records=14, groups=[dict(record=g['record'], manifest_sha256=g['manifest_sha256'],
                                          image=g['config']['image'], origin=g['origin']) for g in reg['groups']],
                  audit_sha256=sha(a.audit), promotion_sha256=sha(a.promotion),
                  registration_sha256=sha(a.registration / 'registration.json'), tool_sha256=sha(Path(__file__)),
                  rights='user-requested compact comparison in existing private repository only; full assets remain local')
    with record.open('x') as f:
        f.write(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(image=target.name, records=14, bytes=target.stat().st_size)))


if __name__ == '__main__':
    main()
