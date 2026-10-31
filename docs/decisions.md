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

