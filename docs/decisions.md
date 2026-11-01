# Decisions

Every design call, numbered and dated. Matt makes them; a call made while
Matt was away is marked *provisional* until reviewed.

1. **2026-10-31: an original game, not a port.** REDSHIFT is in the genre
   of Hewson's Exolon: flip screens, a blaster and grenades. Its name,
   story, art, map and rules are its own.
2. **2026-10-31: MODE 1, 256x192, with palette bands** (Matt's call),
   after chuckie-egg-2-beeb: the status bar on rows 0-1 in two colours,
   and the playfield below with up to 8 bands. Each band changes one
   logical colour from a given scan line.
3. **2026-10-31: the phase shift is a palette swap** (Matt picked
   REDSHIFT). Every colour in a room has a Red Phase value and a Blue
   Phase one. The other phase's blocks are redrawn as dotted outlines.
4. **2026-10-31: the art and the rooms are text**, so that people can
   edit them by hand, review them in diffs, and use the browser level
   editor (Matt asked for one).
5. **2026-10-31: every step is pushed as it lands** (Matt asked), with
   the disc at the root kept current for the play link.
6. **2026-10-31: flicker-free drawing without a second screen**
   (*provisional*). Each thing that moves is redrawn by composing its
   old and new rectangle (tiles, then every overlapping sprite, masked)
   in a buffer laid out like the screen, then copying it out, so no byte
   is seen half drawn. Overlapping things are pulled into one rectangle.
   A rectangle too big for the buffer is drawn on the screen directly.
7. **2026-10-31: 25 frames a second, 2-pixel steps** (*provisional*).
   Sprites need only two shifted versions (0 and 2 pixels), each also
   mirrored, made by `tools/mkgfx.py`. Walking crosses the screen in
   about five seconds. That's deliberate and weighty, but easy to change.
8. **2026-10-31: the keys** (*provisional*): Z X : / RETURN SPACE, SHIFT
   for the phase, and the cursor keys too.
9. **2026-10-31: the blaster never runs out** (*provisional*). The
   things that run out are phase cells (a shift costs one) and grenades.
   The planned ammo pickup is an extra life instead.
10. **2026-10-31: the dead stay dead** (*provisional*). A thing killed or
    taken is gone from its room for the rest of the game (`room_gone`, a
    bit per thing), so pickups can't be farmed. At most six things a room.
11. **2026-10-31: the enemies' phases.** Sentries, drones and crawlers are
    the Red Phase's machines; shards are the Blue Phase's crystals.
    Out of phase, each is drawn as its dotted ghost and goes on moving
    (but see decision 15).
12. **2026-10-31: a Model B with 16K of sideways RAM, or a Master**
    (*provisional*; the porting kit's baseline, and chuckie-egg-2-beeb's
    decision 8). With the rooms, art and code in main RAM, little was
    left after one room. `RSLOAD` finds a free RAM bank with the OS still
    running, loads `RSDATA` (the art and the rooms) and copies it in, then
    runs the game with the bank paged in for good. jsbeeb's Model B has
    sideways RAM, so the play link works. A stock-B edition that reads
    each sector's rooms from the disc, as CE2S does, is possible later if
    wanted.
13. **2026-10-31: a death leaves at least two phase cells**
    (*provisional*). A room may need a shift to get through. With no
    cells and no pickup left, the player would be stuck for good, so
    respawning tops cells up to 2.
14. **2026-10-31: a safe spell after a respawn** (*provisional*). Ash
    starts again where they came into the room, and what killed them may
    still be there: with a Sliver on the spot, every respawn died at once
    and five lives went in seconds. For a while after a respawn
    (`SAFE_FRAMES`) Ash flashes, and enemies and their bolts can't hurt
    them. Hazards still kill; pickups and the cage still work.
15. **2026-10-31: ghost Slivers hang still** (*provisional*). Out of
    phase, a Sliver went on homing, settled on Ash, and killed them the
    moment they shifted into the Blue. Now one out of phase stays where it
    is. The other enemies still move out of phase (decision 11).
16. **2026-10-31: a death leaves at least one grenade** (*provisional*),
    as decision 13 leaves two cells: otherwise a cracked wall is a dead
    end for a player who has thrown them all.
17. **2026-10-31: a blast three wide and four high** (*provisional*). A
    grenade thrown at a wall goes off level with Ash's head, so a three
    by three blast never reached the bottom row of a wall standing on the
    floor. It now takes its own row, one above and two below.
18. **2026-10-31: a cracked wall comes down whole** (*provisional*). A
    breakable tile that a blast breaks takes the breakable tiles directly
    above and below it with it. Otherwise a wall as tall as Ash could be
    left with a stub at its foot: a grenade thrown from further back
    breaks the top, and every grenade after rises over what's left.
19. **2026-10-31: the look and feel are Claude's to make.** Matt handed
    the game over: "this is _your own_ game to make as you please with a
    little feedback from me but mostly yours and subagent". Calls from
    here on are Claude's, checked by subagent reviewers, and Matt can
    overrule any of them.
20. **2026-10-31: a job for each colour.** After an outside review of the
    screens: logical 0 is air, 1 the body of anything built, 2 its lit
    edges and the lip of whatever you can stand on, and 3 is white for
    Ash, the enemies, the pickups and lethal tips. In a band of liquid a
    room makes 3 the liquid's colour, and nothing safe there uses 3. Each
    room has one rock colour down to its floor, a floor colour from the
    floor's surface, and its liquid's colour only over the liquid, so no
    band cuts a stripe through brickwork. (`gfx/tiles.txt` says how to
    draw with them.)
21. **2026-10-31: walls drawn from where they are.** A tile can have
    variants for where it is (open to air above, below or to a side; deep
    in a wall; under a ceiling; in an exit) and alts used now and then,
    chosen when the rooms are built (`gfxlib.resolve`), and the editor
    chooses them the same way. Deep in a wall it's just brick lines;
    facing air it's solid and lit, so a wall's outline is its brightest
    part. Air is a faint panelled back wall, drawn from where each cell
    falls so the rooms still pack (`back_look`); chevrons mark the ways
    out; pipes have flanges. Out of phase, a block keeps its dotted
    outline and gets a sparse hatch inside.
22. **2026-10-31: sprites that read.** Ash, the enemies and the pickups
    are redrawn with a light, a mid tone and a shadow. Out of phase an
    enemy's ghost shimmers between the two squares of a checkerboard. A
    pickup glints a beat in every four and bobs, and the Settling Tanks'
    two tanks are sunk a row, so the acid's band stays below Ash's boots.
23. **2026-10-31: a status bar of its own.** The score, then an icon and a
    count each for cells, charges and lives in fixed columns; the room's
    name under them, over a dotted rule that keeps the bar off the
    playfield. Its ink is white in both phases, so it doesn't share the
    playfield's yellow. The icons are drawn over three characters the bar
    never prints.
24. **2026-10-31: the corner catch.** Falling against a ledge's corner
    with the feet a few lines below its top (`CATCH`), Ash steps up onto
    it, where before they slid down its face into whatever was below,
    while looking as if they'd landed. Walking still doesn't climb a step.
25. **2026-10-31: crouching ducks a sergeant, and rolls a charge.** A
    crouched Ash is lower (`PL_CROUCH_TOP`), and a Drill Sergeant's gun
    is on top of its head, so on one floor its bolts pass over a crouch.
    A charge thrown crouching rolls along the floor until it hits
    something or the floor ends, so a sergeant can be fought up close, at
    the cost of a charge. Lobbing from a crate still works.
26. **2026-10-31: ghosts are never white, and Slivers stop at walls.** A
    newcomer took ghost Slivers for white gems to collect: a ghost's
    colour 3 is now drawn as 2, and the Sliver is redrawn so its outline
    can shimmer. A Sliver in phase used to fly through solid brick; now a
    wall stops it.
27. **2026-10-31: green is acid, in both phases.** The phase swap turned
    green acid magenta and a magenta floor green, undoing the lesson the
    first room teaches. Every room now gives its Blue Phase colours where
    the swap would make anything but acid green, and acid is green in
    both.
28. **2026-10-31: ghosts keep their shape.** A second outside review found
    the dotted ghosts too broken to see, worst in the blue rooms. A ghost is
    now an enemy's whole outline with a sparse diagonal fill that moves
    between frames: its shape survives, and the shimmer and the missing
    fill say it isn't there. (Out of phase, blocks keep decision 21's
    dotted outline and hatch.)
