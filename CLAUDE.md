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
make ROOM=n       # a test build that starts in room n (0 first) at its `start`
make run          # boot it, shots/run.png
make ship         # the disc from HEAD (a scratch worktree), copied to redshift.ssd and committed
```

`node tools/play.mjs '<script>' shots/p_ --until game_start` drives the game. The steps are listed in its header. Key names are jsbeeb's: Z, X, COLON_STAR, SLASH, RETURN, SPACE, SHIFT. `tools/beeb.mjs` presses SPACE at the title page on the way to any game symbol. A sector card shows for about 150 frames first (`f160`, or tap a key). `python3 tools/grid.py out.png 2 a.png b.png` tiles screenshots.

The README's play link boots `redshift.ssd` at the repo root through jsbeeb's `github:` URI, so ship a disc after every change worth seeing. Matt asked for each step to be pushed as it lands.

## How it fits together

- `!BOOT` runs RSLOAD (`rsload.6502`, with the OS alive). It shows the teletext title page, finds a sideways RAM bank, loads RSDATA (the art, the rooms and the text) and copies it in, then runs REDSHFT. REDSHFT copies itself down to `&0E00` and owns the machine from then on: no OS calls.
- The screen is MODE 1 narrowed to 256x192 at `&5000`. The status bar is rows 0-1, in logical colours 0 and 1 only; the playfield is rows 2-23.
- `irq.6502` plays the palette program: the status split, then up to 8 bands per room, each changing one logical colour on a scan line. Its timing is chuckie-egg-2-beeb's, measured there, and the instructions before each write must stay as they are.
- `render.6502` draws moving things flicker-free. Each thing's old and new rectangles are composed in `cbuf` (tiles, then sprites masked), then copied out.
- The art and the rooms are text. `tools/mkgfx.py` and `tools/mkrooms.py` turn them into `build/data/*.6502`, and `tools/gfxlib.py` is the shared reader. The level editor in `editor/` reads the same files.
- Each colour has a job (`gfx/tiles.txt`'s header, decision 20); keep new art to it. A tile's variants are picked from its surroundings when the rooms are built (`gfxlib.resolve`); the editor has a copy of that in its core script, which `editor/check.mjs` holds to the build pixel for pixel. Air is drawn by position at run time (`back_look`), not stored.
- The sideways bank is the tight memory. If it fills, compress the room records with baron's section `transform` and `LZ_PARSE` (they're unpacked once a room); leave the art raw, since it's read every frame.

## Traps met

- **A load after a call sets the flags its caller tests.** `LDX` after `test_area` made every bolt hit; `rd_byte`'s own `INC` hid the byte's Z. Wrap with `PHP`/`PLP` or end with `ORA #0`.
- **Routines that clobber registers callers loop with.** `read_keys` (X and Y), `print_char_a` (leaves Y at &FF), `sound_write` (now keeps Y). Count loops in memory, not registers, across calls.
- **After tiles are drawn over things** (a phase shift, a blast), mark the things changed (`objs_touch`), never forgotten (`objs_forget`). Forgotten things lose their old rectangle and leave trails. `objs_forget` is only for a new room.
- **The sideways bank must stay paged** (`RS_BANK`, `&F4` and `romsel`). Everything in RSDATA is read in place.
- **Enemies and their bolts call `player_hit`, hazards and pits `player_die`.** `player_hit` does nothing in the safe spell after a respawn (decision 14); a pit must always kill, or Ash falls off the bottom of the room.
- **The interrupt runs with D as the game left it**: `add_score` uses decimal mode, so the VSync path does `CLD` before anything that adds.

## House rules

- Commit messages end at `Co-Authored-By:`. Never a claude.ai session link or a `Claude-Session:` trailer. Never force-push.
- Comments and docs carry no figure the build computes or a run measured (addresses, sizes, bytes free). Name the symbol or `ASSERT` the property.
- Deviations and design calls are numbered decisions. Matt makes the calls; one made while Matt is away is marked provisional.
- Never label a statement "honest" or "candid". Size work by what it touches, never by time. Matt and Ash Calder are they/them.
- Every agent brief carries these rules.
