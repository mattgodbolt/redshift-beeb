# REDSHIFT — the brief

Where this project started (31 October 2026). Read this, then
`../porting-to-the-beeb.md`, then the siblings named below.

## What it is

An **original** flip-screen run-and-gun game for the BBC Micro (Model B
and Master 128 from one disc), in 6502 assembly with baron. It sits in
the genre of Hewson's *Exolon*, but it is **not a port or a recreation
of it**: its name, story, map, art, enemies and rules are all its own.
Don't borrow Exolon's screens, sprites, code, names or level structure.
(This directory began life as `exolon-beeb` and was renamed once the
game had its own name.)

Repo: `mattgodbolt/redshift-beeb`, public, so the README's play link can
hand jsbeeb the disc from raw.githubusercontent.com, as
`beeb-scorched-earth` does:
`https://bbc.xania.org/?disc=https://raw.githubusercontent.com/mattgodbolt/redshift-beeb/main/redshift.ssd&autoboot`.
Matt asked for the work to be checked in and pushed as it lands ("we'll
push to a github and I can test in my browser from there").

## The story

Kharon-4, 2189. The colony's deep mine broke into the Prism, an alien
engine that splits reality in two. The Red Phase is overrun by the
Prism's war machines; the Blue Phase by its crystal swarm. Trooper Ash
Calder wears the last working phase harness. Fight down through five
sectors and shut the Prism off.

## Signature mechanics

- **SHIFT flips the phase.**
  - Every palette band's colours swap at once: warm reds and yellows in
    the Red Phase, cold blues and cyans in the Blue.
  - The other phase's blocks and enemies become hollow outlines (their
    tiles redrawn): you pass through them, and they can't hurt you or be
    hurt.
  - Shifts cost phase cells, refilled by pickups. You can't shift while
    standing where the other phase has something solid.
- **Two weapons:** a blaster, and lobbed grenades that crack armoured
  emplacements and breakable walls.
- Flip-screen rooms, mostly travelled left to right, in five sectors.

## The look: Chuckie Egg 2's, not Scorched Earth's

Matt picked this explicitly: "big, bold colourful graphics", in the
manner of `../chuckie-egg-2-beeb`'s high-res colour by interrupt.

- **MODE 1 narrowed to 256x192**, 12K at `&5000` (R1 = 64, R6 = 24;
  CE2's `src/defs.6502` and `src/startup.6502`'s `crtc_regs`), set in the
  hardware, not through the OS. Interlace off.
- **Palette bands**: own IRQ1V (VSync plus the User VIA's T1 running
  free); write new ULA entries in the horizontal blank at each split.
  Only four ULA writes fit one blank, and a MODE 1 logical colour has
  four entries, so a split changes one logical colour per scan line.
  Copy CE2's `src/irq.6502` and `src/bands.6502`, and its measured timing
  constants (`SPLIT_T1`, `BAND_ADJ` in its `src/main.6502`; journal for
  how they were measured), then re-measure for this game's layout.
- Since the art is ours, draw it *for* the bands: plan each room as
  horizontal strata whose colours change at the splits.

## Technical plan (provisional: lay each out as a decision for Matt)

- Own the machine as CE2 does: no OS calls in play; keyboard read from
  the System VIA (`key_down` in CE2's `src/system.6502`); sound written
  straight to the SN76489 through the slow bus (`sound_write` in CE2's
  `src/sound.6502`).
- Status bar on rows 0-1; the playfield below it.
- Movement in 2-pixel steps, so sprites need two shifts (0 and 2), not
  four. Game loop at 25fps (every second VSync).
- Flicker-free drawing without a second screen: for each moving thing,
  compose the rectangle it covered and now covers (rounded out to
  character rows) in an off-screen buffer laid out like the screen
  (background tiles first, then every sprite in it, masked), then copy
  that buffer to the screen. Each screen byte is then written once.
  Rectangles that overlap are merged. A rectangle too big for the buffer
  is drawn directly on the screen.
- Rooms authored as ASCII in text files and art as ASCII or PNG, each
  converted by a Python tool in `tools/` with PNG previews.
- Order of layers (porting guide, rule 3): screen and bands, data,
  drawing, player, monsters, objects, sound, front end, loader. Each is
  working and visible in jsbeeb before the next starts.

## Toolchain to copy

- baron 0.6.0 (`../baron/build/src/baron`; pin `v0.6.0` in CI).
- From `../cauldron-2-beeb/tools`: `asm.sh` (fail on a warning),
  `beeb.mjs`, `play.mjs`, `grid.py`, `sample.mjs`. `package.json` with
  `jsbeeb-mcp` (4.4.0 is installed in the siblings).
- CI after `../chuckie-egg-2-beeb/.github/workflows/check.yml`: baron
  built at the pinned tag, `make check` on `B-DFS1.2` and `Master`.
- The `Makefile` after `../beeb-scorched-earth` and `../cauldron-2-beeb`:
  `.DELETE_ON_ERROR`, a build stamp, `make disc` from a clean tree.

## House rules

- Commit messages end at `Co-Authored-By:`; never a claude.ai session
  link or a `Claude-Session:` trailer. Never force-push a pushed branch.
- Comments and docs carry no figure the build computes or one run
  measured (addresses, sizes, free bytes): name the symbol, `ASSERT` the
  property, or cite the dated decision.
- Every deviation from this brief is a numbered, dated decision in
  `docs/decisions.md`. Matt makes the design calls: lay the options out
  with figures.
- Never label a statement "honest" or "candid". Size work by what it
  touches, never by time. Matt is they/them.
- Every agent brief carries these rules.
