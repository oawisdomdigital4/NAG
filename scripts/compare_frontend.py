import os
from pathlib import Path

root = Path('c:/Users/HP/NAG BACKEND/myproject')
prototype = root / 'frontend' / 'prototype src'
src = root / 'frontend' / 'src'

proto_files = set()
for p in prototype.rglob('*'):
    if p.is_file():
        rel = p.relative_to(prototype).as_posix()
        proto_files.add(rel)

src_files = set()
for p in src.rglob('*'):
    if p.is_file():
        rel = p.relative_to(src).as_posix()
        src_files.add(rel)

only_in_proto = sorted(proto_files - src_files)
only_in_src = sorted(src_files - proto_files)

print('Files only in prototype (relative to prototype src):')
for f in only_in_proto:
    print('  ', f)

print('\nFiles only in src (relative to src):')
for f in only_in_src:
    print('  ', f)
