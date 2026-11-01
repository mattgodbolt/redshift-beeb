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
    lines = Path(path).read_text().splitlines()
    i = 0
    while i < len(lines):
        # (A comment is a whole line starting with '#': '#' is a tile's key.)
        raw = lines[i].strip()
        i += 1
        if not raw or raw.startswith("#"):
            continue
        words = raw.split()
        if words[0] in ("tile", "variant", "alt"):
            h = 8
        elif words[0] == "sprite":
            h = int(words[3])
        else:
            raise SystemExit(f"{path}:{i}: expected 'tile', 'variant', 'alt' or 'sprite', got {raw!r}")
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
    def __init__(self, key, name, flags, pixels):
        self.key, self.name, self.flags, self.pixels = key, name, flags, pixels
        self.variants = []      # (when, pixels), in file order: the first that holds is used
        self.alts = {}          # when -> [pixels]: looks used now and then instead


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
    keeps its variants and alts (the blocks after it that name its key)."""
    tiles = []
    for words, art, line in _blocks(path):
        if words[0] in ("variant", "alt"):
            where = f"{path}:{line}"
            if len(words) != 3:
                raise SystemExit(f"{where}: {words[0]} <key> <when>")
            key = " " if words[1] == "space" else words[1]
            base = next((t for t in tiles if t.key == key), None)
            if base is None:
                raise SystemExit(f"{where}: no tile {words[1]!r} before this")
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
        flags = set(words[3:])
        bad = flags - set(TILE_FLAGS)
        if bad:
            raise SystemExit(f"{path}:{line}: unknown flags {bad}")
        tiles.append(Tile(key, words[2], flags, _pixels(art, 8, f"{path}:{line}")))
    if not tiles or tiles[0].key != " ":
        raise SystemExit(f"{path}: the first tile must be 'space'")
    keys = [t.key for t in tiles]
    if len(set(keys)) != len(keys):
        raise SystemExit(f"{path}: duplicate tile keys")
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
    parities (the game shows them in turn, so the ghost shimmers). Never
    white: colour 3 is drawn as 2, since white marks what can hurt you or
    be taken."""
    h, w = len(pixels), len(pixels[0])
    out = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            c = pixels[y][x]
            if not c:
                continue
            edge = x in (0, w - 1) or y in (0, h - 1) or any(
                not pixels[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            # (A small thing has too little inside for a sparse fill: an outline
            # alone read as a gem to collect. Its whole shape is dithered.)
            if (w <= 8 and (x + y + parity) % 2 == 0) or (w > 8 and (edge or (x + y + 2 * parity) % 4 == 0)):
                out[y][x] = 2 if c == 3 else c
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
    variants or alts. It has its tile's flags."""
    def __init__(self, index, tile, when, alt, pixels):
        self.index, self.tile, self.when, self.alt, self.pixels = index, tile, when, alt, pixels
        self.key, self.flags = tile.key, tile.flags
        self.name = tile.name
        if when != "base":
            self.name += "_" + when.replace("+", "_")
        if alt is not None:
            self.name += f"_alt{alt}"


def looks(tiles):
    """Every look, numbered: the tiles as written first (so a tile's number
    is its place in the file), then each tile's variants and alts in order."""
    out = [Look(i, t, "base", None, t.pixels) for i, t in enumerate(tiles)]
    for t in tiles:
        for when, px in t.variants:
            out.append(Look(len(out), t, when, None, px))
        for when, pxs in t.alts.items():
            for k, px in enumerate(pxs):
                out.append(Look(len(out), t, when, k, px))
    return out


def look_hash(c, r, salt):
    """Where alts go: 0-7, from the cell and the room. (The editor has the
    same sum.)"""
    return ((((c + 1) * 40503) ^ ((r + 1 + salt) * 32587)) >> 5) & 7


def resolve(room, tiles, all_looks=None):
    """The room's map as looks: each cell's tile, as its surroundings choose.

    A side of a solid tile is open when the tile there isn't solid in both
    phases; a side of any other tile is open when the tile there is another
    one. Past the map's edge, a side is closed. A tile takes its first
    variant whose <when> holds, or else its own look; then, where the cell's
    look_hash falls below the number of alts for that <when>, that alt."""
    all_looks = all_looks or looks(tiles)
    keys = {t.key: t for t in tiles}
    by = {(lk.key, lk.when, lk.alt): lk for lk in all_looks}
    salt = sum(map(ord, room.ident)) & 0xFF

    def solid_both(k):
        f = keys[k].flags
        return "solid" in f and not f & {"red", "blue"}

    grid = []
    for r in range(MAP_H):
        row = []
        for c in range(MAP_W):
            k = room.map[r][c]
            t = keys[k]
            opened = set()
            for side, (dc, dr) in zip(SIDES, ((0, -1), (0, 1), (-1, 0), (1, 0))):
                nc, nr = c + dc, r + dr
                if 0 <= nc < MAP_W and 0 <= nr < MAP_H:
                    n = room.map[nr][nc]
                    if (not solid_both(n)) if "solid" in t.flags else n != k:
                        opened.add(side)

            def holds(when):
                if when == "deep":
                    return not opened
                if when == "ceiling":
                    return r > 0 and solid_both(room.map[r - 1][c])
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
    lines = Path(path).read_text().splitlines()
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
