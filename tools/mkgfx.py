#!/usr/bin/env python3
"""The art (gfx/tiles.txt, gfx/sprites.txt) as MODE 1 bytes for the game.

    mkgfx.py build/data/gfx.6502 [--preview build/preview]

Tiles: 16 bytes each in screen order (gfx_lib.tile_bytes), then the dotted
outlines the phase tiles show out of phase. tiles_red and tiles_blue are
each phase's pointer per tile number (low bytes, then high bytes), so
drawing a tile in either phase is one lookup.

Sprites: four versions each, column by column (each column's bytes top
to bottom, then the next): facing right at an even byte, facing right two
pixels on (one byte wider), then both mirrored (for a sprite flagged
"mirror"; the others' are their right-facing ones). spr_lo, spr_hi, spr_w (in
bytes) and spr_h index them by SPR_<NAME> + version.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gfxlib as g  # noqa: E402

FLAG_BITS = {"solid": 1, "hazard": 2, "breakable": 4, "red": 8, "blue": 16}


def eqb(values, per=16):
    values = list(values)
    return "\n".join("    EQUB " + ", ".join(f"&{v:02X}" for v in values[i:i + per])
                     for i in range(0, len(values), per))


def sprite_columns(pixels):
    """Column-major bytes of a sprite whose width is a multiple of 4."""
    w = len(pixels[0])
    return [g.mode1_bytes(row[c * 4:c * 4 + 4]) for c in range(w // 4) for row in pixels]


def variants(pixels):
    shifted = [[0, 0] + r + [0, 0] for r in pixels]
    mirrored = [list(reversed(r)) for r in pixels]
    mshifted = [[0, 0] + r + [0, 0] for r in mirrored]
    return [pixels, shifted, mirrored, mshifted]


def preview(path, images, scale=4, cols=8, palette=g.DEFAULT_PREVIEW):
    from PIL import Image, ImageDraw
    cw = max(len(p[0]) for _, p in images) + 2
    ch = max(len(p) for _, p in images) + 10
    rows = (len(images) + cols - 1) // cols
    im = Image.new("RGB", (cols * cw * scale, rows * ch * scale), (40, 40, 40))
    d = ImageDraw.Draw(im)
    for k, (name, px) in enumerate(images):
        ox, oy = (k % cols) * cw * scale, (k // cols) * ch * scale
        for y, row in enumerate(px):
            for x, c in enumerate(row):
                d.rectangle([ox + x * scale, oy + y * scale, ox + x * scale + scale - 1,
                             oy + y * scale + scale - 1], fill=g.RGB[palette[c]])
        d.text((ox, oy + len(px) * scale + 2), name[:12], fill=(200, 200, 200))
    im.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--preview")
    a = ap.parse_args()
    tiles = g.read_tiles()
    sprites = g.read_sprites()
    if len(tiles) > 128:
        raise SystemExit("at most 128 tiles (the rooms' packing has 7 bits a tile)")

    out = ["\\ Made by tools/mkgfx.py from gfx/tiles.txt and gfx/sprites.txt: don't edit.", ""]
    out.append(f"NTILES = {len(tiles)}")
    for f, b in FLAG_BITS.items():
        out.append(f"TF_{f.upper()} = {b}")
    # Graphics: each tile, then each phase tile's outline.
    gfx = [g.tile_bytes(t.pixels) for t in tiles]
    hollow_of = {}
    for i, t in enumerate(tiles):
        if t.flags & {"red", "blue"}:
            hollow_of[i] = len(gfx)
            gfx.append(g.tile_bytes(g.hollow(t.pixels)))
    out.append(".tile_gfx")
    for i, b in enumerate(gfx):
        out.append(eqb(b))
    for phase, other in (("red", "blue"), ("blue", "red")):
        idx = [hollow_of[i] if other in t.flags else i for i, t in enumerate(tiles)]
        out.append(f".tiles_{phase}")
        out.append("    EQUB " + ", ".join(f"LO(tile_gfx + {k * 16})" for k in idx))
        out.append("    EQUB " + ", ".join(f"HI(tile_gfx + {k * 16})" for k in idx))
    out.append(".tile_attr")
    out.append(eqb(sum(FLAG_BITS[f] for f in t.flags) for t in tiles))
    # What each tile is in each phase: out of its phase, nothing at all.
    for phase, other in (("red", "blue"), ("blue", "red")):
        out.append(f".attr_{phase}")
        out.append(eqb(0 if other in t.flags else sum(FLAG_BITS[f] for f in t.flags) for t in tiles))
    for i, t in enumerate(tiles):
        out.append(f"T_{t.name.upper()} = {i}")

    # Sprites.
    descs = []
    for s in sprites:
        if s.w % 4:
            raise SystemExit(f"sprite {s.name}: width must be a multiple of 4")
        out.append(f"SPR_{s.name.upper()} = {len(descs)}")
        out.append(f".spr_{s.name}")
        # Facing left is a version of its own only for a sprite that faces
        # a way; the others' left versions are their right ones.
        vs = variants(s.pixels)
        for v, px in enumerate(vs):
            if v < 2 or "mirror" in s.flags:
                out.append(f".spr_{s.name}_{v}")
                out.append(eqb(sprite_columns(px)))
            descs.append((f"spr_{s.name}_{v if 'mirror' in s.flags else v & 1}", len(px[0]) // 4, s.h))
    out.append(".spr_lo")
    out.append("    EQUB " + ", ".join(f"LO({d[0]})" for d in descs))
    out.append(".spr_hi")
    out.append("    EQUB " + ", ".join(f"HI({d[0]})" for d in descs))
    out.append(".spr_w")
    out.append("    EQUB " + ", ".join(str(d[1]) for d in descs))
    out.append(".spr_h")
    out.append("    EQUB " + ", ".join(str(d[2]) for d in descs))

    # The sprites' masks: a byte's see-through pixels (both bits 0) keep the
    # screen's, the others take the sprite's.
    mask = []
    for b in range(256):
        m = 0
        for k in range(4):
            if not (b >> (7 - k)) & 1 and not (b >> (3 - k)) & 1:
                m |= 1 << (7 - k) | 1 << (3 - k)
        mask.append(m)
    out.append("    ALIGN 256")
    out.append(".mask_tab")
    out.append(eqb(mask))

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(out) + "\n")

    if a.preview:
        p = Path(a.preview)
        p.mkdir(parents=True, exist_ok=True)
        imgs = [(t.name, t.pixels) for t in tiles]
        imgs += [(t.name + "~", g.hollow(t.pixels)) for t in tiles if t.flags & {"red", "blue"}]
        preview(p / "tiles.png", imgs, scale=6)
        preview(p / "sprites.png", [(s.name, s.pixels) for s in sprites], scale=5)


if __name__ == "__main__":
    main()
