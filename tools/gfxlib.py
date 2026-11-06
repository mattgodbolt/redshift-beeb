"""Shared readers for REDSHIFT's text art (gfx/*.txt) and rooms (rooms/rooms.txt).

The art is logical colours: '.' is 0 (black, or see-through in a sprite),
'1', '2' and '3' the others. Which physical colour each shows depends on the
room's palette bands, so previews use a room's colours, or DEFAULT_PREVIEW.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PIX = {".": 0, "1": 1, "2": 2, "3": 3}
PHYS = {"black": 0, "red": 1, "green": 2, "yellow": 3, "blue": 4,
        "magenta": 5, "cyan": 6, "white": 7}
PHYS_NAMES = {v: k for k, v in PHYS.items()}
RGB = [(0, 0, 0), (255, 0, 0), (0, 255, 0), (255, 255, 0), (0, 0, 255),
       (255, 0, 255), (0, 255, 255), (255, 255, 255)]
# The Blue Phase's colour for each Red Phase colour, unless a room says.
SWAP = {0: 0, 1: 4, 4: 1, 3: 6, 6: 3, 5: 2, 2: 5, 7: 7}
DEFAULT_PREVIEW = [0, 1, 3, 7]
MAP_W, MAP_H = 32, 22
TILE_FLAGS = ("solid", "hazard", "breakable", "red", "blue")


def _blocks(path):
    """(header words, art lines, line number) for each block of a gfx file."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        # (A comment is a whole line starting with '#': '#' is a tile's key.)
        raw = lines[i].strip()
        i += 1
        if not raw or raw.startswith("#"):
            continue
        words = raw.split()
        if words[0] == "tile" and any(w.startswith("as=") for w in words[3:]):
            h = 0               # (drawn as another tile: no art of its own)
        elif words[0] in ("tile", "variant", "alt", "blue"):
            h = 8
        elif words[0] == "sprite":
            h = int(words[3])
        else:
            raise SystemExit(f"{path}:{i}: expected 'tile', 'variant', 'alt', 'blue' or 'sprite', got {raw!r}")
        art = [lines[i + k].rstrip() for k in range(h)]
        yield words, art, i
        i += h


def _pixels(art, w, where):
    rows = []
    for k, line in enumerate(art):
        if len(line) != w or any(c not in PIX for c in line):
            raise SystemExit(f"{where}+{k}: art lines must be {w} of '.123', got {line!r}")
        rows.append([PIX[c] for c in line])
    return rows


class Tile:
    def __init__(self, key, name, flags, pixels, shared=False, partners=None, like=None):
        self.key, self.name, self.flags, self.pixels = key, name, flags, pixels
        self.shared = shared    # its looks are in every sector, whatever the rooms use (Looks)
        self.variants = []      # (when, pixels), in file order: the first that holds is used
        self.alts = {}          # when -> [pixels]: looks used now and then instead
        # The tile it becomes on the room's beat, or once the room's switch is
        # thrown: a key, or None (MACHINES).
        partners = partners or {}
        self.beat, self.switch = partners.get("beat"), partners.get("switch")
        # The tile it's drawn as (as=<key>), with no looks of its own: or None.
        self.like = like
        # Its picture in the Blue Phase, where it's another thing in each
        # phase (a "blue" block: the Hinge's), or None: the same in both.
        self.blue_pixels = None
        # The tile the game's code turns it into next (then=<key>), whose
        # looks travel with this one's: or None (Looks, mkgfx.py's names).
        self.then = None


# What makes a tile machinery (decision 46): beat=<key> becomes that tile on
# the room's beat and back again, and switch=<key> becomes it once the
# room's switch is thrown.
MACHINES = ("beat", "switch")

# What a variant's <when> may say (see gfx/tiles.txt). Sides join with '+'.
SIDES = ("up", "down", "left", "right")
# The air's looks on its two by two grid: the game draws them from where a
# cell is (screen.6502's back_look), so the rooms keep plain air there.
BACK_WHENS = ("tl", "tr", "bl", "br")
WHENS = ("deep", "ceiling", "tl", "tr", "bl", "br", "exit_left", "exit_right", "exit_up", "exit_down")


