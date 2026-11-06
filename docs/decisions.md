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
50. **2026-11-01: Sector 3, THE SUMP** (*provisional*). A level agent built
    the Sump's nine rooms and its kit, with the existing enemies, and a
    one-room Sector 4 to ride down to, held to what the playtests taught
    (decisions 35, 41, 44, 45, 47 and 49): every enemy shot from somewhere
    safe, two ways to kill each sergeant, no hidden take-offs, and every room
    finished from where Ash comes in, in either phase, with two cells.
    - **The water is the Red Phase's.** It boils in the Red and is gone in
      the Blue, where the dry bed under it is the road. Shift back in the bed
      and you're in the soup: the interlock has no opinion about heat. The
      first room teaches it (crystal holds its way out in the Blue, so Ash
      shifts back on the far bank), and most rooms after it have a Red road
      and a Blue one, each with its own enemies.
    - **It's drawn in the body colour (1), not 3 as acid is.** The water
      rises and drains where Ash walks (the sluice, the overflow), and a band
      making 3 red there would turn Ash and the enemies red with it. A room
      with magenta rock makes 1 red from the water's surface down, its floor
      colour (decision 20); one with red rock needs no band. Out of phase the
      body's ghost is faint, and the foam on its surface (`o`, redrawn: no
      room used it) a dotted line at the level the water would be.
    - **Nothing stands in the water but water, unless it's solid.** A cell
      of scenery there (a cistern's legs, a table's) wasn't hot, so a shift
      at just the right spot survived in the soup, and was stuck there.
      Solid things (a drowned desk, a step) are fine: Ash can't be inside
      them. The cistern hangs from rods, and the office's Red road is wall
      shelves.
    - **The machinery,** each warning before it turns (decision 48): the
      steam traps' vents, which steam in turn on the beat; the sluice gate's
      handle, a switch that lifts the gate and drains the water in both
      phases; the overflow, which floods the walkway on the beat; and the
      plughole's plug, a press that drops into the plughole on its chain.
    - **The rooms**, a thing each: OUTFALL the dry bed and where to shift
      back; THE CISTERN the high road over a tank or the low road under it;
      BOILER WALK a sergeant over boiling gaps, lobbed from a steam dome;
      STEAM TRAP the vents; DROWNED OFFICE shelves over the flood, a cabinet
      to lob from, and a sergeant; SLUICE GATE a switch that makes the bed
      safe in the Red; THE U-BEND water that stands to one level in both
      legs, so Ash climbs above it before shifting back; OVERFLOW the flood
      and the depth posts to wait on; THE PLUGHOLE the press over the way
      down, and a sergeant before the cage. Lips alternate yellow and cyan
      from room to room, rock red and magenta.
    - **One Gadfly**, on OUTFALL's far bank, held there by a welded
      barricade that Ash climbs through in the Blue, as the Pump House's is
      (decision 35): a Gadfly bobs over more than two rows, so nothing lower
      holds it that wouldn't hold Ash. Everywhere else a Gadfly could be shot
      standing, its patrol crossed a jump Ash had to make, or it could reach
      nobody.
    - **Slivers** home on Ash and stop at walls, so a pack of them waits
      under a ledge Ash must drop from: THE U-BEND's start in the far leg,
      where the core holds them until Ash is down in the bend, and they come
      along it at Ash's height.

    Calls made in building it (*provisional*):
    - THE PLUGHOLE's basin first flooded on the beat as the plug dropped.
      The flood, the plug and its chain changed as one connected block of
      cells, every frame of the warning redrawing far more than a frame
      holds. Now the basin's water stands, so the Blue is the way down the
      plughole, and the plug is a press over it; the plughole's iron collar
      has no variants, so its walls don't change when the plug drops in.
    - The level editor's check splits every tile between made-up rooms in
      three sectors, not two: with a third sector's kit, two halves held
      more looks than the game can number, and that comparison was skipped.

