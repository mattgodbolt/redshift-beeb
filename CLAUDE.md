# REDSHIFT (BBC Micro): notes for Claude Code

An original flip-screen run-and-gun game for a BBC Model B with 16K of
sideways RAM, or a Master, in 6502 assembly with
[baron](https://github.com/waitingforvsync/baron). It's in the genre of
Exolon but borrows nothing from it: its name, story, art, rooms and rules
are its own (`BRIEF.md`).

- `BRIEF.md` is where it started.
- `docs/story.md` is the plot and the words on screen.
- `docs/decisions.md` holds every design call, numbered.
- `docs/journal.md` is the story of the build.

## Commands

```sh
make              # build/redshift.ssd, symbols build/redshift.json, previews in build/preview
make ROOM=n       # a test build that starts in rooms.txt's room n (0 first) at its `start`
make run          # boot it, shots/run.png
make check        # the smoke test, a sector's load (tools/sectortest.mjs), the editor's checks; MODEL=Master too
make ship         # the disc from HEAD (a scratch worktree), copied to redshift.ssd and committed
make playthrough  # plays the whole of Sector 1, through the cage's load, to the Engine Shed: the end-to-end test
make readme-shots # retakes the README's screenshots (docs/media) from a playthrough
make music-preview  # each piece of music as a WAV in build/preview/music, from the scores
node tools/musiccap.mjs [dir] [--quick]  # what the game writes to the chip for each piece, checked against the scores, as WAVs
```

`node tools/play.mjs '<script>' shots/p_ --until game_start` drives the game. The steps are listed in its header. Key names are jsbeeb's: Z, X, COLON_STAR, SLASH, RETURN, SPACE, SHIFT. `tools/beeb.mjs` presses SPACE at the title page on the way to any game symbol. A sector card shows for about 150 frames first (`f160`, or tap a key). `python3 tools/grid.py out.png 2 a.png b.png` tiles screenshots.

The README's play link boots `redshift.ssd` at the repo root through jsbeeb's `github:` URI, so ship a disc after every change worth seeing. Matt asked for each step to be pushed as it lands.

## How it fits together

- `!BOOT` runs RSLOAD (`rsload.6502`, with the OS alive). It shows the teletext title page, finds a sideways RAM bank, loads RSDATA (the shared art and the text) and S1 (the first sector's rooms and looks) and copies them in, then runs REDSHFT. REDSHFT copies itself down to `&0E00` and owns the machine from then on: no OS calls, but for a sector's load.
- The bank keeps one sector's file at a time, in its sector region (`SECTOR_AT`; decisions 42 and 43): its rooms, its own looks, and the look tables. Rooms are numbered within their sector, and only the cage's down exit leaves it (`NEXT_SECTOR`). After the cage's ride, `sector.6502` gives the OS back its interrupts and the DFS its workspace, loads the next sector's file (`S<n>`) with OSFILE, and takes the machine back.
- A look (a tile, or one of its variants or alts) is shared, in RSDATA, or one sector's own, in its file (`gfxlib.Looks`, decision 43). A tile only one sector's rooms use is that sector's own unless `gfx/tiles.txt` flags it `shared`. Shared looks number from 0 and each sector's own after them, so a sector has at most 128 between them; `make` prints the counts.
- The screen is MODE 1 narrowed to 256x192 at `&5000`. The status bar is rows 0-1, in logical colours 0 and 1 only; the playfield is rows 2-23.
- `irq.6502` plays the palette program: the status split, then up to 8 bands per room, each changing one logical colour on a scan line. Its timing is chuckie-egg-2-beeb's, measured there, and the instructions before each write must stay as they are.
- `render.6502` draws moving things flicker-free. Each thing's old and new rectangles are composed in `cbuf` (tiles, then sprites masked), then copied out.
- `machines.6502` moves a room's machinery (decision 46): tiles that say `beat=` or `switch=` in `gfx/tiles.txt` become other tiles on the room's `beat`, or when a lever or plate is thrown. `mkrooms.py` puts every look that changes in the record as parts, which the game copies into the map and `render` composes.
- The art and the rooms are text. `tools/mkgfx.py` and `tools/mkrooms.py` turn them into `build/data/*.6502`, and `tools/gfxlib.py` is the shared reader. The level editor in `editor/` reads the same files.
- The music is text too (`music/`; `music/instruments.txt` says how), made into data by `tools/mkmusic.py`. One player, `musicplay.6502`, is included twice, each in its own scope with its own data: in the game, where the VSync interrupt steps it (`music.6502`), and in RSLOAD for the title theme. The game's effects take a channel from it whenever they want one.
- Each colour has a job (`gfx/tiles.txt`'s header, decision 20); keep new art to it. A tile's variants are picked from its surroundings when the rooms are built (`gfxlib.resolve`); the editor has a copy of that in its core script, which `editor/check.mjs` holds to the build pixel for pixel. Air is drawn by position at run time (`back_look`), not stored.
- The sideways bank is the tight memory, and the sprites are most of it: each is kept at two shifts, and mirrored if it faces a way. Its sector region holds the largest sector's file, rooms and own looks, so a bigger sector grows it. The rooms are already packed well (runs and row copies): a byte-aligned LZ through baron's `transform` and `LZ_PARSE`, on the packed or the raw maps, came out bigger, so that's been tried.

## Traps met

- **A load after a call sets the flags its caller tests.** `LDX` after `test_area` made every bolt hit; `rd_byte`'s own `INC` hid the byte's Z. Wrap with `PHP`/`PLP` or end with `ORA #0`.
- **Routines that clobber registers callers loop with.** `read_keys` (X and Y), `print_char_a` (leaves Y at &FF), `sound_write` (now keeps Y). Count loops in memory, not registers, across calls.
- **After tiles are drawn over things** (a phase shift, a blast), mark the things changed (`objs_touch`), never forgotten (`objs_forget`). Forgotten things lose their old rectangle and leave trails. `objs_forget` is only for a new room.
- **The sideways bank must stay paged** (`RS_BANK`, `&F4` and `romsel`). Everything in RSDATA is read in place.
- **Enemies and their bolts call `player_hit`, hazards and pits `player_die`.** `player_hit` does nothing in the safe spell after a respawn (decision 14); a pit must always kill, or Ash falls off the bottom of the room.
- **A `make ROOM=n` build starts Ash at that room's `start`, or the first room's**, not where they'd come in; and after a room change its things spawn only once it's drawn, so a script waits for `blackout` to clear.
- **A Gadfly bobs over walls that don't cover the row it fills**: bound its beat with walls the height of its bob.
- **The interrupt runs with D as the game left it**: `add_score` uses decimal mode, so the VSync path does `CLD` before anything that adds.
- **Inside `things_update`, `attr_ptr` is the thing's own phase's tiles**, not Ash's. Anything it calls that tests Ash against the map (a switch's `crushed`) sets it back first (`set_tile_ptrs`).
- **A thing's clock (`th_t`) drives its looks too**: a ghost's shimmer, a pickup's glint. Don't hold it still to time something; let it go round.
- **A thing placed in solid rock can't move**, and nothing may notice: a Sliver in a wall just hangs there. Check every thing against the tiles under it after moving rooms about.
- **Prove a room needs what it's meant to need** with a simulation of Ash's jumps (as `player_update` moves), in each phase and each state of its machinery: a low ceiling shortens a jump, but a fall off a ledge lengthens one.
- **A lob comes down about ten cells off** (`arc_tab`, thrown at two steps a frame). A crate nearer a sergeant than that can't kill it, which breaks decision 41.
- **JavaScript lists integer-like object keys first** ("10" before "00"): pass ordered things from Python to the editor's check as lists.
- **The interrupt writes the sound chip.** Main-loop code that writes a tone (two bytes) holds `mu_busy` across them, as `sound_update` does. A loop that doesn't call `sound_update` (a card, game over) leaves an effect holding its channel: stop the effects first (`sound_quiet`).
- **The game's frame is 312 lines, 39936 cycles, not 40000** (MODE 7's interlaced one is). A tool counting frames from cycles drifts a frame every 150 or so.
- **Until the game runs, the low pages are the OS's.** A harness poke at a game variable there (`pl_safe`) on the title page writes into the OS's workspace.
- **Two channels on one note can cancel.** Two square waves of the same period may be in opposite phase. Keep tunes off each other's notes (the bass low, arpeggios below a bell).
- **DFS 1.2 trusts the catalogue it has while the drive still spins.** Give it back `&0E00-&10FF` (`DFS_KEEP`) as it left them, catalogue and state together: with its state alone, a second call soon after the first searched the game's code for the file, and hung.
- **What runs while the OS has the machine lives above the DFS's workspace and out of page 8**, and reads nothing below it until the game's memory is back (`sector.6502`'s ASSERTs). The game's own routines (`sound_write`, `install_irq`, the printing) are under `&1900`: call them only before the save or after the restore.
- **An OS error reaches BRKV with the language's ROM paged in.** The handler pages `RS_BANK` back (`romshad` and `romsel`) before anything reads the bank. **OSFILE writes the file's details over its block**: set it afresh for each call.
- **A look's number past `NSHARED` is a different look in each sector**, and the look tables (`tiles_red`... `attr_blue`) are in the sector's file, not RSDATA. Code may name only shared looks (`gfx.6502` has `T_` names for no others), and nothing that holds a look number may live across a sector's load.
- **A tile no room uses is shared**, so art drawn for a sector counts against every sector until one of its rooms uses it, and a tile painted into a second sector's room becomes shared too. Once the art has more than 128 looks in all, `editor/check.mjs`'s plain made-up room fails (its blank map uses no tile, so every tile is shared), and its other made-up rooms are refused for that before anything they test: give those checks fewer tiles then.

## House rules

- Commit messages end at `Co-Authored-By:`. Never a claude.ai session link or a `Claude-Session:` trailer. Never force-push.
- Comments and docs carry no figure the build computes or a run measured (addresses, sizes, bytes free). Name the symbol or `ASSERT` the property.
- Deviations and design calls are numbered decisions. Matt makes the calls; one made while Matt is away is marked provisional.
- Never label a statement "honest" or "candid". Size work by what it touches, never by time. Matt and Ash Calder are they/them.
- Every agent brief carries these rules.