def _when(word, where, alt):
    if word == "base" and alt:
        return word
    if word in WHENS or all(s in SIDES for s in word.split("+")):
        return word
    raise SystemExit(f"{where}: unknown <when> {word!r}")


def read_tiles(path=ROOT / "gfx/tiles.txt"):
    """Tiles in file order; the first must be the empty one (key ' '). Each
    keeps its variants and alts (the blocks after it that name its key). A
    tile that says as=<key> is drawn as that one, an earlier tile, with the
    same flags: it has no art, and no looks of its own (machinery that looks
    like something already drawn costs no looks). A "blue <key>" block is
    that tile's picture in the Blue Phase: one thing in the Red and another
    in the Blue, in the same cells, with the same flags in both (the
    Hinge's, decision 58). Such a tile has no variants or alts, and isn't a
    phase's own. then=<key> names the tile the game's code turns it into
    next (the Hinge's), whose looks go wherever this one's do."""
    tiles = []
    for words, art, line in _blocks(path):
        if words[0] == "blue":
            where = f"{path}:{line}"
            if len(words) != 2:
                raise SystemExit(f"{where}: blue <key>")
            key = " " if words[1] == "space" else words[1]
            base = next((t for t in tiles if t.key == key), None)
            if base is None:
                raise SystemExit(f"{where}: no tile {words[1]!r} before this")
            if base.like is not None or base.blue_pixels is not None or base.flags & {"red", "blue"}:
                raise SystemExit(f"{where}: tile {base.name} can't have a Blue Phase picture of its own: it's "
                                 "drawn as another, has one already, or is only in one phase")
            base.blue_pixels = _pixels(art, 8, where)
            continue
        if words[0] in ("variant", "alt"):
            where = f"{path}:{line}"
            if len(words) != 3:
                raise SystemExit(f"{where}: {words[0]} <key> <when>")
            key = " " if words[1] == "space" else words[1]
            base = next((t for t in tiles if t.key == key), None)
            if base is None:
                raise SystemExit(f"{where}: no tile {words[1]!r} before this")
            if base.like is not None:
                raise SystemExit(f"{where}: tile {base.name} is drawn as another, with no looks of its own")
            when = _when(words[2], where, words[0] == "alt")
            px = _pixels(art, 8, where)
            if words[0] == "variant":
                base.variants.append((when, px))
            else:
                base.alts.setdefault(when, []).append(px)
            continue
        if words[0] != "tile":
            continue
        # "tile <key> <name> flags...": the key is one character; a space is
        # written as the word "space".
        key = " " if words[1] == "space" else words[1]
        if len(key) != 1:
            raise SystemExit(f"{path}:{line}: a tile's key is one character")
        # (shared says which file a look travels in, not what the tile is.)
        plain = [w for w in words[3:] if "=" not in w]
        flags = set(plain) - {"shared"}
        bad = flags - set(TILE_FLAGS)
        if bad:
            raise SystemExit(f"{path}:{line}: unknown flags {bad}")
        partners, like, then = {}, None, None
        for w in words[3:]:
            what, eq, other = w.partition("=")
            if not eq:
                continue
            other = " " if other == "space" else other
            if what == "then":
                if then is not None or len(other) != 1:
                    raise SystemExit(f"{path}:{line}: a tile may say then=<key>, once: got {w!r}")
                then = other
                continue
            if what == "as":
                base = next((t for t in tiles if t.key == other), None)
                if like is not None or base is None or base.like is not None:
                    raise SystemExit(f"{path}:{line}: as=<key> names an earlier tile, once, that isn't drawn as "
                                     f"another: got {w!r}")
                if base.flags != flags:
                    raise SystemExit(f"{path}:{line}: a tile drawn as {base.name} has its flags")
                like = base
                continue
            if what not in MACHINES or len(other) != 1 or partners:
                raise SystemExit(f"{path}:{line}: a tile may say beat=<key> or switch=<key>, once: got {w!r}")
            partners[what] = other
        pixels = like.pixels if like else _pixels(art, 8, f"{path}:{line}")
        tiles.append(Tile(key, words[2], flags, pixels, "shared" in plain, partners, like and like.key))
        tiles[-1].then = then
    if not tiles or tiles[0].key != " ":
        raise SystemExit(f"{path}: the first tile must be 'space'")
    keys = [t.key for t in tiles]
    if len(set(keys)) != len(keys):
        raise SystemExit(f"{path}: duplicate tile keys")
    by = {t.key: t for t in tiles}
    for t in tiles:
        if t.blue_pixels is not None and (t.variants or t.alts):
            raise SystemExit(f"{path}: tile {t.name} has a Blue Phase picture, so no variants or alts")
        if t.then is not None and (t.then not in by or by[t.then].like is not None):
            raise SystemExit(f"{path}: tile {t.name}: then={t.then!r} isn't a tile with looks of its own")
        for what in MACHINES:
            other = getattr(t, what)
            if other is None:
                continue
            if other not in by:
                raise SystemExit(f"{path}: tile {t.name}: {what}={other!r} isn't a tile")
            # (A blast clears a breakable tile for good, and the machinery
            # would put it back.)
            if "breakable" in t.flags or "breakable" in by[other].flags:
                raise SystemExit(f"{path}: tile {t.name}: machinery can't be breakable, nor become it")
    return tiles