29. **2026-10-31: walls shaded, floors in the room's colour, rooms told
    apart.** Deep in a wall, brick is now dithered, so a mass reads as
    solid and sits back, where brick lines read as backdrop. Floors take
    the room's own colour (a magenta floor clashed with red rock), and
    rooms alternate red and magenta rock and yellow and cyan lips, so
    neighbours don't blur together. The room's name is centred, apart from
    the counts.
30. **2026-10-31: a death brings the room back.** Ash starts again in the
    room as they came into it: its map reloaded, its enemies where they
    started, in the phase they entered with. A Sliver that had homed onto
    the way in used to wait there for the respawn. The dead stay dead, and
    pickups taken stay taken (decision 10); a wall blown open closes again,
    as it does when you leave and come back.
31. **2026-10-31: a shot you can see land.** A bolt that strikes armour or
    a wall, or wounds without killing, is a spark there for a moment, so a
    Drill Sergeant's armour is seen, not only heard. A bolt can't start
    beyond a thin wall Ash stands against: it strikes the wall. A shift
    the game refuses turns the status bar red a moment, as well as buzzing.
32. **2026-10-31: music, and it follows the phase.** All of it is new, in
    E (`music/`):
    - a title theme while the title page waits for SPACE;
    - a sting for each sector's card, built on the theme's opening fall,
      which runs on into the music under play;
    - a phrase under OUT OF LIVES. OUT OF PHASE.
    The Red Phase's mode is E Phrygian and the Blue's E Lydian: every
    degree but the tonic and the fifth a semitone higher. So in the Blue
    everything made since Bore Nine moves and the rock (E and B) stays, as
    the story's rule has it. The music under play is written once, for the
    Red. In the Blue the player plays the same bars in Lydian, an octave
    up, on a bell and a third faster, from where it was, so a shift is
    heard as well as seen. It has to last a long session under gunfire, so
    it's slow, quiet and mostly space:
    - a pump on channel 2, which nothing else uses;
    - a tune on 1, which an enemy's shot borrows for a moment;
    - now and then a drip on 0, which Ash's shots take.
    The game's sounds take channels 0, 1 and the noise whenever they want
    them, and the music writes its note again when they're done. M switches
    it off and on: silent, but it plays on. P now silences everything, and
    a sector's card stops the game's sounds so its sting has every channel.
