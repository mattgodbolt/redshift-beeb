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

## 2026-10-31: a second playtest, a death, and the README's pictures

- A second newcomer finished every room, and found new trouble: armour
  that gave no sign of a hit (sparks now), bolts that started past a thin
  wall, Slivers that kept their places after a death (a death now brings
  the room back), girders whose lattice read as an out-of-phase hatch, a
  cracked wall whose cracks read as exit chevrons, weeds like spikes, a
  sergeant with a target painted on it, and first enemies no standing shot
  could reach (decision 35).
- Matt pointed out that a death had no effect: Ash just vanished. Ash's
  harness now fails visibly (decision 34).
- `tools/playthrough.mjs` plays the whole sector without losing a life
  (`make playthrough`), and takes the README's screenshots
  (`make readme-shots`).
- The bank is getting full: the next sector's rooms will need the room
  records compressed first.

## 2026-10-31: the music, reviewed

- Two reviewers, a composer and a game-audio designer, analysed the WAVs
  and the scores (decisions 38 and 39). Neither found borrowed music. The
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

## 2026-10-31: compressing the rooms, tried

- With the bank filling, the room records went through a baron section
  transform: each record its own section, packed by `LZ_PARSE` into a
  byte-aligned LZ (a control byte for literals or a match, a byte for the
  distance) and unpacked into a buffer as the room's entered. It saved
  nothing. Measured over every room's map, the existing packing (runs, and
  copies from the row above) takes fewer bytes than that LZ does, on the
  raw maps or on top of the packing. A bit-level format might win a
  little (chuckie-egg-2-beeb's rooms needed one), but the rooms are a
  small part of the bank: the sprites, at two shifts and mirrored, are
  most of it. Reverted.

## 2026-10-31: a code review

- A fresh agent read the engine for bugs, and confirmed four in the
  emulator:
  - a ricochet's spark moved but was never redrawn (it wasn't marked
    changed);
  - nothing kept a sprite above the playfield's foot, and below it the
    renderer writes into the sideways bank: a death in a bottomless pit,
    or an enemy blown up low enough, would have corrupted the tiles for
    the rest of the session (no room has either yet). A pit death now
    holds Ash on the playfield, and an enemy's explosion is held on it as
    a grenade's is;
  - a bolt fired at the right edge read the next map row's first column
    as a wall, and sparked in the open;
  - every line of a sector card was underlined by the status bar's rule.
- And two latent risks closed: decimal mode cleared first on the
  interrupt's blackout path, and T1 stopped before its interrupt is
  enabled at start-up.


## 2026-10-31: a sector at a time

- The bank held the art, the text and every room, and was nearly full.
  Matt's design (decision 42): each sector's rooms a file of their own,
  the bank keeping one sector's at a time, and the cage loading the next.
  `tools/mkrooms.py` numbers rooms within their sector and writes a file
  of them for each; RSLOAD loads S1 with RSDATA; the cage's load is
  `src/sector.6502`.
- The game owns the machine, so a load gives the OS back its interrupts
  and the DFS its workspace, calls OSFILE, and takes everything back. The
  first load worked on both machines.
- The trap was DFS 1.2's catalogue. It reads the catalogue afresh only if
  the drive has stopped or the catalogue it has is another drive's
  (`&AA5F` in the ROM, `&1082` in its workspace). Giving back just its
  state page passed the cage's load, the drive long stopped since boot,
  but a retry straight after an error found the drive still spinning and
  searched the game's code as the catalogue, for ever. Now the catalogue
  is kept with the state, as the DFS left them, and the test retries at
  once to check.
- Three more things to know: an error's BRK reaches BRKV with the
  language's ROM paged in, so the handler pages the bank back first;
  OSFILE writes the file's details over its block, so it's set afresh for
  each call; and DFS 1.2's error for a missing file is "Not found".
