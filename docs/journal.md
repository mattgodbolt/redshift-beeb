# Journal

What was done, in order, with what worked and what didn't.

## 2026-10-31: the start

- Matt asked for a game in the style of Exolon. It's an original game in
  that genre rather than a port, so it has its own name, story, art, map
  and rules. From three pitches Matt picked REDSHIFT, whose signature is
  a phase shift done with the palette (`BRIEF.md`).
- Matt pointed at Chuckie Egg 2's look, MODE 1 with palette bands from
  interrupts, over Scorched Earth's MODE 2. The interrupt handler follows
  CE2's `irq.6502` up to each write, so its measured timing carries over.
  CE2's fixed band splits become a list of per-line changes of one
  logical colour each.
- The art and the rooms are text files (`gfx/`, `rooms/`), read by the
  Python tools and, later, by the level editor.

## 2026-10-31: the first room on screen

- `tools/mkgfx.py` and `tools/mkrooms.py` turn the text art and rooms
  into data, with PNG previews in `build/preview` that render each room in
  both phases, bands and all.
- The room packs as tiles, runs, and runs copied from the row above,
  which suits rooms built of long walls and floors.
- The first boot hung in `load_room`: `rd_byte` returned the flags of its
  pointer's `INC`, not of the byte, so the name loop never saw its 0.
  Then the status text was garbled: `print_char_a` leaves Y at &FF, and
  the string loop indexed with it.
- Bands and the phase shift work as planned. SHIFT recolours every band
  and redraws only the phase tiles (`draw_room_phase`).

## 2026-10-31: Ash moves

- `render.6502`: each changed thing's old and new rectangle grows to take
  in anything it touches, is composed in the buffer (tiles, then sprites
  masked in slot order), and is copied out. Walking and firing hold 25
  frames a second (50 frames in 100 VSyncs).
- `player.6502`: walking, a jump table, falling with gravity, crouching,
  bolts, hazards, and room exits. The phase shift is refused if it would
  put Ash inside something solid.
- Bugs met: two more of the same kind as `rd_byte`'s. A load after a
  routine set the flags its caller tested: `LDX sh_x` after `test_area`
  made every bolt hit at once. Branches out of range were fixed with `JNE`
  and an inverted branch.

## 2026-10-31: things

- `things.6502`: sentries (armoured, fire along their row), drones (bob
  and turn at walls), crawlers (turn at walls and at the floor's end),
  shards (home in), pickups, the grenade's arc and blast (which also
  clears breakable tiles), and enemy bolts. `tools/mkgfx.py` makes each
  phase enemy's ghost, and mirrored copies only of sprites flagged
  `mirror`.
- A trap avoided: after tiles are drawn over things (a blast, a phase
  shift), forgetting what's on screen would leave a trail where a moving
  thing was. They're marked changed instead (`objs_touch`), so both
  rectangles are redrawn.
- The low pages filled up. The interrupt's page-aligned tables now come
  first, and the compose buffer is 768 bytes.
- Memory is getting short below the screen.

## 2026-10-31: sideways RAM

- The art and the rooms move to a sideways RAM bank (decision 12):
  `RSLOAD` finds the bank, loads `RSDATA` and copies it in. That leaves
  main RAM to the code, with plenty of room in both. Both of jsbeeb's B
  and Master find a bank.

## 2026-10-31: sound

- `sound.6502`: table-driven effects on the SN76489 (shots, blasts,
  deaths, pickups, enemy fire, an armour ping, a refusal buzz, and a sweep
  for each phase shift), one step a game frame, from the main loop. The
  interrupt writes nothing to the chip, because a write there could fall
  inside `key_down`'s use of the same VIA port. Checked with jsbeeb's
  sound capture: the periods and volumes arrive as tabled.
- `sound_write` now keeps Y: `sound_update` indexes with it.

## 2026-10-31: Sector 1

- An agent designed Sector 1, THE LEACH WORKS: nine rooms from the
  LANDING ZONE down to the cage in the SKIP SHAFT, and a placeholder
  ENGINE SHED in Sector 2 for the cage to arrive in. Each room teaches
  one thing: jumping, the shift, ghosts, the grenade, the Drill Sergeant,
  then spending cells with care. No room needs more than two shifts from
  where Ash comes in, so the two cells a death leaves are always enough.