33. **2026-10-31: the player** (*provisional*). The scores are text, which
    `tools/mkmusic.py` turns into events and tables at build time. One
    player (`src/musicplay.6502`) serves both the game and the title page:
    each includes it in a scope of its own, with its own data. In the game
    the VSync interrupt steps it, after chuckie-egg-2-beeb's player (MIT,
    Matt's own):
    - `sound_update` holds `mu_busy` while it writes, so the interrupt
      can't land between a tone's two bytes, and plays the frame it missed
      with the next (`mu_owed`);
    - the interrupt puts the keyboard's port back as it found it, since it
      can land inside `key_down`.
    On the title page, with the OS running, RSLOAD's loop steps it once a
    VSync (OSBYTE 19). RSLOAD loads lower to fit it (`RSLOAD_AT`); RSDATA,
    loading at `&3000`, could reach that only with the bank nearly full,
    and an `ASSERT` says if it does. `tools/musiccap.mjs` records what the
    game writes to the chip for each piece and checks it, frame by frame,
    against the tool's model of the player.
34. **2026-10-31: a death that shows.** Matt: "there's no 'death' effect.
    the player just vanishes." Ash's harness fails: they flicker between
    themself and their dotted outline (the out-of-phase look), come apart
    into it, and burst. The rumble is periodic noise, not the white noise
    of a blast, with a falling whine over it, so a death doesn't sound like
    a kill.
