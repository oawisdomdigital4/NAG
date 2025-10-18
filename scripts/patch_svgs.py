#!/usr/bin/env python3
"""Patch SVG files under static/admin/icons/bootstrap to ensure internal fills use currentColor.
Usage: python scripts/patch_svgs.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ICON_DIR = ROOT / 'static' / 'admin' / 'icons' / 'bootstrap'

if not ICON_DIR.exists():
    print(f"Icon directory does not exist: {ICON_DIR}")
    raise SystemExit(1)

svg_files = sorted(ICON_DIR.glob('*.svg'))
if not svg_files:
    print('No SVG files found to patch')
    raise SystemExit(1)

fill_attr_re = re.compile(r'fill\s*=\s*"(#[0-9A-Fa-f]{3,6}|[a-zA-Z0-9_\-:#()\.%, ]+)"')
style_fill_re = re.compile(r'style\s*=\s*"[^"]*fill\s*:\s*([^;"}]+)[;\"]?')

for svg in svg_files:
    s = svg.read_text(encoding='utf-8')
    original = s
    # Replace any explicit fill="..." with fill="currentColor"
    s = fill_attr_re.sub('fill="currentColor"', s)
    # Replace inline style fill:... occurrences
    s = style_fill_re.sub(lambda m: 'style="' + m.group(0).split('=',1)[1].replace(m.group(1), 'currentColor') , s)

    # Ensure <svg ...> contains fill="currentColor"
    s = re.sub(r'<svg(\s[^>]*)?>', lambda m: ("<svg" + (m.group(1) or "") + " fill=\"currentColor\">" ) if 'fill=' not in (m.group(1) or '') else m.group(0), s, count=1)

    if s != original:
        svg.write_text(s, encoding='utf-8')
        print(f'Patched {svg.name}')
    else:
        print(f'No changes for {svg.name}')

print('Done.')