- New tiles: the Blue's swarm span and crystal spikes, the Red's welded
  plate and boiling water (kept for the Sump), and a lamp. The rooms use
  the welded plate, not the red block: its seams are colour 2, so its
  outline still shows in the Blue, where colour 1 is a dark blue.
- A scripted run plays the whole sector without a death, from a driver
  that reads Ash's position, lives, cells and phase every frame.
- The playtests found four faults in the engine (decisions 14-17):
  - An enemy left on the spot where Ash came in killed every respawn at
    once: five lives went in seconds. Now a respawn has a short safe
    spell, with Ash flashing.
  - Ghost Slivers went on homing, and settled on Ash, so the next shift
    into the Blue killed. Now they hang still out of phase.
  - A grenade thrown at a wall goes off at head height, and its blast
    never reached a wall's bottom row. Now it reaches two rows down.
  - A player who'd thrown every grenade could be stuck at a cracked wall.
    A death now leaves at least one.
- Still open: a grenade thrown point blank flies over a Drill Sergeant on
  the same floor, and only lands from well back. Both sergeants have a
  crate to throw from.

## 2026-10-31: a gentler first room

- Matt couldn't see how to finish the LANDING ZONE. It could be done, but
  the obvious way died: walking off the middle girder carried Ash past
  the crate into a pit with the Trundler, and a full jump from the crate
  hit a rock overhang at the room's edge and dropped them back into it.
- The girders and the crate are a tile wider, so a walk off the girder
  lands mid-crate. The overhang is gone, so a jump from the crate clears
  the Trundler and leaves the room. The Pump House's wall opens to match,
  so Ash can't arrive inside rock.
- A small simulator of Ash's movement (the jump table, falling, the
  collision box) over a room's map found the trap and the fix before the
  emulator confirmed them.

## 2026-10-31: the Settling Tanks' wall

- Matt couldn't see the way past the Settling Tanks: the cracked plate
  hung over a gap one tile high, which read as a hole too small to fit
  through, not a wall to blast.
- The gap is filled, so the tunnel mouth is a cracked wall from the step
  to the ceiling. A grenade from further back would only have broken its
  top, and none could then reach its foot, so a cracked wall now comes
  down whole (decision 18). A grenade from the foot of the step or from
  a few tiles back clears it all.

## 2026-10-31: a new look

- Matt asked a fresh agent to compare REDSHIFT's screens with another BBC
  game's, without saying which was ours. It found REDSHIFT readable and
  varied in layout, but flat: walls louder than anything you play with,
  yellow spent on everything, hazard colours on safe floors, palette bands
  cutting stripes through brickwork, plain white sprites. Matt then handed
  the look and feel over (decision 19).
- Each colour has one job now (decision 20), and every room's palette was
  redone to it: one rock colour, a floor colour from the floor's surface,
  the liquid's colour only over the liquid.
- Tiles get variants from where they are (decision 21), chosen as the
  rooms are built, and the level editor chooses them the same way. Its
  check, which draws every room against the build's own picture, caught
  the port's mistakes before they shipped.
- A first back wall, stored as a two by two grid in the map, broke the
  rooms' run-length packing and cost more of the bank than all the new
  tiles. Air is now drawn as the back wall for where it is
  (`back_look`), and the map keeps plain air.
- Ash and the enemies are redrawn with light and shade (decision 22). A
  first Ash's helmet read as a beak, and a first Drill Sergeant as a
  duck: both were redrawn after looking at them large, in more than one
  band's colours.
- The status bar has icons, fixed columns and a rule under it, in white
  (decision 23).
- Matt pointed out that baron can compress sections if memory gets tight.
  The bank is the tight part. When it is, the room records are the first
  thing to compress, since they're unpacked once a room; the art is read
  every frame.

## 2026-10-31: landmarks, and a newcomer's playtest

- An agent dressed every room with a landmark from a small kit of new
  tiles: the beacon and pad, the flywheel, sight glasses, the jar's lid,
  a gauge, the hut's roof and windows, railings, an outflow, a sheave and
  skip, and a signal for the Engine Shed. A script compared every cell's
  flags before and after: only air became scenery.