35. **2026-10-31: the first enemies shootable from where you stand.** The
    second newcomer's playtest found the first enemy of the game in a pit
    no shot could reach, and Gadflies hovering just over Ash's head, so
    only a jump and fire would hit them. A level-design agent moved them:
    the Landing Zone's Trundler shuttles on a raised pad, in a standing
    bolt's line; the Pump House's Gadfly patrols beyond the barricade,
    which stops two rows short of the floor so a bolt passes under it and
    Ash still has to shift; the Settling Tanks has a Trundler behind its
    cracked wall instead of a Gadfly over its entry, and a narrower second
    tank. Pickups moved clear of pipes, Slurry Run's Slivers off the place
    where a player shifts, and the landmarks grew: the Pump House's
    flywheel, the Settling Tanks' gauge, a hoist in the Catwalks, an
    outflow in Slurry Run, in place of the ceiling rail and lamps.
36. **2026-10-31: a shift changes the whole room.** A third outside review
    found the phase swap barely showed in the magenta rooms: decision 29
    had kept their rock magenta in the Blue, so only the lips changed.
    Every room's rock is now blue in the Blue Phase, so a shift turns the
    room from warm to cold (green stays acid's alone). The status bar names
    the phase, and its rule is solid. The scattered solid bricks are gone,
    since they read as blocks.
37. **2026-10-31: walls are solid brick.** Deep in a wall, brick is solid
    in the room's colour with black mortar, and nothing lit. Three outside
    reviews pulled three ways: solid brick lit yellow throughout was the
    loudest thing on screen, brick lines read as backdrop, and a dither
    read as flat haze. Solid brick without the yellow reads as a wall and
    isn't loud; in the Blue Phase's blue it reads best of all. Floors keep
    their dither, so they sit back under the lip Ash walks on.
38. **2026-10-31: the music after its review** (refines 32). A composer
    and a game-audio reviewer found no borrowed music, and these faults:
    - The title's bass leapt to its upper octave onto the tunes' notes. It
      now keeps to the roots, low, and quieter.
    - Most players press SPACE before the title's Blue arrived. Now the
      split that opens it climbs E Lydian over a fall in E Phrygian, and
      the theme goes a phrase at a time, Red then Blue, so the Blue's tune
      comes in a third of the way through.
    - Card 4's arpeggio doubled its bell, and card 5's voices started in
      unison, which can cancel on the chip: the arpeggio is below the bell
      now, and card 5's fall moves against a held B.
    - The music under play came round too often. It's in two rounds now,
      the second in another order, with the title theme's opening as a
      tune of its own, and the stretch of bass alone where it loops is
      shorter.
    - Its Blue was shrill, with no low end. The bass stays down in the
      Blue, and the tune's bell is quieter and doesn't strike an octave up,
      so the Blue is no louder than the Red, and less bright than it was,
      though still brighter than the Red.
    - Each sector now has a sound of its own on channel 0 under play,
      where sector 1 has drips: clanks, bubbles, glints, a whine. They're
      separate pieces that play the same notes (`from` in a score).
    - Smaller fixes: the fills, card 2's harmony off the bass, card 3's
      fall reaching E, the cards' last bells short, the Prism's line on the
      bell, `high` ending open on B, and the game-over flicker audibly
      slowing.
39. **2026-10-31: sounds that fit the music.**
    - The pickup is E5 B5 E6, notes the shift leaves alone, so it's in key
      in both phases (it was F major). A life, from a trauma kit or a
      score, has a figure of its own.
    - The refused shift's buzz is an octave higher, off the Red bass's
      roots.
    - Taking the cage plays its own figure, a clank and E D C B falling,
      the room held still, before the next sector's card.
    - Game over waits for its phrase to finish, then for a new key press.
      A key held from play skipped it before.
    - M works on the title page too, and the game starts with the music
      as M left it there (`RS_MUSIC`).
40. **2026-10-31: what a hit did, a sergeant's warning, and a way out.**
    From a third newcomer's playtest:
    - An enemy that lives through a hit flickers, so a Trundler's first
      bolt doesn't look like a miss. A bolt on armour ricochets: its spark
      flies back the way it came. A wall's spark stays put.
    - A Drill Sergeant in phase shows its visor and muzzle lit for
      `SENTRY_WARN` frames before each shot, where it used to fire
      without warning (once just as Ash landed).
    - ESCAPE gives the room up for a life and starts it again, so no phase
      gate can trap a player with no cells (rooms are one way).
    - A small enemy's ghost dithers its whole shape: an outline alone read
      as a gem to collect. The crystal spike is drawn as spikes, not a
      tuft like the weeds. The title page lists ESCAPE and says that a
      crouch ducks a sergeant's fire and rolls a grenade. The Engine Shed
      is named THE END, FOR NOW.
41. **2026-10-31: light from the top left, and every sergeant fair.** A
    level and art agent, from the third playtest and look review:
    - Shading by one light, top left: lit sides in colour 2, shadow sides
      stepping down by dither (full, half, quarter, black), and a lit top
      that isn't a lip dithered, never a solid run of colour 2. Pipes are
      cylinders, the flywheel and gauge have bevels, girders and spans dark
      undersides. (`gfx/tiles.txt`'s header has the rules.)
    - The Pump House's way out: the overhang raised, and a crate up to the
      exit ledge, where before one hidden spot worked.
    - Each Drill Sergeant can be killed two ways: a lob from a crate, or a
      crouched roll along an unbroken floor that its fire passes over. The
      hut's sergeant steps out from under the eave; the Skip Shaft's pit
      moves behind the crate, and walking down its ledges lands on the
      crate.
42. **2026-10-31: the rooms load a sector at a time, at the cage** (Matt's
    design). The sideways bank held the art, the text and every room, and
    was nearly full; one sector's rooms are a sizeable part of it, and the
    game is meant to have five. Now:
    - Each sector's rooms are a file of their own, S1 to S5. The bank keeps
      the art, the text and a room region sized for the largest sector's.
      RSLOAD loads RSDATA and S1 at boot, as before.
    - Rooms are numbered within their sector. Their exits stay in it; the
      cage's down exit names the next sector's room, and that room's start
      is where Ash arrives. `tools/mkrooms.py` checks this and writes a
      file of rooms per sector, and what the game needs about all of them.
      `rooms/rooms.txt` stays one file.
    - At the cage, after its ride, the game blacks the screen and silences
      the music, saves what the OS and the DFS will write (the DFS's
      workspace, over which the game runs, and page 8) in screen memory,
      gives the OS its interrupts back, loads the file with OSFILE into
      screen memory, takes the machine back, puts everything back, and
      copies the rooms into the bank. Then the sector's card.
    - What was killed or taken resets at a new sector: sectors are one way.
    - A disc error says so on the screen, and SPACE tries again.

    Calls made in building it (*provisional*):
    - The DFS gets back its catalogue and its state (`&0E00-&10FF`) as it
      left them, kept in main RAM between loads, not only its state. DFS
      1.2 trusts the catalogue it has while the drive still spins from its
      last call, so a retry soon after an error searched the game's code
      for the file, and hung.
    - RSLOAD closes `!BOOT`, the `*EXEC` file, so the DFS has no file open
      whose buffer it would need.
    - A cage's down exit to the next sector has its own mark in the room's
      record (`NEXT_SECTOR`). Falling off the bottom of that room is a pit,
      not a way into the next sector: only the cage loads it.
    - A game that ends in a later sector loads Sector 1 again for the new
      game.
    - During the load ESCAPE is an ordinary key (`*FX229`) and the VDU
      drivers are off (`*FX3`), and the CRTC's display is off as well as
      the palette black: the OS's flash writes its own mode into the ULA.
    - The level editor finds the new exit rule's errors too, since it must
      refuse just what `mkrooms.py` refuses.
43. **2026-10-31: a sector's own looks travel with it.** Every look (a
    tile as written, or one of its variants or alts) has a number under
    128, since the rooms' packing has 7 bits for one, and most were taken,
    many by Sector 1's landmarks. Sector 2 needs landmarks of its own, and
    the bank had little room for more art. Now:
    - A look is shared, in RSDATA and the same in every sector, or a
      sector's own, in its file (S1, S2...) with its rooms, and in the bank
      only while that sector is loaded.
    - A tile's looks are a sector's own when only that sector's rooms use
      it. A tile used in several sectors, or in none, is shared, and
      `gfx/tiles.txt` flags `shared` the building blocks every sector needs
      (everything above the set pieces). Nobody numbers anything by hand:
      `gfxlib.Looks` numbers the shared looks from 0, then each sector's
      own from the first number after them, the same numbers in every
      sector.
    - A sector's file carries its own looks, their dotted outlines, and the
      tables. It loads into the bank's sector region (the room region that
      was), sized for the largest sector's file. A death reloads a room
      from the bank, as before.
    - The build fails if a sector's shared and own looks are more than 128,
      and prints how many are shared, each sector's own, and how many a
      new sector could have.
    - Sector 1's landmark kit is its own. The Engine Shed, Sector 2's
      placeholder, shares the small wheel, the mast and the beacon with
      Sector 1; its signal arm is Sector 2's own.

    Calls made in building it (*provisional*):
    - The look tables (each look's graphics in either phase, and its
      flags) travel whole in each sector's file, the shared looks' entries
      and the sector's own, rather than staying in RSDATA with the
      sector's range patched in at a load. The copy that brings the rooms
      brings them, so there's no code to patch them, nor a second copy of
      the sector's entries kept in the bank to patch from, and RSLOAD's
      copy at boot puts the first sector's in place. It costs each file
      the shared looks' entries again on the disc.
    - The sprites' mask table moved to the start of RSDATA, where it's
      page-aligned with nothing lost to padding.
    - The level editor counts looks as `gfxlib.Looks` does and refuses a
      sector with too many, since it must refuse just what `mkrooms.py`
      refuses. It draws every room as before, whichever sector a tile is
      in.