class Sprite:
    def __init__(self, name, w, h, pixels, flags=()):
        self.name, self.w, self.h, self.pixels = name, w, h, pixels
        self.flags = set(flags)


def read_sprites(path=ROOT / "gfx/sprites.txt", ghosts=True):
    """The sprites in file order. With ghosts, each one flagged "phase" is
    followed by its dotted outlines on the two squares of a checkerboard,
    <name>_ghost and <name>_ghost2, shown in turn out of phase."""
    out = []
    for words, art, line in _blocks(path):
        if words[0] != "sprite":
            continue
        name, w, h = words[1], int(words[2]), int(words[3])
        flags = words[4:]
        if set(flags) - {"phase", "mirror"}:
            raise SystemExit(f"{path}:{line}: unknown sprite flags {flags}")
        s = Sprite(name, w, h, _pixels(art, w, f"{path}:{line}"), flags)
        out.append(s)
        if ghosts and "phase" in s.flags:
            out.append(Sprite(name + "_ghost", w, h, ghost_sprite(s.pixels, 0), s.flags - {"phase"}))
            out.append(Sprite(name + "_ghost2", w, h, ghost_sprite(s.pixels, 1), s.flags - {"phase"}))
    return out


def hollow(pixels, parity=None):
    """The out-of-phase look of a phase tile or sprite: a dotted outline.
    The outline is the lit pixels on the edge (a neighbour or the border is
    dark). The dots are the squares of a checkerboard: those of the parity
    given (0 even, 1 odd), or else those that keep more of it (the even
    ones, on a tie). A tiny thing keeps its whole outline, so it never
    vanishes."""
    h, w = len(pixels), len(pixels[0])
    edge = []
    for y in range(h):
        for x in range(w):
            if pixels[y][x] and (x in (0, w - 1) or y in (0, h - 1) or any(
                    not pixels[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))):
                edge.append((x, y))
    even = [(x, y) for x, y in edge if not (x + y) & 1]
    odd = [(x, y) for x, y in edge if (x + y) & 1]
    if parity is None:
        keep = even if len(even) >= len(odd) else odd
    else:
        keep = odd if parity else even
    if len(keep) < 8:
        keep = edge
    out = [[0] * w for _ in range(h)]
    for x, y in keep:
        out[y][x] = pixels[y][x]
    return out


