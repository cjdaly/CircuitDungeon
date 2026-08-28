#!/usr/bin/env python3
"""Chapter 7 tile build pipeline - resolves bead cd-e17.4.

Assembles the four category sheets from their sources into palette-indexed
8-bit BMPs (index 0 transparent), deterministic and re-runnable, desktop-only.

    terrain.bmp    <- art/terrain.py    (procedural,     cd-e17.5)
    creatures.bmp  <- art/creatures.py  (hand-authored,  cd-e17.7)
    heroes.bmp     <- art/heroes.py     (hand-authored,  cd-e17.6)
    objects.bmp    <- art/objects.py    (hand-authored,  cd-e17.8)

Also writes game/tiles/tiles.json (tile index <-> name manifest for the
engine) and, with --preview, the off-device review artifacts (cd-e17.12):

    doc/preview/<sheet>.png    8x labelled contact sheet, committed
    doc/preview/tiles.html     zoom-toggle review page (2x / 4x / 8x / 12x)

Usage:
    python3 Chapter_7/tools/build_tiles.py            # build BMPs + manifest
    python3 Chapter_7/tools/build_tiles.py --preview  # + preview artifacts
    python3 Chapter_7/tools/build_tiles.py --preview --open
"""
from __future__ import annotations

import argparse
import base64
import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tilelib import (  # noqa: E402
    PREVIEW_DIR, TILE, TILES_DIR, Palette, Sheet, to_rgba,
    write_bmp, write_manifest,
)
from art import creatures, heroes, objects, terrain  # noqa: E402

# sheet name -> (source module, sheet columns)
SHEETS = [
    ("terrain", terrain, 8),
    ("creatures", creatures, 8),
    ("heroes", heroes, 8),
    ("objects", objects, 8),
]

PREVIEW_SCALE = 8
ZOOMS = (2, 4, 8, 12)


