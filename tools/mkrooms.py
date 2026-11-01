#!/usr/bin/env python3
"""The rooms (rooms/rooms.txt) as records for the game, a file of them for
each sector (decisions 42 and 43).

    mkrooms.py build/data/rooms.6502 [--preview build/preview]

It writes, beside the file named:
    rooms.6502      what the game needs to know about every sector: how many
                    there are, how many rooms each has, the most bytes one's
                    file takes (the size of the bank's sector region), where
                    a new game starts, and each room's sector and number
                    there (for make ROOM=n)
    sector<n>.6502  sector n's file, the disc's S<n>, assembled where the
                    bank keeps it (SECTOR_AT): a table of each room's
                    address, low bytes then high bytes, SECTOR_ROOMS long;
                    its looks (looks<n>.6502, from tools/mkgfx.py: the look
                    tables and its own looks); then the records
    sectors.6502    an INCLUDE of each sector<n>.6502

Rooms are numbered within their sector, in rooms.txt's order, and a room's
exits go to rooms of its own sector. The one way out of a sector is the
cage's: a room with an exit thing, whose down exit names a room in the next
sector. The game loads that sector's file then (sector.6502).

Each room's record (rooms.6502 reads it):
    sector      its sector, 1-5 (a room with none is in the last one's)
    start       x, y in tiles where the cage brings you in, &FF if none
    exits       left, right, up, down: room numbers in the sector, &FF for
                none; down, &80 + its number for the next sector's room
    colours     logical 1-3 at the top, Red Phase then Blue Phase
    bands       a count, then each band's line, logical colour, Red, Blue
    things      a count, then each thing's type, x, y and argument
    map         packed: a byte under &80 is a look (gfxlib.Looks numbers
                them: a tile, as its surroundings choose, gfxlib.resolve);
                &80+n repeats the last
                tile n+1 more times; &C0+n copies n+1 tiles from the row
                above. MAP_W * MAP_H tiles in all.
    machinery   (decision 46, machines.6502) the beat: frames as drawn, then
                frames the other way (0, 0 for none); a count of parts; then
                each part: what moves it (0 the beat, 1 the switch), x, y,
                w and h in tiles, and a look for each cell of that
                rectangle, row by row: the beat's part has two, its look on
                the beat and as drawn, the switch's one, once thrown. &FF
                for a cell that doesn't change.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gfxlib as g  # noqa: E402

THING_TYPES = ["sentry", "drone", "crawler", "shard", "cell", "grenades", "life", "exit", "lever", "plate"]
# What throws a room's switch (decision 46): shot, or touched.
SWITCH_THINGS = ("lever", "plate")
# A down exit's room number with this set is the next sector's room (the cage's).
NEXT_SECTOR = 0x80
# Each type's size in pixels, with what it reaches beyond its sprite: the
# drone bobs 4 lines up and down, a pickup 2 lines up (things.6502).
THING_BOX = {"sentry": (16, 0, 16), "drone": (16, -4, 14), "crawler": (16, 0, 16),
             "shard": (8, 0, 8), "cell": (8, -2, 8), "grenades": (8, -2, 8),
             "life": (8, -2, 8), "exit": (16, 0, 24), "lever": (8, 0, 16), "plate": (16, 0, 8)}


def cell_look(lk):
    """A look as the map keeps it: the back wall's grid as plain air, which
    the game draws from where the cell is (screen.6502's back_look), so long
    runs of air still pack."""
    return 0 if lk.key == " " and lk.when in g.BACK_WHENS else lk.index


def machinery_bytes(r, tiles, lks):
    """The room's machinery for its record (the docstring's), with what the
    game can't do refused."""
    where = f"room {r.ident}"
    keys = {t.key: t for t in tiles}
    painted = {c for line in r.map for c in line if c in keys}
    for what in g.MACHINES:
        moving = sorted(keys[c].name for c in painted if getattr(keys[c], what) is not None)
        if what == "beat" and moving and not r.beat:
            raise SystemExit(f"{where}: it has machinery on a beat ({', '.join(moving)}), but no beat line")
        if what == "switch" and moving and not any(typ in SWITCH_THINGS for typ, *_ in r.things):
            raise SystemExit(f"{where}: it has tiles a switch throws ({', '.join(moving)}), but no lever or plate")
    out = list(r.beat or (0, 0))
    parts = g.machinery(r, tiles, lks)
    out.append(len(parts))
    for what, x, y, w, h, cells in parts:
        out += [g.MACHINES.index(what), x, y, w, h]
        for row in range(y, y + h):
            for col in range(x, x + w):
                other, drawn = cells.get((col, row), (None, None))
                looks = [other, drawn] if what == "beat" else [other]
                out += [0xFF if lk is None else cell_look(lk) for lk in looks]
    return out


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


