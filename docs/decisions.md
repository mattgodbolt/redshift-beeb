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