- `tools/sectortest.mjs`, in `make check` on both machines, takes the
  cage from the first room and checks that the game's memory comes back
  as it was, that the screen is black and the chip silent while the DFS
  runs, that Ash arrives and the frame rate holds, that a death in
  Sector 2 doesn't touch the disc, that a game over there loads Sector 1
  again, and that a disc without S2 gives the error and then loads once
  the disc is back. It reports how long a load takes. By hand: junk in
  the rest of the DFS's workspace at the call, and ESCAPE held through
  the load, changed nothing.
- The level editor refuses an exit across sectors too, since it must
  refuse just what `mkrooms.py` does.

## 2026-10-31: a sector's own looks

- Every look has a number under 128, and most were taken, many by Sector
  1's landmarks, with Sector 2's still to draw. Now a sector's own looks
  travel in its file with its rooms, and only the shared ones stay in
  RSDATA (decision 43). `gfxlib.Looks` sorts them from the rooms and the
  `shared` flag, and numbers the shared ones from 0 and each sector's own
  after them; `mkgfx.py` writes the shared art into RSDATA and each
  sector's looks into `looks<n>.6502`, which `mkrooms.py`'s sector file
  includes.
- The look tables went into the sector's file whole, at the same place in
  every file, rather than staying in RSDATA to be patched at a load: the
  copy that brings the rooms brings them, nothing in the bank is kept
  twice, and the game's code changed only in where the tables are and in
  the region's name, the sector region now.
- The sprites' mask table, page-aligned, moved to RSDATA's start, where
  the alignment costs nothing.