def ghost_sprite(pixels, parity=0):
    """An enemy out of phase: its whole outline, so its shape still reads,
    and inside it a sparse diagonal fill that moves between the two
    parities (the game shows them in turn, so the ghost shimmers). A small
    thing keeps its dark marks too, its eyes, so its face reads. Never
    white, since white marks what can hurt you or be taken: it's all in the
    body colour, 1, as a room may make 2 white too, as the Prism's do
    (decision 63)."""
    h, w = len(pixels), len(pixels[0])
    out = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            c = pixels[y][x]
            if not c:
                continue
            edge = x in (0, w - 1) or y in (0, h - 1) or any(
                not pixels[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            # (A small thing dithered whole read as a dart, the mite's horns
            # and legs broken into diagonals (decision 57); its outline and
            # eyes read as a creature.)
            if edge or (w <= 8 and c == 1) or (x + y + 2 * parity) % 4 == 0:
                out[y][x] = 1
    return out


def ghost_tile(pixels):
    """A phase tile out of phase: its dotted outline (hollow), and inside
    it a sparse diagonal hatch of its own colours, the same in every room,
    so it reads as a block that isn't there."""
    out = hollow(pixels)
    for y, row in enumerate(pixels):
        for x, c in enumerate(row):
            if c and not out[y][x] and (x - y) % 4 == 0 and 0 < x < 7 and 0 < y < 7:
                out[y][x] = c
    return out


def mode1_bytes(row4):
    """Four logical colours (left first) as one MODE 1 byte."""
    b = 0
    for k, c in enumerate(row4):
        b |= ((c >> 1) & 1) << (7 - k) | (c & 1) << (3 - k)
    return b


def tile_bytes(pixels):
    """A tile's 16 bytes in screen order: the left cell's 8 lines, then the right's."""
    return [mode1_bytes(r[0:4]) for r in pixels] + [mode1_bytes(r[4:8]) for r in pixels]


# --- Looks: each tile's variants and alts, numbered for the game ------------

class Look:
    """One 8x8 picture the game can draw: a tile as written, or one of its
    variants or alts. It has its tile's flags, and the sector it travels
    with: None for a shared look (Looks)."""
    def __init__(self, index, tile, when, alt, pixels, sector=None):
        self.index, self.tile, self.when, self.alt, self.pixels = index, tile, when, alt, pixels
        self.key, self.flags, self.sector = tile.key, tile.flags, sector
        # (Its Blue Phase picture, if it's another thing there: Tile's.)
        self.blue_pixels = tile.blue_pixels if when == "base" and alt is None else None
        self.name = tile.name
        if when != "base":
            self.name += "_" + when.replace("+", "_")
        if alt is not None:
            self.name += f"_alt{alt}"


def looks(tiles, first=0, sector=None):
    """These tiles' looks, numbered from first: the tiles as written, then
    each tile's variants and alts in order. (A tile drawn as another has
    none.)"""
    tiles = [t for t in tiles if t.like is None]
    out = [Look(first + i, t, "base", None, t.pixels, sector) for i, t in enumerate(tiles)]
    for t in tiles:
        for when, px in t.variants:
            out.append(Look(first + len(out), t, when, None, px, sector))
        for when, pxs in t.alts.items():
            for k, px in enumerate(pxs):
                out.append(Look(first + len(out), t, when, k, px, sector))
    return out


# The rooms' packing has 7 bits a look.
MAX_LOOKS = 128
# The game's tables take this many bytes for each look number (mkgfx.py):
# tiles_red and tiles_blue two each, tile_attr, attr_red and attr_blue one.
TABLE_BYTES = 7


class Looks:
    """Every look, numbered for the game (decision 43). The shared looks are
    in RSDATA; a sector's own travel in its file, and are in the bank only
    while it's loaded.

    A tile's looks are a sector's own when only that sector's rooms use the
    tile and it isn't flagged shared; a tile no room uses, and not flagged
    shared, is no sector's, and isn't in the game at all (art drawn ahead
    of its rooms costs nothing). The empty tile's are always shared:
    the game fills with it (T_EMPTY) and draws the back wall from its
    looks. The shared looks number from 0, in file order (looks), so the
    empty tile is 0 and its variants stay in order; each sector's own
    number on from the first number after them, so they take the same
    numbers in every sector.

        shared   the shared looks
        own      sector -> its own looks, for each sector with rooms
        ntiles   how many the game's tables hold: the shared looks, and
                 room for the most any sector has of its own"""
    def __init__(self, tiles, rooms):
        used = {}
        by = {t.key: t for t in tiles}

        def use(c, sector):
            if sector in used.get(c, ()):
                return
            used.setdefault(c, set()).add(sector)
            # (A tile drawn as another uses that one's looks, and one the
            # game's code turns it into, then=, that one's.)
            if c in by and by[c].like is not None:
                use(by[c].like, sector)
            if c in by and by[c].then is not None:
                use(by[c].then, sector)
        for r in rooms:
            for line in r.map:
                for c in line:
                    use(c, r.sector)
                    # (and what it becomes, as machinery: machine_map)
                    for other in (by[c].beat, by[c].switch) if c in by else ():
                        if other is not None:
                            use(other, r.sector)

        UNUSED = "unused"

        def owner(i, t):
            s = used.get(t.key, set())
            if t.like is not None:
                return UNUSED       # (no looks of its own)
            if i == 0 or t.shared or len(s) > 1:
                return None
            return next(iter(s)) if s else UNUSED

        whose = [owner(i, t) for i, t in enumerate(tiles)]
        self.shared = looks([t for t, s in zip(tiles, whose) if s is None])
        n = len(self.shared)
        self.own = {s: looks([t for t, o in zip(tiles, whose) if o == s], n, s)
                    for s in sorted({r.sector for r in rooms})}
        for s, own in self.own.items():
            if n + len(own) > MAX_LOOKS:
                raise SystemExit(f"Sector {s}: {n} shared looks and {len(own)} of its own, "
                                 f"at most {MAX_LOOKS} in all (the rooms' packing has 7 bits a look)")
        self.ntiles = n + max((len(own) for own in self.own.values()), default=0)

    def of(self, sector):
        """The looks a sector's rooms draw with, in number order."""
        return self.shared + self.own.get(sector, [])

    def file_bytes(self, sector):
        """What a sector's looks take in its file (mkgfx.py's looks<n>.6502):
        the tables, and its own looks' graphics."""
        return TABLE_BYTES * self.ntiles + 16 * len(look_blocks(self.own[sector])[0])


def look_blocks(lks):
    """These looks' graphics, 16 bytes each (tile_bytes) in their order,
    then the dotted outlines of the phase ones, then the Blue Phase pictures
    of those that are another thing there (each, unless it's a block
    already); and each look's block in the Red Phase and in the Blue (out of
    its phase, its outline). (A Red Phase picture of a look that's another
    thing in the Blue is stored once too, if another look has it.)"""
    blocks, pic = [], []
    for lk in lks:
        b = tile_bytes(lk.pixels)
        if lk.blue_pixels is None or b not in blocks:
            blocks.append(b)
        pic.append(len(blocks) - 1 if lk.blue_pixels is None else blocks.index(b))
    hollow_of = {}
    for i, lk in enumerate(lks):
        if lk.flags & {"red", "blue"}:
            hollow_of[i] = len(blocks)
            blocks.append(tile_bytes(ghost_tile(lk.pixels)))
    red = [hollow_of[i] if "blue" in lk.flags else pic[i] for i, lk in enumerate(lks)]
    blue = [hollow_of[i] if "red" in lk.flags else pic[i] for i, lk in enumerate(lks)]
    for i, lk in enumerate(lks):
        if lk.blue_pixels is not None:
            b = tile_bytes(lk.blue_pixels)
            if b not in blocks:
                blocks.append(b)
            blue[i] = blocks.index(b)
    return blocks, red, blue


def look_hash(c, r, salt):
    """Where alts go: 0-7, from the cell and the room. (The editor has the
    same sum.)"""
    return ((((c + 1) * 40503) ^ ((r + 1 + salt) * 32587)) >> 5) & 7


def resolve(room, tiles, all_looks=None, state=(0, 0)):
    """The room's map as looks: each cell's tile, as its surroundings choose.

    A side of a solid tile is open when the tile there isn't solid in both
    phases; a side of any other tile is open when the tile there is another
    one. Past the map's edge, a side is closed. A tile takes its first
    variant whose <when> holds, or else its own look; then, where the cell's
    look_hash falls below the number of alts for that <when>, that alt.
    The looks are all_looks, for the game's numbers the room's sector's
    (Looks.of), or else every look numbered in file order. The map is the
    room's machinery in the state given (machine_map), and a tile drawn as
    another (as=) is that one there."""
    all_looks = all_looks or looks(tiles)
    keys = {t.key: t for t in tiles}
    by = {(lk.key, lk.when, lk.alt): lk for lk in all_looks}
    salt = sum(map(ord, room.ident)) & 0xFF
    rows = ["".join(keys[k].like or k if k in keys else k for k in line)
            for line in machine_map(room, tiles, *state)]

    def solid_both(k):
        f = keys[k].flags
        return "solid" in f and not f & {"red", "blue"}

    grid = []
    for r in range(MAP_H):
        row = []
        for c in range(MAP_W):
            k = rows[r][c]
            t = keys[k]
            opened = set()
            for side, (dc, dr) in zip(SIDES, ((0, -1), (0, 1), (-1, 0), (1, 0))):
                nc, nr = c + dc, r + dr
                if 0 <= nc < MAP_W and 0 <= nr < MAP_H:
                    n = rows[nr][nc]
                    if (not solid_both(n)) if "solid" in t.flags else n != k:
                        opened.add(side)

            def holds(when):
                if when == "deep":
                    return not opened
                if when == "ceiling":
                    return r > 0 and solid_both(rows[r - 1][c])
                if when in ("tl", "tr", "bl", "br"):
                    return when == "tb"[r & 1] + "lr"[c & 1]
                if when.startswith("exit_"):
                    d = when[5:]
                    edge = {"left": c == 0, "right": c == MAP_W - 1, "up": r == 0, "down": r == MAP_H - 1}[d]
                    return edge and room.exits[d] != "-"
                return all(s in opened for s in when.split("+"))

            when = next((w for w, _ in t.variants if holds(w)), "base")
            alts = t.alts.get(when, [])
            h = look_hash(c, r, salt)
            row.append(by[(k, when, h if h < len(alts) else None)])
        grid.append(row)
    return grid


# --- Machinery (decision 46) ---------------------------------------------------

def machine_map(room, tiles, beat=0, thrown=0):
    """The room's map with its machinery in a state: on the beat, each tile
    that says beat=<key> is that tile instead; once the switch is thrown,
    each that says switch=<key>. (A key that isn't a tile stays.)"""
    keys = {t.key: t for t in tiles}

    def cell(c):
        t = keys.get(c)
        if t is None:
            return c
        if beat and t.beat is not None:
            return t.beat
        if thrown and t.switch is not None:
            return t.switch
        return c
    return ["".join(cell(c) for c in line) for line in room.map]


# The game redraws machinery a part at a time, each a rectangle of cells that
# render.6502 composes as it does a moving thing's, so a part fits its compose
# buffer: under 256 bytes a row, and CBUF_SIZE in all, at 16 bytes a cell. A
# room has at most MAX_PARTS, as many as the game's list of the parts a frame
# must draw holds.
PART_W = 15
PART_CELLS = 48
MAX_PARTS = 8
# The states that come about: as drawn, on the beat, the switch thrown, both.
STATES = ((0, 0), (1, 0), (0, 1), (1, 1))


def _rects(cells):
    """Cells as rectangles: each 4-connected group's, found in reading order,
    cut into columns at most PART_W wide and those into bands of rows of at
    most PART_CELLS cells, leaving out any with none of the group in it."""
    left, out = set(cells), []
    for r in range(MAP_H):
        for c in range(MAP_W):
            if (c, r) not in left:
                continue
            group, todo = set(), [(c, r)]
            while todo:
                p = todo.pop()
                if p in left:
                    left.discard(p)
                    group.add(p)
                    todo += [(p[0] + dc, p[1] + dr) for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            x0, x1 = min(x for x, _ in group), max(x for x, _ in group)
            y0, y1 = min(y for _, y in group), max(y for _, y in group)
            for x in range(x0, x1 + 1, PART_W):
                w = min(PART_W, x1 + 1 - x)
                band = PART_CELLS // w
                for y in range(y0, y1 + 1, band):
                    h = min(band, y1 + 1 - y)
                    if any((c, r) in group for r in range(y, y + h) for c in range(x, x + w)):
                        out.append((x, y, w, h))
    return out


def machinery(room, tiles, all_looks=None):
    """The room's machinery as parts the game redraws: for the beat, then the
    switch, each part (what, x, y, w, h, cells), where cells has each cell
    of its rectangle that changes, (c, r) -> (its look the other way, its
    look as drawn). A cell changes when its look does: a machine's own, or a
    neighbour's that it shows against. The game can't do two things to one
    cell, nor undo a blast, so it fails if the beat and the switch change a
    cell between them, or if a breakable tile changes."""
    where = f"room {room.ident}"
    keys = {t.key: t for t in tiles}
    grids = {s: resolve(room, tiles, all_looks, s) for s in STATES}
    ident = {s: [[(lk.key, lk.when, lk.alt) for lk in line] for line in grid] for s, grid in grids.items()}
    drawn = ident[0, 0]
    beat = {(c, r) for r in range(MAP_H) for c in range(MAP_W) if ident[1, 0][r][c] != drawn[r][c]}
    thrown = {(c, r) for r in range(MAP_H) for c in range(MAP_W) if ident[0, 1][r][c] != drawn[r][c]}
    for r in range(MAP_H):
        for c in range(MAP_W):
            want = ident[1, 0] if (c, r) in beat else ident[0, 1] if (c, r) in thrown else drawn
            if ((c, r) in beat and (c, r) in thrown) or ident[1, 1][r][c] != want[r][c]:
                raise SystemExit(f"{where}: the cell at {c},{r} changes with the beat and with the switch: "
                                 "keep the two apart")
            if ((c, r) in beat or (c, r) in thrown) and "breakable" in keys[room.map[r][c]].flags:
                raise SystemExit(f"{where}: the breakable tile at {c},{r} changes with the machinery, "
                                 "which would undo a blast")
    parts = []
    for what, cells, s in (("beat", beat, (1, 0)), ("switch", thrown, (0, 1))):
        for x, y, w, h in _rects(cells):
            parts.append((what, x, y, w, h, {(c, r): (grids[s][r][c], grids[0, 0][r][c])
                                               for r in range(y, y + h) for c in range(x, x + w) if (c, r) in cells}))
    if len(parts) > MAX_PARTS:
        raise SystemExit(f"{where}: its machinery is {len(parts)} parts: at most {MAX_PARTS}")
    return parts


# --- Rooms -------------------------------------------------------------------

class Room:
    def __init__(self, ident):
        self.ident = ident
        self.name = ident.upper()
        self.exits = {"left": "-", "right": "-", "up": "-", "down": "-"}
        self.colours = None            # [(red, blue)] for logical 1-3
        self.bands = []                # (line, logical, red, blue)
        self.map = []
        self.things = []               # (type, x, y, args)
        self.start = None
        self.sector = None
        self.beat = None               # (frames as drawn, frames the other way): its machinery's beat


def _colour(word, where):
    """'red' or 'red/cyan': the Red Phase colour and the Blue Phase's."""
    parts = word.split("/")
    try:
        red = PHYS[parts[0]]
        blue = PHYS[parts[1]] if len(parts) > 1 else SWAP[red]
    except (KeyError, IndexError):
        raise SystemExit(f"{where}: unknown colour {word!r}")
    return red, blue


def _int(word, where):
    try:
        return int(word)
    except (TypeError, ValueError):
        raise SystemExit(f"{where}: expected a number, got {word!r}")


def _words(words, n, where, usage):
    if len(words) < n:
        raise SystemExit(f"{where}: {usage}")


def read_rooms(path=ROOT / "rooms/rooms.txt"):
    rooms = []
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    i = 0
    room = None
    while i < len(lines):
        where = f"{path}:{i + 1}"
        raw = lines[i].split("#", 1)[0].rstrip()
        i += 1
        if not raw.strip():
            continue
        words = raw.split()
        key = words[0]
        if key == "room":
            _words(words, 2, where, "room <id>")
            room = Room(words[1])
            rooms.append(room)
        elif room is None:
            raise SystemExit(f"{where}: expected 'room <id>'")
        elif key == "name":
            _words(words, 2, where, "name <text>")
            room.name = raw.split(None, 1)[1].strip()
            if '"' in room.name:
                raise SystemExit(f"{where}: a name can't have a \" in it")
        elif key == "exits":
            for w in words[1:]:
                d, _, target = w.partition("=")
                if d not in room.exits:
                    raise SystemExit(f"{where}: unknown exit {d!r}")
                room.exits[d] = target
        elif key == "colours":
            if len(words) != 4:
                raise SystemExit(f"{where}: colours wants logical 1, 2 and 3")
            room.colours = [_colour(w, where) for w in words[1:]]
        elif key == "band":
            if len(words) != 4:
                raise SystemExit(f"{where}: band <line> <logical 1-3> <colour>")
            line, logical = _int(words[1], where), _int(words[2], where)
            if not 1 <= logical <= 3:
                raise SystemExit(f"{where}: a band changes logical colour 1, 2 or 3")
            room.bands.append((line, logical) + _colour(words[3], where))
        elif key == "sector":
            _words(words, 2, where, "sector <1-5>")
            room.sector = _int(words[1], where)
        elif key == "start":
            _words(words, 3, where, "start <x> <y>")
            room.start = (_int(words[1], where), _int(words[2], where))
        elif key == "beat":
            # The machinery as drawn for the first, the other way for the
            # second (the first again if there's none), in game frames.
            if len(words) not in (2, 3):
                raise SystemExit(f"{where}: beat <frames> [<frames>]")
            frames = [_int(w, where) for w in words[1:]]
            if not all(1 <= f <= 255 for f in frames):
                raise SystemExit(f"{where}: a beat is 1-255 frames each way")
            room.beat = (frames[0], frames[-1])
        elif key == "map":
            # The map's lines are taken whole (spaces matter), and padded.
            rows = []
            for k in range(MAP_H):
                if i + k >= len(lines):
                    raise SystemExit(f"{where}: the map wants {MAP_H} lines")
                line = lines[i + k]
                if len(line) > MAP_W:
                    raise SystemExit(f"{path}:{i + k + 1}: map lines are at most {MAP_W} wide")
                rows.append(line.ljust(MAP_W))
            room.map = rows
            i += MAP_H
        elif key == "thing":
            _words(words, 4, where, "thing <type> <x> <y> [arg]")
            if len(words) > 4:
                _int(words[4], where)       # (the arg; words after it are ignored)
            room.things.append((words[1], _int(words[2], where), _int(words[3], where), words[4:]))
        else:
            raise SystemExit(f"{where}: unknown line {key!r}")
    sector = 1
    for r in rooms:
        if r.sector is None:
            r.sector = sector
        sector = r.sector
        if not r.map:
            raise SystemExit(f"{path}: room {r.ident} has no map")
        if r.colours is None:
            r.colours = [(c, SWAP[c]) for c in DEFAULT_PREVIEW[1:]]
    return rooms


def room_palette_rows(room, phase):
    """Each playfield line's four physical colours, in this phase (0 red, 1 blue)."""
    cur = [0] + [c[phase] for c in room.colours]
    bands = sorted(room.bands)
    rows = []
    for y in range(MAP_H * 8):
        for (line, logical, red, blue) in bands:
            if line == y:
                cur[logical] = (red, blue)[phase]
        rows.append(list(cur))
    return rows