def _font(size):
    for p in ("/System/Library/Fonts/Supplemental/Arial.ttf",
              "/Library/Fonts/Arial.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def build_sheets(pal: Palette) -> list[Sheet]:
    sheets = []
    for name, mod, cols in SHEETS:
        tiles = mod.build(pal)
        sheets.append(Sheet(name, tiles, cols))
    return sheets


# --------------------------------------------------------------------------- #
# previews
# --------------------------------------------------------------------------- #
CHECKER = ((90, 90, 96), (60, 60, 66))


def _composite(rgba: np.ndarray, dark: bool) -> Image.Image:
    bg = (34, 34, 38) if dark else (208, 208, 202)
    base = Image.new("RGB", rgba.shape[1::-1], bg)
    base.paste(Image.fromarray(rgba, "RGBA"), (0, 0),
               Image.fromarray(rgba[:, :, 3], "L"))
    return base


def contact_sheet(sheet: Sheet, pal: Palette, scale=PREVIEW_SCALE) -> Image.Image:
    cols, rows = sheet.cols, sheet.rows
    cell = TILE * scale
    gap = 12
    lab = 20
    margin = 16
    W = margin * 2 + cols * (cell + gap) - gap
    H = margin * 2 + 24 + rows * (cell + gap + lab) - gap
    img = Image.new("RGB", (W, H), (24, 24, 28))
    d = ImageDraw.Draw(img)
    f = _font(11)
    d.text((margin, 6), f"{sheet.name}.bmp  -  {len(sheet.tiles)} tiles  "
           f"@ {scale}x  ({TILE}px, {cols}x{rows} grid)",
           fill=(230, 230, 230), font=_font(13))

    arr = to_rgba(sheet.index_array(), pal)
    for i, t in enumerate(sheet.tiles):
        c, r = i % cols, i // cols
        x = margin + c * (cell + gap)
        y = margin + 24 + r * (cell + gap + lab)
        # checker under the tile so transparency reads
        for yy in range(0, cell, scale * 2):
            for xx in range(0, cell, scale * 2):
                on = ((xx // (scale * 2)) + (yy // (scale * 2))) % 2 == 0
                d.rectangle([x + xx, y + yy, x + xx + scale * 2,
                             y + yy + scale * 2],
                            fill=CHECKER[0] if on else CHECKER[1])
        sub = arr[r * TILE:(r + 1) * TILE, c * TILE:(c + 1) * TILE]
        til = Image.fromarray(sub, "RGBA").resize((cell, cell), Image.NEAREST)
        img.paste(til, (x, y), til)
        d.rectangle([x, y, x + cell, y + cell], outline=(12, 12, 14))
        d.text((x, y + cell + 4), f"{i:2d} {t.name}", fill=(200, 200, 200), font=f)
    return img


def _png_data_uri(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def preview_html(sheets: list[Sheet], pal: Palette) -> str:
    blocks = []
    sheet_css = []
    for s in sheets:
        arr = to_rgba(s.index_array(), pal)
        uri = _png_data_uri(Image.fromarray(arr, "RGBA"))
        sw, sh = s.cols * TILE, s.rows * TILE
        sheet_css.append(
            f'  .s-{s.name} {{ background-image:url({uri}); --sw:{sw}; --sh:{sh}; }}'
        )
        cells = "".join(
            f'<figure><span class="tile s-{s.name}" style="'
            f'--bx:{(i % s.cols) * TILE};--by:{(i // s.cols) * TILE}"></span>'
            f'<figcaption>{i} {t.name}</figcaption></figure>'
            for i, t in enumerate(s.tiles)
        )
        blocks.append(
            f'<section><h2>{s.name}.bmp '
            f'<small>{len(s.tiles)} tiles &middot; {TILE}px &middot; '
            f'{s.cols}&times;{s.rows}</small></h2>'
            f'<div class="grid">{cells}</div></section>'
        )
    body = "\n".join(blocks)
    sheet_css = "\n".join(sheet_css)
    zbtns = "".join(f'<button data-z="{z}">{z}&times;</button>' for z in ZOOMS)
    return f"""<!doctype html><meta charset="utf-8">
<title>Ch7 tiles - preview</title>
<style>
  :root {{ --z: 8; --tile: {TILE}px; }}
  body {{ background:#181820; color:#ddd; font:13px/1.4 system-ui,sans-serif;
         margin:0; padding:24px; }}
  header {{ position:sticky; top:0; background:#181820; padding:8px 0 14px;
           display:flex; gap:16px; align-items:center; flex-wrap:wrap; }}
  h1 {{ font-size:15px; margin:0; }}
  button {{ background:#2a2a36; color:#ddd; border:1px solid #444;
           border-radius:6px; padding:5px 12px; cursor:pointer; font:inherit; }}
  button.on {{ background:#4a6; border-color:#6c8; color:#062; font-weight:700; }}
  label.bg {{ margin-left:auto; }}
  section {{ margin:22px 0; }}
  h2 {{ font-size:14px; border-bottom:1px solid #333; padding-bottom:4px; }}
  h2 small {{ color:#888; font-weight:400; }}
  .grid {{ display:flex; flex-wrap:wrap; gap:16px; }}
  figure {{ margin:0; text-align:center; }}
  .tile {{
     display:block;
     width:calc(var(--tile) * var(--z));
     height:calc(var(--tile) * var(--z));
     background-repeat:no-repeat;
     background-color:var(--cell-bg,#3a3a42);
     background-size:calc(var(--sw) * 1px * var(--z)) calc(var(--sh) * 1px * var(--z));
     background-position:calc(var(--bx) * -1px * var(--z)) calc(var(--by) * -1px * var(--z));
     image-rendering:pixelated;
     outline:1px solid #111;
  }}
  figcaption {{ color:#aaa; margin-top:4px; font-size:11px;
               max-width:calc(var(--tile) * var(--z)); overflow-wrap:anywhere; }}
  body.light {{ background:#d9d9d4; color:#222; --cell-bg:#c4c4bd; }}
  body.light header {{ background:#d9d9d4; }}
{sheet_css}
</style>
<header>
  <h1>Ch7 tiles &mdash; preview <small>(cd-e17.12)</small></h1>
  <span>zoom {zbtns}</span>
  <label class="bg"><input type="checkbox" id="lt"> light background</label>
</header>
{body}
<script>
  const root = document.documentElement;
  function setZoom(z) {{
    root.style.setProperty('--z', z);
    document.querySelectorAll('[data-z]').forEach(b =>
      b.classList.toggle('on', +b.dataset.z === +z));
  }}
  document.querySelectorAll('[data-z]').forEach(b =>
    b.onclick = () => setZoom(b.dataset.z));
  document.getElementById('lt').onchange = e =>
    document.body.classList.toggle('light', e.target.checked);
  setZoom(8);
</script>
"""


def write_previews(sheets, pal):
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    for s in sheets:
        p = PREVIEW_DIR / f"{s.name}.png"
        contact_sheet(s, pal).save(p)
        print(f"  preview {p.relative_to(PREVIEW_DIR.parents[2])}")
    html = PREVIEW_DIR / "tiles.html"
    html.write_text(preview_html(sheets, pal))
    print(f"  preview {html.relative_to(PREVIEW_DIR.parents[2])}")
    return html


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true",
                    help="also emit doc/preview/ contact sheets + tiles.html")
    ap.add_argument("--open", action="store_true",
                    help="open tiles.html when done (implies --preview)")
    args = ap.parse_args()

    pal = Palette()
    sheets = build_sheets(pal)

    for s in sheets:
        path = write_bmp(s, pal)
        print(f"wrote {path.relative_to(TILES_DIR.parents[2])}  "
              f"({s.cols * TILE}x{s.rows * TILE}, {len(s.tiles)} tiles)")
    mpath = write_manifest(sheets)
    print(f"wrote {mpath.relative_to(TILES_DIR.parents[2])}")

    if args.preview or args.open:
        print("previews:")
        html = write_previews(sheets, pal)
        if args.open:
            import webbrowser
            webbrowser.open(html.as_uri())


if __name__ == "__main__":
    main()