- Checked that nothing looks different: every room of both sectors, in
  both phases, captured at `draw_status` after a death had put Ash in it
  (the playfield's screen memory and the palette program), came out byte
  for byte as before, and so did the playthrough's screenshots, but for
  the title page's build stamp. `make check` passes on both machines, and
  the playthrough goes through the cage into Sector 2.
- The level editor counts looks the same way (`lookCounts`), which
  `editor/check.mjs` holds to `gfxlib.Looks`, and refuses a sector with
  too many, as `mkrooms.py` does.

## 2026-11-01: sectors from the disc, and the Marshalling Yard

- The bank holds the art and one sector. At the cage, with the screen
  black, the game hands the OS its machine back for one load of the next
  sector's file, keeping safe what the OS and the DFS write over, and
  takes it back (decision 42). Each sector's own tiles travel in its file
  too (decision 43), so a sector has room for a kit of its own.
- Sector 2 is built (decision 44). A playthrough plays both sectors and
  rides down into Sector 3's placeholder without losing a life, on the B
  and the Master.


## 2026-11-01: machines that move

- A newcomer's playtest of Sector 2 found five rooms named for machines
  that did nothing, a Blue Phase that was a safe way through three rooms,
  breakables that looked like scenery, test discs that started Ash in
  brickwork, and a sergeant that fired the moment Ash landed by it.
- Machinery (decision 46): tiles that become other tiles on the room's
  beat, and switches, a lever or a weigh plate, that change others once.
  The art says what each becomes, so the game knows nothing of rams or
  gates: `tools/mkrooms.py` draws each room every way its machinery goes,
  and every look that changes, a ram's own and the neighbours drawn
  against it, goes in the room's record as parts. The game copies a part
  into the map and draws it as it draws a moving thing, so nothing
  flickers, and the tiles' flags do the rest. Machinery that closes on Ash
  kills them.
- The rooms (decision 47): the turntable's deck turns away from the line,
  the weighbridge's plate opens a shutter, the dead man's handle stops a
  press, and the crusher's jaw comes down over a beam that needs both
  phases, with a press before the cage that opens only while the jaw is
  shut. Crystal and Slivers make the Blue dangerous where it was safe.
  The jammed carts are drawn in the cracked wall's look. Every room has a
  start. A sergeant warns before it fires at someone who's just come into
  its sights.
- Things met on the way:
  - A Sliver placed inside the rock can't move, and the playthrough didn't
    notice at first, since nothing came near it. A scratch check of every
    thing against the tiles it's on found it.
  - A Red jump cleared a three-cell Blue span under the jaw, so the shift
    wasn't needed: the spans are four cells now, and the jaw's housing
    lower. A Blue jump past the Red plates landed on the truck below: the
    beam runs on over the truck now, so a fall from the plates drops into
    the teeth.
  - No crate in the crusher's room can be far enough from a sergeant for a
    lob to come down on it (about ten cells), so the room has none, and the
    press guards the cage.
  - JavaScript lists integer-like keys first ("10" before "00"), so the
    editor's check takes its states from `mkrooms.py` as a list.
  - A reviewer caught the sergeant's clock held still out of its sights
    freezing its ghost's shimmer, which runs by the same clock: it goes
    round short of its warning instead. And a sergeant late in a room's
    list started inside its warning; its clock starts short of it now.
  - A switch thrown from inside `things_update` tested Ash against the
    switch's own phase's tiles: the crush test sets this phase's first.
- The editor shows a room on the beat (B) and thrown (W), dashes the parts
  that change, edits the beat, and refuses what `mkrooms.py` refuses; its
  check draws every room every way its machinery goes. The playthrough
  rides the turntable, steps on the plate, shoots the handle, crosses
  under the jaw and through the press, checks the frame rate as both move,
  and fails if a switch isn't thrown.

## 2026-11-01: machines that warn, and a yard that moves

- A second newcomer's playtest of Sector 2 found the card's promises
  broken (no truck or crane moved), every turn of a beat a switch with no
  tell, the CRUSHER'S MOUTH a spike, lobs bursting on low ceilings, rooms
  one shift made easy, scenery that looked like levers, and bolts through
  the engine's cab.
- The warning (decision 48): the parts that will change flicker between
  their two looks for a moment before the beat turns. The other looks go
  into the map only while `render` draws, so nothing Ash stands on or is
  crushed by changes early. The Crusher's turn had taken more than a frame
  already; drawing a rectangle with no thing in it straight to the screen,
  without the compose buffer's copy, brought the turn and the warning's
  dearest frame well inside one.
- The rooms (decision 49): a truck that drives itself over SIDING FOUR's
  spike gap, ridden where it overlaps itself; a load that drops in the
  CRANE GANTRY and a sergeant on the crane; a truck that runs into the
  BUFFER STOPS and is the step over them. A turntable a newcomer can cross
  straight from the way in, a safe end to the Crusher's beam with a post
  that stops the natural jump short of the jaw, headroom for lobs in the
  signal box and at the jammed carts, something of the Blue's in the
  first two rooms, a stack and levers that sit back, and solid glass in
  the engine's cab.
- The trucks are drawn as tiles that are already there (`as=`), so the
  machinery costs no looks; every printable key was taken, so their keys
  are other characters, and the files are read as UTF-8. The editor and
  its check follow.
- Things met on the way:
  - A gap one cell wider than a jump's reach from a ledge's middle was still
    jumped from the very lip, where Ash's box hangs over: the shunting
    truck's wrong-side gaps had to grow.
  - The weighbridge's taller corridor let the jump onto its ledge go
    further, into the crystal: the crystal moved.
  - BUFFER STOPS' track ran under rock as low as Ash, so the truck couldn't
    be climbed there and its return crushed whoever waited: the rock over
    the truck's run is gone.
  - A Gadfly flying across the CRANE GANTRY's way in killed every respawn
    as it fell into the room. It's gone, and that's a trap now.
  - Throwing in the signal box needed the sergeant against the lever frame:
    a lob that flies over it bursts on the frame, close enough to catch it.
- The playthrough rides the truck, lobs at the crane's sergeant, climbs the
  runaway truck, crosses the turntable straight from the way in and lobs at
  the carts; its frame check now spans the Crusher's warning as well as its
  turn. It passes on the B and the Master.

## 2026-11-01: the Sump

- Sector 3 is built (decision 50): nine rooms from the OUTFALL, where the
  cage from the Marshalling Yard brings Ash in, down THE PLUGHOLE to a cage
  into a one-room Sector 4. Its kit is the sump's plumbing: boiling water's
  body and a dry bed, a big pipe and its flanges, the outfall's pour, a
  cistern's seams, boilers on their firebrick settings, steam and its
  vents, an office's desks, shelves, cabinets, windows and clock, a sluice
  gate and its racks, depth posts, and the plughole's plug, chain and
  collar. The water and the steam move as tiles drawn as others (`as=`), so
  they cost no looks.
- The sump's water is the Red Phase's and drawn in the body colour, which
  a room makes red from the surface down. Drawn in 3, as acid is, its ghost
  in the Blue was a block of white dots, and a band of 3 would have turned
  Ash red wherever the water rises or drains.
- Each room was checked with a search over Ash's movement (every input
  each frame, the beat turning whenever Ash waits for it, a shift costing a
  cell): which way out each entry phase reaches, with how few shifts, and
  where Ash could end up with no way out. The lobs and rolls for each
  sergeant were checked against the grenade's arc.