def render(room, tiles, phase, scale=2, state=(0, 0)):
    """The room as the BBC shows it, in one phase, with its machinery in a
    state (gfxlib.machine_map)."""
    from PIL import Image
    pal_rows = g.room_palette_rows(room, phase)
    grid = g.resolve(room, tiles, state=state)
    im = Image.new("RGB", (256, 176))
    px = im.load()
    for ty, line in enumerate(grid):
        for tx, lk in enumerate(line):
            other = "blue" if phase == 0 else "red"
            pix = g.ghost_tile(lk.pixels) if other in lk.flags else lk.pixels
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
    ids = {r.ident: r for r in rooms}
    if len(ids) != len(rooms):
        raise SystemExit("rooms: duplicate ids")
    first = rooms[0]
    if not first.start:
        raise SystemExit(f"room {first.ident}: the first room needs a start")
    # Each sector's rooms, numbered within it in rooms.txt's order.
    sectors = {}
    for r in rooms:
        if not 1 <= r.sector <= 5:
            raise SystemExit(f"room {r.ident}: sectors are 1-5")
        sectors.setdefault(r.sector, []).append(r)
    number = {r.ident: sectors[r.sector].index(r) for r in rooms}
    # The looks' numbers: the shared, then each sector's own (decision 43).
    lks = g.Looks(tiles, rooms)

    records = {}
    for r in rooms:
        where = f"room {r.ident}"
        rec = [r.sector] + (list(r.start) if r.start else [0xFF, 0xFF])
        cage = any(typ == "exit" for typ, *_ in r.things)
        for d in ("left", "right", "up", "down"):
            t = r.exits[d]
            if t == "-":
                rec.append(0xFF)
                continue
            if t not in ids:
                raise SystemExit(f"{where}: exit {d} to unknown room {t!r}")
            s = ids[t].sector
            if s == r.sector:
                rec.append(number[t])
            elif d == "down" and cage and s == r.sector + 1:
                rec.append(NEXT_SECTOR + number[t])
            else:
                raise SystemExit(f"{where}: exit {d} to {t}, in sector {s}: exits stay in the room's sector "
                                 f"({r.sector}), but for a cage's down exit, which goes to the next")
        rec +=[c[0] for c in r.colours] + [c[1] for c in r.colours]
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
        if len(r.things) > 6:
            raise SystemExit(f"{where}: at most 6 things a room")
        rec.append(len(r.things))
        for (typ, x, y, args) in r.things:
            if typ not in THING_TYPES:
                raise SystemExit(f"{where}: unknown thing {typ!r}")
            w, top, bottom = THING_BOX[typ]
            if x < 0 or x * 8 + w > 256 or y * 8 + top < 0 or y * 8 + bottom > g.MAP_H * 8:
                raise SystemExit(f"{where}: {typ} at {x},{y} doesn't fit on the screen")
            arg = int(args[0]) if args else 0
            rec += [THING_TYPES.index(typ), x, y, arg]
        for k, line in enumerate(r.map):
            for c in line:
                if c not in keys:
                    raise SystemExit(f"{where}: map line {k}: no tile {c!r}")
        grid = g.resolve(r, tiles, lks.of(r.sector))
        assert all(lk.sector in (None, r.sector) for line in grid for lk in line)
        cells = [cell_look(lk) for line in grid for lk in line]
        packed = pack(cells)
        assert unpack(packed) == cells
        records[r.ident] = rec + packed + machinery_bytes(r, tiles, lks.of(r.sector))

    # Every sector's file has its tables the same length, so the game finds
    # them in the bank whichever sector is there: the rooms' (the most rooms
    # a sector has), then the looks' (NTILES long), then its own looks.
    most = max(len(rs) for rs in sectors.values())
    size = {s: 2 * most + lks.file_bytes(s) + sum(len(r.name[:20]) + 1 + len(records[r.ident]) for r in rs)
            for s, rs in sectors.items()}
    head = "\\ Made by tools/mkrooms.py from rooms/rooms.txt: don't edit."
    out_dir = Path(a.out).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    for s, rs in sorted(sectors.items()):
        pad = ["0"] * (most - len(rs))
        out = [head, f"\\ Sector {s}'s file, S{s}, assembled where the bank keeps it: its rooms and its looks.", "",
               f'SECTION Sector{s}, org = SECTOR_AT, load = &FFFF0000 + SECTOR_LOAD, filename = "S{s}", '
               "guard = SECTOR_AT + SECTOR_SIZE",
               f".sector{s}",
               "{",
               "    EQUB " + ", ".join([f"LO(room_{k})" for k in range(len(rs))] + pad),
               "    EQUB " + ", ".join([f"HI(room_{k})" for k in range(len(rs))] + pad),
               "    ASSERT P% = SECTOR_AT + 2 * SECTOR_ROOMS",
               f'    INCLUDE "looks{s}.6502"']
        for k, r in enumerate(rs):
            rec = records[r.ident]
            out.append(f".room_{k}    \\ {r.ident}: {r.name}")
            out.append(f'    EQUS "{r.name[:20]}", 0')
            for j in range(0, len(rec), 16):
                out.append("    EQUB " + ", ".join(f"&{v:02X}" for v in rec[j:j + 16]))
        out += [f"    ASSERT P% = SECTOR_AT + SECTOR_BYTES[{s - 1}]", "}", "ENDSECTION"]
        (out_dir / f"sector{s}.6502").write_text("\n".join(out) + "\n")
    (out_dir / "sectors.6502").write_text(
        "\n".join([head] + [f'INCLUDE "sector{s}.6502"' for s in sorted(sectors)]) + "\n")

    top = max(sectors)
    out = [head, "",
           "\\ Sectors 1 to SECTORS, each a file of rooms and looks on the disc, S1 to",
           "\\ S<SECTORS> (sectors.6502): the rooms each has, and the bytes its file takes.",
           f"SECTORS = {top}",
           "SECTOR_NROOMS = {" + ", ".join(str(len(sectors.get(s, []))) for s in range(1, top + 1)) + "}",
           "SECTOR_BYTES = {" + ", ".join(str(size.get(s, 0)) for s in range(1, top + 1)) + "}",
           "\\ The most rooms in a sector (each file's room table is that long), and",
           "\\ the most bytes, the size of the bank's sector region.",
           f"SECTOR_ROOMS = {most}",
           f"SECTOR_SIZE = {max(size.values())}",
           f"NEXT_SECTOR = &{NEXT_SECTOR:02X}          \\ in a down exit: the next sector's room",
           "\\ A new game: the first room, the first of its sector, at its start.",
           f"FIRST_SECTOR = {first.sector}",
           f"START_X = {first.start[0]}",
           f"START_Y = {first.start[1]}",
           "\\ Each room in rooms.txt's order (make ROOM=n): its sector, and its number there.",
           "ROOM_SECTOR = {" + ", ".join(str(r.sector) for r in rooms) + "}",
           "ROOM_NUMBER = {" + ", ".join(str(number[r.ident]) for r in rooms) + "}",
           "\\ The most parts of machinery a room has, and a part's most cells across",
           "\\ and in all (decision 46: gfxlib.py says why).",
           f"MAX_PARTS = {g.MAX_PARTS}",
           f"PART_W = {g.PART_W}",
           f"PART_CELLS = {g.PART_CELLS}"]
    for k, t in enumerate(THING_TYPES):
        out.append(f"TH_{t.upper()} = {k}")
    Path(a.out).write_text("\n".join(out) + "\n")

    if a.preview:
        from PIL import Image
        p = Path(a.preview)
        p.mkdir(parents=True, exist_ok=True)
        for r in rooms:
            # A room with machinery has a row for each other state it has:
            # on the beat, and the switch thrown.
            states = [(0, 0)] + [s for s, any_ in (((1, 0), r.beat), ((0, 1), any(
                typ in SWITCH_THINGS for typ, *_ in r.things))) if any_]
            shots = [(render(r, tiles, 0, state=s), render(r, tiles, 1, state=s)) for s in states]
            w, h = shots[0][0].width, shots[0][0].height
            both = Image.new("RGB", (w * 2 + 8, (h + 8) * len(shots) - 8), (60, 60, 60))
            for k, (red, blue) in enumerate(shots):
                both.paste(red, (0, k * (h + 8)))
                both.paste(blue, (w + 8, k * (h + 8)))
            both.save(p / f"room_{r.ident}.png")


if __name__ == "__main__":
    main()