- Another agent played every room as a newcomer, from screenshots, with
  no map. It finished all of them, and found:
  - Ash sliding down a ledge's corner into acid while looking landed (the
    corner catch, decision 24);
  - THE PICKLE JAR's opening: the lid a tile too low, so the first jumps
    had a window of a few steps. The lid is a row higher, the second plate
    reaches under the ledge, and the drain's Trundler starts at the far
    end facing away, so the drop into it can be timed by watching;
  - VAT ROW's crystal spike hidden under a Trundler's ghost (moved onto a
    span);
  - ghost Slivers taken for gems, and Slivers flying through brick
    (decision 26);
  - the phase swap making acid magenta (decision 27);
  - crouching not ducking a sergeant (decision 25, which also answers the
    question of how to fight one up close);
  - horizontal pipes and the crystal span's teeth read as ledges and
    ghosts: the pipe is thinner and in the body colour, the span solid.

## 2026-10-31: music

- An agent wrote the music (decisions 32 and 33): a title theme, a sting
  for each sector's card, the music under play and a phrase for the
  game's end, all new and all in E. The idea came from the story's rule
  that what was there before Bore Nine is in both phases. Going from E
  Phrygian to E Lydian moves every degree but the tonic and the fifth, so
  the Red Phase's music becomes the Blue's by raising every "made" note a
  semitone. The music under play is written once and played either way,
  and the player switches at a shift, mid-bar.
- The scores are text grids, a token a semiquaver, so the voices line up
  down the page. `tools/mkmusic.py` checks every bar's length and makes
  the data. It also has a model of the player in Python, which renders
  WAV previews through `tools/snwav.py`, a model of the chip after
  jsbeeb's.
- The player shares the chip with the game's sounds as chuckie-egg-2-beeb's
  does: `mu_busy` across a tone's two bytes, and the keyboard's port put
  back by the interrupt. As there, an effect borrows a channel and the
  music writes its note again when the effect is done; here every effect
  can, on channels 0, 1 and the noise. One source serves the game and the
  title page, which has the OS running: baron scopes let each include it
  with its own zero page, `sound_write` and data. The title page didn't
  fit below MODE 7's screen, so RSLOAD now loads lower.
- `tools/musiccap.mjs` records what the game writes to the chip for each
  piece and checks it, frame by frame, against the Python model. Every
  piece matched, over its whole length. It found two faults of the
  harness's own, both now in CLAUDE.md:
  - the game's frame is 312 lines, not MODE 7's 312.5, and counting
    frames by 40000 cycles slipped one about every 150;
  - the first VSync after start-up writes silence, as every channel
    becomes the music's.
- Reading the flow turned up a real fault. The cage starts its sound and
  goes straight into the next sector's card, and the card doesn't step
  sounds, so the cage's held channel 0 the whole time and the sting's
  tune never sounded. A card now stops the game's sounds first. The first
  try at that clobbered the sector number in A (`sound_quiet` keeps only
  X and Y), and the music check caught it at once: no sting at all.
- P silences everything now. Before, a pause in the middle of an effect
  left its note sounding.

## 2026-10-31: the music, reviewed

- Two reviewers, a composer and a game-audio designer, analysed the WAVs
  and the scores (decisions 34 and 35). Neither found borrowed music. The
  biggest fault was the title's bass: its octave leaps landed in unison
  on the tune at full volume in nearly every bar. Unisons matter on this
  chip: two square waves of the same period can be in opposite phase and
  cancel, which is why card 4's landing note went hollow in the render.
- The fixes were measured as the reviewers measured. A check over the
  model's writes now finds no unison or step between channels except in
  card 5's split, where the clash is meant. The Blue under play was tried
  several ways, and the settings kept put its peaks below the Red's and
  its brightness between the two.
- A piece can now play another's notes on its own instruments (`from`),
  which gives each sector its own sound under play for the cost of its
  instruments.
- The cage now has a figure of its own, and game over waits for its
  phrase, with `music_wait`.
- The capture tool had been poking `pl_safe` on the title page, where the
  low pages are still the OS's, and `pl_safe` falls in its sound
  workspace. It pokes it only once the game is running now.