- Things met on the way:
  - Scenery standing in the water left cells that weren't hot: a shift at
    just the right spot in the cistern's bed, beside a leg, survived and was
    stuck. Nothing but water stands in water now, unless it's solid.
  - A corridor four rows high is too low to jump a gap of three: the steam
    main ends short of it, so Ash has the height there.
  - The U-BEND's Slivers, in the bend, homed up the near leg and waited
    under the ledge Ash had to drop from; and jumping up onto a step in the
    far leg met them coming down. They start up the far leg now, held by the
    core, and come along the bend at Ash's height; its ledges moved off the
    core's face so nothing traps them on the way down.
  - The U-BEND's way out was over Ash's head on the ledge below it: the
    shelf is narrower, and the plate sits beside the ledge, not over it.
  - THE PLUGHOLE's first design, a basin that flooded as the plug dropped,
    redrew most of the room on every frame of the warning, more than
    a frame holds. Standing water, and the plug as a press over the
    way down, is a different room from the OVERFLOW, and cheap.
  - A sergeant's lob from a crate comes down about ten cells off, so the
    dome, the cabinet and the crate went where the arc meets the sergeant.
  - OUTFALL's Gadfly was to be held on the far bank by a bollard a row high.
    A scripted death showed it flying the whole room to the respawn: it bobs
    up as well as down, over more than two rows, and slipped over the
    bollard. A welded barricade holds it, which Ash climbs through in the
    Blue.
- The playthrough plays on through the Sump and the cage into Sector 4,
  checking the frame rate as the vents, the flood and the plug move and as
  the sluice drains; the README has its tour.

## 2026-11-01: what the Sump's first newcomer found

A newcomer played all nine of the Sump's rooms and finished each. What they
liked: the sluice gate, the U-bend's climb that changes phase on the way up,
the steam trap's stop and go. What broke: a shift back to the Red while
wading in the Blue was accepted and boiled them, one accepted beside a
closing Gadfly killed on the next frame, a respawn with a key held walked
them back into the same death, and a pack of Slivers came together into
what looked like one. Those are engine fixes (decision 51): a shift is
refused into what kills and beside an enemy, a respawn waits for the keys,
each Sliver aims at its own part of Ash. Two finds came from looking at the
fixes: the status bar's score had come to touch the room name below it, and
a card line of the frame's full width ran over its sides.

The Sliver fix's first try aimed some of the pack at Ash's head and knees,
and the playthrough lost two lives in the Leach Works: a Sliver aiming low
passed under a standing bolt. The aims now keep to where a standing bolt
meets a Sliver and a crouched Ash is still reached, and the build checks
it, against sizes the art build now names.

