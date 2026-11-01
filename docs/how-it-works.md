# How REDSHIFT works

A tour for anyone reading the source. `CLAUDE.md` has the commands and
traps; `docs/decisions.md` has the why of each choice.

## Loading

`!BOOT` runs `RSLOAD` (`src/rsload.6502`) while the OS is still in charge:

1. It shows the teletext title page.
2. It finds a sideways RAM bank: the highest with no ROM that keeps what's
   written to it.
3. It closes `!BOOT`, the `*EXEC` file, so the DFS has no file open.
4. It loads `RSDATA` at `&3000`, and `S1` just after it, and copies both
   into the bank. `RSDATA` is the shared art and the screen text; `S1` is
   the first sector's file: its rooms, its own looks, and the tables for
   drawing every look (see "Looks").
5. It waits for SPACE, playing the title theme, then runs `REDSHFT`.

`REDSHFT` loads at `&1900`. Its loader keeps what the DFS keeps between
calls (its catalogue and state, `DFS_KEEP`) and the OS's page 8, then
copies the game down to `&0E00`, over the DFS's workspace. Start-up
(`src/startup.6502`, run once from where it loaded):

- reads the OS's font through OSWORD 10;
- notes the OS's interrupts (IRQ1V and the VIAs' enables);
- pages the data bank in for good;
- sets MODE 1 in the hardware, narrowed to 256x192 at `&5000`;
- takes over IRQ1V.

From then on the game makes no OS calls but for a sector's load (below).
It reads the keyboard from the System VIA itself, and writes the sound
chip itself.

## A sector at a time

The bank keeps one sector's file at a time, in its sector region
(`SECTOR_AT`), sized for the largest (decisions 42 and 43): the sector's
rooms, its own looks, and the look tables. Rooms are numbered within their
sector, and their exits stay in it. The one way out is the cage: its down
exit names a room in the next sector, marked `NEXT_SECTOR` in the record.
After the cage's ride, `sector_load` (`src/sector.6502`) brings that
sector's file in:

