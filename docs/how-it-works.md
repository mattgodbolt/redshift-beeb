# How REDSHIFT works

A tour for anyone reading the source. `CLAUDE.md` has the commands and
traps; `docs/decisions.md` has the why of each choice.

## Loading

`!BOOT` runs `RSLOAD` (`src/rsload.6502`) while the OS is still in charge:

1. It shows the teletext title page.
2. It finds a sideways RAM bank: the highest with no ROM that keeps what's
   written to it.
3. It loads `RSDATA` at `&3000` and copies it into the bank. `RSDATA` is
   the art, the rooms and the screen text.
4. It waits for SPACE, then runs `REDSHFT`.

`REDSHFT` loads at `&1900` and copies the game down to `&0E00`, over the
DFS's workspace. Start-up (`src/startup.6502`, run once from where it
loaded):

- reads the OS's font through OSWORD 10;
- pages the data bank in for good;
- sets MODE 1 in the hardware, narrowed to 256x192 at `&5000`;
- takes over IRQ1V.

From then on the game makes no OS calls. It reads the keyboard from the
System VIA itself, and writes the sound chip itself.

## A frame

The game runs at 25 frames a second: one per two VSyncs (`game_start`'s
loop). Each frame:

1. `read_keys` reads the keys (`keys`, and `keys_new` for those just
   pressed).
2. If SHIFT was pressed, `try_shift` flips the phase.
3. `player_update` moves Ash: walking, the jump table, falling, hazards
   and room exits. `shots_update` moves Ash's bolts.
4. `grenade_throw` and `grenade_update` handle the grenade.
5. `things_update` moves each enemy, checks it against Ash and the
   bolts, and collects pickups. `ebolts_update` moves the enemies' bolts.
6. `render` draws whatever changed.
7. `sound_update` steps the effects.

## The palette program

The interrupt (`src/irq.6502`) owns two sources.

**VSync.** It writes all sixteen palette entries: the status bar's colours
for the entries the status bar can show, and the playfield's for the rest.
It starts the User VIA's T1.

**T1.** It runs free:

- The first interrupt comes just before row 2. It writes the playfield's
  colours into the six entries the status bar used.
- Each later interrupt is one of the room's bands. It changes one logical
  colour, which is four ULA entries in MODE 1 and all that fits in a
  horizontal blank.
- Each interrupt also loads T1's latch with the period to the next but
  one, so only VSync's latency moves the splits. (The timing is
  chuckie-egg-2-beeb's, measured there.)

`src/bands.6502` builds these tables from the room's bands:

- `set_timing` works out the periods, once a room.
- `set_colours` works out the entries for the current phase. A phase shift
  just calls it again.

## Drawing without flicker

The room is drawn once, whole, when Ash enters it. After that only the
things are drawn (`src/render.6502`). Things are the player, bolts, the
grenade, enemies, pickups and explosions.

Each changed thing has a footprint: where it was drawn and where it is
now, as one rectangle of byte columns and character rows. The rectangle
grows to take in anything it touches. It is then composed in `cbuf`, a
buffer laid out like the screen:

1. the room's tiles from the map;
2. every thing in it, masked, in slot order;
3. then a copy out to the screen.

Each screen byte is written once, so nothing is ever seen half drawn.

Sprites move in 2-pixel steps, so `tools/mkgfx.py` stores two versions of
each: at a byte, and 2 pixels on. A sprite that faces a way is stored
mirrored too.

## Phases

- Every tile has flags (`gfx/tiles.txt`). `red` or `blue` makes it exist in
  that phase only.
- `tools/mkgfx.py` writes two tables of tile pointers and two of
  attributes, one of each per phase. Out of phase, a tile points at its
  dotted outline and has no flags at all.
- Collision reads the phase's attribute table (`attr_ptr`), and drawing its
  pointer table (`tp_lo` and `tp_hi`).
- A shift redraws only the phase tiles (`draw_room_phase`).
- Enemies belong to a phase too (`type_phase` in `src/things.6502`). Out of
  it they're drawn as their ghost sprite and can't touch or be touched.

## Looks

A tile in `gfx/tiles.txt` can have variants: other pictures for where it
is in a room (open to air above, below or to a side, deep in a wall, under
a ceiling, in an exit) and alts used here and there by a hash of the cell.
`tools/gfxlib.py`'s `resolve` picks each cell's look when the rooms are
built, so the game just draws a tile number, and the editor picks them the
same way.

Air is the exception. Its looks are a two by two grid of faint panel seams,
and storing them would break up the rooms' runs of air, so the map keeps
plain air and the drawing code picks the grid's look from where the cell
is (`back_look` in `src/screen.6502`).

## The data

The art and the rooms are text, so anyone can edit them, by hand or with
the editor.

- `gfx/tiles.txt` and `gfx/sprites.txt` hold the art.
- `rooms/rooms.txt` holds the rooms.
- `tools/mkgfx.py` and `tools/mkrooms.py` turn them into `build/data/*.6502`.
- A room packs as runs of tiles and runs copied from the row above. The
  record format is in `tools/mkrooms.py`'s docstring.