51. **2026-11-01: a shift is refused into what kills, or beside an enemy;
    a respawn waits for the keys** (*provisional*). From the Sump's
    newcomer playtest:
    - **A shift is refused into the new phase's hazards** (`try_shift` tests
      `TF_HAZARD` as well as `TF_SOLID`). Shifting back to the Red while
      wading in the Blue's dry bed was accepted and killed at once, which
      broke the rule that the game had taught with blocks and enemies
      (decision 45).
    - **And beside an enemy of the new phase**, within `SHIFT_MARGIN` steps
      across and twice that in lines down. A shift accepted just clear of a
      closing Gadfly killed on the next frame. The margin is the same all
      round, whichever way the enemy is going: one rule to learn, "not
      right next to one", and the refusal shows it (the red status bar and
      the buzz). The playthrough's routes wait for an enemy to be a tile off.
    - **After a respawn, left and right count only once both are let go**
      (`pl_hold`). With a direction still held, Ash walked straight back
      into what had killed them.
    - **Each Sliver aims at its own part of Ash** (`SHARD_AIM`), so a pack
      no longer comes together into what looks like one Sliver. Across, the
      aims cover Ash's box; down, only where a standing bolt still meets a
      Sliver and it still reaches a crouched Ash, which the build asserts,
      so nothing about how a Sliver is fought changes. `mkgfx.py` names
      each sprite's size (`SPR_<NAME>_W`, `_H`) for asserts like these.
    - **The cell icon** in the status bar is the cell's shape, a nub over a
      banded body: the old one read as a figure.
    - **The status bar has no line above the score.** The margin a look
      review asked for (with the card's frame) left the score's row touching
      the room name's, since the bar's two rows of text and the rule fill
      its lines; the screen's border is the margin.
    - **Card lines sit inside the frame's sides**, which are drawn in its
      first and last columns; `CARD_LINE` asserts it, and three lines are
      shorter.
52. **2026-11-01: the Sump reworked: both phases in every room, a Blue with
    costs of its own, and few cells** (*provisional*). A level pass from the
    Sump's newcomer playtest, on decision 51's shift:
    - **The Blue isn't a way round.** Every room takes both phases, and the
      Blue has costs of its own where it used to be a free pass: its blocks
      across the STEAM TRAP's corridor and hanging over the OVERFLOW's
      walkway, crystal on BOILER WALK's boilers and the office's landing, a
      span and steps that only the Blue has, and Slivers in packs that are a
      fight. The Blue's blockers stay above the water, as decision 50's rule
      has it: nothing that isn't solid stands in a hazard.
    - **Cells are few.** Two cell pickups in the sector, where there were six,
      and neither pays for a shift on the way: the Cistern's is behind its
      Gadfly in the Red, and the U-Bend's is in the bend, with the swarm.
    - **A room an idea.** OUTFALL the dry bed and where to shift back; THE
      CISTERN a full tank in the Red and an empty one in the Blue, its floor
      the Red's plates, with a swarm in it; BOILER WALK the sergeant over the
      boiling gaps, and a welded door; STEAM TRAP the vents in the Red, or
      the bed's swarm in the Blue, which meet before the last vent; DROWNED
      OFFICE the shelves, the cabinet as cover, and the Blue's span where the
      last shelf was; SLUICE GATE the handle, and the swarm the gate held
      back; THE U-BEND the climb that changes phase on the way up; OVERFLOW
      the flood and its depth posts in the Red, then the Blue's steps over
      the basin; THE PLUGHOLE the plug, and the sergeant under it.
    - **OUTFALL is the first lesson.** Down into the dry bed in the Blue, up
      onto the far landing, and back to the Red there, where crystal holds
      the way out. Its Gadfly is gone: a Trundler patrols a step a row above
      the landing, so it can't come down to Ash, a standing bolt meets it, and
      the landing reaches far enough from the step to shift clear of it. Its
      two Slivers start across the sump at the bank's height, so a newcomer
      sees them wake and come: the hint that a Sliver chases.
    - **No precision spots, no ambushes.** STEAM TRAP's corridor runs into its
      shaft, where the way out was a jump from a few spots. OVERFLOW's posts
      are lower, and the last has a kerb that stops a jump held all the way
      short of the basin behind it. BOILER WALK has room on each side of the
      dome, and the office's shelves are wide. Each room's Slivers were
      placed with a simulation of their homing, so they come level with a
      standing bolt before they reach Ash wherever Ash is meant to shift, and
      none is near a way in.
    - **A way out that fixes the phase,** where coming in in the other one
      would be unfair: the U-BEND's is the Red's, through the Blue's blocks,
      so OVERFLOW, whose Slivers would come down on its last post, is always
      entered in the Red.
    - **The plug is striped,** as the yard's presses are: a newcomer took the
      plain one for something to shoot.
    - **One Gadfly,** in THE CISTERN's cellar, as low as Ash's head, so a
      standing bolt meets it through most of its bob, and its walls hold it.

    Calls made in building it (*provisional*):
    - Ash comes into most rooms in one phase, the one the last room's way out
      takes, but a shift in a doorway or a shaft can change that, so every
      room was checked from both, with two cells.
    - The playthrough takes the Red's road through the STEAM TRAP, and checks
      that the Cistern's cell is taken, since the sector's cells only just
      cover its shifts.
53. **2026-11-01: the Sump's third pass: a cell on the Blue's road, posts that
    can be hopped, steps that show, and fewer Slivers** (*provisional*). A
    level pass from the Sump's second newcomer playtest, which finished every
    room and found the rules consistent:
    - **A cell in the STEAM TRAP's dry bed,** on the Blue's road, past its
      pack. The cheapest route came to THE U-BEND with no cells. Ash comes
      into the STEAM TRAP in the Blue, and each of its roads costs a shift:
      the Red's, from the way in, is the vents' stop and go and pays nothing;
      the Blue's, down through the bed and back to the Red in the last
      pocket, pays the cell. A Blue arrival there was a shift spent for
      nothing; now it's a choice with a price and a prize, and a player who
      takes it comes to THE U-BEND with cells to spare.
    - **OVERFLOW's posts are stepping stones that work.** They looked like
      stepping stones, but the ceiling over them cut every jump to a hop, so
      a newcomer jumped into the flood again and again; getting onto a post
      from the walkway took a jump from right against it, and a bump on the
      last one stopped Ash with no room to jump over it. The hall over the
      walkway is open to the roof now, and the posts are lower (still clear
      of the flood) and closer, so a jump reaches the next post from a run of
      take-offs, and a post from the walkway too. The flood still comes and
      goes on the beat, so walking the walkway in its dry spells is the other
      way. The Blue's baffles hang from the roof, so the posts are still the
      Red's, and the last post's kerb still stops a jump held all the way
      short of the basin behind it.
    - **A step that stops Ash shows itself.** Ash can't walk up a step a row
      high, and three had nothing to say so. The OUTFALL's step into its way
      out had the Blue's blocks standing on its lip, and a newcomer threw
      grenades at them, taking them for the wall: they stand back a column
      now, behind the step's lit lip. THE CISTERN's hanging rods came down
      onto the kerb at the tank's rim, so the kerb read as a rod's foot and
      the rod as the wall: the tank stands in the rock, with an inlet pipe
      hung over it, and the kerb's lip is clear. SLUICE GATE's kerb had the
      Blue's blocks on it too; they hang beside it now. The sector's other
      one-row steps are desks in the office's bed, the bed's step up into the
      STEAM TRAP's last pocket, the corners of THE U-BEND's bend and the plug
      in its hole, each lit and looking like what it is.
    - **DROWNED OFFICE.** A wall of the Red's stands behind the sergeant at
      the second shelf's end. In the Red it stops Ash where the way on is
      only the Blue's span, so they stand at it and see the span's ghost,
      where a newcomer walked off the shelf onto it and into the flood; in the
      Blue it's a ghost itself. A lob that sails over the sergeant goes off
      against it and catches it, so the whole of the cabinet's top and of the
      first shelf before it kill, where most of that shelf lobbed into the
      water; the first shelf ends a tile sooner, where even the wall was too
      far behind. A roll along the second shelf works as before.
    - **THE PLUGHOLE's sergeant** stands a column back, against the cage,
      where a lob that sails over it goes off at the screen's edge and
      catches it: the whole of the crate's top and most of the floor before
      it kill now. The roll works as before.
    - **BOILER WALK has no Trundler.** Its patrol took in where the first
      jump over a boiling gap lands. The steam dome must be two rows high to
      stop the sergeant's bolts reaching the way in, and then nothing behind
      it can be shot standing, and every other surface in the room is a
      landing Ash must make. The room is the sergeant, the gaps, the dome to
      lob from and the welded door.
    - **Fewer Slivers, where they make Ash choose.** Every room had a pack
      that died to held fire. Four rooms have one now: the OUTFALL's pair,
      the lesson; THE CISTERN's tank, where a shift by the kerb brings them
      over it in Ash's face and one back along the walkway gives room; the
      STEAM TRAP's bed, guarding the cell, where they come up through the
      plates beside anyone waiting over the hole; THE U-BEND's far leg, where
      they have to be met in the bend before the climb, or they come down on
      Ash in the leg. THE CISTERN and THE U-BEND have one fewer; BOILER WALK,
      SLUICE GATE, OVERFLOW and THE PLUGHOLE have none.
    - **A fall into a room faces Ash into it** (`go_exit`), towards the side
      with more of the room; a respawn faces the same way. Walking into a
      shaft had left Ash facing its wall at the bottom, as the DROWNED
      OFFICE's arrival did.
    - **Smaller.** THE CISTERN's way out is a hole at the cellar's end, with
      the exit's chevrons in it, behind a wall of the Blue's; it was the
      Blue's trapdoor, with no arrow. The STEAM TRAP's shaft is three tiles
      wide, so Ash drops in as soon as they're over it, not after walking on
      past where the sprite looks over the hole; the office's landing below
      it is wider to match.

    Calls made in building it (*provisional*):
    - The cell is on the STEAM TRAP's Blue road, not on a road every player
      takes, so it's the Blue's reason to be there too, and it lies in sight
      of the way in. A player who takes the Red's road there comes to THE
      U-BEND with no more than before.
    - Facing Ash on a fall is an engine change, where the level alone would
      have needed a dog-leg in the STEAM TRAP's shaft to turn them round.
    - The playthrough takes the Blue's road through the STEAM TRAP, checks
      its cell and THE U-BEND's are taken, hops the OVERFLOW's posts with the
      flood up, and checks Ash comes into the office facing the room.
54. **2026-11-01: Sector 4, THE SPAR SEAMS** (*provisional*). A level agent
    built the Spar Seams' nine rooms and its kit, with the existing enemies
    and no change to the engine, and a one-room Sector 5 to ride down to,
    held to what the playtests taught (decisions 35, 41, 44, 45, 47, 49, 51,
    52 and 53).
    - **The swarm's crystal grows.** The Blue is native here, and its crystal
      is alive: on each room's beat its spans draw back and grow again, and
      its spikes sink and push up, flickering first (decision 48). It's all
      the Blue's, so in the Red it's a ghost, and the Red's way is the
      Company's: welded plates, crates, a furnace, a belt, and the machines.
      The moving crystal is drawn as the span or the spikes (as=), so it
      costs no looks.
    - **Spar is the rock's own crystal**, in both phases. Veins of it light
      the walls, a block of it hangs as the chandelier's boss, and a wall of
      it comes down whole to one grenade, as a cracked wall does: it's drawn
      as one, solid with a black crack and no lit edge, a glint on each face.
    - **A room an idea**, each needing both phases, neither a free pass:
      - THE MOTHER LODE, the lesson: a span over the pit whose middle draws
        back and grows again, and two Slivers that wake across it; back to
        the Red on the landing, where crystal holds the way out, for the
        Trundler on the step. The Mother Lode's crystals stand behind the
        landing.
      - SPAR FACE: a face of spar from floor to roof. Two roads to it: the
        gallery, where a Gadfly hunts in the Red over the Blue's crystal, or
        the Blue's span over it, its middle in time. Behind the face, the
        Blue's blocks, then a welded hatch down.
      - THE ASSAY ROOM: in through a welded hatch; the lab's crystal sinks and
        pushes up on the beat; the assay furnace is the crate, out of the
        sergeant's fire and with a cell on it, and a wall of the Blue's
        crystal stands between it and the sergeant.
      - SORTING TABLE: the Blue's spikes push up through the picking belt in
        turn, two groups each way. The Red's road shoots the Trundler on the
        belt from the floor and walks it; the Blue's times the spikes and
        climbs spans under the hopper for a cell. They meet at the Blue's
        blocks and the welded hatch to the chute.
      - THE CHANDELIER: two spans that take turns under a chandelier of spar,
        to its boss and off it; a cell on the boss; a Gadfly in the way
        out's corridor, held there by the Red's plates, and the Blue's
        crystal in the door.
      - SPLIT SEAM: a seam of spar splits the room into two roads. Over it,
        the sergeant's, lobbed from a crate against a stub of spar behind
        it, then the Blue's span; under it, the swarm's, through the Red's
        wall, over spans that grow, and up a welded step only the Red has.
        The gap between the roads is too wide to jump in the Red.
      - ECHO GALLERY: twin bays, each the other's echo in the other phase:
        the Blue's span over the first bay's acid, and the Red's Gadfly in
        the second, whose floor is the Blue's crystal.
      - LAST PAYDIRT: a bridge that comes and goes too fast to cross. The
        Company's lever stops it as drawn, shot across the drop from a
        welded ledge in the Red, where a cell and charges lie; the Blue's
        crystal hangs in every other line of fire.
      - BORE NINE: two sergeants dug in round the drill, each lobbed from a
        crate with a wall behind it, past walls of the Blue's crystal. The
        swarm waits in the drill shaft, which is the cage, behind a welded
        door: it comes out at whoever shifts back to open it.
    - **Two roads that pay differently.** SPAR FACE, SORTING TABLE and SPLIT
      SEAM each have a road for each phase. The dearer one skips a fight or
      pays a cell.
    - **The enemies:** Slivers in four rooms (the Mother Lode's pair, the
      lesson; the split seam's swarm under the seam; a pair over the
      paydirt's bridge; the swarm in Bore Nine's shaft), Gadflies hunting
      three galleries, each out of reach of the way in, and four sergeants,
      the sector's last two together round Bore Nine.

    Calls made in building it (*provisional*):
    - Green is still acid's alone: the story's green glow in the Blue is the
      acid at the foot of the deep drops, in both phases.
    - Walls stay the shared brick, with veins of spar through it, so the
      sector's looks go on its set pieces: the Mother Lode's crystals, the
      chandelier, the assay furnace and its glassware, the picking belt and
      its hopper, and the Prism's face at the foot of Bore Nine.
    - Cells lie where the sector's shifts need them: on the furnace, on the
      chandelier's boss and on the paydirt's ledge, and two more on the
      dearer Blue roads.
    - The playthrough takes the Red's road through SORTING TABLE and the
      sergeant's through SPLIT SEAM, kills every sergeant, throws the
      paydirt's lever, and rides Bore Nine's cage into Sector 5.

55. **2026-11-01: Slivers keep off each other** (*provisional*). From the
    Spar Seams' newcomer playtest: in BORE NINE three Slivers pinned against
    a wall stacked into what looked like one, and outran the gun. Their
    aims (decision 51) differ, but a wall stops them all at the same place.
    A Sliver's step that would put it on another live Sliver is not taken
    (`shard_blocked`, `shard_on`), so a pack held by a wall waits beside and
    below itself, and each can be seen and shot. Two that begin a move on
    each other (placed so, or spawned there) move as the walls let them
    until they're clear, so none is ever stuck. A first try had each
    Sliver give way only to earlier slots; an earlier one then moved onto
    a later one the wall already held.
56. **2026-11-01: the Spar Seams' second pass: one language for crystal, a
    room an idea, and a fair cage** (*provisional*). A level and art pass
    from the Spar Seams' first newcomer playtest, whose engine fix was
    decision 55. What the newcomer liked stays: the split seam's lower road,
    the paydirt's lever, the spar face coming down to one grenade, and a
    ride on the chandelier.
    - **Crystal has one language.** The newcomer took scenery crystal for
      solid or deadly, walked through crystals into spikes, and took the
      spar face, a wall that breaks, for more of the same.
      - Scenery crystal (the Mother Lode's spires, the chandelier's
        pendants, the stalactites) is drawn in the body colour alone, with
        no lit edge and no lip, so it sits back.
      - Crystal you stand on has its lit lip. The swarm's spans are shelves
        of crystal, a lip with points hanging under it, where they read as
        girders; its spikes are prisms of it pushing up, their points white.
        They're the sector's own tiles, and the moving ones are drawn as
        them, so the crystal that grows and draws back looks like crystal.
      - Crystal that stops you is the Blue's blocks, a wall.
      - Spar that breaks is cracked into rhombs, as the cracked wall is, and
        has no glint.
      - No scenery glints or makes a star: that's a Sliver's shape.
    - **A Sliver is a creature.** It was an X and a cross in turn, which read
      as a gem glinting among the crystal, and as a dotted cross out of
      phase. It's a crystal mite now, lit from the top left, with two dark
      eyes, horns, and legs that scuttle between its two looks. Its size, so
      its aims and the build's asserts, is as it was, and it's the same in
      every sector.
    - **A room an idea, and neither phase a free pass.** Three rooms were a
      blinking span then a shift to the Red, and the Sorting Table's Red
      walked past its puzzle.
      - THE MOTHER LODE, the lesson: a welded plate at the ledge's end stops
        the Red, where a newcomer walked onto the span's ghost, taking it for
        a mesh walkway. A cell lies on the span.
      - SORTING TABLE: two rhythms on the picking belt, out of step. In the
        Red its hoppers pour ore onto it; in the Blue the crystal pushes up
        through it. Each phase waits in its own pocket.
      - THE CHANDELIER drops. The Company's winch lowers it on its chains on
        the beat and draws it up again: over the Blue's span onto its boss,
        ride it down onto the cell that hangs where it comes to, and off it
        over the Red's plates before it goes back up. Its spans and its
        Gadfly are gone.
      - ECHO GALLERY: two walkways over the acid, one over the other, each
        the other's echo. Where the lower is the Blue's crystal, the upper is
        the Red's plates, and the other way round, so whichever phase Ash
        comes in with weaves down and up between them on its own. Its bays
        and its Gadfly are gone.
      - LAST PAYDIRT: the lever is in plain sight across the drop, at the
        height of the way in, and a shot from anywhere along it, standing or
        crouched, in either phase, throws it. It was high in a pocket, shot
        from the top of one crate. Crystal grown over the shaft down holds
        the Blue, so Ash goes down to Bore Nine in the Red.
      - BORE NINE: its walls of the Blue's crystal are gone. Arriving in the
        Blue, the swarm used to pin itself against one by the cage, where
        the Red then had to shift beside it. Now the Blue's prisms on the
        floor before the near sergeant keep the Blue on the first crate, and
        a Blue arrival meets the swarm coming across the room. In the Red it
        comes out of the shaft at whoever shifts on the floor before the
        door, from far enough to be shot.
    - **The opening's cells.** The first two rooms cost three cells and gave
      none: the Mother Lode's cell pays for its two shifts and one more.
    - **Smaller.**
      - SPLIT SEAM's way in is four tiles long, ending at the crate, so
        walking on stops at the crate instead of dropping into the lower
        road; the hole down to it is past the crate.
      - The way down a shaft is an arrow (Spar Face, Sorting Table, Last
        Paydirt): chevrons at the foot of a pit read as spikes.

    Calls made in building it (*provisional*):
    - The sector's spans, prisms, chain and way-down arrow are its own
      tiles, not the shared ones redrawn, so the other sectors look as they
      did and the shared looks don't grow.
    - Echo Gallery has no enemy: the weave is its idea. Spar Face's is the
      sector's last Gadfly, as no other gallery had a patrol that kept off
      the jumps Ash must make and could still be shot.
    - Bore Nine's far sergeant can be passed in the Blue, by meeting the
      swarm from the second crate instead of at the door: the same cell, a
      different fight.
    - The paydirt's ledge keeps its charges and loses its cell, as the
      sector has a cell more.
    - The playthrough takes the Red's road through the Sorting Table, rides
      the chandelier, weaves Echo Gallery in the Blue, and checks the Mother
      Lode's and the Chandelier's cells are taken.
57. **2026-11-01: the Spar Seams' third pass: a door, a face that holds back
    a Gadfly, a furnace that fires, a lever that has to be meant, and a
    mite's ghost with eyes** (*provisional*). A level and art pass from the
    Spar Seams' second newcomer playtest, which found nothing broken and
    finished with no deaths. What it liked stays: the Sorting Table's two
    rhythms, the chandelier's ride, Split Seam's two roads and the shift at
    the top of the lower road's climb, Echo Gallery's weave, and Bore Nine.
    No engine change.
    - **The Mother Lode's first move doesn't kill.** The welded plate at the
      ledge's end was three plates high: a newcomer jumped it like crates,
      onto the span's ghost and into the acid. The way in is a tunnel now,
      with the plates as its door, floor to roof, so the Red stops there and
      the Blue walks through.
    - **Spar Face: the face holds back a Gadfly.** The face hangs from the
      roof to two rows short of the floor. The Gadfly patrols behind it at
      head height and turns at it, so it can't come at Ash, and a standing
      bolt from the way in, under the face, meets it through most of its
      bob. Then a grenade brings the face down. Beyond, the Blue's crystal
      covers the floor, so the Red walks it, and only the Blue's span crosses
      the acid to the shaft, too wide to jump in the Red. The gallery, its
      span with the gap on the beat, and the welded hatch are gone.
    - **The Assay Room: the furnace is the room.** It stands alone over the
      acid between the landing Ash falls onto and the far one, the only
      footing between them. In the Red it fires on the beat, flame roaring
      off its top after the machinery's flicker; in the Blue it's cold. It
      stops the sergeant's fire, so its top and the near landing are out of
      it, and a lob from anywhere on its top kills the sergeant; so does a
      roll on the far landing. The far landing is the Blue's crystal, so Ash
      lands there in the Red, and the furnace is where to shift, refused
      while it fires. Its cell lies on the furnace. The crystal that sank and
      pushed up, and the tall column of the Blue's, which never mattered, are
      gone.
    - **The chandelier doesn't strand its rider.** It comes down to the mouth
      of a low corridor, and Ash steps off it onto rock, a walk well inside
      its time down, where it was a jump over the Red's plates. A wall down
      to the corridor keeps Ash from walking off the raised chandelier
      straight onto it. The corridor's floor is the Red's plates, too low a
      corridor to jump them in the Blue.
    - **Last Paydirt's lever has to be meant.** It hangs high on the far
      wall, level with the welded ledge over the way in, so a bolt from the
      floor, standing or crouched, where the Slivers are fought, passes under
      it: climb to the ledge to shoot it. The ledge has a cell again.
    - **Echo Gallery's Blue pays.** The Blue's crystal holds its door, so a
      Blue arrival weaves the walkways and shifts to leave; the Red's weave
      is free as before. Last Paydirt is entered in the Red.
    - **Two bridges with a gap on the beat, not four.** The Mother Lode keeps
      its span, the lesson, and Last Paydirt its bridge, the lever's. Spar
      Face's is gone, and Split Seam's lower road crosses on a span that
      stays, under a seam of the swarm's crystal that grows shut across the
      road on the beat, a wall of the Blue's blocks while it's shut: wait for
      it to open. Its Slivers start clear of it.
    - **What misled.**
      - A dormant Sliver's ghost, its shape dithered whole, read as a dart:
        the checkerboard broke its horns and legs into diagonals. A small
        enemy's ghost is its whole outline, its dark marks (the eyes) and the
        sparse fill, as a big enemy's is outline and fill, and it reads as
        the mite. Decision 40 dithered it when the Sliver was an X that read
        as a gem. It's the same in every sector. The level editor draws it
        so, and its check now holds the editor's ghost to `ghost_sprite`, as
        it held the outline to `hollow`.
      - The Assay Room's flasks were lit, and a row of them read as spikes or
        ledges: they're drawn in the body colour alone, with no shelf top.
      - Split Seam's stub behind the sergeant was spar, which looks cracked
        and didn't break: it's rock.
      - The Sorting Table's ore was drawn as two lit edges down the stream,
        and read as a pillar of crystal: it's lumps, white-hot, one side of
        the middle then the other, with black between.
    - **The Sorting Table's way in** is a row taller, so a jump there does
      something; the Assay Room's way out matches it.
    - **Cells.** A player who comes into the Mother Lode with two cells and
      takes the cells on the way comes to Bore Nine with more than two, by
      either of Split Seam's roads; Echo Gallery's door and the Paydirt's
      second shift are what the ledge's cell pays for.

    Calls made in building it (*provisional*):
    - Spar Face has one road, where it had two, and the Sorting Table and
      Split Seam keep theirs: three rooms of two roads was a repeat too.
    - The furnace's flame is two looks, the sector's own (its body and its
      ragged top); the seam is drawn as the Blue's blocks, and costs none.
    - No spot a whole tile from Ash's floor puts a Gadfly's whole bob in a
      bolt's line, and Spar Face's was already the best of them, a standing
      bolt meeting it through most of its bob; it was fought in its path.
      Now it's fought from where it can't reach.
    - The playthrough shoots Spar Face's Gadfly under the face, takes the
      Assay Room's cell on the furnace and shifts there as it cools, steps
      off the chandelier, leaves Echo Gallery in the Red, and climbs to the
      Paydirt's ledge for the lever and the cell.
58. **2026-11-01: THE HINGE** (*provisional*). The game's boss, at the
    Prism's focus, and the first step of Sector 5: its room replaces the
    sector's placeholder, and Bore Nine's cage brings Ash into it. The
    story's: the one thing in the mine that's in both phases at once, a Drill
    Sergeant the size of a house in the Red and a crystal flower that sheds
    Slivers in the Blue, one heart between them.
    - **It's tiles, each a picture in each phase.** Far bigger than any
      sprite, it's seven tiles by ten on the map. A tile in
      `gfx/tiles.txt` can have a `blue` block: its picture in the Blue Phase,
      in the same cells, with the same flags in both. So a shift turns the
      sergeant into the bloom where it stands. Such a look has both phases'
      bits in `tile_attr`, so a shift draws it again as it does a phase's
      own; it has no variants or alts and isn't a phase's own. The level
      editor reads and draws them, and its check holds both pictures to the
      build's.
    - **Its states are tiles too.** `then=<key>` names the tile the game's
      code turns a tile into next, and its looks go wherever that tile's do;
      `mkgfx.py` names those looks (`T_HINGE_...`), the sector's own, so the
      code may use them only in that sector's rooms. `src/hinge.6502` writes
      them into the map and lists each changed cell for `render`, as the
      machinery's parts are drawn. The room's thing `hinge` marks the heart;
      the gun's muzzle, the bud and the lamps are found on the map by their
      looks when the room is read.
    - **A round:** in the Red, two charges burst on the plate dent it and
      crack it, and the crystal cracks with it, open on the core. In the
      Blue, a bolt into the core through the crack, before the crystal grows
      back, puts out a lamp in its visor, and the crack snaps shut. The crack
      narrows to a slit in its last moments. Three lamps, three rounds, each
      faster than the last: the gun's shots, the bud's Slivers, the swarm's
      size and the crack's time. A crack that closes unshot is a round to
      try again.
    - **It warns, as a sergeant and machinery do (decisions 47, 48).** Its
      gun's muzzle, at Ash's head on the walkway, lights before each shot;
      it fires only while Ash is in the Red and in its line, a crouch ducks
      it, and out of its line its clock goes round short of the warning. Its
      bud, on its face, lights before it sheds a Sliver in front of it, only
      while Ash is in the Blue and the swarm isn't full; otherwise it waits
      just short of its warning, so it sheds soon after a shift into the
      Blue, but never without warning.
    - **It's fair.** The pillar stands above the gun's line: the place to
      lob from, as a sergeant's crate is (decision 41), and the ledge where
      Ash comes in is behind it. The walkway is a patchwork of the Red's
      blocks and the Blue's over white spikes, so every shift is a choice of
      where Ash will be standing: on the pillar, or on a seam between two
      blocks, which holds Ash in both phases. The Slivers hang as ghosts in
      the Red (decision 15), and a shift is refused beside one (decision 51),
      so where Ash left the swarm decides where they can shift back; the
      seams are the other places. A death reads the room again, the fight
      from its start (decision 30).
    - **The Prism's look.** White faces in both phases, cut into diamonds by
      thin lines in the body colour, which the room bands down the screen in
      the colours the Prism splits light into: red, magenta and yellow in the
      Red; blue and cyan in the Blue. Green stays acid's (decision 27). The
      Hinge's body takes the bands too.

    Calls made in building it (*provisional*):
    - The fight starts, on arrival and after every death, with at least
      eight cells and nine charges (`HG_CELLS`, `HG_GRENADES`), as a death
      leaves at least two cells and a charge (decisions 13 and 16). A round
      takes a shift each way and two charges, and a respawn starts the
      fight again, so anything less could leave a player who'd spent them
      unable to win. The room has no pickups: its things are the Hinge and
      the Slivers it sheds, which take the free slots.
    - The bud is on the bloom's face, so its Slivers come out between Ash
      and the core and take the bolts meant for it; from the bloom's top
      they tumbled down its sides and never reached the fight.
    - The Hinge's code and the endings' code are in main RAM, its art in
      Sector 5's file, and the endings' words in RSDATA with the rest of the
      words on screen. Sector 5's eight rooms to come will make its file the
      largest, and so grow the bank's sector region; code there would have
      cost the bank later what it costs main RAM now.
    - Bore Nine's prism face (`Ω`) stays its own: the Prism's walls are a
      tile of Sector 5's (`ϟ`), with its diamonds on a two by two grid as the
      back wall's are.
    - A shift in the Hinge's room draws every one of its cells again, the
      dearest shift in the game; it's a frame's hiccup at a shift, as every
      room's is, and play's own frames stay inside a frame.
59. **2026-11-01: the endings** (*provisional*). The story's two endings,
    with its words on screen (`docs/story.md`, section 6).
    - **Victory**, when the core takes its last bolt: the swarm and every
      bolt go with it; the Hinge folds shut, its cells gone a column at a
      time from its far side to its heart; the Prism goes dark one facet at
      a time, each of the room's bands of colour black in turn from the top;
      a moment's dark; the lamps come up white, every colour white. Then the
      story's victory words, a card at a time, each until a key or a few
      seconds, and THE END, which waits for a key before a new game. Under
      it, what the visor still shows: a second Prism, deeper down, facing
      the other way, in dotted lines. A short
      piece plays under it (`music/win.txt`): the theme's fall in the Red's
      E Phrygian, the split's climb in the Blue's E Lydian, and home to E
      major, with a low E struck under it like a very large door closing.
    - **Out of lives**: after OUT OF LIVES. OUT OF PHASE. and its phrase, the
      story's ending for it on two cards, then a key for a new game. It was
      the one line in the status bar.
    - **Cards of any length.** A card's lines are centred on the screen,
      every other row, in a frame a row out all round (`card_lines`); a
      sector's card is one of three lines. `CARD_LINE` holds each line
      inside the frame, so the story's lines of up to 32 characters are
      broken again for the screen, the same words; section 6 has them as
      shown.

    Calls made in building it (*provisional*):
    - THE END, not the title page: the title page is RSLOAD's, gone from
      memory once the game runs.
    - The fight's victory is the last thing in the game for now: there's
      no score table, and the new game starts from Sector 1.

61. **2026-11-01: a Sliver comes at a crouched Ash where a crouched bolt
    meets it; the ending's pages wait to be read** (*provisional*). From
    the Hinge's newcomer playtest:
    - **Slivers and crouching.** A Sliver aimed where a standing bolt meets
      it (decision 51) still reached a crouched Ash, whose box starts lower,
      but sat over the crouched bolt's line: it could kill a crouched Ash
      that couldn't shoot it. Against a crouched Ash it now aims
      `SHARD_CROUCH_DY` lines lower, and the build asserts that every aim
      meets the crouched bolt and the crouched box as well as the standing
      ones.
    - **The ending's pages** held for a sector card's time, too short for a
      page of the story's words. They hold twice `WORDS_TIME` now, and a
      key still turns them.
    - **The phase word** comes off the status bar once the Hinge is shut.
60. **2026-11-01: Sector 5, INSIDE THE PRISM** (*provisional*; after 61,
    which landed while it was built). A level agent built the eight rooms between Bore Nine's
    cage and THE HINGE, with no change to the engine, held to what the
    playtests taught (decisions 35, 41, 44, 45, 47, 49 and 51 to 57). Bore
    Nine's cage brings Ash into FIRST FACET at its start; THE DARK FRINGE
    leaves in the Red onto THE HINGE's ledge, edge to edge, behind the
    pillar that shields it from the gun, so the fight begins as it did from
    the cage. The Hinge's start stays on its ledge, for a test disc.
    - **The Prism's floors.** No rock: the walls are the Prism's white face
      in both phases (decision 58), and the floors are the Red's blocks and
      the Blue's over white spikes. A run of one phase's blocks holds Ash in
      that phase only; where it meets the other's, a seam, Ash's box stands
      on both, so a seam holds Ash in either and is the place to shift. A
      run of two to four of the other phase's blocks is hopped from a run of
      take-offs; one of seven or more can't be, and each room has one of
      each phase's, so each needs both phases.
    - **The pulse** (decision 46's machinery). On a room's beat a block of
      the Red's becomes the Blue's (`ρ`) and one of the Blue's the Red's
      (`β`), flickering first. Drawn as the blocks (`as=`), they cost no
      looks, and a seam between the two stays a seam through the turn.
    - **True angles, and light.** The Prism's face cut at 45 degrees along
      its lattice's facet lines (`α ε ι ο`) cuts rooms' corners, hangs the
      refractor and saws SPECTRUM WALK's roof; it's solid, so it stays out
      of Ash's reach. Rays in the body colour (`κ λ ν`) cross the back wall,
      taking each band's colour: the beam the refractor bends, the beam
      reflected at the critical angle, two waves out of step, two beams
      brought to a focus. Scenery, so they sit back.
    - **A room an idea**, each needing both phases from the phase a player
      normally comes in with:
      - FIRST FACET, the lesson: the Blue's floor meets the Red's at a seam,
        with the cell on it. A wall of the Red's stops the Red at the way
        in; two Slivers wake over the floor in the Blue; a Trundler holds
        the way out, a step up from the Red's floor, where it can't come
        down to Ash and a standing bolt meets it.
      - THE REFRACTOR: the pulse. Between the Red's floor and the Blue's,
        the middle turns phase half by half; cross it a half at a time,
        waiting on the seam between the halves.
      - CRITICAL ANGLE: a Gadfly between two walls of the Red's that hang
        two rows short of the Blue's floor. Walk under its ghost in the
        Blue; shoot it under either wall in the Red, where it can't come.
        A wall of the Blue's at the way out.
      - DOUBLE IMAGE: two bays, each the other's image. The Red's has a
        Drill Sergeant, lobbed from the block at the way in, where its
        charges lie, or rolled at along the Red's floor; the Blue's has the
        swarm where the sergeant would stand, met from the pillar between.
      - SPECTRUM WALK: runs of each phase's blocks, the other's hopped, two
        runs too long to hop, and a Trundler on the last. The bands are
        thin, the spectrum.
      - INTERFERENCE: the whole floor turns phase on the beat, run by run.
        Across it in the Red to an island, for its cell; through the Red's
        wall in the Blue; across again in the Blue, through the Blue's.
      - FOCAL LENGTH: the swarm hangs over the Prism's floor, where the
        beams meet, still while Ash is in the Red. A shift beside it is
        refused: shift at the floor's far end, and it comes in a line. A
        Trundler on the Red's floor, shot crouching from the step at the
        way in, where it can't come.
      - THE DARK FRINGE: the Hinge's fight before the Hinge, under bands
        that go black. The swarm over the Blue's floor; a pillar of the
        Prism's out of a sergeant's fire, to lob from; the Red's floor to
        roll along; and the way into the Hinge.
    - **Cells** are few: one on FIRST FACET's seam and one on
      INTERFERENCE's island. Each room takes one or two shifts, and a
      careful player comes to the Hinge with some left, where the fight
      tops them up (decision 58).

    Calls made in building it (*provisional*):
    - A room can't set a thing's phase, so each enemy is in its own, as
      decision 11 has it: the Red's machines and the Blue's Slivers.
    - The Prism's face has a look for each corner of its two by two
      lattice, so its cells don't pack into runs as brick does: the walls
      are thin and the rooms open halls, to keep the sector's file small.
    - Slivers are in four rooms, where where Ash shifts or stands decides
      the fight; THE REFRACTOR and INTERFERENCE have no enemy, as Echo
      Gallery has none, their floors being the idea.
    - No pit reaches a room's edge under its way out: a jump from the last
      lip carried Ash out of the room mid-air before they fell. Each way
      out stands on the Prism's floor.
    - The playthrough plays all eight from Bore Nine's cage into the Hinge,
      checks both sergeants die and both cells are taken, tries a shift
      under FOCAL LENGTH's swarm and fails if it isn't refused, and times
      the frames across both rooms' pulse.