1. The screen goes black (the palette, and the CRTC's display off) and
   the music is held, the chip silent.
2. The game's memory that the OS and the DFS write is copied to screen
   memory: the DFS's workspace and page 8.
3. What the DFS keeps, and the OS's page 8, go back in place as the last
   load (or the loader) left them.
4. IRQ1V and the VIAs' interrupt enables go back as start-up found them.
   ESCAPE is made an ordinary key and the VDU drivers are switched off.
5. OSFILE loads the file into screen memory.
6. Everything goes back, the interrupts are the game's again
   (`install_irq`), and the file is copied into the bank, its look tables
   over the last sector's. What was killed or taken is forgotten: sectors
   are one way.

The sector's card follows, and then its first room. A death reloads the
room from the bank, not the disc. A game that ends in a later sector
loads the first sector's file again for the new one.

A disc error comes back as a BRK through BRKV to `se_error`, which puts
everything back, shows the DFS's message, and tries again on SPACE.

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
   bolts, collects pickups, and throws a switch Ash touches or shoots.
   `ebolts_update` moves the enemies' bolts.
6. `mach_update` steps the room's beat, and moves its machinery when it
   turns, or flickers it before (see "Machinery and switches").
7. `render` draws whatever changed, between `mach_show` and `mach_hide`
   (the warning's looks).
8. `sound_update` steps the effects.

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

## Sound and music

Both go straight to the SN76489 through the System VIA (`sound_write` in
`src/chip.6502`).

- **Effects** (`src/sound.6502`) are tables of steps, one step a game
  frame from the main loop: Ash's on tone channel 0, the enemies' on 1,
  blasts on the noise.
- **Music** (`src/musicplay.6502`, scores in `music/`) is stepped every
  VSync by the interrupt (`music_tick` in `src/music.6502`). Its events
  come a row at a time: a note starts an instrument's envelope, which
  then steps its volume each frame. It only writes a channel no effect is
  using; a channel it couldn't write is dirty, and it writes the note
  again when the channel is free.
- `sound_update` holds `mu_busy` while it writes, because a tone is two
  bytes and a write from the interrupt in between would take the second.
  The interrupt plays the frame it missed with the next.
- The music under play is phased: its events index a pitch table, and the
  Blue's table has every note in E Lydian, an octave up, where the Red's
  has it in E Phrygian. A shift tells the player (`music_phase`), which
  writes the new pitches at once.
- Each sector has its own piece under play (`play`, `play2`...): the
  same notes, with the sector's own sound on channel 0. A sector's card
  plays its sting, which runs on into its piece.
- The cage and game over play a piece that stops, and wait for it
  (`music_wait`) before going on.
- The title page plays its theme with the same player, from RSLOAD's own
  copy, a frame each VSync from the loop that waits for SPACE. M switches
  it off there too, and RSLOAD leaves the choice in `RS_MUSIC` for the
  game.

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

Machinery that moved is drawn the same way, before the things: each part's
rectangle (below) grows to take in whatever it touches, and is composed
with it. A rectangle with no thing in it, as a part mostly is, is just
tiles, so it's drawn straight onto the screen, each byte still once,
without the buffer's copy.

Sprites move in 2-pixel steps, so `tools/mkgfx.py` stores two versions of
each: at a byte, and 2 pixels on. A sprite that faces a way is stored
mirrored too.

## Machinery and switches

Decision 46. A room's tiles can move (`src/machines.6502`):

- **On the beat.** A tile in `gfx/tiles.txt` can say `beat=<key>`: on its
  room's beat it becomes that tile, and back on the next. The room says
  how many frames the map holds as drawn and how many the other way
  (`beat` in `rooms/rooms.txt`). A ram and its slot say each other, so
  one drawn shut opens as one drawn open shuts.
- **A switch.** A tile can say `switch=<key>` instead: it becomes that
  tile when the room's switch is thrown, and stays so while Ash is in the
  room. A switch is a thing, a lever (a shot or a touch throws it) or a
  weigh plate (standing on it does). With arg 2 it stops the beat too, the
  machinery back as drawn.

What a tile becomes has its own looks and flags, so the game knows
nothing of rams or gates: a shut ram is solid and a hazard, an open gate
is air. `tools/mkrooms.py` draws the map four ways (as drawn, on the beat,
the switch thrown, both), each through `gfxlib.resolve`, so a changed
tile's neighbours take the looks they'd have against it too. The cells
whose looks change are cut into parts, rectangles small enough for
`cbuf`, which go in the room's record after the map, each with its looks
both ways (the record's format is in `tools/mkrooms.py`).

When the beat turns, or the switch is thrown, `mach_apply` copies the
parts' looks into the map and lists their rectangles for `render`, which
draws them as it draws a moving thing's. If Ash is inside anything solid
or deadly then, they die (`crushed`): nothing else can put them there.

The beat warns before it turns (decision 48). For its last `BEAT_WARN`
frames the parts flicker between how they are and how they'll be,
`WARN_FLICK` frames each way (`warn_vis`), and only the drawing sees it:

- `mach_update` lists the parts when the warning comes and when it goes,
  so `render` draws them again then, and only then.
- While it shows, `mach_show` puts the other looks in the map just before
  `render`, and `mach_hide` puts them back just after (`mach_apply`
  without listing). So what Ash stands on, and what crushes them, is the
  machinery as it is, and a thing that moves over a part is drawn over the
  look the warning shows.
- A switch that stops the beat puts the machinery as drawn, and ends the
  warning.

A tile can be drawn as another (`as=<key>` in `gfx/tiles.txt`): it has no
looks of its own, and `gfxlib.resolve` draws a cell of it as that tile
would be there. So machinery that looks like something already drawn, a
truck that drives itself and the air or torn rail it leaves, costs no
looks; the game never knows the difference, since the map holds looks.

The beat and the switch come back as drawn when the room is read again
(`mach_load`, from `load_room`), so a death brings back the room as it was
entered (decision 30).

## Phases

- Every tile has flags (`gfx/tiles.txt`). `red` or `blue` makes it exist in
  that phase only.
- `tools/mkgfx.py` writes two tables of tile pointers and two of
  attributes, one of each per phase, in each sector's file (see "Looks").
  Out of phase, a tile points at its dotted outline and has no flags at
  all.
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
built, so the game just draws a look's number, and the editor picks them
the same way.

A room has 7 bits for a look, so a sector can draw with 128 at most.
Looks are shared or a sector's own (decision 43), and `gfxlib.Looks`
sorts and numbers them:

- A tile's looks are a sector's own when only that sector's rooms use it,
  unless `gfx/tiles.txt` flags it `shared`. The rest are shared: a tile
  used in several sectors or in none, the flagged building blocks, and
  always the empty tile.
- The shared looks are numbered from 0 and live in `RSDATA`
  (`tile_gfx`). Each sector's own are numbered from the first number
  after them, so every sector's own take the same numbers; they live in
  the sector's file (`build/data/looks<n>.6502`, part of `sector<n>.6502`).
- The tables the game draws and collides with (`tiles_red`, `tiles_blue`,
  `tile_attr`, `attr_red`, `attr_blue`), `NTILES` long, are in the
  sector's file too, at the same place in each (`src/main.6502`): a
  sector's load brings its tables with its rooms, and the drawing code is
  as it was.
- The build fails if a sector has more than 128, and `make` prints how
  many are shared and each sector's own.

Air is the exception. Its looks are a two by two grid of faint panel seams,
and storing them would break up the rooms' runs of air, so the map keeps
plain air and the drawing code picks the grid's look from where the cell
is (`back_look` in `src/screen.6502`).

## The data

The art and the rooms are text, so anyone can edit them, by hand or with
the editor.

- `gfx/tiles.txt` and `gfx/sprites.txt` hold the art.
- `rooms/rooms.txt` holds the rooms.
- `music/*.txt` hold the music: `music/instruments.txt` says how.
- `tools/mkgfx.py`, `tools/mkrooms.py` and `tools/mkmusic.py` turn them
  into `build/data/*.6502`. `tools/mkrooms.py` writes a file for each
  sector (`sector<n>.6502`, the disc's `S<n>`), its rooms with its looks
  from `tools/mkgfx.py` (`looks<n>.6502`), and in `rooms.6502` what the
  game needs to know about them all.
- A room packs as runs of tiles and runs copied from the row above, and
  its machinery's parts follow the map. The record format is in
  `tools/mkrooms.py`'s docstring.
- The build previews each room in both phases, with a row for each state
  its machinery has (`build/preview/room_<id>.png`).
