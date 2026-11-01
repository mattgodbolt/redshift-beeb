#!/usr/bin/env python3
"""The art (gfx/tiles.txt, gfx/sprites.txt) as MODE 1 bytes for the game.

    mkgfx.py build/data/gfx.6502 [--preview build/preview]

Tiles: every look (gfxlib.looks: each tile as written, then its variants
and alts), 16 bytes each in screen order (gfxlib.tile_bytes), then the dotted
outlines the phase tiles show out of phase. The shared looks are in
gfx.6502 (RSDATA), and each sector's own in looks<n>.6502 beside it, which
is part of the sector's file (decision 43; gfxlib.Looks says which are
which, from the rooms). Each looks<n>.6502 starts with the tables for every
look number, the shared and that sector's own, NTILES long, where main.6502
says (tiles_red ... attr_blue):
    tiles_red, tiles_blue   each phase's pointer to a look's graphics (low
                            bytes, then high bytes), so drawing a look in
                            either phase is one lookup
    tile_attr               its flags (TF_*)
    attr_red, attr_blue     its flags in each phase: out of its phase, none

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
    lks = g.Looks(tiles, g.read_rooms())
    sprites = g.read_sprites()
    head = "\\ Made by tools/mkgfx.py from gfx/tiles.txt, gfx/sprites.txt and rooms/rooms.txt: don't edit."

    out = [head, ""]
    out.append("\\ The look numbers: the shared looks from 0, then each sector's own, and")
    out.append("\\ the tables' length, room for the most a sector has (decision 43).")
    out.append(f"NSHARED = {len(lks.shared)}")
    out.append(f"NTILES = {lks.ntiles}")
    out.append("SECTOR_LOOKS = {" + ", ".join(str(len(lks.own.get(s, []))) for s in range(1, max(lks.own) + 1)) + "}")
    for f, b in FLAG_BITS.items():
        out.append(f"TF_{f.upper()} = {b}")
    # The sprites' masks: a byte's see-through pixels (both bits 0) keep the
    # screen's, the others take the sprite's. In a page of their own, first,
    # where RSDATA starts a page: aligned, with nothing lost to padding.
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
    # The shared looks' graphics, then their phase looks' outlines.
    gfx, red, blue = g.look_blocks(lks.shared)
    out.append(".tile_gfx")
    for b in gfx:
        out.append(eqb(b))
    for lk in lks.shared:
        out.append(f"T_{lk.name.upper()} = {lk.index}")

    # Each sector's looks file: the tables, then its own looks' graphics.
    out_dir = Path(a.out).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    for s, own in lks.own.items():
        ogfx, ored, oblue = g.look_blocks(own)
        # (Past the sector's own, nothing uses a number: the empty look.)
        pad = lks.ntiles - len(lks.shared) - len(own)
        ptrs = {phase: [f"tile_gfx + {k * 16}" for k in shared] + [f"own_gfx + {k * 16}" for k in mine]
                + ["tile_gfx"] * pad
                for phase, shared, mine in (("red", red, ored), ("blue", blue, oblue))}
        every = lks.shared + own
        attr = [sum(FLAG_BITS[f] for f in lk.flags) for lk in every] + [0] * pad
        # What each look is in each phase: out of its phase, nothing at all.
        phased = {phase: [0 if other in lk.flags else a for lk, a in zip(every, attr)] + [0] * pad
                  for phase, other in (("red", "blue"), ("blue", "red"))}
        lo = [head, f"\\ Sector {s}'s looks, in its file (sector{s}.6502): the tables for every look",
              "\\ number, the shared looks' as in every sector and then its own, and its own",
              "\\ looks' graphics. Its own looks are:"]
        lo += [f"\\   {lk.index} {lk.name}" for lk in own] or ["\\   (none)"]
        for phase in ("red", "blue"):
            lo.append(f"    ASSERT P% = tiles_{phase}")
            for part in ("LO", "HI"):
                for i in range(0, lks.ntiles, 8):
                    lo.append("    EQUB " + ", ".join(f"{part}({p})" for p in ptrs[phase][i:i + 8]))
        lo.append("    ASSERT P% = tile_attr")
        lo.append(eqb(attr))
        for phase in ("red", "blue"):
            lo.append(f"    ASSERT P% = attr_{phase}")
            lo.append(eqb(phased[phase]))
        lo.append(".own_gfx")
        lo += [eqb(b) for b in ogfx]
        (out_dir / f"looks{s}.6502").write_text("\n".join(lo) + "\n")

    # Sprites.
    descs = []
    for s in sprites:
        if s.w % 4:
            raise SystemExit(f"sprite {s.name}: width must be a multiple of 4")
        out.append(f"SPR_{s.name.upper()} = {len(descs)}")
        # Its size in pixels, for the source's ASSERTs.
        out.append(f"SPR_{s.name.upper()}_W = {s.w} : SPR_{s.name.upper()}_H = {s.h}")
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

    Path(a.out).write_text("\n".join(out) + "\n")

    if a.preview:
        p = Path(a.preview)
        p.mkdir(parents=True, exist_ok=True)
        # Every look: the shared, then each sector's own.
        every = lks.shared + [lk for s in lks.own for lk in lks.own[s]]
        imgs = [(lk.name, lk.pixels) for lk in every]
        imgs += [(lk.name + "~", g.ghost_tile(lk.pixels)) for lk in every if lk.flags & {"red", "blue"}]
        preview(p / "tiles.png", imgs, scale=6)
        preview(p / "sprites.png", [(s.name, s.pixels) for s in sprites], scale=5)


if __name__ == "__main__":
    main()
