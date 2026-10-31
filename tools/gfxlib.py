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
        if words[0] == "tile":
            h = 8
        elif words[0] == "sprite":
            h = int(words[3])
        else:
            raise SystemExit(f"{path}:{i}: expected 'tile' or 'sprite', got {raw!r}")
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


def read_tiles(path=ROOT / "gfx/tiles.txt"):
    """Tiles in file order; the first must be the empty one (key ' ')."""
    tiles = []
    for words, art, line in _blocks(path):
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
    followed by its dotted outline, <name>_ghost, shown out of phase."""
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
            out.append(Sprite(name + "_ghost", w, h, hollow(s.pixels), s.flags - {"phase"}))
    return out


def hollow(pixels):
    """The out-of-phase look of a phase tile or sprite: a dotted outline.
    The outline is the lit pixels on the edge (a neighbour or the border is
    dark). The dots are the squares of a checkerboard that keep more of it
    (the even ones, on a tie); a tiny thing keeps its whole outline, so it
    never vanishes."""
    h, w = len(pixels), len(pixels[0])
    edge = []
    for y in range(h):
        for x in range(w):
            if pixels[y][x] and (x in (0, w - 1) or y in (0, h - 1) or any(
                    not pixels[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))):
                edge.append((x, y))
    even = [(x, y) for x, y in edge if not (x + y) & 1]
    odd = [(x, y) for x, y in edge if (x + y) & 1]
    keep = even if len(even) >= len(odd) else odd
    if len(keep) < 8:
        keep = edge
    out = [[0] * w for _ in range(h)]
    for x, y in keep:
        out[y][x] = pixels[y][x]
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
            room = Room(words[1])
            rooms.append(room)
        elif room is None:
            raise SystemExit(f"{where}: expected 'room <id>'")
        elif key == "name":
            room.name = raw.split(None, 1)[1].strip()
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
            line, logical = int(words[1]), int(words[2])
            if not 1 <= logical <= 3:
                raise SystemExit(f"{where}: a band changes logical colour 1, 2 or 3")
            room.bands.append((line, logical) + _colour(words[3], where))
        elif key == "sector":
            room.sector = int(words[1])
        elif key == "start":
            room.start = (int(words[1]), int(words[2]))
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
            room.things.append((words[1], int(words[2]), int(words[3]), words[4:]))
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
