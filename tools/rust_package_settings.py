"""Shared defaults and strict identifiers for the local packaging tools."""
import os
import re
from pathlib import Path

defaults = dict(line.split('=', 1) for line in Path(__file__).with_name('rust-package-defaults.env').read_text().splitlines() if line)
VERSION = os.environ.get('EIGHTSWORD_PACKAGE_VERSION', defaults['EIGHTSWORD_DEFAULT_VERSION'])
BATCH = os.environ.get('EIGHTSWORD_PACKAGE_BATCH', defaults['EIGHTSWORD_DEFAULT_BATCH'])
if not re.fullmatch(r'v\.[0-9]+\.[0-9]+\.[0-9]+-[0-9]{8}', VERSION):
    raise ValueError('封包版號不符契約')
if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', BATCH):
    raise ValueError('封包工作批次無效')
REL = 'workplace/probe-20261023/graphics-first/battle-r1/' + BATCH
AUDIT = BATCH.removesuffix('-r1') + '-audit-r1.json'