The rest is the sector's design, and goes back to a level agent: the Blue
makes the steam and the flood pointless, eight of nine rooms are a pool,
Slivers and a pickup, two never need a shift, and OUTFALL opens with a
Gadfly that bobs above the bolt's line over the only ledge to shift on.

## 2026-11-01: the Sump, reworked

A level pass over all nine of the Sump's rooms (decision 52), on top of the
engine's new rules for a shift. The playtest's verdict was that the Blue
was a way round everything: the steam and the flood are the Red's, the dry
bed was always there, and a cell in nearly every pool paid for the shift. So
the Blue got costs of its own, and every room needs both phases.

- The water's rule shaped it: nothing that isn't solid may stand in a hazard,
  so the Blue's blocks and crystal can't go in the bed. They went above the
  waterline instead: blocks across the steam trap's corridor, baffles hanging
  over the overflow's walkway, crystal on the boilers and the office's
  landing. The flood's walkway is the Red's because the Blue's baffles hang
  over it, not because anything's in the water.
- Two rooms changed most. The cistern is a tank now: full and boiling in the
  Red, empty in the Blue, with a swarm in it and a floor of Red plates, so
  in the Blue Ash drops right through it into the cellar. The office lost
  its last shelf, and the Blue's span is the only way to the door.
- A simulation of the Slivers' homing placed every pack: for each place Ash
  is meant to shift, when each Sliver comes level with a standing bolt and
  how far off it is then. Slivers stop at walls, so where they wait matters
  as much as where they start. The cistern's swarm first rose straight up
  under the walkway's end and hit Ash from below; a kerb on the tank's rim,
  no higher than the Slivers fly at Ash's height, makes them come over it
  level. The overflow's swarm, woken early from its entrance, came to rest
  over the last post, where it refused the shift there; the U-Bend's way out
  became the Red's, and the overflow's baffles moved so its Slivers wait
  further off.
- Jumps were checked from every x, and two traps turned up. The steam trap's
  bed was a tunnel as low as Ash, so its step up into the last pocket couldn't
  be climbed until the pocket's welded plates opened over it. And a jump held
  all the way onto the overflow's last post went over it into the basin
  behind; a kerb on the post stops it there.
- Every room was played from its way in, in each phase, on a test disc, and
  a scripted death in each showed the respawn where Ash came in, and Ash
  still standing there long after. The playthrough plays the whole sector,
  takes the cistern's cell (the sector's cells only just cover its shifts),
  and checks the frame rate as the vents, the drain, the flood and the plug
  move.

## 2026-11-01: the Sump's second newcomer

A second newcomer finished all nine rooms, found the rules consistent and
the step up from the Marshalling Yard fair, and liked the sluice's drain, the
U-Bend's climb and the steam trap's rhythm. What they hit was smaller, and a
third level pass fixed it (decision 53): cells ran out one short of the
U-Bend, the overflow's posts looked like stepping stones and weren't, three
steps a row high stopped Ash with nothing to show they were there, two
sergeants could be lobbed from only a few of the places a player would try,
a jump landed in a patrol, and every room had a pack of Slivers that held
fire took care of.

- Each fix was measured before it was made. The lob windows the newcomer
  reported, a simulation of the grenade's arc and the game itself agreed to
  the step, so the simulation could try layouts: a wall of the Red's behind
  the office's sergeant, and the plughole's sergeant a column back against
  the cage, both catch a lob that sails over, since a blast reaches a little
  way down from where it goes off.
- Two first tries failed. The overflow's posts could be hopped once the
  ceiling over them opened, but only from a few spots while they stood
  where they were: lower posts, closer together, give a run of take-offs.
  And the boiler walk's Trundler moved behind a steam dome cut to one row,
  so a standing bolt met it over the dome; but the sergeant's bolts, fired
  from just under its head, then crossed the dome as well and killed Ash
  where they came in. The dome is two rows again, and the Trundler is gone:
  nowhere else in the room is out of a jump's landing.