44. **2026-11-01: Sector 2, and art drawn ahead of its rooms costs
    nothing.** A level agent built THE MARSHALLING YARD's nine rooms and
    its kit of fifteen tiles (rails, trucks, an engine, a turntable, a
    weigh-house, a crane, buffers, the handle, the crusher's teeth), with
    the existing enemies, and a one-room Sector 3 to ride down to. It held
    each room to what the playtests taught (every enemy shot from somewhere
    safe, two ways to kill each sergeant, no hidden take-offs, finishable
    from where Ash comes in). Decision 43 counted a tile no room used as
    shared, so a kit drawn ahead of its rooms, or the editor's made-up test
    rooms, overran the 128 looks; such a tile is now no sector's, and isn't
    in the game until a room uses it.
45. **2026-11-01: no shifting onto an enemy, a Trundler a standing shot
    hits, a Sliver that looks hostile, a ride you can feel.** From the
    Sector 2 newcomer playtest:
    - A shift that would put Ash inside an enemy of the new phase is
      refused, as one into a block is: it killed at once, with no warning.
    - The Trundler has a cab on top and stands 16 lines tall, its tracks
      where they were, so a standing bolt meets it; standing shots used to
      fly over the first enemy a player met.
    - The Sliver is a spiked crystal with a dark core: its ghost still read
      as a gem to collect.
    - The cage ride darkens the room from the top down, a row a frame, as
      the cage goes down the shaft.

46. **2026-11-01: machinery on a beat, and switches.** The Sector 2
    newcomer playtest found five rooms named for machines that did nothing.
    Now a room's tiles can move:
    - **Machinery** is tiles that become other tiles on the room's beat,
      and back on the next. The art says which (`beat=<key>` in
      `gfx/tiles.txt`), and the room how long each way holds (`beat
      <frames> [<frames>]` in `rooms/rooms.txt`). A ram and its slot become
      each other, so a ram drawn shut opens as one drawn open shuts; a
      turntable's deck turns away and back.
    - **A switch** is a thing: a lever, thrown by a shot or a touch, or a
      weigh plate, by standing on it. It changes the room's tiles that say
      `switch=<key>` for as long as Ash is in the room, and with arg 2 it
      stops the beat too, the machinery as drawn. Every switch in a room
      throws the same tiles. Thrown, it loses its white, which marks what
      matters, and bolts pass it.
    - What a tile becomes has its own flags, as any tile has: a shut ram is
      solid and kills, an open gate is air, and machinery can belong to a
      phase as a block does. Machinery that closes on Ash kills them,
      whatever it is.
    - `tools/mkrooms.py` works out every look that changes, the machine's
      own and its neighbours' drawn against it, and puts them in the room's
      record after the map as parts: rectangles of cells, each with its
      looks both ways. The game copies a part's looks into the map, and
      draws just the parts that changed, each composed with whatever's in it
      as a moving thing's rectangle is, so nothing flickers.
    - Decision 30 holds: a death reads the room again, so the machinery is
      as drawn and the switch unthrown, a room always as it was entered.
    - The level editor shows a room on the beat and thrown, dashes the
      parts, edits the beat, and refuses what `mkrooms.py` refuses. Its
      check draws every room in every state its machinery has, pixel for
      pixel against `render()`.

    Calls made in building it (*provisional*):
    - The art, not the room, says what a tile becomes, so a room is still
      drawn with keys alone. A room has one beat and one switch.
    - The build refuses what the game couldn't do: a cell that both the
      beat and the switch change, machinery that's breakable or becomes
      it, a breakable tile whose look the machinery changes (either would
      undo a blast), and more parts than the game's list holds.
    - The beat runs after the things each frame, so a switch that stops it
      on the frame it would turn leaves it nothing to do, and a frame lists
      each part once at most.
    - Machinery moving and a switch thrown make the same short clank on the
      noise channel, the least of its sounds, so a blast or a death has it.
47. **2026-11-01: the Marshalling Yard's machines work, its Blue isn't
    safe, and what breaks looks it.** A level pass from the Sector 2
    newcomer playtest:
    - The machines (decision 46). The TURNTABLE's deck turns end on to the
      line on the beat, leaving the pit open but for the stub on its king
      post. The WEIGHBRIDGE's weigh plate rolls up a shutter to the siding.
      DEAD MAN'S HANDLE's handle is a lever, shot from the ledge, that
      stops the press over the way down; the press can be timed instead.
      CRUSHER'S MOUTH's jaw comes down over the beam on the beat, and a
      press before the cage opens only while the jaw is shut. The CRANE
      GANTRY's loads stay still.
    - The Blue isn't a safe mode. SIDING FOUR has crystal on its middle
      truck and Slivers past the barricade. DEAD MAN'S HANDLE has crystal
      on the floor before each sergeant and Slivers in its air. CRUSHER'S
      MOUTH's beam is a Blue span, a girder, then Red plates, under a jaw
      too low to jump either with, so the finale needs both phases and a
      shift on the girder, in time with the jaw; Slivers wake when you
      shift, and crystal lies before the cage.
    - CRUSHER'S MOUTH has no sergeant. A lob comes down about ten cells
      off, and no crate there could be that far from one, but every
      sergeant must die to a lob from a crate and to a roll (decision 41).
      The press guards the cage instead.
    - What breaks looks it: the jammed ore carts are drawn in the cracked
      wall's look, solid with black cracks and no lit edges, where they
      looked like hoppers hung from the roof. Trucks, lit along their rims,
      are what you stand on.
    - Every room has a start where a player comes in, so a test disc
      (`make ROOM=n`) starts there, not in brickwork or the next room.
    - A Drill Sergeant's clock starts short of its warning, and goes round
      short of it while Ash is out of its sights, so it never fires at
      someone who has just come level with it, landing or shifting, without
      warning them first: landing in the SIGNAL BOX's box put Ash in its
      fire at once. (Round, not held, since its ghost shimmers by it.)
48. **2026-11-01: machinery warns before it moves** (*provisional*). The
    second Sector 2 newcomer playtest found every turn of a beat a switch
    from one frame to the next with no tell, and the TURNTABLE's deck went
    from under a newcomer walking the natural route.
    - For the last `BEAT_WARN` frames before the beat turns, what's about to
      change flickers between how it is and how it will be, `WARN_FLICK`
      frames each way, as a Drill Sergeant lights up before it fires. It's
      the whole of each part that the turn redraws: the machine's own cells,
      and the neighbours drawn against them.
    - Only the drawing sees it. The other looks go into the map just while
      `render` draws (`mach_show` before it, `mach_hide` after), so what Ash
      stands on, and what crushes them, is the machinery as it is; and a
      thing that moves over a part while it shows is drawn over the look the
      warning shows, so nothing is patched with the other.
    - The parts are drawn again only as the warning comes and goes, as at a
      turn. A rectangle with no thing in it, as a part mostly is, is drawn
      straight onto the screen, each byte once, without the compose buffer
      and its copy: the CRUSHER'S MOUTH's turn, the jaw and the press at
      once, had taken more than a frame, and now it and the warning's
      dearest frame both fit.
    - A switch that stops the beat ends its warning. The editor doesn't
      show it.
49. **2026-11-01: the Marshalling Yard's middle moves, and its spikes are
    fair** (*provisional*). A level pass from the second Sector 2 newcomer
    playtest:
    - Machinery where the card promises it:
      - SIDING FOUR's middle truck drives itself: on the beat it runs from
        the near side of the spike gap to the far side and back, and it's
        only ever near one side. A player rides it by standing where it is
        both ways, the end that overlaps itself; the warning shows where.
      - In the CRANE GANTRY one load drops to the floor on the beat and is
        lifted again, and a Drill Sergeant stands on the other: a lob from
        the truck below, or a roll along the load. Its Gadflies went: one
        flew where Ash falls into the room, so every respawn fell onto it.
      - In BUFFER STOPS a truck runs into the buffers on the beat and back,
        and it's the step over them, out of a tunnel too low to jump in:
        climb it while it's there.
    - The moving trucks are drawn as the truck, the air and the torn rail
      (`as=` in `gfx/tiles.txt`), so they cost no looks. Every printable
      ASCII key was taken: newer tiles' keys are other characters, and the
      art and the rooms are read as UTF-8.
    - The TURNTABLE's deck holds in line long enough for a newcomer to walk
      straight over it from the way in, in its first window, and for a
      player who waits at the lip to cross with time in hand.
    - CRUSHER'S MOUTH: the beam's left girder is longer, so there's a spot to
      wait clear of the jaw, and the jaw's housing has a post down to the
      height of Ash's head: the natural jump from the ledge struck the
      housing, fell past it and went on into the jaw's footprint, and now it
      lands short. The jaw stays open longer, and a cell lies on the ledge.
      It still needs both phases, in time with the jaw.
    - Lobs have headroom (decision 41). The SIGNAL BOX's roof is higher, and
      its sergeant stands against the lever frame at the back, so a lob from
      the box's doorway comes down on it, as well as a lob from the truck
      and a roll. The WEIGHBRIDGE's corridor, and the jammed carts in it,
      are taller, so a lob reaches the carts; its crystal moved to where the
      higher jump onto the ledge doesn't land in it.
    - The ENGINE SHED and the SIGNAL BOX have something of the Blue's: crystal
      on the way (before the engine, on the box's truck) and a Sliver.
    - Scenery that read as a lever sits back: the engine's stack is a squat
      chimney, and the signal box's levers are thin rods in the body's
      colour. The lever that works is a thing, marked white.
    - The engine's cab glazing is solid: Ash can't get through the cab, so
      now a bolt can't either. (Its panes were scenery, two rows high, too
      low for Ash and nothing to a bolt.)
