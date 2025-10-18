#!/usr/bin/env python3
"""Convert SVG icons in static/admin/icons/bootstrap to PNGs in static/admin/icons/png.

Requires: cairosvg (pip install cairosvg)
Usage: python scripts/convert_svgs_to_pngs.py
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
SVG_DIR = ROOT / 'static' / 'admin' / 'icons' / 'bootstrap'
PNG_DIR = ROOT / 'static' / 'admin' / 'icons' / 'png'

if not SVG_DIR.exists():
    print(f"SVG dir not found: {SVG_DIR}")
    sys.exit(1)

PNG_DIR.mkdir(parents=True, exist_ok=True)

try:
    import cairosvg
except Exception as e:
    print("cairosvg is required to convert SVG to PNG. Install with: pip install cairosvg")
    raise

count = 0
for svg in SVG_DIR.glob('*.svg'):
    out = PNG_DIR / (svg.stem + '.png')
    try:
        cairosvg.svg2png(url=str(svg), write_to=str(out), output_width=64, output_height=64)
        print(f'Wrote {out}')
        count += 1
    except Exception as e:
        print(f'Failed to convert {svg}: {e}')

print(f'Done. Converted {count} files.')
