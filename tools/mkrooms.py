#!/usr/bin/env python3
"""The rooms (rooms/rooms.txt) as records for the game.

    mkrooms.py build/data/rooms.6502 [--preview build/preview]

Each room's record (rooms.6502 reads it):
    exits       left, right, up, down: room numbers, &FF for none
    colours     logical 1-3 at the top, Red Phase then Blue Phase
    bands       a count, then each band's line, logical colour, Red, Blue
    things      a count, then each thing's type, x, y and argument
    map         packed: a byte under &80 is a tile; &80+n repeats the last
                tile n+1 more times; &C0+n copies n+1 tiles from the row
                above. MAP_W * MAP_H tiles in all.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gfxlib as g  # noqa: E402

THING_TYPES = ["sentry", "drone", "crawler", "shard", "cell", "grenades", "life", "exit"]


def pack(cells):
    out, i = [], 0
    n = len(cells)
    while i < n:
        run = 0
        if i:
            while i + run < n and run < 64 and cells[i + run] == cells[i - 1]:
                run += 1
        up = 0
        if i >= g.MAP_W:
            while i + up < n and up < 64 and cells[i + up] == cells[i + up - g.MAP_W]:
                up += 1
        if max(run, up) >= 2:
            if up >= run:
                out.append(0xC0 + up - 1)
                i += up
            else:
                out.append(0x80 + run - 1)
                i += run
        else:
            out.append(cells[i])
            i += 1
    return out


def unpack(data):
    cells = []
    for b in data:
        if b < 0x80:
            cells.append(b)
        elif b < 0xC0:
            cells += [cells[-1]] * (b - 0x80 + 1)
        else:
            for _ in range(b - 0xC0 + 1):
                cells.append(cells[len(cells) - g.MAP_W])
    return cells


def render(room, tiles, phase, scale=2):
    """The room as the BBC shows it, in one phase."""
    from PIL import Image
    pal_rows = g.room_palette_rows(room, phase)
    keys = {t.key: t for t in tiles}
    im = Image.new("RGB", (256, 176))
    px = im.load()
    for ty, line in enumerate(room.map):
        for tx, k in enumerate(line):
            t = keys[k]
            other = "blue" if phase == 0 else "red"
            pix = g.hollow(t.pixels) if other in t.flags else t.pixels
            for y in range(8):
                pal = pal_rows[ty * 8 + y]
                for x in range(8):
                    px[tx * 8 + x, ty * 8 + y] = g.RGB[pal[pix[y][x]]]
    return im.resize((256 * scale, 176 * scale), Image.NEAREST)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--preview")
    a = ap.parse_args()
    tiles = g.read_tiles()
    keys = {t.key: i for i, t in enumerate(tiles)}
    rooms = g.read_rooms()
    ids = {r.ident: i for i, r in enumerate(rooms)}
    if len(ids) != len(rooms):
        raise SystemExit("rooms: duplicate ids")

    out = ["\\ Made by tools/mkrooms.py from rooms/rooms.txt: don't edit.", ""]
    out.append(f"NROOMS = {len(rooms)}")
    first = rooms[0]
    if not first.start:
        raise SystemExit(f"room {first.ident}: the first room needs a start")
    out.append(f"START_X = {first.start[0]}")
    out.append(f"START_Y = {first.start[1]}")
    for k, t in enumerate(THING_TYPES):
        out.append(f"TH_{t.upper()} = {k}")
    out.append(".room_lo")
    out.append("    EQUB " + ", ".join(f"LO(room_{i})" for i in range(len(rooms))))
    out.append(".room_hi")
    out.append("    EQUB " + ", ".join(f"HI(room_{i})" for i in range(len(rooms))))
    total = 0
    for i, r in enumerate(rooms):
        where = f"room {r.ident}"
        rec = []
        for d in ("left", "right", "up", "down"):
            t = r.exits[d]
            if t == "-":
                rec.append(0xFF)
            elif t in ids:
                rec.append(ids[t])
            else:
                raise SystemExit(f"{where}: exit {d} to unknown room {t!r}")
        rec += [c[0] for c in r.colours] + [c[1] for c in r.colours]
        bands = sorted(r.bands)
        if len(bands) > 8:
            raise SystemExit(f"{where}: at most 8 bands")
        last = 0
        for line, *_ in bands:
            if line < 2 or line >= g.MAP_H * 8 or line - last < 2:
                raise SystemExit(f"{where}: band at line {line}: lines run 2-{g.MAP_H * 8 - 1}, at least 2 apart")
            last = line
        rec.append(len(bands))
        for b in bands:
            rec += list(b)
        rec.append(len(r.things))
        for (typ, x, y, args) in r.things:
            if typ not in THING_TYPES:
                raise SystemExit(f"{where}: unknown thing {typ!r}")
            arg = int(args[0]) if args else 0
            rec += [THING_TYPES.index(typ), x, y, arg]
        cells = []
        for k, line in enumerate(r.map):
            for c in line:
                if c not in keys:
                    raise SystemExit(f"{where}: map line {k}: no tile {c!r}")
                cells.append(keys[c])
        packed = pack(cells)
        assert unpack(packed) == cells
        rec += packed
        total += len(rec)
        out.append(f".room_{i}    \\ {r.ident}: {r.name}")
        out.append(f"    EQUS \"{r.name[:20]}\", 0")
        for k in range(0, len(rec), 16):
            out.append("    EQUB " + ", ".join(f"&{v:02X}" for v in rec[k:k + 16]))
    out.append(f"\\ {len(rooms)} rooms")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(out) + "\n")

    if a.preview:
        from PIL import Image
        p = Path(a.preview)
        p.mkdir(parents=True, exist_ok=True)
        for r in rooms:
            red, blue = render(r, tiles, 0), render(r, tiles, 1)
            both = Image.new("RGB", (red.width * 2 + 8, red.height), (60, 60, 60))
            both.paste(red, (0, 0))
            both.paste(blue, (red.width + 8, 0))
            both.save(p / f"room_{r.ident}.png")


if __name__ == "__main__":
    main()