- A sweep listed every step a row high in the sector, in each phase and
  machinery state, so none was missed; the three the newcomer met were the
  ones with something standing on their lips.
- The office's arrival facing its wall was the way Ash walked into the steam
  trap's shaft. A fall into a room now faces Ash into it, which the
  playthrough's stills show in the Pickle Jar and the Skip Shaft as well.
- Every room was played again from its way in, in each phase, and with a
  scripted death; the playthrough takes the steam trap's Blue road for its
  cell and hops the overflow's posts with the flood up.

## 2026-11-01: Sector 4, the Spar Seams

THE SPAR SEAMS are the deepest the Company dug, and the Blue is native
there: the swarm's crystal has grown over everything, and it's alive. A
level agent built the sector's nine rooms round that (decision 54): on each
room's beat the Blue's spans draw back and grow again and its spikes sink
and push up, flickering first, while the Red's way is the Company's welded
plates, crates and machines. Spar, the rock's own crystal, is in both
phases: veins of it light the walls, and a face of it comes down to a
grenade.

- The engine had what the sector needed. Machinery that belongs to a phase
  already worked (the Sump's steam), so a span that draws back is a tile
  drawn as the span, solid and the Blue's, that becomes air on the beat; a
  span that grows is air that becomes one. They cost no looks, and a part
  that flickers in the Red is a ghost flickering.
- A search over Ash's movement in both phases, with every state of each
  room's machinery and a shift costing a cell, checked every room from each
  way in. It found what a glance at the maps missed: Ash's box can hang
  over an edge, so a gap that looked too wide was jumped from its lip, and
  every gap only the Blue may cross is a tile wider; a Red jump across the split
  seam's gap fell past the swarm's pit into the lower road beyond its gates,
  until spar walled the drop; and a bridge that the search let Ash wait out
  on is too long to cross in one of its spells, which is why the paydirt's
  lever matters.
- The grenade's arc, simulated against each layout, set where the crates go:
  a lob from a crate two rows high lands a few cells further than one from
  the floor, so each crate stands a few cells further from its sergeant than
  "about ten", and kills from every take-off on it; a wall right behind the
  sergeant (a stub of spar, a welded door, the next crate) lets it stand a
  little closer.
- The rooms were each played from their way in, in each phase, on test
  discs, with a scripted death in each to see the respawn where Ash came in
  and still standing long after. The Sorting Table's Blue road first ended
  on a single safe cell beside the Blue's blocks, and its spans climbed from
  over the spikes; both moved. Bore Nine's first crate moved under its
  shaft, where a fall from anywhere in it lands.
- The playthrough plays on through the sector, kills its four sergeants,
  throws the paydirt's lever and rides Bore Nine's cage into a one-room
  Sector 5. The split seam's swarm first rose through the upper span while
  it drew back and caught Ash waiting on the stub; the upper road's span is
  still now, and the swarm keeps to the lower road.

## 2026-11-01: the Spar Seams' first newcomer

A newcomer played the Spar Seams through to the cage. The split seam's lower
road, with its shift at the top of a jump, the paydirt's lever and the spar
wall coming down to one grenade were the high points. The low one was the
cage: arriving in the Blue, three Slivers pinned against a column stacked
into one, and the respawn put them back each time. Decision 51's spread
aims hadn't helped, since a wall holds every aim at the same place, so
Slivers now keep off each other (decision 55). The first try let each give
way only to earlier slots, which the emulator showed was no good: the
earlier one walked onto the one the wall already held.

The rest is level work: crystal scenery that looks solid beside a column of
it that is, moving crystal that reads as girders, Slivers that read as gem
glints among the sector's crystal, a lever that is the only way across
with nothing to say so, three rooms that are a blinking span then a shift,
and cells that pinch in the first two rooms.

