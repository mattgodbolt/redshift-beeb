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
